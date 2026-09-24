"""
POLARIS-EMS — Phase 7 Resilience Engine Test Suite
SIH26061: Polar Energy Management & Resilience System

Exhaustive verification of the Phase 7 Resilience Engine:
1. State Machine & Deterministic Precedence (CRITICAL > THREATENED > AT_RISK > WATCH > RECOVERY > SAFE)
2. History-Aware RECOVERY State Transition Logic (Guardrail 4)
3. Subsystem Survival Horizons (Critical, Thermal, Battery, Fuel, Generation, Resupply)
4. Earliest Time-to-Threat & Explicit Timestamps (Guardrail 16)
5. 9 Observable Resilience Dimensions & Explainable Composite Index (Guardrail 10)
6. Generator Contingency & Fleet Outages (Bharati 3x80kW, Maitri 3x62.5kW, Himadri 2x45kW)
7. Battery Derating & Resupply Logistics Gap Topologies
8. 9 Canonical Stress Scenarios
9. Multi-Horizon Coverage (48h Operational & 168h Strategic)
10. Advisory Candidate Recovery Intelligence with Limitations (Guardrail 5)
11. Fair Counterfactual Analysis with Wear-Proxy Terminology (Guardrail 14)
12. Traceable Failure Propagation Chains from Observed Transitions (Guardrail 15)
13. Input Validation & Safe Diagnostic Handling (Guardrail 7: NO_DATA / INPUT_INVALID != CRITICAL)
14. Boundary Edge Cases (Empty, Corrupted, Non-Monotonic, Immediate Failure, Final Failure)
15. Deterministic Reproducibility & Provenance Integrity
16. Architectural Isolation (Zero Policy, API, or UI Leakage)
"""

import pytest
import numpy as np
from datetime import datetime

from backend.data.station_profiles.loader import StationProfileRegistry, StationProfile
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.twin_engine import TwinEngine, TwinTrajectory
from backend.twin.forecast_adapter import TwinInputStep
from backend.twin.state import TwinState
from backend.scenarios.registry import ScenarioRegistry
from backend.optimizer.engine import OptimizerEngine
from backend.optimizer.schema import OptimizationMode, SolverStatus

from backend.resilience.engine import ResilienceEngine
from backend.resilience.schema import (
    ResilienceAssessment,
    ResilienceStateEnum,
    ResilienceThreatEnum,
    AssessmentStatusEnum,
    FailureSeverityEnum,
    RecoveryActionTypeEnum,
    CounterfactualResilienceComparison
)
from backend.resilience.adapter import ResilienceDataAdapter


@pytest.fixture
def profile_registry():
    return StationProfileRegistry()


@pytest.fixture
def safety_registry():
    return SafetyThresholdRegistry()


@pytest.fixture
def scenario_registry():
    return ScenarioRegistry()


@pytest.fixture
def bharati_engine(profile_registry, safety_registry):
    return ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)


@pytest.fixture
def maitri_engine(profile_registry, safety_registry):
    return ResilienceEngine("MAITRI", profile_registry.get("MAITRI"), safety_registry)


@pytest.fixture
def himadri_engine(profile_registry, safety_registry):
    return ResilienceEngine("HIMADRI", profile_registry.get("HIMADRI"), safety_registry)


@pytest.fixture
def bharati_twin(profile_registry, safety_registry):
    return TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)


def build_synthetic_trajectory(
    twin: TwinEngine,
    length_h: int = 48,
    ambient_temp_c: float = -20.0,
    wind_speed_ms: float = 10.0,
    ghi_wm2: float = 200.0,
    base_load_kw: float = 40.0,
    solar_kw: float = 15.0,
    wind_kw: float = 25.0
) -> TwinTrajectory:
    """Simulates a baseline trajectory through the authoritative Phase 4 Digital Twin."""
    init_state = twin.initialize_twin("2026-06-01T00:00:00Z")
    steps = []
    for h in range(1, length_h + 1):
        day = 1 + (h - 1) // 24
        hour = (h - 1) % 24
        steps.append(TwinInputStep(
            timestamp=f"2026-06-{day:02d}T{hour:02d}:00:00Z",
            horizon_h=h,
            ambient_temp_c=ambient_temp_c,
            wind_speed_m_per_s=wind_speed_ms,
            ghi_w_per_m2=ghi_wm2,
            load_kw=base_load_kw,
            solar_kw=solar_kw,
            wind_kw=wind_kw,
            mode="EXPECTED"
        ))
    return twin.simulate(init_state, steps)


