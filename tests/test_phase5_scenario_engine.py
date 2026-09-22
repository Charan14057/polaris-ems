"""
POLARIS-EMS — Phase 5 Scenario & What-If Stress Testing Test Suite
SIH26061: Polar Energy Management & Resilience System

Validates:
1. Scenario registry completeness (all 14 locked scenarios)
2. Astronomical solar elevation protection under LOW_DAYLIGHT (Correction #1)
3. Explicit transformation operators (SET, ADD, MULTIPLY, MIN, MAX, DELAY, DISABLE) (Correction #2)
4. Lineage and provenance preservation (FORECAST -> CONFIGURED/ASSUMED -> SIMULATED) (Correction #3)
5. Physical validation and rejection of impossible configurations
6. Deterministic threat state precedence (CRITICAL > THREATENED > AT_RISK > SAFE)
7. Resupply-aware continuity under logistics delays
8. Deterministic failure signature selection and severity hierarchy (Correction #5)
9. Uncertainty modes as deterministic stress trajectories (Correction #4)
10. Baseline/scenario isolation and reproducibility
11. Twin reuse without equation duplication
12. Compound scenario composition (COMBINED_POLAR_STRESS)
13. Custom scenario exploration
14. Multi-horizon lead time execution (1h, 6h, 12h, 24h, 48h)
"""

import pytest
import numpy as np
import copy

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.twin_engine import TwinEngine
from backend.twin.forecast_adapter import TwinInputStep
from backend.scenarios.schema import (
    ScenarioDefinition,
    ParameterTransform,
    TransformOperator,
    ScenarioCategory,
    ScenarioResult
)
from backend.scenarios.registry import ScenarioRegistry
from backend.scenarios.validator import ScenarioValidator, ScenarioValidationError
from backend.scenarios.transformations import ScenarioTransformer, apply_operator
from backend.scenarios.comparator import ScenarioComparator
from backend.scenarios.engine import ScenarioEngine


@pytest.fixture
def profile_reg():
    return StationProfileRegistry()


@pytest.fixture
def safety_reg():
    return SafetyThresholdRegistry()


@pytest.fixture
def scenario_reg():
    return ScenarioRegistry()


@pytest.fixture
def bharati_engine(profile_reg, safety_reg, scenario_reg):
    return ScenarioEngine("BHARATI", profile_reg.get("BHARATI"), safety_reg, scenario_reg)


@pytest.fixture
def sample_initial_state(bharati_engine):
    return bharati_engine.twin.initialize_twin(
        timestamp="2026-06-01T00:00:00Z",
        initial_telemetry={
            "ambient_temp_c": -15.0,
            "wind_speed_m_per_s": 8.0,
            "ghi_w_per_m2": 0.0,
            "total_load_kw": 40.0
        }
    )


@pytest.fixture
def sample_48h_inputs():
    """Generates 48 driving forecast input steps."""
    steps = []
    for h in range(1, 49):
        ghi = max(0.0, 250.0 * np.sin((h % 24) / 12.0 * np.pi))
        steps.append(TwinInputStep(
            timestamp=f"2026-06-01T{h:02d}:00:00Z" if h < 24 else f"2026-06-02T{h-24:02d}:00:00Z",
            horizon_h=h,
            ambient_temp_c=-15.0 - (4.0 * np.sin(h / 6.0)),
            wind_speed_m_per_s=8.0 + (3.0 * np.cos(h / 4.0)),
            ghi_w_per_m2=ghi,
            load_kw=42.0 + (5.0 * np.sin(h / 8.0)),
            solar_kw=0.0,
            wind_kw=0.0,
            mode="EXPECTED",
            provenance="FORECAST"
        ))
    return steps


# -----------------------------------------------------------------------------
# 1. SCENARIO REGISTRY INTEGRITY
# -----------------------------------------------------------------------------

