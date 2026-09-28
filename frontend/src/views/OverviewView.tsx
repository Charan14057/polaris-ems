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

      {/* 2. Active Stress Scenario Alert Banner (if perturbed) */}
      {activeScenario && (
        <div className="bg-amber-950/40 border border-amber-500/30 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-amber-200">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center shrink-0">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 uppercase">
                  ACTIVE STRESS SCENARIO
                </span>
                <span className="text-xs font-mono font-bold text-white">{activeScenario}</span>
              </div>
              <p className="text-xs text-amber-300/80 mt-0.5">
                Microgrid physical state is currently perturbed. Downstream generation, loads, and resilience reflect this regime.
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
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
            >
              View Scenarios →
            </button>
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

        {/* Visual Flow Representation */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-center">
          
          {/* Column A: Generation Sources (4 cols) */}
          <div className="lg:col-span-4 space-y-2.5">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block px-1">
              Generation Assets & Storage
            </span>

            {/* Solar Box */}
            <div className={`p-3 rounded-lg border flex items-center justify-between transition-colors ${
              isSolarGenerating ? 'bg-amber-50/50 border-amber-200 text-slate-900' : 'bg-slate-50 border-slate-200 text-slate-400'
            }`}>
              <div className="flex items-center gap-3">
                <Sun className={`w-4 h-4 ${isSolarGenerating ? 'text-amber-500' : 'text-slate-400'}`} />
                <div>
                  <span className="text-xs font-bold font-mono block">Solar PV Array</span>
                  <span className="text-[10px] font-mono text-slate-500">Peak: {fmtKw(snapshot.solarCapacityKw)}</span>
                </div>
              </div>
              <span className="text-xs font-mono font-bold">{fmtKw(snapshot.solarGenerationKw)}</span>
            </div>

            {/* Wind Box */}
            <div className={`p-3 rounded-lg border flex items-center justify-between transition-colors ${
              isWindGenerating ? 'bg-teal-50/50 border-teal-200 text-slate-900' : 'bg-slate-50 border-slate-200 text-slate-400'
            }`}>
              <div className="flex items-center gap-3">
                <Wind className={`w-4 h-4 ${isWindGenerating ? 'text-teal-500' : 'text-slate-400'}`} />
                <div>
                  <span className="text-xs font-bold font-mono block">Wind Turbine</span>
                  <span className="text-[10px] font-mono text-slate-500">Rated: {fmtKw(snapshot.windCapacityKw)}</span>
                </div>
              </div>
              <span className="text-xs font-mono font-bold">{fmtKw(snapshot.windGenerationKw)}</span>
            </div>

            {/* Diesel Box */}
            <div className={`p-3 rounded-lg border flex items-center justify-between transition-colors ${
              isDieselOnline ? 'bg-slate-100 border-slate-300 text-slate-900' : 'bg-slate-50 border-slate-200 text-slate-400'
            }`}>
              <div className="flex items-center gap-3">
                <Flame className={`w-4 h-4 ${isDieselOnline ? 'text-amber-600' : 'text-slate-400'}`} />
                <div>
                  <span className="text-xs font-bold font-mono block">Diesel Generator (DG-1)</span>
                  <span className="text-[10px] font-mono text-slate-500">Capacity: {fmtKw(snapshot.dieselMaxKw)}</span>
                </div>
              </div>
              <span className="text-xs font-mono font-bold">{fmtKw(snapshot.dieselGenerationKw)}</span>
            </div>

            {/* BESS Box */}
            <div className={`p-3 rounded-lg border flex items-center justify-between transition-colors ${
              isBessDischarging ? 'bg-emerald-50/60 border-emerald-200 text-slate-900' : 
              (isBessCharging ? 'bg-sky-50/60 border-sky-200 text-slate-900' : 'bg-slate-50 border-slate-200 text-slate-500')
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
              <span className="text-xs font-mono font-bold">{fmtKw(snapshot.bessPowerKw)}</span>
            </div>
          </div>

          {/* Column B: Main Distribution Bus (4 cols) */}
          <div className="lg:col-span-4 flex flex-col items-center justify-center p-5 rounded-xl bg-slate-900 text-white border border-slate-800 shadow-md">
            <span className="text-[10px] font-mono uppercase tracking-widest text-sky-400 mb-2">
              MAIN 415V AC SYNCHRONOUS BUS
            </span>
            
            <div className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-slate-800/90 border border-slate-700 text-xs font-mono mb-3">
              <span className="text-slate-400">Total Generation Inflow</span>
              <span className="font-bold text-emerald-400">{fmtKw(snapshot.totalGenerationKw)}</span>
            </div>

            <div className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-slate-800/90 border border-slate-700 text-xs font-mono mb-3">
              <span className="text-slate-400">Total Demand Throughput</span>
              <span className="font-bold text-sky-300">{fmtKw(snapshot.totalLoadKw)}</span>
            </div>

            <div className="w-full flex items-center justify-between px-3 py-1.5 text-[11px] font-mono text-slate-400 border-t border-slate-800 pt-2">
              <span>Bus Frequency: 50.00 Hz</span>
              <span>Voltage: 415 V</span>
            </div>
          </div>

          {/* Column C: Substation Loads (4 cols) */}
          <div className="lg:col-span-4 space-y-2.5">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block px-1">
              Station Load Demands
            </span>

            {/* Critical Load */}
            <div className="p-3 rounded-lg border border-red-200 bg-red-50/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-4 h-4 text-red-600" />
                <div>
                  <span className="text-xs font-bold font-mono block text-red-950">Priority 1 Life Support</span>
                  <span className="text-[10px] font-mono text-red-700">Habitation, heating & medical</span>
                </div>
              </div>
              <span className="text-xs font-mono font-bold text-red-900">{fmtKw(snapshot.criticalLoadKw)}</span>
            </div>

            {/* Scientific & Operational */}
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Radio className="w-4 h-4 text-sky-600" />
                <div>
                  <span className="text-xs font-bold font-mono block text-slate-900">Priority 2 Research & Comms</span>
                  <span className="text-[10px] font-mono text-slate-500">Satcom, core physics & radars</span>
                </div>
              </div>
              <span className="text-xs font-mono font-bold text-slate-800">
                {snapshot.totalLoadKw && snapshot.criticalLoadKw && snapshot.flexibleLoadKw
                  ? fmtKw(Math.max(0, snapshot.totalLoadKw - snapshot.criticalLoadKw - snapshot.flexibleLoadKw))
                  : '—'}
              </span>
            </div>

            {/* Flexible Loads */}
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Sliders className="w-4 h-4 text-slate-500" />
                <div>
                  <span className="text-xs font-bold font-mono block text-slate-800">Priority 3 Flexible / Deferrable</span>
                  <span className="text-[10px] font-mono text-slate-500">Workshop & secondary HVAC</span>
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
                PHASE 6 HIGHS OPTIMIZER
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
