"""
POLARIS-EMS — Automated Test Suite: Phase 8 Policy Engine
SIH26061: Polar Energy Management & Resilience System

Exhaustive verification of the Phase 8 Policy Engine:
1. Deterministic state policy mapping (SAFE, WATCH, AT_RISK, THREATENED, CRITICAL, RECOVERY)
2. Critical life-safety & load protection policies
3. Reserve erosion, fleet contingency, and generator physical safety hierarchy
4. Thermal protection & habitability preservation
5. Fuel preservation & resupply gap logistics bridging
6. Storage protection & SOC cutoff throttling
7. Multi-policy composition, priority ordering, and conflict suppression
8. Explicit stateful hysteresis & anti-churn deadbands
9. Multi-station dynamic configuration (Bharati 3x80kW, Maitri 3x62.5kW, Himadri 2x45kW)
10. Multi-horizon coverage (48h operational vs 168h strategic)
11. Invalid upstream input handling (graceful degradation, zero hallucinations)
12. Phase 6 optimizer handoff with explicit 4-tier enforcement classification
13. Closed-loop counterfactual validation (PHYSICALLY_VALIDATED vs ESTIMATED)
14. Complete decision explainability & audit traceability
15. Locked 6-tier provenance compliance (SIMULATED / CONFIGURED, zero 7th tier)
16. Architectural isolation (zero FastAPI, UI, or direct device actuation code)
"""

import pytest
from pathlib import Path
from datetime import datetime
import numpy as np

from backend.data.station_profiles.loader import StationProfileRegistry, StationProfile
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.twin_engine import TwinEngine, TwinTrajectory
from backend.twin.forecast_adapter import TwinInputStep
from backend.twin.state import TwinState
from backend.scenarios.registry import ScenarioRegistry
from backend.optimizer.schema import OptimizationMode, SolverStatus
from backend.optimizer.engine import OptimizerEngine
from backend.resilience.engine import ResilienceEngine
from backend.resilience.schema import (
    ResilienceAssessment,
    ResilienceStateEnum,
    AssessmentStatusEnum,
    SurvivalHorizons,
    ThreatIndicator,
    TimeToThreat,
    FailureSeverityEnum,
    ResilienceThreatEnum
)

from backend.policy.engine import PolicyEngine
from backend.policy.schema import (
    PolicyStateEnum,
    PolicyCategoryEnum,
    PolicyPriorityEnum,
    PolicyActionEnum,
    PolicyValidationStatusEnum,
    HandoffEnforcementTierEnum,
    HysteresisState,
    PolicyDecisionTrace
)
from backend.policy.hysteresis import HysteresisController


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
def bharati_policy(profile_registry, safety_registry):
    return PolicyEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)


@pytest.fixture
def maitri_policy(profile_registry, safety_registry):
    return PolicyEngine("MAITRI", profile_registry.get("MAITRI"), safety_registry)


@pytest.fixture
def himadri_policy(profile_registry, safety_registry):
    return PolicyEngine("HIMADRI", profile_registry.get("HIMADRI"), safety_registry)


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
    """Builds an authoritative TwinTrajectory via the Phase 4 Digital Twin."""
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
# 1. DETERMINISTIC STATE POLICY MAPPING
# ==============================================================================

