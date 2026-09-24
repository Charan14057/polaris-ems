"""
POLARIS-EMS — API Schemas for Decision Trace & Explainability
SIH26061: Polar Energy Management & Resilience System
"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class TraceEventResponseSchema(BaseModel):
    event_id: str
    trace_id: str
    stage: str
    event_type: str
    timestamp: str
    station_id: str
    status: str
    reason_code: str
    summary: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    validation_tier: str
    provenance: str
    parent_event_id: Optional[str] = None
    duration_ms: float
    diagnostics: List[str] = Field(default_factory=list)


class DecisionExplanationResponseSchema(BaseModel):
    trace_id: str
    station_id: str
    headline: str
    why_this_state: str
    why_this_policy: str
    why_this_schedule: str
    what_data_used: List[str]
    what_was_validated: List[str]
    what_remains_estimated: List[str]
    what_is_next: str
    reason_codes: List[str]


class DecisionDeltaResponseSchema(BaseModel):
    base_trace_id: str
    compare_trace_id: str
    station_id: str
    state_transitions: Dict[str, List[str]]
    numerical_deltas: Dict[str, float]
    policy_directive_changed: bool
    edge_mode_changed: bool
    summary_narrative: str


class TraceSummaryResponseSchema(BaseModel):
    decision_trace_id: str
    station_id: str
    creation_timestamp: str
    completion_timestamp: Optional[str] = None
    execution_status: str
    stages_executed: List[str]
    horizon_hours: int
    scenario_id: Optional[str] = None
    optimization_mode: str
    primary_directive: Optional[str] = None
    policy_state: Optional[str] = None
    resilience_state: Optional[str] = None
    edge_mode: Optional[str] = None
    total_duration_ms: float
    provenance: str


class TraceDetailResponseSchema(BaseModel):
    decision_trace_id: str
    station_id: str
    pipeline_run_id: Optional[str] = None
    request_id: Optional[str] = None
    creation_timestamp: str
    completion_timestamp: Optional[str] = None
    execution_status: str
    horizon_hours: int
    scenario_id: Optional[str] = None
    optimization_mode: str
    primary_directive: Optional[str] = None
    policy_state: Optional[str] = None
    resilience_state: Optional[str] = None
    edge_mode: Optional[str] = None
    events: List[TraceEventResponseSchema]
    lineage_graph: Dict[str, List[str]]
    explanation: Optional[DecisionExplanationResponseSchema] = None
    provenance: str
    schema_version: str
