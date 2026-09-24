"""
POLARIS-EMS — Decision Trace Lineage Graph & Execution Paths
SIH26061: Polar Energy Management & Resilience System

Constructs and traverses directed acyclic graph (DAG) lineages connecting
causal stages from input telemetry through to final policy governance directives.

INVARIANTS:
- Lineage reflects true execution path only; does not fabricate unexecuted nodes.
- Explicitly flags stopping points when execution is blocked or failed.
"""

from typing import Dict, List, Optional
from backend.trace.schema import TraceEvent, TraceRecord


class LineageGraphBuilder:
    """Builds and analyzes DAG lineage representations of pipeline events."""

    @staticmethod
    def build_adjacency(events: List[TraceEvent]) -> Dict[str, List[str]]:
        """
        Constructs adjacency map: parent_event_id -> [child_event_ids].
        Root events (with parent_event_id=None) are tracked under key '__root__'.
        """
        adj: Dict[str, List[str]] = {"__root__": []}
        for ev in events:
            adj.setdefault(ev.event_id, [])
            if ev.parent_event_id is None:
                adj["__root__"].append(ev.event_id)
            else:
                adj.setdefault(ev.parent_event_id, []).append(ev.event_id)
        return adj

    @staticmethod
    def extract_execution_path(events: List[TraceEvent]) -> List[str]:
        """Returns ordered list of stage names executed in sequence."""
        return [f"{ev.stage.value} ({ev.status})" for ev in events]

    @staticmethod
    def identify_terminal_event(events: List[TraceEvent]) -> Optional[TraceEvent]:
        """Identifies the terminal decision event or point of failure/block."""
        if not events:
            return None
        # Return the last event or the first failed/blocked event
        for ev in events:
            if ev.status in ("FAILED", "BLOCKED", "FALLBACK"):
                return ev
        return events[-1]

    @classmethod
    def assemble_trace_record(
        cls,
        decision_trace_id: str,
        station_id: str,
        events: List[TraceEvent],
        pipeline_run_id: Optional[str] = None,
        request_id: Optional[str] = None,
        horizon_hours: int = 48,
        scenario_id: Optional[str] = None,
        optimization_mode: str = "EXPECTED"
    ) -> TraceRecord:
        """Assembles a full TraceRecord with lineage and terminal status."""
        adj = cls.build_adjacency(events)
        terminal = cls.identify_terminal_event(events)

        status_str = "COMPLETED"
        if terminal is not None:
            if terminal.status == "FAILED":
                status_str = "FAILED"
            elif terminal.status == "BLOCKED":
                status_str = "BLOCKED"
            elif terminal.status == "FALLBACK":
                status_str = "FALLBACK"
            elif len(events) < 6:
                status_str = "PARTIAL"

        # Extract high-level outcomes from events
        pol_state = None
        directive = None
        res_state = None
        edge_mode = None

        for ev in events:
            if ev.stage.value == "POLICY":
                pol_state = ev.outputs.get("policy_state")
                directive = ev.outputs.get("primary_directive")
            elif ev.stage.value == "RESILIENCE":
                res_state = ev.outputs.get("resilience_state")
            elif ev.stage.value == "EDGE":
                edge_mode = ev.outputs.get("edge_mode")

        return TraceRecord(
            decision_trace_id=decision_trace_id,
            station_id=station_id.upper(),
            pipeline_run_id=pipeline_run_id,
            request_id=request_id,
            creation_timestamp=events[0].timestamp if events else datetime.now(timezone.utc).isoformat(),
            completion_timestamp=events[-1].timestamp if events else None,
            execution_status=status_str,
            horizon_hours=horizon_hours,
            scenario_id=scenario_id,
            optimization_mode=optimization_mode,
            primary_directive=directive,
            policy_state=pol_state,
            resilience_state=res_state,
            edge_mode=edge_mode,
            events=events,
            lineage_graph=adj,
            provenance="SIMULATED"
        )
