/**
 * POLARIS-EMS — API Endpoints
 * Polaris-EMS — Polar Energy Management & Resilience System
 * 
 * Provides typed functions mapping to Phase 9 FastAPI endpoints.
 */

import { apiRequest } from './client';
import {
  ReadinessResponse,
  CapabilitiesResponse,
  StationSummary,
  StationDetail,
  ForecastResponseData,
  ScenarioSummary,
  ScenarioDetail,
  ScenarioEvaluateResponseData,
  OptimizeResponseData,
  ResilienceEvaluateResponseData,
  PolicyEvaluateResponseData,
  PipelineAnalyzeResponseData,
  StationId,
} from './types';

export const api = {
  // Health
  getReadiness: () => 
    apiRequest<ReadinessResponse>('/health/ready'),

  getCapabilities: () => 
    apiRequest<CapabilitiesResponse>('/health/capabilities'),

  // Stations
  listStations: () => 
    apiRequest<StationSummary[]>('/api/v1/stations'),

  getStationDetail: (stationId: StationId | string) => 
    apiRequest<StationDetail>(`/api/v1/stations/${stationId.toUpperCase()}`),

  // Forecast
  getForecast: (params: {
    station_id: StationId | string;
    target: 'total_load_kw' | 'solar_generation_kw' | 'wind_generation_kw';
    horizon_hours?: number;
    forecast_origin?: string;
  }) => 
    apiRequest<ForecastResponseData>('/api/v1/forecast', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Scenarios
  listScenarios: () => 
    apiRequest<ScenarioSummary[]>('/api/v1/scenarios'),

  getScenarioDetail: (scenarioId: string) => 
    apiRequest<ScenarioDetail>(`/api/v1/scenarios/${scenarioId.toUpperCase()}`),

  evaluateScenario: (params: {
    station_id: StationId | string;
    scenario_id: string;
    horizon_hours?: number;
    forecast_mode?: string;
    start_timestamp?: string;
    include_trajectory?: boolean;
  }) => 
    apiRequest<ScenarioEvaluateResponseData>('/api/v1/scenarios/evaluate', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Optimizer
  optimizeMicrogrid: (params: {
    station_id: StationId | string;
    horizon_hours?: number;
    mode?: 'EXPECTED' | 'CONSERVATIVE' | 'SCENARIO_ROBUST';
    generator_overrides?: Record<number, string>;
    scenario_id?: string;
    start_timestamp?: string;
    include_schedule?: boolean;
  }) => 
    apiRequest<OptimizeResponseData>('/api/v1/optimize', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Resilience
  evaluateResilience: (params: {
    station_id: StationId | string;
    horizon_hours?: number;
    scenario_id?: string;
    include_propagation?: boolean;
  }) => 
    apiRequest<ResilienceEvaluateResponseData>('/api/v1/resilience/evaluate', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Policy
  evaluatePolicy: (params: {
    station_id: StationId | string;
    horizon_hours?: number;
    scenario_id?: string;
    include_suppressed?: boolean;
    include_evaluation_trace?: boolean;
  }) => 
    apiRequest<PolicyEvaluateResponseData>('/api/v1/policy/evaluate', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  getPolicyTrace: (traceId: string) => 
    apiRequest<any>(`/api/v1/policy/trace/${traceId}`),

  // Pipeline Orchestration
  analyzePipeline: (params: {
    station_id: StationId | string;
    horizon_hours: number;
    scenario_id?: string;
    mode?: 'EXPECTED' | 'CONSERVATIVE' | 'SCENARIO_ROBUST';
    generator_overrides?: Record<number, string>;
  }) => 
    apiRequest<PipelineAnalyzeResponseData>('/api/v1/pipeline/analyze', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Phase 12 — Decision Trace & Audit Endpoints
  listTraces: (params?: { station_id?: string; status?: string; policy_state?: string; resilience_state?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.station_id) q.set('station_id', params.station_id);
    if (params?.status) q.set('status', params.status);
    if (params?.policy_state) q.set('policy_state', params.policy_state);
    if (params?.resilience_state) q.set('resilience_state', params.resilience_state);
    if (params?.limit) q.set('limit', String(params.limit));
    const qs = q.toString();
    return apiRequest<import('./types').TraceSummary[]>(`/api/v1/traces${qs ? `?${qs}` : ''}`);
  },

  getTrace: (traceId: string) =>
    apiRequest<import('./types').TraceDetail>(`/api/v1/traces/${traceId}`),

  getTraceEvents: (traceId: string) =>
    apiRequest<import('./types').TraceEventItem[]>(`/api/v1/traces/${traceId}/events`),

  getTraceSummary: (traceId: string) =>
    apiRequest<import('./types').TraceSummary>(`/api/v1/traces/${traceId}/summary`),

  getTraceExplanation: (traceId: string) =>
    apiRequest<import('./types').DecisionExplanation>(`/api/v1/traces/${traceId}/explanation`),

  compareTraces: (baseTraceId: string, compareTraceId: string) =>
    apiRequest<import('./types').DecisionDelta>(`/api/v1/traces/${baseTraceId}/compare/${compareTraceId}`),

  exportTrace: (traceId: string, format: 'json' | 'csv' = 'json') =>
    fetch(`/api/v1/traces/${traceId}/export?format=${format}`).then(r => r.text()),

  // Phase 18 — Digital Twin Spatial & Simulation Endpoints
  getTwinSpatialProfile: (stationId: StationId | string) =>
    apiRequest<import('./types').TwinSpatialProfile>(`/api/v1/twin/spatial/${stationId.toUpperCase()}`),

  getTwinCurrentState: (stationId: StationId | string, timestamp?: string) => {
    const qs = timestamp ? `?timestamp=${encodeURIComponent(timestamp)}` : '';
    return apiRequest<Record<string, any>>(`/api/v1/twin/state/${stationId.toUpperCase()}${qs}`);
  },

  simulateTwinTrajectory: (params: import('./types').TwinTrajectoryRequest) =>
    apiRequest<import('./types').TwinTrajectoryResponseData>('/api/v1/twin/trajectory', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
};
