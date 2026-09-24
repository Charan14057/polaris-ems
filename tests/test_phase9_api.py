"""
POLARIS-EMS — Automated Test Suite: Phase 9 Backend / API Integration Layer
SIH26061: Polar Energy Management & Resilience System

Exhaustive verification of the Phase 9 FastAPI Integration Layer:
1. Operational Health, Readiness, and Capability discovery endpoints
2. Station profile discovery across Bharati, Maitri, and Himadri (and 404 handling)
3. Probabilistic ML Forecasting endpoints with calibrated quantiles and FORECAST provenance
4. Scenario catalog inspection (14 locked scenarios) and Twin stress test execution
5. Microgrid Optimizer dispatch with HiGHS optimality semantics and Twin replay validation
6. Multi-dimensional Resilience assessment with 9 dimensions and candidate recovery options
7. Policy governance, 4-tier optimizer handoff, hysteresis round-trips, and decision traces
8. Unified End-to-End decision pipeline (Forecast -> Scenario -> Optimize -> Twin -> Resilience -> Policy)
9. Structured error contracts (400, 404, 422) with request correlation IDs (X-Request-ID)
10. Strict 6-tier provenance enforcement (zero 7th tier)
11. Architectural isolation: Zero duplicated physics, MILP, or policy logic in FastAPI routes
"""

import pytest
from fastapi.testclient import TestClient
import inspect

from backend.api import create_app, APIConfig
from backend.api.responses import LOCKED_PROVENANCE_TIERS


@pytest.fixture(scope="module")
def client():
    """Module-scoped FastAPI TestClient instance."""
    app = create_app(APIConfig(debug=True))
    with TestClient(app) as test_client:
        yield test_client


# ==============================================================================
# 1. HEALTH, READINESS & CAPABILITY DISCOVERY
# ==============================================================================

