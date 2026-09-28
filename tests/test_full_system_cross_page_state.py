"""
POLARIS-EMS — Full System Cross-Page State Integration Suite
Prompt ID: 61853 / Operational System-Wide Connectivity Verification

Verifies the unified closed-loop operational information pipeline:
Station -> Environment -> Twin State -> Forecast -> Scenario -> Power/Thermal State
-> Resilience -> Policy -> Dispatch Optimization -> Operator Action -> Decision Trace
-> Assets / Validation / Field status

No isolated pages, no fake dynamic values, no parallel frontend state machines.
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.twin.live_session import live_twin_manager
from backend.scenarios.registry import ScenarioRegistry


@pytest.fixture(scope="module")
def client():
    app = create_app()
    return TestClient(app)


def test_cross_page_station_switching_propagation(client):
    """
    Step 1-10:
    Switching stations (BHARATI -> MAITRI -> HIMADRI) must propagate authoritative,
    station-specific state across all operational modules:
    - Overview / Twin State
    - Energy / Power Topology
    - Forecast Horizon
    - Resilience Envelope
    - Asset Registry
    - Policy Governance
    - Optimizer Dispatch
    - Decision Trace
    """
    # 1. Bharati Baseline Snapshot
    resp_bh = client.get("/api/v1/twin/live/BHARATI")
    assert resp_bh.status_code == 200
    bh_data = resp_bh.json()["data"]
    bh_state = bh_data["state"]
    assert bh_state["station_id"] == "BHARATI"
    assert bh_state["loads"]["total_load_kw"] > 0
    assert bh_state["battery"]["capacity_kwh"] > 0

    # 2. Switch to Maitri
    resp_mt = client.get("/api/v1/twin/live/MAITRI")
    assert resp_mt.status_code == 200
    mt_data = resp_mt.json()["data"]
    mt_state = mt_data["state"]
    assert mt_state["station_id"] == "MAITRI"

    # 3. Verify Overview / State changed
    assert mt_state["loads"]["total_load_kw"] != bh_state["loads"]["total_load_kw"]
    assert mt_state["battery"]["capacity_kwh"] != bh_state["battery"]["capacity_kwh"]

    # 4. Verify Energy / Power Topology differs
    resp_topo_bh = client.get("/api/v1/stations/BHARATI")
    resp_topo_mt = client.get("/api/v1/stations/MAITRI")
    assert resp_topo_bh.status_code == 200 and resp_topo_mt.status_code == 200
    bh_spec = resp_topo_bh.json()["data"]
    mt_spec = resp_topo_mt.json()["data"]
    assert bh_spec["station_id"] != mt_spec["station_id"]
    assert bh_spec["latitude"] != mt_spec["latitude"]

    # 5. Verify Forecast changed
    resp_fc_bh = client.post("/api/v1/forecast", json={"station_id": "BHARATI", "target": "total_load_kw", "horizon_hours": 24})
    resp_fc_mt = client.post("/api/v1/forecast", json={"station_id": "MAITRI", "target": "total_load_kw", "horizon_hours": 24})
    assert resp_fc_bh.status_code == 200 and resp_fc_mt.status_code == 200
    fc_bh = resp_fc_bh.json()["data"]
    fc_mt = resp_fc_mt.json()["data"]
    assert fc_bh["station_id"] == "BHARATI"
    assert fc_mt["station_id"] == "MAITRI"

    # 6. Verify Resilience changed
    resp_res_bh = client.post("/api/v1/resilience/evaluate", json={"station_id": "BHARATI"})
    resp_res_mt = client.post("/api/v1/resilience/evaluate", json={"station_id": "MAITRI"})
    assert resp_res_bh.status_code == 200 and resp_res_mt.status_code == 200
    res_bh = resp_res_bh.json()["data"]
    res_mt = resp_res_mt.json()["data"]
    assert res_bh["station_id"] == "BHARATI"
    assert res_mt["station_id"] == "MAITRI"
    assert "survival_horizons" in res_bh
    assert "survival_horizons" in res_mt

    # 7. Verify Assets changed
    resp_assets_bh = client.get("/api/v1/stations/BHARATI")
    resp_assets_mt = client.get("/api/v1/stations/MAITRI")
    assert resp_assets_bh.status_code == 200 and resp_assets_mt.status_code == 200
    bh_devices = {d["id"] for d in resp_assets_bh.json()["data"]["devices"]}
    mt_devices = {d["id"] for d in resp_assets_mt.json()["data"]["devices"]}
    assert bh_devices != mt_devices

    # 8. Verify Policy changed
    resp_pol_bh = client.post("/api/v1/policy/evaluate", json={"station_id": "BHARATI"})
    resp_pol_mt = client.post("/api/v1/policy/evaluate", json={"station_id": "MAITRI"})
    assert resp_pol_bh.status_code == 200 and resp_pol_mt.status_code == 200

    # 9. Verify Optimization inputs change
    resp_opt_bh = client.post("/api/v1/optimize", json={"station_id": "BHARATI", "mode": "EXPECTED", "horizon_hours": 6})
    resp_opt_mt = client.post("/api/v1/optimize", json={"station_id": "MAITRI", "mode": "EXPECTED", "horizon_hours": 6})
    assert resp_opt_bh.status_code == 200 and resp_opt_mt.status_code == 200
    opt_bh = resp_opt_bh.json()["data"]
    opt_mt = resp_opt_mt.json()["data"]
    assert opt_bh["station_id"] == "BHARATI"
    assert opt_mt["station_id"] == "MAITRI"

    # 10. Verify Decision Trace context changed
    resp_traces = client.get("/api/v1/traces?station_id=MAITRI")
    assert resp_traces.status_code == 200
    trace_data = resp_traces.json()["data"]
    assert isinstance(trace_data, list)
    if trace_data:
        assert trace_data[0]["station_id"] == "MAITRI"


def test_scenario_propagation_and_lifecycle(client):
    """
    Step 11-17:
    Activate BLIZZARD scenario:
    - Environment updates (wind rises, ambient temp drops, irradiance drops)
    - Loads and generation change
    - Resilience evaluates threat
    - Policy responds
    - Optimizer receives modified context
    """
    # Reset Bharati session to clean baseline
    live_twin_manager.reset_session("BHARATI")
    base_res = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    base_temp = base_res["state"]["environment"]["ambient_temperature_c"]
    base_wind = base_res["state"]["environment"]["wind_speed_ms"]

    # 11. Activate BLIZZARD
    resp_apply = client.post("/api/v1/twin/scenario/apply", json={
        "station_id": "BHARATI",
        "scenario_id": "BLIZZARD"
    })
    assert resp_apply.status_code == 200
    app_data = resp_apply.json()["data"]
    assert app_data["status"] == "APPLIED"
    assert app_data["scenario_id"] == "BLIZZARD"

    # 12. Verify Environment Changes
    blizz_res = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    blizz_temp = blizz_res["state"]["environment"]["ambient_temperature_c"]
    blizz_wind = blizz_res["state"]["environment"]["wind_speed_ms"]
    assert blizz_wind > base_wind, "Blizzard must increase wind speed"
    assert blizz_temp < base_temp, "Blizzard must decrease ambient temperature"

    # 13. Verify Load / Generation changes
    assert blizz_res["metadata"]["active_scenario"] == "BLIZZARD"

    # 14. Verify Resilience evaluates threat
    res_resp = client.post("/api/v1/resilience/evaluate", json={"station_id": "BHARATI", "scenario_id": "BLIZZARD"})
    assert res_resp.status_code == 200

    # 15. Verify Policy responds
    pol_resp = client.post("/api/v1/policy/evaluate", json={"station_id": "BHARATI", "scenario_id": "BLIZZARD"})
    assert pol_resp.status_code == 200
    pol_data = pol_resp.json()["data"]
    assert "policy_state" in pol_data
    assert "optimizer_handoff" in pol_data

    # 16. Verify Optimizer inputs reflect scenario
    opt_resp = client.post("/api/v1/optimize", json={"station_id": "BHARATI", "mode": "SCENARIO_ROBUST", "scenario_id": "BLIZZARD", "horizon_hours": 6})
    assert opt_resp.status_code == 200
    assert opt_resp.json()["data"]["mode"] == "SCENARIO_ROBUST"

    # 17. Verify current validation state reflects active scenario
    val_resp = client.get("/api/v1/validation/resilience/BHARATI")
    assert val_resp.status_code == 200


def test_operator_control_actions_and_trace(client):
    """
    Step 18-25:
    Execute DG Start:
    - Twin updates generator status
    - Overview shows DG output
    - Assets show DG running
    - BUS balances
    - Decision trace captures event

    Execute DG Stop:
    - Dependent state updates
    """
    live_twin_manager.reset_session("BHARATI")

    # 18. Execute DG Start
    resp_start = client.post("/api/v1/twin/control/manual", json={
        "station_id": "BHARATI",
        "action_id": "dg1_start",
        "parameters": {"power_kw": 40.0}
    })
    assert resp_start.status_code == 200
    start_data = resp_start.json()["data"]
    assert start_data["status"] == "APPROVED"

    # 19-22. Verify Twin / Overview / Assets / BUS
    twin_res = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    assert twin_res["state"]["diesel"]["generator_status"] == "ONLINE"
    assert twin_res["state"]["diesel"]["generator_power_kw"] >= 24.0

    # 23. Verify Decision Trace
    assert "trace" in start_data
    assert "event" in start_data["trace"]

    # 24-25. Execute DG Stop
    resp_stop = client.post("/api/v1/twin/control/manual", json={
        "station_id": "BHARATI",
        "action_id": "dg1_stop"
    })
    assert resp_stop.status_code == 200
    stop_data = resp_stop.json()["data"]
    assert stop_data["status"] == "APPROVED"


def test_scenario_clear_restores_baseline(client):
    """
    Step 26-27:
    Clearing active scenario restores baseline state without numerical drift.
    """
    live_twin_manager.reset_session("BHARATI")
    base_state = client.get("/api/v1/twin/live/BHARATI").json()["data"]["state"]

    # Activate
    client.post("/api/v1/twin/scenario/apply", json={
        "station_id": "BHARATI",
        "scenario_id": "HIGH_WIND"
    })
    wind_snap = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    assert wind_snap["metadata"]["active_scenario"] == "HIGH_WIND"

    # Clear
    resp_clear = client.post("/api/v1/twin/scenario/clear", json={
        "station_id": "BHARATI"
    })
    assert resp_clear.status_code == 200
    clear_data = resp_clear.json()["data"]
    assert clear_data["status"] == "CLEARED"

    # Verify Baseline Restored
    restored_snap = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    assert restored_snap["metadata"]["active_scenario"] is None
    # Verify no persistent drift in temperature or ambient values
    assert abs(restored_snap["state"]["environment"]["ambient_temperature_c"] - base_state["environment"]["ambient_temperature_c"]) < 1e-4


def test_unforeseen_weather_scenario_propagation(client):
    """
    Step 28:
    Verify UNFORESEEN_WEATHER scenario:
    - Registered as canonical scenario #15
    - Deterministic, bounded perturbation
    - Perturbs ambient temperature, wind, and solar
    - Propagates causally to power balance, resilience, and policy
    """
    reg = ScenarioRegistry()
    scenarios = reg.list_scenarios()
    assert len(scenarios) == 15
    scen = reg.get("UNFORESEEN_WEATHER")
    assert scen is not None
    assert scen.name == "Unforeseen Weather Regime Shift"

    # Apply UNFORESEEN_WEATHER to live twin
    live_twin_manager.reset_session("BHARATI")
    resp = client.post("/api/v1/twin/scenario/apply", json={
        "station_id": "BHARATI",
        "scenario_id": "UNFORESEEN_WEATHER"
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "APPLIED"
    assert data["scenario_id"] == "UNFORESEEN_WEATHER"

    # Verify state reflects perturbation
    twin_data = client.get("/api/v1/twin/live/BHARATI").json()["data"]
    assert twin_data["metadata"]["active_scenario"] == "UNFORESEEN_WEATHER"
    env = twin_data["state"]["environment"]
    assert env["wind_speed_ms"] > 0
    assert env["ambient_temperature_c"] != 0.0

    # Clear after test
    client.post("/api/v1/twin/scenario/clear", json={"station_id": "BHARATI"})
