"""
POLARIS-EMS — Decision Trace & Audit Schemas
SIH26061: Polar Energy Management & Resilience System

Defines typed contracts for end-to-end auditability, event lineage, deterministic
machine-readable reason codes, and factual explainability across all operational phases.

STRICT INVARIANTS:
1. Locked 6-tier provenance: {REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED}.
2. Trace events are strictly observational; zero solver or simulation logic.
3. Reason codes and lifecycle states are operational labels, NEVER provenance tiers.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


# Locked 6-tier provenance taxonomy across Polaris-EMS
LOCKED_PROVENANCE_TIERS = {
    "REAL",
    "CONFIGURED",
    "ASSUMED",
    "SYNTHETIC",
    "FORECAST",
    "SIMULATED"
}


def validate_provenance_tier(v: str) -> str:
    v_upper = v.upper()
    if v_upper not in LOCKED_PROVENANCE_TIERS:
        raise ValueError(
            f"Provenance '{v}' violates the locked 6-tier taxonomy: {sorted(list(LOCKED_PROVENANCE_TIERS))}"
        )
    return v_upper


class TraceLifecycleState(str, Enum):
    """Deterministic lifecycle execution state of a decision trace."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    INFEASIBLE = "INFEASIBLE"
    FALLBACK = "FALLBACK"
    FAILED = "FAILED"


class TraceStage(str, Enum):
    """Explicit pipeline decision and operational stages."""
    EDGE = "EDGE"
    FORECAST = "FORECAST"
    SCENARIO = "SCENARIO"
    OPTIMIZER = "OPTIMIZER"
    TWIN_REPLAY = "TWIN_REPLAY"
    RESILIENCE = "RESILIENCE"
    POLICY = "POLICY"
    RECONCILIATION = "RECONCILIATION"


class ValidationTier(str, Enum):
    """Explicit epistemic validation state of evidence."""
    REQUESTED = "REQUESTED"
    COMPUTED = "COMPUTED"
    SIMULATED = "SIMULATED"
    VALIDATED = "VALIDATED"
    ESTIMATED = "ESTIMATED"
    ADVISORY = "ADVISORY"


class ReasonCode(str, Enum):
    """Deterministic machine-readable reason codes supporting factual explanations."""
    # Forecast
    FORECAST_AVAILABLE = "FORECAST_AVAILABLE"
    FORECAST_FAILED = "FORECAST_FAILED"
    # Scenario
    SCENARIO_BASELINE = "SCENARIO_BASELINE"
    SCENARIO_STRESS_APPLIED = "SCENARIO_STRESS_APPLIED"
    SCENARIO_FAILED = "SCENARIO_FAILED"
    # Optimizer
    OPTIMIZATION_EXACT = "OPTIMIZATION_EXACT"
    OPTIMIZATION_MIP_GAP = "OPTIMIZATION_MIP_GAP"
    OPTIMIZATION_FALLBACK = "OPTIMIZATION_FALLBACK"
    OPTIMIZATION_INFEASIBLE = "OPTIMIZATION_INFEASIBLE"
    OPTIMIZATION_FAILED = "OPTIMIZATION_FAILED"
    # Twin Replay
    TWIN_VALIDATED = "TWIN_VALIDATED"
    TWIN_VALIDATION_FAILED = "TWIN_VALIDATION_FAILED"
    TWIN_BYPASSED = "TWIN_BYPASSED"
    # Resilience
    RESILIENCE_SAFE = "RESILIENCE_SAFE"
    RESILIENCE_WATCH = "RESILIENCE_WATCH"
    RESILIENCE_AT_RISK = "RESILIENCE_AT_RISK"
    RESILIENCE_THREATENED = "RESILIENCE_THREATENED"
    RESILIENCE_CRITICAL = "RESILIENCE_CRITICAL"
    RECOVERY_PHYSICALLY_VALIDATED = "RECOVERY_PHYSICALLY_VALIDATED"
    RECOVERY_ESTIMATED = "RECOVERY_ESTIMATED"
    # Policy
    POLICY_NO_ACTION = "POLICY_NO_ACTION"
    POLICY_NOMINAL = "POLICY_NOMINAL"
    POLICY_MONITOR = "POLICY_MONITOR"
    POLICY_PREPARE = "POLICY_PREPARE"
    POLICY_MITIGATE = "POLICY_MITIGATE"
    POLICY_PROTECT = "POLICY_PROTECT"
    POLICY_RECOVER = "POLICY_RECOVER"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    CRITICAL_LOAD_PROTECTION = "CRITICAL_LOAD_PROTECTION"
    # Edge
    EDGE_CONNECTED = "EDGE_CONNECTED"
    CONNECTIVITY_DEGRADED = "CONNECTIVITY_DEGRADED"
    EDGE_OFFLINE = "EDGE_OFFLINE"
    FALLBACK_REQUIRED = "FALLBACK_REQUIRED"
    TELEMETRY_STALE = "TELEMETRY_STALE"
    RECONCILIATION_COMPLETED = "RECONCILIATION_COMPLETED"


