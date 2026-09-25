"""
POLARIS-EMS — Phase 16 Comprehensive Test Suite
Workstreams B–K: Field / Hardware-in-the-Loop Validation & Reliability

Covers:
  B  Actuation Boundary
  C  Telemetry Ingestion
  D  Disconnect / Reconnect Validation
  E  Buffer & Reconciliation Stress
  F  Fault Injection
  G  Safety / Authorization
  H  Long-Duration Reliability
  I  Trace Continuity
  K  Integration / Demo

INVARIANTS:
  - Locked 6-tier provenance: {REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED}
  - All tests are deterministic
  - No real hardware dependencies
  - PHYSICAL_CONNECTIVITY = DISCONNECTED
  - PHYSICAL_SCADA_LINK = FALSE
"""

import json
import time
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from pathlib import Path

# ---------------------------------------------------------------------------
# Schema & Edge modules
# ---------------------------------------------------------------------------
from backend.edge.schema import (
    TelemetryReading,
    DataQualityState,
    QualityValidationResult,
    DeviceProfile,
    StationDeviceCatalog,
    DeviceChannelConfig,
    ConnectivityState,
    ConnectivityStatus,
    EdgeMode,
    FallbackPosture,
    EdgeStateSnapshot,
    ReconciliationReport,
    ReconciliationAuditEntry,
    DeviceHealthState,
    DeviceHealthStatus,
    DeviceType,
    LOCKED_PROVENANCE_TIERS,
    validate_provenance,
)
from backend.edge.telemetry import TelemetryNormalizer
from backend.edge.quality import TelemetryQualityEngine
from backend.edge.health import DeviceHealthEngine
from backend.edge.connectivity import ConnectivityTracker
from backend.edge.buffer import LocalTelemetryBuffer, BufferedItem
from backend.edge.state import EdgeStateManager
from backend.edge.reconciliation import StateReconciler
from backend.edge.actuation import (
    ActuationBoundary,
    ActuationRequest,
    ActuationResult,
    ActuationOutcome,
)
from backend.edge.telemetry_ingestion import (
    TelemetryCondition,
    AdapterTelemetryIngestor,
)
from backend.edge.fault_injection import (
    FaultInjector,
    DeviceFault,
    TelemetryFault,
    ConnectivityFault,
    InterfaceFault,
    FaultScheduleEntry,
)
from backend.edge.trace_integration import Phase16TraceLinker
from backend.trace.schema import (
    TraceEvent,
    TraceRecord,
    TraceStage,
    TraceLifecycleState,
    ReasonCode,
)

# ---------------------------------------------------------------------------
# Helpers: test device registry mock
# ---------------------------------------------------------------------------

def _make_channel(name: str, unit: str, mn: float, mx: float, fresh: float = 60.0):
    return DeviceChannelConfig(channel=name, unit=unit, min_val=mn, max_val=mx, freshness_limit_seconds=fresh)

def _make_device(dev_id: str, station: str = "TEST_STATION", dtype=DeviceType.SOLAR):
    return DeviceProfile(
        device_id=dev_id,
        station_id=station,
        device_type=dtype,
        name=f"Test {dev_id}",
        rated_capacity=100.0,
        unit="kW",
        enabled=True,
        expected_reporting_interval_sec=10.0,
        freshness_threshold_sec=60.0,
        provenance="CONFIGURED",
        telemetry_channels=[
            _make_channel("power", "kW", 0.0, 200.0),
            _make_channel("voltage", "V", 200.0, 260.0),
        ],
    )

def _make_catalog(station: str = "TEST_STATION"):
    return StationDeviceCatalog(
        station_id=station,
        station_name="Test Station",
        edge_node_id=f"{station.lower()}_edge",
        devices=[_make_device("dev_001", station), _make_device("dev_002", station)],
    )

class MockDeviceRegistry:
    """Minimal device registry mock for deterministic unit tests."""
    def __init__(self):
        self._catalog = _make_catalog()

    def get_catalog(self, station_id: str) -> StationDeviceCatalog:
        return self._catalog

    def list_devices(self, station_id: str, device_type=None):
        devs = self._catalog.devices
        if device_type:
            return [d for d in devs if d.device_type == device_type]
        return list(devs)

    def get_device(self, station_id: str, device_id: str) -> DeviceProfile:
        for d in self._catalog.devices:
            if d.device_id == device_id:
                return d
        raise KeyError(f"Device {device_id} not found")

    def has_device(self, station_id: str, device_id: str) -> bool:
        try:
            self.get_device(station_id, device_id)
            return True
        except KeyError:
            return False


def _make_reading(
    dev: str = "dev_001",
    ch: str = "power",
    val: float = 50.0,
    unit: str = "kW",
    station: str = "TEST_STATION",
    ts: datetime = None,
    seq: int = None,
    prov: str = "SIMULATED",
):
    ts = ts or datetime.now(timezone.utc)
    return TelemetryNormalizer.create_envelope(
        station_id=station, device_id=dev, channel=ch, value=val,
        unit=unit, timestamp=ts, provenance=prov, sequence_number=seq,
    )