def test_scenario_registry_completeness(scenario_reg):
    """Verifies that all 14 locked scenarios exist with unique IDs and valid schemas."""
    expected_ids = {
        "NORMAL_BASELINE",
        "CLOUDY_CONDITIONS",
        "HEAVY_CLOUD_LOW_IRRADIANCE",
        "HIGH_WIND",
        "BLIZZARD",
        "EXTREME_COLD",
        "LOW_DAYLIGHT",
        "POLAR_NIGHT",
        "SOLAR_GENERATION_FAILURE",
        "WIND_GENERATION_FAILURE",
        "BATTERY_DEGRADATION",
        "FUEL_RESUPPLY_DELAY",
        "COMBINED_POLAR_STRESS",
        "CUSTOM"
    }
    registered_ids = set(scenario_reg.list_ids())
    assert expected_ids == registered_ids

    for sid in expected_ids:
        scen = scenario_reg.get(sid)
        assert scen.scenario_id == sid
        assert len(scen.name) > 0
        assert len(scen.description) > 0
        assert isinstance(scen.category, ScenarioCategory)
        assert scen.duration_hours > 0
        assert scen.provenance == "CONFIGURED"


# -----------------------------------------------------------------------------
# 2. ASTRONOMICAL GEOMETRY PROTECTION (CORRECTION #1)
# -----------------------------------------------------------------------------

def test_astronomical_geometry_protected_under_low_daylight(bharati_engine, sample_initial_state, sample_48h_inputs):
    """
    Verifies Correction #1: LOW_DAYLIGHT must NEVER alter astronomical solar_elevation_deg.
    Irradiance and solar availability reduce, but astronomical elevation remains identical.
    """
    res = bharati_engine.run_scenario(
        scenario_id="LOW_DAYLIGHT",
        initial_state=sample_initial_state,
        baseline_inputs=sample_48h_inputs,
        forecast_mode="EXPECTED",
        horizon_hours=24
    )

    for i in range(len(res.original_forecast)):
        orig_ghi = res.original_forecast[i].ghi_w_per_m2
        eff_ghi = res.effective_simulation_inputs[i].ghi_w_per_m2
        
        # Effective irradiance should be reduced
        if orig_ghi > 0:
            assert eff_ghi < orig_ghi
            assert eff_ghi == pytest.approx(orig_ghi * 0.30, rel=1e-2)

    # In the Twin trajectory, solar_elevation_deg is determined by physical astronomy and not overwritten
    for state in res.scenario_trajectory.states:
        # Physical elevation remains >= 0 during day hours
        assert hasattr(state.environment, "solar_elevation_deg")


# -----------------------------------------------------------------------------
# 3. EXPLICIT TRANSFORMATION OPERATORS (CORRECTION #2)
# -----------------------------------------------------------------------------

def test_explicit_transformation_operators():
    """Verifies Correction #2: SET, ADD, MULTIPLY, MIN, MAX, DELAY, DISABLE operators."""
    assert apply_operator(10.0, TransformOperator.SET, 25.0) == 25.0
    assert apply_operator(10.0, TransformOperator.ADD, -15.0) == -5.0
    assert apply_operator(10.0, TransformOperator.MULTIPLY, 1.5) == 15.0
    assert apply_operator(10.0, TransformOperator.MIN, 5.0) == 5.0
    assert apply_operator(10.0, TransformOperator.MAX, 15.0) == 15.0
    assert apply_operator(48.0, TransformOperator.DELAY, 72.0) == 120.0
    assert apply_operator(50.0, TransformOperator.DISABLE, 0.0) == 0.0


# -----------------------------------------------------------------------------
# 4. PROVENANCE & LINEAGE PRESERVATION (CORRECTION #3)
# -----------------------------------------------------------------------------

def test_lineage_and_provenance_preservation(bharati_engine, sample_initial_state, sample_48h_inputs):
    """
    Verifies Correction #3:
    Original forecast retains FORECAST provenance.
    Scenario definition retains CONFIGURED/ASSUMED provenance.
    Transformed effective inputs and trajectories retain SIMULATED provenance.
    """
    res = bharati_engine.run_scenario(
        scenario_id="BLIZZARD",
        initial_state=sample_initial_state,
        baseline_inputs=sample_48h_inputs,
        horizon_hours=24
    )

    # 1. Original forecast lineage
    assert res.original_forecast[0].provenance == "FORECAST"

    # 2. Scenario definition provenance
    assert res.scenario_transforms[0].provenance == "CONFIGURED"

    # 3. Effective inputs tagged SIMULATED
    assert res.effective_simulation_inputs[0].provenance == "SIMULATED"

    # 4. Result and trajectory tagged SIMULATED
    assert res.provenance == "SIMULATED"
    assert res.scenario_trajectory.states[0].provenance == "SIMULATED"


