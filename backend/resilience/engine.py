"""
POLARIS-EMS — Resilience Engine (Phase 7 Orchestrator)
SIH26061: Polar Energy Management & Resilience System

The authoritative Resilience Intelligence layer for polar research stations:
Predict (Phase 3) -> Simulate (Phase 4) -> Stress Test (Phase 5) -> Optimize (Phase 6) -> Assess Resilience (Phase 7)

Answers the central operational question:
“Given the predicted future, current Digital Twin state, tested environmental/logistical threats,
and the optimized dispatch plan, how resilient is the station, what failure progression is likely,
how much survivability remains, and what recovery/mitigation pathways are available?”

Strict Architectural Invariants Enforced:
1. Zero physics recalculation (Digital Twin is the sole physical authority).
2. Zero second optimizer (Phase 6 is the sole dispatch optimizer).
3. Deterministic state classification (CRITICAL > THREATENED > AT_RISK > WATCH > RECOVERY > SAFE).
4. History-aware RECOVERY state machine.
5. Never confuses NO_DATA / INPUT_INVALID with CRITICAL station failure.
6. Multi-horizon support (48h operational and 168h strategic).
7. Candidate recovery options are strictly advisory with zero policy execution.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from backend.twin.state import TwinState
from backend.twin.twin_engine import TwinTrajectory, TwinEngine
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.forecast_adapter import TwinInputStep
from backend.data.station_profiles.loader import StationProfileRegistry, StationProfile
from backend.scenarios.schema import ScenarioDefinition
from backend.optimizer.schema import OptimizationResult

from backend.resilience.schema import (
    ResilienceAssessment,
    ResilienceStateEnum,
    AssessmentStatusEnum,
    SurvivalHorizons,
    TimeToThreat,
    CounterfactualResilienceComparison
)
from backend.resilience.adapter import ResilienceDataAdapter, TrajectoryValidationResult
from backend.resilience.survival import SurvivalCalculator
from backend.resilience.metrics import ResilienceMetricsEngine
from backend.resilience.threats import ThreatAndStateMachine
from backend.resilience.propagation import FailurePropagationAnalyzer
from backend.resilience.recovery import RecoveryAdvisor
from backend.resilience.counterfactual import ResilienceCounterfactualEvaluator


class ResilienceEngine:
    """The central computational Resilience Assessment Engine for Polaris-EMS."""

    def __init__(
        self,
        station_id: str,
        profile: Optional[StationProfile] = None,
        safety_registry: Optional[SafetyThresholdRegistry] = None,
        twin: Optional[TwinEngine] = None,
        weights_path: Optional[Path] = None
    ):
        self.station_id = station_id.upper()

        if profile is None:
            registry = StationProfileRegistry()
            profile = registry.get(self.station_id)
        self.profile = profile

        if safety_registry is None:
            safety_registry = SafetyThresholdRegistry()
        self.safety_registry = safety_registry

        if twin is None:
            twin = TwinEngine(station_id=self.station_id, profile=self.profile, safety_registry=self.safety_registry)
        self.twin = twin

        # Initialize modular resilience subsystems
        self.survival_calc = SurvivalCalculator()
        self.metrics_engine = ResilienceMetricsEngine(self.profile, self.safety_registry, weights_path)
        self.threat_state_machine = ThreatAndStateMachine(self.profile, self.safety_registry)
        self.propagation_analyzer = FailurePropagationAnalyzer(self.profile, self.safety_registry)
        self.recovery_advisor = RecoveryAdvisor(self.profile)
        self.counterfactual_evaluator = ResilienceCounterfactualEvaluator()

    def assess_trajectory(
        self,
        trajectory: Any,
        scenario: Optional[ScenarioDefinition] = None,
        previous_state: Optional[ResilienceStateEnum] = None,
        horizon_hours: Optional[int] = None
    ) -> ResilienceAssessment:
        """
        Computes comprehensive resilience intelligence from a validated TwinTrajectory.
        Handles both 48h operational and 168h strategic horizons.
        """
        # 1. Ingest and Validate Trajectory (Guardrail 7)
        validation: TrajectoryValidationResult = ResilienceDataAdapter.validate_trajectory(
            trajectory, expected_station_id=self.station_id
        )

        if not validation.is_valid:
            # Safe diagnostic return; NEVER falsely tags corrupted/missing data as CRITICAL
            empty_survival = SurvivalHorizons(
                critical_load_survival_horizon_h=0.0,
                thermal_habitability_horizon_h=0.0,
                battery_endurance_horizon_h=0.0,
                fuel_endurance_horizon_h=0.0,
                dependable_generation_horizon_h=0.0,
                resupply_gap_survivability_h=0.0,
                overall_station_survival_horizon_h=0.0,
                binding_subsystem="NONE",
                survives_full_horizon=False
            )
            return ResilienceAssessment(
                station_id=validation.station_id,
                assessment_timestamp="UNKNOWN",
                horizon_hours=0,
                assessment_status=validation.status,
                resilience_state=ResilienceStateEnum.SAFE,  # Neutral default for unassessed state
                active_threat_states=[],
                survival_horizons=empty_survival,
                time_to_threat=TimeToThreat(),
                threat_decomposition=[],
                dimensions=None,
                provenance="ASSUMED",
                diagnostics=validation.errors
            )

        assert validation.trajectory is not None
        states = validation.trajectory.states

        # Bound trajectory if horizon_hours requested (Guardrail 9)
        if horizon_hours and 0 < horizon_hours < len(states):
            states = states[:horizon_hours]

        actual_horizon_h = len(states)
        timestamp_origin = states[0].timestamp if states else "UNKNOWN"

        # 2. Extract Safety Limits
        min_safe_temp = self.safety_registry.get_value(self.station_id, "indoor_min_safe_temp_c", default=12.0)
        fuel_reserve_l = self.safety_registry.get_value(self.station_id, "fuel_reserve_liters", default=25000.0)
        res_threat_pct = self.safety_registry.get_value(self.station_id, "reserve_margin_threatened_pct", default=15.0)
        bat_warn_soc = self.safety_registry.get_value(self.station_id, "battery_warning_soc", default=0.25)

        # 3. Calculate Subsystem Survival & Earliest Time-to-Threat (Guardrails 8 & 16)
        survival, time_to_threat = self.survival_calc.calculate_survival_and_timings(
            states=states,
            min_safe_temp=min_safe_temp,
            fuel_reserve_liters=fuel_reserve_l,
            reserve_threat_pct=res_threat_pct,
            battery_warning_soc=bat_warn_soc
        )

        # 4. Decompose Threats & Classify Deterministic State (Guardrails 4 & 6)
        threats = self.threat_state_machine.decompose_threats(states, scenario)
        res_state, active_states, recovery_dir = self.threat_state_machine.classify_state(
            states=states,
            survival=survival,
            threats=threats,
            previous_state=previous_state
        )

        # 5. Evaluate the 9 Observable Resilience Dimensions & Index (Guardrails 10 & 17)
        dimensions = self.metrics_engine.evaluate_dimensions(states)

        # 6. Trace Observed Failure Propagation Chain (Guardrail 15)
        propagation = self.propagation_analyzer.trace_propagation(states)

        # 7. Synthesize Candidate Recovery Intelligence (Guardrail 5)
        recovery_options = self.recovery_advisor.advise_recovery_options(states, survival, threats)

        # 8. Preserve Scenario Lineage (Guardrail 13)
        scenario_id = scenario.scenario_id if scenario else None
        scenario_lineage = None
        if scenario:
            scenario_lineage = {
                "name": scenario.name,
                "category": scenario.category.value if hasattr(scenario.category, "value") else str(scenario.category),
                "description": scenario.description,
                "transforms": [
                    {"parameter": pt.parameter, "operator": pt.operator.value if hasattr(pt.operator, "value") else str(pt.operator), "value": pt.value}
                    for pt in getattr(scenario, "transforms", [])
                ]
            }

        return ResilienceAssessment(
            station_id=self.station_id,
            assessment_timestamp=timestamp_origin,
            horizon_hours=actual_horizon_h,
            assessment_status=AssessmentStatusEnum.COMPLETED,
            resilience_state=res_state,
            active_threat_states=active_states,
            survival_horizons=survival,
            time_to_threat=time_to_threat,
            threat_decomposition=threats,
            dimensions=dimensions,
            failure_propagation=propagation,
            candidate_recovery_options=recovery_options,
            previous_resilience_state=previous_state,
            recovery_direction=recovery_dir,
            scenario_id=scenario_id,
            scenario_lineage=scenario_lineage,
            provenance="SIMULATED",
            diagnostics=[]
        )

    def assess_optimization(
        self,
        optimization_result: OptimizationResult,
        initial_state: TwinState,
        trajectory_steps: List[TwinInputStep],
        scenario: Optional[ScenarioDefinition] = None,
        previous_state: Optional[ResilienceStateEnum] = None
    ) -> ResilienceAssessment:
        """
        Replays candidate optimization decisions through the authoritative Phase 4 Digital Twin
        and executes physical resilience assessment.
        Preserves Guardrails 2 & 3: Twin is the physical authority, Phase 6 is the optimizer.
        """
        validation = ResilienceDataAdapter.replay_optimization_result_through_twin(
            optimization_result=optimization_result,
            initial_state=initial_state,
            trajectory_steps=trajectory_steps,
            twin=self.twin
        )

        if not validation.is_valid or validation.trajectory is None:
            empty_survival = SurvivalHorizons(
                critical_load_survival_horizon_h=0.0,
                thermal_habitability_horizon_h=0.0,
                battery_endurance_horizon_h=0.0,
                fuel_endurance_horizon_h=0.0,
                dependable_generation_horizon_h=0.0,
                resupply_gap_survivability_h=0.0,
                overall_station_survival_horizon_h=0.0,
                binding_subsystem="NONE",
                survives_full_horizon=False
            )
            return ResilienceAssessment(
                station_id=self.station_id,
                assessment_timestamp=initial_state.timestamp,
                horizon_hours=len(trajectory_steps),
                assessment_status=validation.status,
                resilience_state=ResilienceStateEnum.SAFE,
                active_threat_states=[],
                survival_horizons=empty_survival,
                time_to_threat=TimeToThreat(),
                threat_decomposition=[],
                dimensions=None,
                provenance="SIMULATED",
                diagnostics=["source=Phase6Optimizer"] + validation.errors
            )

        assessment = self.assess_trajectory(
            trajectory=validation.trajectory,
            scenario=scenario,
            previous_state=previous_state,
            horizon_hours=len(trajectory_steps)
        )
        assessment.provenance = "SIMULATED"
        assessment.diagnostics.append("source=Phase6Optimizer")
        if validation.errors:
            assessment.diagnostics.extend(validation.errors)

        return assessment

    def compare_dispatch_resilience(
        self,
        baseline_traj: TwinTrajectory,
        optimized_result: OptimizationResult,
        initial_state: TwinState,
        trajectory_steps: List[TwinInputStep],
        scenario: Optional[ScenarioDefinition] = None
    ) -> CounterfactualResilienceComparison:
        """
        Compares resilience metrics between Baseline and Optimized dispatch.
        Guarantees Guardrail 14: Factual comparison with wear-proxy terminology.
        """
        base_assess = self.assess_trajectory(baseline_traj, scenario=scenario)
        opt_assess = self.assess_optimization(optimized_result, initial_state, trajectory_steps, scenario=scenario)
        return self.counterfactual_evaluator.compare_assessments(
            baseline=base_assess,
            counterfactual=opt_assess,
            comparison_name="BASELINE_VS_OPTIMIZED"
        )

    def compare_scenarios_resilience(
        self,
        nominal_traj: TwinTrajectory,
        stressed_traj: TwinTrajectory,
        scenario: ScenarioDefinition
    ) -> CounterfactualResilienceComparison:
        """
        Compares resilience metrics between Nominal Baseline and Stressed Scenario.
        """
        nom_assess = self.assess_trajectory(nominal_traj)
        stress_assess = self.assess_trajectory(stressed_traj, scenario=scenario)
        return self.counterfactual_evaluator.compare_assessments(
            baseline=nom_assess,
            counterfactual=stress_assess,
            comparison_name=f"NOMINAL_VS_{scenario.scenario_id}"
        )