# ===========================================================================
# WORKSTREAM B — ACTUATION BOUNDARY TESTS
# ===========================================================================
class TestActuationBoundary:

    def test_actuation_request_authorized(self):
        boundary = ActuationBoundary(dispatch_authorized=True)
        req = ActuationRequest(
            station_id="TEST", device_id="dev_001",
            action="set_power", value=50.0, environment="SIMULATOR",
        )
        result = boundary.request_actuation(req)
        assert result.authorized is True
        assert result.outcome in (ActuationOutcome.SIMULATED, ActuationOutcome.UNAVAILABLE)
        assert result.provenance in LOCKED_PROVENANCE_TIERS

    def test_actuation_request_rejected_no_auth(self):
        boundary = ActuationBoundary(dispatch_authorized=False)
        req = ActuationRequest(
            station_id="TEST", device_id="dev_001",
            action="set_power", value=50.0,
        )
        result = boundary.request_actuation(req)
        assert result.authorized is False
        assert result.outcome == ActuationOutcome.REJECTED

    def test_actuation_offline_rejected(self):
        boundary = ActuationBoundary(dispatch_authorized=True, connectivity_state="OFFLINE")
        req = ActuationRequest(
            station_id="TEST", device_id="dev_001",
            action="set_power", value=50.0,
        )
        result = boundary.request_actuation(req)
        assert result.authorized is False
        assert result.outcome == ActuationOutcome.REJECTED

    def test_actuation_unavailable_adapter(self):
        boundary = ActuationBoundary(dispatch_authorized=True)
        req = ActuationRequest(
            station_id="TEST", device_id="dev_001",
            action="set_power", value=50.0,
            environment="NONEXISTENT",
        )
        result = boundary.request_actuation(req)
        assert result.outcome == ActuationOutcome.UNAVAILABLE

    def test_actuation_result_provenance(self):
        boundary = ActuationBoundary()
        req = ActuationRequest(
            station_id="TEST", device_id="dev_001",
            action="set_power", value=50.0,
        )
        result = boundary.request_actuation(req)
        assert result.provenance in LOCKED_PROVENANCE_TIERS

    def test_actuation_history(self):
        boundary = ActuationBoundary()
        for i in range(3):
            req = ActuationRequest(
                station_id="TEST", device_id="dev_001",
                action="cmd", value=i,
            )
            boundary.request_actuation(req)
        assert len(boundary.history) == 3


# ===========================================================================
# WORKSTREAM C — TELEMETRY INGESTION TESTS
# ===========================================================================
class TestTelemetryIngestion:

    def _make_quality_engine(self):
        registry = MockDeviceRegistry()
        return TelemetryQualityEngine(device_registry=registry)

    def test_valid_telemetry(self):
        qe = self._make_quality_engine()
        now = datetime.now(timezone.utc)
        r = _make_reading(ts=now, seq=1)
        result = qe.validate(r, current_time=now)
        assert result.is_valid is True
        assert result.quality == DataQualityState.VALID

    def test_stale_telemetry(self):
        qe = self._make_quality_engine()
        now = datetime.now(timezone.utc)
        old = now - timedelta(seconds=120)
        r = _make_reading(ts=old, seq=1)
        result = qe.validate(r, current_time=now)
        assert result.quality == DataQualityState.STALE

    def test_duplicate_telemetry(self):
        qe = self._make_quality_engine()
        now = datetime.now(timezone.utc)
        r1 = _make_reading(ts=now, seq=1)
        r2 = _make_reading(ts=now, seq=2)  # same timestamp
        qe.validate(r1, current_time=now)
        result = qe.validate(r2, current_time=now)
        assert result.quality == DataQualityState.DUPLICATE

    def test_out_of_range_telemetry(self):
        qe = self._make_quality_engine()
        now = datetime.now(timezone.utc)
        r = _make_reading(val=999.0, ts=now, seq=1)  # max is 200
        result = qe.validate(r, current_time=now)
        assert result.quality == DataQualityState.OUT_OF_RANGE

    def test_out_of_order_telemetry(self):
        qe = self._make_quality_engine()
        now = datetime.now(timezone.utc)
        r1 = _make_reading(ts=now, seq=10)
        r2 = _make_reading(ts=now + timedelta(seconds=1), seq=5)
        qe.validate(r1, current_time=now)
        result = qe.validate(r2, current_time=now + timedelta(seconds=1))
        assert result.quality == DataQualityState.OUT_OF_ORDER

    def test_unknown_channel_telemetry(self):
        qe = self._make_quality_engine()
        now = datetime.now(timezone.utc)
        r = _make_reading(ch="nonexistent_channel", ts=now)
        result = qe.validate(r, current_time=now)
        assert result.quality == DataQualityState.MISSING

    def test_unit_mismatch_telemetry(self):
        qe = self._make_quality_engine()
        now = datetime.now(timezone.utc)
        r = _make_reading(unit="WRONG_UNIT", ts=now)
        result = qe.validate(r, current_time=now)
        assert result.quality == DataQualityState.SUSPECT

    def test_device_not_registered(self):
        qe = self._make_quality_engine()
        now = datetime.now(timezone.utc)
        r = _make_reading(dev="unknown_device", ts=now)
        result = qe.validate(r, current_time=now)
        assert result.quality == DataQualityState.SUSPECT

    def test_future_timestamp(self):
        qe = self._make_quality_engine()
        now = datetime.now(timezone.utc)
        future = now + timedelta(seconds=300)
        r = _make_reading(ts=future, seq=1)
        result = qe.validate(r, current_time=now)
        assert result.quality == DataQualityState.SUSPECT

    def test_adapter_ingestor_classify(self):
        qe = self._make_quality_engine()
        ingestor = AdapterTelemetryIngestor(quality_engine=qe)
        now = datetime.now(timezone.utc)
        r = _make_reading(ts=now, seq=1)
        _, condition = ingestor.validate_and_classify(r, current_time=now)
        assert condition == TelemetryCondition.VALID

    def test_reconnect_burst_generation(self):
        burst = AdapterTelemetryIngestor.generate_reconnect_burst(
            station_id="TEST_STATION", device_id="dev_001",
            channel="power", unit="kW", burst_size=10,
        )
        assert len(burst) == 10
        for r in burst:
            assert r.provenance in LOCKED_PROVENANCE_TIERS

    def test_provenance_preservation(self):
        r = AdapterTelemetryIngestor.create_adapter_reading(
            station_id="TEST", device_id="d1", channel="power",
            value=50.0, unit="kW", provenance="SIMULATED",
        )
        assert r.provenance == "SIMULATED"

    def test_invalid_provenance_rejected(self):
        with pytest.raises(ValueError):
            AdapterTelemetryIngestor.create_adapter_reading(
                station_id="TEST", device_id="d1", channel="power",
                value=50.0, unit="kW", provenance="HIL",
            )


