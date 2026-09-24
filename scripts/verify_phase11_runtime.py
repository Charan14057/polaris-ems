"""
POLARIS-EMS — Phase 11 Live Runtime Verification Script
SIH26061: Polar Energy Management & Resilience System

Validates live integration through Vite reverse proxy (http://127.0.0.1:3000 -> :8000)
for all Phase 11 Edge & Field Device Intelligence endpoints.
"""

import sys
import httpx

BASE_URL = "http://127.0.0.1:3000"
LOCKED_PROVENANCE_TIERS = {"REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"}


def check_provenance(prov: str, context: str):
    if prov not in LOCKED_PROVENANCE_TIERS:
        print(f"[FAIL] {context}: Provenance '{prov}' violates locked 6-tier taxonomy!")
        sys.exit(1)


def main():
    print("=" * 80)
    print("POLARIS-EMS PHASE 11: EDGE & DEVICE INTELLIGENCE RUNTIME AUDIT")
    print(f"Target Gateway: {BASE_URL}")
    print("=" * 80)

    client = httpx.Client(base_url=BASE_URL, timeout=60.0)

    # Gate 1: Edge State
    resp = client.get("/api/v1/edge/BHARATI/state")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    state_json = resp.json()
    check_provenance(state_json["provenance"], "Gate 1")
    edge_mode = state_json["data"]["edge_mode"]
    posture = state_json["data"]["fallback_posture"]
    print(f"[PASS] Gate 1: Edge State retrieved. Mode={edge_mode}, Posture={posture}, Prov={state_json['provenance']}")

    # Gate 2: Device Fleet Catalog
    resp = client.get("/api/v1/edge/BHARATI/devices")
    assert resp.status_code == 200
    devs_json = resp.json()
    check_provenance(devs_json["provenance"], "Gate 2")
    devs = devs_json["data"]
    dev_types = {d["device_type"] for d in devs}
    assert len(devs) >= 10, f"Expected at least 10 devices, got {len(devs)}"
    print(f"[PASS] Gate 2: Device Fleet Catalog. Total={len(devs)} devices, Classes={len(dev_types)}")

    # Gate 3: Latest Telemetry
    resp = client.get("/api/v1/edge/BHARATI/telemetry")
    assert resp.status_code == 200
    tel_json = resp.json()
    check_provenance(tel_json["provenance"], "Gate 3")
    print(f"[PASS] Gate 3: Latest Telemetry. Total observations={len(tel_json['data'])}, Prov={tel_json['provenance']}")

    # Gate 4: Device Health
    resp = client.get("/api/v1/edge/BHARATI/health")
    assert resp.status_code == 200
    hl_json = resp.json()
    check_provenance(hl_json["provenance"], "Gate 4")
    healthy_cnt = sum(1 for h in hl_json["data"] if h["health_state"] == "HEALTHY")
    print(f"[PASS] Gate 4: Device Fleet Health. Total={len(hl_json['data'])}, Healthy={healthy_cnt}")

    # Gate 5: Connectivity Status
    resp = client.get("/api/v1/edge/BHARATI/connectivity")
    assert resp.status_code == 200
    conn_json = resp.json()
    check_provenance(conn_json["provenance"], "Gate 5")
    conn_state = conn_json["data"]["connectivity_state"]
    buf_cnt = conn_json["data"]["buffered_count"]
    print(f"[PASS] Gate 5: Connectivity Status. Link={conn_state}, Buffer Depth={buf_cnt}")

    # Gate 6: Telemetry Ingestion & Validation
    ingest_payload = {
        "readings": [
            {
                "device_id": "bh_gen_01",
                "channel": "power_output_kw",
                "value": 65.5,
                "unit": "kW",
                "provenance": "SYNTHETIC"
            },
            {
                "device_id": "bh_bess_01",
                "channel": "soc_fraction",
                "value": 0.75,
                "unit": "ratio",
                "provenance": "SYNTHETIC"
            }
        ]
    }
    resp = client.post("/api/v1/edge/BHARATI/telemetry/ingest", json=ingest_payload)
    assert resp.status_code == 200
    ing_json = resp.json()
    check_provenance(ing_json["provenance"], "Gate 6")
    assert ing_json["data"]["accepted_count"] == 2
    print(f"[PASS] Gate 6: Telemetry Ingest. Accepted={ing_json['data']['accepted_count']}, Rejected={ing_json['data']['rejected_count']}")

    # Gate 7: Decision Pathway Evaluation (Connected)
    resp = client.post("/api/v1/edge/BHARATI/evaluate")
    assert resp.status_code == 200
    eval_json = resp.json()
    check_provenance(eval_json["provenance"], "Gate 7")
    pathway = eval_json["data"]["pathway"]
    authorized = eval_json["data"]["dispatch_authorized"]
    print(f"[PASS] Gate 7: Decision Pathway Evaluation. Pathway={pathway}, Dispatch Authorized={authorized}")

    # Gate 8: Simulation Condition & Buffer Accumulation (Offline)
    resp = client.post("/api/v1/edge/BHARATI/simulate-condition", json={"condition": "OFFLINE"})
    assert resp.status_code == 200
    # Ingest while offline -> must increase buffer
    resp_ing_off = client.post("/api/v1/edge/BHARATI/telemetry/ingest", json=ingest_payload)
    assert resp_ing_off.status_code == 200
    assert resp_ing_off.json()["data"]["buffered_count"] >= 1
    # Evaluate decision while offline -> must enforce local fallback posture, NOT optimization
    resp_eval_off = client.post("/api/v1/edge/BHARATI/evaluate")
    assert resp_eval_off.status_code == 200
    off_data = resp_eval_off.json()["data"]
    assert off_data["pathway"] == "LOCAL_EDGE_FALLBACK"
    assert not off_data["dispatch_authorized"]
    print(f"[PASS] Gate 8: Offline Fallback & Buffer Growth. Buffered={resp_ing_off.json()['data']['buffered_count']}, Pathway={off_data['pathway']}")

    # Gate 9: Reconnection & Buffer Sync
    resp_sync = client.post("/api/v1/edge/BHARATI/sync")
    assert resp_sync.status_code == 200
    sync_json = resp_sync.json()
    check_provenance(sync_json["provenance"], "Gate 9")
    sync_data = sync_json["data"]
    print(f"[PASS] Gate 9: Reconnection & Buffer Sync. Reconciled={sync_data['processed_count']} items in {sync_data['execution_duration_ms']}ms")

    # Restore normal condition
    client.post("/api/v1/edge/BHARATI/simulate-condition", json={"condition": "NORMAL"})

    # Gate 10: Dynamic Station Coverage (Maitri & Himadri)
    resp_mt = client.get("/api/v1/edge/MAITRI/state")
    resp_hm = client.get("/api/v1/edge/HIMADRI/state")
    assert resp_mt.status_code == 200
    assert resp_hm.status_code == 200
    print(f"[PASS] Gate 10: Multi-Station Dynamic Coverage. Maitri & Himadri verified.")

    print("=" * 80)
    print("ALL 10 PHASE 11 RUNTIME & PROVENANCE AUDIT GATES PASSED (100%)")
    print("=" * 80)


if __name__ == "__main__":
    main()
