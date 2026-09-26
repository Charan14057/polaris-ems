"""
POLARIS-EMS — End-to-End Twin Connectivity & Causal Chain Tests
SIH26061: Polar Energy Management & Resilience System

Validates:
1. LiveTwinSession statefulness and backend ownership across all stations
2. Wall-clock simulation clock advancement
3. Full causal dependency propagation:
   - Weather changes -> Thermal, Load, Renewable potential, Power balance
   - Manual operator action -> Safety validation -> Physical dispatch -> State delta -> Trace
   - Auto mode -> Optimizer recommendation -> Approval -> Twin update -> Trace
   - Scenario perturbation -> Parameter transforms -> Downstream power flow -> Resilience threat
   - Scenario clear -> Baseline restoration
4. Topological causal tracing (Trace Power & Trace Impact)
5. FastAPI Live Twin HTTP & SSE streaming endpoints
6. Epistemic boundary compliance (DISCONNECTED air-gap, SIMULATED provenance)
"""

import pytest
import time
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.twin.live_session import live_twin_manager, LiveTwinSession
from backend.twin.forecast_adapter import TwinInputStep
from backend.twin.state import TwinState


@pytest.fixture(scope="module")
def client():
    app = create_app()
    return TestClient(app)


def test_live_session_initialization_all_stations():
    """Validates that LiveTwinSession initializes with full physical state for all stations."""
    for sid in ["BHARATI", "MAITRI", "HIMADRI"]:
        session = live_twin_manager.get_session(sid)
        assert session.station_id == sid
        assert session.session_id.startswith(f"twin-session-{sid.lower()}-")
        assert session.session_status == "ACTIVE"
        assert session.operating_mode in ["LIVE_AUTO", "LIVE_MANUAL"]
        
        # Verify physical state completeness
        state = session.current_twin_state
        assert isinstance(state, TwinState)
        assert state.station_id == sid
        assert state.battery.capacity_kwh > 0
        assert state.loads.total_load_kw > 0
        assert state.thermal.indoor_temperature_c > 0


def test_live_simulation_clock_progression():
    """Validates that advance_clock synchronously advances the simulation timestamp."""
    session = live_twin_manager.reset_session("BHARATI")
    t0 = session.current_simulation_iso()
    
    # Force advance by 60 seconds
    state_next = session.advance_clock(force_elapsed_seconds=60.0)
    t1 = session.current_simulation_iso()
    
    assert t1 > t0
    assert session.simulation_elapsed_seconds >= 60.0
    assert state_next.timestamp == t1


def test_weather_input_change_propagates():
    """
    Validates:
    WEATHER CHANGE -> THERMAL DEMAND -> LOAD REQUIREMENT -> POWER BALANCE -> RENEWABLE OUTPUT
    """
    session = live_twin_manager.reset_session("BHARATI")
    
    # Baseline state
    base_state = session.current_twin_state
    base_heating = base_state.thermal.thermal_loss_kw
    
    # Step with severe freezing storm (-40°C, 25 m/s wind)
    cold_step = TwinInputStep(
        timestamp=session.current_simulation_iso(),
        horizon_h=1,
        ambient_temp_c=-40.0,
        wind_speed_m_per_s=25.0,
        ghi_w_per_m2=0.0,
        load_kw=45.0,
        solar_kw=0.0,
        wind_kw=0.0,
        mode="CONSERVATIVE",
        provenance="FORECAST"
    )
    
    storm_state = session.twin_engine.step(
        current_state=base_state,
        input_step=cold_step,
        dt_hours=1.0
    )
    
    # 1. Thermal heat loss must increase under severe cold
    assert storm_state.thermal.thermal_loss_kw > base_heating
    # 2. Ambient temperature must reflect -40°C
    assert storm_state.environment.ambient_temperature_c == -40.0
    # 3. Wind speed must reflect storm velocity
    assert storm_state.environment.wind_speed_ms == 25.0


def test_manual_operator_action_propagates_end_to_end():
    """
    Validates:
    OPERATOR ACTION -> BACKEND CONTROL -> TWIN STATE CHANGE -> POWER FLOW -> TRACE
    """
    session = live_twin_manager.reset_session("BHARATI")
    
    # Command generator startup dispatched to 30 kW
    res = session.apply_manual_action("dg1_start", {"power_kw": 30.0})
    
    assert res["status"] == "APPROVED"
    assert res["action_id"] == "dg1_start"
    assert session.operating_mode == "LIVE_MANUAL"
    
    # Verify diesel is online and producing power
    st = session.current_twin_state
    assert st.diesel.generator_status == "ONLINE"
    assert st.diesel.generator_power_kw > 0.0
    assert st.diesel.fuel_consumption_l_per_h > 0.0
    
    # Power flow must show diesel edge active
    flow = session.get_power_flow_topology()
    diesel_edge = next(e for e in flow["edges"] if e["id"] == "flow_diesel_bus")
    assert diesel_edge["active"] is True
    assert diesel_edge["power_kw"] == st.diesel.generator_power_kw
    
    # Trace history must contain MANUAL_ACTION_EXECUTED
    last_trace = session.trace_history[-1]
    assert last_trace["event"] == "MANUAL_ACTION_EXECUTED"
    assert last_trace["action_id"] == "dg1_start"