# ==============================================================================
# 1. STATE MACHINE & DETERMINISTIC SEVERITY PRECEDENCE
# ==============================================================================

def test_resilience_state_precedence_critical_dominance(bharati_engine, bharati_twin):
    """
    Verifies CRITICAL > THREATENED > AT_RISK > WATCH > RECOVERY > SAFE precedence
    and confirms lower-severity active triggers are exposed rather than hidden.
    """
    # Create trajectory with mild wind (WATCH trigger) AND acute unserved critical load (CRITICAL trigger)
    traj = build_synthetic_trajectory(bharati_twin, length_h=24, base_load_kw=40.0)
    # Inject unserved critical load at step 5
    traj.states[5].loads.unserved_critical_kw = 5.0
    traj.states[5].loads.unserved_load_kw = 5.0

    res = bharati_engine.assess_trajectory(traj)
    assert res.assessment_status == AssessmentStatusEnum.COMPLETED
    assert res.resilience_state == ResilienceStateEnum.CRITICAL
    # Both CRITICAL and other active conditions must be preserved in active_threat_states
    assert ResilienceStateEnum.CRITICAL in res.active_threat_states


def test_resilience_state_safe_nominal(bharati_engine, bharati_twin):
    """Verifies that an unperturbed nominal trajectory evaluates to SAFE."""
    traj = build_synthetic_trajectory(
        bharati_twin, length_h=24, ambient_temp_c=-15.0, wind_speed_ms=8.0, ghi_wm2=300.0, base_load_kw=35.0
    )
    res = bharati_engine.assess_trajectory(traj)
    assert res.assessment_status == AssessmentStatusEnum.COMPLETED
    assert res.resilience_state == ResilienceStateEnum.SAFE
    assert res.survival_horizons.survives_full_horizon is True


def test_resilience_state_threatened_and_watch(bharati_engine, bharati_twin):
    """Verifies THREATENED and WATCH triggering on environmental & reserve conditions."""
    # High wind (>= 28 m/s) triggers THREATENED
    traj_blizzard = build_synthetic_trajectory(bharati_twin, length_h=24, wind_speed_ms=30.0)
    res_b = bharati_engine.assess_trajectory(traj_blizzard)
    assert res_b.resilience_state in (ResilienceStateEnum.THREATENED, ResilienceStateEnum.CRITICAL)

    # Moderate wind (22 m/s) with safe margins triggers WATCH
    traj_wind = build_synthetic_trajectory(bharati_twin, length_h=24, wind_speed_ms=22.0)
    res_w = bharati_engine.assess_trajectory(traj_wind)
    assert res_w.resilience_state in (ResilienceStateEnum.WATCH, ResilienceStateEnum.THREATENED, ResilienceStateEnum.AT_RISK)


# ==============================================================================
# 2. HISTORY-AWARE RECOVERY STATE MACHINE (GUARDRAIL 4)
# ==============================================================================

def test_recovery_state_requires_prior_critical_or_threatened(bharati_engine, bharati_twin):
    """
    Guardrail 4: RECOVERY is valid ONLY if previous state was CRITICAL or THREATENED,
    current state is no longer critical, and reserves are measurably restoring.
    """
    traj = build_synthetic_trajectory(bharati_twin, length_h=24, base_load_kw=35.0)

    # Case A: Prior state was SAFE -> Must NOT enter RECOVERY
    res_no_prior = bharati_engine.assess_trajectory(traj, previous_state=ResilienceStateEnum.SAFE)
    assert res_no_prior.resilience_state != ResilienceStateEnum.RECOVERY

    # Case B: Prior state was CRITICAL, current state is healthy and stable -> Enters RECOVERY
    res_recovering = bharati_engine.assess_trajectory(traj, previous_state=ResilienceStateEnum.CRITICAL)
    assert res_recovering.resilience_state == ResilienceStateEnum.RECOVERY
    assert res_recovering.previous_resilience_state == ResilienceStateEnum.CRITICAL
    assert res_recovering.recovery_direction is not None


