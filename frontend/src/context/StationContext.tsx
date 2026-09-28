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

const DEFAULT_SNAPSHOT: OperationalSnapshot = {
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
  ambientTemperatureC: null,
  windSpeedMs: null,
  irradianceWm2: null,
  cloudFraction: null,
  solarElevationDeg: null,
  totalLoadKw: null,
  criticalLoadKw: null,
  flexibleLoadKw: null,
  servedLoadKw: null,
  unservedLoadKw: null,
  solarGenerationKw: null,
  solarCapacityKw: null,
  solarStatus: null,
  windGenerationKw: null,
  windCapacityKw: null,
  windStatus: null,
  dieselGenerationKw: null,
  dieselMaxKw: null,
  dieselStatus: null,
  fuelConsumptionLph: null,
  fuelRemainingL: null,
  daysOfFuelRemaining: null,
  bessSocPct: null,
  bessPowerKw: null,
  bessChargeKw: null,
  bessDischargeKw: null,
  bessCapacityKwh: null,
  bessStatus: null,
  totalGenerationKw: null,
  renewableSharePct: null,
  resilienceState: 'SAFE',
  resilienceDimensions: null,
  survivalHorizons: null,
  activeDirective: null,
  policyState: null,
  optimizerRecommendation: null,
  optimizerRationale: null,
  powerFlowTopology: null,
  latestTrace: null,
  provenance: 'SIMULATED',
  lastUpdated: new Date().toISOString(),
  isStale: false,
};

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
  
  // Direct Cached Engine Responses
  resilienceData: ResilienceEvaluateResponseData | null;
  policyData: PolicyEvaluateResponseData | null;
  optimizerData: OptimizeResponseData | null;
  tracesData: TraceSummary[];
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

      const actScen = metadata.active_scenario || activeScenario || null;
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
        operatingMode: metadata.operating_mode === 'LIVE_MANUAL' ? 'MANUAL' : 'AUTO',
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
        provenance: 'SIMULATED',
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
                  operatingMode: metadata.operating_mode === 'LIVE_MANUAL' ? 'MANUAL' : 'AUTO',
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

  // Action: Activate Scenario
  const activateScenario = useCallback(async (scenarioId: string, customParams?: Record<string, any>) => {
    setActiveScenario(scenarioId.toUpperCase());
    try {
      await api.applyLiveScenario(currentStation, scenarioId.toUpperCase());
      await fetchStationData();
    } catch (err: any) {
      console.error('Failed to activate scenario:', err);
      throw err;
    }
  }, [currentStation, fetchStationData]);

  // Action: Clear Scenario
  const clearScenario = useCallback(async () => {
    setActiveScenario(null);
    try {
      await api.clearLiveScenario(currentStation);
      await fetchStationData();
    } catch (err: any) {
      console.error('Failed to clear scenario:', err);
      throw err;
    }
  }, [currentStation, fetchStationData]);

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
  };
};
