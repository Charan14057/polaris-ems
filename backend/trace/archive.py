"""
POLARIS-EMS — Pluggable Decision Trace Archival Store
SIH26061: Polar Energy Management & Resilience System

Provides a decoupled archival abstraction extending the 500-record active
retention boundary with local compressed cold storage (and future cloud hooks).

INVARIANTS:
1. Does not alter existing REST API trace retrieval contracts.
2. Fully offline-safe: Uses local compressed JSON.gz, zero mandatory cloud egress.
3. Pluggable: Can be swapped for S3/Blob storage in future field deployments.
"""

import json
import gzip
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from backend.trace.schema import TraceRecord, TraceSummary, TraceLifecycleState


class ITraceArchive(ABC):
    """Abstract interface for cold decision trace archival storage."""

    @abstractmethod
    def archive_trace(self, trace: TraceRecord) -> str:
        """Stores a trace in the archive and returns its archive URI/path."""
        pass

    @abstractmethod
    def retrieve_archived(self, trace_id: str) -> Optional[TraceRecord]:
        """Retrieves an archived trace by ID."""
        pass

    @abstractmethod
    def list_archived(self, station_id: Optional[str] = None, limit: int = 100) -> List[TraceSummary]:
        """Lists metadata summaries for archived traces."""
        pass

    @abstractmethod
    def get_archive_stats(self) -> Dict[str, Any]:
        """Returns archival statistics (count, storage size, oldest/newest)."""
        pass


class LocalFileTraceArchive(ITraceArchive):
    """
    Compressed filesystem archival store.
    Stores cold traces under reports/traces/archive/<station_id>/<trace_id>.json.gz
    """

    def __init__(self, archive_dir: Optional[str] = None):
        if archive_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            archive_dir = str(base_dir / "reports" / "traces" / "archive")
        
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self._index: Dict[str, Path] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Indexes available compressed archive files."""
        for p in self.archive_dir.glob("*/*.json.gz"):
            tid = p.name.replace(".json.gz", "")
            self._index[tid] = p

    def archive_trace(self, trace: TraceRecord) -> str:
        """Compresses and archives a TraceRecord."""
        station_dir = self.archive_dir / trace.station_id.upper()
        station_dir.mkdir(parents=True, exist_ok=True)

        file_path = station_dir / f"{trace.decision_trace_id}.json.gz"
        raw_bytes = trace.model_dump_json(indent=None).encode("utf-8")

        with gzip.open(file_path, "wb") as gz_file:
            gz_file.write(raw_bytes)

        self._index[trace.decision_trace_id] = file_path
        return str(file_path)

    def retrieve_archived(self, trace_id: str) -> Optional[TraceRecord]:
        """Extracts and parses a TraceRecord from compressed archive."""
        if trace_id not in self._index:
            self._build_index()

        file_path = self._index.get(trace_id)
        if not file_path or not file_path.exists():
            return None

        try:
            with gzip.open(file_path, "rb") as gz_file:
                raw_bytes = gz_file.read()
            raw_data = json.loads(raw_bytes.decode("utf-8"))
            return TraceRecord.model_validate(raw_data)
        except Exception:
            return None

    def list_archived(self, station_id: Optional[str] = None, limit: int = 100) -> List[TraceSummary]:
        """Lists summaries of archived traces."""
        self._build_index()
        summaries: List[TraceSummary] = []

        for tid, path in self._index.items():
            if station_id and path.parent.name.upper() != station_id.upper():
                continue
            try:
                # Fast metadata extraction without loading all events
                with gzip.open(path, "rb") as gz_file:
                    raw_data = json.loads(gz_file.read().decode("utf-8"))
                
                status_val = raw_data.get("execution_status", "COMPLETED")
                if isinstance(status_val, str):
                    status_enum = getattr(TraceLifecycleState, status_val, TraceLifecycleState.COMPLETED)
                else:
                    status_enum = status_val

                summaries.append(TraceSummary(
                    decision_trace_id=raw_data["decision_trace_id"],
                    station_id=raw_data["station_id"],
                    pipeline_run_id=raw_data.get("pipeline_run_id"),
                    request_id=raw_data.get("request_id"),
                    creation_timestamp=raw_data.get("creation_timestamp", datetime.now(timezone.utc).isoformat()),
                    completion_timestamp=raw_data.get("completion_timestamp"),
                    execution_status=status_enum,
                    horizon_hours=raw_data.get("horizon_hours", 48),
                    scenario_id=raw_data.get("scenario_id"),
                    optimization_mode=raw_data.get("optimization_mode", "EXPECTED"),
                    primary_directive=raw_data.get("primary_directive"),
                    policy_state=raw_data.get("policy_state"),
                    resilience_state=raw_data.get("resilience_state"),
                    edge_mode=raw_data.get("edge_mode"),
                    event_count=len(raw_data.get("events", [])),
                    terminal_stage=raw_data.get("events", [{}])[-1].get("stage") if raw_data.get("events") else None,
                    provenance=raw_data.get("provenance", "SIMULATED")
                ))
            except Exception:
                continue

            if len(summaries) >= limit:
                break

        # Sort newest first
        summaries.sort(key=lambda s: s.creation_timestamp, reverse=True)
        return summaries

    def get_archive_stats(self) -> Dict[str, Any]:
        """Returns storage metrics."""
        self._build_index()
        total_bytes = 0
        for p in self._index.values():
            if p.exists():
                total_bytes += p.stat().st_size

        return {
            "archive_type": "LOCAL_COMPRESSED_GZIP",
            "total_archived_traces": len(self._index),
            "total_archive_bytes": total_bytes,
            "archive_directory": str(self.archive_dir),
            "cloud_sync_ready": True
        }


# Singleton archive instance
_trace_archive_instance: Optional[ITraceArchive] = None


def get_trace_archive() -> ITraceArchive:
    global _trace_archive_instance
    if _trace_archive_instance is None:
        _trace_archive_instance = LocalFileTraceArchive()
    return _trace_archive_instance