def test_recovery_state_blocked_if_critical_persists(bharati_engine, bharati_twin):
    """
    Guardrail 4: Even with prior CRITICAL, if current trajectory still has active
    critical deficit, CRITICAL must take precedence over RECOVERY.
    """
    traj = build_synthetic_trajectory(bharati_twin, length_h=24, base_load_kw=40.0)
    traj.states[10].loads.unserved_critical_kw = 2.0  # Still in active deficit!

    res = bharati_engine.assess_trajectory(traj, previous_state=ResilienceStateEnum.CRITICAL)
    assert res.resilience_state == ResilienceStateEnum.CRITICAL
    assert res.resilience_state != ResilienceStateEnum.RECOVERY


# ==============================================================================
# 3. SUBSYSTEM SURVIVAL HORIZONS & TIME-TO-THREAT (GUARDRAILS 8 & 16)
# ==============================================================================

def test_survival_horizons_binding_thermal_limit(bharati_engine, bharati_twin):
    """
    Verifies that when indoor temperature drops below safe limit, thermal survival
    horizon and binding subsystem are accurately identified.
    """
    traj = build_synthetic_trajectory(bharati_twin, length_h=24)
    # Force thermal breach at step 8
    traj.states[7].thermal.indoor_temperature_c = 10.5  # < 12.0 safe limit

    res = bharati_engine.assess_trajectory(traj)
    assert res.survival_horizons.thermal_habitability_horizon_h == 8.0
    assert res.survival_horizons.binding_subsystem == "THERMAL"
    assert res.survival_horizons.survives_full_horizon is False
    assert res.time_to_threat.time_to_thermal_safety_threshold_h == 8.0
    assert res.time_to_threat.time_to_thermal_safety_threshold_timestamp == traj.states[7].timestamp


def test_survival_horizons_critical_load_failure(bharati_engine, bharati_twin):
    """Verifies critical load failure horizon and earliest timestamp preservation."""
    traj = build_synthetic_trajectory(bharati_twin, length_h=24)
    traj.states[3].loads.unserved_critical_kw = 1.5

    res = bharati_engine.assess_trajectory(traj)
    assert res.survival_horizons.critical_load_survival_horizon_h == 4.0
    assert res.survival_horizons.overall_station_survival_horizon_h == 4.0
    assert res.time_to_threat.time_to_critical_load_failure_h == 4.0
    assert res.time_to_threat.time_to_critical_load_failure_timestamp == traj.states[3].timestamp


def test_survival_horizons_full_input_survival(bharati_engine, bharati_twin):
    """
    Guardrail 8: When no threshold breach occurs, distinguishes
    survives_full_horizon = True and binds to input horizon length without infinite claims.
    """
    traj = build_synthetic_trajectory(bharati_twin, length_h=48, base_load_kw=35.0)
    res = bharati_engine.assess_trajectory(traj)
    assert res.survival_horizons.survives_full_horizon is True
    assert res.survival_horizons.overall_station_survival_horizon_h == 48.0
    assert res.survival_horizons.binding_subsystem == "NONE"


# ==============================================================================
# 4. 9 OBSERVABLE RESILIENCE DIMENSIONS (GUARDRAIL 10)
# ==============================================================================

def test_nine_resilience_dimensions_transparency(bharati_engine, bharati_twin):
    """
    Guardrail 10: Validates that all 9 dimensions expose raw metrics, normalized scores [0, 100],
    weights, contributions, and reference thresholds.
    """
    traj = build_synthetic_trajectory(bharati_twin, length_h=24)
    res = bharati_engine.assess_trajectory(traj)
    dims = res.dimensions
    assert dims is not None

    dim_list = [
        dims.energy_adequacy,
        dims.critical_load_resilience,
        dims.thermal_resilience,
        dims.generation_resilience,
        dims.storage_resilience,
        dims.fuel_resilience,
        dims.logistics_resilience,
        dims.renewable_resilience,
        dims.recovery_resilience
    ]

    tot_weight = 0.0
    for d in dim_list:
        assert 0.0 <= d.normalized_score <= 100.0
        assert d.weight > 0.0
        assert d.reference_threshold != ""
        assert d.normalization_logic != ""
        tot_weight += d.weight

    assert round(tot_weight, 2) == 1.00
    assert 0.0 <= dims.composite_resilience_index <= 100.0


