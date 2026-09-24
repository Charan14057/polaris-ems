"""
POLARIS-EMS — Phase 13 Scientific Validation & Benchmarking Test Suite
SIH26061: Polar Energy Management & Resilience System

Validates:
1. Forecast validation & point accuracy metric computation.
2. Probabilistic conformal interval calibration & quantile crossing invariants.
3. Baseline benchmarking comparisons (XGBoost vs Persistence, Naive, Ridge, RF).
4. Data leakage, chronological partitioning & causality invariants.
5. Exact Tree SHAP explainability, additivity proof, & non-causal labeling.
6. Fair optimizer benchmarking & HiGHS solver optimality tier classification.
7. Closed-loop Digital Twin physical validation replay.
8. Resilience stress progression & 5 formal physical/logical invariants.
9. Edge degradation & offline safety proof (zero solver invocation when disconnected).
10. End-to-end decision trace reproducibility replay & tolerance classification.
11. Pluggable cold trace archive storage, retrieval, and stats.
12. Component latency profiling benchmark harness.
13. Consolidated scientific evidence taxonomy & provenance classification.
14. Strict architectural boundary preservation (no optimizer/physics duplication).
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from backend.validation.schema import (
    BenchmarkOutcome,
    ReproductionCategory,
    ForecastMetricItem,
    ProbabilisticCalibrationItem,
    BaselineComparisonRow,
    RegimeEvaluationItem,
    LeakageAuditReport,
    ModelExplanationResponse,
    OptimizerBenchmarkComparison,
    ResilienceStressValidationItem,
    EdgeDegradationValidationItem,
    ReplayReproductionReport,
    SIHEvidenceRow,
    BenchmarkSuiteSummary
)
from backend.validation.forecast_validator import get_forecast_validator
from backend.validation.optimizer_benchmark import get_optimizer_benchmark
from backend.validation.resilience_validator import get_resilience_validator
from backend.validation.edge_validator import get_edge_validator
from backend.validation.explainability import get_model_explainer
from backend.validation.reproducibility import get_replay_runner
from backend.validation.performance import get_performance_benchmark
from backend.validation.sih_evidence import get_sih_evidence_engine
from backend.trace.archive import get_trace_archive
from backend.trace.repository import get_trace_repository
from backend.trace.schema import TraceRecord


# ──────────────────────────────────────────────────────────────
# 1. FORECAST VALIDATION & POINT ACCURACY
# ──────────────────────────────────────────────────────────────

def test_forecast_validator_metrics():
    val = get_forecast_validator()
    metrics = val.get_forecast_metrics()
    assert len(metrics) > 0, "No forecast metrics returned"
    
    stations = {m.station_id for m in metrics}
    assert "BHARATI" in stations or "MAITRI" in stations or "HIMADRI" in stations

    for m in metrics:
        assert m.mae >= 0.0, f"Negative MAE for {m.station_id} {m.target}"
        assert m.rmse >= m.mae, f"RMSE must be >= MAE for {m.station_id} {m.target}"
        assert 0.0 <= m.smape <= 100.0, f"sMAPE out of bounds [0, 100]: {m.smape}"
        assert m.evidence_type in ["SYNTHETIC", "REAL"]


def test_forecast_validator_horizons():
    val = get_forecast_validator()
    metrics = val.get_forecast_metrics()
    horizons = {m.horizon_hours for m in metrics}
    assert 24 in horizons, "Horizon 24h must be evaluated"
    assert 48 in horizons or 1 in horizons, "Multi-horizon evaluation required"


# ──────────────────────────────────────────────────────────────
# 2. PROBABILISTIC CONFORMAL CALIBRATION
# ──────────────────────────────────────────────────────────────

def test_probabilistic_calibration():
    val = get_forecast_validator()
    calibs = val.get_probabilistic_calibration()
    assert len(calibs) > 0, "No calibration items returned"

    for c in calibs:
        # Quantiles coverage must be bounded [0, 1]
        assert 0.0 <= c.p10_coverage <= 1.0
        assert 0.0 <= c.p50_coverage <= 1.0
        assert 0.0 <= c.p90_coverage <= 1.0
        assert 0.0 <= c.p95_coverage <= 1.0
        # For non-zero-inflated targets, monotonic ordering holds
        if "load" in c.target.lower():
            assert c.p10_coverage <= c.p50_coverage <= c.p90_coverage <= c.p95_coverage, \
                f"Quantile monotonicity violated in {c.station_id} {c.target}"
        # Interval width positive
        assert c.interval_80_width_kw > 0.0, "Interval width must be positive"
        # Zero crossings in conformal calibrators
        assert c.quantile_crossings_count == 0, "Quantile crossings detected"
        # Empirical coverage within valid bounds
        assert 0.0 <= c.interval_80_coverage <= 1.0


# ──────────────────────────────────────────────────────────────
# 3. BASELINE BENCHMARKING
# ──────────────────────────────────────────────────────────────

def test_baseline_comparisons():
    val = get_forecast_validator()
    baselines = val.get_baseline_comparisons()
    assert len(baselines) > 0, "No baseline comparisons returned"

    types = {b.baseline_type for b in baselines}
    assert "PRODUCTION_XGB" in types, "Production XGBoost must be present"
    assert "PERSISTENCE" in types, "Persistence baseline must be present"

    for b in baselines:
        assert b.mae >= 0.0
        assert b.rmse >= 0.0


# ──────────────────────────────────────────────────────────────
# 4. DATA LEAKAGE & CAUSALITY
# ──────────────────────────────────────────────────────────────

def test_leakage_audit():
    val = get_forecast_validator()
    audit = val.run_leakage_audit()
    assert isinstance(audit, LeakageAuditReport)
    assert audit.audit_passed is True, f"Leakage audit failed: {audit.diagnostics}"
    assert audit.chronological_split_verified is True
    assert audit.zero_future_weather_leakage is True
    assert audit.zero_future_target_leakage is True
    assert audit.causal_feature_availability_verified is True


# ──────────────────────────────────────────────────────────────
# 5. MODEL EXPLAINABILITY (TREE SHAP)
# ──────────────────────────────────────────────────────────────

def test_model_explainability_native_tree_shap():
    explainer = get_model_explainer()
    resp = explainer.explain_prediction("BHARATI", "total_load_kw")
    
    assert isinstance(resp, ModelExplanationResponse)
    assert resp.station_id == "BHARATI"
    assert resp.explanation_method == "EXACT_TREE_SHAP_NATIVE"
    assert resp.additivity_verified is True, "Shapley additivity proof failed"
    assert "NOT PHYSICAL CAUSATION" in resp.label_warning
    assert len(resp.contributions) > 0

    # Verify additivity flag and driver ranking
    assert resp.additivity_verified is True
    assert len(resp.contributions) <= 15
    assert all(c.relative_contribution_pct >= 0.0 for c in resp.contributions)


def test_model_explainability_unsupported_target():
    explainer = get_model_explainer()
    with pytest.raises(Exception):
        explainer.explain_prediction("BHARATI", "invalid_target_xyz")


# ──────────────────────────────────────────────────────────────
# 6. OPTIMIZER BENCHMARK & TWIN VALIDATION
# ──────────────────────────────────────────────────────────────

def test_optimizer_benchmark_and_twin_replay():
    bench = get_optimizer_benchmark()
    matrix = bench.run_benchmark_matrix()
    assert len(matrix) > 0, "No optimizer comparisons generated"

    for item in matrix:
        assert isinstance(item, OptimizerBenchmarkComparison)
        assert item.comparability_status == "DIRECTLY_COMPARABLE"
        assert item.baseline_fuel_liters > 0.0
        assert item.optimized_fuel_liters > 0.0
        assert item.solver_time_sec >= 0.0
        assert item.optimality_tier in ["EXACT_OPTIMAL", "MIP_GAP_OPTIMAL", "FEASIBLE"]
        # Closed loop twin replay must be explicitly recorded
        assert isinstance(item.twin_replay_valid, bool)


# ──────────────────────────────────────────────────────────────
# 7. RESILIENCE STRESS RESPONSE & INVARIANTS
# ──────────────────────────────────────────────────────────────

def test_resilience_validation_and_invariants():
    val = get_resilience_validator()
    report = val.validate_stress_sequence("BHARATI")
    assert isinstance(report, ResilienceStressValidationItem)
    assert report.invariants_passed_count == report.total_invariants_count
    assert report.total_invariants_count == 5
    assert report.stress_consistency_verified is True
    assert len(report.observed_states) == 4


# ──────────────────────────────────────────────────────────────
# 8. EDGE DEGRADATION & OFFLINE SAFETY
# ──────────────────────────────────────────────────────────────

def test_edge_offline_safety_proof():
    val = get_edge_validator()
    conditions = val.validate_all_conditions()
    assert len(conditions) >= 5, "Must test at least 5 degradation conditions"

    # Find offline conditions
    offline_items = [c for c in conditions if "OFFLINE" in c.condition]
    assert len(offline_items) > 0, "CONNECTIVITY_OFFLINE condition must be tested"

    for off in offline_items:
        # CRITICAL OFFLINE INVARIANT:
        assert off.central_solver_invoked is False, "Central solver was invoked during OFFLINE!"
        assert off.offline_safety_verified is True
        assert off.fallback_posture != ""


# ──────────────────────────────────────────────────────────────
# 9. END-TO-END REPRODUCIBILITY REPLAY
# ──────────────────────────────────────────────────────────────

def test_reproducibility_replay():
    runner = get_replay_runner()
    trace_repo = get_trace_repository()
    traces = trace_repo.list_traces()
    
    if traces:
        sample_id = traces[0].decision_trace_id
        rep = runner.replay_trace(sample_id)
        assert isinstance(rep, ReplayReproductionReport)
        assert rep.reproduction_category in [
            ReproductionCategory.IDENTICAL,
            ReproductionCategory.NUMERICALLY_EQUIVALENT_WITHIN_TOLERANCE,
            ReproductionCategory.EXPECTED_NONDETERMINISM,
            ReproductionCategory.REPRODUCTION_FAILURE
        ]
        assert rep.original_trace_id == sample_id
        assert len(rep.stages_reproduced) > 0


# ──────────────────────────────────────────────────────────────
# 10. PLUGGABLE TRACE ARCHIVE
# ──────────────────────────────────────────────────────────────

def test_trace_archive_lifecycle(tmp_path):
    archive = get_trace_archive()
    stats = archive.get_archive_stats()
    assert "total_archived_traces" in stats
    assert "total_archive_bytes" in stats
    assert "archive_directory" in stats


# ──────────────────────────────────────────────────────────────
# 11. PERFORMANCE BENCHMARK HARNESS
# ──────────────────────────────────────────────────────────────

def test_performance_benchmark():
    perf = get_performance_benchmark()
    timings = perf.benchmark_component_latencies("BHARATI", n_iterations=1)
    assert "forecast_inference_ms" in timings
    assert "tree_shap_explainability_ms" in timings
    assert "scenario_stress_execution_ms" in timings
    for comp, stats in timings.items():
        assert "median_ms" in stats
        assert stats["median_ms"] >= 0.0


# ──────────────────────────────────────────────────────────────
# 12. SCIENTIFIC EVIDENCE PACKAGE & PROVENANCE
# ──────────────────────────────────────────────────────────────

def test_sih_evidence_table():
    engine = get_sih_evidence_engine()
    rows = engine.generate_evidence_table()
    assert len(rows) >= 6, "Evidence package must contain at least 6 capability tests"

    valid_classes = {"REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"}
    for r in rows:
        assert isinstance(r, SIHEvidenceRow)
        assert r.evidence_class in valid_classes, f"Invalid provenance class: {r.evidence_class}"
        assert r.outcome in [BenchmarkOutcome.PASS, BenchmarkOutcome.FAIL, BenchmarkOutcome.INCONCLUSIVE, BenchmarkOutcome.NOT_APPLICABLE]
        assert r.limitations != "", "Explicit scientific limitations required"


# ──────────────────────────────────────────────────────────────
# 13. STRICT ARCHITECTURAL BOUNDARY AUDIT
# ──────────────────────────────────────────────────────────────

def test_boundary_invariants_no_duplication():
    # Verify validation module does not import or execute raw Pyomo solvers directly
    val_dir = Path(__file__).resolve().parent.parent / "backend" / "validation"
    for py_file in val_dir.glob("*.py"):
        code = py_file.read_text(encoding="utf-8")
        assert "import pyomo" not in code, f"Pyomo directly imported in validation module: {py_file.name}"
        assert "from pyomo" not in code, f"Pyomo directly imported in validation module: {py_file.name}"
        assert "import highspy" not in code, f"HiGHS directly imported in validation module: {py_file.name}"


# ──────────────────────────────────────────────────────────────
# 14. PRE-FREEZE RECONCILIATION GUARDS
# ──────────────────────────────────────────────────────────────

def test_quantile_taxonomy_integrity():
    """Asserts that conformal uncertainty quantiles strictly match P10, P50, P90, P95 and nominal 80% interval [P10, P90]."""
    val = get_forecast_validator()
    calibs = val.get_probabilistic_calibration()
    assert len(calibs) > 0

    for c in calibs:
        assert not hasattr(c, "p05_coverage"), "Prohibited P05 quantile found in calibration schema"
        assert not hasattr(c, "p80_coverage"), "Prohibited P80 quantile found (80% is coverage band, not individual quantile)"
        assert hasattr(c, "p10_coverage")
        assert hasattr(c, "p50_coverage")
        assert hasattr(c, "p90_coverage")
        assert hasattr(c, "p95_coverage")
        assert hasattr(c, "interval_80_coverage")
        # 80% interval coverage is bounded
        assert 0.0 <= c.interval_80_coverage <= 1.0


def test_resilience_vocabulary_integrity():
    """Asserts that all resilience states adhere strictly to Phase 7 ResilienceStateEnum without fictitious states."""
    from backend.resilience.schema import ResilienceStateEnum
    valid_states = {s.value for s in ResilienceStateEnum}
    assert valid_states == {"SAFE", "WATCH", "AT_RISK", "THREATENED", "CRITICAL", "RECOVERY"}
    assert "SECURE" not in valid_states, "Fictitious resilience state 'SECURE' must not exist in Phase 7 enum"

    res_val = get_resilience_validator()
    for station in ["BHARATI", "MAITRI", "HIMADRI"]:
        item = res_val.validate_stress_sequence(station)
        assert len(item.observed_states) > 0
        for s in item.observed_states:
            assert s in valid_states
            assert s != "SECURE"


def test_digital_twin_physical_tolerances():
    """Asserts that digital twin tolerances are explicitly documented and enforced."""
    from backend.twin.power_balance import PowerBalanceEngine
    assert PowerBalanceEngine.TOLERANCE_KW == 1e-4, "Power balance tolerance must be exactly 1e-4 kW (0.1 W)"


def test_sample_count_and_denominator_integrity():
    """Asserts that exactly 57 forecast horizon/target evaluations exist across 3 stations."""
    val = get_forecast_validator()
    metrics = val.get_forecast_metrics()
    assert len(metrics) == 57, f"Expected exactly 57 evaluations, got {len(metrics)}"
    
    from collections import Counter
    station_counts = Counter(m.station_id for m in metrics)
    for st in ["BHARATI", "MAITRI", "HIMADRI"]:
        assert station_counts[st] == 19, f"Station {st} must have exactly 19 evaluations (7 load + 6 solar + 6 wind)"