def test_state_policy_mapping_exhaustive(bharati_policy, profile_registry, safety_registry):
    """
    Guardrail 4: Every Phase 7 resilience state produces explicit deterministic policy behavior:
    SAFE -> NO_ACTION / MONITOR
    WATCH -> MONITOR
    AT_RISK -> PREPARE
    THREATENED -> PROTECT
    CRITICAL -> PROTECT
    RECOVERY -> RECOVER
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    resilience_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    # 1. SAFE
    traj_safe = build_synthetic_trajectory(twin, length_h=24, base_load_kw=30.0)
    assess_safe = resilience_eng.assess_trajectory(traj_safe)
    trace_safe, _ = bharati_policy.evaluate_policy(assess_safe, traj_safe.states[0])
    assert trace_safe.resilience_state == ResilienceStateEnum.SAFE
    assert trace_safe.policy_state in (PolicyStateEnum.NO_ACTION, PolicyStateEnum.MONITOR)

    # 2. WATCH (mild ambient cold)
    traj_watch = build_synthetic_trajectory(twin, length_h=24, ambient_temp_c=-26.0)
    assess_watch = resilience_eng.assess_trajectory(traj_watch)
    trace_watch, _ = bharati_policy.evaluate_policy(assess_watch, traj_watch.states[0])
    assert trace_watch.resilience_state == ResilienceStateEnum.WATCH
    assert trace_watch.policy_state in (PolicyStateEnum.MONITOR, PolicyStateEnum.PREPARE)

    # 3. AT_RISK (low battery SOC)
    traj_risk = build_synthetic_trajectory(twin, length_h=24)
    traj_risk.states[0].battery.soc_pct = 0.24  # <= 25%
    assess_risk = resilience_eng.assess_trajectory(traj_risk)
    trace_risk, _ = bharati_policy.evaluate_policy(assess_risk, traj_risk.states[0])
    assert trace_risk.policy_state in (PolicyStateEnum.PREPARE, PolicyStateEnum.MITIGATE)

    # 4. THREATENED (reserve below 15%)
    traj_threat = build_synthetic_trajectory(twin, length_h=24)
    traj_threat.states[0].resilience.dependable_reserve_pct = 12.0
    assess_threat = resilience_eng.assess_trajectory(traj_threat)
    trace_threat, _ = bharati_policy.evaluate_policy(assess_threat, traj_threat.states[0])
    assert trace_threat.policy_state == PolicyStateEnum.PROTECT

    # 5. CRITICAL (unserved critical load)
    traj_crit = build_synthetic_trajectory(twin, length_h=24)
    traj_crit.states[0].loads.unserved_critical_kw = 5.0
    assess_crit = resilience_eng.assess_trajectory(traj_crit)
    trace_crit, _ = bharati_policy.evaluate_policy(assess_crit, traj_crit.states[0])
    assert trace_crit.policy_state == PolicyStateEnum.PROTECT
    assert trace_crit.primary_policy.action == PolicyActionEnum.PRESERVE_CRITICAL_LOADS

    # 6. RECOVERY
    traj_rec = build_synthetic_trajectory(twin, length_h=24)
    assess_rec = resilience_eng.assess_trajectory(traj_rec, previous_state=ResilienceStateEnum.CRITICAL)
    trace_rec, _ = bharati_policy.evaluate_policy(assess_rec, traj_rec.states[0])
    assert trace_rec.resilience_state == ResilienceStateEnum.RECOVERY
    assert trace_rec.policy_state == PolicyStateEnum.RECOVER
    assert trace_rec.primary_policy.action == PolicyActionEnum.ADOPT_STATION_RECOVERY_POSTURE


# ==============================================================================
# 2. CRITICAL LIFE-SAFETY & THERMAL POLICIES
# ==============================================================================

def test_critical_life_safety_dominance(bharati_policy, profile_registry, safety_registry):
    """
    Validates that unserved critical load or thermal freezing breaches trigger P1
    life-safety policies that take absolute precedence over monitoring.
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    traj = build_synthetic_trajectory(twin, length_h=24)
    traj.states[0].loads.unserved_critical_kw = 12.0
    traj.states[0].thermal.indoor_temperature_c = 10.0  # < 12.0 safe minimum for Bharati

    assess = res_eng.assess_trajectory(traj)
    trace, _ = bharati_policy.evaluate_policy(assess, traj.states[0])

    assert trace.primary_policy is not None
    assert trace.primary_policy.priority == PolicyPriorityEnum.P1_CRITICAL_LIFE_SAFETY
    assert trace.policy_state == PolicyStateEnum.PROTECT
    assert len(trace.active_policies) >= 2


# ==============================================================================
# 3. GENERATOR PHYSICAL SAFETY & AVAILABILITY HIERARCHY
# ==============================================================================

def test_generator_safety_never_forces_faulted_unit_online(bharati_policy, profile_registry, safety_registry):
    """
    Guardrail 5: Physical availability -> Twin constraints -> Phase 6 optimizer -> Phase 8 policy.
    A policy may request preparation of a healthy standby unit.
    It can NEVER force a faulted, maintenance, or prohibited unit online.
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    traj = build_synthetic_trajectory(twin, length_h=24)
    traj.states[0].resilience.dependable_reserve_pct = 10.0  # triggers PREPARE_STANDBY_GENERATOR

    # Case A: Unit 1 is online, Unit 2 is faulted, Unit 3 is healthy standby
    overrides_a = {1: "ONLINE", 2: "FAULT"}
    assess = res_eng.assess_trajectory(traj)
    trace_a, _ = bharati_policy.evaluate_policy(
        assess, traj.states[0], generator_overrides=overrides_a
    )
    handoff_a = trace_a.optimizer_handoff
    assert handoff_a.generator_overrides[2] == "FAULT"
    # Unit 3 should be chosen for preparation, NOT faulted Unit 2
    assert handoff_a.generator_overrides.get(3) == "ONLINE"

    # Case B: All offline units are faulted or in maintenance (Units 2 & 3 unavailable)
    overrides_b = {2: "FAULT", 3: "MAINTENANCE"}
    trace_b, _ = bharati_policy.evaluate_policy(
        assess, traj.states[0], generator_overrides=overrides_b
    )
    handoff_b = trace_b.optimizer_handoff
    assert handoff_b.generator_overrides[2] == "FAULT"
    assert handoff_b.generator_overrides[3] == "MAINTENANCE"
    # Cannot force unit 2 or 3 online!
    assert "ONLINE" not in [handoff_b.generator_overrides.get(2), handoff_b.generator_overrides.get(3)]


# ==============================================================================
# 4. EXPLICIT STATEFUL HYSTERESIS & ANTI-CHURN
# ==============================================================================

def test_explicit_stateful_hysteresis_deadband(bharati_policy, profile_registry, safety_registry):
    """
    Guardrail 2 & 12: Verifies that deadbands prevent policy churn across boundary crossings.
    Activation at <= 15%, deactivation at >= 20%.
    Evaluates:
    - Step 1: Reserve drops to 14.0% -> Triggers PROTECT
    - Step 2: Reserve micro-jitter rises to 17.0% (between 15% and 20%) -> REMAINS PROTECT!
    - Step 3: Reserve recovers to 22.0% (>= 20%) -> Deactivates to nominal!
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    traj = build_synthetic_trajectory(twin, length_h=24)

    # Step 1: 14.0% reserve
    traj.states[0].resilience.dependable_reserve_pct = 14.0
    assess1 = res_eng.assess_trajectory(traj)
    trace1, hyst1 = bharati_policy.evaluate_policy(assess1, traj.states[0], previous_hysteresis=None)
    assert trace1.primary_policy.action == PolicyActionEnum.PREPARE_STANDBY_GENERATOR
    assert hyst1.active_policy_states.get("dependable_reserve_critical") == "ACTIVE"

    # Step 2: 17.0% reserve (in deadband)
    traj.states[0].resilience.dependable_reserve_pct = 17.0
    assess2 = res_eng.assess_trajectory(traj)
    trace2, hyst2 = bharati_policy.evaluate_policy(assess2, traj.states[0], previous_hysteresis=hyst1)
    # Stays active because 17.0% < 20.0% deactivation threshold!
    assert trace2.primary_policy.action == PolicyActionEnum.PREPARE_STANDBY_GENERATOR
    assert hyst2.active_policy_states.get("dependable_reserve_critical") == "ACTIVE"

    # Step 3: 22.0% reserve (recovers past deactivation threshold)
    traj.states[0].resilience.dependable_reserve_pct = 22.0
    assess3 = res_eng.assess_trajectory(traj)
    trace3, hyst3 = bharati_policy.evaluate_policy(assess3, traj.states[0], previous_hysteresis=hyst2)
    # Deactivates!
    assert trace3.primary_policy.action != PolicyActionEnum.PREPARE_STANDBY_GENERATOR
    assert hyst3.active_policy_states.get("dependable_reserve_critical") == "INACTIVE"


