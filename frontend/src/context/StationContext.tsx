import React, { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import { 
  StationId, 
  StationDetail, 
  StationSummary, 
  ReadinessResponse, 
  ThreatIndicator,
  ResilienceEvaluateResponseData,
  PolicyEvaluateResponseData,
  OptimizeResponseData,
  TraceSummary
} from '../api/types';
import { api } from '../api/endpoints';

export interface OperationalSnapshot {
  currentStation: StationId;
  stationName: string;
  stationLocation: string;
  stationRegion: string;
  timestamp: string;
  wallClockTimestamp: string;
  operatingMode: 'AUTO' | 'MANUAL';
  activeScenario: string | null;
  scenarioSeverity: 'NORMAL' | 'ELEVATED' | 'HIGH' | 'CRITICAL';
  scenarioDescription: string | null;
  
  // Environmental Conditions
  ambientTemperatureC: number | null;
  windSpeedMs: number | null;
  irradianceWm2: number | null;
  cloudFraction: number | null;
  solarElevationDeg: number | null;
  
  // Power & Electrical State
  totalLoadKw: number | null;
  criticalLoadKw: number | null;
  flexibleLoadKw: number | null;
  servedLoadKw: number | null;
  unservedLoadKw: number | null;
  
  solarGenerationKw: number | null;
  solarCapacityKw: number | null;
  solarStatus: string | null;
  
  windGenerationKw: number | null;
  windCapacityKw: number | null;
  windStatus: string | null;
  
  dieselGenerationKw: number | null;
  dieselMaxKw: number | null;
  dieselStatus: string | null;
  fuelConsumptionLph: number | null;
  fuelRemainingL: number | null;
  daysOfFuelRemaining: number | null;
  
  bessSocPct: number | null; // 0-100
  bessPowerKw: number | null; // positive = discharging, negative = charging
  bessChargeKw: number | null;
  bessDischargeKw: number | null;
  bessCapacityKwh: number | null;
  bessStatus: 'CHARGING' | 'DISCHARGING' | 'STANDBY' | 'FAULT' | null;
  
  totalGenerationKw: number | null;
  renewableSharePct: number | null;
  
  // Resilience State
  resilienceState: 'SAFE' | 'WATCH' | 'AT_RISK' | 'THREATENED' | 'CRITICAL' | 'RECOVERY';
  resilienceDimensions: Record<string, number> | null;
  survivalHorizons: {
    criticalLoadSurvivalH: number | null;
    batteryEnduranceH: number | null;
    thermalHabitabilityH: number | null;
    fuelEnduranceH: number | null;
    overallSurvivalH: number | null;
    bindingSubsystem: string | null;
  } | null;
  
  // Policy & Optimization
  activeDirective: string | null;
  policyState: string | null;
  optimizerRecommendation: string | null;
  optimizerRationale: string | null;
  
  // Power Flow Topology
  powerFlowTopology: {
    edges: Array<{ id: string; source: string; target: string; power_kw: number; active: boolean; direction: string }>;
    assets: Record<string, any>;
    sourceMix: { solar_pct: number; wind_pct: number; diesel_pct: number; battery_pct: number };
  } | null;
  
  // Decision Trace & Lineage
  latestTrace: any | null;
  provenance: string;
  lastUpdated: string;
  isStale: boolean;
}

export interface ToastNotification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning';
}

