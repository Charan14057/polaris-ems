"""
POLARIS-EMS — Decision Trace Service & Coordinator
SIH26061: Polar Energy Management & Resilience System

Coordinates the construction, persistence, explanation, and auditing of
DecisionTrace records from end-to-end pipeline analysis runs.

STRICT INVARIANTS:
1. Zero solvers, physics equations, or policy modifications.
2. Purely observational audit layer over existing Phase 3–11 engines.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from backend.trace.schema import (
    TraceRecord,
    TraceSummary,
    TraceEvent,
    DecisionExplanation,
    DecisionDelta
)
from backend.trace.builder import TraceEventBuilder
from backend.trace.lineage import LineageGraphBuilder
from backend.trace.explainer import DeterministicExplainer
from backend.trace.repository import TraceRepository, get_trace_repository
from backend.edge.engine import get_edge_engine


class TraceService:
    """High-level service coordinating decision trace auditing and explainability."""

    def __init__(self, repository: Optional[TraceRepository] = None):
        self.repository = repository or get_trace_repository()

    def record_pipeline_run(
        self,
        station_id: str,
        pipeline_data: Any,
        request_schema: Optional[Any] = None,
        request_id: Optional[str] = None
    ) -> TraceRecord:
        """
        Observes a PipelineAnalyzeResponseData object and builds a complete,
        persisted TraceRecord with DAG lineage and deterministic explanations.
        """
        sid = station_id.upper()
        trace_id = TraceEventBuilder.generate_trace_id(sid)

        # 1. Fetch Edge Context (Phase 11)
        edge_snapshot = None
        try:
            edge_eng = get_edge_engine(sid)
            edge_snapshot = edge_eng.get_state()
        except Exception:
            pass

        events: List[TraceEvent] = []

        # Stage 0: Edge Context
        ev_edge = TraceEventBuilder.build_edge_event(
            trace_id=trace_id,
            station_id=sid,
            edge_snapshot=edge_snapshot,
            parent_event_id=None
        )
        events.append(ev_edge)
        prev_event_id = ev_edge.event_id

        # Stages duration mapping from pipeline_data.stages
        durations: Dict[str, float] = {}
        for stg in getattr(pipeline_data, "stages", []):
            durations[stg.stage_name] = stg.duration_sec * 1000.0

        # Stage 1: Forecast (Phase 3)
        ev_fc = TraceEventBuilder.build_forecast_event(
            trace_id=trace_id,
            station_id=sid,
            forecast_data=getattr(pipeline_data, "forecast", None),
            horizon_hours=getattr(pipeline_data, "horizon_hours", 48),
            duration_ms=durations.get("FORECAST", 0.0),
            parent_event_id=prev_event_id
        )
        events.append(ev_fc)
        prev_event_id = ev_fc.event_id

        # Stage 2: Scenario (Phase 5)
        ev_sc = TraceEventBuilder.build_scenario_event(
            trace_id=trace_id,
            station_id=sid,
            scenario_data=getattr(pipeline_data, "scenario", None),
            scenario_id=getattr(pipeline_data, "scenario_id", None),
            duration_ms=durations.get("SCENARIO", 0.0),
            parent_event_id=prev_event_id
        )
        events.append(ev_sc)
        prev_event_id = ev_sc.event_id

        # Stage 3: Optimizer (Phase 6)
        mode = getattr(request_schema, "mode", "EXPECTED") if request_schema else "EXPECTED"
        ev_opt = TraceEventBuilder.build_optimizer_event(
            trace_id=trace_id,
            station_id=sid,
            optimizer_data=getattr(pipeline_data, "optimizer", None),
            mode=mode,
            duration_ms=durations.get("OPTIMIZER", 0.0),
            parent_event_id=prev_event_id
        )
        events.append(ev_opt)
        prev_event_id = ev_opt.event_id

        # Stage 4: Twin Replay (Phase 4)
        ev_tw = TraceEventBuilder.build_twin_replay_event(
            trace_id=trace_id,
            station_id=sid,
            optimizer_data=getattr(pipeline_data, "optimizer", None),
            duration_ms=durations.get("TWIN_REPLAY", 0.0),
            parent_event_id=prev_event_id
        )
        events.append(ev_tw)
        prev_event_id = ev_tw.event_id

        # Stage 5: Resilience (Phase 7)
        ev_res = TraceEventBuilder.build_resilience_event(
            trace_id=trace_id,
            station_id=sid,
            resilience_data=getattr(pipeline_data, "resilience", None),
            duration_ms=durations.get("RESILIENCE", 0.0),
            parent_event_id=prev_event_id
        )
        events.append(ev_res)
        prev_event_id = ev_res.event_id

        # Stage 6: Policy (Phase 8)
        ev_pol = TraceEventBuilder.build_policy_event(
            trace_id=trace_id,
            station_id=sid,
            policy_data=getattr(pipeline_data, "policy", None),
            duration_ms=durations.get("POLICY", 0.0),
            parent_event_id=prev_event_id
        )
        events.append(ev_pol)

        # Assemble full TraceRecord
        record = LineageGraphBuilder.assemble_trace_record(
            decision_trace_id=trace_id,
            station_id=sid,
            events=events,
            pipeline_run_id=getattr(pipeline_data, "pipeline_run_id", None),
            request_id=request_id,
            horizon_hours=getattr(pipeline_data, "horizon_hours", 48),
            scenario_id=getattr(pipeline_data, "scenario_id", None),
            optimization_mode=mode
        )

        # Generate deterministic explanation
        record.explanation = DeterministicExplainer.explain(record)

        # Persist to repository
        self.repository.save_trace(record)

        return record

    def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        return self.repository.get_trace(trace_id)

    def list_traces(
        self,
        station_id: Optional[str] = None,
        status: Optional[str] = None,
        policy_state: Optional[str] = None,
        resilience_state: Optional[str] = None,
        limit: int = 50
    ) -> List[TraceSummary]:
        return self.repository.list_traces(
            station_id=station_id,
            status=status,
            policy_state=policy_state,
            resilience_state=resilience_state,
            limit=limit
        )

    def compare_traces(self, base_id: str, compare_id: str) -> DecisionDelta:
        return self.repository.compare(base_id, compare_id)

    def export_trace(self, trace_id: str, format_type: str = "json") -> str:
        if format_type.lower() == "csv":
            return self.repository.export_trace_csv(trace_id)
        return self.repository.export_trace_json(trace_id)


# Singleton TraceService provider
_trace_service: Optional[TraceService] = None


def get_trace_service() -> TraceService:
    global _trace_service
    if _trace_service is None:
        _trace_service = TraceService()
    return _trace_service