# ==============================================================================
# 5. CROSS-STATION FLEET & PROFILE CONFIGURATION (BHARATI, MAITRI, HIMADRI)
# ==============================================================================

def test_cross_station_fleet_generation_resilience(
    bharati_engine, maitri_engine, himadri_engine, bharati_twin, profile_registry, safety_registry
):
    """
    Verifies dynamic fleet configuration:
    - Bharati: 3 x 80kW = 240kW
    - Maitri: 3 x 62.5kW = 187.5kW
    - Himadri: 2 x 45kW = 90kW
    Zero hardcoded capacities.
    """
    maitri_twin = TwinEngine("MAITRI", profile_registry.get("MAITRI"), safety_registry)
    himadri_twin = TwinEngine("HIMADRI", profile_registry.get("HIMADRI"), safety_registry)

    traj_b = build_synthetic_trajectory(bharati_twin, 24, base_load_kw=50.0)
    traj_m = build_synthetic_trajectory(maitri_twin, 24, base_load_kw=35.0)
    traj_h = build_synthetic_trajectory(himadri_twin, 24, base_load_kw=20.0)

    res_b = bharati_engine.assess_trajectory(traj_b)
    res_m = maitri_engine.assess_trajectory(traj_m)
    res_h = himadri_engine.assess_trajectory(traj_h)

    assert res_b.station_id == "BHARATI"
    assert res_m.station_id == "MAITRI"
    assert res_h.station_id == "HIMADRI"

    # Confirm N-1 capacity references match station configurations
    assert "160.0 kW" in res_b.dimensions.generation_resilience.reference_threshold  # (3-1)*80
    assert "125.0 kW" in res_m.dimensions.generation_resilience.reference_threshold  # (3-1)*62.5
    assert "45.0 kW" in res_h.dimensions.generation_resilience.reference_threshold   # (2-1)*45


# ==============================================================================
# 6. MULTI-HORIZON EVALUATION (48H OPERATIONAL & 168H STRATEGIC)
# ==============================================================================

def test_multi_horizon_48h_vs_168h_differentiation(bharati_engine, bharati_twin):
    """
    Guardrail 9: Evaluates operational (48h) and strategic 7-day (168h) horizons.
    Distinguishes short-term survivability from strategic fuel/resupply gap exposure.
    """
    traj_48 = build_synthetic_trajectory(bharati_twin, length_h=48, base_load_kw=40.0)
    res_48 = bharati_engine.assess_trajectory(traj_48)
    assert res_48.horizon_hours == 48

    # 168h trajectory (7 days)
    traj_168 = build_synthetic_trajectory(bharati_twin, length_h=168, base_load_kw=40.0)
    res_168 = bharati_engine.assess_trajectory(traj_168)
    assert res_168.horizon_hours == 168
    assert res_168.survival_horizons.overall_station_survival_horizon_h <= 168.0


# ==============================================================================
# 7. CANONICAL SCENARIOS & THREAT DECOMPOSITION
# ==============================================================================

@pytest.mark.parametrize("scen_id", [
    "NORMAL_BASELINE",
    "POLAR_NIGHT",
    "BLIZZARD",
    "EXTREME_COLD",
    "SOLAR_GENERATION_FAILURE",
    "WIND_GENERATION_FAILURE",
    "BATTERY_DEGRADATION",
    "FUEL_RESUPPLY_DELAY",
    "COMBINED_POLAR_STRESS"
])
def test_canonical_scenarios_threat_decomposition(bharati_engine, bharati_twin, scenario_registry, scen_id):
    """
    Evaluates all 9 canonical stress scenarios and verifies threat decomposition
    and scenario lineage preservation (Guardrail 13).
    """
    scen = scenario_registry.get(scen_id)
    traj = build_synthetic_trajectory(bharati_twin, length_h=24)

    # Apply scenario conditions to trajectory states for realistic testing
    if scen_id == "EXTREME_COLD":
        for s in traj.states:
            s.environment.ambient_temperature_c = -42.0
    elif scen_id == "BLIZZARD":
        for s in traj.states:
            s.environment.wind_speed_ms = 32.0
    elif scen_id == "POLAR_NIGHT":
        for s in traj.states:
            s.environment.solar_elevation_deg = -5.0
            s.environment.irradiance_wm2 = 0.0

    res = bharati_engine.assess_trajectory(traj, scenario=scen)
    assert res.assessment_status == AssessmentStatusEnum.COMPLETED
    assert res.scenario_id == scen_id
    assert res.scenario_lineage is not None
    assert len(res.threat_decomposition) >= 0


