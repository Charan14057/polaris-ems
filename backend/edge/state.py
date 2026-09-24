"""
POLARIS-EMS — Canonical Local Edge State & Fallback Logic
SIH26061: Polar Energy Management & Resilience System

Manages the local operational state snapshot for a polar station edge node:
- Consolidates latest validated telemetry readings.
- Aggregates fleet-wide device health and data quality counts.
- Derives EdgeMode and FallbackPosture deterministically based on connectivity and fleet health.

INVARIANTS:
- Fallback postures are bounded operational safety postures, NEVER optimization results.
- Zero independent power balance or dispatch optimization logic.
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, timezone
import dateutil.parser

from backend.edge.schema import (
    EdgeMode,
    FallbackPosture,
    ConnectivityState,
    DeviceHealthState,
    DataQualityState,
    TelemetryReading,
    EdgeStateSnapshot,
    DeviceHealthStatus
)


class EdgeStateManager:
    """Maintains local edge node snapshot and derives operational posture."""

    def __init__(self, station_id: str, edge_node_id: str):
        self.station_id = station_id.upper()
        self.edge_node_id = edge_node_id
        self.latest_readings: Dict[str, TelemetryReading] = {}
        self.quality_summary: Dict[str, int] = {q.value: 0 for q in DataQualityState}
        self.health_summary: Dict[str, int] = {h.value: 0 for h in DeviceHealthState}
        self.last_sync_time: Optional[datetime] = datetime.now(timezone.utc)
        self.buffer_depth: int = 0
        self.manual_override_mode: Optional[EdgeMode] = None

    def update_reading(self, reading: TelemetryReading) -> None:
        """Stores a validated reading in latest snapshot and updates quality stats."""
        key = f"{reading.device_id}::{reading.channel}"
        self.latest_readings[key] = reading
        self.quality_summary[reading.quality.value] = self.quality_summary.get(reading.quality.value, 0) + 1

    def update_health_summary(self, fleet_health: List[DeviceHealthStatus]) -> None:
        """Refreshes fleet health summary counts."""
        self.health_summary = {h.value: 0 for h in DeviceHealthState}
        for dh in fleet_health:
            state_str = dh.health_state.value
            self.health_summary[state_str] = self.health_summary.get(state_str, 0) + 1

    def set_sync_time(self, sync_time: Optional[datetime] = None) -> None:
        """Updates timestamp of last successful synchronization."""
        self.last_sync_time = sync_time or datetime.now(timezone.utc)

    def set_buffer_depth(self, depth: int) -> None:
        """Updates local buffer queue depth."""
        self.buffer_depth = depth

    def derive_posture(
        self,
        conn_state: ConnectivityState,
        fleet_health: List[DeviceHealthStatus]
    ) -> Tuple[EdgeMode, FallbackPosture]:
        """
        Determines EdgeMode and FallbackPosture deterministically.
        Rules:
        - OFFLINE: Mode = OFFLINE_EDGE, Posture = SAFE_HOLD (or PROTECT_CRITICAL_SYSTEMS)
        - DEGRADED: Mode = DEGRADED_CONNECTIVITY, Posture = HOLD_LAST_VALIDATED_STATE
        - RECONNECTING: Mode = RECOVERY_SYNC, Posture = BUFFER_AND_FORWARD
        - CONNECTED with severe fleet faults (e.g. > 50% faulted): Mode = SAFE_HOLD, Posture = PROTECT_CRITICAL_SYSTEMS
        - CONNECTED nominal: Mode = CONNECTED_OPERATION, Posture = WAIT_FOR_BACKEND_DECISION
        """
        if self.manual_override_mode is not None:
            mode = self.manual_override_mode
            if mode == EdgeMode.SAFE_HOLD:
                return mode, FallbackPosture.SAFE_HOLD
            elif mode == EdgeMode.OFFLINE_EDGE:
                return mode, FallbackPosture.PROTECT_CRITICAL_SYSTEMS
            elif mode == EdgeMode.DEGRADED_CONNECTIVITY:
                return mode, FallbackPosture.HOLD_LAST_VALIDATED_STATE
            elif mode == EdgeMode.RECOVERY_SYNC:
                return mode, FallbackPosture.BUFFER_AND_FORWARD
            else:
                return mode, FallbackPosture.WAIT_FOR_BACKEND_DECISION

        fault_count = sum(1 for d in fleet_health if d.health_state == DeviceHealthState.FAULT)
        total_devices = len(fleet_health)

        # Severe fleet fault trigger
        if total_devices > 0 and (fault_count / total_devices) >= 0.5:
            return EdgeMode.SAFE_HOLD, FallbackPosture.PROTECT_CRITICAL_SYSTEMS

        if conn_state == ConnectivityState.OFFLINE:
            return EdgeMode.OFFLINE_EDGE, FallbackPosture.SAFE_HOLD
        elif conn_state == ConnectivityState.DEGRADED:
            return EdgeMode.DEGRADED_CONNECTIVITY, FallbackPosture.HOLD_LAST_VALIDATED_STATE
        elif conn_state == ConnectivityState.RECONNECTING:
            return EdgeMode.RECOVERY_SYNC, FallbackPosture.BUFFER_AND_FORWARD
        else:
            return EdgeMode.CONNECTED_OPERATION, FallbackPosture.WAIT_FOR_BACKEND_DECISION

    def get_snapshot(
        self,
        conn_state: ConnectivityState,
        fleet_health: List[DeviceHealthStatus],
        current_time: Optional[datetime] = None
    ) -> EdgeStateSnapshot:
        """Constructs canonical EdgeStateSnapshot."""
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        self.update_health_summary(fleet_health)
        edge_mode, fallback_posture = self.derive_posture(conn_state, fleet_health)

        sync_freshness_sec = (now - self.last_sync_time).total_seconds() if self.last_sync_time else 9999.0

        return EdgeStateSnapshot(
            station_id=self.station_id,
            edge_node_id=self.edge_node_id,
            edge_mode=edge_mode,
            connectivity_state=conn_state,
            fallback_posture=fallback_posture,
            active_devices_count=len(fleet_health),
            healthy_devices_count=self.health_summary.get("HEALTHY", 0),
            degraded_devices_count=self.health_summary.get("DEGRADED", 0),
            fault_devices_count=self.health_summary.get("FAULT", 0),
            buffer_depth=self.buffer_depth,
            last_sync_time=self.last_sync_time.isoformat() if self.last_sync_time else None,
            sync_freshness_sec=round(max(0.0, sync_freshness_sec), 1),
            latest_readings=dict(self.latest_readings),
            quality_summary=dict(self.quality_summary),
            health_summary=dict(self.health_summary),
            provenance="CONFIGURED",
            timestamp=now.isoformat()
        )
