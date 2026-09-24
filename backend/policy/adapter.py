"""
POLARIS-EMS — Policy Upstream Ingestion & Validation Adapter
SIH26061: Polar Energy Management & Resilience System

Validates incoming Phase 7 ResilienceAssessment and Phase 4 TwinState data.
Enforces Guardrail 11:
- If upstream data is incomplete, corrupt, or invalid, returns structured INVALID_INPUT.
- Zero invented safety policies or hallucinations.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import uuid

from backend.twin.state import TwinState
from backend.scenarios.schema import ScenarioDefinition
from backend.optimizer.schema import OptimizationResult
from backend.resilience.schema import (
    ResilienceAssessment,
    AssessmentStatusEnum,
    ResilienceStateEnum,
    SurvivalHorizons,
    ThreatIndicator,
    ResilienceDimensions
)
from backend.policy.schema import (
    PolicyDecisionTrace,
    PolicyStateEnum,
    PolicyValidationStatusEnum
)


@dataclass
class ValidatedPolicyInputs:
    """Strongly validated container for policy evaluation."""
    is_valid: bool
    error_messages: List[str]
    station_id: str
    timestamp: str
    horizon_hours: int
    resilience_state: ResilienceStateEnum
    survival: Optional[SurvivalHorizons]
    threats: List[ThreatIndicator]
    dimensions: Optional[ResilienceDimensions]
    initial_state: Optional[TwinState]
    optimization_result: Optional[OptimizationResult]
    scenario: Optional[ScenarioDefinition]


class PolicyDataAdapter:
    """Validates upstream contracts and prepares normalized policy evaluation inputs."""

    @staticmethod
    def validate_and_adapt(
        assessment: Optional[ResilienceAssessment],
        initial_state: Optional[TwinState],
        optimization_result: Optional[OptimizationResult] = None,
        scenario: Optional[ScenarioDefinition] = None
    ) -> ValidatedPolicyInputs:
        """
        Validates completeness and integrity of incoming resilience assessment and physical state.
        """
        errors: List[str] = []

        if assessment is None:
            errors.append("ResilienceAssessment is None; upstream evaluation missing")
            return ValidatedPolicyInputs(
                is_valid=False,
                error_messages=errors,
                station_id="UNKNOWN",
                timestamp="UNKNOWN",
                horizon_hours=0,
                resilience_state=ResilienceStateEnum.SAFE,
                survival=None,
                threats=[],
                dimensions=None,
                initial_state=initial_state,
                optimization_result=optimization_result,
                scenario=scenario
            )

        # Check upstream assessment status
        if assessment.assessment_status in (AssessmentStatusEnum.INPUT_INVALID, AssessmentStatusEnum.INCOMPLETE):
            errors.append(f"Upstream assessment flagged as {assessment.assessment_status.value}")

        if assessment.survival_horizons is None:
            errors.append("ResilienceAssessment is missing required survival_horizons")

        # Validate initial state
        if initial_state is None:
            errors.append("Initial TwinState is None; cannot evaluate current physical conditions")
        else:
            if initial_state.thermal is None:
                errors.append("TwinState missing thermal subsystem")
            if initial_state.battery is None:
                errors.append("TwinState missing battery subsystem")
            if initial_state.diesel is None:
                errors.append("TwinState missing diesel subsystem")
            if initial_state.fuel is None:
                errors.append("TwinState missing fuel subsystem")
            if initial_state.loads is None:
                errors.append("TwinState missing loads subsystem")

        is_valid = len(errors) == 0
        return ValidatedPolicyInputs(
            is_valid=is_valid,
            error_messages=errors,
            station_id=assessment.station_id,
            timestamp=assessment.assessment_timestamp,
            horizon_hours=assessment.horizon_hours,
            resilience_state=assessment.resilience_state,
            survival=assessment.survival_horizons,
            threats=assessment.threat_decomposition,
            dimensions=assessment.dimensions,
            initial_state=initial_state,
            optimization_result=optimization_result,
            scenario=scenario
        )

    @staticmethod
    def create_invalid_input_trace(
        station_id: str,
        timestamp: str,
        horizon_hours: int,
        error_messages: List[str]
    ) -> PolicyDecisionTrace:
        """
        Produces an explicit, structured invalid input trace without hallucinating policies.
        """
        return PolicyDecisionTrace(
            policy_run_id=f"pol-invalid-{uuid.uuid4().hex[:8]}",
            station_id=station_id,
            timestamp=timestamp,
            horizon_hours=horizon_hours,
            resilience_state=ResilienceStateEnum.SAFE,
            policy_state=PolicyStateEnum.INVALID_INPUT,
            primary_policy=None,
            active_policies=[],
            suppressed_policies=[],
            evaluation_trace=["Upstream input validation failed; no policy evaluated"],
            optimizer_handoff=None,
            hysteresis_state=None,
            validation_status=PolicyValidationStatusEnum.UPSTREAM_INVALID,
            provenance="SIMULATED",
            source_phase="Phase7",
            diagnostics=error_messages
        )