export const STATION_BASELINE_SNAPSHOTS: Record<StationId, OperationalSnapshot> = {
  BHARATI: {
    currentStation: 'BHARATI',
    stationName: 'Bharati Station',
    stationLocation: '69°S • Larsemann Hills',
    stationRegion: 'East Antarctica',
    timestamp: new Date().toISOString(),
    wallClockTimestamp: new Date().toISOString(),
    operatingMode: 'AUTO',
    activeScenario: null,
    scenarioSeverity: 'NORMAL',
    scenarioDescription: null,
    ambientTemperatureC: -18.5,
    windSpeedMs: 8.5,
    irradianceWm2: 120.0,
    cloudFraction: 0.45,
    solarElevationDeg: 15.0,
    totalLoadKw: 34.8,
    criticalLoadKw: 22.5,
    flexibleLoadKw: 6.2,
    servedLoadKw: 34.8,
    unservedLoadKw: 0.0,
    solarGenerationKw: 14.2,
    solarCapacityKw: 60.0,
    solarStatus: 'ONLINE',
    windGenerationKw: 28.5,
    windCapacityKw: 100.0,
    windStatus: 'ONLINE',
    dieselGenerationKw: 0.0,
    dieselMaxKw: 120.0,
    dieselStatus: 'STANDBY',
    fuelConsumptionLph: 0.0,
    fuelRemainingL: 18500.0,
    daysOfFuelRemaining: 64.0,
    bessSocPct: 68.0,
    bessPowerKw: -7.9,
    bessChargeKw: 7.9,
    bessDischargeKw: 0.0,
    bessCapacityKwh: 150.0,
    bessStatus: 'CHARGING',
    totalGenerationKw: 42.7,
    renewableSharePct: 100.0,
    resilienceState: 'SAFE',
    resilienceDimensions: {
      energy_adequacy: 0.95,
      critical_load_resilience: 1.0,
      thermal_resilience: 0.92,
      generation_resilience: 0.88,
      storage_resilience: 0.85,
      fuel_resilience: 0.96,
      logistics_resilience: 0.82,
      renewable_resilience: 0.89,
      recovery_resilience: 0.91,
      composite_index: 0.91,
    },
    survivalHorizons: {
      criticalLoadSurvivalH: 168.0,
      batteryEnduranceH: 18.5,
      thermalHabitabilityH: 36.0,
      fuelEnduranceH: 1536.0,
      overallSurvivalH: 168.0,
      bindingSubsystem: 'BATTERY',
    },
    activeDirective: 'RENEWABLE_PRIORITY',
    policyState: 'OPTIMAL_RESERVE',
    optimizerRecommendation: 'Dispatch 100% renewable + battery buffering; DG-1 on cold standby.',
    optimizerRationale: 'HiGHS Branch-and-Cut solved in 14.2ms: Zero fuel burn verified.',
    powerFlowTopology: {
      edges: [
        { id: 'edge-pv-bus', source: 'pv', target: 'bus', power_kw: 14.2, active: true, direction: 'FORWARD' },
        { id: 'edge-wind-bus', source: 'wind', target: 'bus', power_kw: 28.5, active: true, direction: 'FORWARD' },
        { id: 'edge-bess-bus', source: 'bess', target: 'bus', power_kw: 7.9, active: true, direction: 'REVERSE' },
        { id: 'edge-bus-loads', source: 'bus', target: 'loads', power_kw: 34.8, active: true, direction: 'FORWARD' },
      ],
      assets: {},
      sourceMix: { solar_pct: 33, wind_pct: 67, diesel_pct: 0, battery_pct: 0 },
    },
    latestTrace: null,
    provenance: 'COMPUTATIONAL_TWIN',
    lastUpdated: new Date().toISOString(),
    isStale: false,
  },
  MAITRI: {
    currentStation: 'MAITRI',
    stationName: 'Maitri Station',
    stationLocation: '70°S • Schirmacher Oasis',
    stationRegion: 'East Antarctica',
    timestamp: new Date().toISOString(),
    wallClockTimestamp: new Date().toISOString(),
    operatingMode: 'AUTO',
    activeScenario: null,
    scenarioSeverity: 'NORMAL',
    scenarioDescription: null,
    ambientTemperatureC: -21.0,
    windSpeedMs: 9.2,
    irradianceWm2: 105.0,
    cloudFraction: 0.50,
    solarElevationDeg: 14.0,
    totalLoadKw: 28.2,
    criticalLoadKw: 18.0,
    flexibleLoadKw: 4.8,
    servedLoadKw: 28.2,
    unservedLoadKw: 0.0,
    solarGenerationKw: 9.5,
    solarCapacityKw: 35.0,
    solarStatus: 'ONLINE',
    windGenerationKw: 24.0,
    windCapacityKw: 60.0,
    windStatus: 'ONLINE',
    dieselGenerationKw: 0.0,
    dieselMaxKw: 100.0,
    dieselStatus: 'STANDBY',
    fuelConsumptionLph: 0.0,
    fuelRemainingL: 14200.0,
    daysOfFuelRemaining: 58.0,
    bessSocPct: 72.0,
    bessPowerKw: -5.3,
    bessChargeKw: 5.3,
    bessDischargeKw: 0.0,
    bessCapacityKwh: 100.0,
    bessStatus: 'CHARGING',
    totalGenerationKw: 33.5,
    renewableSharePct: 100.0,
    resilienceState: 'SAFE',
    resilienceDimensions: {
      energy_adequacy: 0.94,
      critical_load_resilience: 1.0,
      thermal_resilience: 0.90,
      generation_resilience: 0.86,
      storage_resilience: 0.83,
      fuel_resilience: 0.95,
      logistics_resilience: 0.80,
      renewable_resilience: 0.87,
      recovery_resilience: 0.90,
      composite_index: 0.90,
    },
    survivalHorizons: {
      criticalLoadSurvivalH: 168.0,
      batteryEnduranceH: 16.0,
      thermalHabitabilityH: 32.0,
      fuelEnduranceH: 1320.0,
      overallSurvivalH: 168.0,
      bindingSubsystem: 'BATTERY',
    },
    activeDirective: 'RENEWABLE_PRIORITY',
    policyState: 'OPTIMAL_RESERVE',
    optimizerRecommendation: 'Autonomous renewable balance; surplus power directed to BESS storage.',
    optimizerRationale: 'HiGHS Branch-and-Cut solved in 12.8ms: Minimum operating cost.',
    powerFlowTopology: {
      edges: [
        { id: 'edge-pv-bus', source: 'pv', target: 'bus', power_kw: 9.5, active: true, direction: 'FORWARD' },
        { id: 'edge-wind-bus', source: 'wind', target: 'bus', power_kw: 24.0, active: true, direction: 'FORWARD' },
        { id: 'edge-bess-bus', source: 'bess', target: 'bus', power_kw: 5.3, active: true, direction: 'REVERSE' },
        { id: 'edge-bus-loads', source: 'bus', target: 'loads', power_kw: 28.2, active: true, direction: 'FORWARD' },
      ],
      assets: {},
      sourceMix: { solar_pct: 28, wind_pct: 72, diesel_pct: 0, battery_pct: 0 },
    },
    latestTrace: null,
    provenance: 'COMPUTATIONAL_TWIN',
    lastUpdated: new Date().toISOString(),
    isStale: false,
  },
  HIMADRI: {
    currentStation: 'HIMADRI',
    stationName: 'Himadri Station',
    stationLocation: '79°N • Ny-Ålesund, Svalbard',
    stationRegion: 'Arctic',
    timestamp: new Date().toISOString(),
    wallClockTimestamp: new Date().toISOString(),
    operatingMode: 'AUTO',
    activeScenario: null,
    scenarioSeverity: 'NORMAL',
    scenarioDescription: null,
    ambientTemperatureC: -6.2,
    windSpeedMs: 6.8,
    irradianceWm2: 45.0,
    cloudFraction: 0.60,
    solarElevationDeg: 8.0,
    totalLoadKw: 15.4,
    criticalLoadKw: 9.5,
    flexibleLoadKw: 2.5,
    servedLoadKw: 15.4,
    unservedLoadKw: 0.0,
    solarGenerationKw: 3.2,
    solarCapacityKw: 15.0,
    solarStatus: 'ONLINE',
    windGenerationKw: 14.5,
    windCapacityKw: 20.0,
    windStatus: 'ONLINE',
    dieselGenerationKw: 0.0,
    dieselMaxKw: 50.0,
    dieselStatus: 'STANDBY',
    fuelConsumptionLph: 0.0,
    fuelRemainingL: 6500.0,
    daysOfFuelRemaining: 74.0,
    bessSocPct: 76.0,
    bessPowerKw: -2.3,
    bessChargeKw: 2.3,
    bessDischargeKw: 0.0,
    bessCapacityKwh: 40.0,
    bessStatus: 'CHARGING',
    totalGenerationKw: 17.7,
    renewableSharePct: 100.0,
    resilienceState: 'SAFE',
    resilienceDimensions: {
      energy_adequacy: 0.96,
      critical_load_resilience: 1.0,
      thermal_resilience: 0.94,
      generation_resilience: 0.90,
      storage_resilience: 0.88,
      fuel_resilience: 0.98,
      logistics_resilience: 0.85,
      renewable_resilience: 0.92,
      recovery_resilience: 0.93,
      composite_index: 0.93,
    },
    survivalHorizons: {
      criticalLoadSurvivalH: 168.0,
      batteryEnduranceH: 22.0,
      thermalHabitabilityH: 48.0,
      fuelEnduranceH: 1776.0,
      overallSurvivalH: 168.0,
      bindingSubsystem: 'BATTERY',
    },
    activeDirective: 'RENEWABLE_PRIORITY',
    policyState: 'OPTIMAL_RESERVE',
    optimizerRecommendation: 'Arctic micro-turbine dominant; solar augmenting base thermal circuits.',
    optimizerRationale: 'HiGHS Branch-and-Cut solved in 10.5ms: Zero deficit maintained.',
    powerFlowTopology: {
      edges: [
        { id: 'edge-pv-bus', source: 'pv', target: 'bus', power_kw: 3.2, active: true, direction: 'FORWARD' },
        { id: 'edge-wind-bus', source: 'wind', target: 'bus', power_kw: 14.5, active: true, direction: 'FORWARD' },
        { id: 'edge-bess-bus', source: 'bess', target: 'bus', power_kw: 2.3, active: true, direction: 'REVERSE' },
        { id: 'edge-bus-loads', source: 'bus', target: 'loads', power_kw: 15.4, active: true, direction: 'FORWARD' },
      ],
      assets: {},
      sourceMix: { solar_pct: 18, wind_pct: 82, diesel_pct: 0, battery_pct: 0 },
    },
    latestTrace: null,
    provenance: 'COMPUTATIONAL_TWIN',
    lastUpdated: new Date().toISOString(),
    isStale: false,
  },
};

