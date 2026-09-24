"""
POLARIS-EMS — Policy API Schemas
SIH26061: Polar Energy Management & Resilience System

Typed schemas for Phase 8 Policy Engine endpoint:
- Exposes deterministic policy evaluation, 4-tier optimizer handoff requirements,
  stateful hysteresis tracking, and auditable decision trace lineage.
- Controls response size via include_suppressed and include_evaluation_trace flags.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PolicyConditionSchema(BaseModel):
    condition_name: str
    threshold_field: str
    operator: str
    threshold_value: Any
    observed_value: Any
    satisfied: bool


class PolicyDecisionSchema(BaseModel):
    rule_id: str
    policy_category: str
    policy_state: str
    priority: int
    action: str
    reason: str
    conditions_met: List[PolicyConditionSchema] = Field(default_factory=list)
    expected_effect: str = ""
    validation_status: str = "APPROVED"
    is_active: bool = True
    is_suppressed: bool = False
    suppressed_by: Optional[str] = None


class OptimizerHandoffRequirementsSchema(BaseModel):
    recommended_mode: str
    generator_overrides: Optional[Dict[int, str]] = None
    min_operating_reserve_pct: Optional[float] = None
    min_terminal_soc_pct: Optional[float] = None
    min_terminal_fuel_liters: Optional[float] = None
    shed_noncritical_load_allowed: bool = False
    protect_heating_demand: bool = False
    enforcement_tiers: Dict[str, str] = Field(default_factory=dict)
    requested_constraints: Dict[str, Any] = Field(default_factory=dict)
    optimizer_enforced_constraints: Dict[str, Any] = Field(default_factory=dict)
    handoff_status: str = "ADVISORY"
    advisory_rationale: str = ""


class HysteresisStateSchema(BaseModel):
    active_policy_states: Dict[str, str] = Field(default_factory=dict)
    consecutive_steps: Dict[str, int] = Field(default_factory=dict)
    last_switch_timestep: Dict[str, str] = Field(default_factory=dict)
    deadbands: Dict[str, float] = Field(default_factory=dict)


class PolicyEvaluateRequestSchema(BaseModel):
    """Request payload to evaluate deterministic policy rules."""
    station_id: str = Field(..., description="BHARATI | MAITRI | HIMADRI")
    horizon_hours: int = Field(48, ge=1, le=168, description="Horizon duration in hours (1-168)")
    scenario_id: Optional[str] = Field(None, description="Optional scenario ID from ScenarioRegistry")
    start_timestamp: Optional[str] = Field("2026-06-01T00:00:00Z", description="Starting observation timestamp")
    previous_hysteresis: Optional[HysteresisStateSchema] = Field(
        None, description="Optional previous hysteresis state for stateful anti-churn tracking"
    )
    generator_overrides: Optional[Dict[int, str]] = Field(None, description="e.g. {1: 'ONLINE', 2: 'FAULT'}")
    include_suppressed: bool = Field(True, description="Whether to include suppressed lower-priority policies")
    include_evaluation_trace: bool = Field(True, description="Whether to include step-by-step conflict resolution trace")

    @field_validator("station_id")
    @classmethod
    def validate_station(cls, v: str) -> str:
        s = v.upper()
        if s not in {"BHARATI", "MAITRI", "HIMADRI"}:
            raise ValueError(f"Station '{v}' is invalid")
        return s


class PolicyEvaluateResponseData(BaseModel):
    """Auditable policy evaluation output from Phase 8."""
    policy_run_id: str
    station_id: str
    timestamp: str
    horizon_hours: int
    resilience_state: str
    policy_state: str = Field(
        ...,
        description="NO_ACTION | MONITOR | PREPARE | MITIGATE | PROTECT | RECOVER | ESCALATE | BLOCKED | INVALID_INPUT"
    )
    primary_policy: Optional[PolicyDecisionSchema] = None
    active_policies: List[PolicyDecisionSchema] = Field(default_factory=list)
    suppressed_policies: Optional[List[PolicyDecisionSchema]] = None
    optimizer_handoff: Optional[OptimizerHandoffRequirementsSchema] = None
    hysteresis_state: Optional[HysteresisStateSchema] = None
    evaluation_trace: Optional[List[str]] = None
    validation_status: str
    provenance: str = "SIMULATED"
    diagnostics: List[str] = Field(default_factory=list)
