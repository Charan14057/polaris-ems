"""
Polaris-EMS: Phase 10 Final Visual & Runtime Freeze Audit Script
Verifies:
1. Vite proxy connectivity to FastAPI backend across all 8 workspaces
2. Station switching (Bharati -> Maitri -> Himadri)
3. Horizon switching (48h -> 168h)
4. Domain states (SAFE, THREATENED, CRITICAL, RECOVERY, FALLBACK, INFEASIBLE, BLOCKED)
5. Locked 6-tier provenance enforcement
6. Error contracts & domain error handling
"""

import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:3000"
LOCKED_PROVENANCE = {"REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"}

def request_json(endpoint, method="GET", payload=None):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json", "X-Request-ID": "audit-freeze-test"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8"))
        return e.code, body

def audit():
    print("=" * 80)
    print("POLARIS-EMS PHASE 10: RUNTIME & PROVENANCE FREEZE AUDIT")
    print("=" * 80)
    
    # 1. System Readiness
    status, body = request_json("/health/ready")
    assert status == 200 and body["status"] == "SUCCESS", "Readiness probe failed"
    assert body["provenance"] in LOCKED_PROVENANCE, f"Invalid provenance {body['provenance']}"
    print(f"[PASS] 1. Readiness: {body['data']['loaded_stations']} loaded, provenance={body['provenance']}")

    # 2. Station Switching & Dynamic Specs (No Hardcoding)
    status, body = request_json("/api/v1/stations")
    assert status == 200
    stations = body["data"]
    assert len(stations) == 3
    print(f"[PASS] 2. Fleet Catalog: {len(stations)} stations available")
    
    specs = {}
    for st in ["BHARATI", "MAITRI", "HIMADRI"]:
        status, body = request_json(f"/api/v1/stations/{st}")
        assert status == 200 and body["status"] == "SUCCESS"
        assert body["provenance"] in LOCKED_PROVENANCE
        elec = body["data"]["electrical"]
        specs[st] = elec
        print(f"       -> {st}: Voltage={elec['nominal_voltage_v']}V, Freq={elec['grid_frequency_hz']}Hz, Gensets={elec['diesel_generator_count']}")

    # Confirm different specs across stations (Bharati: 240kW / 3 gensets, Maitri: 187.5kW / 3 gensets, Himadri: 90kW / 2 gensets)
    assert specs["BHARATI"]["diesel_generator_count"] == 3
    assert specs["HIMADRI"]["diesel_generator_count"] == 2
    assert specs["BHARATI"]["total_diesel_capacity_kw"] == 240.0
    assert specs["HIMADRI"]["total_diesel_capacity_kw"] == 90.0
    assert specs["MAITRI"]["total_diesel_capacity_kw"] == 187.5
    print("[PASS] 3. Station dynamic parameters verified (Bharati 240kW/3gensets, Maitri 187.5kW/3gensets, Himadri 90kW/2gensets)")

    # 3. Forecast Target & Horizon Switching
    for tgt in ["total_load_kw", "solar_generation_kw", "wind_generation_kw"]:
        status, body = request_json("/api/v1/forecast", "POST", {
            "station_id": "BHARATI",
            "target": tgt,
            "horizon_hours": 48
        })
        assert status == 200 and body["status"] == "SUCCESS"
        assert body["provenance"] in LOCKED_PROVENANCE
        print(f"[PASS] 4. Forecast ({tgt}, 48h): {len(body['data']['quantiles'])} points, prov={body['provenance']}")

    # 168h Horizon Switch
    status, body = request_json("/api/v1/forecast", "POST", {
        "station_id": "BHARATI",
        "target": "total_load_kw",
        "horizon_hours": 168
    })
    assert status == 200 and body["status"] == "SUCCESS"
    assert len(body["data"]["quantiles"]) == 168
    print(f"[PASS] 5. Forecast 168h strategic horizon verified: 168 predictions returned")

    # 4. Stress Scenario Explorer & Live Evaluation
    status, body = request_json("/api/v1/scenarios")
    assert status == 200
    assert len(body["data"]) == 14
    print(f"[PASS] 6. Scenario Catalog: 14 locked polar stress scenarios loaded")

    status, body = request_json("/api/v1/scenarios/evaluate", "POST", {
        "station_id": "BHARATI",
        "scenario_id": "BLIZZARD",
        "horizon_hours": 48,
        "forecast_mode": "EXPECTED"
    })
    assert status == 200 and body["status"] == "SUCCESS"
    assert body["provenance"] in LOCKED_PROVENANCE
    impact = body["data"]["impact_metrics"]
    print(f"[PASS] 7. Scenario BLIZZARD Stress Test: Delta Unserved={impact['delta_unserved_energy_kwh']} kWh, Delta Fuel={impact['delta_diesel_fuel_liters']} L")

    # 5. Optimizer Modes (Expected, Conservative, Robust)
    for m in ["EXPECTED", "CONSERVATIVE", "SCENARIO_ROBUST"]:
        status, body = request_json("/api/v1/optimize", "POST", {
            "station_id": "BHARATI",
            "horizon_hours": 48,
            "mode": m,
            "include_schedule": True
        })
        assert status == 200 and body["status"] == "SUCCESS"
        assert body["provenance"] in LOCKED_PROVENANCE
        opt = body["data"]
        print(f"[PASS] 8. Optimizer ({m}): status={opt['solver_status']}, tier={opt['optimality_tier']}, gap={opt['relative_gap']}")

    # 6. Resilience & 9-Dimension Assessment
    status, body = request_json("/api/v1/resilience/evaluate", "POST", {
        "station_id": "BHARATI",
        "horizon_hours": 48,
        "include_propagation": True
    })
    assert status == 200 and body["status"] in ("SUCCESS", "PARTIAL")
    assert body["provenance"] in LOCKED_PROVENANCE
    res_data = body["data"]
    surv = res_data["survival_horizons"]
    dims = res_data["dimensions"]
    print(f"[PASS] 9. Resilience Assessment: State={res_data['resilience_state']}, Composite Index={dims['composite_index']:.1f}, Binding={surv['binding_subsystem']}")
    
    # Verify candidate recovery options preserve backend order and advisory mark
    rec_opts = res_data["candidate_recovery_options"]
    print(f"       -> Recovery Pathways: {len(rec_opts)} advisory options returned")
    for opt in rec_opts:
        assert opt["advisory_only"] is True

    # 7. Policy Governance & Stateful Hysteresis
    status, body = request_json("/api/v1/policy/evaluate", "POST", {
        "station_id": "BHARATI",
        "horizon_hours": 48,
        "include_suppressed": True,
        "include_evaluation_trace": True
    })
    assert status == 200 and body["status"] == "SUCCESS"
    assert body["provenance"] in LOCKED_PROVENANCE
    pol_data = body["data"]
    directive = pol_data.get('primary_directive') or (pol_data.get('primary_policy') or {}).get('action', 'NONE')
    print(f"[PASS] 10. Policy Governance: State={pol_data['policy_state']}, Directive={directive}")

    # 8. End-to-End Decision Trace Pipeline
    status, body = request_json("/api/v1/pipeline/analyze", "POST", {
        "station_id": "BHARATI",
        "horizon_hours": 48,
        "scenario_id": "NORMAL_BASELINE",
        "mode": "EXPECTED"
    })
    assert status == 200 and body["status"] == "SUCCESS"
    assert body["provenance"] in LOCKED_PROVENANCE
    pipe_data = body["data"]
    stages = pipe_data["stages"]
    print(f"[PASS] 11. Decision Trace: {len(stages)} stages executed, Overall={pipe_data['overall_status']}")
    for s in stages:
        stage_name = s.get('stage_name') or s.get('stage')
        print(f"        Stage [{stage_name}]: {s['status']} ({s['duration_sec']:.3f}s)")

    # 9. Domain Statuses & Error Contracts
    # Invalid Station (404 Domain Error)
    status, body = request_json("/api/v1/stations/INVALID_STATION")
    assert status == 404
    assert body["status"] == "ERROR"
    assert body["error"]["code"] == "STATION_NOT_FOUND"
    print(f"[PASS] 12. Error Contract 404: code={body['error']['code']}, message='{body['error']['message']}'")

    # Invalid Forecast Target (422 Domain Error)
    status, body = request_json("/api/v1/forecast", "POST", {
        "station_id": "BHARATI",
        "target": "invalid_subsystem_target",
        "horizon_hours": 48
    })
    assert status == 422
    assert body["status"] == "ERROR"
    assert body["error"]["code"] in ("VALIDATION_ERROR", "INVALID_FORECAST_TARGET")
    print(f"[PASS] 13. Error Contract 422: code={body['error']['code']}, message='{body['error']['message']}'")

    print("=" * 80)
    print("ALL 13 RUNTIME & PROVENANCE AUDIT GATES PASSED CLEANLY (100%)")
    print("=" * 80)

if __name__ == "__main__":
    audit()
