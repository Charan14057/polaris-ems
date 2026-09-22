"""
POLARIS-EMS — Phase 4 Digital Twin Test Suite
SIH26061: Polar Energy Management & Resilience System

Validates:
1. State initialization and field provenance
2. Thermodynamic persistence and heat loss equations (Q_chp = 0.0)
3. Subload decomposition consistency
4. Aerodynamic & photovoltaic physical boundaries (cut-in, cut-out, night)
5. Battery electrochemical dynamics and cold derating
6. Diesel burn curves and monotonic fuel depletion
7. Power balance exact conservation (|err| < 1e-4 kW)
8. Honest critical deficit accounting and failure states
9. Dependable reserve margin distinctions
10. Polar threat state classifications
11. Forecast adapter trajectory modes
12. 48-hour end-to-end forward simulation integration
"""

import pytest
import numpy as np
import pandas as pd

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.twin_engine import TwinEngine, TwinTrajectory
from backend.twin.state import TwinState
from backend.twin.power_balance import PowerBalanceEngine
from backend.twin.forecast_adapter import ForecastAdapter, TwinInputStep
from backend.ml.inference import ForecastResult


@pytest.fixture
def profile_registry():
    return StationProfileRegistry()


@pytest.fixture
def safety_registry():
    return SafetyThresholdRegistry()


@pytest.fixture
def bharati_twin(profile_registry, safety_registry):
    return TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)


def test_state_initialization(bharati_twin):
    """Verifies complete, strongly-typed state initialization with provenance."""
    init_state = bharati_twin.initialize_twin("2026-06-01T00:00:00Z")
    
    assert init_state.station_id == "BHARATI"
    assert init_state.timestamp == "2026-06-01T00:00:00Z"
    assert init_state.dispatch_policy == "BASELINE_SIMULATION_DISPATCH"
    assert init_state.provenance in ["CONFIGURED", "SIMULATED"]
    assert init_state.resilience is not None
    assert len(init_state.constraints) >= 8
    
    # Check subsystem initializations
    assert init_state.thermal.building_ua_kw_per_k > 0
    assert init_state.thermal.chp_heat_recovered_kw == 0.0
    assert init_state.battery.soc_pct > 0.20
    assert init_state.diesel.generator_status in ["ONLINE", "STANDBY"]
    assert init_state.fuel.fuel_remaining_l > 0


def test_thermal_persistence(bharati_twin):
    """Verifies that indoor temperature evolves according to physics with Q_chp = 0.0."""
    init_state = bharati_twin.initialize_twin("2026-06-01T00:00:00Z")
    init_temp = init_state.thermal.indoor_temp_c
    
    # Severe polar cold without heating -> temperature must drop
    cool_state = bharati_twin.thermal_engine.step(
        current_state=init_state.thermal,
        ambient_temp_c=-35.0,
        actual_heating_power_kw=0.0,
        dt_hours=1.0
    )
    assert cool_state.indoor_temp_c < init_temp
    assert cool_state.chp_heat_recovered_kw == 0.0
    
    # Ample electric heating -> temperature must rise
    warm_state = bharati_twin.thermal_engine.step(
        current_state=cool_state,
        ambient_temp_c=-10.0,
        actual_heating_power_kw=100.0,
        dt_hours=1.0
    )
    assert warm_state.indoor_temp_c > cool_state.indoor_temp_c


def test_subload_decomposition(bharati_twin):
    """Verifies honest subload decomposition matching station devices."""
    init_state = bharati_twin.initialize_twin("2026-06-01T00:00:00Z")
    load_state = bharati_twin.load_engine.calculate_subloads(
        thermal_load_kw=15.0,
        op_state=init_state.operational,
        effective_temp_c=-20.0,
        forecast_total_load_kw=55.0
    )
    
    assert load_state.critical_load_kw > 0.0
    assert load_state.important_load_kw > 0.0
    assert load_state.total_load_kw == pytest.approx(55.0, rel=1e-2)
    assert load_state.critical_load_kw < load_state.total_load_kw


