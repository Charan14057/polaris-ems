/**
 * POLARIS-EMS — Synchronized Frontend Type Definitions
 * Polaris-EMS — Polar Energy Management & Resilience System
 * 
 * Accurately mirrors Phase 9 FastAPI schemas in backend/api/schemas/.
 * Preserves strict 6-tier provenance: REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED.
 */

export type ProvenanceTier = 
  | 'REAL' 
  | 'CONFIGURED' 
  | 'ASSUMED' 
  | 'SYNTHETIC' 
  | 'FORECAST' 
  | 'SIMULATED';

export type StationId = 'BHARATI' | 'MAITRI' | 'HIMADRI';

export type ResilienceState = 
  | 'SAFE' 
  | 'WATCH' 
  | 'AT_RISK' 
  | 'THREATENED' 
  | 'CRITICAL' 
  | 'RECOVERY';

export type PolicyState = 
  | 'NO_ACTION' 
  | 'MONITOR' 
  | 'PREPARE' 
  | 'MITIGATE' 
  | 'PROTECT' 
  | 'RECOVER' 
  | 'ESCALATE' 
  | 'BLOCKED';

export type OptimizationMode = 'EXPECTED' | 'CONSERVATIVE' | 'SCENARIO_ROBUST';

export type OptimalityTier = 'EXACT_OPTIMAL' | 'MIP_GAP_OPTIMAL' | 'FALLBACK' | 'INFEASIBLE';

// Standard API Response Envelope
export interface APIResponse<T> {
  request_id: string;
  status: 'SUCCESS' | 'PARTIAL' | 'ERROR';
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  diagnostics: string[];
  provenance: ProvenanceTier;
  timestamp: string;
  api_version: string;
}

// Health & Capabilities
export interface ReadinessResponse {
  ready: boolean;
  loaded_stations: string[];
  loaded_scenarios: number;
  loaded_models: string[];
  timestamp: string;
}

export interface CapabilitiesResponse {
  stations: string[];
  horizons_supported_hours: number[];
  forecasting: {
    owning_phase: string;
    targets: string[];
    calibrated_quantiles: string[];
    uncertainty_calibration: string;
  };
  twin_simulation: {
    owning_phase: string;
    physical_subsystems: string[];
    constraints_evaluated: number;
    power_balance_tolerance_kw: number;
  };
  scenarios: {
    owning_phase: string;
    registered_count: number;
    categories: string[];
  };
  optimizer: {
    owning_phase: string;
    solver: string;
    modes: string[];
    relative_gap_tolerance: number;
  };
  resilience: {
    owning_phase: string;
    states: string[];
    dimensions_count: number;
    horizons: string[];
  };
  policy_governance: {
    owning_phase: string;
    states: string[];
    priority_tiers: number;
    handoff_enforcement_tiers: string[];
  };
  timestamp: string;
}

// Station Details
export interface DeviceSummary {
  id: string;
  name: string;
  category: string;
  priority_rank: number;
  nominal_power_kw: number;
  deferrable: boolean;
}

export interface ElectricalDetail {
  nominal_voltage_v: number;
  grid_frequency_hz: number;
  solar_pv_kw_peak: number;
  wind_turbine_kw_rated: number;
  diesel_generator_count: number;
  diesel_generator_kw_rated: number;
  total_diesel_capacity_kw: number;
  battery_capacity_kwh: number;
  battery_min_soc: number;
  battery_max_soc: number;
  battery_max_charge_kw: number;
  battery_max_discharge_kw: number;
}

export interface ThermalDetail {
  indoor_target_temp_c: number;
  indoor_min_safe_temp_c: number;
  building_ua_kw_per_k: number;
  thermal_capacitance_kwh_per_k: number;
  internal_heat_gain_kw: number;
}

export interface FuelDetail {
  storage_capacity_liters: number;
  initial_fuel_liters: number;
  critical_fuel_reserve_liters: number;
  fuel_type: string;
}

export interface StationDetail {
  station_id: string;
  name: string;
  region: string;
  location: string;
  latitude: number;
  longitude: number;
  altitude_m: number;
  classification: string;
  climate_zone: string;
  polar_day_range: [string, string];
  polar_night_range: [string, string];
  resupply_interval_days: number;
  electrical: ElectricalDetail;
  thermal: ThermalDetail;
  fuel: FuelDetail;
  devices: DeviceSummary[];
  provenance: ProvenanceTier;
}