# ==============================================================================
# 5. CROSS-STATION DYNAMIC THRESHOLDS (BHARATI, MAITRI, HIMADRI)
# ==============================================================================

def test_cross_station_dynamic_thresholds(
    bharati_policy, maitri_policy, himadri_policy, profile_registry, safety_registry
):
    """
    Guardrail 7: Asserts dynamic configuration without hardcoded station constants:
    Bharati: 240kW, 25k L, 12°C
    Maitri: 187.5kW, 15k L, 10°C
    Himadri: 90kW, 10k L, 14°C
    """
    twin_b = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    twin_m = TwinEngine("MAITRI", profile_registry.get("MAITRI"), safety_registry)
    twin_h = TwinEngine("HIMADRI", profile_registry.get("HIMADRI"), safety_registry)

    res_b = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_m = ResilienceEngine("MAITRI", profile_registry.get("MAITRI"), safety_registry)
    res_h = ResilienceEngine("HIMADRI", profile_registry.get("HIMADRI"), safety_registry)

    # Fuel test at 12,000 Liters:
    # Safe at Himadri (> 10,000 L)
    # Critical breach at Maitri (<= 15,000 L) and Bharati (<= 25,000 L)
    traj_h = build_synthetic_trajectory(twin_h, length_h=24)
    traj_h.states[0].fuel.fuel_remaining_l = 12000.0
    assess_h = res_h.assess_trajectory(traj_h)
    trace_h, _ = himadri_policy.evaluate_policy(assess_h, traj_h.states[0])
    # Not fuel emergency for Himadri
    assert not any(p.action == PolicyActionEnum.PRESERVE_EMERGENCY_FUEL for p in trace_h.active_policies)

    traj_m = build_synthetic_trajectory(twin_m, length_h=24)
    traj_m.states[0].fuel.fuel_remaining_l = 12000.0
    assess_m = res_m.assess_trajectory(traj_m)
    trace_m, _ = maitri_policy.evaluate_policy(assess_m, traj_m.states[0])
    # IS fuel emergency for Maitri (<= 15,000 L)
    assert any(p.action == PolicyActionEnum.PRESERVE_EMERGENCY_FUEL for p in trace_m.active_policies)


# ==============================================================================
# 6. MULTI-HORIZON COVERAGE (48H OPERATIONAL VS 168H STRATEGIC)
# ==============================================================================

