import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { useEvidence } from '../context/EvidenceContext';
import { api } from '../api/endpoints';
import { PolicyEvaluateResponseData, PolicyRuleTrace } from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { WhyThisMatters } from '../components/common/WhyThisMatters';
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { JargonTooltip } from '../components/common/JargonTooltip';
import { 
  Scale, 
  ShieldCheck, 
  Layers, 
  ArrowUpDown, 
  Sliders, 
  FileText,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

export const PolicyView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();
  const { inspectEvidence } = useEvidence();

  const [policyData, setPolicyData] = useState<PolicyEvaluateResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showSuppressed, setShowSuppressed] = useState<boolean>(false);
  const [expandedTier, setExpandedTier] = useState<string | null>(null);

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

  // Canonical 8-tier Priority Ladder definitions
  const priorityLadder = [
    { tier: 'P1', title: 'Life Safety & Habitat Life Support', desc: 'Station atmospheric pressure, breathing air, fire suppression, critical life support circuits. Absolute non-sheddable priority.', status: 'ENFORCED' },
    { tier: 'P2', title: 'Station Critical Scientific Operations', desc: 'Active primary scientific payloads, core atmospheric lidar, ice drill power, primary satellite downlink.', status: 'PROTECTED' },
    { tier: 'P3', title: 'Thermal Plant & Deep Freeze Defrost', desc: 'District heating circulation pumps, fuel line heat tracing, sub-zero pipe freeze protection.', status: 'NORMAL' },
    { tier: 'P4', title: 'Operating Reserve Margin & Spinning Reserve', desc: 'Minimum 20% spinning margin or 15-minute battery headroom under fluctuating wind/solar.', status: 'GOVERNED' },
    { tier: 'P5', title: 'Battery State-of-Charge & Thermal Bounds', desc: 'BESS protection between 20% and 90% SOC; cell temperature maintenance above -10°C.', status: 'MAINTAINED' },
    { tier: 'P6', title: 'Renewable Generation & Ramp Smoothing', desc: 'Wind turbine pitch modulation and solar MPPT curtailment during excessive generation transients.', status: 'ACTIVE' },
    { tier: 'P7', title: 'Secondary Habitat Comfort HVAC', desc: 'Living quarters ambient heating setback allowances (+18°C to +21°C buffer). Sheddable during deficit.', status: 'NOMINAL' },
    { tier: 'P8', title: 'Non-Essential & Auxiliary Monitoring', desc: 'Long-term data archiving, non-critical telemetry relays, exterior decorative lighting. First shed candidate.', status: 'SHEDDABLE' },
  ];

  return (
    <div className="p-4 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Editorial Header */}
      <div className="border-b border-[#DDD6C6] pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-[#78716C] mb-2">
            <span>07 Policy Governance</span>
            <span>•</span>
            <ProvenanceTag provenance="SIMULATED" size="xs" />
          </div>
          <h1 className="font-serif text-3xl lg:text-4xl text-[#1C1917] tracking-tight">
            Autonomous Policy Governance
          </h1>
          <p className="text-sm text-[#57534E] font-sans mt-2 max-w-2xl">
            Deterministic decision rules, priority ordering (P1 &gt; ... &gt; P8), stateful hysteresis, and four-tier optimizer handoff.
          </p>
        </div>

        <div className="flex items-center space-x-3 bg-white p-3 rounded border border-[#DDD6C6] shadow-sm">
          <span className="text-xs font-mono text-[#78716C] uppercase">Active Directive:</span>
          <StatusBadge status={policyData.policy_state} size="md" />
        </div>
      </div>

      {/* Primary Directive Callout */}
      <div className="editorial-sheet p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#B45309] font-semibold">
              Primary Operational Directive
            </span>
            <div className="font-serif text-2xl lg:text-3xl text-[#1C1917]">
              {policyData.primary_directive}
            </div>
            <p className="text-xs text-[#78716C] font-sans">
              Evaluated across {policyData.evaluated_rules_count} deterministic rules with active hysteresis anti-chatter damping.
            </p>
          </div>

          <div className="flex items-center space-x-4 p-3 bg-[#F6F3EC] rounded border border-[#DDD6C6] text-xs font-mono shrink-0">
            <div>
              <div className="text-[10px] text-[#A8A29E] uppercase">Handoff Status</div>
              <div className="text-sm font-semibold text-[#1C1917] mt-0.5">{handoff.handoff_status}</div>
            </div>
            <div className="h-8 w-px bg-[#DDD6C6]" />
            <div>
              <div className="text-[10px] text-[#A8A29E] uppercase">Recommended Mode</div>
              <div className="text-sm font-semibold text-[#B45309] mt-0.5">{handoff.recommended_mode}</div>
            </div>
          </div>
        </div>

        {/* Why This Matters */}
        <WhyThisMatters
          summary={`Policy engine enforces strict life-safety protection over economic optimization. At ${currentStation}, secondary scientific and comfort loads are sheddable whenever reserve margins tighten, preserving critical habitat heat and life-support power.`}
          technicalDetail="Governed by deterministic rule evaluation with asymmetric deadband hysteresis. If battery SOC or diesel reserve drops below safety thresholds, load-shedding orders are dispatched before the mathematical optimizer selects economic dispatch."
          invariant="Invariant: P1 Life Safety load is strictly non-sheddable across all policy regimes. Requested policy constraints are partitioned into 4 distinct enforcement tiers prior to MILP handoff."
          stage="Policy Governance Engine"
        />
      </div>

      {/* Non-Technical Explainer for Policy Rules */}
      <ExplainThis
        title="What is the Autonomous Policy Priority Ladder?"
        whatAmILookingAt="This ladder shows the 8 operational tiers (P1 to P8) of the station. P1 (human life-support and heating) sits at the top and can never be compromised. P8 (exterior lighting and non-essential telemetry) sits at the bottom and is shed first."
        whyIsItImportant="In sub-zero Antarctic emergencies, software cannot hesitate or wait for email approvals. This ruleset gives the autonomous system legal and operational authority to shed lower-tier circuits instantaneously if a generator fails."
        howIsItCalculated="Evaluated deterministically every tick using strict lexicographical ordering (P1 > P2 > ... > P8) with anti-chatter hysteresis damping."
      />

      <NextStepExplanation
        title="WHAT HAPPENS IF EMERGENCY SHEDDING TRIGGERS?"
        timeframe="Autonomous Instant Response"
        outlook="If generation falls below the critical reserve threshold, Polaris-EMS immediately sheds Tier P8 and Tier P7 circuits, keeping Tier P1 (living quarters heating and life-support) 100% energized."
      />

      {/* Priority Ladder (P1 to P8) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Scale className="w-4 h-4 text-[#B45309]" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-[#1C1917]">
              Operational Priority Hierarchy (P1 → P8)
            </h2>
          </div>
          <span className="text-xs font-mono text-[#78716C]">
            Deterministic Priority Cascade
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {priorityLadder.map((tier) => (
            <div 
              key={tier.tier}
              className="p-4 bg-white rounded border border-[#DDD6C6] hover:border-[#B45309]/50 transition-colors shadow-sm flex items-start space-x-3"
            >
              <span className="px-2 py-0.5 rounded bg-[#F6F3EC] text-[#B45309] font-mono text-xs font-bold border border-[#DDD6C6] shrink-0">
                {tier.tier}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-xs font-bold text-[#1C1917] truncate">{tier.title}</h3>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#F6F3EC] text-[#57534E]">
                    {tier.status}
                  </span>
                </div>
                <p className="text-[11px] text-[#78716C] font-sans mt-1 leading-relaxed">
                  {tier.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Four-Tier Optimizer Handoff Contract Table */}
      <div className="editorial-sheet p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ArrowUpDown className="w-4 h-4 text-[#B45309]" />
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-[#1C1917]">
              Four-Tier Optimizer Handoff Contract
            </h3>
          </div>
          <span className="text-xs font-mono text-[#78716C]">
            Requested Constraints ≠ Optimizer-Enforced Constraints
          </span>
        </div>

        <p className="text-xs text-[#57534E] font-sans leading-relaxed">
          {handoff.advisory_rationale}
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-[#DDD6C6] text-[#78716C] uppercase text-[10px]">
                <th className="py-2.5 px-3">Policy Constraint</th>
                <th className="py-2.5 px-3">Requested Target</th>
                <th className="py-2.5 px-3">Enforcement Tier</th>
                <th className="py-2.5 px-3 text-center">Solver Enforced?</th>
                <th className="py-2.5 px-3 text-right">Evidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#DDD6C6]">
              {Object.entries(handoff.requested_constraints || {}).map(([key, val]) => {
                const tier = tiers[key] || 'DECLARATIVE_ONLY';
                const isEnforced = key in (handoff.optimizer_enforced_constraints || {});
                return (
                  <tr key={key} className="hover:bg-[#F6F3EC]/80 transition-colors">
                    <td className="py-2.5 px-3 text-[#1C1917] font-semibold">{key}</td>
                    <td className="py-2.5 px-3 text-[#B45309] font-mono-numbers">{String(val)}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        tier === 'DIRECTLY_SUPPORTED' 
                          ? 'bg-[#EBF7F0] text-[#166534] border border-[#BBF7D0]'
                          : tier === 'DERIVED_FROM_SUPPORTED_INPUT'
                          ? 'bg-[#E0F2FE] text-[#0369A1] border border-[#BAE6FD]'
                          : tier === 'DECLARATIVE_ONLY'
                          ? 'bg-[#F6F3EC] text-[#78716C] border border-[#DDD6C6]'
                          : 'bg-[#FEF3C7] text-[#92400E] border border-[#FDE68A]'
                      }`}>
                        {tier}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      {isEnforced ? (
                        <span className="text-[#166534] font-bold">✓ Enforced</span>
                      ) : (
                        <span className="text-[#A8A29E]">Post-Replay Monitored</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => inspectEvidence({
                          value: String(val),
                          source: 'POLICY_GOVERNANCE',
                          provenance: 'SIMULATED',
                          timestamp: new Date().toISOString(),
                          station: currentStation,
                          model: 'Deterministic Rule Engine',
                          validationState: isEnforced ? 'VALIDATED' : 'ADVISORY',
                          uncertaintyInterval: 'Exact Constraint',
                          governingInvariant: 'Priority cascade: Requested policy constraints are mapped to solver linear inequalities where physically supported.'
                        })}
                        className="text-[10px] font-mono text-[#0284C7] hover:underline"
                      >
                        Inspect →
                      </button>
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
        <div className="editorial-sheet p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-[#B45309]" />
              <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-[#1C1917]">
                Stateful Hysteresis Telemetry
              </h3>
            </div>
            <span className="text-xs font-mono text-[#78716C]">Anti-Oscillation Damping</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            {Object.entries(policyData.hysteresis.consecutive_steps || {}).map(([state, steps]) => (
              <div key={state} className="p-3 bg-white rounded border border-[#DDD6C6]">
                <span className="text-[#78716C] text-[10px] uppercase truncate block">{state}</span>
                <div className="text-lg font-bold font-mono-numbers text-[#1C1917] mt-1">
                  {steps} <span className="text-xs text-[#A8A29E] font-normal">steps stable</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fired & Evaluated Rules List */}
      <div className="editorial-sheet p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-[#B45309]" />
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-[#1C1917]">
              Active Policy Rules ({policyData.active_rules?.length || 0} Fired)
            </h3>
          </div>
          <button
            onClick={() => setShowSuppressed(!showSuppressed)}
            className="text-xs text-[#0284C7] hover:underline font-mono"
          >
            {showSuppressed ? 'Hide Suppressed Rules' : 'Show Suppressed Rules'}
          </button>
        </div>

        <div className="space-y-2.5">
          {policyData.active_rules?.map((rule) => (
            <div key={rule.rule_id} className="p-3 bg-white rounded border border-[#DDD6C6] text-xs flex items-start justify-between gap-3 shadow-sm">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#FEF3C7] text-[#92400E] border border-[#FDE68A] font-bold">
                    {rule.priority_tier}
                  </span>
                  <span className="font-bold text-[#1C1917] font-mono">{rule.rule_id}</span>
                  <span className="text-[#78716C]">• {rule.action}</span>
                </div>
                <p className="text-[#57534E] text-[11px] font-sans">{rule.rationale}</p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#EBF7F0] text-[#166534] border border-[#BBF7D0] uppercase font-bold shrink-0">
                ACTIVE
              </span>
            </div>
          ))}

          {showSuppressed && policyData.suppressed_rules?.map((rule) => (
            <div key={rule.rule_id} className="p-3 bg-[#F6F3EC]/60 rounded border border-[#DDD6C6] text-xs flex items-start justify-between gap-3 opacity-70">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#E7E5E4] text-[#78716C]">
                    {rule.priority_tier}
                  </span>
                  <span className="font-bold text-[#78716C] font-mono">{rule.rule_id}</span>
                  <span className="text-[#A8A29E]">• {rule.action}</span>
                </div>
                <p className="text-[#78716C] text-[11px] font-sans">
                  Suppressed: {rule.suppression_reason || 'Lower priority than active life-safety rule'}
                </p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#E7E5E4] text-[#78716C] uppercase shrink-0">
                SUPPRESSED
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
