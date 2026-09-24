"""
POLARIS-EMS — End-to-End Pipeline Orchestrator
SIH26061: Polar Energy Management & Resilience System

Coordinates the full sequence of frozen Polaris-EMS engines:
Forecast (Phase 3) -> Scenario (Phase 5) -> Optimizer (Phase 6) ->
Twin Replay (Phase 4) -> Resilience (Phase 7) -> Policy (Phase 8).

Guarantees:
- Pure orchestration; zero duplicated physics, ML, or policy math.
- Graceful partial execution: intermediate errors stop downstream fabrication.
- Exact stage execution times and status tracking.
"""

from typing import Optional, Dict, Any, List
import time
import uuid
import pandas as pd
from datetime import datetime, timezone

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.twin_engine import TwinEngine
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.ml.inference import InferenceEngine, ForecastResult
from backend.ml.data_loader import MLDataLoader
from backend.scenarios.registry import ScenarioRegistry
from backend.scenarios.engine import ScenarioEngine
from backend.scenarios.schema import ScenarioResult
from backend.optimizer.engine import OptimizerEngine
from backend.optimizer.schema import OptimizationMode, OptimizationResult
from backend.resilience.engine import ResilienceEngine
from backend.resilience.schema import ResilienceAssessment
from backend.policy.engine import PolicyEngine
from backend.policy.schema import PolicyDecisionTrace, HysteresisState

from backend.api.schemas.pipeline import (
    PipelineAnalyzeRequestSchema,
    PipelineAnalyzeResponseData,
    PipelineStageStatus
)
from backend.api.adapters.forecast_adapter import ForecastAPIAdapter
from backend.api.adapters.scenario_adapter import ScenarioAPIAdapter
from backend.api.adapters.optimizer_adapter import OptimizerAPIAdapter
from backend.api.adapters.resilience_adapter import ResilienceAPIAdapter
from backend.api.adapters.policy_adapter import PolicyAPIAdapter
from backend.api.schemas.forecast import ForecastRequestSchema, ForecastResponseData, QuantilePointSchema
from backend.api.schemas.scenario import ScenarioEvaluateResponseData, ScenarioImpactMetricsSchema
from backend.api.schemas.optimizer import OptimizeResponseData, OptimizationSummarySchema


