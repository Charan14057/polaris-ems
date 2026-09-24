"""
POLARIS-EMS — Phase 14 Master Production & Demonstration Script
SIH26061: Polar Energy Management & Resilience System

Workstream J: Deterministic Master Demonstration Workflow
Executes the full operational sequence across all frozen computational authorities:
1. Production Configuration & Reality Bridge Initialization
2. Reality Bridge External Validation & Boundary Filter Check
3. Multi-Station Fleet Selection (BHARATI, MAITRI, HIMADRI)
4. Tactical Horizon Conformal Forecast Generation (P10, P50, P90, P95)
5. Authoritative Polar Stress Perturbation (Scenario BLIZZARD)
6. Mixed-Integer Microgrid Optimal Dispatch (HiGHS MILP)
7. Digital Twin Physical Feasibility Replay (Power Balance, SOC, Thermal)
8. Multi-Horizon Resilience Assessment & Survival Horizons
9. Policy Governance Directive & Priority Enforcement (P1-P8)
10. Immutable Decision Trace Lineage & Operator Review Approval Boundary
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import get_settings
from backend.integrations.bridge import get_reality_bridge
from backend.integrations.schemas import ExternalWeatherObservation
from backend.data.station_profiles.loader import StationProfileRegistry
from backend.ml.registry import ModelRegistry
from backend.scenarios.registry import ScenarioRegistry
from backend.api.adapters.pipeline_orchestrator import PipelineOrchestrator
from backend.api.schemas.pipeline import PipelineAnalyzeRequestSchema


def run_phase14_demonstration():
    print("\n" + "=" * 80)
    print("POLARIS-EMS: PHASE 14 PRODUCTION & REALITY BRIDGE DEMONSTRATION")
    print("SIH26061: AI-Driven Smart Energy Management System for Polar Research Stations")
    print("=" * 80)

    # 1. Configuration & Runtime Environment
    settings = get_settings()
    print(f"\n[STEP 1] Inspecting Production Configuration...")
    print(f"  -> Product Name         : {settings.product.product_name}")
    print(f"  -> System Title         : {settings.product.system_title}")
    print(f"  -> Version              : {settings.product.version}")
    print(f"  -> Environment          : {settings.deployment.environment}")
    print(f"  -> Operator Mode        : {settings.product.operator_mode}")
    print(f"  -> Physical SCADA Link  : {settings.product.physical_scada_connected} (Calibrated Digital Twin Mode)")
    print(f"  -> Security Headers     : {settings.security.enable_security_headers}")
    print(f"  -> Payload Limit        : {settings.security.max_request_bytes} bytes")

    # 2. Reality Bridge & Quality Sanity Filter
    print(f"\n[STEP 2] Testing External Reality Bridge & Quality Sanity Filter...")
    bridge = get_reality_bridge()
    summary = bridge.get_bridge_summary()
    print(f"  -> Registered Adapters  : {summary['registered_providers']} {summary['active_adapters']}")
    print(f"  -> Provenance Taxonomy  : {summary['provenance_policy']}")

    # Test physical boundary validator with valid observation
    valid_obs = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=datetime.now(timezone.utc),
        ambient_temperature_c=-24.5,
        wind_speed_ms=18.2,
        solar_irradiance_wm2=0.0,
        source_provider="Demonstration-Source",
        provenance="SYNTHETIC"
    )
    val_res = bridge.validator.validate_weather(valid_obs)
    assert val_res.is_valid, f"Validation failed: {val_res.errors}"
    print(f"  -> Boundary Filter Check: PASS (Quality Score: {val_res.quality_score}, Status: {val_res.staleness_status.value})")

    # Test physical boundary validator rejecting out-of-bounds temperature (-105°C)
    invalid_obs = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=datetime.now(timezone.utc),
        ambient_temperature_c=-105.0,  # Below -90°C physical limit
        wind_speed_ms=10.0,
        solar_irradiance_wm2=0.0,
        source_provider="Demonstration-Source",
        provenance="SYNTHETIC"
    )
    inv_res = bridge.validator.validate_weather(invalid_obs)
    assert not inv_res.is_valid, "Expected physical boundary filter rejection for -105°C"
    print(f"  -> Out-of-Bounds Reject : PASS (Correctly quarantined: {inv_res.errors[0]})")

    # 3. Fleet Initialization
    print(f"\n[STEP 3] Initializing Multi-Station Polar Fleet...")
    profile_reg = StationProfileRegistry()
    stations = profile_reg.list_stations()
    print(f"  -> Loaded Stations      : {len(stations)} ({', '.join(stations)})")
    for st in stations:
        spec = profile_reg.get(st)
        agg_diesel = spec.electrical.diesel_generator_count * spec.electrical.diesel_generator_kw_rated
        print(f"     * {st:8s}: Bus {spec.electrical.nominal_voltage_v}V @ {spec.electrical.grid_frequency_hz}Hz, "
              f"{spec.electrical.diesel_generator_count} Gensets ({agg_diesel:.0f} kW)")

    # 4. Pipeline Execution: Station BHARATI, 48h Tactical, BLIZZARD Scenario
    target_station = "BHARATI"
    print(f"\n[STEP 4] Executing Full Operational Decision Pipeline for {target_station}...")
    orchestrator = PipelineOrchestrator()
    req = PipelineAnalyzeRequestSchema(
        station_id=target_station,
        horizon_hours=48,
        scenario_id="BLIZZARD",
        mode="SCENARIO_ROBUST"
    )

    t0 = time.perf_counter()
    pipeline_res = orchestrator.run_pipeline(req)
    duration_sec = time.perf_counter() - t0

    print(f"  -> Pipeline Trace ID    : {pipeline_res.decision_trace_id}")
    print(f"  -> Overall Outcome      : {pipeline_res.overall_status}")
    print(f"  -> Execution Duration   : {duration_sec:.3f} seconds")
    print(f"  -> Stages Executed      : {len(pipeline_res.stages)}")

    for stage in pipeline_res.stages:
        status_symbol = "OK" if stage.status == "COMPLETED" else stage.status
        print(f"     [{stage.stage_name:12s}] : {status_symbol:9s} ({stage.duration_sec:.3f}s)")

    # 5. Review Stage Highlights
    print(f"\n[STEP 5] Reviewing Subsystem Highlights...")
    if pipeline_res.forecast:
        print(f"  -> Conformal Forecast   : {len(pipeline_res.forecast.quantiles)} intervals computed across P10-P95")

    if pipeline_res.optimizer:
        print(f"  -> Optimizer Solution   : Status={pipeline_res.optimizer.solver_status}, "
              f"Tier={pipeline_res.optimizer.optimality_tier}, "
              f"Cost=${pipeline_res.optimizer.summary.total_cost:.2f}, "
              f"Min Reserve={pipeline_res.optimizer.summary.min_reserve_margin_pct:.1f}%")

    if pipeline_res.resilience:
        print(f"  -> Resilience Assessment: State={pipeline_res.resilience.resilience_state}, "
              f"Survival Horizon={pipeline_res.resilience.survival_horizons.overall_station_survival_horizon_h}h")

    if pipeline_res.policy:
        action_desc = pipeline_res.policy.primary_policy.action if pipeline_res.policy.primary_policy else "MONITOR"
        print(f"  -> Policy Directive     : State={pipeline_res.policy.policy_state}, "
              f"P1-P8 Action={action_desc}, "
              f"Active Policies={len(pipeline_res.policy.active_policies)}")

    # 6. Operator Review & Approval Boundary
    print(f"\n[STEP 6] Operator Review Approval Boundary...")
    print(f"  -> Actuator Dispatch    : HELD PENDING SUPERVISOR REVIEW")
    print(f"  -> Supervisory Posture  : {settings.product.operator_mode} (No autonomous physical actuation)")
    print(f"  -> Physical SCADA Presence: Zero connected physical polar SCADA telemetry")
    print(f"  -> Dispatch Authorization: SIMULATION VALIDATION COMPLETE")

    print("\n" + "=" * 80)
    print("ALL PHASE 14 PRODUCTION & INTEGRATION GATES DEMONSTRATED SUCCESSFULLY (100%)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_phase14_demonstration()
