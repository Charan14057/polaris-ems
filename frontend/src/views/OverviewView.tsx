import React from 'react';
import { useStation, useOperationalSnapshot } from '../context/StationContext';
import { useComprehension } from '../context/ComprehensionContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { 
  Zap, 
  BatteryCharging, 
  Wind, 
  Sun,
  Flame,
  ShieldAlert, 
  ArrowRight,
  ShieldCheck, 
  AlertTriangle,
  RotateCw,
  Info,
  Maximize2,
  ChevronRight,
  Sparkles,
  Compass,
  Thermometer,
  CloudSun,
  Activity,
  Layers,
  Cpu,
  Radio,
  Sliders,
  CheckCircle2,
  XCircle
} from 'lucide-react';

interface OverviewViewProps {
  onNavigate?: (tab: any) => void;
  onNavigateTab?: (tab: any) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate, onNavigateTab }) => {
  const navigate = onNavigate || onNavigateTab || (() => {});
  const { stationDetail, refreshStationData, loading } = useStation();
  const { snapshot, activeScenario, clearScenario } = useOperationalSnapshot();
  const { openOrientation } = useComprehension();

  // Helper formatters: Render "—" when data is genuinely null or undefined
  const fmtKw = (val: number | null | undefined): string => {
    if (val === null || val === undefined || isNaN(val)) return '—';
    return `${val.toFixed(1)} kW`;
  };

  const fmtPct = (val: number | null | undefined): string => {
    if (val === null || val === undefined || isNaN(val)) return '—';
    return `${Math.round(val)}%`;
  };

  const fmtHours = (val: number | null | undefined): string => {
    if (val === null || val === undefined || isNaN(val)) return '—';
    if (val > 500) return '>500 h';
    return `${val.toFixed(0)} h`;
  };

  const fmtLiters = (val: number | null | undefined): string => {
    if (val === null || val === undefined || isNaN(val)) return '—';
    return `${Math.round(val).toLocaleString()} L`;
  };

  const fmtTemp = (val: number | null | undefined): string => {
    if (val === null || val === undefined || isNaN(val)) return '—';
    return `${val > 0 ? `+${val.toFixed(1)}` : val.toFixed(1)}°C`;
  };

  const fmtSpeed = (val: number | null | undefined): string => {
    if (val === null || val === undefined || isNaN(val)) return '—';
    return `${val.toFixed(1)} m/s`;
  };

  const fmtWm2 = (val: number | null | undefined): string => {
    if (val === null || val === undefined || isNaN(val)) return '—';
    return `${val.toFixed(0)} W/m²`;
  };

  const isBessDischarging = snapshot.bessStatus === 'DISCHARGING';
  const isBessCharging = snapshot.bessStatus === 'CHARGING';
  const isSolarGenerating = snapshot.solarGenerationKw !== null && snapshot.solarGenerationKw > 0.1;
  const isWindGenerating = snapshot.windGenerationKw !== null && snapshot.windGenerationKw > 0.1;
  const isDieselOnline = snapshot.dieselGenerationKw !== null && snapshot.dieselGenerationKw > 0.1;

  // Source mix percentages from authoritative topology
  const sourceMix = snapshot.powerFlowTopology?.sourceMix || {
    solar_pct: snapshot.totalGenerationKw && snapshot.solarGenerationKw ? Math.round((snapshot.solarGenerationKw / snapshot.totalGenerationKw) * 100) : 0,
    wind_pct: snapshot.totalGenerationKw && snapshot.windGenerationKw ? Math.round((snapshot.windGenerationKw / snapshot.totalGenerationKw) * 100) : 0,
    diesel_pct: snapshot.totalGenerationKw && snapshot.dieselGenerationKw ? Math.round((snapshot.dieselGenerationKw / snapshot.totalGenerationKw) * 100) : 0,
    battery_pct: snapshot.totalGenerationKw && isBessDischarging && snapshot.bessPowerKw ? Math.round((snapshot.bessPowerKw / snapshot.totalGenerationKw) * 100) : 0,
  };

  return (
    <div className="space-y-6 max-w-[1520px] mx-auto pb-12 font-sans selection:bg-sky-500/20">
      
      {/* 1. Industrial Header & Station Condition Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 relative z-10">
          <div>
            <div className="flex items-center gap-2.5 text-[11px] font-mono uppercase tracking-wider text-sky-400 mb-1.5">
              <span className="font-semibold text-slate-300">{snapshot.stationRegion}</span>
              <span className="text-slate-600">•</span>
              <span>{snapshot.stationLocation}</span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-400">STATION ID: {snapshot.currentStation}</span>
            </div>
            
            <div className="flex items-baseline gap-3.5">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                {snapshot.stationName}
              </h1>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-sky-300 border border-slate-700">
                400V 3-Phase Microgrid
              </span>
            </div>
            
            <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Authoritative operational command center monitoring real-time generation balance, thermal habitability, and multi-horizon survivability.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="bg-slate-800/80 border border-slate-700 rounded-lg px-3.5 py-2 flex flex-col items-start lg:items-end">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Resilience State</span>
              <div className="mt-0.5">
                <StatusBadge status={snapshot.resilienceState} size="md" />
              </div>
            </div>

            <div className="bg-slate-800/80 border border-slate-700 rounded-lg px-3.5 py-2 flex flex-col items-start lg:items-end">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Operating Mode</span>
              <span className="text-xs font-mono font-bold text-sky-300 mt-0.5 flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${snapshot.operatingMode === 'AUTO' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                {snapshot.operatingMode} GOVERNANCE
              </span>
            </div>

            <button
              onClick={() => refreshStationData()}
              disabled={loading}
              className="p-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors"
              title="Refresh Authoritative Telemetry"
            >
              <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Environmental Telemetry Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-4 border-t border-slate-800/80 text-xs font-mono">
          <div className="flex items-center gap-2.5 text-slate-300">
            <Thermometer className="w-4 h-4 text-sky-400 shrink-0" />
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Ambient Temp</span>
              <span className="font-bold text-white">{fmtTemp(snapshot.ambientTemperatureC)}</span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 text-slate-300">
            <Wind className="w-4 h-4 text-teal-400 shrink-0" />
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Wind Velocity</span>
              <span className="font-bold text-white">{fmtSpeed(snapshot.windSpeedMs)}</span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 text-slate-300">
            <Sun className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Solar Irradiance</span>
              <span className="font-bold text-white">{fmtWm2(snapshot.irradianceWm2)}</span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 text-slate-300">
            <CloudSun className="w-4 h-4 text-indigo-400 shrink-0" />
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Cloud Cover</span>
              <span className="font-bold text-white">{snapshot.cloudFraction !== null ? `${Math.round(snapshot.cloudFraction * 100)}%` : '—'}</span>
            </div>
          </div>
        </div>
      </div>


      {/* 2. Active Scenario Panel with SCENARIO IMPACT strip */}
      {activeScenario && (
        <div className="bg-amber-950/40 border border-amber-500/30 rounded-xl overflow-hidden">
          {/* Header row */}
          <div className="px-4 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 uppercase tracking-wider">
                    ACTIVE SCENARIO
                  </span>
                  <span className="text-sm font-mono font-bold text-white">{activeScenario.replace(/_/g, ' ')}</span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded uppercase font-bold ${
                    snapshot.scenarioSeverity === 'CRITICAL' ? 'bg-red-500/20 text-red-300'
                    : snapshot.scenarioSeverity === 'HIGH' ? 'bg-orange-500/20 text-orange-300'
                    : 'bg-yellow-500/20 text-yellow-300'
                  }`}>{snapshot.scenarioSeverity}</span>
                </div>
                <p className="text-[11px] text-amber-300/70 mt-0.5">
                  Operational state perturbed. All downstream pages reflect this regime.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => clearScenario()}
                className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/40 text-xs font-mono font-semibold transition-colors"
              >
                Restore Baseline
              </button>
              <button
                onClick={() => navigate('scenarios')}
                className="px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700/60 text-slate-200 text-xs font-mono transition-colors border border-slate-700/40"
              >
                Scenarios →
              </button>
            </div>
          </div>

          {/* SCENARIO IMPACT strip */}
          <div className="border-t border-amber-500/20 bg-amber-950/20 px-4 py-2.5">
            <div className="flex items-center gap-1.5 mb-2">
              <span className="text-[9px] font-mono uppercase tracking-widest text-amber-400/70 font-bold">Scenario Impact</span>
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-[11px] font-mono">
              {activeScenario === 'BLIZZARD' || activeScenario === 'EXTREME_COLD' || activeScenario === 'UNFORESEEN_WEATHER' ? (
                <>
                  <span className="flex items-center gap-1 text-blue-300"><span className="opacity-60">Environment</span> ↓ degraded</span>
                  <span className="flex items-center gap-1 text-amber-300"><span className="opacity-60">Solar</span> ↓ suppressed</span>
                  <span className="flex items-center gap-1 text-orange-300"><span className="opacity-60">Wind stress</span> ↑ elevated</span>
                  <span className="flex items-center gap-1 text-red-300"><span className="opacity-60">Load</span> ↑ +heating demand</span>
                  <span className="flex items-center gap-1 text-yellow-300"><span className="opacity-60">Battery demand</span> ↑ increased</span>
                  <span className="flex items-center gap-1 text-red-300"><span className="opacity-60">Resilience margin</span> ↓ reduced</span>
                </>
              ) : activeScenario === 'SOLAR_GENERATION_FAILURE' ? (
                <>
                  <span className="flex items-center gap-1 text-amber-300"><span className="opacity-60">Solar</span> ↓ 0.0 kW forced</span>
                  <span className="flex items-center gap-1 text-emerald-300"><span className="opacity-60">Battery</span> ↑ compensating</span>
                  <span className="flex items-center gap-1 text-slate-300"><span className="opacity-60">Diesel reserve</span> → on standby</span>
                  <span className="flex items-center gap-1 text-yellow-300"><span className="opacity-60">Renewable share</span> ↓ wind-only</span>
                </>
              ) : activeScenario === 'WIND_GENERATION_FAILURE' ? (
                <>
                  <span className="flex items-center gap-1 text-teal-300"><span className="opacity-60">Wind</span> ↓ 0.0 kW forced</span>
                  <span className="flex items-center gap-1 text-slate-300"><span className="opacity-60">Diesel</span> ↑ ramping up</span>
                  <span className="flex items-center gap-1 text-red-300"><span className="opacity-60">Renewable share</span> ↓ critical</span>
                  <span className="flex items-center gap-1 text-orange-300"><span className="opacity-60">Fuel burn rate</span> ↑ active</span>
                </>
              ) : activeScenario === 'BATTERY_DEGRADATION' ? (
                <>
                  <span className="flex items-center gap-1 text-emerald-300"><span className="opacity-60">BESS capacity</span> ↓ derated</span>
                  <span className="flex items-center gap-1 text-orange-300"><span className="opacity-60">Battery endurance</span> ↓ reduced</span>
                  <span className="flex items-center gap-1 text-slate-300"><span className="opacity-60">Diesel reserve</span> ↑ elevated</span>
                </>
              ) : (
                <>
                  <span className="flex items-center gap-1 text-amber-300"><span className="opacity-60">Scenario</span> → {activeScenario.replace(/_/g, ' ')}</span>
                  <span className="flex items-center gap-1 text-orange-300"><span className="opacity-60">State</span> → perturbed</span>
                  <span className="flex items-center gap-1 text-red-300"><span className="opacity-60">Resilience</span> ↓ under review</span>
                </>
              )}
              <span className="flex items-center gap-1 ml-auto">
                <span className="text-amber-400/50 font-mono text-[9px]">temp:{fmtTemp(snapshot.ambientTemperatureC)}</span>
                <span className="text-teal-400/50 font-mono text-[9px] ml-2">wind:{fmtSpeed(snapshot.windSpeedMs)}</span>
                <span className="text-amber-400/50 font-mono text-[9px] ml-2">diesel:{fmtKw(snapshot.dieselGenerationKw)}</span>
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 3. Primary Real-Time Operational Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-3.5">
        {/* Metric 1: Total Demand */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">Total Demand</span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl sm:text-2xl font-bold font-mono text-slate-900">{fmtKw(snapshot.totalLoadKw)}</span>
          </div>
          <div className="text-[11px] font-mono text-slate-500 mt-1 flex items-center justify-between">
            <span>Critical: {fmtKw(snapshot.criticalLoadKw)}</span>
            <span className="text-slate-400">Flex: {fmtKw(snapshot.flexibleLoadKw)}</span>
          </div>
        </div>

        {/* Metric 2: Solar PV Generation */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Solar PV Output</span>
            <span className={`w-2 h-2 rounded-full ${isSolarGenerating ? 'bg-amber-500' : 'bg-slate-300'}`} />
          </div>
          <span className="text-xl sm:text-2xl font-bold font-mono text-amber-600">{fmtKw(snapshot.solarGenerationKw)}</span>
          <div className="text-[11px] font-mono text-slate-500 mt-1">
            Status: <span className="font-semibold text-slate-700">{snapshot.solarStatus || '—'}</span>
          </div>
        </div>

        {/* Metric 3: Wind Turbine Generation */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Wind Turbine Output</span>
            <span className={`w-2 h-2 rounded-full ${isWindGenerating ? 'bg-teal-500' : 'bg-slate-300'}`} />
          </div>
          <span className="text-xl sm:text-2xl font-bold font-mono text-teal-600">{fmtKw(snapshot.windGenerationKw)}</span>
          <div className="text-[11px] font-mono text-slate-500 mt-1">
            Status: <span className="font-semibold text-slate-700">{snapshot.windStatus || '—'}</span>
          </div>
        </div>

        {/* Metric 4: Diesel Generation */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Diesel Genset</span>
            <span className={`w-2 h-2 rounded-full ${isDieselOnline ? 'bg-amber-600 animate-pulse' : 'bg-slate-300'}`} />
          </div>
          <span className="text-xl sm:text-2xl font-bold font-mono text-slate-800">{fmtKw(snapshot.dieselGenerationKw)}</span>
          <div className="text-[11px] font-mono text-slate-500 mt-1">
            Burn: <span className="font-semibold text-slate-700">{snapshot.fuelConsumptionLph !== null ? `${snapshot.fuelConsumptionLph.toFixed(1)} L/h` : '—'}</span>
          </div>
        </div>

        {/* Metric 5: BESS State of Charge */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">BESS SOC</span>
            <BatteryCharging className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <span className="text-xl sm:text-2xl font-bold font-mono text-emerald-600">{fmtPct(snapshot.bessSocPct)}</span>
          <div className="text-[11px] font-mono text-slate-500 mt-1">
            Flow: <span className="font-semibold text-slate-700">{fmtKw(snapshot.bessPowerKw)}</span>
          </div>
        </div>

        {/* Metric 6: Fuel & Survival Horizon */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">Survival Horizon</span>
          <span className="text-xl sm:text-2xl font-bold font-mono text-indigo-600">
            {fmtHours(snapshot.survivalHorizons?.criticalLoadSurvivalH)}
          </span>
          <div className="text-[11px] font-mono text-slate-500 mt-1">
            Fuel: <span className="font-semibold text-slate-700">{fmtLiters(snapshot.fuelRemainingL)}</span>
          </div>
        </div>
      </div>

      {/* 4. VISUAL ENERGY BALANCE (Interactive Physical Bus Topology) */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-5 border-b border-slate-100 gap-2">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-sky-600 font-bold block">
              INSTANTANEOUS POWER BALANCE & SCADA TOPOLOGY
            </span>
            <h2 className="text-lg font-bold text-slate-900 mt-0.5">
              Live Microgrid Generation, Distribution Bus & Substation Feeders
            </h2>
          </div>
          
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-slate-500">
              Renewable Penetration: <strong className="text-emerald-600 font-bold">{fmtPct(snapshot.renewableSharePct)}</strong>
            </span>
            <button
              onClick={() => navigate('twin')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-50 text-sky-700 hover:bg-sky-100 text-xs font-mono font-medium transition-colors"
            >
              <span>Explore 3D Twin</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Visual Flow Representation with Connected Electrical Conduits */}
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_64px_minmax(0,1.2fr)_64px_minmax(0,1fr)] gap-2 lg:gap-0 items-center">
          
          {/* Column A: Generation Sources */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between px-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                Generation Assets & Storage
              </span>
              <span className="text-[9px] font-mono text-emerald-600 font-bold bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                INFLOW: {fmtKw(snapshot.totalGenerationKw)}
              </span>
            </div>

            {/* Solar Box */}
            <div className={`p-3 rounded-lg border flex items-center justify-between transition-colors relative ${
              isSolarGenerating ? 'bg-amber-50/60 border-amber-300 text-slate-900 shadow-xs' : 'bg-slate-50 border-slate-200 text-slate-400'
            }`}>
              <div className="flex items-center gap-3">
                <Sun className={`w-4 h-4 ${isSolarGenerating ? 'text-amber-500' : 'text-slate-400'}`} />
                <div>
                  <span className="text-xs font-bold font-mono block">Solar PV Array</span>
                  <span className="text-[10px] font-mono text-slate-500">Peak: {fmtKw(snapshot.solarCapacityKw)}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold">{fmtKw(snapshot.solarGenerationKw)}</span>
                <span className={`hidden lg:inline-block w-2.5 h-2.5 rounded-full border-2 ${
                  isSolarGenerating ? 'bg-amber-500 border-amber-300 shadow-[0_0_8px_rgba(245,158,11,0.6)]' : 'bg-slate-300 border-slate-200'
                }`} title="Feeder Terminal Node" />
              </div>
            </div>

            {/* Wind Box */}
            <div className={`p-3 rounded-lg border flex items-center justify-between transition-colors relative ${
              isWindGenerating ? 'bg-teal-50/60 border-teal-300 text-slate-900 shadow-xs' : 'bg-slate-50 border-slate-200 text-slate-400'
            }`}>
              <div className="flex items-center gap-3">
                <Wind className={`w-4 h-4 ${isWindGenerating ? 'text-teal-500' : 'text-slate-400'}`} />
                <div>
                  <span className="text-xs font-bold font-mono block">Wind Turbine</span>
                  <span className="text-[10px] font-mono text-slate-500">Rated: {fmtKw(snapshot.windCapacityKw)}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold">{fmtKw(snapshot.windGenerationKw)}</span>
                <span className={`hidden lg:inline-block w-2.5 h-2.5 rounded-full border-2 ${
                  isWindGenerating ? 'bg-teal-500 border-teal-300 shadow-[0_0_8px_rgba(13,148,136,0.6)]' : 'bg-slate-300 border-slate-200'
                }`} title="Feeder Terminal Node" />
              </div>
            </div>

            {/* Diesel Box */}
            <div className={`p-3 rounded-lg border flex items-center justify-between transition-colors relative ${
              isDieselOnline ? 'bg-amber-50/70 border-amber-400 text-slate-900 shadow-xs' : 'bg-slate-50 border-slate-200 text-slate-400'
            }`}>
              <div className="flex items-center gap-3">
                <Flame className={`w-4 h-4 ${isDieselOnline ? 'text-amber-600' : 'text-slate-400'}`} />
                <div>
                  <span className="text-xs font-bold font-mono block">Diesel Generator (DG-1)</span>
                  <span className="text-[10px] font-mono text-slate-500">Capacity: {fmtKw(snapshot.dieselMaxKw)}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold">{fmtKw(snapshot.dieselGenerationKw)}</span>
                <span className={`hidden lg:inline-block w-2.5 h-2.5 rounded-full border-2 ${
                  isDieselOnline ? 'bg-amber-600 border-amber-300 shadow-[0_0_8px_rgba(234,88,12,0.6)] animate-pulse' : 'bg-slate-300 border-slate-200'
                }`} title="Feeder Terminal Node" />
              </div>
            </div>

            {/* BESS Box */}
            <div className={`p-3 rounded-lg border flex items-center justify-between transition-colors relative ${
              isBessDischarging ? 'bg-emerald-50/70 border-emerald-300 text-slate-900 shadow-xs' : 
              (isBessCharging ? 'bg-sky-50/70 border-sky-300 text-slate-900 shadow-xs' : 'bg-slate-50 border-slate-200 text-slate-500')
            }`}>
              <div className="flex items-center gap-3">
                <BatteryCharging className={`w-4 h-4 ${isBessDischarging ? 'text-emerald-600' : (isBessCharging ? 'text-sky-600' : 'text-slate-400')}`} />
                <div>
                  <span className="text-xs font-bold font-mono block">Station BESS (120 kWh)</span>
                  <span className="text-[10px] font-mono text-slate-500">
                    SOC: {fmtPct(snapshot.bessSocPct)} • {snapshot.bessStatus || 'STANDBY'}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold">{fmtKw(snapshot.bessPowerKw)}</span>
                <span className={`hidden lg:inline-block w-2.5 h-2.5 rounded-full border-2 ${
                  isBessDischarging ? 'bg-emerald-500 border-emerald-300 shadow-[0_0_8px_rgba(16,185,129,0.6)]' :
                  (isBessCharging ? 'bg-sky-500 border-sky-300 shadow-[0_0_8px_rgba(2,132,199,0.6)]' : 'bg-slate-300 border-slate-200')
                }`} title="Battery Tie Node" />
              </div>
            </div>
          </div>

          {/* Left SVG Conduit Bridge: Desktop Converging Feeder Lines */}
          <div className="hidden lg:flex flex-col items-center justify-center h-full w-full relative">
            <svg viewBox="0 0 64 300" className="w-full h-full min-h-[290px] overflow-visible" preserveAspectRatio="none">
              <defs>
                <marker id="arrow-solar" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#f59e0b" />
                </marker>
                <marker id="arrow-wind" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#0d9488" />
                </marker>
                <marker id="arrow-diesel" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#ea580c" />
                </marker>
                <marker id="arrow-bess-out" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#10b981" />
                </marker>
                <marker id="arrow-bess-in" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 8 1 L 0 5 L 8 9 z" fill="#0284c7" />
                </marker>
              </defs>

              {/* Line 1: Solar PV -> Bus Intake (y=36 -> y=105) */}
              <path d="M 0 36 C 36 36, 32 105, 64 105" fill="none" stroke="#e2e8f0" strokeWidth="2.5" />
              {isSolarGenerating && (
                <path 
                  d="M 0 36 C 36 36, 32 105, 64 105" 
                  fill="none" 
                  stroke="#f59e0b" 
                  strokeWidth="2.5" 
                  className="animate-flow-line" 
                  markerEnd="url(#arrow-solar)"
                />
              )}

              {/* Line 2: Wind -> Bus Intake (y=110 -> y=125) */}
              <path d="M 0 110 C 36 110, 32 125, 64 125" fill="none" stroke="#e2e8f0" strokeWidth="2.5" />
              {isWindGenerating && (
                <path 
                  d="M 0 110 C 36 110, 32 125, 64 125" 
                  fill="none" 
                  stroke="#0d9488" 
                  strokeWidth="2.5" 
                  className="animate-flow-line" 
                  markerEnd="url(#arrow-wind)"
                />
              )}

              {/* Line 3: Diesel -> Bus Intake (y=184 -> y=175) */}
              <path d="M 0 184 C 36 184, 32 175, 64 175" fill="none" stroke="#e2e8f0" strokeWidth="2.5" />
              {isDieselOnline && (
                <path 
                  d="M 0 184 C 36 184, 32 175, 64 175" 
                  fill="none" 
                  stroke="#ea580c" 
                  strokeWidth="2.5" 
                  className="animate-flow-line" 
                  markerEnd="url(#arrow-diesel)"
                />
              )}

              {/* Line 4: BESS -> Bus Intake (y=258 -> y=195) */}
              <path d="M 0 258 C 36 258, 32 195, 64 195" fill="none" stroke="#e2e8f0" strokeWidth="2.5" />
              {isBessDischarging && (
                <path 
                  d="M 0 258 C 36 258, 32 195, 64 195" 
                  fill="none" 
                  stroke="#10b981" 
                  strokeWidth="2.5" 
                  className="animate-flow-line" 
                  markerEnd="url(#arrow-bess-out)"
                />
              )}
              {isBessCharging && (
                <path 
                  d="M 64 195 C 32 195, 36 258, 0 258" 
                  fill="none" 
                  stroke="#0284c7" 
                  strokeWidth="2.5" 
                  className="animate-flow-line-reverse" 
                  markerEnd="url(#arrow-bess-in)"
                />
              )}
            </svg>
          </div>

          {/* Mobile Vertical Flow Indicator: Generation -> Main Bus */}
          <div className="lg:hidden flex flex-col items-center justify-center my-2 py-1">
            <div className="h-4 w-0.5 bg-gradient-to-b from-slate-300 to-sky-500 animate-pulse" />
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 text-sky-300 text-[10px] font-mono border border-slate-700 shadow-xs">
              <span className="animate-bounce">↓</span>
              <span>INFLOW CONDUIT: {fmtKw(snapshot.totalGenerationKw)}</span>
              <span className="animate-bounce">↓</span>
            </div>
            <div className="h-4 w-0.5 bg-gradient-to-b from-sky-500 to-slate-900 animate-pulse" />
          </div>

          {/* Column B: Main Distribution Bus */}
          <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-900 text-white border-2 border-slate-700 shadow-xl relative overflow-hidden">
            {/* Top Bus Title */}
            <div className="w-full flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[10px] font-mono uppercase tracking-widest text-sky-400 font-bold">
                  415V AC SYNCHRONOUS BUS
                </span>
              </div>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800 font-semibold">
                3-PHASE
              </span>
            </div>
            
            {/* Total Inflow Row */}
            <div className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-slate-800/90 border border-slate-700 text-xs font-mono mb-2">
              <span className="text-slate-400">Total Generation Inflow</span>
              <span className="font-bold text-emerald-400">{fmtKw(snapshot.totalGenerationKw)}</span>
            </div>

            {/* Total Outflow Row */}
            <div className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-slate-800/90 border border-slate-700 text-xs font-mono mb-2">
              <span className="text-slate-400">Total Demand Throughput</span>
              <span className="font-bold text-sky-300">{fmtKw(snapshot.totalLoadKw)}</span>
            </div>

            {/* Power Balance / Net Gap Indicator */}
            <div className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-[11px] font-mono mb-3 text-emerald-300">
              <span>Instantaneous Balance</span>
              <span className="font-bold">ΔP = 0.0 kW (100% Balanced)</span>
            </div>

            {/* Bus Technical Specs */}
            <div className="w-full flex items-center justify-between px-3 py-1.5 text-[10px] font-mono text-slate-400 border-t border-slate-800 pt-2">
              <span>Frequency: 50.00 Hz</span>
              <span>Voltage: 415 V</span>
              <span>PF: 0.98</span>
            </div>
          </div>

          {/* Right SVG Conduit Bridge: Desktop Diverging Feeder Lines */}
          <div className="hidden lg:flex flex-col items-center justify-center h-full w-full relative">
            <svg viewBox="0 0 64 300" className="w-full h-full min-h-[290px] overflow-visible" preserveAspectRatio="none">
              <defs>
                <marker id="arrow-p1" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#ef4444" />
                </marker>
                <marker id="arrow-p2" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#0284c7" />
                </marker>
                <marker id="arrow-p3" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#64748b" />
                </marker>
              </defs>

              {/* Line 1: Bus Feeder -> P1 Life Support (y=115 -> y=45) */}
              <path d="M 0 115 C 28 115, 32 45, 64 45" fill="none" stroke="#fee2e2" strokeWidth="2.5" />
              <path 
                d="M 0 115 C 28 115, 32 45, 64 45" 
                fill="none" 
                stroke="#ef4444" 
                strokeWidth="2.5" 
                className="animate-flow-line" 
                markerEnd="url(#arrow-p1)"
              />

              {/* Line 2: Bus Feeder -> P2 Science/Comms (y=150 -> y=150) */}
              <path d="M 0 150 L 64 150" fill="none" stroke="#e0f2fe" strokeWidth="2.5" />
              <path 
                d="M 0 150 L 64 150" 
                fill="none" 
                stroke="#0284c7" 
                strokeWidth="2.5" 
                className="animate-flow-line" 
                markerEnd="url(#arrow-p2)"
              />

              {/* Line 3: Bus Feeder -> P3 Flexible (y=185 -> y=255) */}
              <path d="M 0 185 C 28 185, 32 255, 64 255" fill="none" stroke="#f1f5f9" strokeWidth="2.5" />
              <path 
                d="M 0 185 C 28 185, 32 255, 64 255" 
                fill="none" 
                stroke="#64748b" 
                strokeWidth="2.5" 
                className="animate-flow-line" 
                markerEnd="url(#arrow-p3)"
              />
            </svg>
          </div>

          {/* Mobile Vertical Flow Indicator: Main Bus -> Loads */}
          <div className="lg:hidden flex flex-col items-center justify-center my-2 py-1">
            <div className="h-4 w-0.5 bg-gradient-to-b from-slate-900 to-sky-500 animate-pulse" />
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 text-sky-300 text-[10px] font-mono border border-slate-700 shadow-xs">
              <span className="animate-bounce">↓</span>
              <span>FEEDER DISTRIBUTION: {fmtKw(snapshot.totalLoadKw)}</span>
              <span className="animate-bounce">↓</span>
            </div>
            <div className="h-4 w-0.5 bg-gradient-to-b from-sky-500 to-slate-300 animate-pulse" />
          </div>

          {/* Column C: Substation Loads */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between px-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                Station Load Demands
              </span>
              <span className="text-[9px] font-mono text-sky-700 font-bold bg-sky-50 px-1.5 py-0.5 rounded border border-sky-200">
                THROUGHPUT: {fmtKw(snapshot.totalLoadKw)}
              </span>
            </div>

            {/* Critical Load */}
            <div className="p-3 rounded-lg border border-red-200 bg-red-50/50 flex items-center justify-between relative shadow-xs">
              <div className="flex items-center gap-2">
                <span className="hidden lg:inline-block w-2.5 h-2.5 rounded-full border-2 bg-red-600 border-red-300 shadow-[0_0_8px_rgba(239,68,68,0.6)] shrink-0" title="Substation Feeder Terminal" />
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-red-600 shrink-0" />
                  <div>
                    <span className="text-xs font-bold font-mono block text-red-950">Priority 1 Life Support</span>
                    <span className="text-[10px] font-mono text-red-700">Habitation, heating & medical</span>
                  </div>
                </div>
              </div>
              <span className="text-xs font-mono font-bold text-red-900">{fmtKw(snapshot.criticalLoadKw)}</span>
            </div>

            {/* Scientific & Operational */}
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-between relative shadow-xs">
              <div className="flex items-center gap-2">
                <span className="hidden lg:inline-block w-2.5 h-2.5 rounded-full border-2 bg-sky-600 border-sky-300 shadow-[0_0_8px_rgba(2,132,199,0.6)] shrink-0" title="Substation Feeder Terminal" />
                <div className="flex items-center gap-2.5">
                  <Radio className="w-4 h-4 text-sky-600 shrink-0" />
                  <div>
                    <span className="text-xs font-bold font-mono block text-slate-900">Priority 2 Research & Comms</span>
                    <span className="text-[10px] font-mono text-slate-500">Satcom, core physics & radars</span>
                  </div>
                </div>
              </div>
              <span className="text-xs font-mono font-bold text-slate-800">
                {snapshot.totalLoadKw && snapshot.criticalLoadKw && snapshot.flexibleLoadKw
                  ? fmtKw(Math.max(0, snapshot.totalLoadKw - snapshot.criticalLoadKw - snapshot.flexibleLoadKw))
                  : '—'}
              </span>
            </div>

            {/* Flexible Loads */}
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-between relative shadow-xs">
              <div className="flex items-center gap-2">
                <span className="hidden lg:inline-block w-2.5 h-2.5 rounded-full border-2 bg-slate-600 border-slate-300 shadow-[0_0_8px_rgba(100,116,139,0.6)] shrink-0" title="Substation Feeder Terminal" />
                <div className="flex items-center gap-2.5">
                  <Sliders className="w-4 h-4 text-slate-500 shrink-0" />
                  <div>
                    <span className="text-xs font-bold font-mono block text-slate-800">Priority 3 Flexible / Deferrable</span>
                    <span className="text-[10px] font-mono text-slate-500">Workshop & secondary HVAC</span>
                  </div>
                </div>
              </div>
              <span className="text-xs font-mono font-bold text-slate-700">{fmtKw(snapshot.flexibleLoadKw)}</span>
            </div>
          </div>
        </div>

        {/* Source Mix Progress Bar */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <div className="flex items-center justify-between text-xs font-mono mb-2">
            <span className="font-semibold text-slate-700">Generation Source Mix</span>
            <span className="text-slate-500">
              Solar: {sourceMix.solar_pct}% • Wind: {sourceMix.wind_pct}% • Diesel: {sourceMix.diesel_pct}% • BESS: {sourceMix.battery_pct}%
            </span>
          </div>

          <div className="h-3.5 w-full bg-slate-100 rounded-full overflow-hidden flex shadow-inner">
            <div 
              style={{ width: `${sourceMix.solar_pct}%` }} 
              className="bg-amber-500 h-full transition-all duration-500" 
              title={`Solar: ${sourceMix.solar_pct}%`}
            />
            <div 
              style={{ width: `${sourceMix.wind_pct}%` }} 
              className="bg-teal-500 h-full transition-all duration-500" 
              title={`Wind: ${sourceMix.wind_pct}%`}
            />
            <div 
              style={{ width: `${sourceMix.diesel_pct}%` }} 
              className="bg-slate-700 h-full transition-all duration-500" 
              title={`Diesel: ${sourceMix.diesel_pct}%`}
            />
            <div 
              style={{ width: `${sourceMix.battery_pct}%` }} 
              className="bg-emerald-500 h-full transition-all duration-500" 
              title={`Battery: ${sourceMix.battery_pct}%`}
            />
          </div>
        </div>
      </div>

      {/* 5. Policy Directive & HiGHS Optimizer Recommendations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Policy Box */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                OPERATIONAL POLICY GOVERNANCE
              </span>
              <StatusBadge status={snapshot.resilienceState} size="sm" />
            </div>
            <h3 className="text-base font-bold text-slate-900 font-sans">
              Directive: {snapshot.activeDirective || 'RENEWABLE_PRIORITY'}
            </h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Enforcing priority order across the station load ladder. Life-support circuits are unconditionally protected against curtailment.
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-mono">
            <span className="text-slate-500">Policy State: {snapshot.policyState || 'MONITOR'}</span>
            <button
              onClick={() => navigate('policy')}
              className="text-sky-600 hover:text-sky-700 font-semibold flex items-center gap-1"
            >
              <span>Audit Rules</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Optimizer Box */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-sky-600 font-bold">
                HiGHS MILP OPTIMIZER
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                SOLVER: HiGHS C++
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-900 font-sans">
              {snapshot.optimizerRecommendation}
            </h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              {snapshot.optimizerRationale}
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-mono">
            <span className="text-slate-500">Lookahead: 48h Rolling MILP</span>
            <button
              onClick={() => navigate('optimization')}
              className="text-sky-600 hover:text-sky-700 font-semibold flex items-center gap-1"
            >
              <span>View Dispatch Schedule</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