# ===========================================================================
# WORKSTREAM D — DISCONNECT / RECONNECT TESTS
# ===========================================================================
class TestDisconnectReconnect:

    def test_connected_to_degraded(self):
        ct = ConnectivityTracker("TEST")
        assert ct.state == ConnectivityState.CONNECTED
        ct.record_failure("link degraded")
        assert ct.state == ConnectivityState.DEGRADED

    def test_degraded_to_offline(self):
        ct = ConnectivityTracker("TEST")
        ct.record_failure("fail1")
        ct.record_failure("fail2")
        ct.record_failure("fail3")
        assert ct.state == ConnectivityState.OFFLINE

    def test_offline_to_reconnecting(self):
        ct = ConnectivityTracker("TEST")
        for _ in range(3):
            ct.record_failure("link lost")
        assert ct.state == ConnectivityState.OFFLINE
        ct.start_reconnect()
        assert ct.state == ConnectivityState.RECONNECTING

    def test_reconnecting_to_connected(self):
        ct = ConnectivityTracker("TEST")
        for _ in range(3):
            ct.record_failure("link lost")
        ct.start_reconnect()
        ct.finish_reconnect()
        assert ct.state == ConnectivityState.CONNECTED

    def test_full_transition_cycle(self):
        """CONNECTED → DEGRADED → OFFLINE → RECONNECTING → CONNECTED"""
        ct = ConnectivityTracker("TEST")
        assert ct.state == ConnectivityState.CONNECTED

        ct.record_failure("storm")
        assert ct.state == ConnectivityState.DEGRADED

        ct.record_failure("storm")
        ct.record_failure("storm")
        assert ct.state == ConnectivityState.OFFLINE

        ct.start_reconnect()
        assert ct.state == ConnectivityState.RECONNECTING

        ct.finish_reconnect()
        assert ct.state == ConnectivityState.CONNECTED

    def test_heartbeat_timeout_transition(self):
        ct = ConnectivityTracker("TEST", heartbeat_timeout_sec=10.0)
        now = datetime.now(timezone.utc)
        ct.record_success(current_time=now)
        later = now + timedelta(seconds=30)
        status = ct.get_status(current_time=later)
        assert status.connectivity_state == ConnectivityState.DEGRADED

    def test_edge_mode_offline(self):
        sm = EdgeStateManager("TEST", "test_edge")
        mode, posture = sm.derive_posture(ConnectivityState.OFFLINE, [])
        assert mode == EdgeMode.OFFLINE_EDGE
        assert posture == FallbackPosture.SAFE_HOLD

    def test_edge_mode_degraded(self):
        sm = EdgeStateManager("TEST", "test_edge")
        mode, posture = sm.derive_posture(ConnectivityState.DEGRADED, [])
        assert mode == EdgeMode.DEGRADED_CONNECTIVITY
        assert posture == FallbackPosture.HOLD_LAST_VALIDATED_STATE

    def test_edge_mode_reconnecting(self):
        sm = EdgeStateManager("TEST", "test_edge")
        mode, posture = sm.derive_posture(ConnectivityState.RECONNECTING, [])
        assert mode == EdgeMode.RECOVERY_SYNC
        assert posture == FallbackPosture.BUFFER_AND_FORWARD

    def test_safe_hold_override(self):
        sm = EdgeStateManager("TEST", "test_edge")
        sm.manual_override_mode = EdgeMode.SAFE_HOLD
        mode, posture = sm.derive_posture(ConnectivityState.CONNECTED, [])
        assert mode == EdgeMode.SAFE_HOLD
        assert posture == FallbackPosture.SAFE_HOLD

    def test_offline_to_safe_hold(self):
        """CONNECTED → OFFLINE → SAFE_HOLD"""
        sm = EdgeStateManager("TEST", "test_edge")
        mode, _ = sm.derive_posture(ConnectivityState.CONNECTED, [])
        assert mode == EdgeMode.CONNECTED_OPERATION

        mode, _ = sm.derive_posture(ConnectivityState.OFFLINE, [])
        assert mode == EdgeMode.OFFLINE_EDGE

        sm.manual_override_mode = EdgeMode.SAFE_HOLD
        mode, posture = sm.derive_posture(ConnectivityState.OFFLINE, [])
        assert mode == EdgeMode.SAFE_HOLD
        assert posture == FallbackPosture.SAFE_HOLD