def test_multi_horizon_strategic_resupply_policy(bharati_policy, profile_registry, safety_registry):
    """
    Verifies horizon sensitivity: station may be SAFE over 48h but requires
    CONSERVE_FUEL_UNTIL_RESUPPLY over 168h due to resupply gap vulnerability.
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    # 48h trajectory
    traj_48 = build_synthetic_trajectory(twin, length_h=48)
    assess_48 = res_eng.assess_trajectory(traj_48)
    trace_48, _ = bharati_policy.evaluate_policy(assess_48, traj_48.states[0])
    assert trace_48.horizon_hours == 48

    # 168h trajectory with resupply gap
    traj_168 = build_synthetic_trajectory(twin, length_h=168)
    assess_168 = res_eng.assess_trajectory(traj_168)
    # Inject resupply gap limit
    assess_168.survival_horizons.resupply_gap_survivability_h = 120.0  # < 168h
    assess_168.survival_horizons.binding_subsystem = "RESUPPLY"

    trace_168, _ = bharati_policy.evaluate_policy(assess_168, traj_168.states[0])
    assert trace_168.horizon_hours == 168
    assert any(p.action == PolicyActionEnum.CONSERVE_FUEL_UNTIL_RESUPPLY for p in trace_168.active_policies)


# ==============================================================================
# 7. INVALID UPSTREAM INPUT SAFETY (GUARDRAIL 11)
# ==============================================================================

def test_invalid_upstream_input_graceful_handling(bharati_policy):
    """
    Guardrail 11: When Phase 7 input is None, corrupt, or invalid, returns structured
    INVALID_INPUT / UPSTREAM_INVALID with zero invented policies.
    """
    # 1. Assessment is None
    trace1, _ = bharati_policy.evaluate_policy(None, None)
    assert trace1.policy_state == PolicyStateEnum.INVALID_INPUT
    assert trace1.validation_status == PolicyValidationStatusEnum.UPSTREAM_INVALID
    assert len(trace1.active_policies) == 0

    # 2. Corrupted assessment status
    corrupt_assess = ResilienceAssessment(
        station_id="BHARATI",
        assessment_timestamp="2026-06-01T00:00:00Z",
        horizon_hours=24,
        assessment_status=AssessmentStatusEnum.INPUT_INVALID,
        resilience_state=ResilienceStateEnum.SAFE,
        active_threat_states=[],
        survival_horizons=None,
        time_to_threat=TimeToThreat(),
        threat_decomposition=[]
    )
    trace2, _ = bharati_policy.evaluate_policy(corrupt_assess, None)
    assert trace2.policy_state == PolicyStateEnum.INVALID_INPUT
    assert trace2.validation_status == PolicyValidationStatusEnum.UPSTREAM_INVALID


# ==============================================================================
# 8. PHASE 6 OPTIMIZER HANDOFF WITH 4-TIER ENFORCEMENT CLASSIFICATION
# ==============================================================================

def test_optimizer_handoff_four_tier_classification(bharati_policy, profile_registry, safety_registry):
    """
    Final Handoff Clarification: Proves that every handoff requirement is classified into:
    - DIRECTLY_SUPPORTED
    - DERIVED_FROM_SUPPORTED_INPUT
    - DECLARATIVE_ONLY
    - REQUIRES_OPTIMIZATION
    and distinguishes requested from optimizer-enforced constraints.
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    traj = build_synthetic_trajectory(twin, length_h=24)
    traj.states[0].loads.unserved_critical_kw = 5.0
    traj.states[0].resilience.dependable_reserve_pct = 12.0
    traj.states[0].battery.soc_pct = 0.22

    assess = res_eng.assess_trajectory(traj)
    trace, _ = bharati_policy.evaluate_policy(assess, traj.states[0])

    handoff = trace.optimizer_handoff
    assert handoff is not None

    tiers = handoff.enforcement_tiers
    # Mode is directly supported
    assert tiers["recommended_mode"] == HandoffEnforcementTierEnum.DIRECTLY_SUPPORTED.value
    assert handoff.recommended_mode == OptimizationMode.CONSERVATIVE

    # Generator overrides directly supported
    if handoff.generator_overrides:
        assert tiers["generator_overrides"] == HandoffEnforcementTierEnum.DIRECTLY_SUPPORTED.value

    # Derived from supported input (mode=CONSERVATIVE derives elevated reserve margin)
    assert tiers["min_operating_reserve_pct"] == HandoffEnforcementTierEnum.DERIVED_FROM_SUPPORTED_INPUT.value

    # Declarative targets (not directly enforced as Pyomo constraints)
    assert tiers["min_terminal_soc_pct"] == HandoffEnforcementTierEnum.DECLARATIVE_ONLY.value
    assert tiers["shed_noncritical_load_allowed"] == HandoffEnforcementTierEnum.DECLARATIVE_ONLY.value

    # Distinct separation
    assert len(handoff.requested_constraints) > 0
    assert len(handoff.optimizer_enforced_constraints) > 0


# ==============================================================================
# 9. CLOSED-LOOP REPLAY & COUNTERFACTUAL (PHYSICALLY_VALIDATED)
# ==============================================================================