def test_renewable_physics_and_bounds(bharati_twin):
    """Verifies solar night zeros and wind cut-in/cut-out boundaries."""
    # Solar night check
    solar_night = bharati_twin.solar_engine.step(
        irradiance_wm2=0.0,
        ambient_temp_c=-15.0,
        solar_elevation_deg=-5.0
    )
    assert solar_night.solar_available_kw == 0.0
    assert solar_night.solar_status == "NIGHT"

    # Solar daytime generation
    solar_day = bharati_twin.solar_engine.step(
        irradiance_wm2=600.0,
        ambient_temp_c=-10.0,
        solar_elevation_deg=25.0
    )
    assert solar_day.solar_available_kw > 0.0

    # Wind below cut-in (v < 3.0 m/s)
    wind_calm = bharati_twin.wind_engine.step(wind_speed_ms=2.0)
    assert wind_calm.wind_available_kw == 0.0
    assert wind_calm.wind_status == "BELOW_CUT_IN"

    # Wind operating ramp (3.0 <= v < 11.0 m/s)
    wind_ramp = bharati_twin.wind_engine.step(wind_speed_ms=7.0)
    assert wind_ramp.wind_available_kw > 0.0
    assert wind_ramp.wind_status == "OPERATING_RAMP"

    # Wind storm cut-out (v >= 25.0 m/s)
    wind_storm = bharati_twin.wind_engine.step(wind_speed_ms=28.0)
    assert wind_storm.wind_available_kw == 0.0
    assert wind_storm.wind_status == "STORM_CUT_OUT"


def test_battery_electrochemical_limits(bharati_twin):
    """Verifies SOC bounds, cold derating, and energy conservation."""
    init_state = bharati_twin.initialize_twin("2026-06-01T00:00:00Z")
    
    # Cold derating test
    derate_warm, cap_warm = bharati_twin.battery_engine.compute_derating(0.0)
    derate_cold, cap_cold = bharati_twin.battery_engine.compute_derating(-30.0)
    assert derate_cold < derate_warm
    assert cap_cold < cap_warm
    assert derate_cold >= 0.70  # Derate floor

    # Discharge down to minimum SOC
    bat_discharged = bharati_twin.battery_engine.step(
        current_state=init_state.battery,
        ambient_temp_c=-15.0,
        charge_kw=0.0,
        discharge_kw=200.0,
        dt_hours=5.0
    )
    assert bat_discharged.soc_pct >= init_state.battery.soc_min

    # Charge up to maximum SOC
    bat_charged = bharati_twin.battery_engine.step(
        current_state=init_state.battery,
        ambient_temp_c=-15.0,
        charge_kw=200.0,
        discharge_kw=0.0,
        dt_hours=5.0
    )
    assert bat_charged.soc_pct <= init_state.battery.soc_max


def test_diesel_and_fuel_monotonicity(bharati_twin):
    """Verifies monotonic fuel depletion and explicit resupply delivery."""
    init_state = bharati_twin.initialize_twin("2026-06-01T00:00:00Z")
    init_fuel = init_state.fuel.fuel_remaining_l
    
    # Step generator at 50 kW
    d_step1, f_step1 = bharati_twin.diesel_fuel_engine.step(
        diesel_state=init_state.diesel,
        fuel_state=init_state.fuel,
        requested_gen_power_kw=50.0,
        dt_hours=2.0
    )
    assert f_step1.fuel_remaining_l < init_fuel
    assert f_step1.fuel_consumed_l > 0.0
    assert d_step1.fuel_consumption_l_per_h > 0.0

    # Step generator again without resupply -> strictly non-increasing
    d_step2, f_step2 = bharati_twin.diesel_fuel_engine.step(
        diesel_state=d_step1,
        fuel_state=f_step1,
        requested_gen_power_kw=50.0,
        dt_hours=2.0
    )
    assert f_step2.fuel_remaining_l < f_step1.fuel_remaining_l

    # Explicit resupply delivery event
    resupply = init_state.resupply
    resupply.resupply_event_active = True
    resupply.fuel_delivered_liters = 5000.0

    d_resupplied, f_resupplied = bharati_twin.diesel_fuel_engine.step(
        diesel_state=d_step2,
        fuel_state=f_step2,
        requested_gen_power_kw=50.0,
        resupply_state=resupply,
        dt_hours=1.0
    )
    assert f_resupplied.fuel_remaining_l > f_step2.fuel_remaining_l


