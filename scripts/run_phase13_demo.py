#!/usr/bin/env python3
"""
POLARIS-EMS — Phase 13 Master End-to-End Scientific Demonstration
SIH26061: Polar Energy Management & Resilience System

Demonstrates complete execution across all 13 phases:
1. Select Bharati Station
2. Ingest validated operational telemetry
3. Produce Phase 3 ML Forecast (calibrated quantiles P10..P95)
4. Evaluate Phase 5 stress scenario (BLIZZARD)
5. Run Phase 6 Microgrid Optimizer (SCENARIO_ROBUST dispatch)
6. Replay through Phase 4 Computational Digital Twin
7. Evaluate Phase 7 Resilience Assessment & Survival Horizons
8. Enforce Phase 8 Operational Policy Governance
9. Capture immutable Phase 12 Decision Trace
10. Generate Phase 12 deterministic 'Why?' explainability narrative
11. Execute Phase 13 model feature attribution (Tree SHAP)
12. Replay recorded Decision Trace via ReplayRunner & evaluate reproducibility
13. Exercise Phase 11 Edge-First Field Resilience & Offline Safety Invariant
14. Repeat fleet validation across Maitri and Himadri
15. Export audit-ready scientific evidence package
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.api.adapters.pipeline_orchestrator import PipelineOrchestrator
from backend.api.schemas.pipeline import PipelineAnalyzeRequestSchema
from backend.validation.explainability import get_model_explainer
from backend.validation.reproducibility import get_replay_runner
from backend.validation.edge_validator import get_edge_validator
from backend.validation.sih_evidence import get_sih_evidence_engine
from backend.trace.repository import get_trace_repository


def section(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def main():
    section("POLARIS-EMS: PHASE 13 MASTER SCIENTIFIC VALIDATION DEMONSTRATION")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("Platform: 3 Polar Stations (BHARATI, MAITRI, HIMADRI)")
    print("Status: PHASES 1-12 FROZEN | PHASE 13 BENCHMARK & EVIDENCE ACTIVE\n")

    orchestrator = PipelineOrchestrator()
    trace_repo = get_trace_repository()
    explainer = get_model_explainer()
    replay_runner = get_replay_runner()

    # ──────────────────────────────────────────────────────────────
    # 1. BHARATI END-TO-END PIPELINE RUN
    # ──────────────────────────────────────────────────────────────
    section("1. BHARATI END-TO-END PIPELINE EXECUTION (BLIZZARD STRESS)")
    
    req_bharati = PipelineAnalyzeRequestSchema(
        station_id="BHARATI",
        horizon_hours=24,
        scenario_id="BLIZZARD",
        mode="SCENARIO_ROBUST"
    )
    print(f"Running pipeline with: Station={req_bharati.station_id}, Horizon={req_bharati.horizon_hours}h, Scenario={req_bharati.scenario_id}, Mode={req_bharati.mode}...")
    
    resp_bharati = orchestrator.run_pipeline(req_bharati)
    trace_id_bharati = resp_bharati.decision_trace_id

    print(f"\n[OUTPUT] Pipeline Execution Completed:")
    print(f"  -> Decision Trace ID : {trace_id_bharati}")
    print(f"  -> Overall Status     : {resp_bharati.overall_status}")
    print(f"  -> Stages Executed    : {len(resp_bharati.stages)}")
    print(f"  -> Optimizer Status   : {resp_bharati.optimizer.solver_status if resp_bharati.optimizer else 'N/A'}")
    print(f"  -> Resilience State   : {resp_bharati.resilience.resilience_state if resp_bharati.resilience else 'N/A'}")
    print(f"  -> Policy Directive   : {resp_bharati.policy.policy_state if resp_bharati.policy else 'N/A'}")

    # ──────────────────────────────────────────────────────────────
    # 2. DECISION TRACE & EXPLAINABILITY
    # ──────────────────────────────────────────────────────────────
    section("2. DECISION TRACE & EXPLAINABILITY AUDIT")
    trace_record = trace_repo.get_trace(trace_id_bharati)
    assert trace_record is not None, "Trace record was not persisted!"
    print(f"Trace Record '{trace_id_bharati}' loaded from store:")
    print(f"  -> Stages Executed   : {[s.stage.value for s in trace_record.events]}")
    print(f"  -> Lineage DAG Nodes : {len(trace_record.events)} stages with parent-child links")
    if trace_record.explanation:
        print(f"  -> Deterministic 'Why?': {trace_record.explanation.headline}")

    # ──────────────────────────────────────────────────────────────
    # 3. NATIVE TREE SHAP EXPLAINABILITY
    # ──────────────────────────────────────────────────────────────
    section("3. PHASE 13 MODEL EXPLAINABILITY (TREE SHAP ATTRIBUTION)")
    shap_resp = explainer.explain_prediction("BHARATI", "total_load_kw")
    print(f"Target: {shap_resp.target} | Model: {shap_resp.model_name}")
    print(f"Base Value E[f(x)]: {shap_resp.base_value:.2f} kW | Model Prediction f(x): {shap_resp.predicted_value:.2f} kW")
    print(f"Additivity Verified: {shap_resp.additivity_verified} | Label: {shap_resp.label_warning}")
    print("Top Feature Drivers (Model Contributions):")
    for i, c in enumerate(shap_resp.contributions[:5], 1):
        print(f"  {i}. {c.feature_name:24s} : {c.shapley_value:+7.3f} kW ({c.relative_contribution_pct:5.1f}%) [{c.direction}]")

    # ──────────────────────────────────────────────────────────────
    # 4. CLOSED-LOOP REPRODUCIBILITY REPLAY
    # ──────────────────────────────────────────────────────────────
    section("4. PHASE 13 DECISION TRACE REPRODUCIBILITY REPLAY")
    print(f"Rerunning complete pipeline from snapshot inputs for trace '{trace_id_bharati}'...")
    replay_report = replay_runner.replay_trace(trace_id_bharati)
    print(f"Replay Category: {replay_report.reproduction_category.value}")
    print(f"Max Absolute Objective Delta: {replay_report.max_absolute_error:.5f}")
    print(f"Stages Reproduced: {replay_report.stages_reproduced}")
    print(f"State Matches: Policy={replay_report.matches.get('policy_state_match')}, Resilience={replay_report.matches.get('resilience_state_match')}")

    # ──────────────────────────────────────────────────────────────
    # 5. OFFLINE EDGE RESILIENCE SAFETY INVARIANT
    # ──────────────────────────────────────────────────────────────
    section("5. PHASE 11 EDGE-FIRST FIELD RESILIENCE & OFFLINE SAFETY PROOF")
    edge_val = get_edge_validator()
    edge_results = edge_val.validate_all_conditions()
    for e in edge_results:
        solver_status = "BLOCKED (SAFE)" if not e.central_solver_invoked else "PERMITTED"
        print(f"Condition: {e.condition:22s} | Mode: {e.edge_mode:20s} | Posture: {e.fallback_posture:26s} | Solver: {solver_status}")

    # ──────────────────────────────────────────────────────────────
    # 6. MULTI-STATION COVERAGE (MAITRI & HIMADRI)
    # ──────────────────────────────────────────────────────────────
    section("6. MULTI-STATION COVERAGE (MAITRI & HIMADRI)")
    for st, scn, md in [("MAITRI", "SOLAR_FAILURE", "CONSERVATIVE"), ("HIMADRI", "EXTREME_COLD", "EXPECTED")]:
        print(f"\nExecuting pipeline for {st} ({scn}, {md})...")
        req_st = PipelineAnalyzeRequestSchema(
            station_id=st,
            horizon_hours=24,
            scenario_id=scn,
            mode=md
        )
        resp_st = orchestrator.run_pipeline(req_st)
        print(f"  -> Station {st}: Trace={resp_st.decision_trace_id}, Status={resp_st.overall_status}, Resilience={resp_st.resilience.resilience_state if resp_st.resilience else 'N/A'}")

    # ──────────────────────────────────────────────────────────────
    # 7. SCIENTIFIC EVIDENCE PACKAGE
    # ──────────────────────────────────────────────────────────────
    section("7. CONSOLIDATED SCIENTIFIC EVIDENCE SUMMARY")
    evidence_eng = get_sih_evidence_engine()
    summary = evidence_eng.generate_suite_summary()
    print(f"Suite ID                     : {summary.suite_id}")
    print(f"Overall Suite Outcome        : {summary.overall_outcome.value}")
    print(f"Average Conformal Coverage   : {summary.conformal_coverage_average_pct:.1f}%")
    print(f"Average Point Forecast MAE   : {summary.forecast_mae_average:.2f} kW")
    print(f"Digital Twin Replay Pass Rate: {summary.twin_replay_pass_rate_pct:.1f}%")
    print(f"Offline Safety Compliance    : {summary.offline_safety_compliance_pct:.1f}%")
    print(f"Trace Reproducibility Rate   : {summary.reproducibility_rate_pct:.1f}%")
    print(f"Data Leakage Audit Clean     : {summary.leakage_audit_clean}")

    section("PHASE 13 SCIENTIFIC DEMONSTRATION COMPLETE: READY FOR VALIDATION")


if __name__ == "__main__":
    main()