def test_closed_loop_handoff_and_physically_validated_counterfactual(
    bharati_policy, profile_registry, safety_registry
):
    """
    Guardrail 8: Closed-loop handoff executes:
    Policy Requirements -> Phase 6 Optimizer -> Phase 4 Twin Replay -> Phase 7 Reassessment
    and awards PHYSICALLY_VALIDATED status only after the full loop completes.
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    # 12-hour test for rapid execution
    init_state = twin.initialize_twin("2026-06-01T00:00:00Z")
    steps = [
        TwinInputStep(
            timestamp=f"2026-06-01T{h:02d}:00:00Z",
            horizon_h=h + 1,
            ambient_temp_c=-25.0,
            wind_speed_m_per_s=12.0,
            ghi_w_per_m2=250.0 if 6 <= h <= 18 else 0.0,
            load_kw=45.0,
            solar_kw=10.0 if 6 <= h <= 18 else 0.0,
            wind_kw=20.0,
            mode="EXPECTED"
        )
        for h in range(12)
    ]
    traj = twin.simulate(init_state, steps)
    assess = res_eng.assess_trajectory(traj)

    trace, _ = bharati_policy.evaluate_policy(assess, traj.states[0])

    # Execute closed loop
    opt_res, post_assess = bharati_policy.execute_optimizer_handoff(
        policy_trace=trace,
        initial_state=init_state,
        trajectory=steps
    )

    assert opt_res.solver_status == SolverStatus.OPTIMAL
    assert post_assess.assessment_status == AssessmentStatusEnum.COMPLETED

    outcomes = trace.optimizer_handoff.post_replay_validated_outcomes
    assert outcomes["validation_tier"] == "PHYSICALLY_VALIDATED"
    assert "overall_survival_horizon_h" in outcomes
    assert "min_reserve_margin_pct" in outcomes


# ==============================================================================
# 10. DECISION TRACEABILITY & EXPLAINABILITY
# ==============================================================================

def test_decision_trace_full_transparency(bharati_policy, profile_registry, safety_registry):
    """
    Guardrail 10: Asserts that every field of PolicyDecisionTrace is populated,
    with transparent conditions met, thresholds used, and priority lineage.
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    traj = build_synthetic_trajectory(twin, length_h=24)
    traj.states[0].thermal.indoor_temperature_c = 13.5  # near threshold
    traj.states[0].resilience.dependable_reserve_pct = 12.0

    assess = res_eng.assess_trajectory(traj)
    trace, _ = bharati_policy.evaluate_policy(assess, traj.states[0])

    d = trace.to_dict()
    assert d["policy_run_id"].startswith("pol-")
    assert d["station_id"] == "BHARATI"
    assert d["policy_state"] == "PROTECT"
    assert d["primary_policy"] is not None
    assert len(d["evaluation_trace"]) > 0
    assert d["provenance"] == "SIMULATED"
    assert d["source_phase"] == "Phase7"


# ==============================================================================
# 11. LOCKED 6-TIER PROVENANCE TAXONOMY COMPLIANCE
# ==============================================================================

def test_locked_provenance_taxonomy_compliance(bharati_policy, profile_registry, safety_registry):
    """
    Guardrail 3: Verifies that Phase 8 strictly adheres to the frozen 6-tier taxonomy:
    {REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED}.
    Confirms zero 7th tier (no POLICY, OPTIMIZED, DERIVED).
    """
    APPROVED_TIERS = {"REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"}

    assert "POLICY" not in APPROVED_TIERS
    assert "OPTIMIZED" not in APPROVED_TIERS
    assert "DERIVED" not in APPROVED_TIERS

    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    traj = build_synthetic_trajectory(twin, length_h=24)
    assess = res_eng.assess_trajectory(traj)
    trace, _ = bharati_policy.evaluate_policy(assess, traj.states[0])

    assert trace.provenance in APPROVED_TIERS
    assert trace.provenance == "SIMULATED"
    if trace.primary_policy:
        assert trace.primary_policy.provenance in APPROVED_TIERS


# ==============================================================================
# 12. ARCHITECTURAL ISOLATION & ZERO POLICY EXECUTION LEAKAGE
# ==============================================================================

def test_architectural_isolation_no_device_or_api_leakage():
    """
    Guardrail 15: Confirms zero FastAPI endpoints, React components, ESP32,
    or PLC device actuator control in backend/policy.
    """
    import inspect
    import backend.policy.schema as schema
    import backend.policy.engine as engine
    import backend.policy.priority as priority

    for mod in [schema, engine, priority]:
        src = inspect.getsource(mod).lower()
        assert "fastapi" not in src
        assert "apirouter" not in src
        assert "react" not in src
        assert "esp32" not in src
        assert "plc" not in src
        assert "modbus" not in src
        assert "scada" not in src


# ==============================================================================
# 13. GENERATOR AVAILABILITY PERMUTATIONS EXHAUSTIVE
# ==============================================================================

