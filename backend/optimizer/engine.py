"""
POLARIS-EMS — High-Level Optimizer Engine
SIH26061: Polar Energy Management & Resilience System

Coordinates model building, HiGHS solving, per-generator schedule validation,
Phase 4 Digital Twin replay, safe fallback handling, and counterfactual comparison.
"""

from typing import Dict, List, Optional, Any, Tuple
import uuid
from pathlib import Path

from backend.data.station_profiles.loader import StationProfileRegistry, StationProfile
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.twin_engine import TwinEngine, TwinTrajectory
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.scenarios.schema import ScenarioDefinition

from backend.optimizer.schema import (
    OptimizationResult,
    OptimizationMode,
    SolverStatus,
    DecisionStep,
    GeneratorScheduleStep,
    OptimizationSummary
)
from backend.optimizer.adapter import OptimizerDataAdapter, OptimizerModelInputs
from backend.optimizer.model import build_optimizer_model
from backend.optimizer.solver import OptimizerSolver
from backend.optimizer.generator_adapter import GeneratorReplayAdapter
from backend.optimizer.replay import TwinReplayValidator
from backend.optimizer.comparator import OptimizerComparator, CounterfactualComparison


class OptimizerEngine:
    """Primary production interface for multi-horizon risk-aware dispatch optimization."""

    def __init__(
        self,
        station_id: str,
        profile: Optional[StationProfile] = None,
        safety_registry: Optional[SafetyThresholdRegistry] = None,
        weights_path: Optional[Path] = None,
        solver_name: str = "appsi_highs",
        time_limit_sec: float = 120.0
    ):
        self.station_id = station_id.upper()
        if profile is None:
            reg = StationProfileRegistry()
            profile = reg.get(self.station_id)
        self.profile = profile

        self.safety_registry = safety_registry or SafetyThresholdRegistry()
        self.twin = TwinEngine(self.station_id, self.profile, self.safety_registry)

        self.adapter = OptimizerDataAdapter(
            weights_path=weights_path,
            safety_registry=self.safety_registry
        )
        self.solver = OptimizerSolver(
            solver_name=solver_name,
            time_limit_sec=time_limit_sec
        )

        # Per-generator adapter setup
        gen_count = int(self.profile.electrical.diesel_generator_count)
        gen_rated = float(self.profile.electrical.diesel_generator_kw_rated)
        min_load_pct = float(self.profile.electrical.diesel_min_loading_pct)
        self.generator_adapter = GeneratorReplayAdapter(
            generator_count=gen_count,
            rated_kw=gen_rated,
            min_loading_pct=min_load_pct
        )

        self.replay_validator = TwinReplayValidator(
            twin=self.twin,
            generator_adapter=self.generator_adapter
        )

    def optimize(
        self,
        initial_state: TwinState,
        trajectory: List[TwinInputStep],
        scenario: Optional[ScenarioDefinition] = None,
        mode: OptimizationMode = OptimizationMode.EXPECTED,
        generator_overrides: Optional[Dict[int, str]] = None
    ) -> OptimizationResult:
        """
        Executes full optimization lifecycle:
        1. Adapt inputs & synthesize effective resupply schedule
        2. Build Pyomo MILP model with terminal protection
        3. Solve via HiGHS
        4. Validate per-generator decisions & replay through Digital Twin
        5. Return validated OptimizationResult or safe fallback
        """
        run_id = f"opt-{uuid.uuid4().hex[:8]}"
        forecast_origin = trajectory[0].timestamp if trajectory else "T+0"
        horizon_hours = len(trajectory)
        scenario_id = scenario.scenario_id if scenario else "NORMAL_BASELINE"

        # 1. Adapt inputs
        inputs = self.adapter.adapt(
            profile=self.profile,
            initial_state=initial_state,
            trajectory=trajectory,
            scenario=scenario,
            mode=mode,
            generator_overrides=generator_overrides
        )

        # Update generator adapter with active availability
        self.generator_adapter.generator_availability = inputs.generator_availability

        # 2. Build model
        model = build_optimizer_model(inputs)

        # 3. Solve model
        status, solve_time, term_cond, dec_schedule, summary = self.solver.solve(model, inputs)

        # 4. Handle Infeasible or Error -> Safe Fallback
        if status in (SolverStatus.INFEASIBLE, SolverStatus.ERROR) or dec_schedule is None:
            return self._build_fallback_result(
                run_id=run_id,
                forecast_origin=forecast_origin,
                horizon_hours=horizon_hours,
                mode=mode,
                scenario_id=scenario_id,
                status=status,
                solve_time=solve_time,
                term_cond=term_cond,
                inputs=inputs,
                initial_state=initial_state,
                trajectory=trajectory,
                failure_reason=f"Solver returned {status.value}: {term_cond}"
            )

        # 5. Physical Twin Replay Validation
        is_valid, validation_msgs, replayed_traj = self.replay_validator.validate_and_replay(
            initial_state=initial_state,
            trajectory=trajectory,
            decision_schedule=dec_schedule
        )

        # Extract detailed solver optimality telemetry
        solve_info = getattr(self.solver, "last_solver_info", {})
        incumbent_obj = solve_info.get("incumbent_objective", summary.objective_value)
        best_bound = solve_info.get("best_bound")
        rel_gap = solve_info.get("relative_mip_gap")
        opt_tier = solve_info.get("optimality_tier", "MIP_GAP_OPTIMAL")

        return OptimizationResult(
            run_id=run_id,
            station_id=self.station_id,
            forecast_origin=forecast_origin,
            horizon_hours=horizon_hours,
            optimization_mode=mode,
            scenario_id=scenario_id,
            solver_status=status,
            solver_time_seconds=solve_time,
            solver_termination_condition=term_cond,
            is_valid=is_valid,
            validation_messages=validation_msgs,
            decision_schedule=dec_schedule,
            effective_resupply_schedule=inputs.effective_resupplies,
            summary=summary,
            fallback_used=False,
            incumbent_objective=incumbent_obj,
            best_bound=best_bound,
            relative_mip_gap=rel_gap,
            optimality_tier=opt_tier
        )

    def _build_fallback_result(
        self,
        run_id: str,
        forecast_origin: str,
        horizon_hours: int,
        mode: OptimizationMode,
        scenario_id: str,
        status: SolverStatus,
        solve_time: float,
        term_cond: str,
        inputs: OptimizerModelInputs,
        initial_state: TwinState,
        trajectory: List[TwinInputStep],
        failure_reason: str
    ) -> OptimizationResult:
        """Constructs safe baseline simulation fallback labeled FALLBACK — NOT OPTIMIZED."""
        base_traj = self.twin.simulate(initial_state, trajectory)
        b_sum = base_traj.summary

        # Convert baseline trajectory states into DecisionStep format
        fallback_steps: List[DecisionStep] = []
        gen_count = int(self.profile.electrical.diesel_generator_count)
        gen_rated = float(self.profile.electrical.diesel_generator_kw_rated)

        for t, s in enumerate(base_traj.states):
            is_on = (s.diesel.generator_status == "ONLINE")
            gen_schedules = [
                GeneratorScheduleStep(
                    generator_id=g,
                    is_online=(is_on and g == 1),
                    is_started=False,
                    is_stopped=False,
                    power_kw=s.diesel.generator_power_kw if g == 1 else 0.0,
                    rated_kw=gen_rated,
                    min_power_kw=gen_rated * float(self.profile.electrical.diesel_min_loading_pct)
                )
                for g in range(1, gen_count + 1)
            ]

            margin_pct = (s.resilience.dependable_reserve_kw / max(0.01, s.loads.total_load_kw)) * 100.0 if s.resilience else 0.0

            fallback_steps.append(DecisionStep(
                timestamp=s.timestamp,
                horizon_h=t + 1,
                diesel_total_kw=s.diesel.generator_power_kw,
                online_generator_count=1 if is_on else 0,
                generator_schedules=gen_schedules,
                battery_charge_kw=s.battery.charge_power_kw,
                battery_discharge_kw=s.battery.discharge_power_kw,
                battery_soc_pct=round(s.battery.soc_pct * 100.0, 2),
                battery_energy_kwh=round(s.battery.energy_kwh, 2),
                solar_generation_kw=s.solar.solar_generation_kw,
                solar_curtailed_kw=s.solar.solar_curtailed_kw,
                wind_generation_kw=s.wind.wind_generation_kw,
                wind_curtailed_kw=s.wind.wind_curtailed_kw,
                load_served_kw=s.loads.served_load_kw,
                load_unserved_kw=s.loads.unserved_load_kw,
                critical_served_kw=s.loads.served_critical_kw,
                critical_unserved_kw=s.loads.unserved_critical_kw,
                flexible_served_kw=0.0,
                heating_power_kw=s.loads.thermal_load_kw,
                indoor_temp_c=s.thermal.indoor_temp_c,
                fuel_burned_liters=s.diesel.fuel_consumption_l_per_h,
                fuel_remaining_liters=s.fuel.fuel_remaining_l,
                dependable_reserve_kw=s.resilience.dependable_reserve_kw if s.resilience else 0.0,
                reserve_margin_pct=round(margin_pct, 1)
            ))

        total_fuel = float(b_sum.get("total_fuel_burned_liters", 0.0))
        total_renew = sum(s.solar.solar_generation_kw + s.wind.wind_generation_kw for s in base_traj.states)
        total_curt = float(b_sum.get("total_curtailed_kwh", 0.0))
        avail = total_renew + total_curt
        util_pct = round((total_renew / max(0.01, avail)) * 100.0, 1)
        throughput = sum(s.battery.charge_power_kw + s.battery.discharge_power_kw for s in base_traj.states)

        fallback_summary = OptimizationSummary(
            total_fuel_consumed_liters=round(total_fuel, 2),
            final_fuel_remaining_liters=float(b_sum.get("final_fuel_remaining_liters", 0.0)),
            total_renewable_generation_kwh=round(total_renew, 2),
            total_renewable_curtailment_kwh=round(total_curt, 2),
            renewable_utilization_pct=util_pct,
            battery_throughput_kwh=round(throughput, 2),
            min_battery_soc_pct=round(min(s.battery.soc_pct * 100.0 for s in base_traj.states), 2),
            final_battery_soc_pct=round(float(b_sum.get("final_battery_soc", 0.0)) * 100.0, 2),
            total_critical_unserved_kwh=float(b_sum.get("total_critical_unserved_kwh", 0.0)),
            total_noncritical_unserved_kwh=float(b_sum.get("total_unserved_kwh", 0.0)),
            critical_survival_passed=(float(b_sum.get("total_critical_unserved_kwh", 0.0)) < 1e-4),
            total_generator_starts=1,
            total_generator_runtime_hours=float(len(base_traj.states)),
            min_indoor_temp_c=min(s.thermal.indoor_temp_c for s in base_traj.states),
            thermal_violation_degree_hours=0.0,
            min_reserve_margin_pct=0.0,
            objective_value=9999999.0
        )

        return OptimizationResult(
            run_id=run_id,
            station_id=self.station_id,
            forecast_origin=forecast_origin,
            horizon_hours=horizon_hours,
            optimization_mode=mode,
            scenario_id=scenario_id,
            solver_status=status,
            solver_time_seconds=solve_time,
            solver_termination_condition=term_cond,
            is_valid=False,
            validation_messages=[f"FALLBACK — NOT OPTIMIZED: {failure_reason}"],
            decision_schedule=fallback_steps,
            effective_resupply_schedule=inputs.effective_resupplies,
            summary=fallback_summary,
            fallback_used=True,
            optimality_tier="FALLBACK"
        )

    def compare_with_baseline(
        self,
        initial_state: TwinState,
        trajectory: List[TwinInputStep],
        optimized_result: OptimizationResult
    ) -> CounterfactualComparison:
        """Runs baseline dispatch simulation and computes exact counterfactual metrics."""
        baseline_traj = self.twin.simulate(initial_state, trajectory)
        return OptimizerComparator.compare(baseline_traj, optimized_result.summary)
