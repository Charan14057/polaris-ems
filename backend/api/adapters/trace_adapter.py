"""
POLARIS-EMS — API Adapter for Decision Trace Domain
SIH26061: Polar Energy Management & Resilience System
"""

from typing import List, Dict, Any

from backend.trace.schema import (
    TraceRecord,
    TraceEvent,
    TraceSummary,
    DecisionExplanation,
    DecisionDelta
)
from backend.api.schemas.trace import (
    TraceEventResponseSchema,
    TraceSummaryResponseSchema,
    DecisionExplanationResponseSchema,
    DecisionDeltaResponseSchema,
    TraceDetailResponseSchema
)


class TraceAPIAdapter:
    """Transforms domain trace entities into standardized API response models."""

    @staticmethod
    def to_event_schema(ev: TraceEvent) -> TraceEventResponseSchema:
        return TraceEventResponseSchema(
            event_id=ev.event_id,
            trace_id=ev.trace_id,
            stage=ev.stage.value,
            event_type=ev.event_type,
            timestamp=ev.timestamp,
            station_id=ev.station_id,
            status=ev.status,
            reason_code=ev.reason_code.value,
            summary=ev.summary,
            inputs=dict(ev.inputs),
            outputs=dict(ev.outputs),
            validation_tier=ev.validation_tier.value,
            provenance=ev.provenance,
            parent_event_id=ev.parent_event_id,
            duration_ms=ev.duration_ms,
            diagnostics=list(ev.diagnostics)
        )

    @staticmethod
    def to_explanation_schema(exp: DecisionExplanation) -> DecisionExplanationResponseSchema:
        return DecisionExplanationResponseSchema(
            trace_id=exp.trace_id,
            station_id=exp.station_id,
            headline=exp.headline,
            why_this_state=exp.why_this_state,
            why_this_policy=exp.why_this_policy,
            why_this_schedule=exp.why_this_schedule,
            what_data_used=list(exp.what_data_used),
            what_was_validated=list(exp.what_was_validated),
            what_remains_estimated=list(exp.what_remains_estimated),
            what_is_next=exp.what_is_next,
            reason_codes=[r.value for r in exp.reason_codes]
        )

    @staticmethod
    def to_delta_schema(delta: DecisionDelta) -> DecisionDeltaResponseSchema:
        transitions_map = {
            k: [v[0], v[1]] for k, v in delta.state_transitions.items()
        }
        return DecisionDeltaResponseSchema(
            base_trace_id=delta.base_trace_id,
            compare_trace_id=delta.compare_trace_id,
            station_id=delta.station_id,
            state_transitions=transitions_map,
            numerical_deltas=dict(delta.numerical_deltas),
            policy_directive_changed=delta.policy_directive_changed,
            edge_mode_changed=delta.edge_mode_changed,
            summary_narrative=delta.summary_narrative
        )

    @staticmethod
    def to_summary_schema(summary: TraceSummary) -> TraceSummaryResponseSchema:
        return TraceSummaryResponseSchema(
            decision_trace_id=summary.decision_trace_id,
            station_id=summary.station_id,
            creation_timestamp=summary.creation_timestamp,
            completion_timestamp=summary.completion_timestamp,
            execution_status=summary.execution_status.value,
            stages_executed=list(summary.stages_executed),
            horizon_hours=summary.horizon_hours,
            scenario_id=summary.scenario_id,
            optimization_mode=summary.optimization_mode,
            primary_directive=summary.primary_directive,
            policy_state=summary.policy_state,
            resilience_state=summary.resilience_state,
            edge_mode=summary.edge_mode,
            total_duration_ms=round(summary.total_duration_ms, 2),
            provenance=summary.provenance
        )

    @classmethod
    def to_detail_schema(cls, record: TraceRecord) -> TraceDetailResponseSchema:
        events = [cls.to_event_schema(e) for e in record.events]
        exp = cls.to_explanation_schema(record.explanation) if record.explanation else None
        return TraceDetailResponseSchema(
            decision_trace_id=record.decision_trace_id,
            station_id=record.station_id,
            pipeline_run_id=record.pipeline_run_id,
            request_id=record.request_id,
            creation_timestamp=record.creation_timestamp,
            completion_timestamp=record.completion_timestamp,
            execution_status=record.execution_status.value,
            horizon_hours=record.horizon_hours,
            scenario_id=record.scenario_id,
            optimization_mode=record.optimization_mode,
            primary_directive=record.primary_directive,
            policy_state=record.policy_state,
            resilience_state=record.resilience_state,
            edge_mode=record.edge_mode,
            events=events,
            lineage_graph=dict(record.lineage_graph),
            explanation=exp,
            provenance=record.provenance,
            schema_version=record.schema_version
        )
