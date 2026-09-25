"""
POLARIS-EMS — Phase 16 Trace Integration (Workstream I)
SIH26061: Polar Energy Management & Resilience System

Integrates Phase 16 field/HIL/reliability events with the existing
Phase 12 Decision Trace architecture.

Does NOT create another trace system. Extends trace linkage for:
  adapter, device, telemetry, fault injection, connectivity transition,
  actuation request, authorization, actuation result, reconciliation, recovery.

Preserves existing stages:
  EDGE, FORECAST, SCENARIO, OPTIMIZER, TWIN_REPLAY, RESILIENCE, POLICY, RECONCILIATION
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.trace.schema import (
    TraceEvent,
    TraceRecord,
    TraceStage,
    TraceLifecycleState,
    ReasonCode,
    ValidationTier,
)


class Phase16TraceLinker:
    """Links Phase 16 events into the existing Phase 12 trace DAG.

    Each method creates a TraceEvent that can be appended to a TraceRecord.
    """

    @staticmethod
    def _event_id() -> str:
        return f"p16_{uuid.uuid4().hex[:12]}"

    @classmethod
    def trace_adapter_event(
        cls,
        trace_id: str,
        station_id: str,
        adapter_name: str,
        environment: str,
        action: str,
        parent_event_id: Optional[str] = None,
    ) -> TraceEvent:
        return TraceEvent(
            event_id=cls._event_id(),
            trace_id=trace_id,
            stage=TraceStage.EDGE,
            event_type="ADAPTER_EVENT",
            station_id=station_id,
            status="COMPLETED",
            reason_code=ReasonCode.EDGE_CONNECTED,
            summary=f"Adapter {adapter_name} ({environment}): {action}",
            inputs={"adapter": adapter_name, "environment": environment},
            outputs={"action": action},
            validation_tier=ValidationTier.SIMULATED,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
        )

    @classmethod
    def trace_telemetry_event(
        cls,
        trace_id: str,
        station_id: str,
        device_id: str,
        channel: str,
        quality: str,
        condition: str,
        parent_event_id: Optional[str] = None,
    ) -> TraceEvent:
        reason = ReasonCode.EDGE_CONNECTED if quality == "VALID" else ReasonCode.TELEMETRY_STALE
        return TraceEvent(
            event_id=cls._event_id(),
            trace_id=trace_id,
            stage=TraceStage.EDGE,
            event_type="TELEMETRY_INGESTION",
            station_id=station_id,
            status="COMPLETED",
            reason_code=reason,
            summary=f"Telemetry {device_id}::{channel} quality={quality} condition={condition}",
            inputs={"device_id": device_id, "channel": channel},
            outputs={"quality": quality, "condition": condition},
            validation_tier=ValidationTier.SIMULATED,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
        )

    @classmethod
    def trace_connectivity_transition(
        cls,
        trace_id: str,
        station_id: str,
        from_state: str,
        to_state: str,
        parent_event_id: Optional[str] = None,
    ) -> TraceEvent:
        reason_map = {
            "CONNECTED": ReasonCode.EDGE_CONNECTED,
            "DEGRADED": ReasonCode.CONNECTIVITY_DEGRADED,
            "OFFLINE": ReasonCode.EDGE_OFFLINE,
            "RECONNECTING": ReasonCode.RECONCILIATION_COMPLETED,
        }
        reason = reason_map.get(to_state, ReasonCode.EDGE_CONNECTED)
        return TraceEvent(
            event_id=cls._event_id(),
            trace_id=trace_id,
            stage=TraceStage.EDGE,
            event_type="CONNECTIVITY_TRANSITION",
            station_id=station_id,
            status="COMPLETED",
            reason_code=reason,
            summary=f"Connectivity: {from_state} → {to_state}",
            inputs={"from_state": from_state},
            outputs={"to_state": to_state},
            validation_tier=ValidationTier.SIMULATED,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
        )

    @classmethod
    def trace_fault_injection(
        cls,
        trace_id: str,
        station_id: str,
        fault_type: str,
        fault_class: str,
        target: str,
        parent_event_id: Optional[str] = None,
    ) -> TraceEvent:
        return TraceEvent(
            event_id=cls._event_id(),
            trace_id=trace_id,
            stage=TraceStage.EDGE,
            event_type="FAULT_INJECTION",
            station_id=station_id,
            status="COMPLETED",
            reason_code=ReasonCode.TELEMETRY_STALE,
            summary=f"Fault injected: {fault_class}/{fault_type} on {target}",
            inputs={"fault_type": fault_type, "fault_class": fault_class},
            outputs={"target": target},
            validation_tier=ValidationTier.SIMULATED,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
        )

    @classmethod
    def trace_actuation_request(
        cls,
        trace_id: str,
        station_id: str,
        device_id: str,
        action: str,
        authorized: bool,
        outcome: str,
        parent_event_id: Optional[str] = None,
    ) -> TraceEvent:
        reason = ReasonCode.EDGE_CONNECTED if authorized else ReasonCode.FALLBACK_REQUIRED
        return TraceEvent(
            event_id=cls._event_id(),
            trace_id=trace_id,
            stage=TraceStage.EDGE,
            event_type="ACTUATION_REQUEST",
            station_id=station_id,
            status="COMPLETED" if authorized else "BLOCKED",
            reason_code=reason,
            summary=f"Actuation {action} on {device_id}: authorized={authorized}, outcome={outcome}",
            inputs={"device_id": device_id, "action": action},
            outputs={"authorized": authorized, "outcome": outcome},
            validation_tier=ValidationTier.SIMULATED,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
        )

    @classmethod
    def trace_reconciliation(
        cls,
        trace_id: str,
        station_id: str,
        total_buffered: int,
        processed: int,
        duplicates: int,
        gaps: int,
        parent_event_id: Optional[str] = None,
    ) -> TraceEvent:
        return TraceEvent(
            event_id=cls._event_id(),
            trace_id=trace_id,
            stage=TraceStage.RECONCILIATION,
            event_type="BUFFER_RECONCILIATION",
            station_id=station_id,
            status="COMPLETED",
            reason_code=ReasonCode.RECONCILIATION_COMPLETED,
            summary=f"Reconciled {processed}/{total_buffered} items, {duplicates} dups, {gaps} gaps",
            inputs={"total_buffered": total_buffered},
            outputs={"processed": processed, "duplicates": duplicates, "gaps": gaps},
            validation_tier=ValidationTier.SIMULATED,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
        )

    @classmethod
    def trace_recovery(
        cls,
        trace_id: str,
        station_id: str,
        recovered_state: str,
        parent_event_id: Optional[str] = None,
    ) -> TraceEvent:
        return TraceEvent(
            event_id=cls._event_id(),
            trace_id=trace_id,
            stage=TraceStage.EDGE,
            event_type="STATE_RECOVERY",
            station_id=station_id,
            status="COMPLETED",
            reason_code=ReasonCode.EDGE_CONNECTED,
            summary=f"State recovery complete: {recovered_state}",
            inputs={},
            outputs={"recovered_state": recovered_state},
            validation_tier=ValidationTier.SIMULATED,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
        )

    @classmethod
    def create_phase16_trace(cls, station_id: str) -> TraceRecord:
        """Create a new TraceRecord for a Phase 16 validation lifecycle."""
        trace_id = f"P16_{station_id}_{uuid.uuid4().hex[:8]}"
        return TraceRecord(
            decision_trace_id=trace_id,
            station_id=station_id,
            execution_status=TraceLifecycleState.CREATED,
            horizon_hours=0,
            optimization_mode="VALIDATION",
            provenance="SIMULATED",
        )