export interface StationSummary {
  station_id: string;
  name: string;
  region: string;
  total_diesel_capacity_kw: number;
  solar_pv_kw_peak: number;
  wind_turbine_kw_rated: number;
  battery_capacity_kwh: number;
  fuel_storage_liters: number;
  provenance: ProvenanceTier;
}

// Forecast
export interface QuantilePoint {
  horizon_h: number;
  timestamp: string;
  point: number;
  p10: number;
  p50: number;
  p90: number;
  p95: number;
}

export interface ForecastResponseData {
  station_id: string;
  forecast_origin: string;
  target: string;
  horizon_hours: number;
  quantiles: QuantilePoint[];
  mean_forecast_kw: number;
  min_p10_kw: number;
  max_p90_kw: number;
  model_version: string;
  feature_schema_version: string;
  provenance: ProvenanceTier;
}

// Scenarios
export interface ParameterTransform {
  parameter: string;
  operator: string;
  value: number;
  unit: string;
  rationale: string;
}

export interface ScenarioSummary {
  scenario_id: string;
  name: string;
  description: string;
  category: string;
  duration_hours: number;
  active_effects: string[];
  provenance: ProvenanceTier;
}

export interface ScenarioDetail extends ScenarioSummary {
  transforms: ParameterTransform[];
  rationale: string;
}

export interface ScenarioImpactMetrics {
  delta_unserved_energy_kwh: number;
  delta_critical_unserved_kwh: number;
  delta_diesel_fuel_liters: number;
  delta_min_indoor_temp_c: number;
  delta_min_battery_soc: number;
  primary_failure_mode: string;
  earliest_failure_hour?: number | null;
  failure_occurred: boolean;
}

export interface ScenarioEvaluateResponseData {
  scenario_id: string;
  station_id: string;
  category: string;
  duration_hours: number;
  impact_metrics: ScenarioImpactMetrics;
  violated_constraints: string[];
  failure_indicators: string[];
  baseline_trajectory_summary: Record<string, any>;
  scenario_trajectory_summary: Record<string, any>;
  provenance: ProvenanceTier;
}

// Optimizer
export interface DecisionStep {
  t: number;
  timestamp: string;
  p_diesel_kw: number;
  p_battery_charge_kw: number;
  p_battery_discharge_kw: number;
  p_solar_kw: number;
  p_wind_kw: number;
  p_served_load_kw: number;
  p_unserved_load_kw: number;
  battery_soc: number;
  fuel_remaining_l: number;
  indoor_temp_c: number;
  reserve_margin_pct: number;
}

export interface OptimizationSummary {
  total_cost: number;
  total_fuel_consumed_liters: number;
  total_unserved_load_kwh: number;
  total_critical_unserved_kwh: number;
  total_curtailed_renewable_kwh: number;
  min_reserve_margin_pct: number;
  final_battery_soc_pct: number;
  final_fuel_remaining_liters: number;
  min_indoor_temp_c: number;
}

export interface OptimizeResponseData {
  station_id: string;
  horizon_hours: number;
  mode: string;
  solver_status: string;
  optimality_tier: OptimalityTier;
  objective_value: number;
  best_bound?: number | null;
  relative_gap?: number | null;
  solve_time_sec: number;
  is_valid: boolean;
  twin_replay_valid: boolean;
  summary: OptimizationSummary;
  schedule?: DecisionStep[] | null;
  generator_schedules?: Record<number, any[]> | null;
  provenance: ProvenanceTier;
  diagnostics: string[];
}

// Resilience
export interface SurvivalHorizons {
  overall_station_survival_horizon_h: number;
  battery_endurance_horizon_h: number;
  thermal_habitability_horizon_h: number;
  fuel_endurance_horizon_h: number;
  critical_load_survival_horizon_h: number;
  resupply_gap_survivability_h: number;
  dependable_generation_horizon_h: number;
  binding_subsystem: string;
  survives_full_horizon: boolean;
}

export interface ResilienceDimensions {
  energy_adequacy: number;
  critical_load_resilience: number;
  thermal_resilience: number;
  generation_resilience: number;
  storage_resilience: number;
  fuel_resilience: number;
  logistics_resilience: number;
  renewable_resilience: number;
  recovery_resilience: number;
  composite_index: number;
  composite_resilience_index: number;
  explainable_loss?: Record<string, number>;
}

