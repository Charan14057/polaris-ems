"""
POLARIS-EMS — Optimizer API Adapter
SIH26061: Polar Energy Management & Resilience System

Translates API requests into calls to the frozen Phase 6 OptimizerEngine.
Preserves explicit HiGHS solver optimality semantics:
- EXACT_OPTIMAL when gap == 0.0
- MIP_GAP_OPTIMAL when gap <= configured tolerance (e.g. 3%)
- FALLBACK when heuristic / conservative dispatch was required
- INFEASIBLE when solver mathematically rejected problem
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from dataclasses import asdict

from backend.optimizer.engine import OptimizerEngine
from backend.optimizer.schema import OptimizationMode, OptimizationResult, SolverStatus
from backend.scenarios.registry import ScenarioRegistry
from backend.twin.twin_engine import TwinEngine
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.api.schemas.optimizer import (
    OptimizeRequestSchema,
    OptimizeResponseData,
    OptimizationSummarySchema,
    DecisionStepSchema
)
from backend.api.errors import InvalidRequestException, ScenarioNotFoundException


class OptimizerAPIAdapter:
    """Adapts Phase 6 OptimizerEngine to the API boundary."""

    def __init__(self, scenario_registry: Optional[ScenarioRegistry] = None):
        self.scenario_registry = scenario_registry or ScenarioRegistry()

    def execute_optimization(
        self,
        req: OptimizeRequestSchema,
        optimizer: OptimizerEngine,
        twin: TwinEngine
    ) -> OptimizeResponseData:
        """Executes microgrid optimization with Digital Twin replay validation."""
        sid = req.station_id.upper()
        horizon_h = req.horizon_hours
        start_ts = req.start_timestamp or "2026-06-01T00:00:00Z"
        mode = OptimizationMode(req.mode.upper())

        # 1. Resolve Initial State from Twin
        initial_state: TwinState = twin.initialize_twin(start_ts)

        # 2. Resolve Scenario if requested
        scenario_def = None
        if req.scenario_id:
            try:
                scenario_def = self.scenario_registry.get(req.scenario_id.upper())
            except KeyError:
                raise ScenarioNotFoundException(req.scenario_id)

        # 3. Build Driving Trajectory Steps
        trajectory_steps = []
        for h in range(1, horizon_h + 1):
            day = 1 + (h - 1) // 24
            hour = (h - 1) % 24
            ghi = 200.0 if (6 <= hour <= 18) else 0.0
            trajectory_steps.append(TwinInputStep(
                timestamp=f"2026-06-{day:02d}T{hour:02d}:00:00Z",
                horizon_h=h,
                ambient_temp_c=-20.0,
                wind_speed_m_per_s=10.0,
                ghi_w_per_m2=ghi,
                load_kw=45.0,
                solar_kw=15.0 if ghi > 0 else 0.0,
                wind_kw=25.0,
                mode=req.mode
            ))

        # 4. Execute Phase 6 Optimization
        try:
            res: OptimizationResult = optimizer.optimize(
                initial_state=initial_state,
                trajectory=trajectory_steps,
                scenario=scenario_def,
                mode=mode,
                generator_overrides=req.generator_overrides
            )
        except Exception as e:
            raise InvalidRequestException(f"Optimizer execution failed: {str(e)}")

        # 5. Extract Explicit Optimality Tier Semantics
        tier = res.optimality_tier

        # 6. Map Summary
        summary = OptimizationSummarySchema(
            total_cost=res.summary.objective_value,
            total_fuel_consumed_liters=res.summary.total_fuel_consumed_liters,
            total_unserved_load_kwh=res.summary.total_critical_unserved_kwh + res.summary.total_noncritical_unserved_kwh,
            total_critical_unserved_kwh=res.summary.total_critical_unserved_kwh,
            total_curtailed_renewable_kwh=res.summary.total_renewable_curtailment_kwh,
            min_reserve_margin_pct=res.summary.min_reserve_margin_pct,
            final_battery_soc_pct=res.summary.final_battery_soc_pct,
            final_fuel_remaining_liters=res.summary.final_fuel_remaining_liters,
            min_indoor_temp_c=res.summary.min_indoor_temp_c
        )

        # 7. Map Schedule if requested
        schedule_list = None
        gen_schedules = None
        if req.include_schedule and res.decision_schedule:
            schedule_list = [
                DecisionStepSchema(
                    t=step.horizon_h,
                    timestamp=step.timestamp,
                    p_diesel_kw=step.diesel_total_kw,
                    p_battery_charge_kw=step.battery_charge_kw,
                    p_battery_discharge_kw=step.battery_discharge_kw,
                    p_solar_kw=step.solar_generation_kw,
                    p_wind_kw=step.wind_generation_kw,
                    p_served_load_kw=step.load_served_kw,
                    p_unserved_load_kw=step.load_unserved_kw,
                    battery_soc=step.battery_soc_pct,
                    fuel_remaining_l=step.fuel_remaining_liters,
                    indoor_temp_c=step.indoor_temp_c,
                    reserve_margin_pct=step.reserve_margin_pct
                )
                for step in res.decision_schedule
            ]
            gen_schedules = {
                step.horizon_h: [asdict(gs) for gs in step.generator_schedules]
                for step in res.decision_schedule
            }

        mode_str = res.optimization_mode.value if hasattr(res.optimization_mode, "value") else str(res.optimization_mode)
        solver_status_str = res.solver_status.value if hasattr(res.solver_status, "value") else str(res.solver_status)

        return OptimizeResponseData(
            station_id=res.station_id,
            horizon_hours=res.horizon_hours,
            mode=mode_str,
            solver_status=solver_status_str,
            optimality_tier=tier,
            objective_value=res.summary.objective_value,
            best_bound=res.best_bound,
            relative_gap=res.relative_mip_gap,
            solve_time_sec=round(res.solver_time_seconds, 3),
            is_valid=res.is_valid,
            twin_replay_valid=res.is_valid,
            summary=summary,
            schedule=schedule_list,
            generator_schedules=gen_schedules,
            provenance="SIMULATED",
            diagnostics=res.validation_messages
        )