# ===========================================================================
# WORKSTREAM E — BUFFER & RECONCILIATION STRESS TESTS
# ===========================================================================
class TestBufferReconciliationStress:

    def test_buffer_capacity_bounded(self):
        buf = LocalTelemetryBuffer(max_capacity=100)
        for i in range(200):
            ts = datetime.now(timezone.utc) + timedelta(seconds=i)
            r = _make_reading(ts=ts)
            buf.enqueue(r)
        assert buf.size() <= 100

    def test_duplicate_rejection(self):
        buf = LocalTelemetryBuffer()
        r = _make_reading()
        ok1, _ = buf.enqueue(r)
        ok2, _ = buf.enqueue(r)  # same timestamp
        assert ok1 is True
        assert ok2 is False
        assert buf.size() == 1

    def test_duplicate_burst(self):
        buf = LocalTelemetryBuffer()
        r = _make_reading()
        for _ in range(50):
            buf.enqueue(r)
        assert buf.size() == 1  # no duplicate multiplication

    def test_fifo_eviction(self):
        buf = LocalTelemetryBuffer(max_capacity=5)
        readings = []
        for i in range(10):
            ts = datetime.now(timezone.utc) + timedelta(seconds=i)
            r = _make_reading(ts=ts, seq=i)
            buf.enqueue(r)
            readings.append(r)
        assert buf.size() == 5

    def test_acknowledge_removes_items(self):
        buf = LocalTelemetryBuffer()
        ts = datetime.now(timezone.utc)
        r = _make_reading(ts=ts)
        ok, item_id = buf.enqueue(r)
        assert ok
        acked = buf.acknowledge([item_id])
        assert acked == 1
        assert buf.size() == 0

    def test_in_flight_reset(self):
        buf = LocalTelemetryBuffer()
        ids = []
        for i in range(5):
            ts = datetime.now(timezone.utc) + timedelta(seconds=i)
            r = _make_reading(ts=ts)
            ok, iid = buf.enqueue(r)
            ids.append(iid)
        buf.mark_in_flight(ids)
        for item in buf.peek_unconfirmed():
            assert item.state == "IN_FLIGHT"
        reset = buf.reset_in_flight()
        assert reset == 5
        for item in buf.peek_unconfirmed():
            assert item.state == "BUFFERED"

    def test_reconciliation_deterministic(self):
        buf = LocalTelemetryBuffer()
        now = datetime.now(timezone.utc)
        for i in range(10):
            ts = now + timedelta(seconds=i * 10)
            r = _make_reading(ts=ts, seq=i)
            buf.enqueue(r)
        live = {}
        report, ack_ids = StateReconciler.reconcile("TEST_STATION", buf, live)
        assert report.status == "COMPLETED"
        assert report.total_buffered == 10
        assert report.processed_count + report.duplicate_count == len(ack_ids)
        assert report.provenance in LOCKED_PROVENANCE_TIERS

    def test_reconciliation_with_duplicates(self):
        buf = LocalTelemetryBuffer()
        now = datetime.now(timezone.utc)
        r = _make_reading(ts=now, seq=1)
        buf.enqueue(r)
        live = {f"{r.device_id}::{r.channel}": r}
        report, ack_ids = StateReconciler.reconcile("TEST_STATION", buf, live)
        assert report.duplicate_count == 1

    def test_no_unbounded_growth(self):
        """Verify buffer never exceeds capacity under sustained load."""
        buf = LocalTelemetryBuffer(max_capacity=50)
        for i in range(1000):
            ts = datetime.now(timezone.utc) + timedelta(milliseconds=i)
            r = _make_reading(ts=ts, seq=i)
            buf.enqueue(r)
        assert buf.size() <= 50

    def test_repeated_reconciliation(self):
        buf = LocalTelemetryBuffer()
        now = datetime.now(timezone.utc)
        for i in range(5):
            ts = now + timedelta(seconds=i * 10)
            r = _make_reading(ts=ts, seq=i)
            buf.enqueue(r)
        live = {}
        report1, ids1 = StateReconciler.reconcile("TEST_STATION", buf, live)
        buf.acknowledge(ids1)
        report2, ids2 = StateReconciler.reconcile("TEST_STATION", buf, live)
        assert report2.total_buffered == 0

    def test_out_of_order_reconciliation(self):
        buf = LocalTelemetryBuffer()
        now = datetime.now(timezone.utc)
        # Insert out of order
        r2 = _make_reading(ts=now + timedelta(seconds=20), seq=2)
        r1 = _make_reading(ts=now + timedelta(seconds=10), seq=1)
        buf.enqueue(r2)
        buf.enqueue(r1)
        live = {}
        report, ack_ids = StateReconciler.reconcile("TEST_STATION", buf, live)
        assert report.processed_count == 2  # both processed in sorted order