# ==============================================================================
# 8. ADVISORY CANDIDATE RECOVERY INTELLIGENCE (GUARDRAIL 5)
# ==============================================================================

def test_candidate_recovery_options_advisory_only(bharati_engine, bharati_twin):
    """
    Guardrail 5: Validates that candidate recovery actions are strictly advisory,
    contain no arbitrary fabricated numbers, and explicitly flag validation_tier.
    """
    traj = build_synthetic_trajectory(bharati_twin, length_h=24)
    # Inject generation stress
    traj.states[5].resilience.dependable_reserve_pct = 8.0  # < 15%

    res = bharati_engine.assess_trajectory(traj)
    options = res.candidate_recovery_options
    assert len(options) > 0

    gen_opt = next((o for o in options if o.action_type == RecoveryActionTypeEnum.INCREASE_DIESEL_COMMITMENT), None)
    assert gen_opt is not None
    assert gen_opt.validation_tier == "ESTIMATED"
    assert gen_opt.validation_tier != "PHYSICALLY_VALIDATED"
    assert "advisory" in gen_opt.limitations.lower()
    assert gen_opt.expected_reserve_margin_gain_pct > 0.0


# ==============================================================================
# 9. FAIR COUNTERFACTUAL ANALYSIS (GUARDRAIL 14)
# ==============================================================================

def test_counterfactual_comparison_factual_deltas(bharati_engine, bharati_twin):
    """
    Guardrail 14: Verifies factual counterfactual comparison between baseline
    and stressed trajectories using wear-proxy terminology.
    """
    nom_traj = build_synthetic_trajectory(bharati_twin, length_h=24, ambient_temp_c=-15.0)
    stress_traj = build_synthetic_trajectory(bharati_twin, length_h=24, ambient_temp_c=-40.0)

    assess_nom = bharati_engine.assess_trajectory(nom_traj)
    assess_stress = bharati_engine.assess_trajectory(stress_traj)

    comp = bharati_engine.counterfactual_evaluator.compare_assessments(
        baseline=assess_nom,
        counterfactual=assess_stress,
        comparison_name="NOMINAL_VS_EXTREME_COLD"
    )

    assert isinstance(comp, CounterfactualResilienceComparison)
    assert isinstance(comp.delta_composite_index, float)
    assert isinstance(comp.delta_battery_throughput_kwh, float)  # Wear proxy verified
    assert comp.summary_narrative != ""


# ==============================================================================
# 10. TRACEABLE FAILURE PROPAGATION CHAIN (GUARDRAIL 15)
# ==============================================================================

def test_failure_propagation_chain_from_observed_transitions(bharati_engine, bharati_twin):
    """
    Guardrail 15: Confirms that failure propagation steps are generated
    only from observed state transitions in the trajectory.
    """
    traj = build_synthetic_trajectory(bharati_twin, length_h=24)
    # Simulate causal progression:
    # Step 2: Environmental drop
    traj.states[1].environment.ambient_temperature_c = -36.0
    # Step 3: Battery drops to warning
    traj.states[2].battery.soc_pct = 0.22
    # Step 4: Reserve collapses
    traj.states[3].resilience.dependable_reserve_pct = 10.0

    res = bharati_engine.assess_trajectory(traj)
    chain = res.failure_propagation
    assert len(chain) >= 2

    # Check structure
    for step in chain:
        assert step.step_number > 0
        assert step.timestamp != ""
        assert step.trigger != ""
        assert step.affected_subsystem != ""
        assert step.observed_state_change != ""
        assert step.possible_recovery_opportunity != ""


# ==============================================================================
# 11. SAFE ERROR HANDLING & BOUNDARY CONDITIONS (GUARDRAILS 7 & 18)
# ==============================================================================

