import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { api } from '../api/endpoints';
import { PolicyEvaluateResponseData, PolicyRuleTrace } from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { 
  Scale, 
  ShieldCheck, 
  Layers, 
  ArrowUpDown, 
  AlertCircle, 
  CheckCircle2, 
  Sliders 
} from 'lucide-react';

export const PolicyView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();

  const [policyData, setPolicyData] = useState<PolicyEvaluateResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showSuppressed, setShowSuppressed] = useState<boolean>(true);

  const fetchPolicy = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.evaluatePolicy({
        station_id: currentStation,
        horizon_hours: horizonHours,
        include_suppressed: true,
        include_evaluation_trace: true,
      });
      if (res.data) {
        setPolicyData(res.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to evaluate policy governance');
    } finally {
      setLoading(false);
    }
  }, [currentStation, horizonHours]);

  useEffect(() => {
    fetchPolicy();
  }, [fetchPolicy]);

  if (loading) {
    return (
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        <LoadingSkeleton height="h-36" rows={2} />
      </div>
    );
  }

  if (error || !policyData) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <ErrorCard title="Policy Engine Error" message={error || 'Policy governance telemetry unavailable'} onRetry={fetchPolicy} />
      </div>
    );
  }

  const handoff = policyData.optimizer_handoff;
  const tiers = handoff.enforcement_tiers || {};

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-xl bg-polar-900/60 border border-polar-800">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold font-mono text-polar-100 uppercase tracking-wide">
              Policy Governance Engine (Phase 8)
            </h2>
            <ProvenanceTag provenance="SIMULATED" size="xs" />
          </div>
          <p className="text-xs text-polar-400 mt-1">
            Deterministic decision rules, priority ordering (P1 &gt; ... &gt; P8), stateful hysteresis, and optimizer handoff.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-xs font-mono text-polar-400">Directive:</span>
          <StatusBadge status={policyData.policy_state} size="md" />
        </div>
      </div>

      {/* Active Directive & Priority Hero Banner */}
      <div className="p-5 rounded-xl bg-polar-900/80 border border-polar-750 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-1">
          <span className="text-[10px] font-mono text-polar-400 uppercase tracking-wider">
            Primary Operational Directive
          </span>
          <div className="text-xl font-bold font-mono text-cyan-300">
            {policyData.primary_directive}
          </div>
          <p className="text-xs text-polar-300 font-sans">
            Evaluated across {policyData.evaluated_rules_count} deterministic governance rules with active hysteresis damping.
          </p>
        </div>

        <div className="flex items-center space-x-3 font-mono text-xs bg-polar-950/80 p-3 rounded-lg border border-polar-800 shrink-0">
          <div>
            <div className="text-[10px] text-polar-500 uppercase">Handoff Status</div>
            <div className="text-sm font-bold text-polar-100 mt-0.5">{handoff.handoff_status}</div>
          </div>
          <div className="h-8 w-px bg-polar-800" />
          <div>
            <div className="text-[10px] text-polar-500 uppercase">Recommended Mode</div>
            <div className="text-sm font-bold text-cyan-400 mt-0.5">{handoff.recommended_mode}</div>
          </div>
        </div>
      </div>

      {/* Four-Tier Optimizer Handoff Contract Table */}
      <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ArrowUpDown className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
              Four-Tier Optimizer Handoff Contract
            </h3>
          </div>
          <span className="text-[10px] font-mono text-polar-400">
            Requested Constraints ≠ Optimizer-Enforced Constraints
          </span>
        </div>

        <p className="text-xs text-polar-300 font-sans leading-relaxed">
          {handoff.advisory_rationale}
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-polar-800 text-polar-400 uppercase text-[10px]">
                <th className="py-2 px-3">Policy Constraint</th>
                <th className="py-2 px-3">Requested Target</th>
                <th className="py-2 px-3">Enforcement Tier</th>
                <th className="py-2 px-3 text-center">Solver Enforced?</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-polar-850/60">
              {Object.entries(handoff.requested_constraints || {}).map(([key, val]) => {
                const tier = tiers[key] || 'DECLARATIVE_ONLY';
                const isEnforced = key in (handoff.optimizer_enforced_constraints || {});
                return (
                  <tr key={key} className="hover:bg-polar-800/40">
                    <td className="py-2 px-3 text-polar-100 font-semibold">{key}</td>
                    <td className="py-2 px-3 text-cyan-300 font-mono-numbers">{String(val)}</td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        tier === 'DIRECTLY_SUPPORTED' 
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/30'
                          : tier === 'DERIVED_FROM_SUPPORTED_INPUT'
                          ? 'bg-blue-950 text-blue-300 border border-blue-500/30'
                          : tier === 'DECLARATIVE_ONLY'
                          ? 'bg-polar-800 text-polar-300 border border-polar-700'
                          : 'bg-amber-950 text-amber-300 border border-amber-500/30'
                      }`}>
                        {tier}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-center">
                      {isEnforced ? (
                        <span className="text-emerald-400 font-bold">✓ Enforced</span>
                      ) : (
                        <span className="text-polar-500">Post-Replay Monitored</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stateful Hysteresis Deadband Inspector */}
      {policyData.hysteresis && (
        <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
                Stateful Hysteresis Telemetry
              </h3>
            </div>
            <span className="text-xs font-mono text-polar-400">Anti-Oscillation Damping</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            {Object.entries(policyData.hysteresis.consecutive_steps || {}).map(([state, steps]) => (
              <div key={state} className="p-3 rounded-lg bg-polar-950 border border-polar-800">
                <span className="text-polar-400 text-[10px] uppercase truncate block">{state}</span>
                <div className="text-lg font-bold font-mono-numbers text-polar-100 mt-1">
                  {steps} <span className="text-xs text-polar-500 font-normal">steps stable</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fired & Evaluated Rules List */}
      <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
              Active Policy Rules ({policyData.active_rules?.length || 0} Fired)
            </h3>
          </div>
          <button
            onClick={() => setShowSuppressed(!showSuppressed)}
            className="text-xs text-cyan-400 hover:underline font-mono"
          >
            {showSuppressed ? 'Hide Suppressed Rules' : 'Show Suppressed Rules'}
          </button>
        </div>

        <div className="space-y-2">
          {policyData.active_rules?.map((rule) => (
            <div key={rule.rule_id} className="p-3 rounded-lg bg-polar-950/80 border border-polar-800 text-xs flex items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                    {rule.priority_tier}
                  </span>
                  <span className="font-bold text-polar-100 font-mono">{rule.rule_id}</span>
                  <span className="text-polar-400">• {rule.action}</span>
                </div>
                <p className="text-polar-300 text-[11px] font-sans">{rule.rationale}</p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-500/30 uppercase shrink-0">
                ACTIVE
              </span>
            </div>
          ))}

          {showSuppressed && policyData.suppressed_rules?.map((rule) => (
            <div key={rule.rule_id} className="p-3 rounded-lg bg-polar-950/40 border border-polar-850/80 text-xs flex items-start justify-between gap-3 opacity-60">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-polar-900 text-polar-500">
                    {rule.priority_tier}
                  </span>
                  <span className="font-bold text-polar-400 font-mono">{rule.rule_id}</span>
                  <span className="text-polar-500">• {rule.action}</span>
                </div>
                <p className="text-polar-400 text-[11px] font-sans">
                  Suppressed: {rule.suppression_reason || 'Lower priority than active life-safety rule'}
                </p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-polar-900 text-polar-500 uppercase shrink-0">
                SUPPRESSED
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
