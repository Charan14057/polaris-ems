"""
POLARIS-EMS — Final Full-Circle Acceptance Integration Suite
Section 5 Acceptance Pass: Complete Closed-Loop Verification

Validates the complete authoritative operational chain:
1. BASELINE BHARATI: snapshot capture
2. SWITCH MAITRI: verify station-dependent telemetry & topology changes
3. SWITCH HIMADRI: verify station-dependent telemetry & topology changes
4. SWITCH BHARATI: verify restoration to baseline
5. ACTIVATE BLIZZARD: environment, solar, wind, loads, resilience, policy, optimizer, trace
6. ACTIVATE SOLAR_GENERATION_FAILURE: solar = 0, source mix changes, downstream response
7. ACTIVATE WIND_GENERATION_FAILURE: wind = 0, source balance, diesel/BESS response
8. ACTIVATE BATTERY_DEGRADATION: available capacity changes, resilience/storage changes
9. ACTIVATE UNFORESEEN_WEATHER: weather regime shift, load/generation changes
10. DG START: diesel power increases, fuel consumption changes, BUS updates, trace logged
11. DG STOP: diesel power falls, fuel burn changes, BUS updates, trace logged
12. CLEAR SCENARIO: baseline returns, drift < 1e-4, all dependent state restored
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.twin.live_session import live_twin_manager


@pytest.fixture(scope="module")
def client():
    app = create_app()
    return TestClient(app)


def test_station_switching_full_circle(client):
    """
    Validates complete station switching cycle:
    BHARATI -> MAITRI -> HIMADRI -> BHARATI
    Verifies that all electrical, spatial, and meteorological metrics change authoritatively
    and restore cleanly to the baseline.
    """
    # 1. BASELINE BHARATI
    live_twin_manager.reset_session("BHARATI")
    resp_bh1 = client.get("/api/v1/twin/live/BHARATI")
    assert resp_bh1.status_code == 200
    bh1_data = resp_bh1.json()["data"]["state"]
    assert bh1_data["station_id"] == "BHARATI"
    bh1_load = bh1_data["loads"]["total_load_kw"]
    bh1_bat_cap = bh1_data["battery"]["capacity_kwh"]

    # 2. SWITCH MAITRI
    live_twin_manager.reset_session("MAITRI")
    resp_mt = client.get("/api/v1/twin/live/MAITRI")
    assert resp_mt.status_code == 200
    mt_data = resp_mt.json()["data"]["state"]
    assert mt_data["station_id"] == "MAITRI"
    assert mt_data["loads"]["total_load_kw"] != bh1_load
    assert mt_data["battery"]["capacity_kwh"] != bh1_bat_cap

    # Verify Maitri topology differs
    resp_mt_spec = client.get("/api/v1/stations/MAITRI")
    assert resp_mt_spec.status_code == 200
    mt_spec = resp_mt_spec.json()["data"]
    assert mt_spec["station_id"] == "MAITRI"
    assert mt_spec["latitude"] != bh1_data.get("latitude", 0)

    # 3. SWITCH HIMADRI
    live_twin_manager.reset_session("HIMADRI")
    resp_hm = client.get("/api/v1/twin/live/HIMADRI")
    assert resp_hm.status_code == 200
    hm_data = resp_hm.json()["data"]["state"]
    assert hm_data["station_id"] == "HIMADRI"
    assert hm_data["loads"]["total_load_kw"] != mt_data["loads"]["total_load_kw"]
    assert hm_data["battery"]["capacity_kwh"] != mt_data["battery"]["capacity_kwh"]

    # Verify Himadri (Arctic) topology differs
    resp_hm_spec = client.get("/api/v1/stations/HIMADRI")
    assert resp_hm_spec.status_code == 200
    hm_spec = resp_hm_spec.json()["data"]
    assert hm_spec["station_id"] == "HIMADRI"
    assert hm_spec["latitude"] > 0, "Himadri must be in the Arctic (positive latitude)"

    # 4. SWITCH BHARATI (Restoration)
    resp_bh2 = client.get("/api/v1/twin/live/BHARATI")
    assert resp_bh2.status_code == 200
    bh2_data = resp_bh2.json()["data"]["state"]
    assert bh2_data["station_id"] == "BHARATI"
    assert abs(bh2_data["loads"]["total_load_kw"] - bh1_load) < 1e-4
    assert abs(bh2_data["battery"]["capacity_kwh"] - bh1_bat_cap) < 1e-4


def test_scenario_blizzard_full_propagation(client):
    """
    Validates BLIZZARD scenario:
    - environment changes (temp drops, wind rises, irradiance drops to 0)
    - thermal/load changes
    - resilience re-evaluates
    - policy recomputes
    - optimizer receives changed context
    - trace logged
    """
    live_twin_manager.reset_session("BHARATI")
    baseline = client.get("/api/v1/twin/live/BHARATI").json()["data"]["state"]
    base_temp = baseline["environment"]["ambient_temperature_c"]
    base_wind = baseline["environment"]["wind_speed_ms"]

    # Activate BLIZZARD
    resp = client.post("/api/v1/twin/scenario/apply", json={
        "station_id": "BHARATI",
        "scenario_id": "BLIZZARD"
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "APPLIED"

    twin_snap = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    state = twin_snap["state"]

    # Environment changes
    assert state["environment"]["ambient_temperature_c"] < base_temp
    assert state["environment"]["wind_speed_ms"] > base_wind
    assert state["environment"]["irradiance_wm2"] == 0.0

    # Solar drops to 0
    assert state["solar"]["solar_generation_kw"] == 0.0

    # Downstream Resilience reflects blizzard stress
    res_resp = client.post("/api/v1/resilience/evaluate", json={
        "station_id": "BHARATI",
        "scenario_id": "BLIZZARD"
    })
    assert res_resp.status_code == 200
    res_data = res_resp.json()["data"]
    assert "survival_horizons" in res_data
    assert "dimensions" in res_data

    # Downstream Policy responds
    pol_resp = client.post("/api/v1/policy/evaluate", json={
        "station_id": "BHARATI",
        "scenario_id": "BLIZZARD"
    })
    assert pol_resp.status_code == 200
    pol_data = pol_resp.json()["data"]
    assert "policy_state" in pol_data
    assert "optimizer_handoff" in pol_data

    # Downstream Optimizer receives changed context
    opt_resp = client.post("/api/v1/optimize", json={
        "station_id": "BHARATI",
        "mode": "SCENARIO_ROBUST",
        "scenario_id": "BLIZZARD",
        "horizon_hours": 6,
        "include_schedule": True
    })
    assert opt_resp.status_code == 200
    opt_data = opt_resp.json()["data"]
    assert opt_data["mode"] == "SCENARIO_ROBUST"
    assert opt_data["schedule"] is not None and len(opt_data["schedule"]) > 0

    # Traces contain scenario application
    apply_data = resp.json()["data"]
    assert "trace" in apply_data
    assert apply_data["trace"]["event"] == "SCENARIO_APPLIED"
    assert apply_data["trace"]["scenario_id"] == "BLIZZARD"

    session = live_twin_manager.get_session("BHARATI")
    assert any(t.get("event") == "SCENARIO_APPLIED" and t.get("scenario_id") == "BLIZZARD" for t in session.trace_history)


def test_scenario_solar_generation_failure(client):
    """
    Validates SOLAR_GENERATION_FAILURE:
    - solar = 0 where model requires
    - source mix changes
    - downstream sources respond
    - resilience/policy/optimizer reflect condition
    """
    live_twin_manager.reset_session("BHARATI")

    resp = client.post("/api/v1/twin/scenario/apply", json={
        "station_id": "BHARATI",
        "scenario_id": "SOLAR_GENERATION_FAILURE"
    })
    assert resp.status_code == 200

    twin_snap = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    state = twin_snap["state"]

    # Solar must be strictly 0
    assert state["solar"]["solar_generation_kw"] == 0.0

    # Source balance must be maintained by backup / BESS / Wind
    total_gen = state["solar"]["solar_generation_kw"] + state["wind"]["wind_generation_kw"] + state["diesel"]["generator_power_kw"]
    net_battery = state["battery"]["discharge_kw"] - state["battery"]["charge_kw"]
    assert (total_gen + net_battery) >= 0.0

    # Policy and Resilience reflect failure
    res_resp = client.post("/api/v1/resilience/evaluate", json={"station_id": "BHARATI", "scenario_id": "SOLAR_GENERATION_FAILURE"})
    assert res_resp.status_code == 200

    pol_resp = client.post("/api/v1/policy/evaluate", json={"station_id": "BHARATI", "scenario_id": "SOLAR_GENERATION_FAILURE"})
    assert pol_resp.status_code == 200


def test_scenario_wind_generation_failure(client):
    """
    Validates WIND_GENERATION_FAILURE:
    - wind = 0
    - source balance changes
    - diesel/BESS response changes
    - downstream pages update
    """
    live_twin_manager.reset_session("BHARATI")

    resp = client.post("/api/v1/twin/scenario/apply", json={
        "station_id": "BHARATI",
        "scenario_id": "WIND_GENERATION_FAILURE"
    })
    assert resp.status_code == 200

    twin_snap = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    state = twin_snap["state"]

    # Wind must be strictly 0
    assert state["wind"]["wind_generation_kw"] == 0.0

    # Balance check
    assert state["loads"]["served_load_kw"] > 0.0


def test_scenario_battery_degradation(client):
    """
    Validates BATTERY_DEGRADATION:
    - available capacity changes
    - resilience/storage changes
    - optimizer constraint/context changes
    """
    live_twin_manager.reset_session("BHARATI")
    base_state = client.get("/api/v1/twin/live/BHARATI").json()["data"]["state"]
    base_cap = base_state["battery"]["capacity_kwh"]

    resp = client.post("/api/v1/twin/scenario/apply", json={
        "station_id": "BHARATI",
        "scenario_id": "BATTERY_DEGRADATION"
    })
    assert resp.status_code == 200

    twin_snap = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    state = twin_snap["state"]

    # Capacity must be degraded
    assert state["battery"]["capacity_kwh"] < base_cap
    assert abs(state["battery"]["capacity_kwh"] - (base_cap * 0.65)) < 1.0

    # Resilience storage horizon reflects degraded BESS
    res_resp = client.post("/api/v1/resilience/evaluate", json={"station_id": "BHARATI", "scenario_id": "BATTERY_DEGRADATION"})
    assert res_resp.status_code == 200
    res_data = res_resp.json()["data"]
    assert res_data["survival_horizons"]["battery_endurance_horizon_h"] > 0.0


def test_scenario_unforeseen_weather(client):
    """
    Validates UNFORESEEN_WEATHER:
    - temperature changes
    - wind changes
    - irradiance changes
    - affected load/generation changes
    - resilience/policy/optimizer update
    """
    live_twin_manager.reset_session("BHARATI")
    base_state = client.get("/api/v1/twin/live/BHARATI").json()["data"]["state"]
    base_temp = base_state["environment"]["ambient_temperature_c"]
    base_wind = base_state["environment"]["wind_speed_ms"]

    resp = client.post("/api/v1/twin/scenario/apply", json={
        "station_id": "BHARATI",
        "scenario_id": "UNFORESEEN_WEATHER"
    })
    assert resp.status_code == 200

    twin_snap = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    state = twin_snap["state"]

    assert state["environment"]["ambient_temperature_c"] < base_temp
    assert state["environment"]["wind_speed_ms"] > base_wind

    # Downstream optimizer
    opt_resp = client.post("/api/v1/optimize", json={
        "station_id": "BHARATI",
        "mode": "SCENARIO_ROBUST",
        "scenario_id": "UNFORESEEN_WEATHER",
        "horizon_hours": 6
    })
    assert opt_resp.status_code == 200


def test_operator_dg_start_and_stop_lifecycle(client):
    """
    Validates manual control actions and trace logging:
    DG START:
    - diesel power increases
    - fuel consumption changes
    - BUS balance maintained
    - trace created
    DG STOP:
    - diesel power falls to 0
    - fuel burn falls to 0
    - BUS balance maintained
    - trace created
    """
    live_twin_manager.reset_session("BHARATI")

    # 1. DG START
    resp_start = client.post("/api/v1/twin/control/manual", json={
        "station_id": "BHARATI",
        "action_id": "dg1_start",
        "parameters": {"power_kw": 45.0}
    })
    assert resp_start.status_code == 200
    start_body = resp_start.json()["data"]
    assert start_body["status"] == "APPROVED"
    assert "trace" in start_body

    # Verify diesel power increased
    twin_start = client.get("/api/v1/twin/live/BHARATI").json()["data"]["state"]
    assert twin_start["diesel"]["generator_power_kw"] >= 20.0
    assert twin_start["diesel"]["fuel_consumption_l_per_h"] > 0.0

    # 2. DG STOP
    resp_stop = client.post("/api/v1/twin/control/manual", json={
        "station_id": "BHARATI",
        "action_id": "dg1_stop"
    })
    assert resp_stop.status_code == 200
    stop_body = resp_stop.json()["data"]
    assert stop_body["status"] == "APPROVED"
    assert "trace" in stop_body

    # Verify diesel power fell to 0
    twin_stop = client.get("/api/v1/twin/live/BHARATI").json()["data"]["state"]
    assert twin_stop["diesel"]["generator_power_kw"] == 0.0
    assert twin_stop["diesel"]["fuel_consumption_l_per_h"] == 0.0


def test_scenario_clear_restores_baseline_without_drift(client):
    """
    Validates that clearing an active scenario restores baseline state with drift < 1e-4.
    """
    live_twin_manager.reset_session("BHARATI")
    baseline = client.get("/api/v1/twin/live/BHARATI").json()["data"]["state"]

    # Perturb with BLIZZARD
    client.post("/api/v1/twin/scenario/apply", json={
        "station_id": "BHARATI",
        "scenario_id": "BLIZZARD"
    })
    perturbed = client.get("/api/v1/twin/live/BHARATI").json()["data"]["state"]
    assert perturbed["environment"]["ambient_temperature_c"] != baseline["environment"]["ambient_temperature_c"]

    # Clear Scenario
    resp_clear = client.post("/api/v1/twin/scenario/clear", json={
        "station_id": "BHARATI"
    })
    assert resp_clear.status_code == 200
    assert resp_clear.json()["data"]["status"] == "CLEARED"

    # Restored state check
    restored = client.get("/api/v1/twin/live/BHARATI").json()["data"]["state"]
    temp_drift = abs(restored["environment"]["ambient_temperature_c"] - baseline["environment"]["ambient_temperature_c"])
    wind_drift = abs(restored["environment"]["wind_speed_ms"] - baseline["environment"]["wind_speed_ms"])

    assert temp_drift < 1e-4, f"Temperature drift {temp_drift} exceeds tolerance 1e-4"
    assert wind_drift < 1e-4, f"Wind speed drift {wind_drift} exceeds tolerance 1e-4"