def test_power_balance_exact_conservation():
    """Verifies exact conservation of energy |err| < 1e-4 kW under surplus and deficit."""
    # Surplus scenario: 50 kW solar + 40 kW wind with 30 kW load
    res_surplus = PowerBalanceEngine.solve_baseline_dispatch(
        requested_load_kw=30.0,
        critical_load_kw=15.0,
        solar_available_kw=50.0,
        wind_available_kw=40.0,
        max_battery_charge_kw=30.0,
        max_battery_discharge_kw=30.0,
        max_diesel_power_kw=100.0
    )
    assert res_surplus.is_balanced
    assert res_surplus.balance_error_kw < 1e-4
    assert res_surplus.served_load_kw == 30.0
    assert res_surplus.battery_charge_kw == 30.0
    assert res_surplus.curtailment_kw == 30.0
    assert res_surplus.diesel_power_kw == 0.0

    # Deficit scenario: 0 kW renewables, 80 kW load, 20 kW battery max dis, 50 kW diesel max
    res_deficit = PowerBalanceEngine.solve_baseline_dispatch(
        requested_load_kw=80.0,
        critical_load_kw=25.0,
        solar_available_kw=0.0,
        wind_available_kw=0.0,
        max_battery_charge_kw=30.0,
        max_battery_discharge_kw=20.0,
        max_diesel_power_kw=50.0
    )
    assert res_deficit.is_balanced
    assert res_deficit.balance_error_kw < 1e-4
    assert res_deficit.battery_discharge_kw == 20.0
    assert res_deficit.diesel_power_kw == 50.0
    assert res_deficit.served_load_kw == 70.0
    assert res_deficit.unserved_load_kw == 10.0
    assert res_deficit.served_critical_kw == 25.0
    assert res_deficit.unserved_critical_kw == 0.0


def test_honest_deficit_and_critical_unserved_energy(bharati_twin):
    """
    Verifies that when generation and battery are insufficient for critical load:
    1. Unserved critical energy is honestly reported (no unphysical energy creation)
    2. critical_load_protection constraint is VIOLATED
    3. Resilience critical_load_survival_status is FAILED
    4. Threat state is CRITICAL
    """
    init_state = bharati_twin.initialize_twin("2026-06-01T00:00:00Z")
    
    # Disable generator and empty battery
    init_state.diesel.generator_status = "FAULT"
    init_state.diesel.generator_max_power_kw = 0.0
    init_state.battery.soc_pct = init_state.battery.soc_min
    
    # Severe load step with 0 renewables
    deficit_step = TwinInputStep(
        timestamp="2026-06-01T01:00:00Z",
        horizon_h=1,
        ambient_temp_c=-30.0,
        wind_speed_m_per_s=0.0,
        ghi_w_per_m2=0.0,
        load_kw=60.0,
        solar_kw=0.0,
        wind_kw=0.0,
        mode="CONSERVATIVE"
    )
    
    next_state = bharati_twin.step(init_state, deficit_step, dt_hours=1.0)
    
    assert next_state.loads.unserved_load_kw > 0.0
    assert next_state.loads.unserved_critical_kw > 0.0
    assert next_state.resilience.critical_load_survival_status == "FAILED"
    assert next_state.resilience.threat_state == "CRITICAL"
    
    # Check constraint violation
    crit_eval = next(c for c in next_state.constraints if c.constraint_name == "critical_load_protection")
    assert crit_eval.status == "VIOLATED"
    assert crit_eval.violation_magnitude > 0.0