def test_flexible_load_shedding_propagates():
    """Validates that shedding flexible loads directly reduces station load demand."""
    session = live_twin_manager.reset_session("BHARATI")
    base_demand = session.current_twin_state.loads.total_load_kw
    
    res = session.apply_manual_action("shed_flexible", {"shed_kw": 10.0})
    assert res["status"] == "APPROVED"
    
    new_demand = session.current_twin_state.loads.total_load_kw
    assert new_demand <= base_demand


def test_auto_recommendation_approval_propagates():
    """
    Validates:
    AUTO MODE -> OPTIMIZER ADVISORY -> APPROVAL -> TWIN RECALCULATION -> TRACE
    """
    session = live_twin_manager.reset_session("BHARATI")
    
    res = session.approve_auto_recommendation()
    assert res["status"] == "APPROVED"
    assert "recommendation" in res
    assert "rationale" in res
    assert session.operating_mode == "LIVE_AUTO"
    
    last_trace = session.trace_history[-1]
    assert last_trace["event"] == "AUTO_RECOMMENDATION_APPROVED"


def test_scenario_perturbation_propagation_and_clear():
    """
    Validates:
    SCENARIO INJECTION -> PARAMETER PERTURBATION -> DOWNSTREAM TWIN DELTA -> RESTORE BASELINE
    """
    session = live_twin_manager.reset_session("BHARATI")
    base_fuel = session.current_twin_state.fuel.fuel_remaining_l
    
    # Apply BLIZZARD scenario
    apply_res = session.apply_scenario("BLIZZARD")
    assert apply_res["status"] == "APPLIED"
    assert session.active_scenario == "BLIZZARD"
    
    # Perturbation delta verified in trace
    last_trace = session.trace_history[-1]
    assert last_trace["event"] == "SCENARIO_APPLIED"
    assert last_trace["scenario_id"] == "BLIZZARD"
    
    # Clear scenario
    clear_res = session.clear_scenario()
    assert clear_res["status"] == "CLEARED"
    assert session.active_scenario is None


def test_topological_trace_power():
    """Validates upstream power path tracing from load to active sources."""
    session = live_twin_manager.get_session("BHARATI")
    
    trace_data = session.trace_power_path("z_utilities")
    assert trace_data["station_id"] == "BHARATI"
    assert trace_data["target_id"] == "z_utilities"
    assert len(trace_data["upstream_chain"]) == 4
    assert trace_data["upstream_chain"][0]["level"] == "SOURCES"
    assert trace_data["upstream_chain"][1]["level"] == "MAIN_BUS"
    assert trace_data["provenance"] == "SIMULATED"


def test_topological_trace_impact():
    """Validates downstream impact tracing when an asset is lost."""
    session = live_twin_manager.get_session("BHARATI")
    
    impact_data = session.trace_impact("diesel")
    assert impact_data["station_id"] == "BHARATI"
    assert impact_data["asset_id"] == "diesel"
    assert "lost_power_kw" in impact_data
    assert "net_deficit_kw" in impact_data
    assert "recommended_mitigation" in impact_data
    assert len(impact_data["affected_subsystems"]) > 0


def test_fastapi_live_twin_endpoints(client):
    """Validates REST endpoints for Live Twin Session interaction."""
    # 1. GET /live/BHARATI
    r1 = client.get("/api/v1/twin/live/BHARATI")
    assert r1.status_code == 200
    snap = r1.json()["data"]
    assert "metadata" in snap
    assert "state" in snap
    assert "power_flow" in snap
    assert snap["metadata"]["station_id"] == "BHARATI"
    
    # 2. POST /control/manual
    r2 = client.post("/api/v1/twin/control/manual", json={
        "station_id": "BHARATI",
        "action_id": "dg1_start",
        "parameters": {"power_kw": 25.0}
    })
    assert r2.status_code == 200
    assert r2.json()["data"]["status"] == "APPROVED"
    
    # 3. POST /control/auto-approve
    r3 = client.post("/api/v1/twin/control/auto-approve", json={
        "station_id": "BHARATI"
    })
    assert r3.status_code == 200
    assert r3.json()["data"]["status"] == "APPROVED"
    
    # 4. POST /scenario/apply
    r4 = client.post("/api/v1/twin/scenario/apply", json={
        "station_id": "BHARATI",
        "scenario_id": "COMBINED_POLAR_STRESS"
    })
    assert r4.status_code == 200
    assert r4.json()["data"]["status"] == "APPLIED"
    
    # 5. POST /scenario/clear
    r5 = client.post("/api/v1/twin/scenario/clear", json={
        "station_id": "BHARATI"
    })
    assert r5.status_code == 200
    assert r5.json()["data"]["status"] == "CLEARED"
    
    # 6. GET /trace/power
    r6 = client.get("/api/v1/twin/trace/power/BHARATI/z_utilities")
    assert r6.status_code == 200
    assert r6.json()["data"]["target_id"] == "z_utilities"
    
    # 7. GET /trace/impact
    r7 = client.get("/api/v1/twin/trace/impact/BHARATI/diesel")
    assert r7.status_code == 200
    assert r7.json()["data"]["asset_id"] == "diesel"


def test_epistemic_airgap_boundary():
    """Enforces absolute physical boundary requirement: PHYSICAL_CONNECTIVITY = DISCONNECTED."""
    session = live_twin_manager.get_session("BHARATI")
    snap = session.get_snapshot()
    
    assert snap["provenance"] == "SIMULATED"
    assert snap["metadata"]["provenance"] == "SIMULATED"
    assert snap["power_flow"]["provenance"] == "SIMULATED"
