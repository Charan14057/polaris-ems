/**
 * POLARIS-EMS — API Endpoints
 * SIH26061: Polar Energy Management & Resilience System
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
};