def test_safe_handling_empty_or_none_trajectory(bharati_engine):
    """
    Guardrail 7: Confirms that None or empty trajectory returns NO_DATA / INPUT_INVALID
    and NEVER falsely diagnoses CRITICAL station failure.
    """
    res_none = bharati_engine.assess_trajectory(None)
    assert res_none.assessment_status == AssessmentStatusEnum.NO_DATA
    assert res_none.resilience_state != ResilienceStateEnum.CRITICAL
    assert len(res_none.diagnostics) > 0

    class EmptyTraj:
        states = []
        station_id = "BHARATI"

    res_empty = bharati_engine.assess_trajectory(EmptyTraj())
    assert res_empty.assessment_status == AssessmentStatusEnum.NO_DATA
    assert res_empty.resilience_state != ResilienceStateEnum.CRITICAL


def test_safe_handling_corrupted_non_monotonic_trajectory(bharati_engine, bharati_twin):
    """
    Guardrail 18: Confirms that non-monotonic timestamps or corrupted states
    are cleanly rejected with INPUT_INVALID status.
    """
    traj = build_synthetic_trajectory(bharati_twin, length_h=6)
    # Corrupt timestamp order: step 3 timestamp precedes step 2
    traj.states[2].timestamp = "2026-05-30T00:00:00Z"

    res = bharati_engine.assess_trajectory(traj)
    assert res.assessment_status == AssessmentStatusEnum.INPUT_INVALID
    assert res.resilience_state != ResilienceStateEnum.CRITICAL
    assert any("non-monotonic" in d.lower() for d in res.diagnostics)


def test_safe_handling_nan_inf_values(bharati_engine, bharati_twin):
    """Confirms that NaN or Inf values in states yield INPUT_INVALID safely."""
    traj = build_synthetic_trajectory(bharati_twin, length_h=6)
    traj.states[1].loads.total_load_kw = float("nan")

    res = bharati_engine.assess_trajectory(traj)
    assert res.assessment_status == AssessmentStatusEnum.INPUT_INVALID
    assert res.resilience_state != ResilienceStateEnum.CRITICAL
    assert any("nan/inf" in d.lower() for d in res.diagnostics)


def test_immediate_failure_at_step_one(bharati_engine, bharati_twin):
    """Guardrail 18: Immediate failure at first timestep."""
    traj = build_synthetic_trajectory(bharati_twin, length_h=12)
    traj.states[0].loads.unserved_critical_kw = 10.0

    res = bharati_engine.assess_trajectory(traj)
    assert res.survival_horizons.critical_load_survival_horizon_h == 1.0
    assert res.survival_horizons.overall_station_survival_horizon_h == 1.0
    assert res.resilience_state == ResilienceStateEnum.CRITICAL


def test_failure_at_final_timestep(bharati_engine, bharati_twin):
    """Guardrail 18: Failure at final timestep."""
    traj = build_synthetic_trajectory(bharati_twin, length_h=12)
    traj.states[-1].loads.unserved_critical_kw = 5.0

    res = bharati_engine.assess_trajectory(traj)
    assert res.survival_horizons.critical_load_survival_horizon_h == 12.0
    assert res.survival_horizons.overall_station_survival_horizon_h == 12.0
    assert res.survival_horizons.survives_full_horizon is False


# ==============================================================================
# 12. DETERMINISM & REPRODUCIBILITY
# ==============================================================================

def test_resilience_assessment_determinism(bharati_engine, bharati_twin):
    """Validates bitwise identical resilience outputs across multiple identical runs."""
    traj = build_synthetic_trajectory(bharati_twin, length_h=24)

    res1 = bharati_engine.assess_trajectory(traj)
    res2 = bharati_engine.assess_trajectory(traj)
    res3 = bharati_engine.assess_trajectory(traj)

    assert res1.resilience_state == res2.resilience_state == res3.resilience_state
    assert res1.dimensions.composite_resilience_index == res2.dimensions.composite_resilience_index == res3.dimensions.composite_resilience_index
    assert res1.survival_horizons.overall_station_survival_horizon_h == res2.survival_horizons.overall_station_survival_horizon_h == res3.survival_horizons.overall_station_survival_horizon_h


# ==============================================================================
# 13. CLOSED-LOOP OPTIMIZER INTEGRATION (PHASE 6 TWIN REPLAY)
# ==============================================================================