export interface ThreatIndicator {
  threat_type: string;
  severity: string;
  trigger_condition: string;
  affected_subsystems: string[];
}

export interface CandidateRecoveryOption {
  action_type: string;
  description: string;
  target_subsystem: string;
  rationale: string;
  expected_survival_horizon_gain_h: number;
  expected_reserve_margin_gain_pct: number;
  urgency: string;
  validation_tier: string;
  limitations: string;
  action_id?: string;
  expected_gain_h?: number;
  fuel_penalty_l?: number;
  advisory_only: boolean;
}

export interface ResilienceEvaluateResponseData {
  station_id: string;
  assessment_timestamp: string;
  horizon_hours: number;
  assessment_status: string;
  resilience_state: ResilienceState;
  active_threat_states: string[];
  survival_horizons: SurvivalHorizons;
  dimensions?: ResilienceDimensions | null;
  threat_decomposition: ThreatIndicator[];
  candidate_recovery_options: CandidateRecoveryOption[];
  failure_propagation?: any[] | null;
  provenance: ProvenanceTier;
  diagnostics: string[];
}

// Policy
export interface PolicyHysteresisState {
  active_policy_states: Record<string, string>;
  consecutive_steps: Record<string, number>;
  last_switch_timestep: Record<string, number>;
  deadbands: Record<string, number>;
}

export interface OptimizerHandoffRequirements {
  recommended_mode: string;
  generator_overrides: Record<number, string>;
  requested_constraints: Record<string, any>;
  optimizer_enforced_constraints: Record<string, any>;
  enforcement_tiers: Record<string, string>;
  handoff_status: string;
  advisory_rationale: string;
}

export interface PolicyRuleTrace {
  rule_id: string;
  priority_tier: string;
  action: string;
  target_subsystem: string;
  fired: boolean;
  suppressed: boolean;
  suppression_reason?: string | null;
  rationale: string;
  enforcement_tier: string;
}

export interface PolicyEvaluateResponseData {
  station_id: string;
  evaluation_timestamp: string;
  policy_state: PolicyState;
  primary_directive: string;
  resilience_state: string;
  evaluated_rules_count: number;
  active_rules: PolicyRuleTrace[];
  suppressed_rules?: PolicyRuleTrace[] | null;
  hysteresis: PolicyHysteresisState;
  optimizer_handoff: OptimizerHandoffRequirements;
  provenance: ProvenanceTier;
  diagnostics: string[];
}

// Pipeline Orchestrator
export interface PipelineStageStatus {
  stage_name: 'FORECAST' | 'SCENARIO' | 'OPTIMIZER' | 'TWIN_REPLAY' | 'RESILIENCE' | 'POLICY';
  status: 'COMPLETED' | 'SKIPPED' | 'PARTIAL' | 'FAILED';
  duration_sec: number;
  message: string;
}

export interface PipelineAnalyzeResponseData {
  pipeline_run_id: string;
  station_id: string;
  decision_trace_id?: string | null;
  horizon_hours: number;
  scenario_id?: string | null;
  overall_status: 'SUCCESS' | 'PARTIAL' | 'ERROR';
  stages: PipelineStageStatus[];
  forecast?: ForecastResponseData | null;
  scenario?: ScenarioEvaluateResponseData | null;
  optimizer?: OptimizeResponseData | null;
  resilience?: ResilienceEvaluateResponseData | null;
  policy?: PolicyEvaluateResponseData | null;
  provenance: ProvenanceTier;
}

// Phase 12 — Decision Trace & Explainability Types
export type TraceLifecycleState = 
  | 'CREATED'
  | 'RUNNING'
  | 'COMPLETED'
  | 'PARTIAL'
  | 'BLOCKED'
  | 'INFEASIBLE'
  | 'FALLBACK'
  | 'FAILED';

export type TraceStage = 
  | 'EDGE'
  | 'FORECAST'
  | 'SCENARIO'
  | 'OPTIMIZER'
  | 'TWIN_REPLAY'
  | 'RESILIENCE'
  | 'POLICY'
  | 'RECONCILIATION';

export type ValidationTier = 
  | 'REQUESTED'
  | 'COMPUTED'
  | 'SIMULATED'
  | 'VALIDATED'
  | 'ESTIMATED'
  | 'ADVISORY';

