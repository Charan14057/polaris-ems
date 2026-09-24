"""
POLARIS-EMS — Phase 13 Validation & Benchmarking Schemas
SIH26061: Polar Energy Management & Resilience System

Typed data schemas for scientific validation, model explainability,
optimizer benchmarking, reproducibility audits, and SIH technical evidence.
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class BenchmarkOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ReproductionCategory(str, Enum):
    IDENTICAL = "IDENTICAL"
    NUMERICALLY_EQUIVALENT_WITHIN_TOLERANCE = "NUMERICALLY_EQUIVALENT_WITHIN_TOLERANCE"
    EXPECTED_NONDETERMINISM = "EXPECTED_NONDETERMINISM"
    REPRODUCTION_FAILURE = "REPRODUCTION_FAILURE"


class ForecastMetricItem(BaseModel):
    station_id: str
    target: str
    horizon_hours: int
    n_samples: int
    mae: float
    rmse: float
    smape: float
    r2: float
    mbe: float
    capacity_norm_mae_pct: float
    capacity_norm_rmse_pct: float
    evidence_type: str = "SYNTHETIC"  # SYNTHETIC | REAL


class ProbabilisticCalibrationItem(BaseModel):
    station_id: str
    target: str
    horizon_hours: int
    p10_coverage: float
    p50_coverage: float
    p90_coverage: float
    p95_coverage: float
    interval_80_coverage: float
    interval_80_nominal_gap: float
    interval_80_width_kw: float
    quantile_crossings_count: int
    quantile_crossing_rate: float
    is_calibrated: bool


class BaselineComparisonRow(BaseModel):
    station_id: str
    target: str
    horizon_hours: int
    model_name: str
    baseline_type: str  # PERSISTENCE | SEASONAL_NAIVE | RIDGE | RANDOM_FOREST | PRODUCTION_XGB
    mae: float
    rmse: float
    smape: float
    r2: float
    relative_improvement_pct: float  # vs persistence


class RegimeEvaluationItem(BaseModel):
    regime: str  # NORMAL | BLIZZARD | POLAR_NIGHT | EXTREME_COLD | etc.
    station_id: str
    target: str
    mae: float
    rmse: float
    degradation_ratio: float  # ratio relative to normal regime
    evidence_type: str = "SIMULATED"


class LeakageAuditReport(BaseModel):
    audit_passed: bool
    chronological_split_verified: bool
    zero_future_weather_leakage: bool
    zero_future_target_leakage: bool
    causal_feature_availability_verified: bool
    audit_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    diagnostics: List[str] = Field(default_factory=list)


class FeatureContributionItem(BaseModel):
    feature_name: str
    feature_value: float
    shapley_value: float  # Exact marginal model contribution
    relative_contribution_pct: float
    direction: str  # INCREASES_PREDICTION | DECREASES_PREDICTION


class ModelExplanationResponse(BaseModel):
    station_id: str
    target: str
    model_name: str
    model_version: str
    explanation_method: str = "EXACT_TREE_SHAP_NATIVE"
    base_value: float  # Expected value E[f(x)]
    predicted_value: float  # f(x)
    additivity_verified: bool  # sum(shap) + base_value == predicted_value
    label_warning: str = "MODEL CONTRIBUTION ONLY — NOT PHYSICAL CAUSATION"
    contributions: List[FeatureContributionItem]
    explanation_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provenance: str = "FORECAST"


class OptimizerBenchmarkComparison(BaseModel):
    station_id: str
    scenario_id: str
    horizon_hours: int
    mode: str
    comparability_status: str = "DIRECTLY_COMPARABLE"
    baseline_fuel_liters: float
    optimized_fuel_liters: float
    fuel_delta_liters: float
    fuel_savings_pct: float
    baseline_unserved_kwh: float
    optimized_unserved_kwh: float
    unserved_delta_kwh: float
    baseline_min_reserve_pct: float
    optimized_min_reserve_pct: float
    twin_replay_valid: bool
    solver_time_sec: float
    optimality_tier: str


class ResilienceStressValidationItem(BaseModel):
    station_id: str
    scenario_sequence: List[str]
    observed_states: List[str]
    observed_composite_indices: List[float]
    stress_consistency_verified: bool
    invariants_passed_count: int
    total_invariants_count: int


class EdgeDegradationValidationItem(BaseModel):
    station_id: str
    condition: str
    edge_mode: str
    connectivity_state: str
    fallback_posture: str
    central_solver_invoked: bool  # MUST BE FALSE for offline
    offline_safety_verified: bool
    buffered_observations: int


class ReplayReproductionReport(BaseModel):
    original_trace_id: str
    station_id: str
    reproduction_category: ReproductionCategory
    max_absolute_error: float
    max_relative_error: float
    stages_reproduced: List[str]
    matches: Dict[str, bool]
    notes: str
    replayed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SIHEvidenceRow(BaseModel):
    capability: str
    test_description: str
    metric_measured: str
    measured_result: str
    source_authority: str
    evidence_class: str  # REAL | CONFIGURED | ASSUMED | SYNTHETIC | FORECAST | SIMULATED
    limitations: str
    outcome: BenchmarkOutcome


class BenchmarkSuiteSummary(BaseModel):
    suite_id: str
    executed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    software_version: str = "1.0.0"
    overall_outcome: BenchmarkOutcome
    forecast_mae_average: float
    conformal_coverage_average_pct: float
    optimizer_average_fuel_savings_pct: float
    twin_replay_pass_rate_pct: float
    offline_safety_compliance_pct: float
    reproducibility_rate_pct: float
    leakage_audit_clean: bool
    total_benchmarks_executed: int
