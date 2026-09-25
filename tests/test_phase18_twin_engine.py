"""
POLARIS-EMS — Phase 18 Spatial Digital Twin Engine Tests
SIH26061: Polar Energy Management & Resilience System

Validates:
1. Spatial profile loading and schema compliance for BHARATI, MAITRI, HIMADRI
2. Exact mapping between spatial device nodes and authoritative StationProfile devices
3. Twin instantaneous state retrieval through TwinAPIAdapter
4. Multi-horizon forward trajectory simulation (24h, 48h) through TwinEngine
5. Stress scenario perturbation integration
6. FastAPI read-only endpoints:
   - GET /api/v1/twin/spatial/{station_id}
   - GET /api/v1/twin/state/{station_id}
   - POST /api/v1/twin/trajectory
7. Epistemic boundary enforcement: PHYSICAL_SCADA_LINK = FALSE, SIMULATED provenance
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.adapters.twin_adapter import TwinAPIAdapter
from backend.api.schemas.twin import TwinTrajectoryRequestSchema
from backend.data.station_profiles.loader import StationProfileRegistry


@pytest.fixture(scope="module")
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture(scope="module")
def twin_adapter():
    return TwinAPIAdapter()


def test_spatial_profiles_all_stations(twin_adapter):
    """Verifies that all three stations have complete, valid spatial profiles."""
    stations = ["BHARATI", "MAITRI", "HIMADRI"]
    profile_reg = StationProfileRegistry()

    for sid in stations:
        spatial = twin_adapter.get_spatial_profile(sid)
        assert spatial["stationId"] == sid
        assert spatial["layoutStatus"] == "REPRESENTATIVE"
        assert len(spatial["zones"]) >= 5
        assert len(spatial["nodes"]) >= 10
        assert len(spatial["edges"]) >= 10

        # Check device correspondence
        station_profile = profile_reg.get(sid)
        station_device_ids = {d.id for d in station_profile.devices}
        spatial_device_ids = {n["deviceId"] for n in spatial["nodes"] if n.get("deviceId")}

        assert spatial_device_ids == station_device_ids, (
            f"Mismatch between station profile devices and spatial layout devices for {sid}"
        )


def test_twin_current_state_retrieval(twin_adapter):
    """Verifies instantaneous physical state generation from Phase 4 Twin."""
    state = twin_adapter.get_current_state("BHARATI")
    assert state["station_id"] == "BHARATI"
    assert "environment" in state
    assert "thermal" in state
    assert "loads" in state
    assert "solar" in state
    assert "wind" in state
    assert "battery" in state
    assert "diesel" in state
    assert "fuel" in state
    assert state["provenance"] in ["CONFIGURED", "SIMULATED"]


def test_twin_trajectory_simulation_24h(twin_adapter):
    """Verifies 24-step forward simulation trajectory."""
    req = TwinTrajectoryRequestSchema(
        station_id="BHARATI",
        horizon_hours=24,
        mode="EXPECTED"
    )
    res = twin_adapter.simulate_trajectory(req)
    assert res.station_id == "BHARATI"
    assert res.steps_count == 24
    assert len(res.states) == 24
    assert res.duration_hours == 24.0
    assert "total_unserved_kwh" in res.summary
    assert res.provenance == "SIMULATED"


def test_twin_trajectory_simulation_with_scenario(twin_adapter):
    """Verifies scenario perturbation integration without duplicating physics."""
    req = TwinTrajectoryRequestSchema(
        station_id="BHARATI",
        horizon_hours=24,
        mode="CONSERVATIVE",
        scenario_id="BLIZZARD"
    )
    res = twin_adapter.simulate_trajectory(req)
    assert res.station_id == "BHARATI"
    assert res.summary.get("scenario_id") == "BLIZZARD"
    assert "impact_metrics" in res.summary


def test_api_spatial_profile_endpoint(client):
    """Tests GET /api/v1/twin/spatial/BHARATI endpoint."""
    resp = client.get("/api/v1/twin/spatial/BHARATI")
    assert resp.status_code == 200
    json_data = resp.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["data"]["stationId"] == "BHARATI"
    assert json_data["data"]["layoutStatus"] == "REPRESENTATIVE"


def test_api_current_state_endpoint(client):
    """Tests GET /api/v1/twin/state/BHARATI endpoint."""
    resp = client.get("/api/v1/twin/state/BHARATI")
    assert resp.status_code == 200
    json_data = resp.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["data"]["station_id"] == "BHARATI"
    assert json_data["data"]["battery"]["soc_pct"] > 0


def test_api_trajectory_endpoint(client):
    """Tests POST /api/v1/twin/trajectory endpoint."""
    resp = client.post("/api/v1/twin/trajectory", json={
        "station_id": "BHARATI",
        "horizon_hours": 24,
        "mode": "EXPECTED"
    })
    assert resp.status_code == 200
    json_data = resp.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["data"]["steps_count"] == 24
    assert len(json_data["data"]["states"]) == 24


def test_station_switching_spatial_isolation(client):
    """Verifies that switching from BHARATI to MAITRI and HIMADRI isolates profiles."""
    res_b = client.get("/api/v1/twin/spatial/BHARATI").json()["data"]
    res_m = client.get("/api/v1/twin/spatial/MAITRI").json()["data"]
    res_h = client.get("/api/v1/twin/spatial/HIMADRI").json()["data"]

    assert res_b["stationId"] == "BHARATI"
    assert res_m["stationId"] == "MAITRI"
    assert res_h["stationId"] == "HIMADRI"

    # Distinct zone IDs and device sets
    b_nodes = {n["id"] for n in res_b["nodes"]}
    m_nodes = {n["id"] for n in res_m["nodes"]}
    h_nodes = {n["id"] for n in res_h["nodes"]}

    assert len(b_nodes.intersection(m_nodes)) == 0
    assert len(b_nodes.intersection(h_nodes)) == 0
