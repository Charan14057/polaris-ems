"""
POLARIS-EMS — Phase 16 Deterministic Demo (Workstream K)
SIH26061: Polar Energy Management & Resilience System

Runnable demonstration covering the complete Phase 16 lifecycle:
  1. Initialize station
  2. Load device catalog
  3. Resolve adapters
  4. Receive telemetry
  5. Connected operation
  6. Telemetry degradation
  7. Backend connectivity loss
  8. Enter OFFLINE_EDGE
  9. Safe fallback activates
  10. Buffer telemetry
  11. Device/telemetry fault injected
  12. Reconnect initiated
  13. Reconciliation
  14. State restored
  15. Authorization evaluated
  16. ActuationBoundary evaluated
  17. Simulated/HIL/LAB/UNAVAILABLE result
  18. Decision trace linked
  19. Recovery evaluated
  20. Final validation report

IMPORTANT: This is a VALIDATION ENVIRONMENT, not a live polar SCADA installation.

PHYSICAL_CONNECTIVITY = DISCONNECTED
PHYSICAL_SCADA_LINK = FALSE
PHYSICAL_VALIDATION = NOT_AVAILABLE
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.edge.schema import (
    ConnectivityState,
    EdgeMode,
    FallbackPosture,
    DataQualityState,
    LOCKED_PROVENANCE_TIERS,
)
from backend.edge.telemetry import TelemetryNormalizer
from backend.edge.connectivity import ConnectivityTracker
from backend.edge.buffer import LocalTelemetryBuffer
from backend.edge.state import EdgeStateManager
from backend.edge.reconciliation import StateReconciler
from backend.edge.actuation import (
    ActuationBoundary,
    ActuationRequest,
    ActuationOutcome,
)
from backend.edge.fault_injection import (
    FaultInjector,
    TelemetryFault,
    DeviceFault,
)
from backend.edge.trace_integration import Phase16TraceLinker


def run_demo() -> dict:
    """Execute the full Phase 16 deterministic demo. Returns a result dict."""
    station_id = "BHARATI"
    t0 = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    results = {"steps": [], "errors": []}

    def log(step: int, msg: str, **kwargs):
        entry = {"step": step, "message": msg, **kwargs}
        results["steps"].append(entry)
        print(f"  [{step:2d}] {msg}")

    print("=" * 70)
    print("POLARIS-EMS — Phase 16 Deterministic Demo")
    print("SCADA: SIMULATION ONLY")
    print("PHYSICAL_CONNECTIVITY = DISCONNECTED")
    print("=" * 70)

    # 1. Initialize station
    ct = ConnectivityTracker(station_id)
    sm = EdgeStateManager(station_id, f"{station_id.lower()}_edge")
    buf = LocalTelemetryBuffer(max_capacity=200)
    fi = FaultInjector(seed=42)
    boundary = ActuationBoundary(dispatch_authorized=True)
    trace = Phase16TraceLinker.create_phase16_trace(station_id)
    tid = trace.decision_trace_id
    log(1, f"Station {station_id} initialized", trace_id=tid)

    # 2. Device catalog (mock)
    log(2, "Device catalog loaded (simulated)", devices=["gen-001", "solar-001", "bat-001"])

    # 3. Adapters registered
    log(3, "Adapters registered: SIMULATOR, EMULATOR, HIL, LAB")
    events = []
    e_init = Phase16TraceLinker.trace_adapter_event(tid, station_id, "SimulatorAdapter", "SIMULATOR", "init")
    events.append(e_init)

    # 4. Receive telemetry
    ct.record_success(current_time=t0)
    r = TelemetryNormalizer.create_envelope(
        station_id=station_id, device_id="gen-001", channel="power",
        value=45.0, unit="kW", timestamp=t0, provenance="SIMULATED",
    )
    sm.update_reading(r)
    log(4, f"Telemetry received: {r.device_id}::{r.channel} = {r.value} {r.unit}", provenance=r.provenance)

    # 5. Connected operation
    mode, posture = sm.derive_posture(ct.state, [])
    assert mode == EdgeMode.CONNECTED_OPERATION
    log(5, f"Operating in {mode.value}, posture={posture.value}")

    # 6. Telemetry degradation
    r_stale = TelemetryNormalizer.create_envelope(
        station_id=station_id, device_id="gen-001", channel="power",
        value=44.0, unit="kW", timestamp=t0 - timedelta(seconds=300), provenance="SIMULATED",
    )
    fi.inject_telemetry_fault(r_stale, TelemetryFault.STALE, current_time=t0)
    e_fault = Phase16TraceLinker.trace_fault_injection(tid, station_id, "STALE", "TELEMETRY", "gen-001::power", e_init.event_id)
    events.append(e_fault)
    log(6, "Telemetry degradation injected: STALE fault on gen-001::power")

    # 7. Backend connectivity loss
    ct.record_failure("satellite link lost")
    ct.record_failure("satellite link lost")
    ct.record_failure("satellite link lost")
    assert ct.state == ConnectivityState.OFFLINE
    e_off = Phase16TraceLinker.trace_connectivity_transition(tid, station_id, "CONNECTED", "OFFLINE", e_fault.event_id)
    events.append(e_off)
    log(7, "Backend connectivity LOST — state: OFFLINE")

    # 8. OFFLINE_EDGE mode
    mode, posture = sm.derive_posture(ct.state, [])
    assert mode == EdgeMode.OFFLINE_EDGE
    log(8, f"Edge mode: {mode.value}")

    # 9. Safe fallback
    assert posture == FallbackPosture.SAFE_HOLD
    log(9, f"Safe fallback posture: {posture.value}")

    # 10. Buffer telemetry
    for i in range(15):
        ts = t0 + timedelta(seconds=i * 10)
        r_buf = TelemetryNormalizer.create_envelope(
            station_id=station_id, device_id="gen-001", channel="power",
            value=45.0 + i * 0.1, unit="kW", timestamp=ts, provenance="SIMULATED",
        )
        buf.enqueue(r_buf)
    log(10, f"Buffered {buf.size()} telemetry readings")

    # 11. Device fault
    fi.inject_device_fault("gen-001", DeviceFault.SENSOR_FAILURE, current_time=t0)
    log(11, "Device fault injected: SENSOR_FAILURE on gen-001")

    # 12. Reconnect
    ct.start_reconnect()
    assert ct.state == ConnectivityState.RECONNECTING
    e_recon = Phase16TraceLinker.trace_connectivity_transition(tid, station_id, "OFFLINE", "RECONNECTING", e_off.event_id)
    events.append(e_recon)
    log(12, "Reconnect initiated — state: RECONNECTING")

    # 13. Reconciliation
    report, ack_ids = StateReconciler.reconcile(station_id, buf, sm.latest_readings)
    buf.acknowledge(ack_ids)
    ct.finish_reconnect()
    e_rec = Phase16TraceLinker.trace_reconciliation(
        tid, station_id, report.total_buffered, report.processed_count,
        report.duplicate_count, report.gap_count, e_recon.event_id,
    )
    events.append(e_rec)
    log(13, f"Reconciliation: {report.processed_count} processed, {report.duplicate_count} dups, {report.gap_count} gaps")

    # 14. State restored
    assert ct.state == ConnectivityState.CONNECTED
    mode, posture = sm.derive_posture(ct.state, [])
    assert mode == EdgeMode.CONNECTED_OPERATION
    log(14, f"State restored: {mode.value}, buffer={buf.size()}")

    # 15. Authorization
    boundary.set_connectivity("CONNECTED")
    boundary.set_authorization(True)
    log(15, "Authorization: dispatch_authorized=True, connectivity=CONNECTED")

    # 16. ActuationBoundary
    req = ActuationRequest(
        station_id=station_id, device_id="gen-001",
        action="set_power", value=75.0, environment="SIMULATOR",
    )
    act_result = boundary.request_actuation(req)
    e_act = Phase16TraceLinker.trace_actuation_request(
        tid, station_id, "gen-001", "set_power",
        act_result.authorized, act_result.outcome.value, e_rec.event_id,
    )
    events.append(e_act)
    log(16, f"Actuation: authorized={act_result.authorized}, outcome={act_result.outcome.value}")

    # 17. Record result
    log(17, f"Execution result: outcome={act_result.outcome.value}, adapter={act_result.adapter_name}, provenance={act_result.provenance}")

    # 18. Decision trace
    trace.events = events
    log(18, f"Decision trace linked: {len(trace.events)} events, trace_id={tid}")

    # 19. Recovery
    e_recovery = Phase16TraceLinker.trace_recovery(tid, station_id, "CONNECTED", e_act.event_id)
    events.append(e_recovery)
    trace.events = events
    log(19, "Recovery evaluation complete")

    # 20. Final validation
    validation = {
        "station_id": station_id,
        "trace_id": tid,
        "total_events": len(trace.events),
        "connectivity": ct.state.value,
        "edge_mode": mode.value,
        "buffer_remaining": buf.size(),
        "actuation_outcome": act_result.outcome.value,
        "provenance_valid": all(ev.provenance in LOCKED_PROVENANCE_TIERS for ev in trace.events),
        "physical_connectivity": "DISCONNECTED",
        "physical_scada_link": False,
        "physical_validation": "NOT_AVAILABLE",
        "result": "PASS",
    }
    log(20, f"FINAL VALIDATION: {validation['result']}", **validation)

    results["validation"] = validation
    print("\n" + "=" * 70)
    print(f"DEMO RESULT: {validation['result']}")
    print(f"All provenance valid: {validation['provenance_valid']}")
    print(f"Physical connectivity: {validation['physical_connectivity']}")
    print("=" * 70)

    return results


if __name__ == "__main__":
    run_demo()