def test_generator_availability_permutations_exhaustive(bharati_policy, profile_registry, safety_registry):
    """
    Guardrail 5: Tests all generator contingency permutations:
    - All healthy (Unit 1 online, Unit 2 available -> commits Unit 2)
    - One faulted (Unit 2 FAULT -> commits Unit 3)
    - One maintenance (Unit 2 MAINTENANCE -> commits Unit 3)
    - Multiple unavailable (Units 2 FAULT, 3 MAINTENANCE -> zero units forced)
    - Only one healthy generator (Units 2 & 3 FAULT -> alerts without forcing prohibited units)
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    traj = build_synthetic_trajectory(twin, length_h=24)
    traj.states[0].resilience.dependable_reserve_pct = 10.0
    assess = res_eng.assess_trajectory(traj)

    # 1. All healthy
    t1, _ = bharati_policy.evaluate_policy(assess, traj.states[0], generator_overrides={1: "ONLINE"})
    assert t1.optimizer_handoff.generator_overrides.get(2) == "ONLINE"

    # 2. One faulted
    t2, _ = bharati_policy.evaluate_policy(assess, traj.states[0], generator_overrides={1: "ONLINE", 2: "FAULT"})
    assert t2.optimizer_handoff.generator_overrides.get(3) == "ONLINE"
    assert t2.optimizer_handoff.generator_overrides.get(2) == "FAULT"

    # 3. One maintenance
    t3, _ = bharati_policy.evaluate_policy(assess, traj.states[0], generator_overrides={1: "ONLINE", 2: "MAINTENANCE"})
    assert t3.optimizer_handoff.generator_overrides.get(3) == "ONLINE"
    assert t3.optimizer_handoff.generator_overrides.get(2) == "MAINTENANCE"

    # 4. Multiple unavailable
    t4, _ = bharati_policy.evaluate_policy(assess, traj.states[0], generator_overrides={1: "ONLINE", 2: "FAULT", 3: "MAINTENANCE"})
    assert t4.optimizer_handoff.generator_overrides.get(2) == "FAULT"
    assert t4.optimizer_handoff.generator_overrides.get(3) == "MAINTENANCE"

    # 5. Only one healthy generator
    t5, _ = bharati_policy.evaluate_policy(assess, traj.states[0], generator_overrides={1: "ONLINE", 2: "FAULT", 3: "FAULT"})
    assert t5.optimizer_handoff.generator_overrides.get(2) == "FAULT"
    assert t5.optimizer_handoff.generator_overrides.get(3) == "FAULT"


# ==============================================================================
# 14. HYSTERESIS OSCILLATION, PROLONGED CONDITIONS & RESET
# ==============================================================================

def test_hysteresis_oscillations_prolonged_and_reset(bharati_policy, profile_registry, safety_registry):
    """
    Guardrail 12: Tests activation threshold, one-step jitter, repeated crossing,
    prolonged conditions, and reset after complete recovery.
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    traj = build_synthetic_trajectory(twin, length_h=24)

    hyst: Optional[HysteresisState] = None

    # Step 1: Activation at 14.0%
    traj.states[0].resilience.dependable_reserve_pct = 14.0
    a1 = res_eng.assess_trajectory(traj)
    t1, hyst = bharati_policy.evaluate_policy(a1, traj.states[0], previous_hysteresis=hyst)
    assert hyst.active_policy_states.get("dependable_reserve_critical") == "ACTIVE"
    assert hyst.consecutive_steps.get("dependable_reserve_critical") == 1

    # Step 2: Prolonged condition (remains at 13.0%)
    traj.states[0].resilience.dependable_reserve_pct = 13.0
    a2 = res_eng.assess_trajectory(traj)
    t2, hyst = bharati_policy.evaluate_policy(a2, traj.states[0], previous_hysteresis=hyst)
    assert hyst.active_policy_states.get("dependable_reserve_critical") == "ACTIVE"
    assert hyst.consecutive_steps.get("dependable_reserve_critical") == 2

    # Step 3: Upward jitter to 18.0% (within deadband < 20%) -> remains ACTIVE
    traj.states[0].resilience.dependable_reserve_pct = 18.0
    a3 = res_eng.assess_trajectory(traj)
    t3, hyst = bharati_policy.evaluate_policy(a3, traj.states[0], previous_hysteresis=hyst)
    assert hyst.active_policy_states.get("dependable_reserve_critical") == "ACTIVE"
    assert hyst.consecutive_steps.get("dependable_reserve_critical") == 3

    # Step 4: Full recovery past 20.0% -> deactivates to INACTIVE and resets counter
    traj.states[0].resilience.dependable_reserve_pct = 25.0
    a4 = res_eng.assess_trajectory(traj)
    t4, hyst = bharati_policy.evaluate_policy(a4, traj.states[0], previous_hysteresis=hyst)
    assert hyst.active_policy_states.get("dependable_reserve_critical") == "INACTIVE"
    assert hyst.consecutive_steps.get("dependable_reserve_critical") == 0


# ==============================================================================
# 15. CANONICAL SCENARIOS POLICY RESPONSE EXHAUSTIVE
# ==============================================================================

