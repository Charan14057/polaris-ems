/**
 * POLARIS-EMS — Validation & Benchmarking API Client
 * Enterprise Scientific Validation & Model Explainability
 */

import { apiRequest } from './client';

export interface ForecastMetricItem {
  station_id: string;
  target: string;
  horizon_hours: number;
  n_samples: number;
  mae: number;
  rmse: number;
  smape: number;
  r2: number;
  mbe: number;
  capacity_norm_mae_pct: number;
  capacity_norm_rmse_pct: number;
  evidence_type: string;
}

export interface ProbabilisticCalibrationItem {
  station_id: string;
  target: string;
  horizon_hours: number;
  p10_coverage: number;
  p50_coverage: number;
  p90_coverage: number;
  p95_coverage: number;
  interval_80_coverage: number;
  interval_80_nominal_gap: number;
  interval_80_width_kw: number;
  quantile_crossings_count: number;
  quantile_crossing_rate: number;
  is_calibrated: boolean;
}

export interface BaselineComparisonRow {
  station_id: string;
  target: string;
  horizon_hours: number;
  model_name: string;
  baseline_type: string;
  mae: number;
  rmse: number;
  smape: number;
  r2: number;
  relative_improvement_pct: number;
}

export interface RegimeEvaluationItem {
  regime: string;
  station_id: string;
  target: string;
  mae: number;
  rmse: number;
  degradation_ratio: number;
  evidence_type: string;
}

export interface LeakageAuditReport {
  audit_passed: boolean;
  chronological_split_verified: boolean;
  zero_future_weather_leakage: boolean;
  zero_future_target_leakage: boolean;
  causal_feature_availability_verified: boolean;
  audit_timestamp: string;
  diagnostics: string[];
}

export interface FeatureContributionItem {
  feature_name: string;
  feature_value: number;
  shapley_value: number;
  relative_contribution_pct: number;
  direction: string;
}

export interface ModelExplanationResponse {
  station_id: string;
  target: string;
  model_name: string;
  model_version: string;
  explanation_method: string;
  base_value: number;
  predicted_value: number;
  additivity_verified: boolean;
  label_warning: string;
  contributions: FeatureContributionItem[];
  explanation_timestamp: string;
  provenance: string;
}

export interface OptimizerBenchmarkComparison {
  station_id: string;
  scenario_id: string;
  horizon_hours: number;
  mode: string;
  comparability_status: string;
  baseline_fuel_liters: number;
  optimized_fuel_liters: number;
  fuel_delta_liters: number;
  fuel_savings_pct: number;
  baseline_unserved_kwh: number;
  optimized_unserved_kwh: number;
  unserved_delta_kwh: number;
  baseline_min_reserve_pct: number;
  optimized_min_reserve_pct: number;
  twin_replay_valid: boolean;
  solver_time_sec: number;
  optimality_tier: string;
}

export interface ResilienceStressValidationItem {
  station_id: string;
  scenario_sequence: string[];
  observed_states: string[];
  observed_composite_indices: number[];
  stress_consistency_verified: boolean;
  invariants_passed_count: number;
  total_invariants_count: number;
}

export interface EdgeDegradationValidationItem {
  station_id: string;
  condition: string;
  edge_mode: string;
  connectivity_state: string;
  fallback_posture: string;
  central_solver_invoked: boolean;
  offline_safety_verified: boolean;
  buffered_observations: number;
}

export interface ReplayReproductionReport {
  original_trace_id: string;
  station_id: string;
  reproduction_category: string;
  max_absolute_error: number;
  max_relative_error: number;
  stages_reproduced: string[];
  matches: Record<string, boolean>;
  notes: string;
  replayed_at: string;
}

export interface TechnicalEvidenceRow {
  capability: string;
  test_description: string;
  metric_measured: string;
  measured_result: string;
  source_authority: string;
  evidence_class: string;
  limitations: string;
  outcome: string;
}

export interface BenchmarkSuiteSummary {
  suite_id: string;
  executed_at: string;
  software_version: string;
  overall_outcome: string;
  forecast_mae_average: number;
  conformal_coverage_average_pct: number;
  optimizer_average_fuel_savings_pct: number;
  twin_replay_pass_rate_pct: number;
  offline_safety_compliance_pct: number;
  reproducibility_rate_pct: number;
  leakage_audit_clean: boolean;
  total_benchmarks_executed: number;
}

