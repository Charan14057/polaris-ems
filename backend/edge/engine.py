"""
POLARIS-EMS — Edge Orchestration Engine
SIH26061: Polar Energy Management & Resilience System

Coordinates the complete edge field resilience architecture:
- Device registry lookups.
- Ingestion and normalization of heterogeneous telemetry.
- Deterministic data quality validation.
- Fleet device health monitoring.
- Edge connectivity tracking and buffer lifecycle.
- Reconnection state reconciliation.
- Integration with central decision pathways via non-optimizing adapters.

STRICT INVARIANTS:
1. Zero independent optimization or Pyomo/HiGHS code.
2. Zero duplicate physical simulation math.
3. Fallbacks are safe operational postures, not calculated schedules.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone

from backend.edge.schema import (
    TelemetryReading,
    QualityValidationResult,
    DeviceHealthStatus,
    ConnectivityStatus,
    EdgeStateSnapshot,
    ReconciliationReport,
    EdgeMode,
    FallbackPosture,
    ConnectivityState
)
from backend.edge.devices import DeviceRegistry, get_device_registry
from backend.edge.telemetry import TelemetryNormalizer
from backend.edge.quality import TelemetryQualityEngine
from backend.edge.health import DeviceHealthEngine
from backend.edge.connectivity import ConnectivityTracker
from backend.edge.buffer import LocalTelemetryBuffer
from backend.edge.state import EdgeStateManager
from backend.edge.reconciliation import StateReconciler
from backend.edge.adapters import EdgeDecisionBridge


class EdgeEngine:
    """Station-specific edge node coordinator."""

    def __init__(
        self,
        station_id: str,
        device_registry: Optional[DeviceRegistry] = None,
        max_buffer_capacity: int = 5000
    ):
        self.station_id = station_id.upper()
        self.device_registry = device_registry or get_device_registry()

        catalog = self.device_registry.get_catalog(self.station_id)
        self.edge_node_id = catalog.edge_node_id

        self.quality_engine = TelemetryQualityEngine(self.device_registry)
        self.health_engine = DeviceHealthEngine(self.device_registry)
        self.connectivity_tracker = ConnectivityTracker(self.station_id)
        self.buffer = LocalTelemetryBuffer(max_capacity=max_buffer_capacity)
        self.state_manager = EdgeStateManager(self.station_id, self.edge_node_id)

    def ingest_telemetry(
        self,
        reading_or_dict: Union[TelemetryReading, Dict[str, Any]],
        current_time: Optional[datetime] = None
    ) -> Tuple[TelemetryReading, QualityValidationResult]:
        """
        Ingests a telemetry record:
        1. Normalizes envelope.
        2. Validates data quality.
        3. Updates device health tracker.
        4. Checks connectivity: if offline or degraded, buffers reading locally.
        5. Updates edge state snapshot.
        """
        now = current_time or datetime.now(timezone.utc)
        if isinstance(reading_or_dict, dict):
            reading = TelemetryNormalizer.from_dict(reading_or_dict)
        else:
            reading = reading_or_dict

        # 1. Deterministic quality check
        val_result = self.quality_engine.validate(reading, current_time=now)

        # 2. Update health tracker
        self.health_engine.record_reading(reading)

        # 3. Buffer management depending on connectivity
        conn_status = self.connectivity_tracker.get_status(current_time=now)

        if conn_status.connectivity_state in (ConnectivityState.OFFLINE, ConnectivityState.DEGRADED, ConnectivityState.RECONNECTING):
            enqueued, msg = self.buffer.enqueue(reading)
            self.connectivity_tracker.set_buffered_count(self.buffer.size())
            self.state_manager.set_buffer_depth(self.buffer.size())

        # 4. Update latest validated snapshot if reading is accepted
        if val_result.is_valid:
            self.state_manager.update_reading(reading)

        return reading, val_result

    def ingest_batch(
        self,
        batch: List[Union[TelemetryReading, Dict[str, Any]]],
        current_time: Optional[datetime] = None
    ) -> List[Tuple[TelemetryReading, QualityValidationResult]]:
        """Processes a sequence of telemetry readings."""
        now = current_time or datetime.now(timezone.utc)
        results = []
        for item in batch:
            res = self.ingest_telemetry(item, current_time=now)
            results.append(res)
        return results

    def get_state(self, current_time: Optional[datetime] = None) -> EdgeStateSnapshot:
        """Returns the canonical state snapshot."""
        now = current_time or datetime.now(timezone.utc)
        conn_status = self.connectivity_tracker.get_status(current_time=now)
        fleet_health = self.health_engine.evaluate_fleet(self.station_id, current_time=now)
        self.state_manager.set_buffer_depth(self.buffer.size())
        return self.state_manager.get_snapshot(conn_status.connectivity_state, fleet_health, current_time=now)

    def get_fleet_health(self, current_time: Optional[datetime] = None) -> List[DeviceHealthStatus]:
        """Returns fleet health evaluations."""
        return self.health_engine.evaluate_fleet(self.station_id, current_time=current_time)

    def get_connectivity(self, current_time: Optional[datetime] = None) -> ConnectivityStatus:
        """Returns edge-to-backend connectivity status."""
        self.connectivity_tracker.set_buffered_count(self.buffer.size())
        return self.connectivity_tracker.get_status(current_time=current_time)

    def sync_telemetry(self, current_time: Optional[datetime] = None) -> ReconciliationReport:
        """
        Executes reconnection reconciliation between local buffer and central backend state.
        """
        now = current_time or datetime.now(timezone.utc)
        self.connectivity_tracker.start_reconnect()

        # Reconcile buffer against latest live readings
        report, ack_ids = StateReconciler.reconcile(
            station_id=self.station_id,
            buffer=self.buffer,
            latest_live_snapshots=self.state_manager.latest_readings
        )

        # Acknowledge confirmed items
        self.buffer.acknowledge(ack_ids)

        # Update connectivity & sync time
        self.connectivity_tracker.set_buffered_count(self.buffer.size())
        self.connectivity_tracker.finish_reconnect()
        self.state_manager.set_sync_time(now)
        self.state_manager.set_buffer_depth(self.buffer.size())

        return report

    def evaluate_decision(self) -> Dict[str, Any]:
        """Evaluates operational decision pathway."""
        snapshot = self.get_state()
        return EdgeDecisionBridge.evaluate_edge_decision(snapshot)

    def set_simulation_condition(self, condition: str) -> None:
        """
        Applies a simulated operational condition for testing:
        - 'OFFLINE': forces connectivity offline
        - 'DEGRADED': forces connectivity degraded
        - 'CONNECTED': restores connected state
        - 'SAFE_HOLD': forces safe hold override
        - 'NORMAL': clears manual overrides and restores connected state
        """
        if condition == "OFFLINE":
            self.connectivity_tracker.state = ConnectivityState.OFFLINE
            self.connectivity_tracker.consecutive_failures = 3
            self.connectivity_tracker.diagnostics.append("Simulated total satellite link loss")
            self.state_manager.manual_override_mode = EdgeMode.OFFLINE_EDGE
        elif condition == "DEGRADED":
            self.connectivity_tracker.state = ConnectivityState.DEGRADED
            self.connectivity_tracker.consecutive_failures = 1
            self.connectivity_tracker.packet_loss_pct = 45.0
            self.connectivity_tracker.diagnostics.append("Simulated polar storm RF degradation")
            self.state_manager.manual_override_mode = EdgeMode.DEGRADED_CONNECTIVITY
        elif condition == "SAFE_HOLD":
            self.state_manager.manual_override_mode = EdgeMode.SAFE_HOLD
        elif condition in ("CONNECTED", "NORMAL"):
            self.connectivity_tracker.record_success()
            self.state_manager.manual_override_mode = None


# Registry of EdgeEngine instances keyed by station_id
_edge_engines: Dict[str, EdgeEngine] = {}


def get_edge_engine(station_id: str, device_registry: Optional[DeviceRegistry] = None) -> EdgeEngine:
    """Singleton/factory for station-specific EdgeEngine."""
    sid = station_id.upper()
    if sid not in _edge_engines:
        _edge_engines[sid] = EdgeEngine(sid, device_registry=device_registry)
    return _edge_engines[sid]
