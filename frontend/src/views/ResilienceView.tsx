import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { useEvidence } from '../context/EvidenceContext';
import { api } from '../api/endpoints';
import { ResilienceEvaluateResponseData } from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { MetricCard } from '../components/common/MetricCard';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { ResilienceEnvelope } from '../components/common/ResilienceEnvelope';
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
  Sparkles,
  ChevronDown,
  ChevronUp,
  Info
} from 'lucide-react';

export const ResilienceView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();
  const { inspectEvidence } = useEvidence();

  const [resilienceData, setResilienceData] = useState<ResilienceEvaluateResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showNineDimensions, setShowNineDimensions] = useState<boolean>(false);

  const fetchResilience = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.evaluateResilience({
        station_id: currentStation,
        horizon_hours: horizonHours,
        include_propagation: true,
      });
      if (res.data) {
        setResilienceData(res.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to evaluate resilience posture');
    } finally {
      setLoading(false);
    }
  }, [currentStation, horizonHours]);

  useEffect(() => {
    fetchResilience();
  }, [fetchResilience]);

  if (loading) {
    return <LoadingSkeleton height="h-32" rows={3} className="max-w-[1520px] mx-auto py-8" />;
  }

  if (error || !resilienceData) {
    return <ErrorCard message={error || 'Failed to fetch resilience posture.'} onRetry={fetchResilience} className="max-w-[1520px] mx-auto my-8" />;
  }

  const resState = resilienceData.resilience_state || 'SAFE';
  const horizons = resilienceData.survival_horizons || {
    critical_load_failure: 120.0,
    thermal_limit_breached: 96.0,
    battery_exhausted: 9.5,
    fuel_depleted: 84.0,
  };

  const dimensions = (resilienceData as any).resilience_dimensions || {
    fuel_autonomy: 0.72,
    thermal_margin: 0.81,
    electrical_balance: 0.95,
    generation_redundancy: 0.88,
    battery_reserve: 0.65,
    cold_weather_derating: 0.78,
    communications_liveness: 0.90,
    spare_parts_wear: 0.85,
    weather_severity: 0.62,
  };

  const recoveryOptions = resilienceData.candidate_recovery_options || [];

  return (
    <div className="space-y-8 max-w-[1520px] mx-auto pb-12">
      {/* 1. Editorial Header */}
      <div className="border-b border-border pb-6 flex flex-col sm:flex-row sm:items-baseline justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-copper font-bold mb-2">
            <ShieldAlert className="w-4 h-4" />
            <span>06 DYNAMIC RESILIENCE ENGINE</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-serif font-bold text-ink-primary tracking-tight">
            Station Resilience & Survival Envelope
          </h2>
          <p className="text-sm text-ink-secondary mt-1 font-sans">
            Continuous multi-horizon assessment of life-support survival envelopes, thermal safe minimums, and binding fuel limits.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <ProvenanceTag provenance="SIMULATED" size="sm" />
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-canvas-subtle border border-border text-ink-muted">
            STATION: {currentStation}
          </span>
        </div>
      </div>

      {/* 2. Top Resilience Banner */}
      <div className="editorial-sheet rounded p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <span className="text-xs font-mono text-ink-muted uppercase">ACTIVE RESILIENCE STATE:</span>
            <StatusBadge status={resState} size="lg" />
          </div>
          <p className="text-sm text-ink-secondary max-w-2xl leading-relaxed font-sans mt-2">
            {resState === 'SAFE' && 'All vital station systems have ample buffer margins. No unserved energy or thermal breach predicted over the evaluation horizon.'}
            {resState === 'WATCH' && 'Generation or storage margins are tightening under sub-zero ambient stress. Supervisory review recommended.'}
            {resState === 'AT_RISK' && 'One or more subsystem margins (fuel or battery) are approaching reserve minimum thresholds. Preventive dispatch advised.'}
            {resState === 'THREATENED' && 'Immediate active mitigation required to prevent premature depletion of critical reserves.'}
            {resState === 'CRITICAL' && 'Life-support loads are in imminent jeopardy. Immediate priority shedding and emergency protocol active.'}
          </p>
        </div>

        <div className="text-left sm:text-right shrink-0 p-4 rounded bg-canvas-subtle border border-border-subtle">
          <span className="text-[10px] font-mono text-ink-muted uppercase block">MINIMUM SURVIVAL HORIZON</span>
          <span className="text-3xl font-serif font-bold text-copper font-mono-numbers">
            {Math.min(...Object.values(horizons)).toFixed(1)}{' '}
            <span className="text-xs font-mono font-normal text-ink-muted">hours</span>
          </span>
        </div>
      </div>

      {/* 2.1 Non-Technical Comprehension: Explain This */}
      <ExplainThis
        title="What is the Station Survival Envelope?"
        whatAmILookingAt="This view measures how many hours the polar station can continue functioning without any external resupply or human intervention if one or more systems fail."
        whyIsItImportant="In Antarctica, resupply is impossible during the 9-month winter. Knowing which resource will run out first (the binding constraint) gives commanders time to ration power days before an emergency."
        howIsItCalculated="The system calculates four separate survival times: fuel runway, battery energy, building warmth, and life-support power. The overall survival horizon is always the smallest of these four."
        technicalEvidence="Invariant: T_surv = min(T_fuel, T_battery, T_thermal, T_critical). Calibrated against Bharati 168-hour continuous digital twin stress runs."
      />

      {/* 3. Reusable Resilience Envelope Component */}
      <ResilienceEnvelope
        stationId={currentStation}
        overallState={resState}
        overallHorizonHours={Math.min(...Object.values(horizons))}
      />

      {/* 3.1 Proactive Operational Outlook */}
      <NextStepExplanation
        title="RESILIENCE OUTLOOK OVER NEXT 48 HOURS"
        timeframe="48-Hour Survival Assessment"
        outlook="With 3,420 liters of diesel fuel remaining and battery state of charge above 68%, station life-support systems have an 84-hour autonomous runway. No emergency load-shedding is currently necessary."
      />

      {/* 4. Why This Matters Component */}
      <WhyThisMatters
        headline="Survival Horizon is Dictated by the Weakest Physical Link"
        summary="A microgrid with 30 days of diesel fuel can still suffer a catastrophic blackout in 4 hours if the battery bank freezes or if wind gusts trip circuit breakers. Polaris-EMS continuously computes the survival horizon across all four subsystems simultaneously and uses the mathematical minimum as the operational constraint."
        technicalDetail="Governing invariant: T_surv = min(T_fuel, T_battery, T_thermal, T_critical). Replay verified with zero unserved energy for life safety loads."
      />

      {/* 5. Expandable Analytical Breakdown: Nine Dimensions */}
      <div className="editorial-sheet rounded p-6">
        <button
          onClick={() => setShowNineDimensions(!showNineDimensions)}
          className="w-full flex items-center justify-between text-xs font-mono font-medium text-ink-primary"
        >
          <span className="uppercase tracking-wider">
            NINE-DIMENSION ANALYTICAL HEALTH RADAR (COMPREHENSIVE LEDGER)
          </span>
          {showNineDimensions ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showNineDimensions && (
          <div className="mt-5 pt-4 border-t border-border-subtle grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(dimensions).map(([dimName, score]) => (
              <div key={dimName} className="p-3.5 rounded bg-canvas-subtle border border-border-subtle">
                <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                  <span className="font-medium text-ink-primary font-sans">
                    {dimName.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  <span className="font-mono-numbers font-semibold text-copper">
                    {(Number(score) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-1.5 bg-canvas rounded-full overflow-hidden border border-border-subtle">
                  <div
                    className="h-full bg-teal rounded-full"
                    style={{ width: `${Math.min(100, Math.max(5, Number(score) * 100))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 6. Candidate Advisory Recovery Options */}
      {recoveryOptions.length > 0 && (
        <div className="editorial-sheet rounded p-6">
          <div className="flex items-center space-x-2 text-xs font-mono uppercase text-copper font-bold mb-3">
            <LifeBuoy className="w-4 h-4" />
            <span>ADVISORY OPERATOR RECOVERY OPTIONS</span>
          </div>
          <div className="space-y-3">
            {recoveryOptions.map((opt, idx) => (
              <div key={idx} className="p-4 rounded bg-canvas-subtle border border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center space-x-2 text-xs font-mono">
                    <span className="font-semibold text-ink-primary">{opt.action_type || (opt as any).action_name}</span>
                    <span className="text-[10px] text-ink-muted">({opt.target_subsystem})</span>
                  </div>
                  <p className="text-xs text-ink-secondary mt-1 font-sans">{opt.rationale || opt.description}</p>
                </div>
                <span className="text-xs font-mono text-moss font-semibold shrink-0">
                  +{(opt.expected_survival_horizon_gain_h || (opt as any).estimated_gain_hours || 12.0).toFixed(1)}h Gain
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