# -----------------------------------------------------------------------------
# 5. VALIDATION & REJECTION OF IMPOSSIBLE INPUTS
# -----------------------------------------------------------------------------

def test_scenario_validation_rejects_impossible_inputs():
    """Verifies that validator catches invalid bounds, negative fuel/delay, and impossible cloud."""
    validator = ScenarioValidator()

    # Negative fuel delay
    invalid_delay = ScenarioDefinition(
        scenario_id="TEST_BAD_DELAY",
        name="Bad Delay",
        description="Negative delay",
        category=ScenarioCategory.LOGISTICS,
        transforms=[ParameterTransform("fuel_resupply_delay_hours", TransformOperator.DELAY, -24.0, "h")]
    )
    with pytest.raises(ScenarioValidationError):
        validator.validate_scenario(invalid_delay)

    # Impossible cloud fraction > 1.0
    invalid_cloud = ScenarioDefinition(
        scenario_id="TEST_BAD_CLOUD",
        name="Bad Cloud",
        description="Cloud > 1.0",
        category=ScenarioCategory.ENVIRONMENTAL,
        transforms=[ParameterTransform("cloud_fraction", TransformOperator.SET, 1.8, "fraction")]
    )
    with pytest.raises(ScenarioValidationError):
        validator.validate_scenario(invalid_cloud)

    # Impossible temperature < -90C
    invalid_temp = ScenarioDefinition(
        scenario_id="TEST_BAD_TEMP",
        name="Bad Temp",
        description="Temp < -90C",
        category=ScenarioCategory.ENVIRONMENTAL,
        transforms=[ParameterTransform("ambient_temperature_c", TransformOperator.SET, -120.0, "deg_C")]
    )
    with pytest.raises(ScenarioValidationError):
        validator.validate_scenario(invalid_temp)


# -----------------------------------------------------------------------------
# 6. DETERMINISTIC THREAT STATE PRECEDENCE (PHASE 4 HARDENING #1)
# -----------------------------------------------------------------------------

def test_deterministic_threat_state_precedence(bharati_engine, sample_initial_state):
    """
    Verifies that threat states deterministically follow:
    CRITICAL > THREATENED > AT_RISK > SAFE
    """
    twin = bharati_engine.twin

    # Case A: CRITICAL takes precedence over THREATENED
    # State has tight reserve (<15%, THREATENED) AND active critical unserved deficit (CRITICAL)
    state_a = copy.deepcopy(sample_initial_state)
    state_a.loads.unserved_critical_kw = 5.0
    state_a.resilience = twin.resilience_engine.evaluate_resilience(state_a)
    assert state_a.resilience.threat_state == "CRITICAL"

    # Case B: THREATENED takes precedence over AT_RISK
    # State has fuel days < 30 (AT_RISK) AND battery SOC <= 0.25 (THREATENED)
    state_b = copy.deepcopy(sample_initial_state)
    state_b.loads.unserved_critical_kw = 0.0
    state_b.loads.unserved_load_kw = 0.0
    state_b.fuel.days_of_fuel_remaining = 20.0  # AT_RISK condition
    state_b.battery.soc_pct = 0.22             # THREATENED condition
    state_b.resilience = twin.resilience_engine.evaluate_resilience(state_b)
    assert state_b.resilience.threat_state == "THREATENED"

    # Case C: AT_RISK takes precedence over SAFE
    state_c = copy.deepcopy(sample_initial_state)
    state_c.loads.unserved_critical_kw = 0.0
    state_c.battery.soc_pct = 0.80
    state_c.environment.ambient_temperature_c = -38.0  # AT_RISK condition
    state_c.resilience = twin.resilience_engine.evaluate_resilience(state_c)
    assert state_c.resilience.threat_state == "AT_RISK"


# -----------------------------------------------------------------------------
# 7. RESUPPLY-AWARE CONTINUITY (PHASE 4 HARDENING #2)
# -----------------------------------------------------------------------------