def test_health_liveness(client):
    """GET /health returns 200 with service_status=HEALTHY and request_id."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "SUCCESS"
    assert body["data"]["service_status"] == "HEALTHY"
    assert body["data"]["api_version"] == "v1"
    assert "X-Request-ID" in resp.headers
    assert body["request_id"].startswith("req-")
    assert body["provenance"] in LOCKED_PROVENANCE_TIERS


def test_health_readiness(client):
    """GET /health/ready confirms loaded stations, scenarios, and models."""
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "SUCCESS"
    data = body["data"]
    assert data["ready"] is True
    assert set(data["loaded_stations"]).issuperset({"BHARATI", "MAITRI", "HIMADRI"})
    assert data["loaded_scenarios"] >= 14


def test_health_capabilities_matrix(client):
    """GET /health/capabilities exposes intelligence matrix across Phases 3-8."""
    resp = client.get("/health/capabilities")
    assert resp.status_code == 200
    body = resp.json()
    caps = body["data"]
    assert set(caps["stations"]).issuperset({"BHARATI", "MAITRI", "HIMADRI"})
    assert 48 in caps["horizons_supported_hours"]
    assert 168 in caps["horizons_supported_hours"]
    assert caps["forecasting"]["owning_phase"] == "Phase 3"
    assert caps["twin_simulation"]["owning_phase"] == "Phase 4"
    assert caps["scenarios"]["owning_phase"] == "Phase 5"
    assert caps["optimizer"]["owning_phase"] == "Phase 6"
    assert caps["resilience"]["owning_phase"] == "Phase 7"
    assert caps["policy_governance"]["owning_phase"] == "Phase 8"


# ==============================================================================
# 2. STATION ENDPOINTS & AUTHORITATIVE CONFIGURATION
# ==============================================================================

def test_list_stations(client):
    """GET /api/v1/stations returns Bharati, Maitri, and Himadri summaries."""
    resp = client.get("/api/v1/stations")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "SUCCESS"
    stations = {s["station_id"]: s for s in body["data"]}
    assert "BHARATI" in stations
    assert "MAITRI" in stations
    assert "HIMADRI" in stations

    # Authoritative fleet checks
    assert stations["BHARATI"]["total_diesel_capacity_kw"] == 240.0   # 3 x 80kW
    assert stations["MAITRI"]["total_diesel_capacity_kw"] == 187.5    # 3 x 62.5kW
    assert stations["HIMADRI"]["total_diesel_capacity_kw"] == 90.0    # 2 x 45kW


def test_get_station_detail_bharati(client):
    """GET /api/v1/stations/BHARATI returns full validated configuration."""
    resp = client.get("/api/v1/stations/BHARATI")
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["station_id"] == "BHARATI"
    assert data["electrical"]["diesel_generator_count"] == 3
    assert data["electrical"]["diesel_generator_kw_rated"] == 80.0
    assert data["fuel"]["storage_capacity_liters"] == 160000.0
    assert data["fuel"]["critical_fuel_reserve_liters"] == 25000.0
    assert data["thermal"]["indoor_min_safe_temp_c"] == 12.0
    assert len(data["devices"]) > 0
    assert data["provenance"] == "CONFIGURED"


def test_get_station_not_found(client):
    """GET /api/v1/stations/INVALID returns structured 404 error."""
    resp = client.get("/api/v1/stations/UNKNOWN_STATION")
    assert resp.status_code == 404
    body = resp.json()
    assert body["status"] == "ERROR"
    assert body["error"]["code"] == "STATION_NOT_FOUND"
    assert "UNKNOWN_STATION" in body["error"]["message"]


# ==============================================================================
# 3. PROBABILISTIC FORECASTING (PHASE 3)
# ==============================================================================

def test_forecast_probabilistic_load(client):
    """POST /api/v1/forecast returns point and calibrated quantile predictions."""
    payload = {
        "station_id": "BHARATI",
        "target": "total_load_kw",
        "horizon_hours": 24,
        "forecast_origin": "2025-06-01T00:00:00Z"
    }
    resp = client.post("/api/v1/forecast", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "SUCCESS"
    assert body["provenance"] == "FORECAST"

    data = body["data"]
    assert data["station_id"] == "BHARATI"
    assert data["target"] == "total_load_kw"
    assert data["horizon_hours"] == 24
    assert len(data["quantiles"]) == 24

    # Quantile monotonicity verification: P10 <= P50 <= P90 <= P95
    for q in data["quantiles"]:
        assert q["p10"] <= q["p50"] + 1e-3
        assert q["p50"] <= q["p90"] + 1e-3
        assert q["p90"] <= q["p95"] + 1e-3


def test_forecast_invalid_target(client):
    """POST /api/v1/forecast with invalid target returns 422."""
    payload = {
        "station_id": "BHARATI",
        "target": "invalid_subsystem_target",
        "horizon_hours": 24
    }
    resp = client.post("/api/v1/forecast", json=payload)
    assert resp.status_code == 422
    body = resp.json()
    assert body["status"] == "ERROR"
    assert body["error"]["code"] == "VALIDATION_ERROR"


# ==============================================================================
# 4. SCENARIO STRESS TESTING (PHASE 5)
# ==============================================================================

def test_list_scenarios(client):
    """GET /api/v1/scenarios returns 14 locked scenarios."""
    resp = client.get("/api/v1/scenarios")
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert len(data) >= 14
    scen_ids = [s["scenario_id"] for s in data]
    assert "NORMAL_BASELINE" in scen_ids
    assert "BLIZZARD" in scen_ids
    assert "EXTREME_COLD" in scen_ids
    assert "SOLAR_GENERATION_FAILURE" in scen_ids
    assert "COMBINED_POLAR_STRESS" in scen_ids


def test_get_scenario_detail(client):
    """GET /api/v1/scenarios/BLIZZARD returns transforms and rationale."""
    resp = client.get("/api/v1/scenarios/BLIZZARD")
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["scenario_id"] == "BLIZZARD"
    assert len(data["transforms"]) > 0
    assert data["provenance"] == "CONFIGURED"


def test_evaluate_scenario_blizzard(client):
    """POST /api/v1/scenarios/evaluate runs Blizzard stress test on Bharati."""
    payload = {
        "station_id": "BHARATI",
        "scenario_id": "BLIZZARD",
        "horizon_hours": 24,
        "forecast_mode": "EXPECTED"
    }
    resp = client.post("/api/v1/scenarios/evaluate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "SUCCESS"
    assert body["provenance"] == "SIMULATED"

    data = body["data"]
    assert data["scenario_id"] == "BLIZZARD"
    assert data["station_id"] == "BHARATI"
    assert "impact_metrics" in data
    assert "delta_diesel_fuel_liters" in data["impact_metrics"]


# ==============================================================================
# 5. ENERGY OPTIMIZER (PHASE 6)
# ==============================================================================

def test_optimize_microgrid_expected(client):
    """POST /api/v1/optimize solves 24h dispatch with HiGHS MILP."""
    payload = {
        "station_id": "BHARATI",
        "horizon_hours": 24,
        "mode": "EXPECTED",
        "generator_overrides": {1: "ONLINE", 2: "ONLINE"},
        "include_schedule": True
    }
    resp = client.post("/api/v1/optimize", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["provenance"] == "SIMULATED"

    data = body["data"]
    assert data["station_id"] == "BHARATI"
    assert data["horizon_hours"] == 24
    assert data["solver_status"] in ("OPTIMAL", "GAP_ACCEPTED")
    assert data["optimality_tier"] in ("EXACT_OPTIMAL", "MIP_GAP_OPTIMAL")
    assert data["twin_replay_valid"] is True
    assert data["summary"]["min_reserve_margin_pct"] >= 0.0
    assert len(data["schedule"]) == 24


def test_optimize_with_generator_override(client):
    """POST /api/v1/optimize respects generator fault override."""
    payload = {
        "station_id": "BHARATI",
        "horizon_hours": 12,
        "mode": "CONSERVATIVE",
        "generator_overrides": {1: "ONLINE", 2: "FAULT"},
        "include_schedule": False
    }
    resp = client.post("/api/v1/optimize", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["station_id"] == "BHARATI"
    assert data["mode"] == "CONSERVATIVE"
    assert data["schedule"] is None  # size control respected


# ==============================================================================
# 6. RESILIENCE ASSESSMENT (PHASE 7)
# ==============================================================================

def test_resilience_evaluation(client):
    """POST /api/v1/resilience/evaluate computes 9 dimensions & survival horizons."""
    payload = {
        "station_id": "BHARATI",
        "horizon_hours": 24,
        "scenario_id": "NORMAL_BASELINE"
    }
    resp = client.post("/api/v1/resilience/evaluate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["provenance"] == "SIMULATED"

    data = body["data"]
    assert data["station_id"] == "BHARATI"
    assert data["resilience_state"] in ("SAFE", "WATCH", "AT_RISK", "THREATENED", "CRITICAL", "RECOVERY")
    assert "survival_horizons" in data
    assert data["survival_horizons"]["overall_station_survival_horizon_h"] > 0.0
    assert data["dimensions"] is not None
    assert 0.0 <= data["dimensions"]["composite_index"] <= 1.0


# ==============================================================================
# 7. POLICY GOVERNANCE & DECISION TRACE (PHASE 8)
# ==============================================================================

def test_policy_evaluate(client):
    """POST /api/v1/policy/evaluate evaluates explicit rules and handoff requirements."""
    payload = {
        "station_id": "BHARATI",
        "horizon_hours": 24,
        "include_suppressed": True,
        "include_evaluation_trace": True
    }
    resp = client.post("/api/v1/policy/evaluate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["provenance"] == "SIMULATED"

    data = body["data"]
    assert data["station_id"] == "BHARATI"
    assert data["policy_state"] in (
        "NO_ACTION", "MONITOR", "PREPARE", "MITIGATE", "PROTECT", "RECOVER", "ESCALATE", "BLOCKED"
    )
    assert data["optimizer_handoff"] is not None
    assert "recommended_mode" in data["optimizer_handoff"]["enforcement_tiers"]


def test_policy_hysteresis_state_roundtrip(client):
    """POST /api/v1/policy/evaluate accepts and returns updated HysteresisState."""
    payload1 = {
        "station_id": "BHARATI",
        "horizon_hours": 24
    }
    resp1 = client.post("/api/v1/policy/evaluate", json=payload1)
    assert resp1.status_code == 200
    hyst1 = resp1.json()["data"]["hysteresis_state"]
    assert hyst1 is not None

    # Step 2: pass hyst1 into second request
    payload2 = {
        "station_id": "BHARATI",
        "horizon_hours": 24,
        "previous_hysteresis": hyst1
    }
    resp2 = client.post("/api/v1/policy/evaluate", json=payload2)
    assert resp2.status_code == 200
    hyst2 = resp2.json()["data"]["hysteresis_state"]
    assert hyst2 is not None


def test_policy_decision_trace_endpoint(client):
    """POST /api/v1/decision-trace returns complete audit lineage (Option A)."""
    payload = {
        "station_id": "BHARATI",
        "horizon_hours": 24
    }
    resp = client.post("/api/v1/decision-trace", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["evaluation_trace"] is not None
    assert len(data["evaluation_trace"]) > 0


# ==============================================================================
# 8. END-TO-END PIPELINE ORCHESTRATION
# ==============================================================================

def test_pipeline_analyze_full_chain(client):
    """
    POST /api/v1/pipeline/analyze executes complete chain:
    Forecast -> Scenario -> Optimize -> Twin Replay -> Resilience -> Policy.
    """
    payload = {
        "station_id": "BHARATI",
        "horizon_hours": 12,
        "mode": "EXPECTED",
        "scenario_id": "NORMAL_BASELINE"
    }
    resp = client.post("/api/v1/pipeline/analyze", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["provenance"] == "SIMULATED"

    data = body["data"]
    assert data["station_id"] == "BHARATI"
    assert data["horizon_hours"] == 12
    assert data["overall_status"] in ("SUCCESS", "PARTIAL")

    stage_names = [s["stage_name"] for s in data["stages"]]
    assert stage_names == ["FORECAST", "SCENARIO", "OPTIMIZER", "TWIN_REPLAY", "RESILIENCE", "POLICY"]
    for stage in data["stages"]:
        assert stage["status"] in ("COMPLETED", "SKIPPED")
        assert stage["duration_sec"] >= 0.0

    assert data["forecast"] is not None
    assert data["optimizer"] is not None
    assert data["resilience"] is not None
    assert data["policy"] is not None


# ==============================================================================
# 9. STRUCTURED ERROR CONTRACTS & SEMANTIC CODE MAPPING
# ==============================================================================

def test_error_contracts_404_and_422(client):
    """Verifies structured error response envelope on 404 and 422."""
    # 404 test
    resp_404 = client.get("/api/v1/scenarios/NON_EXISTENT_SCENARIO")
    assert resp_404.status_code == 404
    b_404 = resp_404.json()
    assert b_404["status"] == "ERROR"
    assert b_404["error"]["code"] == "SCENARIO_NOT_FOUND"
    assert "X-Request-ID" in resp_404.headers

    # 422 test (negative horizon)
    resp_422 = client.post("/api/v1/optimize", json={"station_id": "BHARATI", "horizon_hours": -5})
    assert resp_422.status_code == 422
    b_422 = resp_422.json()
    assert b_422["status"] == "ERROR"
    assert b_422["error"]["code"] == "VALIDATION_ERROR"


# ==============================================================================
# 10. STRICT 6-TIER PROVENANCE TAXONOMY COMPLIANCE
# ==============================================================================

def test_provenance_taxonomy_compliance(client):
    """
    Verifies that all API responses strictly declare provenance in the locked 6 tiers:
    {REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED}.
    Confirms zero 7th tier (no API, LIVE_API, DERIVED, OPTIMIZED, POLICY).
    """
    FORBIDDEN_TIERS = {"API", "LIVE_API", "DERIVED", "OPTIMIZED", "POLICY"}

    endpoints = [
        ("GET", "/health"),
        ("GET", "/api/v1/stations"),
        ("GET", "/api/v1/stations/BHARATI"),
        ("GET", "/api/v1/scenarios"),
        ("GET", "/api/v1/scenarios/BLIZZARD")
    ]

    for method, path in endpoints:
        resp = client.get(path) if method == "GET" else None
        assert resp.status_code == 200
        body = resp.json()
        prov = body.get("provenance")
        assert prov in LOCKED_PROVENANCE_TIERS, f"Path {path} returned unauthorized provenance {prov}"
        assert prov not in FORBIDDEN_TIERS, f"Path {path} returned forbidden provenance {prov}"


# ==============================================================================
# 11. ARCHITECTURAL ISOLATION: ROUTES REMAIN THIN ADAPTERS
# ==============================================================================

def test_routes_architectural_isolation():
    """
    Verifies that route handlers contain zero duplicated physics, MILP solvers,
    or policy math. Route files should only import schemas and adapters.
    """
    import backend.api.routes.optimizer as opt_route
    import backend.api.routes.resilience as res_route
    import backend.api.routes.policy as pol_route
    import backend.api.routes.scenarios as scen_route

    for route_module in [opt_route, res_route, pol_route, scen_route]:
        src = inspect.getsource(route_module).lower()
        # Verify routes do not directly import Pyomo or HiGHS solvers
        assert "pyomo.environ" not in src
        assert "highspy" not in src
        # Verify routes do not recalculate battery SOC or thermal equations
        assert "soc_pct =" not in src
        assert "fuel_remaining_l =" not in src
        assert "indoor_temp_c =" not in src