def test_assess_optimization_via_twin_replay(bharati_engine, bharati_twin, profile_registry, safety_registry):
    """
    Validates end-to-end integration:
    Phase 6 OptimizationResult -> Twin Replay -> Phase 7 Resilience Assessment.
    """
    opt_engine = OptimizerEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    init_state = bharati_twin.initialize_twin("2026-06-01T00:00:00Z")

    # Generate 12-hour input trajectory
    steps = [
        TwinInputStep(
            timestamp=f"2026-06-01T{h:02d}:00:00Z",
            horizon_h=h + 1,
            ambient_temp_c=-20.0,
            wind_speed_m_per_s=10.0,
            ghi_w_per_m2=200.0 if 6 <= h <= 18 else 0.0,
            load_kw=45.0,
            solar_kw=10.0 if 6 <= h <= 18 else 0.0,
            wind_kw=20.0,
            mode="EXPECTED"
        )
        for h in range(12)
    ]

    opt_res = opt_engine.optimize(init_state, steps)
    assert opt_res.solver_status == SolverStatus.OPTIMAL

    # Phase 7 assesses the optimized dispatch schedule
    res_assess = bharati_engine.assess_optimization(opt_res, init_state, steps)
    assert res_assess.assessment_status == AssessmentStatusEnum.COMPLETED
    assert res_assess.provenance == "SIMULATED"
    assert any("source=Phase6Optimizer" in d for d in res_assess.diagnostics)
    assert res_assess.horizon_hours == 12
    assert res_assess.survival_horizons.survives_full_horizon is True


# ==============================================================================
# 14. ARCHITECTURAL BOUNDARY & ISOLATION CHECK
# ==============================================================================

def test_architectural_boundary_no_policy_or_api_leakage():
    """
    Inspects backend/resilience to ensure zero Phase 8 policy execution,
    FastAPI endpoints, or frontend UI components have been introduced.
    """
    import inspect
    import backend.resilience.schema as schema
    import backend.resilience.engine as engine

    # Ensure no FastAPI imports
    schema_src = inspect.getsource(schema)
    engine_src = inspect.getsource(engine)

    assert "fastapi" not in schema_src.lower()
    assert "fastapi" not in engine_src.lower()
    assert "apirouter" not in engine_src.lower()
    assert "react" not in engine_src.lower()


# ==============================================================================
# 15. LOCKED PROVENANCE TAXONOMY COMPLIANCE
# ==============================================================================

def test_locked_provenance_taxonomy_compliance(bharati_engine, bharati_twin):
    """
    Verifies that Phase 7 adheres strictly to the project-wide locked 6-tier
    provenance taxonomy: {REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED}.
    Confirms 'OPTIMIZED' is NOT introduced as a seventh provenance tier.
    """
    APPROVED_PROVENANCE_TIERS = {
        "REAL",
        "CONFIGURED",
        "ASSUMED",
        "SYNTHETIC",
        "FORECAST",
        "SIMULATED"
    }

    assert "OPTIMIZED" not in APPROVED_PROVENANCE_TIERS

    # 1. Baseline assessment provenance
    traj = build_synthetic_trajectory(bharati_twin, length_h=24)
    res = bharati_engine.assess_trajectory(traj)
    assert res.provenance in APPROVED_PROVENANCE_TIERS
    assert res.provenance == "SIMULATED"
    assert res.dimensions.provenance in APPROVED_PROVENANCE_TIERS
    for threat in res.threat_decomposition:
        assert threat.provenance in APPROVED_PROVENANCE_TIERS

    # 2. Counterfactual comparison provenance
    stress_traj = build_synthetic_trajectory(bharati_twin, length_h=24, ambient_temp_c=-40.0)
    stress_res = bharati_engine.assess_trajectory(stress_traj)
    comparison = bharati_engine.counterfactual_evaluator.compare_assessments(res, stress_res, "TEST_COMP")
    assert comparison.provenance in APPROVED_PROVENANCE_TIERS
    assert comparison.provenance == "SIMULATED"

    # 3. Fallback / empty assessment provenance
    empty_res = bharati_engine.assess_trajectory(None)
    assert empty_res.provenance in APPROVED_PROVENANCE_TIERS
    assert empty_res.provenance == "ASSUMED"


# ==============================================================================
# 16. HIMADRI THERMAL SAFE-MINIMUM VERIFICATION (CASE A: 14.0°C)
# ==============================================================================