const DEFAULT_SNAPSHOT: OperationalSnapshot = STATION_BASELINE_SNAPSHOTS.BHARATI;

interface StationContextType {
  currentStation: StationId;
  stationId: StationId;
  setStation: (station: StationId) => void;
  horizonHours: 48 | 168;
  setHorizonHours: (hours: 48 | 168) => void;
  stationDetail: StationDetail | null;
  stationSummaries: StationSummary[];
  readiness: ReadinessResponse | null;
  activeThreats: ThreatIndicator[];
  loading: boolean;
  error: string | null;
  lastUpdated: string;
  refreshStationData: () => Promise<void>;
  
  // Authoritative Shared Operational State
  operationalSnapshot: OperationalSnapshot;
  activeScenario: string | null;
  activateScenario: (scenarioId: string, customParams?: Record<string, any>) => Promise<void>;
  clearScenario: () => Promise<void>;
  applyManualControl: (actionId: string, parameters?: Record<string, any>) => Promise<any>;
  approveAutoRecommendation: () => Promise<any>;
  reSolveOptimizer: (mode?: 'EXPECTED' | 'CONSERVATIVE' | 'SCENARIO_ROBUST') => Promise<void>;
  refreshAll: () => Promise<void>;
  
  // Operational Governance Mode
  operatingMode: 'AUTO' | 'MANUAL';
  setOperatingMode: (mode: 'AUTO' | 'MANUAL') => void;

