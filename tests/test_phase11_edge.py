"""
POLARIS-EMS — Phase 11 Edge Resilience & Device Intelligence Test Suite
SIH26061: Polar Energy Management & Resilience System

Validates:
1. Device Registry: all 10 device classes across BHARATI, MAITRI, HIMADRI.
2. Telemetry Normalization & Quality: range, unit, freshness, duplicate, sequence.
3. Device Health: healthy, degraded, unavailable, fault, unknown.
4. Connectivity State Machine: connected, degraded, offline, reconnecting.
5. Local Bounded Buffer: FIFO eviction, deduplication, acknowledged lifecycle.
6. Reconnection Reconciliation: newer data wins, older logged, duplicates dropped, gaps flagged.
7. Edge Mode & Fallback: non-optimizing safety postures.
8. Architectural Boundaries: zero Pyomo/HiGHS solvers, zero duplicate physics.
9. API Endpoints: GET/POST routes, provenance preservation, 404/422 error contracts.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.edge.schema import (
    DeviceType,
    DataQualityState,
    DeviceHealthState,
    ConnectivityState,
    EdgeMode,
    FallbackPosture,
    TelemetryReading,
    LOCKED_PROVENANCE_TIERS,
    validate_provenance
)
from backend.edge.devices import DeviceRegistry, get_device_registry
from backend.edge.telemetry import TelemetryNormalizer
from backend.edge.quality import TelemetryQualityEngine
from backend.edge.health import DeviceHealthEngine
from backend.edge.connectivity import ConnectivityTracker
from backend.edge.buffer import LocalTelemetryBuffer
from backend.edge.state import EdgeStateManager
from backend.edge.reconciliation import StateReconciler
from backend.edge.simulation import EdgeSimulationHarness
from backend.edge.adapters import EdgeToTwinAdapter, EdgeDecisionBridge
from backend.edge.engine import EdgeEngine, get_edge_engine
from backend.api.app import create_app


# =========================================================================
# 1. Device Model & Registry Tests
# =========================================================================

def test_device_registry_stations_and_classes():
    reg = DeviceRegistry()
    stations = reg.list_stations()
    assert "BHARATI" in stations
    assert "MAITRI" in stations
    assert "HIMADRI" in stations

    for sid in ["BHARATI", "MAITRI", "HIMADRI"]:
        catalog = reg.get_catalog(sid)
        assert len(catalog.devices) > 0
        device_types = {d.device_type for d in catalog.devices}
        # Verify core critical types are present
        assert DeviceType.DIESEL_GENERATOR in device_types
        assert DeviceType.BATTERY in device_types
        assert DeviceType.WEATHER in device_types
        assert DeviceType.POWER_METER in device_types
        assert DeviceType.FUEL in device_types

    # Verify Bharati covers all 10 device classes
    bh_types = {d.device_type for d in reg.list_devices("BHARATI")}
    expected_10 = {
        DeviceType.SOLAR,
        DeviceType.WIND,
        DeviceType.DIESEL_GENERATOR,
        DeviceType.BATTERY,
        DeviceType.THERMAL,
        DeviceType.WEATHER,
        DeviceType.POWER_METER,
        DeviceType.FUEL,
        DeviceType.GPS,
        DeviceType.COMMUNICATIONS
    }
    assert expected_10.issubset(bh_types)


def test_device_registry_lookup_and_mismatch():
    reg = DeviceRegistry()
    assert reg.has_device("BHARATI", "bh_gen_01")
    assert not reg.has_device("BHARATI", "non_existent_device")
    assert not reg.has_device("MAITRI", "bh_gen_01")  # Station mismatch

    with pytest.raises(KeyError):
        reg.get_device("BHARATI", "non_existent_device")

    with pytest.raises(KeyError):
        reg.get_catalog("UNKNOWN_STATION")


# =========================================================================
# 2. Telemetry Normalization & Quality Engine Tests
# =========================================================================

def test_telemetry_normalization_provenance():
    # Valid locked provenance
    reading = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=50.0,
        unit="kW",
        provenance="SYNTHETIC"
    )
    assert reading.provenance == "SYNTHETIC"
    assert reading.validation_status == "ACCEPTED"

    # Invalid provenance must raise ValueError
    with pytest.raises(ValueError):
        TelemetryNormalizer.create_envelope(
            station_id="BHARATI",
            device_id="bh_gen_01",
            channel="power_output_kw",
            value=50.0,
            unit="kW",
            provenance="LIVE_TELEMETRY"  # 7th tier violation!
        )


def test_quality_engine_deterministic_checks():
    reg = DeviceRegistry()
    qe = TelemetryQualityEngine(reg)
    now = datetime.now(timezone.utc)

    # 1. Nominal valid reading
    r_valid = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=60.0,
        unit="kW",
        timestamp=now
    )
    res = qe.validate(r_valid, current_time=now)
    assert res.is_valid
    assert res.quality == DataQualityState.VALID

    # 2. Unknown device -> SUSPECT
    r_bad_dev = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="ghost_sensor",
        channel="power_output_kw",
        value=60.0,
        unit="kW",
        timestamp=now
    )
    res = qe.validate(r_bad_dev, current_time=now)
    assert not res.is_valid
    assert res.quality == DataQualityState.SUSPECT
    assert res.rejection_code == "DEVICE_NOT_REGISTERED"

    # 3. Unit mismatch -> SUSPECT
    r_bad_unit = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=60.0,
        unit="MW",  # Expected kW
        timestamp=now
    )
    res = qe.validate(r_bad_unit, current_time=now)
    assert not res.is_valid
    assert res.quality == DataQualityState.SUSPECT
    assert res.rejection_code == "UNIT_MISMATCH"

    # 4. Out of range -> OUT_OF_RANGE
    r_oor = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=150.0,  # Max is 95.0 kW
        unit="kW",
        timestamp=now
    )
    res = qe.validate(r_oor, current_time=now)
    assert not res.is_valid
    assert res.quality == DataQualityState.OUT_OF_RANGE

    # 5. Future timestamp -> SUSPECT
    r_future = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=50.0,
        unit="kW",
        timestamp=now + timedelta(seconds=120)  # Skew > 60s
    )
    res = qe.validate(r_future, current_time=now)
    assert not res.is_valid
    assert res.quality == DataQualityState.SUSPECT
    assert res.rejection_code == "FUTURE_TIMESTAMP"

    # 6. Duplicate observation -> DUPLICATE
    qe.reset_state()
    r1 = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=50.0,
        unit="kW",
        timestamp=now
    )
    r2 = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=52.0,
        unit="kW",
        timestamp=now  # Same timestamp!
    )
    res1 = qe.validate(r1, current_time=now)
    res2 = qe.validate(r2, current_time=now)
    assert res1.is_valid
    assert not res2.is_valid
    assert res2.quality == DataQualityState.DUPLICATE

    # 7. Out of order sequence -> OUT_OF_ORDER
    qe.reset_state()
    s1 = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=50.0,
        unit="kW",
        timestamp=now - timedelta(seconds=5),
        sequence_number=10
    )
    s2 = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=50.0,
        unit="kW",
        timestamp=now,
        sequence_number=5  # Regressed sequence
    )
    qe.validate(s1, current_time=now)
    res_seq = qe.validate(s2, current_time=now)
    assert not res_seq.is_valid
    assert res_seq.quality == DataQualityState.OUT_OF_ORDER

    # 8. Stale data -> STALE
    r_stale = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=50.0,
        unit="kW",
        timestamp=now - timedelta(seconds=90)  # Exceeds 30s threshold
    )
    res_stale = qe.validate(r_stale, current_time=now)
    assert not res_stale.is_valid
    assert res_stale.quality == DataQualityState.STALE


# =========================================================================
# 3. Device Health Engine Tests
# =========================================================================

def test_device_health_evaluation():
    reg = DeviceRegistry()
    he = DeviceHealthEngine(reg)
    now = datetime.now(timezone.utc)

    # Initial state without telemetry: UNKNOWN
    status = he.evaluate_device("BHARATI", "bh_gen_01", current_time=now)
    assert status.health_state == DeviceHealthState.UNKNOWN

    # Record valid telemetry: HEALTHY
    r = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=60.0,
        unit="kW",
        timestamp=now
    )
    he.record_reading(r)
    status_healthy = he.evaluate_device("BHARATI", "bh_gen_01", current_time=now)
    assert status_healthy.health_state == DeviceHealthState.HEALTHY
    assert status_healthy.health_score == 1.0

    # Delay past freshness threshold (30s): DEGRADED
    later_degraded = now + timedelta(seconds=45)
    status_degraded = he.evaluate_device("BHARATI", "bh_gen_01", current_time=later_degraded)
    assert status_degraded.health_state == DeviceHealthState.DEGRADED

    # Delay past 3x freshness threshold (90s): UNAVAILABLE
    later_unavail = now + timedelta(seconds=120)
    status_unavail = he.evaluate_device("BHARATI", "bh_gen_01", current_time=later_unavail)
    assert status_unavail.health_state == DeviceHealthState.UNAVAILABLE
    assert status_unavail.health_score == 0.0

    # Multiple out-of-range readings: FAULT
    for _ in range(4):
        r_oor = TelemetryNormalizer.create_envelope(
            station_id="BHARATI",
            device_id="bh_gen_01",
            channel="power_output_kw",
            value=120.0,
            unit="kW",
            timestamp=now,
            quality=DataQualityState.OUT_OF_RANGE
        )
        he.record_reading(r_oor)

    status_fault = he.evaluate_device("BHARATI", "bh_gen_01", current_time=now)
    assert status_fault.health_state == DeviceHealthState.FAULT
    assert status_fault.health_score <= 0.3


# =========================================================================
# 4. Connectivity State Machine Tests
# =========================================================================

def test_connectivity_state_machine():
    conn = ConnectivityTracker("BHARATI", degraded_failure_threshold=1, offline_failure_threshold=3)
    now = datetime.now(timezone.utc)

    # Initial state
    status = conn.get_status(current_time=now)
    assert status.connectivity_state == ConnectivityState.CONNECTED

    # 1 failure -> DEGRADED
    conn.record_failure("Dropped packet", current_time=now)
    assert conn.state == ConnectivityState.DEGRADED

    # 3 failures -> OFFLINE
    conn.record_failure("Timeout", current_time=now)
    conn.record_failure("Socket reset", current_time=now)
    assert conn.state == ConnectivityState.OFFLINE
    assert conn.consecutive_failures == 3

    # Reconnect initiation
    conn.set_buffered_count(15)
    conn.start_reconnect()
    assert conn.state == ConnectivityState.RECONNECTING
    assert conn.sync_in_progress

    # Finish reconnect -> CONNECTED
    conn.finish_reconnect()
    assert conn.state == ConnectivityState.CONNECTED
    assert conn.consecutive_failures == 0


# =========================================================================
# 5. Local Telemetry Buffer Tests
# =========================================================================

def test_local_telemetry_buffer_lifecycle():
    buf = LocalTelemetryBuffer(max_capacity=5)
    now = datetime.now(timezone.utc)

    # Enqueue items
    items = []
    for i in range(5):
        r = TelemetryNormalizer.create_envelope(
            station_id="BHARATI",
            device_id="bh_gen_01",
            channel="power_output_kw",
            value=50.0 + i,
            unit="kW",
            timestamp=now + timedelta(seconds=i)
        )
        enqueued, iid = buf.enqueue(r)
        assert enqueued
        items.append(iid)

    assert buf.size() == 5

    # Duplicate rejection
    dup_r = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=50.0,
        unit="kW",
        timestamp=now
    )
    enqueued, msg = buf.enqueue(dup_r)
    assert not enqueued
    assert "Duplicate" in msg
    assert buf.size() == 5

    # FIFO eviction when overflowing capacity
    overflow_r = TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=99.0,
        unit="kW",
        timestamp=now + timedelta(seconds=10)
    )
    enqueued, new_iid = buf.enqueue(overflow_r)
    assert enqueued
    assert buf.size() == 5

    # Peek unconfirmed
    unconf = buf.peek_unconfirmed(limit=3)
    assert len(unconf) == 3

    # Mark in-flight and acknowledge
    buf.mark_in_flight([unconf[0].item_id])
    assert unconf[0].state == "IN_FLIGHT"

    acked = buf.acknowledge([unconf[0].item_id])
    assert acked == 1
    assert buf.size() == 4


# =========================================================================
# 6. Reconnection & State Reconciliation Tests
# =========================================================================

def test_state_reconciliation():
    buf = LocalTelemetryBuffer(max_capacity=100)
    now = datetime.now(timezone.utc)

    # Scenario: Backend has a snapshot at T=100
    t100 = now
    t50 = now - timedelta(seconds=50)  # Older buffered reading
    t120 = now + timedelta(seconds=20)  # Newer buffered reading

    live_snapshots = {
        "bh_gen_01::power_output_kw": TelemetryNormalizer.create_envelope(
            station_id="BHARATI",
            device_id="bh_gen_01",
            channel="power_output_kw",
            value=60.0,
            unit="kW",
            timestamp=t100
        )
    }

    # Buffered:
    # 1. Older reading (t50) -> should be BUFFER_LOGGED (does not overwrite live 60.0)
    # 2. Duplicate reading (t100) -> should be DUPLICATE_DROPPED
    # 3. Newer reading (t120) -> should be ACCEPTED_NEW (updates live snapshot)
    buf.enqueue(TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=55.0,
        unit="kW",
        timestamp=t50
    ))
    buf.enqueue(TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=60.0,
        unit="kW",
        timestamp=t100
    ))
    buf.enqueue(TelemetryNormalizer.create_envelope(
        station_id="BHARATI",
        device_id="bh_gen_01",
        channel="power_output_kw",
        value=72.0,
        unit="kW",
        timestamp=t120
    ))

    report, ack_ids = StateReconciler.reconcile("BHARATI", buf, live_snapshots)

    assert report.total_buffered == 3
    assert report.duplicate_count == 1
    assert report.conflict_count == 1
    assert report.processed_count == 2
    assert len(ack_ids) == 3

    # Live snapshot should now be updated to 72.0 kW (the newest reading)
    assert live_snapshots["bh_gen_01::power_output_kw"].value == 72.0


# =========================================================================
# 7. Edge Mode & Fallback Postures Tests
# =========================================================================

def test_edge_state_fallback_postures():
    sm = EdgeStateManager("BHARATI", "bh_edge_node")

    # 1. Connected nominal
    mode, posture = sm.derive_posture(ConnectivityState.CONNECTED, [])
    assert mode == EdgeMode.CONNECTED_OPERATION
    assert posture == FallbackPosture.WAIT_FOR_BACKEND_DECISION

    # 2. Degraded connectivity
    mode, posture = sm.derive_posture(ConnectivityState.DEGRADED, [])
    assert mode == EdgeMode.DEGRADED_CONNECTIVITY
    assert posture == FallbackPosture.HOLD_LAST_VALIDATED_STATE

    # 3. Offline edge
    mode, posture = sm.derive_posture(ConnectivityState.OFFLINE, [])
    assert mode == EdgeMode.OFFLINE_EDGE
    assert posture == FallbackPosture.SAFE_HOLD


# =========================================================================
# 8. Architecture Boundary Tests (Strict Invariants)
# =========================================================================

def test_architecture_boundary_invariants():
    import sys
    import backend.edge.schema as edge_schema
    import backend.edge.engine as edge_engine
    import backend.edge.adapters as edge_adapters

    # Check imported symbols and inspect source
    for mod in [edge_schema, edge_engine, edge_adapters]:
        source = open(mod.__file__, "r", encoding="utf-8").read()
        assert "import pyomo" not in source
        assert "from pyomo" not in source
        assert "appsi_highs" not in source.lower()
        assert "solverfactory" not in source.lower()
        assert "solve(" not in source

    # Verify locked 6-tier provenance
    assert len(LOCKED_PROVENANCE_TIERS) == 6
    assert "REAL" in LOCKED_PROVENANCE_TIERS
    assert "CONFIGURED" in LOCKED_PROVENANCE_TIERS
    assert "ASSUMED" in LOCKED_PROVENANCE_TIERS
    assert "SYNTHETIC" in LOCKED_PROVENANCE_TIERS
    assert "FORECAST" in LOCKED_PROVENANCE_TIERS
    assert "SIMULATED" in LOCKED_PROVENANCE_TIERS
    assert "LIVE" not in LOCKED_PROVENANCE_TIERS
    assert "REAL_TIME" not in LOCKED_PROVENANCE_TIERS


# =========================================================================
# 9. API Integration Tests (FastAPI TestClient)
# =========================================================================

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_api_edge_endpoints(client):
    # 1. GET /api/v1/edge/BHARATI/state
    resp = client.get("/api/v1/edge/BHARATI/state")
    assert resp.status_code == 200
    json_data = resp.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["data"]["station_id"] == "BHARATI"
    assert json_data["provenance"] in LOCKED_PROVENANCE_TIERS

    # 2. GET /api/v1/edge/BHARATI/devices
    resp = client.get("/api/v1/edge/BHARATI/devices")
    assert resp.status_code == 200
    devs = resp.json()["data"]
    assert len(devs) >= 10

    # 3. GET /api/v1/edge/BHARATI/health
    resp = client.get("/api/v1/edge/BHARATI/health")
    assert resp.status_code == 200
    health = resp.json()["data"]
    assert len(health) >= 10

    # 4. GET /api/v1/edge/BHARATI/connectivity
    resp = client.get("/api/v1/edge/BHARATI/connectivity")
    assert resp.status_code == 200
    conn = resp.json()["data"]
    assert "connectivity_state" in conn

    # 5. POST /api/v1/edge/BHARATI/telemetry/ingest
    ingest_payload = {
        "readings": [
            {
                "device_id": "bh_gen_01",
                "channel": "power_output_kw",
                "value": 55.0,
                "unit": "kW",
                "provenance": "SYNTHETIC"
            }
        ]
    }
    resp = client.post("/api/v1/edge/BHARATI/telemetry/ingest", json=ingest_payload)
    assert resp.status_code == 200
    ing_data = resp.json()["data"]
    assert ing_data["accepted_count"] == 1
    assert ing_data["rejected_count"] == 0

    # 6. POST /api/v1/edge/BHARATI/sync
    resp = client.post("/api/v1/edge/BHARATI/sync")
    assert resp.status_code == 200
    sync_data = resp.json()["data"]
    assert sync_data["status"] == "COMPLETED"

    # 7. POST /api/v1/edge/BHARATI/evaluate
    resp = client.post("/api/v1/edge/BHARATI/evaluate")
    assert resp.status_code == 200
    eval_data = resp.json()["data"]
    assert "pathway" in eval_data

    # 8. 404 for unknown station
    resp_404 = client.get("/api/v1/edge/UNKNOWN_STATION/state")
    assert resp_404.status_code == 404

    # 9. 422 for malformed ingestion payload
    resp_422 = client.post("/api/v1/edge/BHARATI/telemetry/ingest", json={"invalid": "payload"})
    assert resp_422.status_code == 422
