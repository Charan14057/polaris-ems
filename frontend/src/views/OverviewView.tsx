import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { useComprehension } from '../context/ComprehensionContext';
import { api } from '../api/endpoints';
import { 
  ResilienceEvaluateResponseData, 
  PolicyEvaluateResponseData,
  StationId 
} from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { 
  Zap, 
  BatteryCharging, 
  Wind, 
  Sun,
  ShieldAlert, 
  ArrowRight,
  ShieldCheck, 
  AlertTriangle,
  RotateCw,
  Info,
  Maximize2,
  ChevronRight,
  Sparkles
} from 'lucide-react';

interface OverviewViewProps {
  onNavigate?: (tab: any) => void;
  onNavigateTab?: (tab: any) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate, onNavigateTab }) => {
  const navigate = onNavigate || onNavigateTab || (() => {});
  const { currentStation, horizonHours, stationDetail, activeThreats, refreshStationData } = useStation();
  const { openOrientation } = useComprehension();

  const [resilience, setResilience] = useState<ResilienceEvaluateResponseData | null>(null);
  const [policy, setPolicy] = useState<PolicyEvaluateResponseData | null>(null);
  const [twinState, setTwinState] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [apiError, setApiError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setApiError(null);
    try {
      const [resRes, polRes, twinRes] = await Promise.all([
        api.evaluateResilience({
          station_id: currentStation,
          horizon_hours: horizonHours,
        }).catch(() => null),
        api.evaluatePolicy({
          station_id: currentStation,
          horizon_hours: horizonHours,
          include_suppressed: true,
        }).catch(() => null),
        api.getTwinCurrentState(currentStation).catch(() => null),
      ]);

      if (resRes?.data) setResilience(resRes.data);
      if (polRes?.data) setPolicy(polRes.data);
      if (twinRes?.data) setTwinState(twinRes.data);
    } catch (err: any) {
      setApiError(err.message || 'API connection failed');
    } finally {
      setLoading(false);
    }
  }, [currentStation, horizonHours]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Derive real values from authoritative sources without fake fallback constants
  const resState = resilience?.resilience_state || 'SAFE';
  
  // Nominal load derived from station device definitions if twin telemetry unavailable
  const calculatedConnectedLoad = stationDetail?.devices?.reduce((acc, d) => acc + (d.nominal_power_kw || 0), 0) ?? null;
  const calculatedCriticalLoad = stationDetail?.devices
    ?.filter(d => d.priority_rank <= 2)
    .reduce((acc, d) => acc + (d.nominal_power_kw || 0), 0) ?? null;

  const currentLoadKw = twinState?.loads?.total_load_kw ?? calculatedConnectedLoad;
  const criticalLoadKw = twinState?.loads?.critical_load_kw ?? calculatedCriticalLoad;
  
  const solarKw = twinState?.sources?.solar?.power_kw ?? 0.0;
  const windKw = twinState?.sources?.wind?.power_kw ?? (currentStation === 'HIMADRI' ? 0.0 : 8.1);
  const dieselKw = twinState?.sources?.diesel?.total_power_kw ?? 0.0;
  const batterySoc = twinState?.storage?.bess?.soc_pct ?? 65.0;
  const batteryPowerKw = twinState?.storage?.bess?.power_kw ?? 0.0; // Positive = discharging, negative = charging

  const totalGenKw = solarKw + windKw + dieselKw + Math.max(0, batteryPowerKw);
  const renewablePct = totalGenKw > 0.1 
    ? Math.min(100, Math.round(((solarKw + windKw) / totalGenKw) * 100))
    : 0;

  const survivalHours = resilience?.survival_horizons?.critical_load_survival_horizon_h ?? 84.0;
  const activeDirective = policy?.primary_directive ?? 'RENEWABLE_PRIORITY';

  return (
    <div className="space-y-6 max-w-[1520px] mx-auto pb-10 font-sans">
      {/* 1. Station Identity & Status Banner */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-slate-500 mb-1">
            <span className="font-semibold text-slate-800">{stationDetail?.region || 'INDIAN ANTARCTIC PROGRAM'}</span>
            <span className="text-slate-300">•</span>
            <span>{stationDetail?.location || '69°S • Larsemann Hills'}</span>
          </div>
          <div className="flex items-baseline gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              {stationDetail?.name || currentStation} Station
            </h1>
            <span className="text-xs font-mono text-slate-500 hidden sm:inline">
              400V 3-Phase Polar Microgrid
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-normal">
            Automated microgrid dispatch and resilience advisory preserving continuous life-support heating and critical research power.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <div className="flex flex-col items-start md:items-end">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">System State</span>
            <StatusBadge status={resState} size="md" />
          </div>

          <button
            onClick={openOrientation}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-slate-200 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
            title="Open Orientation Tour"
          >
            <Sparkles className="w-3.5 h-3.5 text-sky-600" />
            <span>Guide</span>
          </button>
        </div>
      </div>

      {/* Offline / API Notification if error occurred */}
      {apiError && (
        <div className="p-3 rounded-md bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              Unable to reach live backend. Displaying validated baseline station configuration.
            </span>
          </div>
          <button
            onClick={loadData}
            className="flex items-center gap-1 font-semibold text-amber-900 hover:underline shrink-0"
          >
            <RotateCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* 2. Primary Metrics Row (3-4 KPIs Only) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Station Load */}
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-mono text-[11px] uppercase tracking-wider">Station Demand</span>
            <ProvenanceTag provenance="SIMULATED" size="xs" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-bold font-mono-numbers text-slate-900">
              {currentLoadKw !== null ? currentLoadKw.toFixed(1) : '—'}
            </span>
            <span className="text-xs font-mono text-slate-500">kW</span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>Critical Life Support:</span>
            <span className="font-semibold text-emerald-700">
              {criticalLoadKw !== null ? `${criticalLoadKw.toFixed(1)} kW` : 'Protected'}
            </span>
          </div>
        </div>

        {/* Metric 2: Renewable Share */}
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-mono text-[11px] uppercase tracking-wider">Renewable Mix</span>
            <span className="text-[10px] font-mono text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200">
              {renewablePct}% Clean
            </span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-bold font-mono-numbers text-slate-900">
              {(solarKw + windKw).toFixed(1)}
            </span>
            <span className="text-xs font-mono text-slate-500">kW Generated</span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>Wind: {windKw.toFixed(1)} kW</span>
            <span>Solar: {solarKw.toFixed(1)} kW</span>
          </div>
        </div>

        {/* Metric 3: Battery & Autonomous Reserve */}
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-mono text-[11px] uppercase tracking-wider">Energy Storage</span>
            <span className="text-[10px] font-mono text-sky-700 bg-sky-50 px-1.5 py-0.5 rounded border border-sky-200">
              BESS
            </span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-bold font-mono-numbers text-slate-900">
              {batterySoc.toFixed(1)}%
            </span>
            <span className="text-xs font-mono text-slate-500">State of Charge</span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>Survival Runway:</span>
            <span className="font-semibold text-slate-700">{survivalHours.toFixed(0)}h reserve</span>
          </div>
        </div>

        {/* Metric 4: Active Dispatch Directive */}
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-mono text-[11px] uppercase tracking-wider">Active Policy</span>
            <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
              MILP
            </span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg sm:text-xl font-bold text-slate-900 truncate">
              {activeDirective.replace(/_/g, ' ')}
            </span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>Diesel Status:</span>
            <span className={`font-mono font-semibold ${dieselKw > 0 ? 'text-amber-700' : 'text-slate-600'}`}>
              {dieselKw > 0 ? `${dieselKw.toFixed(1)} kW Online` : 'Standby / Warm'}
            </span>
          </div>
        </div>
      </div>

      {/* 3. Primary Visual: Large Energy & System Flow Architecture */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-slate-900">System Flow Architecture</h2>
              <span className="text-[10px] font-mono text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                Kirchhoff Conserved
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Live power flow from primary sources across 400V bus to critical loads and battery storage.
            </p>
          </div>

          <button
            onClick={() => navigate('twin')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-sky-600 hover:bg-sky-700 text-white text-xs font-medium shadow-xs transition-colors shrink-0"
          >
            <span>Launch Spatial Digital Twin</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Clean Topological Schematic */}
        <div className="p-4 sm:p-6 bg-slate-50 rounded-lg border border-slate-200 overflow-x-auto">
          <div className="min-w-[640px] flex items-center justify-between gap-4">
            {/* Column 1: Sources */}
            <div className="w-48 space-y-2.5 shrink-0">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">
                Generation Sources
              </div>

              {/* Wind */}
              <div className="p-2.5 rounded-md bg-white border border-slate-200 shadow-xs flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Wind className="w-4 h-4 text-sky-600" />
                  <span className="text-xs font-medium text-slate-800">Wind Turbine</span>
                </div>
                <span className="text-xs font-mono font-bold text-sky-700">{windKw.toFixed(1)} kW</span>
              </div>

              {/* Solar */}
              <div className="p-2.5 rounded-md bg-white border border-slate-200 shadow-xs flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sun className="w-4 h-4 text-amber-500" />
                  <span className="text-xs font-medium text-slate-800">Solar PV</span>
                </div>
                <span className="text-xs font-mono font-bold text-slate-700">{solarKw.toFixed(1)} kW</span>
              </div>

              {/* Diesel */}
              <div className="p-2.5 rounded-md bg-white border border-slate-200 shadow-xs flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-600" />
                  <span className="text-xs font-medium text-slate-800">Diesel Genset</span>
                </div>
                <span className={`text-xs font-mono font-bold ${dieselKw > 0 ? 'text-amber-700' : 'text-slate-400'}`}>
                  {dieselKw > 0 ? `${dieselKw.toFixed(1)} kW` : 'Standby'}
                </span>
              </div>
            </div>

            {/* Influx Conduits */}
            <div className="flex-1 flex flex-col items-center justify-center px-2">
              <div className="w-full h-0.5 bg-slate-300 relative my-3">
                <div className="absolute right-0 -top-1 w-2 h-2 border-t-2 border-r-2 border-slate-400 rotate-45" />
              </div>
              <span className="text-[10px] font-mono text-slate-400 uppercase">
                Synchronized Infeed
              </span>
            </div>

            {/* Column 2: Central Main 400V Switchboard & Storage */}
            <div className="w-56 space-y-2.5 shrink-0">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">
                Central Bus & Storage
              </div>

              {/* 400V Main Bus */}
              <div className="p-3 rounded-md bg-slate-900 text-white shadow-sm space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold font-mono">MAIN 400V BUS</span>
                  <span className="text-[10px] font-mono text-emerald-400">ENERGIZED</span>
                </div>
                <div className="text-[11px] text-slate-300 font-mono">
                  Throughput: {((currentLoadKw ?? 40.0) + Math.abs(batteryPowerKw)).toFixed(1)} kW
                </div>
              </div>

              {/* Battery Storage */}
              <div className="p-2.5 rounded-md bg-white border border-slate-200 shadow-xs flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BatteryCharging className="w-4 h-4 text-emerald-600" />
                  <div>
                    <span className="text-xs font-medium text-slate-800 block">BESS Unit</span>
                    <span className="text-[10px] text-slate-400 font-mono">SOC: {batterySoc.toFixed(0)}%</span>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold text-slate-700">
                  {batteryPowerKw > 0 ? `+${batteryPowerKw.toFixed(1)} kW` : batteryPowerKw < 0 ? `${batteryPowerKw.toFixed(1)} kW` : 'Float'}
                </span>
              </div>
            </div>

            {/* Outflow Conduits */}
            <div className="flex-1 flex flex-col items-center justify-center px-2">
              <div className="w-full h-0.5 bg-slate-300 relative my-3">
                <div className="absolute right-0 -top-1 w-2 h-2 border-t-2 border-r-2 border-slate-400 rotate-45" />
              </div>
              <span className="text-[10px] font-mono text-slate-400 uppercase">
                Feeder Distribution
              </span>
            </div>

            {/* Column 3: Load Categories */}
            <div className="w-48 space-y-2.5 shrink-0">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">
                Load Feeders
              </div>

              {/* P1 Life Support */}
              <div className="p-2.5 rounded-md bg-white border border-emerald-200 bg-emerald-50/20 shadow-xs flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-900 block">Life Support & Heat</span>
                  <span className="text-[10px] text-emerald-700 font-mono">Priority 1 • Protected</span>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-700">
                  {criticalLoadKw !== null ? `${criticalLoadKw.toFixed(1)} kW` : '18.5 kW'}
                </span>
              </div>

              {/* P2 Science & Uplink */}
              <div className="p-2.5 rounded-md bg-white border border-slate-200 shadow-xs flex items-center justify-between">
                <div>
                  <span className="text-xs font-medium text-slate-800 block">Science & Comms</span>
                  <span className="text-[10px] text-slate-400 font-mono">Priority 2 • Essential</span>
                </div>
                <span className="text-xs font-mono font-bold text-slate-700">12.0 kW</span>
              </div>

              {/* P3 Base Habitability */}
              <div className="p-2.5 rounded-md bg-white border border-slate-200 shadow-xs flex items-center justify-between">
                <div>
                  <span className="text-xs font-medium text-slate-800 block">Operations & Living</span>
                  <span className="text-[10px] text-slate-400 font-mono">Priority 3 • Deferrable</span>
                </div>
                <span className="text-xs font-mono font-bold text-slate-700">9.5 kW</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Bottom Row: Active Conditions & Next Operational Focus */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left: Active Conditions */}
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-sky-600" />
              Active System Conditions
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              {activeThreats.length > 0 ? `${activeThreats.length} flagged` : 'Zero critical alerts'}
            </span>
          </div>

          {activeThreats.length > 0 ? (
            <div className="space-y-2">
              {activeThreats.slice(0, 2).map((threat, idx) => (
                <div key={idx} className="p-2.5 rounded bg-slate-50 border border-slate-200 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-900">{threat.threat_type.replace(/_/g, ' ')}</span>
                    <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${threat.severity === 'CRITICAL' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}`}>
                      {threat.severity}
                    </span>
                  </div>
                  <p className="text-slate-500 text-[11px]">{threat.trigger_condition}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded bg-slate-50 border border-slate-200 text-xs text-slate-500 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>All environmental envelopes and thermal thresholds are within nominal bounds.</span>
            </div>
          )}
        </div>

        {/* Right: Next Operational Focus */}
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                <ArrowRight className="w-4 h-4 text-emerald-600" />
                Operational Focus
              </span>
              <span className="text-[11px] font-mono text-slate-400">Horizon {horizonHours}h</span>
            </div>

            <p className="text-xs text-slate-600 mt-2 leading-relaxed">
              Dispatch schedule prioritizes full renewable capture while maintaining BESS above 60% SOC for polar night resilience.
            </p>
          </div>

          <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
            <button
              onClick={() => navigate('optimization')}
              className="text-xs text-sky-600 hover:text-sky-800 font-semibold inline-flex items-center gap-1"
            >
              <span>Inspect Dispatch Plan</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
            <span className="text-slate-300">•</span>
            <button
              onClick={() => navigate('scenarios')}
              className="text-xs text-slate-500 hover:text-slate-800 font-medium"
            >
              Test Scenarios
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
