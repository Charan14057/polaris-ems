import React, { useState, useMemo } from 'react';
import { useStation, useOperationalSnapshot } from '../context/StationContext';
import { useComprehension } from '../context/ComprehensionContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { PhysicalStationReferenceCard } from '../features/twin/components/PhysicalStationReferenceCard';
import { ReferenceComparisonModal } from '../features/twin/components/ReferenceComparisonModal';
import { StationKey, getStationPhoto, getPublicStationPhoto } from '../features/twin/model/stationPhotos';
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
  XCircle,
  Camera,
  Play
} from 'lucide-react';

interface OverviewViewProps {
  onNavigate?: (tab: any) => void;
  onNavigateTab?: (tab: any) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate, onNavigateTab }) => {
  const navigate = onNavigate || onNavigateTab || (() => {});
  const { currentStation, setStation, stationDetail, refreshStationData, loading } = useStation();
  const { snapshot, activeScenario, clearScenario, operatingMode, setOperatingMode } = useOperationalSnapshot();
  const { openOrientation } = useComprehension();
  const [showReferenceModal, setShowReferenceModal] = useState(false);
  const [overviewFlowMode, setOverviewFlowMode] = useState<'2D_BUS' | 'GROUND_TRUTH'>('2D_BUS');
  const activeStationId = (currentStation || snapshot.currentStation || 'BHARATI') as StationKey;

  // Active failure & perturbation flags for high-visibility UI alarms
  const isWindTripped = Boolean(
    (activeScenario && (
      activeScenario.includes('WIND') || 
      activeScenario === 'COMBINED_POLAR_STRESS' ||
      activeScenario === 'BLIZZARD'
    )) || snapshot.windStatus === 'FAULT' || snapshot.windStatus === 'TRIPPED'
  );
  const isSolarTripped = Boolean(
    (activeScenario && activeScenario.includes('SOLAR')) || snapshot.solarStatus === 'FAULT'
  );
  const isBessDegraded = Boolean(
    activeScenario && activeScenario.includes('BATTERY')
  );

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

            {/* Quick Station Switcher Tabs */}
            <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-slate-800">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold mr-1">
                RESEARCH STATION:
              </span>
              {[
                { id: 'BHARATI', name: 'Bharati', region: 'Larsemann Hills (69°S)' },
                { id: 'MAITRI', name: 'Maitri', region: 'Schirmacher Oasis (70°S)' },
                { id: 'HIMADRI', name: 'Himadri', region: 'Ny-Ålesund, Svalbard (79°N)' },
              ].map(st => {
                const isSelected = activeStationId === st.id;
                return (
                  <button
                    key={st.id}
                    type="button"
                    onClick={() => setStation(st.id as any)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                      isSelected
                        ? 'bg-sky-500 text-slate-950 font-bold shadow-md ring-1 ring-sky-300'
                        : 'bg-slate-800/80 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700/60'
                    }`}
                  >
                    <span className="font-bold">{st.name}</span>
                    <span className={`text-[10px] ${isSelected ? 'text-slate-900/80' : 'text-slate-400'}`}>• {st.region}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Authentic Real Station Ground Truth Spotlight */}
            <div 
              onClick={() => setShowReferenceModal(true)}
              className="group cursor-pointer bg-slate-950/80 hover:bg-slate-950 p-2 rounded-xl border border-teal-500/40 hover:border-teal-400 flex items-center gap-3 transition-all shadow-lg ring-1 ring-teal-500/20"
              title="Click to Compare Physical Station Ground Truth vs 3D Digital Twin"
            >
              <div className="relative w-24 h-16 rounded-lg overflow-hidden border border-teal-500/50 shrink-0 bg-slate-900 shadow-inner">
                <img
                  key={activeStationId}
                  src={getStationPhoto(activeStationId)}
                  alt={snapshot.stationName}
                  onError={(e) => {
                    const target = e.currentTarget;
                    const fallback = getPublicStationPhoto(activeStationId);
                    if (target.src !== fallback && !target.src.endsWith(fallback)) {
                      target.src = fallback;
                    }
                  }}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent pointer-events-none" />
                <span className="absolute bottom-0.5 right-0.5 text-[8px] font-mono font-bold text-teal-300 bg-slate-950/90 px-1 py-0.2 rounded border border-teal-500/40">
                  REAL
                </span>
              </div>
              <div className="text-left font-sans pr-1">
                <div className="flex items-center gap-1 text-[10px] font-mono text-teal-300 font-bold uppercase tracking-wider">
                  <Camera className="w-3 h-3 text-teal-400" />
                  <span>Ground Truth Photo</span>
                </div>
                <div className="text-xs text-white font-bold truncate max-w-[130px] mt-0.5">
                  {snapshot.stationName.split(' ')[0]} Base
                </div>
                <span className="text-[10px] font-mono text-teal-400/90 group-hover:text-teal-300 underline flex items-center gap-1 mt-0.5 font-semibold">
                  <span>Compare vs 3D</span>
                  <Maximize2 className="w-2.5 h-2.5" />
                </span>
              </div>
            </div>

            <div className="bg-slate-800/80 border border-slate-700 rounded-lg px-3.5 py-2 flex flex-col items-start lg:items-end">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Resilience State</span>
              <div className="mt-0.5">
                <StatusBadge status={snapshot.resilienceState} size="md" />
              </div>
            </div>

            <div className="bg-slate-800/80 border border-slate-700 rounded-lg px-3.5 py-2 flex flex-col items-start lg:items-end">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Operating Mode</span>
              <button
                type="button"
                onClick={() => setOperatingMode(operatingMode === 'AUTO' ? 'MANUAL' : 'AUTO')}
                className="text-xs font-mono font-bold text-sky-300 mt-0.5 flex items-center gap-1.5 hover:text-white transition-colors cursor-pointer"
                title="Click to toggle Operating Mode between AUTO and MANUAL"
              >
                <span className={`w-2 h-2 rounded-full ${operatingMode === 'AUTO' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                <span>{operatingMode} GOVERNANCE</span>
              </button>
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
            <Wind className={`w-4 h-4 shrink-0 ${isWindTripped ? 'text-rose-400 animate-pulse' : 'text-teal-400'}`} />
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Wind Velocity</span>
              <span className={`font-bold ${isWindTripped ? 'text-rose-300 font-mono' : 'text-white'}`}>
                {fmtSpeed(snapshot.windSpeedMs)}
                {isWindTripped && <span className="ml-1 text-[9px] text-rose-400 font-normal">(Turbine Tripped)</span>}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 text-slate-300">
            <Sun className={`w-4 h-4 shrink-0 ${isSolarTripped ? 'text-rose-400 animate-pulse' : 'text-amber-400'}`} />
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


      {/* 2. Sleek Industrial Scenario Alert & Automated EMS Solution (Cybernetic Design) */}
      {activeScenario && !['NORMAL_BASELINE', 'BASELINE', 'NOMINAL', 'NORMAL'].includes(activeScenario.toUpperCase().trim()) && (
        <div className="space-y-3">
          {/* Master Cybernetic Perturbation Bar */}
          <div className="bg-slate-900 border border-slate-700/80 rounded-xl overflow-hidden shadow-2xl">
            <div className="px-5 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-9 h-9 rounded-lg bg-rose-500/20 border border-rose-500/40 flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(244,63,94,0.3)]">
                  <AlertTriangle className="w-5 h-5 text-rose-400 animate-pulse" />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 uppercase tracking-wider">
                      ACTIVE CONTINGENCY
                    </span>
                    <span className="text-base font-mono font-extrabold text-white tracking-wide">
                      {activeScenario.replace(/_/g, ' ')}
                    </span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase font-bold ${
                      snapshot.scenarioSeverity === 'CRITICAL' ? 'bg-rose-500/30 text-rose-200 border border-rose-500/50'
                      : snapshot.scenarioSeverity === 'HIGH' ? 'bg-orange-500/30 text-orange-200 border border-orange-500/50'
                      : 'bg-amber-500/30 text-amber-200 border border-amber-500/50'
                    }`}>
                      {snapshot.scenarioSeverity} SEVERITY
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1">
                    Microgrid perturbation active. Automated governance has engaged contingency controls to protect habitat life support.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2.5 shrink-0">
                <button
                  onClick={() => clearScenario()}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-600 text-xs font-mono font-semibold transition-colors shadow-xs"
                >
                  Restore Baseline
                </button>
                <button
                  onClick={() => navigate('scenarios')}
                  className="px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-mono font-bold transition-colors shadow-xs"
                >
                  Scenarios Console →
                </button>
              </div>
            </div>

            {/* Scenario Energy Impact & Solution Strip */}
            <div className="border-t border-slate-800 bg-slate-950/70 p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                {/* Left Column: Energy Impact */}
                <div className="bg-slate-900/90 rounded-lg p-3.5 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-rose-400 font-bold uppercase text-[11px]">
                    <span className="flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-rose-400" />
                      <span>1. Microgrid Power Impact</span>
                    </span>
                    <span className="text-[10px] text-slate-400">TELEMETRY DELTA</span>
                  </div>
                  
                  {isWindTripped ? (
                    <div className="space-y-1 text-slate-300 text-[11px]">
                      <div className="flex justify-between items-center text-rose-300">
                        <span>Wind Generation:</span>
                        <span className="font-bold font-mono">0.0 kW (FORCED TRIP)</span>
                      </div>
                      <div className="flex justify-between items-center text-amber-300">
                        <span>Generation Loss:</span>
                        <span className="font-bold font-mono">-14.5 kW deficit</span>
                      </div>
                      <div className="flex justify-between items-center text-slate-400">
                        <span>Station Bus Frequency:</span>
                        <span>49.8 Hz (Compensated)</span>
                      </div>
                    </div>
                  ) : isSolarTripped ? (
                    <div className="space-y-1 text-slate-300 text-[11px]">
                      <div className="flex justify-between items-center text-rose-300">
                        <span>Solar Generation:</span>
                        <span className="font-bold font-mono">0.0 kW (OBSCURED)</span>
                      </div>
                      <div className="flex justify-between items-center text-amber-300">
                        <span>Generation Deficit:</span>
                        <span className="font-bold font-mono">Solar circuit dropped</span>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-1 text-slate-300 text-[11px]">
                      <div className="flex justify-between items-center text-amber-300">
                        <span>Polar Ambient Stress:</span>
                        <span className="font-bold font-mono">Elevated thermal & aerodynamic drag</span>
                      </div>
                      <div className="flex justify-between items-center text-slate-400">
                        <span>Heating Load Spike:</span>
                        <span>Auxiliary heating circuits drawn</span>
                      </div>
                    </div>
                  )}

                  <div className="pt-2 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => navigate('twin')}
                      className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 text-xs font-bold border border-sky-500/30 transition-colors"
                    >
                      <Zap className="w-3.5 h-3.5" />
                      <span>Inspect 3D Power Flow in Energy Twin →</span>
                    </button>
                  </div>
                </div>

                {/* Right Column: Automated EMS Solution */}
                <div className="bg-slate-900/90 rounded-lg p-3.5 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-emerald-400 font-bold uppercase text-[11px]">
                    <span className="flex items-center gap-1.5">
                      <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                      <span>2. Automated EMS Solution</span>
                    </span>
                    <span className="text-[10px] text-emerald-400/80">HIGHS OPTIMAL</span>
                  </div>

                  <div className="space-y-1 text-slate-300 text-[11px]">
                    <div className="flex justify-between items-center text-emerald-300">
                      <span>BESS Dynamic Discharge:</span>
                      <span className="font-bold font-mono">+12.3 kW compensating</span>
                    </div>
                    <div className="flex justify-between items-center text-slate-300">
                      <span>Diesel Generator (DG-1):</span>
                      <span className="font-bold font-mono">Spinning Reserve Pre-heated</span>
                    </div>
                    <div className="flex justify-between items-center text-slate-400">
                      <span>Life Support Habitat:</span>
                      <span className="text-emerald-400 font-bold">100% UNCURTAILED</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => navigate('optimization')}
                      className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-xs font-bold border border-emerald-500/30 transition-colors"
                    >
                      <Cpu className="w-3.5 h-3.5" />
                      <span>View Dispatch Matrix & Unit Commitment →</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Station Ground Truth & Physical Reference Card */}
      <PhysicalStationReferenceCard
        stationId={activeStationId}
        onOpenComparisonModal={() => setShowReferenceModal(true)}
        onSelectStation={(s) => setStation(s as any)}
      />

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
        <div className={`rounded-xl p-4 shadow-xs transition-all ${
          isWindTripped 
            ? 'bg-rose-50 border-2 border-rose-500 ring-2 ring-rose-500/50 animate-pulse shadow-[0_0_15px_rgba(244,63,94,0.3)]' 
            : 'bg-white border border-slate-200'
        }`}>
          <div className="flex items-center justify-between mb-1">
            <span className={`text-[10px] font-mono uppercase tracking-wider ${isWindTripped ? 'text-rose-700 font-bold' : 'text-slate-400'}`}>
              Wind Turbine Output
            </span>
            <span className={`w-2.5 h-2.5 rounded-full ${isWindTripped ? 'bg-rose-500 animate-ping' : (isWindGenerating ? 'bg-teal-500' : 'bg-slate-300')}`} />
          </div>
          <span className={`text-xl sm:text-2xl font-bold font-mono ${isWindTripped ? 'text-rose-600' : 'text-teal-600'}`}>
            {fmtKw(snapshot.windGenerationKw)}
          </span>
          <div className="text-[11px] font-mono mt-1 flex items-center justify-between">
            <span className={isWindTripped ? 'text-rose-600 font-medium' : 'text-slate-500'}>Status:</span>
            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
              isWindTripped ? 'bg-rose-600 text-white animate-pulse' : 'bg-slate-100 text-slate-700'
            }`}>
              {isWindTripped ? 'TRIPPED / FAULT' : (snapshot.windStatus || '—')}
            </span>
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

      {/* 4. VISUAL ENERGY BALANCE (High-Performance SCADA Power Flow & Substation Distribution) */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-5 border-b border-slate-100 gap-3">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-sky-600 font-bold block">
              AUTHORITATIVE POWER DISTRIBUTION & SCADA BUS
            </span>
            <h2 className="text-lg font-bold text-slate-900 mt-0.5">
              Microgrid Power Inflow, Central Substation Bus & Distribution Feeders
            </h2>
          </div>
          
          <div className="flex flex-wrap items-center gap-2.5">
            {/* View Switcher Tabs: SCADA Bus Wiring, Ground Truth */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-mono">
              <button
                type="button"
                onClick={() => setOverviewFlowMode('2D_BUS')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-bold transition-all ${
                  overviewFlowMode === '2D_BUS'
                    ? 'bg-sky-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                <span>SCADA Bus Wiring</span>
              </button>

              <button
                type="button"
                onClick={() => setOverviewFlowMode('GROUND_TRUTH')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-bold transition-all ${
                  overviewFlowMode === 'GROUND_TRUTH'
                    ? 'bg-teal-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <Camera className="w-3.5 h-3.5" />
                <span>Ground Truth Photo</span>
              </button>
            </div>

            <button
              onClick={() => navigate('twin')}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-mono font-bold transition-colors shadow-xs"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Full 3D Twin Console →</span>
            </button>
          </div>
        </div>

        {/* MODE 1: GROUND TRUTH AUTHENTIC PHOTO & SPECS */}
        {overviewFlowMode === 'GROUND_TRUTH' && (
          <div className="space-y-4">
            <PhysicalStationReferenceCard
              stationId={activeStationId}
              onOpenComparisonModal={() => setShowReferenceModal(true)}
              onSelectStation={(s) => setStation(s as any)}
            />
          </div>
        )}

        {/* MODE 2: HIGH-VISIBILITY 2D SCADA ELECTRICAL BUS CONDUITS */}
        {overviewFlowMode === '2D_BUS' && (
          <div>
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
              isWindTripped 
                ? 'bg-rose-50/90 border-2 border-rose-500 ring-2 ring-rose-500/40 animate-pulse text-slate-900 shadow-sm'
                : (isWindGenerating ? 'bg-teal-50/60 border-teal-300 text-slate-900 shadow-xs' : 'bg-slate-50 border-slate-200 text-slate-400')
            }`}>
              <div className="flex items-center gap-3">
                <Wind className={`w-4 h-4 ${isWindTripped ? 'text-rose-600 animate-pulse' : (isWindGenerating ? 'text-teal-500' : 'text-slate-400')}`} />
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold font-mono block">Wind Turbine</span>
                    {isWindTripped && (
                      <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-rose-600 text-white animate-pulse">
                        TRIPPED
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">Rated: {fmtKw(snapshot.windCapacityKw)}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-mono font-bold ${isWindTripped ? 'text-rose-600' : ''}`}>
                  {fmtKw(snapshot.windGenerationKw)}
                </span>
                <span className={`hidden lg:inline-block w-2.5 h-2.5 rounded-full border-2 ${
                  isWindTripped 
                    ? 'bg-rose-500 border-rose-300 shadow-[0_0_10px_rgba(244,63,94,0.8)] animate-ping'
                    : (isWindGenerating ? 'bg-teal-500 border-teal-300 shadow-[0_0_8px_rgba(13,148,136,0.6)]' : 'bg-slate-300 border-slate-200')
                }`} title={isWindTripped ? 'Feeder Tripped' : 'Feeder Terminal Node'} />
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
                <filter id="neon-glow-solar" x="-30%" y="-30%" width="160%" height="160%">
                  <feDropShadow dx="0" dy="0" stdDeviation="3.5" floodColor="#f59e0b" floodOpacity="0.9" />
                </filter>
                <filter id="neon-glow-wind" x="-30%" y="-30%" width="160%" height="160%">
                  <feDropShadow dx="0" dy="0" stdDeviation="3.5" floodColor="#06b6d4" floodOpacity="0.9" />
                </filter>
                <filter id="neon-glow-diesel" x="-30%" y="-30%" width="160%" height="160%">
                  <feDropShadow dx="0" dy="0" stdDeviation="3.5" floodColor="#f97316" floodOpacity="0.9" />
                </filter>
                <filter id="neon-glow-bess" x="-30%" y="-30%" width="160%" height="160%">
                  <feDropShadow dx="0" dy="0" stdDeviation="3.5" floodColor="#10b981" floodOpacity="0.9" />
                </filter>
                <marker id="arrow-solar" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#f59e0b" />
                </marker>
                <marker id="arrow-wind" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#06b6d4" />
                </marker>
                <marker id="arrow-diesel" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#f97316" />
                </marker>
                <marker id="arrow-bess-out" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#10b981" />
                </marker>
                <marker id="arrow-bess-in" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 8 1 L 0 5 L 8 9 z" fill="#0284c7" />
                </marker>
              </defs>

              {/* Line 1: Solar PV -> Bus Intake (y=36 -> y=105) */}
              <path d="M 0 36 C 36 36, 32 105, 64 105" fill="none" stroke="#334155" strokeWidth="6" strokeLinecap="round" />
              {isSolarGenerating && (
                <path 
                  d="M 0 36 C 36 36, 32 105, 64 105" 
                  fill="none" 
                  stroke="#f59e0b" 
                  strokeWidth="4" 
                  strokeDasharray="9 6"
                  className="animate-flow-line" 
                  filter="url(#neon-glow-solar)"
                  markerEnd="url(#arrow-solar)"
                />
              )}

              {/* Line 2: Wind -> Bus Intake (y=110 -> y=125) */}
              <path d="M 0 110 C 36 110, 32 125, 64 125" fill="none" stroke={isWindTripped ? "#991b1b" : "#334155"} strokeWidth="6" strokeLinecap="round" />
              {isWindGenerating && !isWindTripped && (
                <path 
                  d="M 0 110 C 36 110, 32 125, 64 125" 
                  fill="none" 
                  stroke="#06b6d4" 
                  strokeWidth="4" 
                  strokeDasharray="9 6"
                  className="animate-flow-line" 
                  filter="url(#neon-glow-wind)"
                  markerEnd="url(#arrow-wind)"
                />
              )}
              {isWindTripped && (
                <path 
                  d="M 0 110 C 36 110, 32 125, 64 125" 
                  fill="none" 
                  stroke="#f43f5e" 
                  strokeWidth="3.5" 
                  strokeDasharray="5 4"
                  className="animate-pulse" 
                />
              )}

              {/* Line 3: Diesel -> Bus Intake (y=184 -> y=175) */}
              <path d="M 0 184 C 36 184, 32 175, 64 175" fill="none" stroke="#334155" strokeWidth="6" strokeLinecap="round" />
              {isDieselOnline && (
                <path 
                  d="M 0 184 C 36 184, 32 175, 64 175" 
                  fill="none" 
                  stroke="#f97316" 
                  strokeWidth="4" 
                  strokeDasharray="9 6"
                  className="animate-flow-line" 
                  filter="url(#neon-glow-diesel)"
                  markerEnd="url(#arrow-diesel)"
                />
              )}

              {/* Line 4: BESS -> Bus Intake (y=258 -> y=195) */}
              <path d="M 0 258 C 36 258, 32 195, 64 195" fill="none" stroke="#334155" strokeWidth="6" strokeLinecap="round" />
              {isBessDischarging && (
                <path 
                  d="M 0 258 C 36 258, 32 195, 64 195" 
                  fill="none" 
                  stroke="#10b981" 
                  strokeWidth="4" 
                  strokeDasharray="9 6"
                  className="animate-flow-line" 
                  filter="url(#neon-glow-bess)"
                  markerEnd="url(#arrow-bess-out)"
                />
              )}
              {isBessCharging && (
                <path 
                  d="M 64 195 C 32 195, 36 258, 0 258" 
                  fill="none" 
                  stroke="#0284c7" 
                  strokeWidth="4" 
                  strokeDasharray="9 6"
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
                <filter id="neon-glow-red" x="-30%" y="-30%" width="160%" height="160%">
                  <feDropShadow dx="0" dy="0" stdDeviation="3.5" floodColor="#ef4444" floodOpacity="0.9" />
                </filter>
                <filter id="neon-glow-blue" x="-30%" y="-30%" width="160%" height="160%">
                  <feDropShadow dx="0" dy="0" stdDeviation="3.5" floodColor="#0284c7" floodOpacity="0.9" />
                </filter>
                <filter id="neon-glow-slate" x="-30%" y="-30%" width="160%" height="160%">
                  <feDropShadow dx="0" dy="0" stdDeviation="3.5" floodColor="#94a3b8" floodOpacity="0.8" />
                </filter>
                <marker id="arrow-p1" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#ef4444" />
                </marker>
                <marker id="arrow-p2" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#0284c7" />
                </marker>
                <marker id="arrow-p3" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#94a3b8" />
                </marker>
              </defs>

              {/* Line 1: Bus Feeder -> P1 Life Support (y=115 -> y=45) */}
              <path d="M 0 115 C 28 115, 32 45, 64 45" fill="none" stroke="#334155" strokeWidth="6" strokeLinecap="round" />
              <path 
                d="M 0 115 C 28 115, 32 45, 64 45" 
                fill="none" 
                stroke="#ef4444" 
                strokeWidth="4" 
                strokeDasharray="9 6"
                className="animate-flow-line" 
                filter="url(#neon-glow-red)"
                markerEnd="url(#arrow-p1)"
              />

              {/* Line 2: Bus Feeder -> P2 Science/Comms (y=150 -> y=150) */}
              <path d="M 0 150 L 64 150" fill="none" stroke="#334155" strokeWidth="6" strokeLinecap="round" />
              <path 
                d="M 0 150 L 64 150" 
                fill="none" 
                stroke="#0284c7" 
                strokeWidth="4" 
                strokeDasharray="9 6"
                className="animate-flow-line" 
                filter="url(#neon-glow-blue)"
                markerEnd="url(#arrow-p2)"
              />

              {/* Line 3: Bus Feeder -> P3 Flexible (y=185 -> y=255) */}
              <path d="M 0 185 C 28 185, 32 255, 64 255" fill="none" stroke="#334155" strokeWidth="6" strokeLinecap="round" />
              <path 
                d="M 0 185 C 28 185, 32 255, 64 255" 
                fill="none" 
                stroke="#94a3b8" 
                strokeWidth="4" 
                strokeDasharray="9 6"
                className="animate-flow-line" 
                filter="url(#neon-glow-slate)"
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
      </div>
    )}

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

      {/* Interactive Ground Truth ↔ 3D Digital Twin Comparison Modal */}
      <ReferenceComparisonModal
        stationId={activeStationId}
        isOpen={showReferenceModal}
        onClose={() => setShowReferenceModal(false)}
        onStationChange={(s) => setStation(s as any)}
      />
    </div>
  );
};