@pytest.mark.parametrize("scenario_id", [
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
def test_canonical_scenarios_policy_response_exhaustive(
    bharati_policy, profile_registry, safety_registry, scenario_registry, scenario_id
):
    """
    Guardrail 13: Verifies that every canonical Phase 5 scenario generates a valid,
    deterministic, explainable policy decision with appropriate governance posture.
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    scen = scenario_registry.get(scenario_id)
    traj = build_synthetic_trajectory(twin, length_h=24)

    # Ingest scenario context into resilience and policy engines
    assess = res_eng.assess_trajectory(traj, scenario=scen)
    trace, _ = bharati_policy.evaluate_policy(assess, traj.states[0], scenario=scen)

    assert trace.policy_state in (
        PolicyStateEnum.NO_ACTION,
        PolicyStateEnum.MONITOR,
        PolicyStateEnum.PREPARE,
        PolicyStateEnum.MITIGATE,
        PolicyStateEnum.PROTECT,
        PolicyStateEnum.RECOVER,
        PolicyStateEnum.ESCALATE,
        PolicyStateEnum.BLOCKED
    )
    assert trace.validation_status in (
        PolicyValidationStatusEnum.VALID,
        PolicyValidationStatusEnum.APPROVED,
        PolicyValidationStatusEnum.BLOCKED,
        PolicyValidationStatusEnum.ADVISORY,
        PolicyValidationStatusEnum.REQUIRES_OPTIMIZATION
    )
    assert trace.provenance == "SIMULATED"
    assert len(trace.evaluation_trace) > 0


# ==============================================================================
# 16. EXPLICIT FOUR-TIER HANDOFF & REQUIRES_OPTIMIZATION VERIFICATION
# ==============================================================================

def test_handoff_four_tiers_explicit_requires_optimization(bharati_policy, profile_registry, safety_registry):
    """
    Phase 8 Freeze Audit Item 1:
    Explicitly test all four handoff enforcement tiers:
    - DIRECTLY_SUPPORTED
    - DERIVED_FROM_SUPPORTED_INPUT
    - DECLARATIVE_ONLY
    - REQUIRES_OPTIMIZATION
    
    Verifies:
    * enforcement_tier == REQUIRES_OPTIMIZATION for legitimate policy requirement
      that cannot be enforced through frozen Phase 6 interface (e.g. min_terminal_fuel_liters).
    * requested requirement is preserved in requested_constraints.
    * NOT falsely inserted into optimizer_enforced_constraints.
    * Phase 6 remains unchanged.
    * No false VALID / APPROVED claim is produced (handoff_status is REQUIRES_OPTIMIZATION).
    * Diagnostic clearly explains why optimization/re-solve is required.
    * Supported requirement produces DIRECTLY_SUPPORTED.
    * Mode-derived requirement produces DERIVED_FROM_SUPPORTED_INPUT.
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    traj = build_synthetic_trajectory(twin, length_h=24)
    # Trigger fuel emergency preservation: fuel remaining <= emergency reserve (25,000 L for Bharati)
    traj.states[0].fuel.fuel_remaining_l = 22000.0
    traj.states[0].resilience.dependable_reserve_pct = 12.0  # triggers reserve protection (mode=CONSERVATIVE)

    assess = res_eng.assess_trajectory(traj)
    trace, _ = bharati_policy.evaluate_policy(
        assess, traj.states[0], generator_overrides={1: "ONLINE", 2: "ONLINE"}
    )

    handoff = trace.optimizer_handoff
    assert handoff is not None

    # 1. Verify REQUIRES_OPTIMIZATION
    assert "min_terminal_fuel_liters" in handoff.enforcement_tiers
    assert handoff.enforcement_tiers["min_terminal_fuel_liters"] == HandoffEnforcementTierEnum.REQUIRES_OPTIMIZATION.value

    # 2. Verify preserved in requested_constraints
    assert "min_terminal_fuel_liters" in handoff.requested_constraints
    assert handoff.requested_constraints["min_terminal_fuel_liters"] == 25000.0

    # 3. Verify NOT falsely inserted into optimizer_enforced_constraints
    assert "min_terminal_fuel_liters" not in handoff.optimizer_enforced_constraints

    # 4. Verify no false VALID or APPROVED claim is produced
    assert handoff.handoff_status == PolicyValidationStatusEnum.REQUIRES_OPTIMIZATION
    assert handoff.handoff_status not in (PolicyValidationStatusEnum.VALID, PolicyValidationStatusEnum.APPROVED)

    # 5. Verify diagnostic clearly explains why optimization/re-solve is required
    assert "REQUIRES_OPTIMIZATION" in handoff.advisory_rationale
    assert "Phase 6" in handoff.advisory_rationale
    assert "re-optimization" in handoff.advisory_rationale.lower()

    # 6. Verify DIRECTLY_SUPPORTED
    assert handoff.enforcement_tiers["recommended_mode"] == HandoffEnforcementTierEnum.DIRECTLY_SUPPORTED.value
    assert handoff.enforcement_tiers["generator_overrides"] == HandoffEnforcementTierEnum.DIRECTLY_SUPPORTED.value
    assert "mode" in handoff.optimizer_enforced_constraints
    assert "generator_overrides" in handoff.optimizer_enforced_constraints

    # 7. Verify DERIVED_FROM_SUPPORTED_INPUT
    assert handoff.enforcement_tiers["min_operating_reserve_pct"] == HandoffEnforcementTierEnum.DERIVED_FROM_SUPPORTED_INPUT.value
    assert handoff.optimizer_enforced_constraints["derived_reserve_margin_elevation"] is True


# ==============================================================================
# 17. COMPLETE POLICY STATE ENUM LIFECYCLE COVERAGE
# ==============================================================================

def test_complete_policy_state_enum_coverage(bharati_policy, profile_registry, safety_registry):
    """
    Phase 8 Freeze Audit Item 2:
    Explicitly tests all 9 lifecycle states in PolicyStateEnum:
    - NO_ACTION: Nominal station with no elevated policy requirement.
    - MONITOR: SAFE/WATCH observation state.
    - PREPARE: AT_RISK condition requiring preparedness.
    - MITIGATE: AT_RISK/THREATENED condition requiring active mitigation posture.
    - PROTECT: Critical protection condition.
    - RECOVER: Valid Phase 7 RECOVERY state.
    - ESCALATE: Critical condition requiring governance escalation.
    - BLOCKED: Policy whose requested action cannot safely proceed due to constraint.
    - INVALID_INPUT: Malformed/incomplete upstream assessment.
    """
    twin = TwinEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)
    res_eng = ResilienceEngine("BHARATI", profile_registry.get("BHARATI"), safety_registry)

    # 1. NO_ACTION: Nominal station in SAFE state
    traj_nom = build_synthetic_trajectory(twin, length_h=24, base_load_kw=30.0)
    assess_nom = res_eng.assess_trajectory(traj_nom)
    trace_no_action, _ = bharati_policy.evaluate_policy(assess_nom, traj_nom.states[0])
    assert trace_no_action.policy_state == PolicyStateEnum.NO_ACTION

    # 2. MONITOR: SAFE/WATCH observation state
    traj_mon = build_synthetic_trajectory(twin, length_h=24, ambient_temp_c=-26.0)
    assess_mon = res_eng.assess_trajectory(traj_mon)
    trace_mon, _ = bharati_policy.evaluate_policy(assess_mon, traj_mon.states[0])
    assert trace_mon.policy_state == PolicyStateEnum.MONITOR

    # 3. PREPARE: AT_RISK condition requiring preparedness (thermal warning buffer)
    traj_prep = build_synthetic_trajectory(twin, length_h=24)
    traj_prep.states[0].thermal.indoor_temperature_c = 13.5  # within [12.0, 14.0] buffer
    assess_prep = res_eng.assess_trajectory(traj_prep)
    trace_prep, _ = bharati_policy.evaluate_policy(assess_prep, traj_prep.states[0])
    assert trace_prep.policy_state == PolicyStateEnum.PREPARE
    assert trace_prep.primary_policy.action == PolicyActionEnum.PREPARE_THERMAL_ENVELOPE

    # 4. MITIGATE: AT_RISK/THREATENED condition requiring active mitigation posture
    traj_mit = build_synthetic_trajectory(twin, length_h=24)
    assess_mit = res_eng.assess_trajectory(traj_mit)
    assess_mit.resilience_state = ResilienceStateEnum.AT_RISK
    assess_mit.threat_decomposition.append(
        ThreatIndicator(
            threat_type=ResilienceThreatEnum.SOLAR_FAILURE,
            severity=FailureSeverityEnum.WARNING,
            trigger_condition="Solar generation loss during peak daylight",
            affected_subsystems=["SOLAR", "ELECTRICAL"]
        )
    )
    trace_mit, _ = bharati_policy.evaluate_policy(assess_mit, traj_mit.states[0])
    assert trace_mit.policy_state == PolicyStateEnum.MITIGATE
    assert trace_mit.primary_policy.action == PolicyActionEnum.BLOCK_DISCRETIONARY_LOADS

    # 5. PROTECT: Critical protection condition (reserve collapse)
    traj_prot = build_synthetic_trajectory(twin, length_h=24)
    traj_prot.states[0].resilience.dependable_reserve_pct = 11.0
    assess_prot = res_eng.assess_trajectory(traj_prot)
    trace_prot, _ = bharati_policy.evaluate_policy(assess_prot, traj_prot.states[0])
    assert trace_prot.policy_state == PolicyStateEnum.PROTECT

    # 6. RECOVER: Valid Phase 7 RECOVERY state
    traj_rec = build_synthetic_trajectory(twin, length_h=24)
    assess_rec = res_eng.assess_trajectory(traj_rec, previous_state=ResilienceStateEnum.CRITICAL)
    trace_rec, _ = bharati_policy.evaluate_policy(assess_rec, traj_rec.states[0])
    assert trace_rec.policy_state == PolicyStateEnum.RECOVER
    assert trace_rec.primary_policy.action == PolicyActionEnum.ADOPT_STATION_RECOVERY_POSTURE

    # 7. ESCALATE: Critical condition requiring governance escalation (compound crisis)
    traj_esc = build_synthetic_trajectory(twin, length_h=24)
    traj_esc.states[0].loads.unserved_critical_kw = 15.0
    traj_esc.states[0].fuel.fuel_remaining_l = 20000.0  # <= 25,000 L emergency limit
    assess_esc = res_eng.assess_trajectory(traj_esc)
    assess_esc.resilience_state = ResilienceStateEnum.CRITICAL
    trace_esc, _ = bharati_policy.evaluate_policy(assess_esc, traj_esc.states[0])
    assert trace_esc.policy_state == PolicyStateEnum.ESCALATE
    assert trace_esc.primary_policy.policy_state == PolicyStateEnum.ESCALATE

    # 8. BLOCKED: Requested action cannot safely proceed (all standby generators faulted)
    traj_blk = build_synthetic_trajectory(twin, length_h=24)
    traj_blk.states[0].resilience.dependable_reserve_pct = 10.0  # triggers PREPARE_STANDBY_GENERATOR
    assess_blk = res_eng.assess_trajectory(traj_blk)
    # Unit 1 is online; Units 2 and 3 are faulted -> zero standby units available in 3-generator fleet
    trace_blk, _ = bharati_policy.evaluate_policy(
        assess_blk, traj_blk.states[0], generator_overrides={1: "ONLINE", 2: "FAULT", 3: "FAULT"}
    )
    assert trace_blk.policy_state == PolicyStateEnum.BLOCKED
    assert trace_blk.validation_status == PolicyValidationStatusEnum.BLOCKED
    assert trace_blk.primary_policy.policy_state == PolicyStateEnum.BLOCKED
    assert trace_blk.primary_policy.validation_status == PolicyValidationStatusEnum.BLOCKED
    assert "BLOCKED" in trace_blk.primary_policy.reason

    # 9. INVALID_INPUT: Malformed/incomplete upstream assessment
    trace_inv, _ = bharati_policy.evaluate_policy(None, None)
    assert trace_inv.policy_state == PolicyStateEnum.INVALID_INPUT
    assert trace_inv.validation_status == PolicyValidationStatusEnum.UPSTREAM_INVALID


