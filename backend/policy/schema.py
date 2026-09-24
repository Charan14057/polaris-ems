"""
POLARIS-EMS — Policy Engine Contracts & Schemas
SIH26061: Polar Energy Management & Resilience System

Provides strongly typed schemas for:
- Deterministic policy states, categories, actions, priorities, and validation tiers
- Explicit hysteresis state tracking
- Four-tier optimizer handoff classification
- Transparent, auditable PolicyDecision and PolicyDecisionTrace contracts
- Strict locked 6-tier provenance compliance
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum, IntEnum

from backend.optimizer.schema import OptimizationMode
from backend.resilience.schema import ResilienceStateEnum


class PolicyStateEnum(str, Enum):
    """Deterministic policy lifecycle state."""
    NO_ACTION = "NO_ACTION"
    MONITOR = "MONITOR"
    PREPARE = "PREPARE"
    MITIGATE = "MITIGATE"
    PROTECT = "PROTECT"
    RECOVER = "RECOVER"
    ESCALATE = "ESCALATE"
    BLOCKED = "BLOCKED"
    INVALID_INPUT = "INVALID_INPUT"


class PolicyCategoryEnum(str, Enum):
    """Authoritative policy functional families."""
    MONITORING = "MONITORING"
    PREPAREDNESS = "PREPAREDNESS"
    CRITICAL_LOAD_PROTECTION = "CRITICAL_LOAD_PROTECTION"
    STORAGE_PROTECTION = "STORAGE_PROTECTION"
    FUEL_PRESERVATION = "FUEL_PRESERVATION"
    THERMAL_PROTECTION = "THERMAL_PROTECTION"
    RESUPPLY_PROTECTION = "RESUPPLY_PROTECTION"
    RECOVERY = "RECOVERY"


class PolicyPriorityEnum(IntEnum):
    """
    Deterministic conflict resolution precedence.
    Lower numerical value indicates higher priority (1 = highest).
    """
    P1_CRITICAL_LIFE_SAFETY = 1
    P2_CRITICAL_LOAD_PROTECTION = 2
    P3_GENERATION_RESERVE_PROTECTION = 3
    P4_THERMAL_SAFETY = 4
    P5_FUEL_RESUPPLY_PROTECTION = 5
    P6_STORAGE_PROTECTION = 6
    P7_NONCRITICAL_OPTIMIZATION = 7
    P8_MONITORING = 8


class PolicyActionEnum(str, Enum):
    """
    Deterministic policy action directives.
    Represents internal policy decisions and optimizer requirement formulation ONLY.
    Strictly zero physical device or actuator control.
    """
    MONITOR_RESERVES = "MONITOR_RESERVES"
    MONITOR_FUEL_TRAJECTORY = "MONITOR_FUEL_TRAJECTORY"
    MONITOR_THERMAL_MARGIN = "MONITOR_THERMAL_MARGIN"
    MONITOR_RESUPPLY_EXPOSURE = "MONITOR_RESUPPLY_EXPOSURE"
    PREPARE_STANDBY_GENERATOR = "PREPARE_STANDBY_GENERATOR"
    PREPARE_LOAD_SHEDDING = "PREPARE_LOAD_SHEDDING"
    PREPARE_THERMAL_ENVELOPE = "PREPARE_THERMAL_ENVELOPE"
    PRESERVE_CRITICAL_LOADS = "PRESERVE_CRITICAL_LOADS"
    SHED_NONCRITICAL_LOADS = "SHED_NONCRITICAL_LOADS"
    BLOCK_DISCRETIONARY_LOADS = "BLOCK_DISCRETIONARY_LOADS"
    PRESERVE_MINIMUM_BATTERY_SOC = "PRESERVE_MINIMUM_BATTERY_SOC"
    THROTTLE_BATTERY_DISCHARGE = "THROTTLE_BATTERY_DISCHARGE"
    PRESERVE_EMERGENCY_FUEL = "PRESERVE_EMERGENCY_FUEL"
    CONSERVE_FUEL_UNTIL_RESUPPLY = "CONSERVE_FUEL_UNTIL_RESUPPLY"
    PROTECT_INDOOR_TEMPERATURE = "PROTECT_INDOOR_TEMPERATURE"
    PRIORITIZE_HEATING_POWER = "PRIORITIZE_HEATING_POWER"
    ADOPT_STATION_RECOVERY_POSTURE = "ADOPT_STATION_RECOVERY_POSTURE"
    RESTORE_STORAGE_RESERVES = "RESTORE_STORAGE_RESERVES"
    RETURN_TO_NORMAL_DISPATCH = "RETURN_TO_NORMAL_DISPATCH"


class PolicyValidationStatusEnum(str, Enum):
    """Deterministic validation and eligibility state."""
    VALID = "VALID"
    ADVISORY = "ADVISORY"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    INPUT_INVALID = "INPUT_INVALID"
    UPSTREAM_INVALID = "UPSTREAM_INVALID"
    REQUIRES_OPTIMIZATION = "REQUIRES_OPTIMIZATION"


class HandoffEnforcementTierEnum(str, Enum):
    """
    Four-tier field classification for Phase 6 Optimizer handoffs.
    Guarantees that requirements not directly supported by Phase 6 are never falsely claimed as enforced.
    """
    DIRECTLY_SUPPORTED = "DIRECTLY_SUPPORTED"                      # Native parameter in OptimizerEngine.optimize()
    DERIVED_FROM_SUPPORTED_INPUT = "DERIVED_FROM_SUPPORTED_INPUT"  # Induced via native mode (e.g. CONSERVATIVE)
    DECLARATIVE_ONLY = "DECLARATIVE_ONLY"                          # Desired target; not a native constraint
    REQUIRES_OPTIMIZATION = "REQUIRES_OPTIMIZATION"                # Requires re-solving through Phase 6


@dataclass
class HysteresisState:
    """
    Explicit, stateful anti-churn and deadband tracking.
    Must be passed into and returned from evaluate_policy to guarantee mathematical determinism.
    """
    active_policy_states: Dict[str, str] = field(default_factory=dict)
    consecutive_steps: Dict[str, int] = field(default_factory=dict)
    last_switch_timestep: Dict[str, str] = field(default_factory=dict)
    deadbands: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyCondition:
    """Evaluated measurable physical condition."""
    condition_name: str
    threshold_field: str
    operator: str
    threshold_value: Any
    observed_value: Any
    satisfied: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizerHandoffRequirements:
    """
    Structured handoff contract from Phase 8 Policy to Phase 6 Optimizer.
    Strictly preserves distinction between:
    1. Requested policy constraint
    2. Optimizer-enforced constraint (DIRECTLY_SUPPORTED or DERIVED)
    3. Post-replay validated outcome (via Phase 4 Twin replay)
    """
    recommended_mode: OptimizationMode = OptimizationMode.EXPECTED
    generator_overrides: Optional[Dict[int, str]] = None
    target_scenario_id: Optional[str] = None
    min_operating_reserve_pct: Optional[float] = None
    min_terminal_soc_pct: Optional[float] = None
    min_terminal_fuel_liters: Optional[float] = None
    shed_noncritical_load_allowed: bool = False
    protect_heating_demand: bool = False
    enforcement_tiers: Dict[str, str] = field(default_factory=dict)
    requested_constraints: Dict[str, Any] = field(default_factory=dict)
    optimizer_enforced_constraints: Dict[str, Any] = field(default_factory=dict)
    post_replay_validated_outcomes: Dict[str, Any] = field(default_factory=dict)
    handoff_status: PolicyValidationStatusEnum = PolicyValidationStatusEnum.ADVISORY
    advisory_rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommended_mode": self.recommended_mode.value if isinstance(self.recommended_mode, OptimizationMode) else str(self.recommended_mode),
            "generator_overrides": self.generator_overrides,
            "target_scenario_id": self.target_scenario_id,
            "min_operating_reserve_pct": self.min_operating_reserve_pct,
            "min_terminal_soc_pct": self.min_terminal_soc_pct,
            "min_terminal_fuel_liters": self.min_terminal_fuel_liters,
            "shed_noncritical_load_allowed": self.shed_noncritical_load_allowed,
            "protect_heating_demand": self.protect_heating_demand,
            "enforcement_tiers": self.enforcement_tiers,
            "requested_constraints": self.requested_constraints,
            "optimizer_enforced_constraints": self.optimizer_enforced_constraints,
            "post_replay_validated_outcomes": self.post_replay_validated_outcomes,
            "handoff_status": self.handoff_status.value if isinstance(self.handoff_status, PolicyValidationStatusEnum) else str(self.handoff_status),
            "advisory_rationale": self.advisory_rationale
        }


@dataclass
class PolicyDecision:
    """Individual evaluated policy directive with full condition lineage."""
    rule_id: str
    policy_category: PolicyCategoryEnum
    policy_state: PolicyStateEnum
    priority: PolicyPriorityEnum
    action: PolicyActionEnum
    reason: str
    conditions_met: List[PolicyCondition] = field(default_factory=list)
    expected_effect: str = ""
    validation_status: PolicyValidationStatusEnum = PolicyValidationStatusEnum.APPROVED
    is_active: bool = True
    is_suppressed: bool = False
    suppressed_by: Optional[str] = None
    optimizer_handoff: Optional[OptimizerHandoffRequirements] = None
    provenance: str = "SIMULATED"
    rule_source: str = "policy_rules.json"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "policy_category": self.policy_category.value,
            "policy_state": self.policy_state.value,
            "priority": self.priority.value,
            "action": self.action.value,
            "reason": self.reason,
            "conditions_met": [c.to_dict() for c in self.conditions_met],
            "expected_effect": self.expected_effect,
            "validation_status": self.validation_status.value,
            "is_active": self.is_active,
            "is_suppressed": self.is_suppressed,
            "suppressed_by": self.suppressed_by,
            "optimizer_handoff": self.optimizer_handoff.to_dict() if self.optimizer_handoff else None,
            "provenance": self.provenance,
            "rule_source": self.rule_source
        }


@dataclass
class PolicyDecisionTrace:
    """Master auditable decision trace output of the Polaris-EMS Policy Engine."""
    policy_run_id: str
    station_id: str
    timestamp: str
    horizon_hours: int
    resilience_state: ResilienceStateEnum
    policy_state: PolicyStateEnum
    primary_policy: Optional[PolicyDecision] = None
    active_policies: List[PolicyDecision] = field(default_factory=list)
    suppressed_policies: List[PolicyDecision] = field(default_factory=list)
    evaluation_trace: List[str] = field(default_factory=list)
    optimizer_handoff: Optional[OptimizerHandoffRequirements] = None
    hysteresis_state: Optional[HysteresisState] = None
    validation_status: PolicyValidationStatusEnum = PolicyValidationStatusEnum.VALID
    provenance: str = "SIMULATED"
    source_phase: str = "Phase7"
    diagnostics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_run_id": self.policy_run_id,
            "station_id": self.station_id,
            "timestamp": self.timestamp,
            "horizon_hours": self.horizon_hours,
            "resilience_state": self.resilience_state.value if isinstance(self.resilience_state, ResilienceStateEnum) else str(self.resilience_state),
            "policy_state": self.policy_state.value if isinstance(self.policy_state, PolicyStateEnum) else str(self.policy_state),
            "primary_policy": self.primary_policy.to_dict() if self.primary_policy else None,
            "active_policies": [p.to_dict() for p in self.active_policies],
            "suppressed_policies": [p.to_dict() for p in self.suppressed_policies],
            "evaluation_trace": self.evaluation_trace,
            "optimizer_handoff": self.optimizer_handoff.to_dict() if self.optimizer_handoff else None,
            "hysteresis_state": self.hysteresis_state.to_dict() if self.hysteresis_state else None,
            "validation_status": self.validation_status.value if isinstance(self.validation_status, PolicyValidationStatusEnum) else str(self.validation_status),
            "provenance": self.provenance,
            "source_phase": self.source_phase,
            "diagnostics": self.diagnostics
        }