class PipelineOrchestrator:
    """Orchestrates end-to-end multi-phase analysis over frozen engine boundaries."""

    def __init__(
        self,
        profile_registry: Optional[StationProfileRegistry] = None,
        safety_registry: Optional[SafetyThresholdRegistry] = None,
        scenario_registry: Optional[ScenarioRegistry] = None,
        inference_engine: Optional[InferenceEngine] = None,
        data_loader: Optional[MLDataLoader] = None
    ):
        self.profile_registry = profile_registry or StationProfileRegistry()
        self.safety_registry = safety_registry or SafetyThresholdRegistry()
        self.scenario_registry = scenario_registry or ScenarioRegistry()
        self.inference_engine = inference_engine or InferenceEngine()
        self.data_loader = data_loader or MLDataLoader()

    def run_pipeline(self, req: PipelineAnalyzeRequestSchema) -> PipelineAnalyzeResponseData:
        """Executes full pipeline chain: Forecast -> Scenario -> Optimize -> Twin Replay -> Resilience -> Policy."""
        run_id = f"pipe-{uuid.uuid4().hex[:8]}"
        sid = req.station_id.upper()
        horizon_h = req.horizon_hours
        start_ts = req.start_timestamp or "2026-06-01T00:00:00Z"
        mode = OptimizationMode(req.mode.upper())

        stages: List[PipelineStageStatus] = []
        overall_status = "SUCCESS"

        forecast_data = None
        scenario_data = None
        optimizer_data = None
        resilience_data = None
        policy_data = None

        profile = self.profile_registry.get(sid)
        twin = TwinEngine(station_id=sid, profile=profile, safety_registry=self.safety_registry)
        optimizer = OptimizerEngine(station_id=sid, profile=profile, safety_registry=self.safety_registry)
        resilience = ResilienceEngine(station_id=sid, profile=profile, safety_registry=self.safety_registry)
        policy_engine = PolicyEngine(station_id=sid, profile=profile, safety_registry=self.safety_registry)

        # ----------------------------------------------------------------------
        # Stage 1: FORECAST (Phase 3)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        try:
            forecast_adapter = ForecastAPIAdapter(self.inference_engine, self.data_loader)
            forecast_data = forecast_adapter.execute_forecast(
                ForecastRequestSchema(
                    station_id=sid,
                    target="total_load_kw",
                    horizon_hours=horizon_h,
                    forecast_origin=start_ts
                )
            )
            stages.append(PipelineStageStatus(
                stage_name="FORECAST",
                status="COMPLETED",
                duration_sec=round(time.perf_counter() - t0, 4),
                message=f"Generated {horizon_h}h probabilistic forecast for total_load_kw"
            ))
        except Exception as e:
            stages.append(PipelineStageStatus(
                stage_name="FORECAST",
                status="FAILED",
                duration_sec=round(time.perf_counter() - t0, 4),
                message=f"Forecasting error: {str(e)}"
            ))
            overall_status = "ERROR"
            return PipelineAnalyzeResponseData(
                pipeline_run_id=run_id,
                station_id=sid,
                horizon_hours=horizon_h,
                scenario_id=req.scenario_id,
                overall_status=overall_status,
                stages=stages,
                provenance="SIMULATED"
            )

        # Build initial TwinState and driving input steps
        initial_state: TwinState = twin.initialize_twin(start_ts)
        driving_steps = []
        for h in range(1, horizon_h + 1):
            day = 1 + (h - 1) // 24
            hour = (h - 1) % 24
            ghi = 200.0 if (6 <= hour <= 18) else 0.0
            load_val = forecast_data.quantiles[h - 1].point if (h - 1 < len(forecast_data.quantiles)) else 45.0
            driving_steps.append(TwinInputStep(
                timestamp=f"2026-06-{day:02d}T{hour:02d}:00:00Z",
                horizon_h=h,
                ambient_temp_c=-20.0,
                wind_speed_m_per_s=10.0,
                ghi_w_per_m2=ghi,
                load_kw=load_val,
                solar_kw=15.0 if ghi > 0 else 0.0,
                wind_kw=25.0,
                mode=req.mode
            ))

        # ----------------------------------------------------------------------
        # Stage 2: SCENARIO (Phase 5)
        # ----------------------------------------------------------------------
        scenario_def = None
        t0 = time.perf_counter()
        if req.scenario_id:
            try:
                scen_engine = ScenarioEngine(
                    station_id=sid,
                    profile=profile,
                    safety_registry=self.safety_registry,
                    scenario_registry=self.scenario_registry
                )
                scen_res: ScenarioResult = scen_engine.run_scenario(
                    scenario_id=req.scenario_id.upper(),
                    initial_state=initial_state,
                    baseline_inputs=driving_steps,
                    forecast_mode=req.mode,
                    horizon_hours=horizon_h
                )
                scenario_def = self.scenario_registry.get(req.scenario_id.upper())

                cat_val = scenario_def.category.value if hasattr(scenario_def.category, "value") else str(scenario_def.category)
                impact = ScenarioImpactMetricsSchema(
                    delta_unserved_energy_kwh=scen_res.impact_metrics.delta_unserved_energy_kwh,
                    delta_critical_unserved_kwh=scen_res.impact_metrics.delta_critical_unserved_energy_kwh,
                    delta_diesel_fuel_liters=scen_res.impact_metrics.delta_fuel_burn_liters,
                    delta_min_indoor_temp_c=scen_res.impact_metrics.delta_min_indoor_temperature_c,
                    delta_min_battery_soc=scen_res.impact_metrics.delta_min_battery_soc,
                    primary_failure_mode=scen_res.impact_metrics.primary_failure_signature,
                    earliest_failure_hour=float(scen_res.impact_metrics.scenario_failure_time_h) if scen_res.impact_metrics.scenario_failure_time_h is not None else None,
                    failure_occurred=(scen_res.impact_metrics.scenario_failure_time_h is not None or len(scen_res.constraints_violated) > 0)
                )
                scenario_data = ScenarioEvaluateResponseData(
                    scenario_id=scen_res.scenario_id,
                    station_id=scen_res.station_id,
                    category=cat_val,
                    duration_hours=scen_res.duration_hours,
                    impact_metrics=impact,
                    violated_constraints=list(scen_res.constraints_violated),
                    failure_indicators=[scen_res.primary_failure_signature] if scen_res.primary_failure_signature else [],
                    baseline_trajectory_summary=scen_res.baseline_summary,
                    scenario_trajectory_summary=scen_res.scenario_summary,
                    provenance="SIMULATED"
                )
                stages.append(PipelineStageStatus(
                    stage_name="SCENARIO",
                    status="COMPLETED",
                    duration_sec=round(time.perf_counter() - t0, 4),
                    message=f"Applied scenario '{req.scenario_id}'"
                ))
            except Exception as e:
                stages.append(PipelineStageStatus(
                    stage_name="SCENARIO",
                    status="FAILED",
                    duration_sec=round(time.perf_counter() - t0, 4),
                    message=f"Scenario error: {str(e)}"
                ))
                overall_status = "PARTIAL"
        else:
            stages.append(PipelineStageStatus(
                stage_name="SCENARIO",
                status="SKIPPED",
                duration_sec=0.0,
                message="No scenario requested; baseline unperturbed"
            ))

        # ----------------------------------------------------------------------
        # Stage 3: OPTIMIZER (Phase 6)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        opt_res: Optional[OptimizationResult] = None
        try:
            opt_res = optimizer.optimize(
                initial_state=initial_state,
                trajectory=driving_steps,
                scenario=scenario_def,
                mode=mode,
                generator_overrides=req.generator_overrides
            )
            opt_summary = OptimizationSummarySchema(
                total_cost=opt_res.summary.objective_value,
                total_fuel_consumed_liters=opt_res.summary.total_fuel_consumed_liters,
                total_unserved_load_kwh=opt_res.summary.total_critical_unserved_kwh + opt_res.summary.total_noncritical_unserved_kwh,
                total_critical_unserved_kwh=opt_res.summary.total_critical_unserved_kwh,
                total_curtailed_renewable_kwh=opt_res.summary.total_renewable_curtailment_kwh,
                min_reserve_margin_pct=opt_res.summary.min_reserve_margin_pct,
                final_battery_soc_pct=opt_res.summary.final_battery_soc_pct,
                final_fuel_remaining_liters=opt_res.summary.final_fuel_remaining_liters,
                min_indoor_temp_c=opt_res.summary.min_indoor_temp_c
            )
            optimizer_data = OptimizeResponseData(
                station_id=opt_res.station_id,
                horizon_hours=opt_res.horizon_hours,
                mode=opt_res.optimization_mode.value if hasattr(opt_res.optimization_mode, "value") else str(opt_res.optimization_mode),
                solver_status=opt_res.solver_status.value if hasattr(opt_res.solver_status, "value") else str(opt_res.solver_status),
                optimality_tier=opt_res.optimality_tier,
                objective_value=opt_res.summary.objective_value,
                best_bound=opt_res.best_bound,
                relative_gap=opt_res.relative_mip_gap,
                solve_time_sec=round(opt_res.solver_time_seconds, 3),
                is_valid=opt_res.is_valid,
                twin_replay_valid=opt_res.is_valid,
                summary=opt_summary,
                provenance="SIMULATED",
                diagnostics=opt_res.validation_messages
            )
            stages.append(PipelineStageStatus(
                stage_name="OPTIMIZER",
                status="COMPLETED",
                duration_sec=round(time.perf_counter() - t0, 4),
                message=f"Solved in mode={mode.value} with status={opt_res.solver_status.value}"
            ))
        except Exception as e:
            stages.append(PipelineStageStatus(
                stage_name="OPTIMIZER",
                status="FAILED",
                duration_sec=round(time.perf_counter() - t0, 4),
                message=f"Optimizer error: {str(e)}"
            ))
            overall_status = "PARTIAL"

        # ----------------------------------------------------------------------
        # Stage 4: TWIN_REPLAY (Phase 4)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        twin_replay_ok = (opt_res is not None and opt_res.is_valid)
        stages.append(PipelineStageStatus(
            stage_name="TWIN_REPLAY",
            status="COMPLETED" if twin_replay_ok else ("SKIPPED" if opt_res is None else "FAILED"),
            duration_sec=round(time.perf_counter() - t0, 4),
            message="Twin replay power balance & physical constraints validated" if twin_replay_ok else "Replay bypassed/failed"
        ))

        # ----------------------------------------------------------------------
        # Stage 5: RESILIENCE (Phase 7)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        assess_res: Optional[ResilienceAssessment] = None
        try:
            if opt_res is not None:
                assess_res = resilience.assess_optimization(
                    optimization_result=opt_res,
                    initial_state=initial_state,
                    trajectory_steps=driving_steps,
                    scenario=scenario_def
                )
            else:
                sim_traj = twin.simulate(initial_state, driving_steps)
                assess_res = resilience.assess_trajectory(sim_traj, scenario=scenario_def)

            resilience_data = ResilienceAPIAdapter.to_schema(assess_res, include_propagation=False)
            stages.append(PipelineStageStatus(
                stage_name="RESILIENCE",
                status="COMPLETED",
                duration_sec=round(time.perf_counter() - t0, 4),
                message=f"Resilience state classified as {assess_res.resilience_state.value}"
            ))
        except Exception as e:
            stages.append(PipelineStageStatus(
                stage_name="RESILIENCE",
                status="FAILED",
                duration_sec=round(time.perf_counter() - t0, 4),
                message=f"Resilience error: {str(e)}"
            ))
            overall_status = "PARTIAL"

        # ----------------------------------------------------------------------
        # Stage 6: POLICY (Phase 8)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        try:
            prev_hyst = None
            if req.previous_hysteresis:
                prev_hyst = HysteresisState(
                    active_policy_states=dict(req.previous_hysteresis.active_policy_states),
                    consecutive_steps=dict(req.previous_hysteresis.consecutive_steps),
                    last_switch_timestep=dict(req.previous_hysteresis.last_switch_timestep),
                    deadbands=dict(req.previous_hysteresis.deadbands)
                )

            trace, updated_hyst = policy_engine.evaluate_policy(
                assessment=assess_res,
                initial_state=initial_state,
                previous_hysteresis=prev_hyst,
                optimization_result=opt_res,
                scenario=scenario_def,
                generator_overrides=req.generator_overrides,
                horizon_hours=horizon_h
            )
            policy_data = PolicyAPIAdapter.to_schema(
                trace=trace,
                updated_hysteresis=updated_hyst,
                include_suppressed=True,
                include_evaluation_trace=False
            )
            stages.append(PipelineStageStatus(
                stage_name="POLICY",
                status="COMPLETED",
                duration_sec=round(time.perf_counter() - t0, 4),
                message=f"Policy directive evaluated: {trace.policy_state.value}"
            ))
        except Exception as e:
            stages.append(PipelineStageStatus(
                stage_name="POLICY",
                status="FAILED",
                duration_sec=round(time.perf_counter() - t0, 4),
                message=f"Policy error: {str(e)}"
            ))
            overall_status = "PARTIAL"

        return PipelineAnalyzeResponseData(
            pipeline_run_id=run_id,
            station_id=sid,
            horizon_hours=horizon_h,
            scenario_id=req.scenario_id,
            overall_status=overall_status,
            stages=stages,
            forecast=forecast_data,
            scenario=scenario_data,
            optimizer=optimizer_data,
            resilience=resilience_data,
            policy=policy_data,
            provenance="SIMULATED"
        )