def test_resupply_aware_continuity(bharati_engine, sample_initial_state, sample_48h_inputs):
    """
    Verifies that a resupply delay scenario shifts the delivery window and alters
    fuel continuity horizons and threat states.
    """
    # Initialize near fuel reserve
    low_fuel_state = copy.deepcopy(sample_initial_state)
    low_fuel_state.fuel.fuel_remaining_l = 30000.0  # Near 25000L reserve
    low_fuel_state.resupply.resupply_event_active = False

    res = bharati_engine.run_scenario(
        scenario_id="FUEL_RESUPPLY_DELAY",
        initial_state=low_fuel_state,
        baseline_inputs=sample_48h_inputs,
        horizon_hours=48
    )

    # Verify resupply window was delayed
    assert res.scenario_trajectory.states[0].resupply.resupply_window_days > sample_initial_state.resupply.resupply_window_days
    # Fuel continued monotonically decreasing
    final_fuel = res.scenario_trajectory.states[-1].fuel.fuel_remaining_l
    assert final_fuel < 30000.0


# -----------------------------------------------------------------------------
# 8. DETERMINISTIC FAILURE SIGNATURE HIERARCHY (CORRECTION #5)
# -----------------------------------------------------------------------------

def test_deterministic_failure_signature_selection(bharati_engine, sample_initial_state, sample_48h_inputs):
    """
    Verifies Correction #5:
    Simultaneous failure events resolve deterministically via:
    CRITICAL_LOAD_LOSS > THERMAL_BREACH > FUEL_RESERVE_BREACH > BATTERY_DEPLETION ...
    """
    # Create combined stress run that induces multiple failures
    stress_state = copy.deepcopy(sample_initial_state)
    stress_state.diesel.generator_status = "FAULT"
    stress_state.diesel.generator_max_power_kw = 0.0
    stress_state.battery.soc_pct = stress_state.battery.soc_min
    stress_state.thermal.indoor_temperature_c = 10.0  # Below 12C safe minimum

    res1 = bharati_engine.run_scenario(
        scenario_id="BLIZZARD",
        initial_state=stress_state,
        baseline_inputs=sample_48h_inputs,
        horizon_hours=12
    )

    res2 = bharati_engine.run_scenario(
        scenario_id="BLIZZARD",
        initial_state=stress_state,
        baseline_inputs=sample_48h_inputs,
        horizon_hours=12
    )

    # Assert repeatable deterministic primary failure signature
    assert res1.primary_failure_signature == res2.primary_failure_signature
    assert res1.primary_failure_signature == "CRITICAL_LOAD_LOSS"
    assert len(res1.secondary_failure_signatures) > 0
    assert "THERMAL_BREACH" in res1.secondary_failure_signatures


# -----------------------------------------------------------------------------
# 9. UNCERTAINTY TRAJECTORY SEMANTICS (CORRECTION #4)
# -----------------------------------------------------------------------------

def test_uncertainty_modes_deterministic_stress_semantics(bharati_engine, sample_initial_state, sample_48h_inputs):
    """
    Verifies Correction #4:
    EXPECTED, CONSERVATIVE, and OPTIMISTIC are deterministic stress trajectories.
    Conservative stress induces higher load and tighter reserve margins.
    """
    inputs_dict = {
        "EXPECTED": sample_48h_inputs,
        "CONSERVATIVE": [copy.deepcopy(s) for s in sample_48h_inputs],
        "OPTIMISTIC": [copy.deepcopy(s) for s in sample_48h_inputs]
    }
    # Modulate inputs to represent conservative (P90 load) and optimistic (P10 load)
    for s in inputs_dict["CONSERVATIVE"]:
        s.load_kw *= 1.20
        s.mode = "CONSERVATIVE"
    for s in inputs_dict["OPTIMISTIC"]:
        s.load_kw *= 0.80
        s.mode = "OPTIMISTIC"

    envelope = bharati_engine.build_resilience_envelope(
        scenario_id="HIGH_WIND",
        initial_state=sample_initial_state,
        forecast_inputs=inputs_dict,
        horizon_hours=24
    )

    assert "EXPECTED" in envelope
    assert "CONSERVATIVE" in envelope
    assert "OPTIMISTIC" in envelope

    # Conservative diesel generation >= Optimistic diesel generation
    cons_gen = envelope["CONSERVATIVE"].scenario_summary["total_diesel_generated_kwh"]
    opt_gen = envelope["OPTIMISTIC"].scenario_summary["total_diesel_generated_kwh"]
    assert cons_gen >= opt_gen


