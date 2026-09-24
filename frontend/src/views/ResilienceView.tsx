import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { api } from '../api/endpoints';
import { ResilienceEvaluateResponseData } from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { MetricCard } from '../components/common/MetricCard';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Clock, 
  Activity, 
  AlertTriangle, 
  CheckCircle2, 
  LifeBuoy, 
  Sparkles 
} from 'lucide-react';

export const ResilienceView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();

  const [resilienceData, setResilienceData] = useState<ResilienceEvaluateResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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
    return (
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        <LoadingSkeleton height="h-44" rows={2} />
      </div>
    );
  }

  if (error || !resilienceData) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <ErrorCard title="Resilience Engine Error" message={error || 'Data unavailable'} onRetry={fetchResilience} />
      </div>
    );
  }

  const surv = resilienceData.survival_horizons;
  const dims = resilienceData.dimensions;

  // 9 Observable dimensions list
  const dimensionItems = dims ? [
    { name: 'Energy Adequacy', score: dims.energy_adequacy, desc: 'Overall generation availability to meet electrical demand' },
    { name: 'Critical Load Resilience', score: dims.critical_load_resilience, desc: 'Continuity of Tier 1 life-safety circuits without deficit' },
    { name: 'Thermal Habitability', score: dims.thermal_resilience, desc: 'Indoor temperature preservation above safe minimum threshold' },
    { name: 'Generation Headroom', score: dims.generation_resilience, desc: 'Dependable operational reserve margin & dispatch headroom' },
    { name: 'Storage Health', score: dims.storage_resilience, desc: 'BESS usable state of charge buffer and cold-derate margins' },
    { name: 'Fuel Endurance', score: dims.fuel_resilience, desc: 'Remaining diesel inventory relative to critical emergency reserve' },
    { name: 'Logistics Buffer', score: dims.logistics_resilience, desc: 'Survivability relative to scheduled seasonal resupply gap' },
    { name: 'Renewable Utilization', score: dims.renewable_resilience, desc: 'Clean energy penetration and weather shortfall buffering' },
    { name: 'Recovery Capacity', score: dims.recovery_resilience, desc: 'Observable restorative capacity to transition from threat to safe' },
  ] : [];

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-xl bg-polar-900/60 border border-polar-800">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold font-mono text-polar-100 uppercase tracking-wide">
              Station Resilience Engine (Phase 7)
            </h2>
            <ProvenanceTag provenance="SIMULATED" size="xs" />
          </div>
          <p className="text-xs text-polar-400 mt-1">
            Nine transparent engineering dimensions, multi-horizon survival boundaries, and advisory mitigation options.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-xs font-mono text-polar-400">Station State:</span>
          <StatusBadge status={resilienceData.resilience_state} size="md" />
        </div>
      </div>

      {/* Survival Horizons Card Grid */}
      <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
              Subsystem Survival Horizons (Hours)
            </h3>
          </div>
          <span className="text-xs font-mono text-cyan-300">
            Binding Constraint: <strong className="uppercase">{surv.binding_subsystem}</strong>
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono text-xs">
          <div className="p-3 rounded-lg bg-polar-950/80 border border-polar-800">
            <span className="text-[10px] text-polar-400 uppercase">Station Overall</span>
            <div className="text-xl font-bold font-mono-numbers text-cyan-400 mt-1">
              {surv.overall_station_survival_horizon_h.toFixed(1)}h
            </div>
            <span className="text-[10px] text-polar-500">Binding limit</span>
          </div>

          <div className="p-3 rounded-lg bg-polar-950/80 border border-polar-800">
            <span className="text-[10px] text-polar-400 uppercase">Critical Load</span>
            <div className="text-xl font-bold font-mono-numbers text-polar-100 mt-1">
              {surv.critical_load_survival_horizon_h.toFixed(1)}h
            </div>
            <span className="text-[10px] text-polar-500">Tier 1 loads</span>
          </div>

          <div className="p-3 rounded-lg bg-polar-950/80 border border-polar-800">
            <span className="text-[10px] text-polar-400 uppercase">Thermal Safe</span>
            <div className="text-xl font-bold font-mono-numbers text-polar-100 mt-1">
              {surv.thermal_habitability_horizon_h.toFixed(1)}h
            </div>
            <span className="text-[10px] text-polar-500">Envelope habitability</span>
          </div>

          <div className="p-3 rounded-lg bg-polar-950/80 border border-polar-800">
            <span className="text-[10px] text-polar-400 uppercase">BESS Battery</span>
            <div className="text-xl font-bold font-mono-numbers text-polar-100 mt-1">
              {surv.battery_endurance_horizon_h.toFixed(1)}h
            </div>
            <span className="text-[10px] text-polar-500">Electrochemical buffer</span>
          </div>

          <div className="p-3 rounded-lg bg-polar-950/80 border border-polar-800">
            <span className="text-[10px] text-polar-400 uppercase">Fuel Inventory</span>
            <div className="text-xl font-bold font-mono-numbers text-polar-100 mt-1">
              {surv.fuel_endurance_horizon_h.toFixed(1)}h
            </div>
            <span className="text-[10px] text-polar-500">To critical waterline</span>
          </div>

          <div className="p-3 rounded-lg bg-polar-950/80 border border-polar-800">
            <span className="text-[10px] text-polar-400 uppercase">Resupply Gap</span>
            <div className="text-xl font-bold font-mono-numbers text-polar-100 mt-1">
              {surv.resupply_gap_survivability_h.toFixed(1)}h
            </div>
            <span className="text-[10px] text-polar-500">Seasonal buffer</span>
          </div>
        </div>
      </div>

      {/* 9 Dimensions Breakdown */}
      {dims && (
        <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
                Nine Transparent Resilience Dimensions (0–100 Scores)
              </h3>
            </div>
            <div className="flex items-center space-x-2 text-xs font-mono">
              <span className="text-polar-400">Composite Index:</span>
              <span className="text-cyan-400 font-bold text-base font-mono-numbers">
                {dims.composite_resilience_index.toFixed(1)}
              </span>
              <span className="text-polar-500">/ 100</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dimensionItems.map((dim, idx) => (
              <div key={idx} className="p-3.5 rounded-lg bg-polar-950/80 border border-polar-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold font-mono text-polar-200">{dim.name}</span>
                  <span className={`text-xs font-bold font-mono-numbers ${
                    dim.score >= 75 ? 'text-emerald-400' : dim.score >= 50 ? 'text-amber-400' : 'text-red-400'
                  }`}>
                    {dim.score.toFixed(1)}
                  </span>
                </div>

                {/* Score Progress Bar */}
                <div className="h-1.5 w-full bg-polar-800 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-500 ${
                      dim.score >= 75 ? 'bg-emerald-400' : dim.score >= 50 ? 'bg-amber-400' : 'bg-red-400'
                    }`}
                    style={{ width: `${Math.min(Math.max(dim.score, 0), 100)}%` }}
                  />
                </div>

                <p className="text-[10px] text-polar-400 leading-relaxed font-sans">{dim.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Advisory Recovery Options (Strict Backend Ordering — No Frontend Re-ranking) */}
      <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <LifeBuoy className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
              Candidate Advisory Recovery Pathways ({resilienceData.candidate_recovery_options?.length || 0})
            </h3>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-polar-950 text-cyan-400 border border-cyan-800">
            Advisory Only • Zero Automatic Execution
          </span>
        </div>

        <div className="space-y-2.5">
          {(!resilienceData.candidate_recovery_options || resilienceData.candidate_recovery_options.length === 0) ? (
            <p className="text-xs text-polar-400 font-mono p-3 bg-polar-950 rounded">
              No advisory recovery actions required; all operational margins satisfy safety parameters.
            </p>
          ) : (
            resilienceData.candidate_recovery_options.map((opt, idx) => (
              <div 
                key={idx} 
                className="p-3.5 rounded-lg bg-polar-950/70 border border-polar-800 text-xs flex flex-col md:flex-row md:items-center md:justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-polar-100 font-mono uppercase text-xs">
                      #{idx + 1}: {opt.action_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-polar-900 border border-polar-750 text-polar-400">
                      {opt.target_subsystem}
                    </span>
                    <StatusBadge status={opt.urgency} size="sm" showIcon={false} />
                  </div>
                  <p className="text-polar-300 text-[11px] leading-relaxed font-sans">
                    {opt.description}
                  </p>
                </div>

                <div className="flex items-center space-x-4 shrink-0 font-mono text-xs">
                  <div className="text-right">
                    <span className="text-[10px] text-polar-500 block">Expected Gain</span>
                    <span className="text-emerald-400 font-bold">+{opt.expected_survival_horizon_gain_h.toFixed(1)}h</span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-polar-500 block">Reserve Gain</span>
                    <span className="text-cyan-400 font-bold">+{opt.expected_reserve_margin_gain_pct.toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
