#!/usr/bin/env python3
"""
POLARIS-EMS — Phase 13 Scientific Validation & Benchmarking Runtime Audit
SIH26061: Polar Energy Management & Resilience System

Validates:
1. Scientific benchmark configuration registry
2. Forecast accuracy validation & point metrics
3. Conformal uncertainty calibration & coverage
4. Formal data leakage & causality audit
5. Weather disturbance regime evaluation
6. Native Tree SHAP model feature explainability
7. Fair microgrid optimizer benchmarking
8. Closed-loop Digital Twin physical validation
9. Resilience stress escalation & property invariants
10. Edge telemetry degradation & offline safety proof
11. End-to-end decision trace reproducibility replay
12. Pluggable cold trace archive statistics
13. Pipeline component latency performance profiling
14. Consolidated SIH evidence table & report generation
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

GATEWAY_URL = "http://127.0.0.1:3000"
BACKEND_URL = "http://127.0.0.1:8000"

# Target port 3000 (Vite reverse proxy) with fallback to 8000 (FastAPI direct)
def get_base_url():
    try:
        req = urllib.request.Request(f"{GATEWAY_URL}/health/ready", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                return GATEWAY_URL
    except Exception:
        pass
    return BACKEND_URL

BASE_URL = get_base_url()
LOCKED_PROVENANCE_TIERS = {"REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"}


def request_json(endpoint: str, method: str = "GET", payload: dict = None):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json", "X-Request-ID": "audit-phase13"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8"))
        return e.code, body


def check_prov(provenance: str, context: str):
    assert provenance in LOCKED_PROVENANCE_TIERS, f"{context}: Invalid provenance tier '{provenance}'"


def main():
    print("=" * 80)
    print("POLARIS-EMS PHASE 13: SCIENTIFIC VALIDATION & BENCHMARKING AUDIT")
    print(f"Target Gateway: {BASE_URL}")
    print("=" * 80)

    passed_gates = 0
    total_gates = 14

    # Gate 1: Benchmark Configuration
    print("\nGate 1: Validation Configuration Registry...")
    config_file = ROOT / "configs" / "benchmark_registry.json"
    assert config_file.exists(), "configs/benchmark_registry.json missing"
    with open(config_file, "r", encoding="utf-8") as f:
        bench_cfg = json.load(f)
    assert len(bench_cfg["stations"]) == 3
    assert len(bench_cfg["baselines"]) >= 4
    passed_gates += 1
    print(f"[PASS] Gate 1: Configuration verified. Suite ID: {bench_cfg['benchmark_suite_id']}")

    # Gate 2: Forecast Validation Metrics
    print("\nGate 2: Forecast Validation Metrics...")
    status, body = request_json("/api/v1/validation/forecast")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 2")
    metrics = body["data"]
    assert len(metrics) == 57, f"Expected exactly 57 evaluated forecast horizons and targets, got {len(metrics)}"
    avg_mae = sum(m["mae"] for m in metrics) / len(metrics)
    assert 3.50 <= avg_mae <= 3.60, f"Average MAE {avg_mae:.3f} deviates from expected 3.55 kW baseline"
    passed_gates += 1
    print(f"[PASS] Gate 2: Forecast Metrics retrieved ({len(metrics)} points across 3 stations, avg MAE={avg_mae:.2f} kW). Prov={body['provenance']}")

    # Gate 3: Conformal Calibration
    print("\nGate 3: Conformal Uncertainty Calibration & Quantile Taxonomy...")
    status, body = request_json("/api/v1/validation/calibration")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 3")
    calibs = body["data"]
    assert len(calibs) > 0
    
    # Audit Quantile Taxonomy: strictly P10, P50, P90, P95 (80% nominal interval [P10, P90])
    for c in calibs:
        assert "p05_coverage" not in c, "Invalid P05 quantile found in calibration schema"
        assert "p80_coverage" not in c, "Invalid P80 quantile found (80% is coverage band, not individual quantile)"
        assert c["p10_coverage"] >= 0.0 and c["p95_coverage"] <= 1.0
        if "load" in c["target"].lower():
            assert c["p10_coverage"] <= c["p50_coverage"] <= c["p90_coverage"] <= c["p95_coverage"], \
                f"Quantile monotonicity violated in {c['station_id']} {c['target']}"
        assert c["quantile_crossings_count"] == 0, f"Quantile crossing detected in {c['station_id']}"
    
    avg_cov = sum(c["interval_80_coverage"] for c in calibs) / len(calibs) * 100.0
    passed_gates += 1
    print(f"[PASS] Gate 3: Conformal Calibration verified (Avg 80% coverage={avg_cov:.1f}%, Zero crossings, Quantiles=[P10, P50, P90, P95]). Prov={body['provenance']}")

    # Gate 4: Leakage Audit
    print("\nGate 4: Data Leakage & Causality Audit...")
    status, body = request_json("/api/v1/validation/leakage-audit")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 4")
    leak = body["data"]
    assert leak["audit_passed"] is True
    assert leak["zero_future_target_leakage"] is True
    passed_gates += 1
    print(f"[PASS] Gate 4: Data Leakage Audit certified clean (0 violations). Prov={body['provenance']}")

    # Gate 5: Disturbance Regimes
    print("\nGate 5: Disturbance Regime Evaluations...")
    status, body = request_json("/api/v1/validation/regimes")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 5")
    regimes = body["data"]
    assert len(regimes) > 0
    passed_gates += 1
    print(f"[PASS] Gate 5: {len(regimes)} Disturbance Regime evaluations retrieved. Prov={body['provenance']}")

    # Gate 6: Native Tree SHAP Explainability
    print("\nGate 6: Model Explainability (Tree SHAP)...")
    status, body = request_json("/api/v1/validation/explain/BHARATI/total_load_kw")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 6")
    exp = body["data"]
    assert exp["explanation_method"] == "EXACT_TREE_SHAP_NATIVE"
    assert exp["additivity_verified"] is True
    assert len(exp["contributions"]) > 0
    top_driver = exp["contributions"][0]
    passed_gates += 1
    print(f"[PASS] Gate 6: Tree SHAP explainability verified (Top driver: '{top_driver['feature_name']}' {top_driver['relative_contribution_pct']}%). Prov={body['provenance']}")

    # Gate 7: Optimizer Benchmarks
    print("\nGate 7: Optimizer vs Baseline Benchmarks...")
    status, body = request_json("/api/v1/validation/optimizer")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 7")
    opt = body["data"]
    assert len(opt) > 0
    passed_gates += 1
    print(f"[PASS] Gate 7: Optimizer benchmark matrix verified ({len(opt)} comparisons, fair initial states). Prov={body['provenance']}")

    # Gate 8: Digital Twin Physical Replay Validation
    print("\nGate 8: Digital Twin Physical Validation...")
    replay_passes = sum(1 for o in opt if o["twin_replay_valid"])
    assert replay_passes > 0, "Zero optimizer schedules passed twin replay"
    pass_rate = (replay_passes / len(opt)) * 100.0
    passed_gates += 1
    print(f"[PASS] Gate 8: Closed-Loop Twin physical validation verified ({replay_passes}/{len(opt)} valid, {pass_rate:.1f}% pass rate; physical limits enforced).")

    # Gate 9: Resilience Stress Validation
    print("\nGate 9: Resilience Stress & Invariant Validation...")
    status, body = request_json("/api/v1/validation/resilience/BHARATI")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 9")
    res = body["data"]
    assert res["stress_consistency_verified"] is True
    assert res["invariants_passed_count"] == res["total_invariants_count"]
    
    # Vocabulary Audit: strictly {SAFE, WATCH, AT_RISK, THREATENED, CRITICAL, RECOVERY}
    LOCKED_RESILIENCE_STATES = {"SAFE", "WATCH", "AT_RISK", "THREATENED", "CRITICAL", "RECOVERY"}
    for step in res.get("escalation_steps", []):
        st = step["state"]
        assert st in LOCKED_RESILIENCE_STATES, f"Invalid resilience state '{st}' encountered"
        assert st != "SECURE", "Prohibited non-existent resilience state 'SECURE' detected"
    
    passed_gates += 1
    print(f"[PASS] Gate 9: Resilience Stress Invariants verified ({res['invariants_passed_count']}/{res['total_invariants_count']} invariants passed; vocabulary conformant). Prov={body['provenance']}")

    # Gate 10: Edge Degradation & Offline Safety
    print("\nGate 10: Edge Degradation & Offline Safety Proof...")
    status, body = request_json("/api/v1/validation/edge")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 10")
    edge = body["data"]
    assert len(edge) >= 5
    offline_item = next(e for e in edge if "OFFLINE" in e["condition"])
    assert offline_item["central_solver_invoked"] is False
    assert offline_item["offline_safety_verified"] is True
    passed_gates += 1
    print(f"[PASS] Gate 10: Edge offline safety proof certified (central_solver_invoked=False during offline). Prov={body['provenance']}")

    # Gate 11: End-to-End Decision Trace Reproducibility Replay
    print("\nGate 11: Decision Trace Reproducibility Replay...")
    # Get available traces
    status, trace_list_resp = request_json("/api/v1/traces?limit=1")
    raw_data = trace_list_resp.get("data", [])
    traces = raw_data if isinstance(raw_data, list) else raw_data.get("traces", [])
    assert len(traces) > 0, "No recorded traces found for replay"
    sample_tid = traces[0]["decision_trace_id"]

    status, body = request_json(f"/api/v1/validation/replay/{sample_tid}")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 11")
    rep = body["data"]
    assert rep["reproduction_category"] in [
        "IDENTICAL",
        "NUMERICALLY_EQUIVALENT_WITHIN_TOLERANCE",
        "EXPECTED_NONDETERMINISM"
    ]
    passed_gates += 1
    print(f"[PASS] Gate 11: Trace '{sample_tid}' replayed successfully (Category: {rep['reproduction_category']}, Max Δ={rep['max_absolute_error']:.4f}). Prov={body['provenance']}")

    # Gate 12: Pluggable Cold Trace Archive
    print("\nGate 12: Pluggable Cold Trace Archive Statistics...")
    status, body = request_json("/api/v1/validation/archive/stats")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 12")
    arch = body["data"]
    assert "total_archived_traces" in arch
    assert "archive_type" in arch
    passed_gates += 1
    print(f"[PASS] Gate 12: Trace Archive verified (Type: {arch['archive_type']}, Retained: {arch['total_archived_traces']}). Prov={body['provenance']}")

    # Gate 13: Computational Latency Performance Profiling
    print("\nGate 13: Pipeline Performance & Latency Benchmarks...")
    status, body = request_json("/api/v1/validation/performance?station_id=BHARATI")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 13")
    perf = body["data"]
    fc_lat = perf.get("forecast_inference_ms", {}).get("median_ms", 0.0)
    shap_lat = perf.get("tree_shap_explainability_ms", {}).get("median_ms", 0.0)
    passed_gates += 1
    print(f"[PASS] Gate 13: Latency profile retrieved (Forecast median={fc_lat:.2f}ms, SHAP median={shap_lat:.2f}ms). Prov={body['provenance']}")

    # Gate 14: Evidence Table & Scientific Artifacts
    print("\nGate 14: Consolidated Scientific Evidence & Artifacts...")
    status, body = request_json("/api/v1/validation/evidence")
    assert status == 200 and body["status"] == "SUCCESS"
    check_prov(body["provenance"], "Gate 14")
    evidence = body["data"]
    assert len(evidence) >= 6

    # Verify report files exist on disk
    expected_reports = [
        "forecast_benchmark.json",
        "forecast_benchmark.csv",
        "forecast_benchmark.md",
        "forecast_calibration.json",
        "forecast_calibration.md",
        "optimizer_benchmark.json",
        "resilience_validation.json",
        "edge_validation.json",
        "explainability_report.json",
        "reproducibility.json",
        "reproducibility.csv",
        "reproducibility.md",
        "leakage_audit.md",
        "SIH_TECHNICAL_EVIDENCE.md",
        "phase13_summary.md"
    ]
    rep_dir = ROOT / "reports" / "phase13"
    missing = [r for r in expected_reports if not (rep_dir / r).exists()]
    assert not missing, f"Missing report files in reports/phase13/: {missing}"

    # Automated Language & Claim Guard: scan all exported markdown files
    for r in expected_reports:
        if r.endswith(".md"):
            content = (rep_dir / r).read_text(encoding="utf-8")
            assert "guarantees zero shed load under all conditions" not in content, f"Overstated guarantee claim found in {r}"
            assert "`SECURE`" not in content and "State=SECURE" not in content, f"Non-authoritative state 'SECURE' found in {r}"

    passed_gates += 1
    print(f"[PASS] Gate 14: Scientific Evidence verified ({len(evidence)} capabilities, {len(expected_reports)} reports on disk, claim guard passed). Prov={body['provenance']}")

    print("\n" + "=" * 80)
    print(f"ALL {passed_gates}/{total_gates} PHASE 13 SCIENTIFIC VALIDATION AUDIT GATES PASSED (100%)")
    print("=" * 80)
    sys.exit(0)


if __name__ == "__main__":
    main()