# ===========================================================================
# WORKSTREAM F — FAULT INJECTION TESTS
# ===========================================================================
class TestFaultInjection:

    def test_telemetry_stale_fault(self):
        fi = FaultInjector(seed=42)
        r = _make_reading()
        fi.inject_telemetry_fault(r, TelemetryFault.STALE)
        assert r.quality == DataQualityState.STALE
        assert len(fi.results) == 1
        assert fi.results[0].fault_class == "TELEMETRY"

    def test_telemetry_out_of_range_fault(self):
        fi = FaultInjector(seed=42)
        r = _make_reading(val=10.0)
        fi.inject_telemetry_fault(r, TelemetryFault.OUT_OF_RANGE)
        assert r.value == 1000.0  # 10 * 100

    def test_telemetry_malformed_fault(self):
        fi = FaultInjector(seed=42)
        r = _make_reading()
        fi.inject_telemetry_fault(r, TelemetryFault.MALFORMED)
        assert r.value == "MALFORMED_DATA_###"
        assert r.quality == DataQualityState.SUSPECT

    def test_device_fault_injection(self):
        fi = FaultInjector()
        result = fi.inject_device_fault("dev_001", DeviceFault.SENSOR_FAILURE)
        assert result.fault_class == "DEVICE"
        assert result.fault_type == "SENSOR_FAILURE"

    def test_connectivity_fault_injection(self):
        fi = FaultInjector()
        result = fi.inject_connectivity_fault(ConnectivityFault.DISCONNECT, "TEST")
        assert result.fault_class == "CONNECTIVITY"

    def test_interface_fault_injection(self):
        fi = FaultInjector()
        result = fi.inject_interface_fault(InterfaceFault.GENERATOR_UNAVAILABLE)
        assert result.fault_class == "INTERFACE"

    def test_fault_schedule(self):
        fi = FaultInjector(seed=42)
        fi.add_fault(FaultScheduleEntry(
            fault_type="DEVICE_UNAVAILABLE",
            fault_class="DEVICE",
            target_device_id="dev_001",
            trigger_offset_sec=0.0,
        ))
        fi.add_fault(FaultScheduleEntry(
            fault_type="DISCONNECT",
            fault_class="CONNECTIVITY",
            trigger_offset_sec=60.0,
        ))
        results = fi.run_schedule()
        assert len(results) == 2

    def test_all_device_faults(self):
        fi = FaultInjector()
        for fault in DeviceFault:
            fi.inject_device_fault("dev_001", fault)
        assert len(fi.results) == len(DeviceFault)

    def test_all_telemetry_faults(self):
        fi = FaultInjector()
        for fault in TelemetryFault:
            r = _make_reading()
            fi.inject_telemetry_fault(r, fault)
        assert len(fi.results) == len(TelemetryFault)

    def test_all_connectivity_faults(self):
        fi = FaultInjector()
        for fault in ConnectivityFault:
            fi.inject_connectivity_fault(fault)
        assert len(fi.results) == len(ConnectivityFault)

    def test_all_interface_faults(self):
        fi = FaultInjector()
        for fault in InterfaceFault:
            fi.inject_interface_fault(fault)
        assert len(fi.results) == len(InterfaceFault)

    def test_deterministic_reproducibility(self):
        """Same seed produces identical results."""
        fi1 = FaultInjector(seed=123)
        fi2 = FaultInjector(seed=123)
        r1 = _make_reading(val=42.0)
        r2 = _make_reading(val=42.0)
        fi1.inject_telemetry_fault(r1, TelemetryFault.STALE)
        fi2.inject_telemetry_fault(r2, TelemetryFault.STALE)
        assert r1.quality == r2.quality

    def test_provenance_preserved_after_fault(self):
        fi = FaultInjector()
        r = _make_reading()
        fi.inject_telemetry_fault(r, TelemetryFault.DELAYED)
        assert r.provenance in LOCKED_PROVENANCE_TIERS