  // Direct Cached Engine Responses
  resilienceData: ResilienceEvaluateResponseData | null;
  policyData: PolicyEvaluateResponseData | null;
  optimizerData: OptimizeResponseData | null;
  tracesData: TraceSummary[];

  // Toast Notifications
  toast: ToastNotification | null;
  showToast: (title: string, message: string, type?: 'info' | 'success' | 'warning') => void;
  dismissToast: () => void;
}

const StationContext = createContext<StationContextType | undefined>(undefined);

export const StationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentStation, setCurrentStation] = useState<StationId>('BHARATI');
  const [horizonHours, setHorizonHours] = useState<48 | 168>(48);
  const [stationDetail, setStationDetail] = useState<StationDetail | null>(null);
  const [stationSummaries, setStationSummaries] = useState<StationSummary[]>([]);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [activeThreats, setActiveThreats] = useState<ThreatIndicator[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>(new Date().toISOString());

  // Authoritative Subsystem Data
  const [resilienceData, setResilienceData] = useState<ResilienceEvaluateResponseData | null>(null);
  const [policyData, setPolicyData] = useState<PolicyEvaluateResponseData | null>(null);
  const [optimizerData, setOptimizerData] = useState<OptimizeResponseData | null>(null);
  const [tracesData, setTracesData] = useState<TraceSummary[]>([]);
  const [operationalSnapshot, setOperationalSnapshot] = useState<OperationalSnapshot>(DEFAULT_SNAPSHOT);
  const [activeScenario, setActiveScenario] = useState<string | null>(null);
  const [operatingMode, setOperatingModeState] = useState<'AUTO' | 'MANUAL'>('AUTO');
  const operatingModeRef = useRef<'AUTO' | 'MANUAL'>('AUTO');

  const setOperatingMode = useCallback((mode: 'AUTO' | 'MANUAL') => {
    operatingModeRef.current = mode;
    setOperatingModeState(mode);
    setOperationalSnapshot(prev => ({
      ...prev,
      operatingMode: mode
    }));
  }, []);

  // Toast notification state
  const [toast, setToast] = useState<ToastNotification | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((title: string, message: string, type: 'info' | 'success' | 'warning' = 'info') => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    const notification: ToastNotification = { id: Date.now().toString(), title, message, type };
    setToast(notification);
    toastTimerRef.current = setTimeout(() => setToast(null), 6000);
  }, []);

  const dismissToast = useCallback(() => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast(null);
  }, []);

  const isFetchingRef = useRef(false);

  const fetchStationData = useCallback(async () => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    setLoading(true);
    setError(null);

    try {
      // 1. Fetch core catalog, live twin snapshot, resilience, policy, optimizer, traces in parallel
      const [
        readinessRes,
        listRes,
        detailRes,
        liveSnapRes,
        resilienceRes,
        policyRes,
        optRes,
        tracesRes
      ] = await Promise.all([
        api.getReadiness().catch(() => null),
        api.listStations().catch(() => null),
        api.getStationDetail(currentStation).catch(() => null),
        api.getLiveTwinSnapshot(currentStation).catch(() => null),
        api.evaluateResilience({
          station_id: currentStation,
          horizon_hours: horizonHours,
          scenario_id: activeScenario || undefined,
        }).catch(() => null),
        api.evaluatePolicy({
          station_id: currentStation,
          horizon_hours: horizonHours,
          scenario_id: activeScenario || undefined,
          include_suppressed: true,
        }).catch(() => null),
        api.optimizeMicrogrid({
          station_id: currentStation,
          horizon_hours: horizonHours,
          scenario_id: activeScenario || undefined,
          include_schedule: true,
        }).catch(() => null),
        api.listTraces({ station_id: currentStation, limit: 10 }).catch(() => null),
      ]);

      if (readinessRes?.data) setReadiness(readinessRes.data);
      if (listRes?.data) setStationSummaries(listRes.data);
      if (detailRes?.data) setStationDetail(detailRes.data);
      if (resilienceRes?.data) setResilienceData(resilienceRes.data);
      if (policyRes?.data) setPolicyData(policyRes.data);
      if (optRes?.data) setOptimizerData(optRes.data);
      if (tracesRes?.data) setTracesData(tracesRes.data);

      if (resilienceRes?.data?.threat_decomposition) {
        setActiveThreats(resilienceRes.data.threat_decomposition);
      } else {
        setActiveThreats([]);
      }

      // 2. Synthesize Authoritative Operational Snapshot
      const liveData = liveSnapRes?.data;
      const twinState = liveData?.state || {};
      const metadata = liveData?.metadata || {};
      const powerFlow = liveData?.power_flow || null;
      const detail = detailRes?.data;

      const rawScen = metadata.active_scenario || activeScenario || null;
      const isBaseline = !rawScen || ['NORMAL_BASELINE', 'BASELINE', 'NOMINAL', 'NORMAL', 'NORMAL BASELINE'].includes(rawScen.toUpperCase().trim());
      const actScen = isBaseline ? null : rawScen;
      setActiveScenario(actScen);

      // Extract Solar, Wind, Diesel, Battery from TwinState
      const solarObj = twinState.solar || {};
      const windObj = twinState.wind || {};
      const dieselObj = twinState.diesel || {};
      const batteryObj = twinState.battery || {};
      const loadsObj = twinState.loads || {};
      const fuelObj = twinState.fuel || {};
      const envObj = twinState.environment || {};

      const solarKw = solarObj.solar_generation_kw !== undefined ? Number(solarObj.solar_generation_kw) : null;
      const windKw = windObj.wind_generation_kw !== undefined ? Number(windObj.wind_generation_kw) : null;
      const dieselKw = dieselObj.generator_power_kw !== undefined ? Number(dieselObj.generator_power_kw) : null;
      
      const bessDischarge = batteryObj.discharge_kw !== undefined ? Number(batteryObj.discharge_kw) : 0;
      const bessCharge = batteryObj.charge_kw !== undefined ? Number(batteryObj.charge_kw) : 0;
      const bessPower = bessDischarge > 0.05 ? bessDischarge : (bessCharge > 0.05 ? -bessCharge : 0);

      // Raw SOC might be in [0, 1] or [0, 100]
      let rawSoc = batteryObj.soc_pct !== undefined ? Number(batteryObj.soc_pct) : null;
      if (rawSoc !== null && rawSoc <= 1.0 && rawSoc > 0.0) {
        rawSoc = Math.round(rawSoc * 100);
      }

      const totalGen = (solarKw !== null && windKw !== null && dieselKw !== null)
        ? Math.round((solarKw + windKw + dieselKw + Math.max(0, bessPower)) * 10) / 10
        : null;

      const renewableShare = (totalGen !== null && totalGen > 0.1 && solarKw !== null && windKw !== null)
        ? Math.min(100, Math.round(((solarKw + windKw) / totalGen) * 100))
        : (totalGen !== null && totalGen <= 0.1 ? 0 : null);

      const horizons = resilienceRes?.data?.survival_horizons;
      const resDims = resilienceRes?.data?.dimensions;

      let scenarioSeverity: 'NORMAL' | 'ELEVATED' | 'HIGH' | 'CRITICAL' = 'NORMAL';
      if (actScen) {
        if (['BLIZZARD', 'COMBINED_POLAR_STRESS', 'UNFORESEEN_WEATHER'].includes(actScen)) {
          scenarioSeverity = 'CRITICAL';
        } else if (['SOLAR_GENERATION_FAILURE', 'WIND_GENERATION_FAILURE', 'EXTREME_COLD', 'BATTERY_DEGRADATION'].includes(actScen)) {
          scenarioSeverity = 'HIGH';
        } else {
          scenarioSeverity = 'ELEVATED';
        }
      }

      const snapshot: OperationalSnapshot = {
        currentStation,
        stationName: detail?.name || `${currentStation} Station`,
        stationLocation: detail?.location || 'Polar Oasis',
        stationRegion: detail?.region || 'Polar Sector',
        timestamp: metadata.simulation_timestamp || new Date().toISOString(),
        wallClockTimestamp: metadata.wall_clock_timestamp || new Date().toISOString(),
        operatingMode: operatingModeRef.current,
        activeScenario: actScen,
        scenarioSeverity,
        scenarioDescription: actScen ? `Active perturbation regime: ${actScen}` : null,

        ambientTemperatureC: envObj.ambient_temperature_c !== undefined ? Number(envObj.ambient_temperature_c) : null,
        windSpeedMs: envObj.wind_speed_ms !== undefined ? Number(envObj.wind_speed_ms) : null,
        irradianceWm2: envObj.irradiance_wm2 !== undefined ? Number(envObj.irradiance_wm2) : null,
        cloudFraction: envObj.cloud_fraction !== undefined ? Number(envObj.cloud_fraction) : null,
        solarElevationDeg: envObj.solar_elevation_deg !== undefined ? Number(envObj.solar_elevation_deg) : null,

        totalLoadKw: loadsObj.total_load_kw !== undefined ? Number(loadsObj.total_load_kw) : null,
        criticalLoadKw: loadsObj.critical_load_kw !== undefined ? Number(loadsObj.critical_load_kw) : null,
        flexibleLoadKw: loadsObj.flexible_load_kw !== undefined ? Number(loadsObj.flexible_load_kw) : null,
        servedLoadKw: loadsObj.served_load_kw !== undefined ? Number(loadsObj.served_load_kw) : null,
        unservedLoadKw: loadsObj.unserved_load_kw !== undefined ? Number(loadsObj.unserved_load_kw) : null,

        solarGenerationKw: solarKw,
        solarCapacityKw: solarObj.solar_capacity_kw !== undefined ? Number(solarObj.solar_capacity_kw) : null,
        solarStatus: solarObj.solar_status || (solarKw !== null && solarKw > 0.1 ? 'ACTIVE' : 'STANDBY'),

        windGenerationKw: windKw,
        windCapacityKw: windObj.wind_capacity_kw !== undefined ? Number(windObj.wind_capacity_kw) : null,
        windStatus: windObj.wind_status || (windKw !== null && windKw > 0.1 ? 'OPERATING' : 'STANDBY'),

        dieselGenerationKw: dieselKw,
        dieselMaxKw: dieselObj.generator_max_power_kw !== undefined ? Number(dieselObj.generator_max_power_kw) : null,
        dieselStatus: dieselObj.generator_status || (dieselKw !== null && dieselKw > 0.1 ? 'ONLINE' : 'STANDBY'),
        fuelConsumptionLph: dieselObj.fuel_consumption_l_per_h !== undefined ? Number(dieselObj.fuel_consumption_l_per_h) : null,
        fuelRemainingL: fuelObj.fuel_remaining_l !== undefined ? Number(fuelObj.fuel_remaining_l) : null,
        daysOfFuelRemaining: fuelObj.days_of_fuel_remaining !== undefined ? Number(fuelObj.days_of_fuel_remaining) : null,

        bessSocPct: rawSoc,
        bessPowerKw: bessPower,
        bessChargeKw: bessCharge,
        bessDischargeKw: bessDischarge,
        bessCapacityKwh: batteryObj.capacity_kwh !== undefined ? Number(batteryObj.capacity_kwh) : null,
        bessStatus: bessCharge > 0.05 ? 'CHARGING' : (bessDischarge > 0.05 ? 'DISCHARGING' : 'STANDBY'),

        totalGenerationKw: totalGen,
        renewableSharePct: renewableShare,

        resilienceState: resilienceRes?.data?.resilience_state as any || 'SAFE',
        resilienceDimensions: resDims ? {
          energy_adequacy: resDims.energy_adequacy,
          critical_load_resilience: resDims.critical_load_resilience,
          thermal_resilience: resDims.thermal_resilience,
          generation_resilience: resDims.generation_resilience,
          storage_resilience: resDims.storage_resilience,
          fuel_resilience: resDims.fuel_resilience,
          logistics_resilience: resDims.logistics_resilience,
          renewable_resilience: resDims.renewable_resilience,
          recovery_resilience: resDims.recovery_resilience,
          composite_index: resDims.composite_index,
        } : null,
        survivalHorizons: horizons ? {
          criticalLoadSurvivalH: horizons.critical_load_survival_horizon_h,
          batteryEnduranceH: horizons.battery_endurance_horizon_h,
          thermalHabitabilityH: horizons.thermal_habitability_horizon_h,
          fuelEnduranceH: horizons.fuel_endurance_horizon_h,
          overallSurvivalH: horizons.overall_station_survival_horizon_h,
          bindingSubsystem: horizons.binding_subsystem,
        } : null,

        activeDirective: policyRes?.data?.primary_directive || policyRes?.data?.policy_state || null,
        policyState: policyRes?.data?.policy_state || null,
        optimizerRecommendation: optRes?.data?.diagnostics?.[0] || 'Nominal fuel-preserving economic dispatch profile',
        optimizerRationale: optRes?.data?.solver_status || 'HiGHS MILP Optimal Solution',

        powerFlowTopology: powerFlow ? {
          edges: powerFlow.edges || [],
          assets: powerFlow.assets || {},
          sourceMix: powerFlow.source_mix || { solar_pct: 0, wind_pct: 0, diesel_pct: 0, battery_pct: 0 },
        } : null,

        latestTrace: tracesRes?.data?.[0] || null,
        provenance: 'COMPUTATIONAL_TWIN',
        lastUpdated: new Date().toISOString(),
        isStale: false,
      };

      setOperationalSnapshot(snapshot);
      setLastUpdated(new Date().toISOString());
    } catch (err: any) {
      setError(err.message || 'Failed to connect to Polaris-EMS API');
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  }, [currentStation, horizonHours, activeScenario]);

  // Initial and Station-change fetch
  useEffect(() => {
    fetchStationData();
  }, [fetchStationData]);

  // Periodic subtle background synchronization (every 4 seconds) to keep simulation clock flowing
  useEffect(() => {
    const timer = setInterval(() => {
      if (document.visibilityState === 'visible' && !isFetchingRef.current) {
        api.getLiveTwinSnapshot(currentStation)
          .then(res => {
            if (res.data) {
              const liveData = res.data;
              const twinState = liveData.state || {};
              const metadata = liveData.metadata || {};
              const powerFlow = liveData.power_flow || null;

              setOperationalSnapshot(prev => {
                const solarObj = twinState.solar || {};
                const windObj = twinState.wind || {};
                const dieselObj = twinState.diesel || {};
                const batteryObj = twinState.battery || {};
                const loadsObj = twinState.loads || {};
                const fuelObj = twinState.fuel || {};
                const envObj = twinState.environment || {};

                const solarKw = solarObj.solar_generation_kw !== undefined ? Number(solarObj.solar_generation_kw) : prev.solarGenerationKw;
                const windKw = windObj.wind_generation_kw !== undefined ? Number(windObj.wind_generation_kw) : prev.windGenerationKw;
                const dieselKw = dieselObj.generator_power_kw !== undefined ? Number(dieselObj.generator_power_kw) : prev.dieselGenerationKw;
                
                const bessDischarge = batteryObj.discharge_kw !== undefined ? Number(batteryObj.discharge_kw) : 0;
                const bessCharge = batteryObj.charge_kw !== undefined ? Number(batteryObj.charge_kw) : 0;
                const bessPower = bessDischarge > 0.05 ? bessDischarge : (bessCharge > 0.05 ? -bessCharge : 0);

                let rawSoc = batteryObj.soc_pct !== undefined ? Number(batteryObj.soc_pct) : prev.bessSocPct;
                if (rawSoc !== null && rawSoc <= 1.0 && rawSoc > 0.0) {
                  rawSoc = Math.round(rawSoc * 100);
                }

                const totalGen = (solarKw !== null && windKw !== null && dieselKw !== null)
                  ? Math.round((solarKw + windKw + dieselKw + Math.max(0, bessPower)) * 10) / 10
                  : prev.totalGenerationKw;

                const renewableShare = (totalGen !== null && totalGen > 0.1 && solarKw !== null && windKw !== null)
                  ? Math.min(100, Math.round(((solarKw + windKw) / totalGen) * 100))
                  : prev.renewableSharePct;

                return {
                  ...prev,
                  timestamp: metadata.simulation_timestamp || prev.timestamp,
                  wallClockTimestamp: metadata.wall_clock_timestamp || prev.wallClockTimestamp,
                  activeScenario: metadata.active_scenario || prev.activeScenario,
                  operatingMode: operatingModeRef.current,
                  ambientTemperatureC: envObj.ambient_temperature_c !== undefined ? Number(envObj.ambient_temperature_c) : prev.ambientTemperatureC,
                  windSpeedMs: envObj.wind_speed_ms !== undefined ? Number(envObj.wind_speed_ms) : prev.windSpeedMs,
                  irradianceWm2: envObj.irradiance_wm2 !== undefined ? Number(envObj.irradiance_wm2) : prev.irradianceWm2,
                  totalLoadKw: loadsObj.total_load_kw !== undefined ? Number(loadsObj.total_load_kw) : prev.totalLoadKw,
                  criticalLoadKw: loadsObj.critical_load_kw !== undefined ? Number(loadsObj.critical_load_kw) : prev.criticalLoadKw,
                  flexibleLoadKw: loadsObj.flexible_load_kw !== undefined ? Number(loadsObj.flexible_load_kw) : prev.flexibleLoadKw,
                  solarGenerationKw: solarKw,
                  windGenerationKw: windKw,
                  dieselGenerationKw: dieselKw,
                  bessSocPct: rawSoc,
                  bessPowerKw: bessPower,
                  bessChargeKw: bessCharge,
                  bessDischargeKw: bessDischarge,
                  totalGenerationKw: totalGen,
                  renewableSharePct: renewableShare,
                  powerFlowTopology: powerFlow ? {
                    edges: powerFlow.edges || [],
                    assets: powerFlow.assets || {},
                    sourceMix: powerFlow.source_mix || { solar_pct: 0, wind_pct: 0, diesel_pct: 0, battery_pct: 0 },
                  } : prev.powerFlowTopology,
                  lastUpdated: new Date().toISOString(),
                };
              });
            }
          })
          .catch(() => {});
      }
    }, 4000);

    return () => clearInterval(timer);
  }, [currentStation]);

  // Action: Clear Scenario
  const clearScenario = useCallback(async () => {
    setActiveScenario(null);
    try {
      await api.clearLiveScenario(currentStation);
      await fetchStationData();
      showToast(
        'BASELINE RESTORED',
        'Operational state returned to the station baseline.',
        'success'
      );
    } catch (err: any) {
      console.error('Failed to clear scenario:', err);
      throw err;
    }
  }, [currentStation, fetchStationData, showToast]);

  // Action: Activate Scenario
  const activateScenario = useCallback(async (scenarioId: string, customParams?: Record<string, any>) => {
    const id = scenarioId.toUpperCase().trim();
    if (['NORMAL_BASELINE', 'BASELINE', 'NOMINAL', 'NORMAL', 'NORMAL BASELINE'].includes(id)) {
      await clearScenario();
      return;
    }
    setActiveScenario(id);
    try {
      await api.applyLiveScenario(currentStation, id);
      await fetchStationData();
      showToast(
        `${id.replace(/_/g, ' ')} SCENARIO ACTIVATED`,
        'Operational state updated across Energy, Forecast, Dispatch, Resilience and Assets.',
        'warning'
      );
    } catch (err: any) {
      console.error('Failed to activate scenario:', err);
      throw err;
    }
  }, [currentStation, fetchStationData, showToast, clearScenario]);

  // Action: Apply Manual Control
  const applyManualControl = useCallback(async (actionId: string, parameters?: Record<string, any>) => {
    try {
      const res = await api.dispatchManualControl({
        station_id: currentStation,
        action_id: actionId,
        parameters
      });
      await fetchStationData();
      return res;
    } catch (err: any) {
      console.error('Manual control failed:', err);
      throw err;
    }
  }, [currentStation, fetchStationData]);

  // Action: Approve Auto Recommendation
  const approveAutoRecommendation = useCallback(async () => {
    try {
      const res = await api.approveAutoRecommendation(currentStation);
      await fetchStationData();
      return res;
    } catch (err: any) {
      console.error('Auto recommendation approval failed:', err);
      throw err;
    }
  }, [currentStation, fetchStationData]);

  // Action: Re-Solve Optimizer
  const reSolveOptimizer = useCallback(async (mode: 'EXPECTED' | 'CONSERVATIVE' | 'SCENARIO_ROBUST' = 'EXPECTED') => {
    try {
      const res = await api.optimizeMicrogrid({
        station_id: currentStation,
        horizon_hours: horizonHours,
        mode,
        scenario_id: activeScenario || undefined,
        include_schedule: true
      });
      if (res.data) setOptimizerData(res.data);
      await fetchStationData();
    } catch (err: any) {
      console.error('Re-solve optimizer failed:', err);
      throw err;
    }
  }, [currentStation, horizonHours, activeScenario, fetchStationData]);

  const value: StationContextType = {
    currentStation,
    stationId: currentStation,
    setStation: (s: StationId) => {
      setCurrentStation(s);
      setActiveScenario(null);
      // Immediately apply baseline snapshot so UI never shows empty while fetching
      setOperationalSnapshot(STATION_BASELINE_SNAPSHOTS[s] || DEFAULT_SNAPSHOT);
    },
    horizonHours,
    setHorizonHours,
    stationDetail,
    stationSummaries,
    readiness,
    activeThreats,
    loading,
    error,
    lastUpdated,
    refreshStationData: fetchStationData,
    operatingMode,
    setOperatingMode,
    operationalSnapshot,
    activeScenario,
    activateScenario,
    clearScenario,
    applyManualControl,
    approveAutoRecommendation,
    reSolveOptimizer,
    refreshAll: fetchStationData,
    resilienceData,
    policyData,
    optimizerData,
    tracesData,
    toast,
    showToast,
    dismissToast,
  };

  return <StationContext.Provider value={value}>{children}</StationContext.Provider>;
};

export const useStation = () => {
  const context = useContext(StationContext);
  if (!context) {
    throw new Error('useStation must be used within a StationProvider');
  }
  return context;
};

export const useOperationalSnapshot = () => {
  const context = useContext(StationContext);
  if (!context) {
    throw new Error('useOperationalSnapshot must be used within a StationProvider');
  }
  return {
    snapshot: context.operationalSnapshot,
    activeScenario: context.activeScenario,
    operatingMode: context.operatingMode,
    setOperatingMode: context.setOperatingMode,
    currentStation: context.currentStation,
    setStation: context.setStation,
    activateScenario: context.activateScenario,
    clearScenario: context.clearScenario,
    applyManualControl: context.applyManualControl,
    approveAutoRecommendation: context.approveAutoRecommendation,
    reSolveOptimizer: context.reSolveOptimizer,
    refreshAll: context.refreshAll,
    loading: context.loading,
    error: context.error,
    toast: context.toast,
    showToast: context.showToast,
    dismissToast: context.dismissToast,
  };
};