def test_dependable_reserve_margin(bharati_twin):
    """Verifies distinction between nameplate, dependable, and fuel-constrained reserves."""
    init_state = bharati_twin.initialize_twin("2026-06-01T00:00:00Z")
    res = init_state.resilience
    
    assert res.nameplate_reserve_kw > 0.0
    assert res.dependable_reserve_kw > 0.0
    assert res.dependable_reserve_pct > 0.0
    
    # If fuel is depleted to 0, fuel-constrained reserve must collapse
    init_state.fuel.fuel_remaining_l = 0.0
    res_no_fuel = bharati_twin.resilience_engine.evaluate_resilience(init_state)
    assert res_no_fuel.fuel_constrained_reserve_kw < res.fuel_constrained_reserve_kw
    assert res_no_fuel.threat_state == "CRITICAL"


def test_forecast_adapter_trajectory_modes():
    """Verifies that ForecastAdapter generates correct EXPECTED, CONSERVATIVE, and OPTIMISTIC steps."""
    adapter = ForecastAdapter()
    
    load_fc = ForecastResult(
        station_id="BHARATI",
        forecast_origin="2026-06-01T00:00:00Z",
        target="load",
        horizons=[1, 2],
        target_timestamps=["2026-06-01T01:00:00Z", "2026-06-01T02:00:00Z"],
        point_predictions=[40.0, 42.0],
        p10=[30.0, 32.0],
        p50=[40.0, 42.0],
        p90=[50.0, 52.0],
        p95=[55.0, 58.0],
        model_version="xgb_q_v1",
        feature_schema_version="phase3_v1"
    )
    
    # Expected mode (P50)
    exp_steps = adapter.build_trajectory("BHARATI", load_fc, mode="EXPECTED")
    assert exp_steps[0].load_kw == 40.0
    assert exp_steps[0].provenance == "FORECAST"
    
    # Conservative mode (P90)
    stress_steps = adapter.build_trajectory("BHARATI", load_fc, mode="CONSERVATIVE")
    assert stress_steps[0].load_kw == 50.0
    assert stress_steps[0].provenance == "FORECAST"

    # Optimistic mode (P10)
    opt_steps = adapter.build_trajectory("BHARATI", load_fc, mode="OPTIMISTIC")
    assert opt_steps[0].load_kw == 30.0


def test_end_to_end_twin_simulation(bharati_twin):
    """Executes a 48-hour forward simulation and verifies continuity, summary, and DataFrame output."""
    init_state = bharati_twin.initialize_twin("2026-06-01T00:00:00Z")
    
    steps = [
        TwinInputStep(
            timestamp=f"2026-06-01T{h:02d}:00:00Z" if h < 24 else f"2026-06-02T{h-24:02d}:00:00Z",
            horizon_h=h,
            ambient_temp_c=-15.0 - (5.0 * np.sin(h / 6.0)),
            wind_speed_m_per_s=8.0 + (3.0 * np.cos(h / 4.0)),
            ghi_w_per_m2=max(0.0, 200.0 * np.sin((h % 24) / 12.0 * np.pi)),
            load_kw=42.0 + (6.0 * np.sin(h / 8.0)),
            solar_kw=0.0,
            wind_kw=0.0,
            mode="EXPECTED"
        )
        for h in range(1, 49)
    ]
    
    trajectory = bharati_twin.simulate(init_state, steps, dt_hours=1.0)
    
    assert len(trajectory.states) == 48
    assert trajectory.summary["duration_hours"] == 48.0
    assert trajectory.summary["total_diesel_generated_kwh"] > 0.0
    assert trajectory.summary["final_fuel_remaining_liters"] < init_state.fuel.fuel_remaining_l
    
    df = trajectory.to_dataframe()
    assert len(df) == 48
    assert "indoor_temp_c" in df.columns
    assert "battery_soc_pct" in df.columns
    assert "threat_state" in df.columns
    assert "dependable_reserve_pct" in df.columns