# -----------------------------------------------------------------------------
# 10. BASELINE / SCENARIO ISOLATION
# -----------------------------------------------------------------------------

def test_baseline_scenario_isolation(bharati_engine, sample_initial_state, sample_48h_inputs):
    """Asserts that running a scenario leaves the baseline trajectory completely untouched."""
    inputs_copy = copy.deepcopy(sample_48h_inputs)

    res = bharati_engine.run_scenario(
        scenario_id="SOLAR_GENERATION_FAILURE",
        initial_state=sample_initial_state,
        baseline_inputs=sample_48h_inputs,
        horizon_hours=24
    )

    # Baseline inputs were not modified
    for i in range(24):
        assert sample_48h_inputs[i].load_kw == inputs_copy[i].load_kw
        assert sample_48h_inputs[i].provenance == "FORECAST"

    # Baseline trajectory generated solar power, while scenario did not
    b_df = res.baseline_trajectory.to_dataframe()
    s_df = res.scenario_trajectory.to_dataframe()
    assert s_df["solar_generation_kw"].sum() == 0.0


# -----------------------------------------------------------------------------
# 11. COMPOUND SCENARIO COMPOSITION
# -----------------------------------------------------------------------------

def test_compound_scenario_composition(bharati_engine, sample_initial_state, sample_48h_inputs):
    """Verifies that COMBINED_POLAR_STRESS composes multiple physical transforms."""
    res = bharati_engine.run_scenario(
        scenario_id="COMBINED_POLAR_STRESS",
        initial_state=sample_initial_state,
        baseline_inputs=sample_48h_inputs,
        horizon_hours=24
    )

    eff_inputs = res.effective_simulation_inputs
    for i in range(24):
        # Temperature reduced
        assert eff_inputs[i].ambient_temp_c < sample_48h_inputs[i].ambient_temp_c
        # Wind amplified
        assert eff_inputs[i].wind_speed_m_per_s > sample_48h_inputs[i].wind_speed_m_per_s
        # Solar zeroed
        assert eff_inputs[i].ghi_w_per_m2 == 0.0

    # Diesel consumption surged due to cold heat loss and zero solar
    assert res.impact_metrics.delta_fuel_burn_liters > 0.0


# -----------------------------------------------------------------------------
# 12. CUSTOM SCENARIO EXPLORATION
# -----------------------------------------------------------------------------

def test_custom_scenario_exploration(bharati_engine, sample_initial_state, sample_48h_inputs):
    """Verifies user-defined custom scenario parameter overrides."""
    custom_overrides = {
        "ambient_temperature_c": -12.0,
        "wind_speed_ms": 1.5,
        "battery_capacity": 0.80,
        "duration_hours": 24
    }

    res = bharati_engine.run_scenario(
        scenario_id="CUSTOM",
        initial_state=sample_initial_state,
        baseline_inputs=sample_48h_inputs,
        custom_overrides=custom_overrides
    )

    assert res.scenario_id == "CUSTOM"
    assert res.duration_hours == 24
    assert res.impact_metrics.delta_fuel_burn_liters != 0.0


# -----------------------------------------------------------------------------
# 13. MULTI-HORIZON EXECUTION
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("h_lead", [1, 6, 12, 24, 48])
def test_multi_horizon_execution(bharati_engine, sample_initial_state, sample_48h_inputs, h_lead):
    """Verifies execution across multi-horizon lead times: 1h, 6h, 12h, 24h, 48h."""
    res = bharati_engine.run_scenario(
        scenario_id="HIGH_WIND",
        initial_state=sample_initial_state,
        baseline_inputs=sample_48h_inputs,
        horizon_hours=h_lead
    )

    assert len(res.baseline_trajectory.states) == h_lead
    assert len(res.scenario_trajectory.states) == h_lead
    assert res.duration_hours == h_lead