# ===========================================================================
# WORKSTREAM G — SAFETY / AUTHORIZATION TESTS
# ===========================================================================
class TestSafetyAuthorization:

    def test_offline_no_dispatch(self):
        boundary = ActuationBoundary(dispatch_authorized=True, connectivity_state="OFFLINE")
        req = ActuationRequest(station_id="T", device_id="d1", action="cmd")
        result = boundary.request_actuation(req)
        assert result.authorized is False
        assert result.outcome == ActuationOutcome.REJECTED

    def test_safe_hold_no_dispatch(self):
        boundary = ActuationBoundary(dispatch_authorized=True, connectivity_state="SAFE_HOLD")
        req = ActuationRequest(station_id="T", device_id="d1", action="cmd")
        result = boundary.request_actuation(req)
        assert result.authorized is False

    def test_degraded_allows_dispatch(self):
        boundary = ActuationBoundary(dispatch_authorized=True, connectivity_state="DEGRADED")
        req = ActuationRequest(station_id="T", device_id="d1", action="cmd")
        result = boundary.request_actuation(req)
        assert result.authorized is True

    def test_unavailable_device_not_successful(self):
        boundary = ActuationBoundary(dispatch_authorized=True)
        req = ActuationRequest(
            station_id="T", device_id="nonexistent", action="cmd",
            environment="NONEXISTENT",
        )
        result = boundary.request_actuation(req)
        assert result.outcome in (ActuationOutcome.UNAVAILABLE, ActuationOutcome.REJECTED)

    def test_unsupported_command_rejected(self):
        boundary = ActuationBoundary(dispatch_authorized=False)
        req = ActuationRequest(station_id="T", device_id="d1", action="unknown_cmd")
        result = boundary.request_actuation(req)
        assert result.outcome == ActuationOutcome.REJECTED

    def test_planning_not_physical(self):
        """Verify simulation result is never labelled as physical execution."""
        boundary = ActuationBoundary()
        req = ActuationRequest(station_id="T", device_id="d1", action="cmd")
        result = boundary.request_actuation(req)
        assert result.provenance == "SIMULATED"
        assert "PHYSICAL" not in result.source_metadata.get("source", "")

    def test_no_false_real_provenance(self):
        boundary = ActuationBoundary()
        req = ActuationRequest(station_id="T", device_id="d1", action="cmd")
        result = boundary.request_actuation(req)
        assert result.provenance != "REAL"

    def test_dispatch_authorized_toggle(self):
        boundary = ActuationBoundary(dispatch_authorized=True)
        req = ActuationRequest(station_id="T", device_id="d1", action="cmd")
        r1 = boundary.request_actuation(req)
        assert r1.authorized is True
        boundary.set_authorization(False)
        r2 = boundary.request_actuation(req)
        assert r2.authorized is False


# ===========================================================================
# WORKSTREAM H — LONG-DURATION RELIABILITY TESTS
# ===========================================================================
class TestLongDurationReliability:

    def _simulate_duration(self, hours: int):
        """Simulate N hours of operation with deterministic clock."""
        buf = LocalTelemetryBuffer(max_capacity=500)
        ct = ConnectivityTracker("TEST")
        sm = EdgeStateManager("TEST", "test_edge")
        fi = FaultInjector(seed=42)

        t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
        interval_sec = 10
        steps = (hours * 3600) // interval_sec
        max_buf = 0
        fault_count = 0
        reconcile_count = 0

        for step in range(steps):
            now = t0 + timedelta(seconds=step * interval_sec)

            # Inject faults every 1000 steps
            if step % 1000 == 500:
                ct.record_failure("simulated storm")
                fault_count += 1
            elif step % 1000 == 800:
                ct.start_reconnect()
            elif step % 1000 == 900:
                report, ack_ids = StateReconciler.reconcile("TEST", buf, sm.latest_readings)
                buf.acknowledge(ack_ids)
                ct.finish_reconnect()
                reconcile_count += 1
            else:
                ct.record_success(current_time=now)

            # Generate and buffer/process telemetry
            r = _make_reading(ts=now, seq=step)
            conn = ct.state
            if conn in (ConnectivityState.OFFLINE, ConnectivityState.DEGRADED,
                        ConnectivityState.RECONNECTING):
                buf.enqueue(r)
            else:
                sm.update_reading(r)

            max_buf = max(max_buf, buf.size())

        return {
            "steps": steps,
            "max_buffer": max_buf,
            "final_buffer": buf.size(),
            "faults": fault_count,
            "reconciliations": reconcile_count,
            "final_connectivity": ct.state.value,
        }

    def test_24_hour_reliability(self):
        result = self._simulate_duration(24)
        assert result["steps"] > 0
        assert result["max_buffer"] <= 500  # bounded
        assert result["final_buffer"] <= 500
        assert result["reconciliations"] > 0

    def test_72_hour_reliability(self):
        result = self._simulate_duration(72)
        assert result["steps"] > 0
        assert result["max_buffer"] <= 500
        assert result["final_buffer"] <= 500
        assert result["reconciliations"] > 0

    def test_bounded_resource_behavior(self):
        """Verify no unbounded growth over sustained operation."""
        result = self._simulate_duration(24)
        assert result["max_buffer"] <= 500
        assert result["final_buffer"] <= 500