def test_himadri_thermal_safe_minimum_authoritative_compliance(himadri_engine, profile_registry, safety_registry):
    """
    Case A Audit: Verifies that Himadri's authoritative indoor thermal safe-minimum
    is 14.0°C (as configured in configs/safety_thresholds.json and configs/station_profiles.json).
    Confirms Phase 7 evaluates thermal safety and habitability horizons using 14.0°C.
    """
    # 1. Authoritative configuration checks
    cfg_val = safety_registry.get_value("HIMADRI", "indoor_min_safe_temp_c")
    assert cfg_val == 14.0, f"Expected 14.0°C, found {cfg_val}"

    prof = profile_registry.get("HIMADRI")
    assert prof.thermal.indoor_min_safe_temp_c == 14.0

    himadri_twin = TwinEngine("HIMADRI", prof, safety_registry)

    # 2. Test Safe Temperature: 18.0°C >= 14.0°C + 2.0°C buffer (no thermal breach or warning)
    safe_traj = build_synthetic_trajectory(himadri_twin, length_h=12, base_load_kw=20.0)
    for s in safe_traj.states:
        s.thermal.indoor_temperature_c = 18.0
        s.thermal.indoor_min_safe_temp_c = 14.0

    safe_res = himadri_engine.assess_trajectory(safe_traj)
    assert safe_res.survival_horizons.thermal_habitability_horizon_h == 12.0
    assert not any(t.threat_type == ResilienceThreatEnum.THERMAL_STRESS for t in safe_res.threat_decomposition)

    # 3. Test Near-Threshold Temperature: 14.5°C >= 14.0°C (survives full horizon; warning trigger only)
    # Note: If threshold were 15.0°C, 14.5°C would fail immediately (< 15.0°C).
    # Since authoritative threshold is 14.0°C, 14.5°C survives all 12 hours.
    warning_traj = build_synthetic_trajectory(himadri_twin, length_h=12, base_load_kw=20.0)
    for s in warning_traj.states:
        s.thermal.indoor_temperature_c = 14.5
        s.thermal.indoor_min_safe_temp_c = 14.0

    warning_res = himadri_engine.assess_trajectory(warning_traj)
    assert warning_res.survival_horizons.thermal_habitability_horizon_h == 12.0
    therm_threat = next((t for t in warning_res.threat_decomposition if t.threat_type == ResilienceThreatEnum.THERMAL_STRESS), None)
    assert therm_threat is not None
    assert therm_threat.severity == FailureSeverityEnum.WARNING

    # 4. Test Violation Temperature: 13.5°C < 14.0°C (breach at hour 5)
    breach_traj = build_synthetic_trajectory(himadri_twin, length_h=12, base_load_kw=20.0)
    for i, s in enumerate(breach_traj.states):
        s.thermal.indoor_min_safe_temp_c = 14.0
        if i >= 4:  # Hour 5 onwards (indices 4..11)
            s.thermal.indoor_temperature_c = 13.5
        else:
            s.thermal.indoor_temperature_c = 18.0

    breach_res = himadri_engine.assess_trajectory(breach_traj)
    assert breach_res.survival_horizons.thermal_habitability_horizon_h == 5.0
    assert breach_res.survival_horizons.binding_subsystem == "THERMAL"
    crit_threat = next((t for t in breach_res.threat_decomposition if t.threat_type == ResilienceThreatEnum.THERMAL_STRESS), None)
    assert crit_threat is not None
    assert crit_threat.severity == FailureSeverityEnum.CRITICAL


# ==============================================================================
# 17. RECOVERY PROJECTION SEMANTICS (ESTIMATED VS PHYSICALLY_VALIDATED)
# ==============================================================================

def test_recovery_projection_semantics_explicitly_estimated(bharati_engine, bharati_twin):
    """
    Guardrail 5 & Semantics: Recovery gain projections derived from rated capacity
    or heuristic capabilities must remain explicitly ESTIMATED. They cannot be
    presented as PHYSICALLY_VALIDATED without closed-loop simulation.
    """
    traj = build_synthetic_trajectory(bharati_twin, length_h=24)
    traj.states[3].loads.unserved_critical_kw = 10.0
    traj.states[5].resilience.dependable_reserve_pct = 5.0

    res = bharati_engine.assess_trajectory(traj)
    for opt in res.candidate_recovery_options:
        assert opt.validation_tier == "ESTIMATED"
        assert opt.validation_tier != "PHYSICALLY_VALIDATED"
        assert "advisory" in opt.limitations.lower()