class TraceEvent(BaseModel):
    """Atomic decision or validation event within an end-to-end pipeline trace."""
    event_id: str = Field(..., description="Unique event identifier")
    trace_id: str = Field(..., description="Parent decision trace ID")
    stage: TraceStage = Field(..., description="Pipeline execution stage")
    event_type: str = Field(..., description="Domain event categorization")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    station_id: str = Field(..., description="Polar station identifier")
    status: str = Field(..., description="COMPLETED | PARTIAL | BLOCKED | FAILED | FALLBACK")
    reason_code: ReasonCode = Field(..., description="Machine-readable deterministic reason code")
    summary: str = Field(..., description="Factual, concise event summary")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Structured reference inputs")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Structured observed outputs")
    validation_tier: ValidationTier = Field(ValidationTier.SIMULATED)
    provenance: str = Field("SIMULATED", description="Locked 6-tier provenance value")
    parent_event_id: Optional[str] = Field(None, description="Preceding event ID in DAG lineage")
    request_id: Optional[str] = Field(None, description="Correlation HTTP request ID")
    duration_ms: float = Field(0.0, description="Stage execution duration in milliseconds")
    engine_version: str = Field("v1")
    schema_version: str = Field("1.0.0")
    diagnostics: List[str] = Field(default_factory=list)

    @field_validator("provenance")
    @classmethod
    def check_prov(cls, v: str) -> str:
        return validate_provenance_tier(v)


class TraceSummary(BaseModel):
    """Compact summary of a decision trace for indexing and lists."""
    decision_trace_id: str
    station_id: str
    creation_timestamp: str
    completion_timestamp: Optional[str] = None
    execution_status: TraceLifecycleState
    stages_executed: List[str] = Field(default_factory=list)
    horizon_hours: int
    scenario_id: Optional[str] = None
    optimization_mode: str
    primary_directive: Optional[str] = None
    policy_state: Optional[str] = None
    resilience_state: Optional[str] = None
    edge_mode: Optional[str] = None
    total_duration_ms: float = 0.0
    provenance: str = "SIMULATED"

    @field_validator("provenance")
    @classmethod
    def check_prov(cls, v: str) -> str:
        return validate_provenance_tier(v)


class DecisionExplanation(BaseModel):
    """Deterministic human-readable explanation derived from structured factual evidence."""
    trace_id: str
    station_id: str
    headline: str
    why_this_state: str
    why_this_policy: str
    why_this_schedule: str
    what_data_used: List[str] = Field(default_factory=list)
    what_was_validated: List[str] = Field(default_factory=list)
    what_remains_estimated: List[str] = Field(default_factory=list)
    what_is_next: str
    reason_codes: List[ReasonCode] = Field(default_factory=list)


class DecisionDelta(BaseModel):
    """Factual comparative delta between two decision traces."""
    base_trace_id: str
    compare_trace_id: str
    station_id: str
    state_transitions: Dict[str, Tuple[str, str]] = Field(default_factory=dict)
    numerical_deltas: Dict[str, float] = Field(default_factory=dict)
    policy_directive_changed: bool = False
    edge_mode_changed: bool = False
    summary_narrative: str


class TraceRecord(BaseModel):
    """Complete, auditable decision trace record containing full lineage and stage events."""
    decision_trace_id: str = Field(..., description="Unique globally identifiable trace ID")
    station_id: str = Field(..., description="Polar station identifier")
    pipeline_run_id: Optional[str] = None
    request_id: Optional[str] = None
    creation_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completion_timestamp: Optional[str] = None
    execution_status: TraceLifecycleState = TraceLifecycleState.CREATED
    horizon_hours: int = 48
    scenario_id: Optional[str] = None
    optimization_mode: str = "EXPECTED"
    primary_directive: Optional[str] = None
    policy_state: Optional[str] = None
    resilience_state: Optional[str] = None
    edge_mode: Optional[str] = None
    events: List[TraceEvent] = Field(default_factory=list)
    lineage_graph: Dict[str, List[str]] = Field(default_factory=dict, description="DAG adjacency: parent_event_id -> [child_event_ids]")
    explanation: Optional[DecisionExplanation] = None
    provenance: str = Field("SIMULATED", description="Locked 6-tier provenance value")
    schema_version: str = "1.0.0"

    @field_validator("provenance")
    @classmethod
    def check_prov(cls, v: str) -> str:
        return validate_provenance_tier(v)

    def to_summary(self) -> TraceSummary:
        """Derives compact TraceSummary for list displays."""
        dur = sum(e.duration_ms for e in self.events)
        stages = [e.stage.value for e in self.events]
        return TraceSummary(
            decision_trace_id=self.decision_trace_id,
            station_id=self.station_id,
            creation_timestamp=self.creation_timestamp,
            completion_timestamp=self.completion_timestamp,
            execution_status=self.execution_status,
            stages_executed=stages,
            horizon_hours=self.horizon_hours,
            scenario_id=self.scenario_id,
            optimization_mode=self.optimization_mode,
            primary_directive=self.primary_directive,
            policy_state=self.policy_state,
            resilience_state=self.resilience_state,
            edge_mode=self.edge_mode,
            total_duration_ms=dur,
            provenance=self.provenance
        )