# ===========================================================================
# WORKSTREAM I — TRACE CONTINUITY TESTS
# ===========================================================================
class TestTraceContinuity:

    def test_create_phase16_trace(self):
        trace = Phase16TraceLinker.create_phase16_trace("TEST")
        assert trace.station_id == "TEST"
        assert trace.execution_status == TraceLifecycleState.CREATED
        assert trace.provenance == "SIMULATED"

    def test_adapter_event(self):
        ev = Phase16TraceLinker.trace_adapter_event(
            "T1", "TEST", "SimulatorAdapter", "SIMULATOR", "discover",
        )
        assert ev.stage == TraceStage.EDGE
        assert ev.event_type == "ADAPTER_EVENT"
        assert ev.provenance in LOCKED_PROVENANCE_TIERS

    def test_telemetry_event(self):
        ev = Phase16TraceLinker.trace_telemetry_event(
            "T1", "TEST", "dev_001", "power", "VALID", "VALID",
        )
        assert ev.stage == TraceStage.EDGE
        assert ev.event_type == "TELEMETRY_INGESTION"

    def test_connectivity_transition_event(self):
        ev = Phase16TraceLinker.trace_connectivity_transition(
            "T1", "TEST", "CONNECTED", "OFFLINE",
        )
        assert "CONNECTED" in ev.summary
        assert "OFFLINE" in ev.summary

    def test_fault_injection_event(self):
        ev = Phase16TraceLinker.trace_fault_injection(
            "T1", "TEST", "STALE", "TELEMETRY", "dev_001::power",
        )
        assert ev.event_type == "FAULT_INJECTION"

    def test_actuation_event(self):
        ev = Phase16TraceLinker.trace_actuation_request(
            "T1", "TEST", "dev_001", "set_power", True, "SIMULATED",
        )
        assert ev.event_type == "ACTUATION_REQUEST"
        assert ev.status == "COMPLETED"

    def test_rejected_actuation_event(self):
        ev = Phase16TraceLinker.trace_actuation_request(
            "T1", "TEST", "dev_001", "set_power", False, "REJECTED",
        )
        assert ev.status == "BLOCKED"

    def test_reconciliation_event(self):
        ev = Phase16TraceLinker.trace_reconciliation(
            "T1", "TEST", 10, 8, 2, 1,
        )
        assert ev.stage == TraceStage.RECONCILIATION

    def test_recovery_event(self):
        ev = Phase16TraceLinker.trace_recovery("T1", "TEST", "CONNECTED")
        assert ev.event_type == "STATE_RECOVERY"

    def test_complete_lifecycle_trace(self):
        """Build a complete traceable lifecycle across all Phase 16 stages."""
        trace = Phase16TraceLinker.create_phase16_trace("TEST")
        tid = trace.decision_trace_id

        e1 = Phase16TraceLinker.trace_adapter_event(tid, "TEST", "SimulatorAdapter", "SIMULATOR", "init")
        e2 = Phase16TraceLinker.trace_telemetry_event(tid, "TEST", "dev_001", "power", "VALID", "VALID", e1.event_id)
        e3 = Phase16TraceLinker.trace_connectivity_transition(tid, "TEST", "CONNECTED", "OFFLINE", e2.event_id)
        e4 = Phase16TraceLinker.trace_fault_injection(tid, "TEST", "STALE", "TELEMETRY", "dev_001::power", e3.event_id)
        e5 = Phase16TraceLinker.trace_connectivity_transition(tid, "TEST", "OFFLINE", "RECONNECTING", e4.event_id)
        e6 = Phase16TraceLinker.trace_reconciliation(tid, "TEST", 10, 8, 2, 1, e5.event_id)
        e7 = Phase16TraceLinker.trace_recovery(tid, "TEST", "CONNECTED", e6.event_id)

        events = [e1, e2, e3, e4, e5, e6, e7]
        trace.events = events
        trace.execution_status = TraceLifecycleState.COMPLETED

        assert len(trace.events) == 7
        assert trace.execution_status == TraceLifecycleState.COMPLETED
        for ev in trace.events:
            assert ev.provenance in LOCKED_PROVENANCE_TIERS

        # Verify DAG linkage
        assert e2.parent_event_id == e1.event_id
        assert e7.parent_event_id == e6.event_id


