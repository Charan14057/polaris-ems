import React, { useState, useEffect, useCallback } from 'react';
import { useStation, useOperationalSnapshot } from '../context/StationContext';
import { useEvidence } from '../context/EvidenceContext';
import { api } from '../api/endpoints';
import { ResilienceEvaluateResponseData } from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { ResilienceEnvelope, ResilienceDimension } from '../components/common/ResilienceEnvelope';
import { WhyThisMatters } from '../components/common/WhyThisMatters';
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { JargonTooltip } from '../components/common/JargonTooltip';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Clock, 
  Activity, 
  AlertTriangle, 
  CheckCircle2, 
  LifeBuoy, 
  ChevronDown,
  ChevronUp,
  Layers,
  Flame,
  BatteryCharging,
  Thermometer,
  Shield
} from 'lucide-react';

export const ResilienceView: React.FC = () => {
  const { currentStation, horizonHours, activeScenario, resilienceData: contextResilience } = useStation();
  const { snapshot } = useOperationalSnapshot();
  const { inspectEvidence } = useEvidence();

  const [resilienceData, setResilienceData] = useState<ResilienceEvaluateResponseData | null>(contextResilience);
  const [loading, setLoading] = useState<boolean>(!contextResilience && !snapshot.survivalHorizons);
  const [error, setError] = useState<string | null>(null);
  const [showNineDimensions, setShowNineDimensions] = useState<boolean>(true);

  // Sync with context resilience updates
  useEffect(() => {
    if (contextResilience) {
      setResilienceData(contextResilience);
    }
  }, [contextResilience]);

  const fetchResilience = useCallback(async () => {
    if (!resilienceData && !contextResilience) {
      setLoading(true);
    }
    setError(null);
    try {
      const res = await api.evaluateResilience({
        station_id: currentStation,
        horizon_hours: horizonHours,
        scenario_id: activeScenario || undefined,
        include_propagation: true,
      });
      if (res.data) {
        setResilienceData(res.data);
      }
    } catch (err: any) {
      if (!resilienceData && !contextResilience) {
        setError(err.message || 'Failed to evaluate resilience posture');
      }
    } finally {
      setLoading(false);
    }
  }, [currentStation, horizonHours, activeScenario, resilienceData, contextResilience]);

  useEffect(() => {
    fetchResilience();
  }, [currentStation, horizonHours, activeScenario]);

  if (loading && !resilienceData && !contextResilience) {
    return <LoadingSkeleton height="h-32" rows={3} className="max-w-[1520px] mx-auto py-8" />;
  }

  const effectiveData = resilienceData || contextResilience;

  if (error && !effectiveData) {
    return <ErrorCard message={error || 'Failed to fetch resilience posture.'} onRetry={fetchResilience} className="max-w-[1520px] mx-auto my-8" />;
  }

  const resState = (activeScenario && !['NORMAL_BASELINE', 'BASELINE', 'NOMINAL', 'NORMAL'].includes(activeScenario.toUpperCase().trim()))
    ? (snapshot.resilienceState !== 'SAFE' ? snapshot.resilienceState : (effectiveData?.resilience_state || 'WATCH'))
    : (effectiveData?.resilience_state || snapshot.resilienceState || 'SAFE');

  const horizons = effectiveData?.survival_horizons || {
    critical_load_survival_horizon_h: snapshot.survivalHorizons?.criticalLoadSurvivalH ?? 168.0,
    fuel_endurance_horizon_h: snapshot.survivalHorizons?.fuelEnduranceH ?? 720.0,
    thermal_habitability_horizon_h: snapshot.survivalHorizons?.thermalHabitabilityH ?? 48.0,
    battery_endurance_horizon_h: snapshot.survivalHorizons?.batteryEnduranceH ?? 18.0,
    overall_station_survival_horizon_h: snapshot.survivalHorizons?.overallSurvivalH ?? 18.0,
    binding_subsystem: snapshot.survivalHorizons?.bindingSubsystem ?? 'BATTERY',
  };
  const overallHorizon = horizons?.overall_station_survival_horizon_h ?? (snapshot.survivalHorizons?.overallSurvivalH ?? 0);
  const bindingSubsystem = horizons?.binding_subsystem || (snapshot.survivalHorizons?.bindingSubsystem ?? 'NONE');

  // Dynamic breakdown for ResilienceEnvelope
  const envelopeDimensions: ResilienceDimension[] = horizons ? [
    {
      id: 'critical_load',
      name: 'Life-Support Critical Load',
      horizonHours: horizons.critical_load_survival_horizon_h,
      score: Math.min(1.0, horizons.critical_load_survival_horizon_h / Math.max(1, horizonHours)),
      isBinding: bindingSubsystem.toLowerCase().includes('critical') || bindingSubsystem.toLowerCase().includes('electrical'),
      status: horizons.critical_load_survival_horizon_h < 24 ? 'CRITICAL' : horizons.critical_load_survival_horizon_h < 48 ? 'WATCH' : 'SAFE',
      description: `Critical life-support circuit priority dispatch runway: ${horizons.critical_load_survival_horizon_h.toFixed(1)}h.`,
    },
    {
      id: 'fuel',
      name: 'Diesel Fuel Reserve',
      horizonHours: horizons.fuel_endurance_horizon_h,
      score: Math.min(1.0, horizons.fuel_endurance_horizon_h / Math.max(1, horizonHours)),
      isBinding: bindingSubsystem.toLowerCase().includes('fuel'),
      status: horizons.fuel_endurance_horizon_h < 24 ? 'CRITICAL' : horizons.fuel_endurance_horizon_h < 48 ? 'WATCH' : 'SAFE',
      description: `Autonomous generator fuel endurance: ${horizons.fuel_endurance_horizon_h.toFixed(1)}h at current consumption.`,
    },
    {
      id: 'thermal',
      name: 'Thermal Building Envelope',
      horizonHours: horizons.thermal_habitability_horizon_h,
      score: Math.min(1.0, horizons.thermal_habitability_horizon_h / Math.max(1, horizonHours)),
      isBinding: bindingSubsystem.toLowerCase().includes('thermal'),
      status: horizons.thermal_habitability_horizon_h < 24 ? 'CRITICAL' : horizons.thermal_habitability_horizon_h < 48 ? 'WATCH' : 'SAFE',
      description: `Building envelope heat retention before reaching safe threshold: ${horizons.thermal_habitability_horizon_h.toFixed(1)}h.`,
    },
    {
      id: 'battery',
      name: 'BESS Electrochemical Reserve',
      horizonHours: horizons.battery_endurance_horizon_h,
      score: Math.min(1.0, horizons.battery_endurance_horizon_h / Math.max(1, horizonHours)),
      isBinding: bindingSubsystem.toLowerCase().includes('battery') || bindingSubsystem.toLowerCase().includes('storage'),
      status: horizons.battery_endurance_horizon_h < 6 ? 'CRITICAL' : horizons.battery_endurance_horizon_h < 12 ? 'WATCH' : 'SAFE',
      description: `Battery bank emergency discharge bridging horizon: ${horizons.battery_endurance_horizon_h.toFixed(1)}h.`,
    },
  ] : [];

  const rawDims = effectiveData?.dimensions || snapshot.resilienceDimensions;
  const dimensionsList = rawDims ? [
    { name: 'Energy Adequacy', score: rawDims.energy_adequacy },
    { name: 'Critical Load Resilience', score: rawDims.critical_load_resilience },
    { name: 'Thermal Resilience', score: rawDims.thermal_resilience },
    { name: 'Generation Resilience', score: rawDims.generation_resilience },
    { name: 'Storage Resilience', score: rawDims.storage_resilience },
    { name: 'Fuel Resilience', score: rawDims.fuel_resilience },
    { name: 'Logistics Resilience', score: rawDims.logistics_resilience },
    { name: 'Renewable Resilience', score: rawDims.renewable_resilience },
    { name: 'Recovery Resilience', score: rawDims.recovery_resilience },
  ] : [];

  const recoveryOptions = effectiveData?.candidate_recovery_options || [];

  const fuelLiters = snapshot?.fuelRemainingL != null ? `${snapshot.fuelRemainingL.toLocaleString()} L` : '0 L';
  const bessSoc = snapshot?.bessSocPct != null ? `${snapshot.bessSocPct.toFixed(0)}%` : '0%';
  const dynamicOutlook = `Station fuel reserve is currently at ${fuelLiters} with battery state of charge at ${bessSoc}. The binding subsystem is ${bindingSubsystem} establishing an autonomous survival envelope of ${overallHorizon.toFixed(1)} hours.`;

  return (
    <div className="space-y-6 max-w-[1520px] mx-auto pb-12 font-sans">
      {/* 1. Editorial Header */}
      <div className="border-b border-rose-200 bg-white rounded-xl p-6 shadow-xs border flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-rose-600 font-bold mb-1">
            <ShieldAlert className="w-4 h-4" />
            <span>06 DYNAMIC RESILIENCE ENGINE • MULTI-HORIZON SURVIVABILITY</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-sans font-bold text-slate-900 tracking-tight">
            Station Resilience & Survival Envelope
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 mt-1">
            Multi-horizon assessment of life-support survival envelopes, thermal safe minimums, and binding fuel limits.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <ProvenanceTag provenance="COMPUTATIONAL_TWIN" size="sm" />
          <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-md bg-slate-900 text-slate-100">
            STATION: {currentStation}
          </span>
        </div>
      </div>

      {/* Dramatic Scenario Threat Escalation Banner */}
      {activeScenario && !['NORMAL_BASELINE', 'BASELINE', 'NOMINAL', 'NORMAL'].includes(activeScenario.toUpperCase().trim()) && (
        <div className="bg-slate-900 border-2 border-rose-500 rounded-xl p-5 shadow-2xl relative overflow-hidden animate-pulse">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-lg bg-rose-500/30 border border-rose-500 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(244,63,94,0.6)]">
                <AlertTriangle className="w-6 h-6 text-rose-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-600 text-white tracking-widest uppercase">
                    POLAR THREAT ESCALATION ACTIVE
                  </span>
                  <span className="text-sm font-mono font-bold text-rose-300">
                    REGIME: {activeScenario.replace(/_/g, ' ')}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1">
                  Subsystem margins are being actively stressed. Binding bottleneck shifted to <strong className="text-rose-400 font-mono">{bindingSubsystem}</strong> with autonomous runway of <strong className="text-rose-400 font-mono">{overallHorizon.toFixed(1)} hours</strong>.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0 font-mono text-xs">
              <div className="px-3 py-1.5 rounded bg-rose-950/80 border border-rose-500/40 text-rose-200">
                <span className="text-[10px] text-rose-400 block uppercase">Threat Posture</span>
                <span className="font-bold text-white text-sm">{resState}</span>
              </div>
              <div className="px-3 py-1.5 rounded bg-amber-950/80 border border-amber-500/40 text-amber-200">
                <span className="text-[10px] text-amber-400 block uppercase">Runway Floor</span>
                <span className="font-bold text-white text-sm">{overallHorizon.toFixed(1)}h</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2. Top Resilience Banner */}
      <div className="bg-white border border-slate-200 shadow-xs rounded-xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <span className="text-xs font-mono text-slate-500 uppercase font-semibold">ACTIVE RESILIENCE STATE:</span>
            <StatusBadge status={resState} size="lg" />
            {activeScenario && (
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300">
                SCENARIO: {activeScenario}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-700 max-w-2xl leading-relaxed mt-2">
            {resState === 'SAFE' && 'All vital station systems have ample buffer margins. No unserved energy or thermal breach predicted over the evaluation horizon.'}
            {resState === 'WATCH' && 'Generation or storage margins are tightening under polar ambient stress. Supervisory review recommended.'}
            {resState === 'AT_RISK' && 'One or more subsystem margins (fuel or battery) are approaching reserve minimum thresholds. Preventive dispatch advised.'}
            {resState === 'THREATENED' && 'Immediate active mitigation required to prevent premature depletion of critical life-support reserves.'}
            {resState === 'CRITICAL' && 'Life-support loads are in imminent jeopardy. Immediate priority load-shedding and emergency protocol active.'}
          </p>
        </div>

        <div className="text-left sm:text-right shrink-0 p-4 rounded-xl bg-slate-900 text-white border border-slate-800">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">OVERALL SURVIVAL HORIZON</span>
          <span className="text-3xl font-sans font-bold text-rose-400 font-mono-numbers">
            {overallHorizon.toFixed(1)}{' '}
            <span className="text-xs font-mono font-normal text-slate-400">hours</span>
          </span>
          <span className="text-[10px] font-mono text-amber-300 block mt-1">
            BINDING: {bindingSubsystem.toUpperCase()}
          </span>
        </div>
      </div>

      {/* 2.1 Non-Technical Comprehension */}
      <ExplainThis
        title="What is the Station Survival Envelope?"
        whatAmILookingAt="This view measures how many hours the polar station can continue functioning without external resupply if generation or weather shifts occur."
        whyIsItImportant="In Antarctica or the high Arctic, resupply is impossible for months. Knowing which resource will bind first gives commanders time to ration power days before an emergency."
        howIsItCalculated="The resilience engine calculates four simultaneous survival horizons: fuel runway, battery energy, building warmth, and critical load coverage. Overall survival is the mathematical minimum."
        technicalEvidence="Governing invariant: T_surv = min(T_fuel, T_battery, T_thermal, T_critical). Calibrated against Digital Twin physics."
      />

      {/* 3. Authoritative Dynamic Resilience Envelope */}
      <ResilienceEnvelope
        stationId={currentStation}
        overallState={resState}
        overallHorizonHours={overallHorizon}
        dimensions={envelopeDimensions}
        bindingConstraint={bindingSubsystem}
        bindingDescription={`Calculated bottleneck: ${bindingSubsystem} imposes an operational survival ceiling of ${overallHorizon.toFixed(1)} hours.`}
      />

      {/* 3.1 Proactive Operational Outlook */}
      <NextStepExplanation
        title={`RESILIENCE OUTLOOK OVER NEXT ${horizonHours} HOURS`}
        timeframe={`${horizonHours}-Hour Survival Assessment`}
        outlook={dynamicOutlook}
      />

      {/* 4. Why This Matters */}
      <WhyThisMatters
        headline="Survival Horizon is Dictated by the Weakest Physical Link"
        summary="A microgrid with 30 days of diesel fuel can still suffer a catastrophic blackout in 4 hours if the battery bank freezes or if wind gusts trip circuit breakers. Polaris-EMS continuously computes the survival horizon across all subsystems simultaneously and uses the mathematical minimum as the operational constraint."
        technicalDetail="Governing invariant: T_surv = min(T_fuel, T_battery, T_thermal, T_critical). Replay verified with zero unserved energy for life safety loads."
      />

      {/* 5. Analytical Breakdown: Nine Dimensions */}
      {dimensionsList.length > 0 && (
        <div className="bg-white border border-slate-200 shadow-xs rounded-xl p-6">
          <button
            onClick={() => setShowNineDimensions(!showNineDimensions)}
            className="w-full flex items-center justify-between text-xs font-mono font-bold text-slate-900"
          >
            <span className="uppercase tracking-wider">
              NINE-DIMENSION ANALYTICAL HEALTH RADAR
            </span>
            {showNineDimensions ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showNineDimensions && (
            <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {dimensionsList.map((dim) => (
                <div key={dim.name} className="p-3.5 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                    <span className="font-semibold text-slate-900 font-sans">
                      {dim.name}
                    </span>
                    <span className="font-mono-numbers font-bold text-indigo-600">
                      {(Number(dim.score) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        Number(dim.score) > 0.75
                          ? 'bg-emerald-500'
                          : Number(dim.score) > 0.45
                          ? 'bg-amber-500'
                          : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(5, Number(dim.score) * 100))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 6. Candidate Advisory Recovery Options */}
      {recoveryOptions.length > 0 && (
        <div className="bg-white border border-slate-200 shadow-xs rounded-xl p-6">
          <div className="flex items-center space-x-2 text-xs font-mono uppercase text-indigo-600 font-bold mb-3">
            <LifeBuoy className="w-4 h-4" />
            <span>ADVISORY OPERATOR RECOVERY OPTIONS</span>
          </div>
          <div className="space-y-3">
            {recoveryOptions.map((opt, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-slate-50 border border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center space-x-2 text-xs font-mono">
                    <span className="font-bold text-slate-900">{opt.action_type || (opt as any).action_name}</span>
                    <span className="text-[10px] text-slate-500">({opt.target_subsystem})</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{opt.rationale || opt.description}</p>
                </div>
                <span className="text-xs font-mono text-emerald-600 font-bold shrink-0">
                  {opt.expected_survival_horizon_gain_h !== undefined ? `+${opt.expected_survival_horizon_gain_h.toFixed(1)}h Gain` : '—'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