export interface TraceEventItem {
  event_id: string;
  trace_id: string;
  stage: TraceStage;
  event_type: string;
  timestamp: string;
  station_id: string;
  status: string;
  reason_code: string;
  summary: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  validation_tier: ValidationTier;
  provenance: ProvenanceTier;
  parent_event_id?: string | null;
  request_id?: string | null;
  duration_ms: number;
  engine_version: string;
  schema_version: string;
  diagnostics: string[];
}

export interface DecisionExplanation {
  trace_id: string;
  station_id: string;
  headline: string;
  why_this_state: string;
  why_this_policy: string;
  why_this_schedule: string;
  what_data_used: string[];
  what_was_validated: string[];
  what_remains_estimated: string[];
  what_is_next: string;
  reason_codes: string[];
}

export interface DecisionDelta {
  base_trace_id: string;
  compare_trace_id: string;
  station_id: string;
  state_transitions: Record<string, [string, string]>;
  numerical_deltas: Record<string, number>;
  policy_directive_changed: boolean;
  edge_mode_changed: boolean;
  summary_narrative: string;
}

export interface TraceSummary {
  decision_trace_id: string;
  station_id: string;
  pipeline_run_id?: string | null;
  request_id?: string | null;
  creation_timestamp: string;
  completion_timestamp?: string | null;
  execution_status: TraceLifecycleState;
  horizon_hours: number;
  scenario_id?: string | null;
  optimization_mode: string;
  primary_directive?: string | null;
  policy_state?: string | null;
  resilience_state?: string | null;
  edge_mode?: string | null;
  event_count: number;
  terminal_stage?: string | null;
  provenance: ProvenanceTier;
}

export interface TraceDetail extends TraceSummary {
  events: TraceEventItem[];
  lineage_graph: Record<string, string[]>;
  explanation?: DecisionExplanation | null;
  schema_version: string;
}

// Phase 11 — Edge & Device Intelligence Types
export type DataQualityState = 
  | 'VALID' 
  | 'STALE' 
  | 'MISSING' 
  | 'OUT_OF_RANGE' 
  | 'SUSPECT' 
  | 'DUPLICATE' 
  | 'OUT_OF_ORDER';

export type DeviceHealthState = 
  | 'HEALTHY' 
  | 'DEGRADED' 
  | 'UNAVAILABLE' 
  | 'FAULT' 
  | 'UNKNOWN';

export type EdgeConnectivityState = 
  | 'CONNECTED' 
  | 'DEGRADED' 
  | 'OFFLINE' 
  | 'RECONNECTING' 
  | 'UNKNOWN';

export type EdgeMode = 
  | 'CONNECTED_OPERATION' 
  | 'DEGRADED_CONNECTIVITY' 
  | 'OFFLINE_EDGE' 
  | 'RECOVERY_SYNC' 
  | 'SAFE_HOLD';

export type FallbackPosture = 
  | 'HOLD_LAST_VALIDATED_STATE' 
  | 'SAFE_HOLD' 
  | 'PROTECT_CRITICAL_SYSTEMS' 
  | 'SUSPEND_NONCRITICAL_REQUESTS' 
  | 'BUFFER_AND_FORWARD' 
  | 'REQUEST_RECONNECTION' 
  | 'WAIT_FOR_BACKEND_DECISION';

export interface DeviceChannelInfo {
  channel: string;
  unit: string;
  min_val: number;
  max_val: number;
  freshness_limit_seconds: number;
}

export interface DeviceSummary {
  device_id: string;
  station_id: string;
  device_type: string;
  name: string;
  rated_capacity?: number | null;
  unit: string;
  enabled: boolean;
  health_state: DeviceHealthState;
  connectivity_state: EdgeConnectivityState;
  provenance: ProvenanceTier;
  last_seen?: string | null;
  telemetry_channels: DeviceChannelInfo[];
  source_metadata: Record<string, any>;
}

export interface TelemetryReadingItem {
  timestamp: string;
  station_id: string;
  device_id: string;
  channel: string;
  value: number | string | boolean;
  unit: string;
  quality: DataQualityState;
  source: string;
  received_at: string;
  sequence_number?: number | null;
  provenance: ProvenanceTier;
  validation_status: string;
  diagnostics: string[];
}

export interface DeviceHealthItem {
  device_id: string;
  station_id: string;
  device_type: string;
  health_state: DeviceHealthState;
  health_score: number;
  contributing_signals: string[];
  last_seen?: string | null;
  last_valid_telemetry?: string | null;
  provenance: ProvenanceTier;
  diagnostics: string[];
}

