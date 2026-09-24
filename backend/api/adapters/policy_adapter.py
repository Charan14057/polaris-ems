"""
POLARIS-EMS — Policy API Adapter
SIH26061: Polar Energy Management & Resilience System

Translates API requests into calls to the Phase 8 PolicyEngine.
Evaluates deterministic policy rules, conflict resolution, 4-tier optimizer handoff,
and stateful hysteresis tracking.
"""

from typing import Optional, List, Dict, Any

from backend.policy.engine import PolicyEngine
from backend.policy.schema import PolicyDecisionTrace, PolicyDecision, HysteresisState
from backend.resilience.engine import ResilienceEngine
from backend.scenarios.registry import ScenarioRegistry
from backend.twin.twin_engine import TwinEngine
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.api.schemas.policy import (
    PolicyEvaluateRequestSchema,
    PolicyEvaluateResponseData,
    PolicyDecisionSchema,
    PolicyConditionSchema,
    OptimizerHandoffRequirementsSchema,
    HysteresisStateSchema
)
from backend.api.errors import InvalidRequestException, ScenarioNotFoundException


class PolicyAPIAdapter:
    """Adapts Phase 8 PolicyEngine to API presentation schemas."""

    def __init__(self, scenario_registry: Optional[ScenarioRegistry] = None):
        self.scenario_registry = scenario_registry or ScenarioRegistry()

    def evaluate_policy(
        self,
        req: PolicyEvaluateRequestSchema,
        policy_engine: PolicyEngine,
        resilience_engine: ResilienceEngine,
        twin: TwinEngine
    ) -> PolicyEvaluateResponseData:
        """Executes full policy evaluation from initial physical state and resilience assessment."""
        sid = req.station_id.upper()
        horizon_h = req.horizon_hours
        start_ts = req.start_timestamp or "2026-06-01T00:00:00Z"

        # 1. Initialize Authoritative Initial State from Twin
        initial_state: TwinState = twin.initialize_twin(start_ts)

        # 2. Resolve Scenario if requested
        scenario_def = None
        if req.scenario_id:
            try:
                scenario_def = self.scenario_registry.get(req.scenario_id.upper())
            except KeyError:
                raise ScenarioNotFoundException(req.scenario_id)

        # 3. Build Driving Baseline Steps
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
                mode="EXPECTED"
            ))

        # 4. Simulate Trajectory and Assess Resilience
        trajectory = twin.simulate(initial_state, trajectory_steps)
        assessment = resilience_engine.assess_trajectory(trajectory, scenario=scenario_def)

        # 5. Reconstruct Previous Hysteresis State if provided
        prev_hyst = None
        if req.previous_hysteresis:
            prev_hyst = HysteresisState(
                active_policy_states=dict(req.previous_hysteresis.active_policy_states),
                consecutive_steps=dict(req.previous_hysteresis.consecutive_steps),
                last_switch_timestep=dict(req.previous_hysteresis.last_switch_timestep),
                deadbands=dict(req.previous_hysteresis.deadbands)
            )

        # 6. Evaluate Policy
        try:
            trace, updated_hyst = policy_engine.evaluate_policy(
                assessment=assessment,
                initial_state=initial_state,
                previous_hysteresis=prev_hyst,
                scenario=scenario_def,
                generator_overrides=req.generator_overrides,
                horizon_hours=horizon_h
            )
        except Exception as e:
            raise InvalidRequestException(f"Policy evaluation failed: {str(e)}")

        return self.to_schema(
            trace=trace,
            updated_hysteresis=updated_hyst,
            include_suppressed=req.include_suppressed,
            include_evaluation_trace=req.include_evaluation_trace
        )

    @staticmethod
    def to_decision_schema(decision: PolicyDecision) -> PolicyDecisionSchema:
        """Maps a PolicyDecision dataclass to schema."""
        conds = [
            PolicyConditionSchema(
                condition_name=c.condition_name,
                threshold_field=c.threshold_field,
                operator=c.operator,
                threshold_value=c.threshold_value,
                observed_value=c.observed_value,
                satisfied=c.satisfied
            )
            for c in decision.conditions_met
        ]
        return PolicyDecisionSchema(
            rule_id=decision.rule_id,
            policy_category=decision.policy_category.value if hasattr(decision.policy_category, "value") else str(decision.policy_category),
            policy_state=decision.policy_state.value if hasattr(decision.policy_state, "value") else str(decision.policy_state),
            priority=int(decision.priority),
            action=decision.action.value if hasattr(decision.action, "value") else str(decision.action),
            reason=decision.reason,
            conditions_met=conds,
            expected_effect=decision.expected_effect,
            validation_status=decision.validation_status.value if hasattr(decision.validation_status, "value") else str(decision.validation_status),
            is_active=decision.is_active,
            is_suppressed=decision.is_suppressed,
            suppressed_by=decision.suppressed_by
        )

    @classmethod
    def to_schema(
        cls,
        trace: PolicyDecisionTrace,
        updated_hysteresis: Optional[HysteresisState] = None,
        include_suppressed: bool = True,
        include_evaluation_trace: bool = True
    ) -> PolicyEvaluateResponseData:
        """Converts PolicyDecisionTrace to API schema."""
        primary_schema = cls.to_decision_schema(trace.primary_policy) if trace.primary_policy else None
        active_schemas = [cls.to_decision_schema(p) for p in trace.active_policies]

        suppressed_schemas = None
        if include_suppressed and trace.suppressed_policies:
            suppressed_schemas = [cls.to_decision_schema(p) for p in trace.suppressed_policies]

        handoff_schema = None
        if trace.optimizer_handoff:
            ho = trace.optimizer_handoff
            handoff_schema = OptimizerHandoffRequirementsSchema(
                recommended_mode=ho.recommended_mode.value if hasattr(ho.recommended_mode, "value") else str(ho.recommended_mode),
                generator_overrides=ho.generator_overrides,
                min_operating_reserve_pct=ho.min_operating_reserve_pct,
                min_terminal_soc_pct=ho.min_terminal_soc_pct,
                min_terminal_fuel_liters=ho.min_terminal_fuel_liters,
                shed_noncritical_load_allowed=ho.shed_noncritical_load_allowed,
                protect_heating_demand=ho.protect_heating_demand,
                enforcement_tiers=ho.enforcement_tiers,
                requested_constraints=ho.requested_constraints,
                optimizer_enforced_constraints=ho.optimizer_enforced_constraints,
                handoff_status=ho.handoff_status.value if hasattr(ho.handoff_status, "value") else str(ho.handoff_status),
                advisory_rationale=ho.advisory_rationale
            )

        hyst_schema = None
        effective_hyst = updated_hysteresis or trace.hysteresis_state
        if effective_hyst:
            hyst_schema = HysteresisStateSchema(
                active_policy_states=effective_hyst.active_policy_states,
                consecutive_steps=effective_hyst.consecutive_steps,
                last_switch_timestep=effective_hyst.last_switch_timestep,
                deadbands=effective_hyst.deadbands
            )

        eval_trace = trace.evaluation_trace if include_evaluation_trace else None

        return PolicyEvaluateResponseData(
            policy_run_id=trace.policy_run_id,
            station_id=trace.station_id,
            timestamp=trace.timestamp,
            horizon_hours=trace.horizon_hours,
            resilience_state=trace.resilience_state.value if hasattr(trace.resilience_state, "value") else str(trace.resilience_state),
            policy_state=trace.policy_state.value if hasattr(trace.policy_state, "value") else str(trace.policy_state),
            primary_policy=primary_schema,
            active_policies=active_schemas,
            suppressed_policies=suppressed_schemas,
            optimizer_handoff=handoff_schema,
            hysteresis_state=hyst_schema,
            evaluation_trace=eval_trace,
            validation_status=trace.validation_status.value if hasattr(trace.validation_status, "value") else str(trace.validation_status),
            provenance="SIMULATED",
            diagnostics=trace.diagnostics
        )