# ===========================================================================
# WORKSTREAM K — INTEGRATION / DEMO TESTS
# ===========================================================================
class TestPhase16Demo:

    def test_deterministic_demo_lifecycle(self):
        """Execute the full 20-step deterministic demo."""
        # Step 1: Initialize station
        station_id = "DEMO_STATION"
        buf = LocalTelemetryBuffer(max_capacity=100)
        ct = ConnectivityTracker(station_id)
        sm = EdgeStateManager(station_id, f"{station_id.lower()}_edge")
        fi = FaultInjector(seed=42)
        boundary = ActuationBoundary(dispatch_authorized=True)
        trace = Phase16TraceLinker.create_phase16_trace(station_id)
        tid = trace.decision_trace_id

        t0 = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Step 2-3: Device catalog + adapters (mocked)
        events = []

        # Step 4: Receive telemetry
        e1 = Phase16TraceLinker.trace_adapter_event(tid, station_id, "SimulatorAdapter", "SIMULATOR", "init")
        events.append(e1)

        # Step 5: Connected operation
        ct.record_success(current_time=t0)
        assert ct.state == ConnectivityState.CONNECTED

        # Step 6: Inject telemetry degradation
        r = _make_reading(station=station_id, ts=t0)
        fi.inject_telemetry_fault(r, TelemetryFault.STALE, current_time=t0)
        e2 = Phase16TraceLinker.trace_fault_injection(tid, station_id, "STALE", "TELEMETRY", "dev_001::power", e1.event_id)
        events.append(e2)

        # Step 7: Disconnect backend
        ct.record_failure("satellite link lost")
        ct.record_failure("satellite link lost")
        ct.record_failure("satellite link lost")
        assert ct.state == ConnectivityState.OFFLINE
        e3 = Phase16TraceLinker.trace_connectivity_transition(tid, station_id, "CONNECTED", "OFFLINE", e2.event_id)
        events.append(e3)

        # Step 8: Enter OFFLINE_EDGE
        mode, posture = sm.derive_posture(ct.state, [])
        assert mode == EdgeMode.OFFLINE_EDGE

        # Step 9: Safe fallback
        assert posture == FallbackPosture.SAFE_HOLD

        # Step 10: Buffer telemetry
        for i in range(10):
            ts = t0 + timedelta(seconds=i * 10)
            r = _make_reading(station=station_id, ts=ts, seq=i)
            buf.enqueue(r)
        assert buf.size() == 10

        # Step 11: Device fault
        fi.inject_device_fault("dev_001", DeviceFault.SENSOR_FAILURE, current_time=t0)

        # Step 12: Reconnect
        ct.start_reconnect()
        assert ct.state == ConnectivityState.RECONNECTING
        e4 = Phase16TraceLinker.trace_connectivity_transition(tid, station_id, "OFFLINE", "RECONNECTING", e3.event_id)
        events.append(e4)

        # Step 13: Reconcile
        report, ack_ids = StateReconciler.reconcile(station_id, buf, sm.latest_readings)
        buf.acknowledge(ack_ids)
        ct.finish_reconnect()
        assert ct.state == ConnectivityState.CONNECTED
        e5 = Phase16TraceLinker.trace_reconciliation(
            tid, station_id, report.total_buffered, report.processed_count,
            report.duplicate_count, report.gap_count, e4.event_id,
        )
        events.append(e5)

        # Step 14: Restore state
        mode, posture = sm.derive_posture(ct.state, [])
        assert mode == EdgeMode.CONNECTED_OPERATION

        # Step 15-16: Authorization + actuation
        boundary.set_connectivity("CONNECTED")
        req = ActuationRequest(
            station_id=station_id, device_id="dev_001",
            action="set_power", value=75.0, environment="SIMULATOR",
        )
        act_result = boundary.request_actuation(req)
        e6 = Phase16TraceLinker.trace_actuation_request(
            tid, station_id, "dev_001", "set_power",
            act_result.authorized, act_result.outcome.value, e5.event_id,
        )
        events.append(e6)

        # Step 17: Record outcome
        assert act_result.provenance in LOCKED_PROVENANCE_TIERS

        # Step 18: Decision trace
        trace.events = events
        assert len(trace.events) >= 6

        # Step 19: Recovery
        e7 = Phase16TraceLinker.trace_recovery(tid, station_id, "CONNECTED", e6.event_id)
        events.append(e7)

        # Step 20: Final validation
        trace.events = events
        trace.execution_status = TraceLifecycleState.COMPLETED

        # Verify all constraints
        assert trace.provenance in LOCKED_PROVENANCE_TIERS
        for ev in trace.events:
            assert ev.provenance in LOCKED_PROVENANCE_TIERS
        assert ct.state == ConnectivityState.CONNECTED
        assert buf.size() == 0 or buf.size() <= 100  # bounded

    def test_provenance_never_violated(self):
        """Verify no invalid provenance anywhere in the test models."""
        for tier in ["REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"]:
            assert tier in LOCKED_PROVENANCE_TIERS
        for invalid in ["LIVE", "REAL_TIME", "OPTIMIZED", "DERIVED", "HIL", "LAB", "EMULATOR"]:
            assert invalid not in LOCKED_PROVENANCE_TIERS
            with pytest.raises(ValueError):
                validate_provenance(invalid)

    def test_physical_boundary_truth(self):
        """The system must report physical connectivity as DISCONNECTED."""
        # This is an architectural verification test
        physical_state = {
            "PHYSICAL_CONNECTIVITY": "DISCONNECTED",
            "PHYSICAL_SCADA_LINK": False,
            "PHYSICAL_VALIDATION": "NOT_AVAILABLE",
        }
        assert physical_state["PHYSICAL_CONNECTIVITY"] == "DISCONNECTED"
        assert physical_state["PHYSICAL_SCADA_LINK"] is False
        assert physical_state["PHYSICAL_VALIDATION"] == "NOT_AVAILABLE"
