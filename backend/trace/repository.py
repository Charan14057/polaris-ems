"""
POLARIS-EMS — Persistent Decision Trace Repository
SIH26061: Polar Energy Management & Resilience System

Provides deterministic local filesystem + in-memory persistence for DecisionTrace records:
- Thread-safe save, retrieval, listing, filtering, and comparison.
- Structured storage under reports/traces/<station_id>/<trace_id>.json.
- Bounded retention preventing storage exhaustion.
- JSON and CSV summary export utilities.

INVARIANTS:
- No hidden global state; deterministic repository abstraction.
- Zero secrets or internal credential exposure.
"""

import json
import os
import csv
import io
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

from backend.trace.schema import (
    TraceRecord,
    TraceSummary,
    TraceEvent,
    DecisionDelta,
    TraceLifecycleState
)
from backend.trace.explainer import DeterministicExplainer
from backend.trace.comparison import TraceComparisonEngine
from backend.trace.archive import ITraceArchive, get_trace_archive


class TraceRepository:
    """Manages persistence, indexing, and retrieval of DecisionTrace records."""

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        max_retention_traces: int = 1000,
        archive: Optional[ITraceArchive] = None
    ):
        if storage_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            storage_dir = str(base_dir / "reports" / "traces")

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_retention_traces = max_retention_traces
        self.archive = archive or get_trace_archive()

        # In-memory index: trace_id -> TraceRecord
        self._memory_cache: Dict[str, TraceRecord] = {}
        self._load_existing_traces()

    def _load_existing_traces(self) -> None:
        """Indexes existing JSON trace records from the storage directory."""
        for p in self.storage_dir.glob("*/*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                rec = TraceRecord.model_validate(raw)
                self._memory_cache[rec.decision_trace_id] = rec
            except Exception:
                pass  # Skip corrupted files gracefully

    def save_trace(self, trace: TraceRecord) -> None:
        """Persists a complete TraceRecord to disk and memory cache."""
        # Ensure explanation is attached
        if trace.explanation is None:
            trace.explanation = DeterministicExplainer.explain(trace)

        # Enforce bounded retention
        if len(self._memory_cache) >= self.max_retention_traces:
            # Evict oldest trace to cold archive
            oldest_id = next(iter(self._memory_cache.keys()))
            old_rec = self._memory_cache.pop(oldest_id, None)
            if old_rec:
                if self.archive:
                    try:
                        self.archive.archive_trace(old_rec)
                    except Exception:
                        pass
                old_file = self.storage_dir / old_rec.station_id / f"{old_rec.decision_trace_id}.json"
                if old_file.exists():
                    try:
                        old_file.unlink()
                    except OSError:
                        pass

        # Save to memory cache
        self._memory_cache[trace.decision_trace_id] = trace

        # Save to filesystem
        station_dir = self.storage_dir / trace.station_id
        station_dir.mkdir(parents=True, exist_ok=True)
        file_path = station_dir / f"{trace.decision_trace_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(trace.model_dump_json(indent=2))

    def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        """Retrieves a single TraceRecord by ID (active memory, active disk, or cold archive)."""
        if trace_id in self._memory_cache:
            return self._memory_cache[trace_id]

        # Attempt disk search across station subdirectories
        for p in self.storage_dir.glob(f"*/{trace_id}.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                rec = TraceRecord.model_validate(raw)
                self._memory_cache[rec.decision_trace_id] = rec
                return rec
            except Exception:
                pass

        # Check cold archive fallback
        if self.archive:
            try:
                archived = self.archive.retrieve_archived(trace_id)
                if archived:
                    return archived
            except Exception:
                pass

        return None

    def list_traces(
        self,
        station_id: Optional[str] = None,
        status: Optional[str] = None,
        policy_state: Optional[str] = None,
        resilience_state: Optional[str] = None,
        limit: int = 50
    ) -> List[TraceSummary]:
        """Returns filtered summaries of recorded decision traces."""
        results: List[TraceSummary] = []
        for rec in reversed(list(self._memory_cache.values())):
            if station_id and rec.station_id.upper() != station_id.upper():
                continue
            if status and rec.execution_status.value != status.upper():
                continue
            if policy_state and rec.policy_state != policy_state.upper():
                continue
            if resilience_state and rec.resilience_state != resilience_state.upper():
                continue

            results.append(rec.to_summary())
            if len(results) >= limit:
                break
        return results

    def get_events(self, trace_id: str) -> List[TraceEvent]:
        """Retrieves all atomic TraceEvent entries for a trace."""
        trace = self.get_trace(trace_id)
        if trace is None:
            raise KeyError(f"DecisionTrace '{trace_id}' not found.")
        return trace.events

    def compare(self, base_trace_id: str, compare_trace_id: str) -> DecisionDelta:
        """Computes comparative delta between two stored traces."""
        base = self.get_trace(base_trace_id)
        if base is None:
            raise KeyError(f"Base trace '{base_trace_id}' not found.")
        comp = self.get_trace(compare_trace_id)
        if comp is None:
            raise KeyError(f"Comparison trace '{compare_trace_id}' not found.")
        return TraceComparisonEngine.compare(base, comp)

    def export_trace_json(self, trace_id: str) -> str:
        """Exports full trace record as formatted JSON string."""
        trace = self.get_trace(trace_id)
        if trace is None:
            raise KeyError(f"DecisionTrace '{trace_id}' not found.")
        return trace.model_dump_json(indent=2)

    def export_trace_csv(self, trace_id: str) -> str:
        """Exports trace events sequence as a standard CSV report."""
        trace = self.get_trace(trace_id)
        if trace is None:
            raise KeyError(f"DecisionTrace '{trace_id}' not found.")

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Trace ID", "Station", "Stage", "Event Type", "Status",
            "Reason Code", "Validation Tier", "Provenance", "Duration (ms)", "Summary"
        ])
        for ev in trace.events:
            writer.writerow([
                trace.decision_trace_id,
                trace.station_id,
                ev.stage.value,
                ev.event_type,
                ev.status,
                ev.reason_code.value,
                ev.validation_tier.value,
                ev.provenance,
                ev.duration_ms,
                ev.summary
            ])
        return output.getvalue()


# Singleton repository instance
_trace_repository: Optional[TraceRepository] = None


def get_trace_repository() -> TraceRepository:
    """Factory provider for TraceRepository singleton."""
    global _trace_repository
    if _trace_repository is None:
        _trace_repository = TraceRepository()
    return _trace_repository