export interface ConnectivityResponseData {
  station_id: string;
  connectivity_state: EdgeConnectivityState;
  last_successful_contact?: string | null;
  heartbeat_age_sec: number;
  packet_loss_pct: number;
  buffered_count: number;
  consecutive_failures: number;
  sync_in_progress: boolean;
  diagnostics: string[];
  provenance: ProvenanceTier;
}

export interface EdgeStateResponseData {
  station_id: string;
  edge_node_id: string;
  edge_mode: EdgeMode;
  connectivity_state: EdgeConnectivityState;
  fallback_posture: FallbackPosture;
  active_devices_count: number;
  healthy_devices_count: number;
  degraded_devices_count: number;
  fault_devices_count: number;
  buffer_depth: number;
  last_sync_time?: string | null;
  sync_freshness_sec: number;
  latest_readings: Record<string, TelemetryReadingItem>;
  quality_summary: Record<string, number>;
  health_summary: Record<string, number>;
  provenance: ProvenanceTier;
  timestamp: string;
}

export interface ReconciliationAuditItem {
  timestamp: string;
  station_id: string;
  device_id: string;
  channel: string;
  action: string;
  sequence_number?: number | null;
  reason: string;
}

export interface SyncResponseData {
  station_id: string;
  total_buffered: number;
  processed_count: number;
  duplicate_count: number;
  gap_count: number;
  conflict_count: number;
  execution_duration_ms: number;
  audit_log: ReconciliationAuditItem[];
  status: string;
  provenance: ProvenanceTier;
}

export interface EdgeEvaluateResponseData {
  station_id: string;
  pathway: string;
  edge_mode: EdgeMode;
  fallback_posture: FallbackPosture;
  action_taken: string;
  dispatch_authorized: boolean;
  buffered_telemetry_count: number;
  provenance: ProvenanceTier;
  diagnostics: string[];
}

// -----------------------------------------------------------------------------
// Digital Twin Spatial & Simulation Types (Phase 18)
// -----------------------------------------------------------------------------

export interface TwinZoneBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface TwinZone {
  id: string;
  name: string;
  label: string;
  category: 'HABITATION' | 'SCIENCE' | 'OPERATIONS' | 'POWER' | 'MECHANICAL' | 'STORAGE' | 'COMMUNICATIONS' | 'OTHER' | string;
  bounds: TwinZoneBounds;
}

export interface TwinSpatialNodePosition {
  x: number;
  y: number;
}

export interface TwinSpatialNode {
  id: string;
  kind: 'SOURCE' | 'BUS' | 'STORAGE' | 'LOAD' | 'THERMAL' | 'DEVICE' | string;
  label: string;
  zoneId?: string;
  deviceId?: string;
  circuitId?: string;
  position: TwinSpatialNodePosition;
  iconKey?: string;
  selectable: boolean;
}

export interface TwinFlowGeometry {
  type: 'polyline' | 'path';
  points?: TwinSpatialNodePosition[];
  d?: string;
}

export interface TwinSourceMix {
  solarKw: number;
  windKw: number;
  dieselKw: number;
  batteryKw: number;
}

export interface TwinFlowEdge {
  id: string;
  fromNodeId: string;
  toNodeId: string;
  circuitId?: string;
  geometry: TwinFlowGeometry;
  direction: 'FORWARD' | 'REVERSE' | 'NONE';
  powerKw: number;
  sourceMix: TwinSourceMix;
  active: boolean;
}

export interface TwinSpatialProfile {
  stationId: string;
  version: string;
  layoutStatus: 'REPRESENTATIVE' | 'CONFIGURED';
  geometryBasis: string;
  width: number;
  height: number;
  zones: TwinZone[];
  nodes: TwinSpatialNode[];
  edges: TwinFlowEdge[];
}

export interface TwinTrajectoryRequest {
  station_id: StationId | string;
  horizon_hours?: number;
  mode?: 'EXPECTED' | 'CONSERVATIVE' | 'OPTIMISTIC';
  scenario_id?: string;
  start_timestamp?: string;
}

export interface TwinTrajectoryResponseData {
  station_id: string;
  mode: string;
  steps_count: number;
  duration_hours: number;
  states: Record<string, any>[];
  summary: Record<string, any>;
  provenance: ProvenanceTier;
}

export type TwinState = Record<string, any>;
export type StationProfileDetail = StationDetail;


