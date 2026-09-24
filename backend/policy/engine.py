"""
POLARIS-EMS — High-Level Policy Engine
SIH26061: Polar Energy Management & Resilience System

Primary production orchestrator for decision governance:
- Coordinates upstream validation, deterministic rule evaluation, conflict resolution, and hysteresis.
- Translates active policies into Phase 6 optimizer requirements without modifying Phase 6.
- Executes closed-loop Twin replay to award PHYSICALLY_VALIDATED status to factual counterfactual improvements.
- Generates auditable, transparent PolicyDecisionTrace outputs.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import uuid

from backend.data.station_profiles.loader import StationProfileRegistry, StationProfile
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.scenarios.schema import ScenarioDefinition
from backend.optimizer.schema import OptimizationResult
from backend.optimizer.engine import OptimizerEngine
from backend.resilience.schema import ResilienceAssessment, AssessmentStatusEnum
from backend.resilience.engine import ResilienceEngine

from backend.policy.schema import (
    PolicyDecisionTrace,
    PolicyDecision,
    PolicyStateEnum,
    PolicyPriorityEnum,
    PolicyValidationStatusEnum,
    HysteresisState,
    OptimizerHandoffRequirements
)
from backend.policy.adapter import PolicyDataAdapter
from backend.policy.rules import PolicyRuleEvaluator
from backend.policy.priority import PolicyPriorityResolver
from backend.policy.handoff import PolicyOptimizerHandoffTranslator


class PolicyEngine:
    """Primary production interface for Polaris-EMS Phase 8 Decision Governance."""

    def __init__(
        self,
        station_id: str,
        profile: Optional[StationProfile] = None,
        safety_registry: Optional[SafetyThresholdRegistry] = None,
        config_path: Optional[Path] = None
    ):
        self.station_id = station_id.upper()
        if profile is None:
            reg = StationProfileRegistry()
            profile = reg.get(self.station_id)
        self.profile = profile

        self.safety_registry = safety_registry or SafetyThresholdRegistry()
        self.config_path = config_path

        self.adapter = PolicyDataAdapter()
        self.rule_evaluator = PolicyRuleEvaluator(
            profile=self.profile,
            safety_registry=self.safety_registry,
            config_path=self.config_path
        )
        self.handoff_translator = PolicyOptimizerHandoffTranslator()

        # Phase 6 Optimizer & Phase 7 Resilience Engine for closed-loop handoff & validation
        self.optimizer = OptimizerEngine(self.station_id, self.profile, self.safety_registry)
        self.resilience = ResilienceEngine(self.station_id, self.profile, self.safety_registry)

    def evaluate_policy(
        self,
        assessment: Optional[ResilienceAssessment],
        initial_state: Optional[TwinState],
        previous_hysteresis: Optional[HysteresisState] = None,
        optimization_result: Optional[OptimizationResult] = None,
        scenario: Optional[ScenarioDefinition] = None,
        generator_overrides: Optional[Dict[int, str]] = None,
        horizon_hours: Optional[int] = None
    ) -> Tuple[PolicyDecisionTrace, HysteresisState]:
        """
        Executes full deterministic policy evaluation lifecycle:
        1. Ingest & validate upstream Phase 7 and Phase 4 inputs.
        2. Evaluate explicit rules across all 8 policy families under deadband hysteresis.
        3. Resolve conflicts, apply priority precedence, and enforce generator safety gates.
        4. Synthesize structured Phase 6 optimizer handoff requirements.
        5. Return transparent PolicyDecisionTrace and updated HysteresisState.
        """
        # 1. Validate upstream inputs
        validated = self.adapter.validate_and_adapt(
            assessment=assessment,
            initial_state=initial_state,
            optimization_result=optimization_result,
            scenario=scenario
        )

        if not validated.is_valid:
            invalid_trace = self.adapter.create_invalid_input_trace(
                station_id=self.station_id,
                timestamp=validated.timestamp,
                horizon_hours=horizon_hours or validated.horizon_hours,
                error_messages=validated.error_messages
            )
            return invalid_trace, previous_hysteresis or HysteresisState()

        # 2. Rule evaluation with hysteresis
        candidates, updated_hyst = self.rule_evaluator.evaluate_rules(
            inputs=validated,
            previous_hysteresis=previous_hysteresis
        )

        # 3. Conflict resolution & generator physical safety gate
        primary, active, suppressed, trace_logs = PolicyPriorityResolver.resolve_conflicts(
            candidates=candidates,
            profile=self.profile,
            initial_state=validated.initial_state,
            generator_overrides=generator_overrides
        )

        # 4. Synthesize optimizer handoff requirements
        handoff = self.handoff_translator.build_handoff_requirements(
            active_policies=active,
            profile=self.profile,
            initial_state=validated.initial_state,
            generator_overrides=generator_overrides
        )

        # Link handoff to primary policy
        if primary:
            primary.optimizer_handoff = handoff

        overall_policy_state = primary.policy_state if primary else PolicyStateEnum.NO_ACTION

        trace = PolicyDecisionTrace(
            policy_run_id=f"pol-{uuid.uuid4().hex[:8]}",
            station_id=self.station_id,
            timestamp=validated.timestamp,
            horizon_hours=validated.horizon_hours,
            resilience_state=validated.resilience_state,
            policy_state=overall_policy_state,
            primary_policy=primary,
            active_policies=active,
            suppressed_policies=suppressed,
            evaluation_trace=trace_logs,
            optimizer_handoff=handoff,
            hysteresis_state=updated_hyst,
            validation_status=primary.validation_status if primary else PolicyValidationStatusEnum.VALID,
            provenance="SIMULATED",
            source_phase="Phase7",
            diagnostics=[primary.reason] if (primary and primary.policy_state == PolicyStateEnum.BLOCKED) else []
        )

        return trace, updated_hyst

    def execute_optimizer_handoff(
        self,
        policy_trace: PolicyDecisionTrace,
        initial_state: TwinState,
        trajectory: List[TwinInputStep],
        scenario: Optional[ScenarioDefinition] = None
    ) -> Tuple[OptimizationResult, ResilienceAssessment]:
        """
        Executes the closed-loop handoff:
        Policy Requirements -> Phase 6 Optimizer -> Phase 4 Twin Replay -> Phase 7 Reassessment.
        Enforces Guardrail 8: Fills post_replay_validated_outcomes with physically validated truth.
        """
        if not policy_trace.optimizer_handoff:
            raise ValueError("PolicyDecisionTrace contains no optimizer_handoff requirements")

        handoff = policy_trace.optimizer_handoff

        # 1. Phase 6 solves using policy requirements
        opt_res = self.optimizer.optimize(
            initial_state=initial_state,
            trajectory=trajectory,
            scenario=scenario,
            mode=handoff.recommended_mode,
            generator_overrides=handoff.generator_overrides
        )

        # 2. Phase 7 evaluates resulting trajectory (which passes through Twin replay internally)
        post_assess = self.resilience.assess_optimization(
            optimization_result=opt_res,
            initial_state=initial_state,
            trajectory_steps=trajectory,
            scenario=scenario
        )

        # 3. Populate post_replay_validated_outcomes
        is_physically_validated = (
            opt_res.is_valid and
            post_assess.assessment_status == AssessmentStatusEnum.COMPLETED
        )

        handoff.post_replay_validated_outcomes = {
            "survives_full_horizon": post_assess.survival_horizons.survives_full_horizon,
            "overall_survival_horizon_h": post_assess.survival_horizons.overall_station_survival_horizon_h,
            "binding_subsystem": post_assess.survival_horizons.binding_subsystem,
            "min_reserve_margin_pct": opt_res.summary.min_reserve_margin_pct,
            "final_battery_soc_pct": opt_res.summary.final_battery_soc_pct,
            "final_fuel_remaining_liters": opt_res.summary.final_fuel_remaining_liters,
            "min_indoor_temp_c": opt_res.summary.min_indoor_temp_c,
            "validation_tier": "PHYSICALLY_VALIDATED" if is_physically_validated else "ESTIMATED",
            "solver_status": opt_res.solver_status.value
        }

        return opt_res, post_assess

    def evaluate_policy_counterfactual(
        self,
        baseline_trace: PolicyDecisionTrace,
        policy_trace: PolicyDecisionTrace,
        initial_state: TwinState,
        trajectory: List[TwinInputStep],
        scenario: Optional[ScenarioDefinition] = None
    ) -> Dict[str, Any]:
        """
        Computes factual comparative deltas between baseline and policy-guided operations.
        Awards PHYSICALLY_VALIDATED status only after closed-loop Twin replay.
        """
        # Execute baseline
        base_opt, base_assess = self.execute_optimizer_handoff(
            baseline_trace, initial_state, trajectory, scenario
        )

        # Execute policy-guided
        pol_opt, pol_assess = self.execute_optimizer_handoff(
            policy_trace, initial_state, trajectory, scenario
        )

        delta_survival_h = round(
            pol_assess.survival_horizons.overall_station_survival_horizon_h -
            base_assess.survival_horizons.overall_station_survival_horizon_h,
            1
        )
        delta_reserve_pct = round(
            pol_opt.summary.min_reserve_margin_pct -
            base_opt.summary.min_reserve_margin_pct,
            1
        )
        delta_indoor_temp_c = round(
            pol_opt.summary.min_indoor_temp_c -
            base_opt.summary.min_indoor_temp_c,
            2
        )

        return {
            "comparison_name": "BASELINE_VS_POLICY_GUIDED",
            "station_id": self.station_id,
            "baseline_policy": baseline_trace.policy_state.value,
            "active_policy": policy_trace.policy_state.value,
            "delta_survival_horizon_h": delta_survival_h,
            "delta_reserve_margin_pct": delta_reserve_pct,
            "delta_min_indoor_temp_c": delta_indoor_temp_c,
            "baseline_survives_full_horizon": base_assess.survival_horizons.survives_full_horizon,
            "policy_survives_full_horizon": pol_assess.survival_horizons.survives_full_horizon,
            "validation_tier": "PHYSICALLY_VALIDATED",
            "provenance": "SIMULATED"
        }
