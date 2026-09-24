"""
POLARIS-EMS — Validation, Benchmarking & Explainability API Routes
SIH26061: Polar Energy Management & Resilience System

Exposes REST API endpoints for Phase 13:
- Forecast metrics and uncertainty calibration
- Baseline comparisons vs ML models
- Data leakage & causality audit
- Optimizer vs baseline dispatch benchmarks
- Resilience stress progression and property invariants
- Edge degradation and offline safety proof
- Native Tree SHAP model explainability
- Decision trace reproducibility replay
- Cold archive statistics
- Consolidated SIH technical evidence table
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Request

from backend.api.responses import APIResponse
from backend.validation.schema import (
    ForecastMetricItem,
    ProbabilisticCalibrationItem,
    BaselineComparisonRow,
    RegimeEvaluationItem,
    LeakageAuditReport,
    OptimizerBenchmarkComparison,
    ResilienceStressValidationItem,
    EdgeDegradationValidationItem,
    ModelExplanationResponse,
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

router = APIRouter(prefix="/validation", tags=["Validation & Benchmarking"])


@router.get("/forecast", response_model=APIResponse[List[ForecastMetricItem]])
async def get_forecast_metrics(request: Request) -> APIResponse[List[ForecastMetricItem]]:
    """Returns standardized point-forecast evaluation metrics across registered models."""
    val = get_forecast_validator()
    data = val.get_forecast_metrics()
    return APIResponse.success(data=data, provenance="SYNTHETIC")


@router.get("/calibration", response_model=APIResponse[List[ProbabilisticCalibrationItem]])
async def get_uncertainty_calibration(request: Request) -> APIResponse[List[ProbabilisticCalibrationItem]]:
    """Returns empirical coverage and sharpness across conformal calibrators."""
    val = get_forecast_validator()
    data = val.get_probabilistic_calibration()
    return APIResponse.success(data=data, provenance="SYNTHETIC")


@router.get("/baselines", response_model=APIResponse[List[BaselineComparisonRow]])
async def get_baseline_comparisons(request: Request) -> APIResponse[List[BaselineComparisonRow]]:
    """Compares production models against persistence, seasonal naive, ridge, and random forest."""
    val = get_forecast_validator()
    data = val.get_baseline_comparisons()
    return APIResponse.success(data=data, provenance="SYNTHETIC")


@router.get("/regimes", response_model=APIResponse[List[RegimeEvaluationItem]])
async def get_regime_evaluations(request: Request) -> APIResponse[List[RegimeEvaluationItem]]:
    """Evaluates forecast degradation ratios across polar disturbance regimes."""
    val = get_forecast_validator()
    data = val.get_regime_evaluations()
    return APIResponse.success(data=data, provenance="SIMULATED")


@router.get("/leakage-audit", response_model=APIResponse[LeakageAuditReport])
async def get_leakage_audit(request: Request) -> APIResponse[LeakageAuditReport]:
    """Returns automated data leakage and causality verification report."""
    val = get_forecast_validator()
    data = val.run_leakage_audit()
    return APIResponse.success(data=data, provenance="CONFIGURED")


@router.get("/optimizer", response_model=APIResponse[List[OptimizerBenchmarkComparison]])
async def get_optimizer_benchmarks(request: Request) -> APIResponse[List[OptimizerBenchmarkComparison]]:
    """Returns fair benchmark matrix comparing baseline simulation vs optimizer modes."""
    bench = get_optimizer_benchmark()
    data = bench.run_benchmark_matrix()
    return APIResponse.success(data=data, provenance="SIMULATED")


@router.get("/resilience/{station_id}", response_model=APIResponse[ResilienceStressValidationItem])
async def get_resilience_validation(station_id: str, request: Request) -> APIResponse[ResilienceStressValidationItem]:
    """Returns resilience stress response consistency and invariant pass rates."""
    val = get_resilience_validator()
    data = val.validate_stress_sequence(station_id)
    return APIResponse.success(data=data, provenance="SIMULATED")


@router.get("/edge", response_model=APIResponse[List[EdgeDegradationValidationItem]])
async def get_edge_validation(request: Request) -> APIResponse[List[EdgeDegradationValidationItem]]:
    """Returns edge behavior across 7 canonical degraded telemetry conditions."""
    val = get_edge_validator()
    data = val.validate_all_conditions()
    return APIResponse.success(data=data, provenance="CONFIGURED")


@router.get("/explain/{station_id}/{target}", response_model=APIResponse[ModelExplanationResponse])
async def get_feature_explainability(
    station_id: str,
    target: str,
    request: Request
) -> APIResponse[ModelExplanationResponse]:
    """Computes exact native Tree SHAP feature contributions for a model prediction."""
    explainer = get_model_explainer()
    try:
        data = explainer.explain_prediction(station_id=station_id, target=target)
        return APIResponse.success(data=data, provenance="FORECAST")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/replay/{trace_id}", response_model=APIResponse[ReplayReproductionReport])
async def replay_decision_trace(trace_id: str, request: Request) -> APIResponse[ReplayReproductionReport]:
    """Reruns the complete pipeline from recorded trace inputs and evaluates reproducibility."""
    runner = get_replay_runner()
    try:
        data = runner.replay_trace(trace_id)
        return APIResponse.success(data=data, provenance="SIMULATED")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=APIResponse[Dict[str, Dict[str, float]]])
async def get_performance_latencies(
    station_id: str = "BHARATI",
    request: Request = None
) -> APIResponse[Dict[str, Dict[str, float]]]:
    """Returns computational latency distributions (median, p95, max) across pipeline components."""
    perf = get_performance_benchmark()
    data = perf.benchmark_component_latencies(station_id=station_id, n_iterations=2)
    return APIResponse.success(data=data, provenance="SIMULATED")


@router.get("/evidence", response_model=APIResponse[List[SIHEvidenceRow]])
async def get_sih_evidence_table(request: Request) -> APIResponse[List[SIHEvidenceRow]]:
    """Returns the consolidated, audit-ready SIH technical evidence table."""
    engine = get_sih_evidence_engine()
    data = engine.generate_evidence_table()
    return APIResponse.success(data=data, provenance="SIMULATED")


@router.get("/summary", response_model=APIResponse[BenchmarkSuiteSummary])
async def get_benchmark_suite_summary(request: Request) -> APIResponse[BenchmarkSuiteSummary]:
    """Returns high-level executive benchmark summary metrics."""
    engine = get_sih_evidence_engine()
    data = engine.generate_suite_summary()
    return APIResponse.success(data=data, provenance="SIMULATED")


@router.get("/archive/stats", response_model=APIResponse[Dict[str, Any]])
async def get_archive_stats(request: Request) -> APIResponse[Dict[str, Any]]:
    """Returns cold decision trace archive statistics."""
    archive = get_trace_archive()
    data = archive.get_archive_stats()
    return APIResponse.success(data=data, provenance="CONFIGURED")
