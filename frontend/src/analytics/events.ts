/**
 * POLARIS-EMS ANALYTICS EVENTS DEFINITION
 * Lightweight, strictly privacy-respecting client telemetry.
 * Default behavior: NO external tracking.
 */

export type AnalyticsEventType =
  | 'view_opened'
  | 'station_changed'
  | 'forecast_horizon_changed'
  | 'scenario_opened'
  | 'optimizer_detail_expanded'
  | 'evidence_opened'
  | 'decision_trace_node_opened'
  | 'field_hil_viewed'
  | 'operator_override_attempted'
  | 'experiment_variant_assigned';

export interface AnalyticsEvent {
  type: AnalyticsEventType;
  timestamp: string;
  properties?: Record<string, any>;
}
