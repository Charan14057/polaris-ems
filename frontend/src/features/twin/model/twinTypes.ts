/**
 * POLARIS-EMS — Digital Twin Spatial Engine Types
 * Phase 18: Spatial Digital Twin Engine
 */

import {
  TwinSpatialProfile,
  TwinZone,
  TwinSpatialNode,
  TwinFlowEdge,
  TwinSourceMix,
  ProvenanceTier,
  StationId
} from '../../../api/types';

export type TwinViewMode = '3D_SPATIAL' | 'ARCHITECTURAL' | 'SCHEMATIC' | 'ACCESSIBLE_TABLE';

export type TwinDeviceFilter = 
  | 'ALL' 
  | 'CRITICAL' 
  | 'ACTIVE' 
  | 'FAULTED' 
  | 'GENERATION' 
  | 'STORAGE' 
  | 'LOADS' 
  | 'THERMAL';

export interface VisualDeviceState {
  id: string;
  name: string;
  category: 'CRITICAL' | 'IMPORTANT' | 'OPERATIONAL' | 'FLEXIBLE' | string;
  priorityRank: number;
  nominalPowerKw: number;
  currentPowerKw: number;
  currentAmps: number | null; // null if missing or derived
  nominalVoltageV: number;
  status: 'ONLINE' | 'STANDBY' | 'DEFERRED' | 'FAULT' | 'OFF';
  zoneId: string;
  zoneName: string;
  circuitId: string;
  deferrable: boolean;
  thermalConsequence: string;
  provenance: ProvenanceTier;
  whatItDoes: string;
  whyItMatters: string;
  upstreamNodeIds: string[];
  upstreamEdgeIds: string[];
}

export interface VisualEdgeState extends TwinFlowEdge {
  hasDieselContribution: boolean;
  isRenewableDominant: boolean;
  isBatteryCharge: boolean;
  isBatteryDischarge: boolean;
  flowSemantic: 'RENEWABLE' | 'NON_RENEWABLE' | 'BATTERY' | 'DORMANT' | 'FAULT';
  lineWidthPx: number;
  highlighted: boolean;
  dimmed: boolean;
}

export interface VisualZoneState extends TwinZone {
  totalLoadKw: number;
  criticalLoadKw: number;
  connectedDeviceCount: number;
  activeDeviceCount: number;
  hasFault: boolean;
  highlighted: boolean;
}

export interface TimelineMarker {
  stepIndex: number;
  timeLabel: string;
  title: string;
  description: string;
  kind: 'SOLAR_PEAK' | 'WIND_SHIFT' | 'GENERATOR_START' | 'BATTERY_CYCLE' | 'STORM_EVENT' | 'FAULT_EVENT' | 'OPTIMAL_POINT';
}

export interface TwinViewModel {
  stationId: string;
  timestamp: string;
  viewMode: TwinViewMode;
  layoutStatus: 'REPRESENTATIVE' | 'CONFIGURED';
  geometryBasis: string;
  dimensions: { width: number; height: number };

  // Subsystem Generation & Consumption
  powerSummary: {
    totalGenerationKw: number;
    solarGenerationKw: number;
    windGenerationKw: number;
    dieselGenerationKw: number;
    batteryPowerKw: number; // positive = discharge, negative = charge
    batterySocPct: number;
    totalLoadKw: number;
    servedLoadKw: number;
    unservedLoadKw: number;
    criticalLoadKw: number;
    renewableFractionPct: number;
    dominantSource: 'RENEWABLE' | 'BATTERY' | 'DIESEL' | 'BALANCED';
    conservationGapKw: number;
  };

  // Environmental & Building Thermal
  environment: {
    ambientTempC: number;
    windSpeedMs: number;
    irradianceWm2: number;
    stormState: string;
  };

  thermal: {
    indoorTempC: number;
    targetTempC: number;
    minSafeTempC: number;
    isSafe: boolean;
    heatingPowerKw: number;
  };

  resilience: {
    threatState: 'SAFE' | 'AT_RISK' | 'THREATENED' | 'CRITICAL' | string;
    survivalHorizonHours: number;
    limitingResource: string;
  };

  // Visual Geometry Entities
  zones: VisualZoneState[];
  nodes: TwinSpatialNode[];
  edges: VisualEdgeState[];
  devices: Record<string, VisualDeviceState>;

  // Selection & Tracing
  selectedNodeId: string | null;
  selectedZoneId: string | null;
  selectedDeviceId: string | null;
  tracedPathEdgeIds: Set<string>;
  tracedPathNodeIds: Set<string>;
  activeFaultCircuitIds: Set<string>;

  // Provenance
  provenance: ProvenanceTier;
}