export const validationApi = {
  getSummary: () =>
    apiRequest<BenchmarkSuiteSummary>('/api/v1/validation/summary'),

  getEvidence: () =>
    apiRequest<TechnicalEvidenceRow[]>('/api/v1/validation/evidence'),

  getForecastMetrics: () =>
    apiRequest<ForecastMetricItem[]>('/api/v1/validation/forecast'),

  getCalibration: () =>
    apiRequest<ProbabilisticCalibrationItem[]>('/api/v1/validation/calibration'),

  getBaselines: () =>
    apiRequest<BaselineComparisonRow[]>('/api/v1/validation/baselines'),

  getRegimes: () =>
    apiRequest<RegimeEvaluationItem[]>('/api/v1/validation/regimes'),

  getLeakageAudit: () =>
    apiRequest<LeakageAuditReport>('/api/v1/validation/leakage-audit'),

  getOptimizerBenchmarks: () =>
    apiRequest<OptimizerBenchmarkComparison[]>('/api/v1/validation/optimizer'),

  getResilienceValidation: (stationId: string) =>
    apiRequest<ResilienceStressValidationItem>(`/api/v1/validation/resilience/${stationId}`),

  getEdgeValidation: () =>
    apiRequest<EdgeDegradationValidationItem[]>('/api/v1/validation/edge'),

  getExplainability: (stationId: string, target: string = 'total_load_kw') =>
    apiRequest<ModelExplanationResponse>(`/api/v1/validation/explain/${stationId}/${target}`),

  replayTrace: (traceId: string) =>
    apiRequest<ReplayReproductionReport>(`/api/v1/validation/replay/${traceId}`),

  getArchiveStats: () =>
    apiRequest<Record<string, any>>('/api/v1/validation/archive/stats'),

  getPerformance: (stationId: string = 'BHARATI') =>
    apiRequest<Record<string, Record<string, number>>>(`/api/v1/validation/performance?station_id=${stationId}`),

  // Phase 15 — Real-World Integration, Drift & Twin Calibration Endpoints
  getRealityMetrics: (stationId?: string) =>
    apiRequest<RealityMetricItem[]>(`/api/v1/integrations/validation/metrics${stationId ? `?station_id=${stationId}` : ''}`),

  getDriftIndicators: () =>
    apiRequest<DriftIndicatorItem[]>('/api/v1/integrations/validation/drift'),

  getTwinRealityChecks: (stationId?: string) =>
    apiRequest<TwinRealityItem[]>(`/api/v1/integrations/validation/twin-check${stationId ? `?station_id=${stationId}` : ''}`),

  getCalibrationCandidates: () =>
    apiRequest<CalibrationCandidateItem[]>('/api/v1/integrations/validation/candidates'),

  getProviders: () =>
    apiRequest<ProviderHealthItem[]>('/api/v1/integrations/providers'),

  getIntegrationStatus: () =>
    apiRequest<Record<string, any>>('/api/v1/integrations/status'),
};

export interface RealityMetricItem {
  station_id: string;
  target: string;
  horizon_hours: number;
  n_samples: number;
  mae: number;
  rmse: number;
  smape: number;
  signed_bias: number;
  interval_80_coverage: number;
  source: string;
  weather_regime?: string | null;
  provenance: string;
}

export interface TwinRealityItem {
  station_id: string;
  subsystem: 'electrical' | 'thermal' | 'battery' | 'fuel';
  timestamp: string;
  observed_value: number;
  simulated_value: number;
  residual: number;
  relative_error_pct: number;
  status: 'VALIDATED' | 'DISCREPANCY' | 'CALIBRATION_CANDIDATE';
  candidate_id?: string | null;
  unit: string;
}

export interface DriftIndicatorItem {
  metric_name: string;
  station_id: string;
  drift_type: 'DATA_DRIFT' | 'MODEL_DRIFT' | 'PHYSICAL_MODEL_MISMATCH' | 'PROVIDER_FAILURE';
  severity: 'NOMINAL' | 'WARNING' | 'ALERT';
  score: number;
  threshold: number;
  p_value?: number | null;
  description: string;
  detected_at: string;
}

export interface CalibrationCandidateItem {
  candidate_id: string;
  target_subsystem: string;
  model_or_param: string;
  created_at: string;
  baseline_metric: number;
  candidate_metric: number;
  quantified_degradation: number;
  status: 'PROPOSED' | 'REVIEWED' | 'APPLIED' | 'REJECTED';
  evidence_summary: string;
}

export interface ProviderHealthItem {
  provider_name: string;
  status: 'AVAILABLE' | 'DEGRADED' | 'STALE' | 'FAILED' | 'QUARANTINED' | 'DISABLED';
  latency_ms: number;
  last_success_timestamp?: string | null;
  error_count: number;
  failure_reason?: string | null;
  consecutive_failures: number;
}
