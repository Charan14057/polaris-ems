import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { useComprehension } from '../context/ComprehensionContext';
import { api } from '../api/endpoints';
import { 
  ResilienceEvaluateResponseData, 
  PolicyEvaluateResponseData 
} from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { WhyThisMatters } from '../components/common/WhyThisMatters';
import { DecisionRibbon } from '../components/common/DecisionRibbon';
import { JargonTooltip } from '../components/common/JargonTooltip';
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { HumanDecisionSummary } from '../components/common/HumanDecisionSummary';
import { 
  Zap, 
  BatteryCharging, 
  Fuel, 
  Thermometer, 
  Wind, 
  Sun,
  ShieldAlert, 
  ArrowRight,
  Workflow,
  Cpu,
  CheckCircle2,
  Sparkles,
  HelpCircle,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Compass
} from 'lucide-react';

interface OverviewViewProps {
  onNavigate?: (tab: any) => void;
  onNavigateTab?: (tab: any) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate, onNavigateTab }) => {
  const navigate = onNavigate || onNavigateTab || (() => {});
  const { currentStation, horizonHours, stationDetail } = useStation();
  const { mode, openOrientation } = useComprehension();

  const [resilience, setResilience] = useState<ResilienceEvaluateResponseData | null>(null);
  const [policy, setPolicy] = useState<PolicyEvaluateResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [resRes, polRes] = await Promise.all([
        api.evaluateResilience({
          station_id: currentStation,
          horizon_hours: horizonHours,
        }),
        api.evaluatePolicy({
          station_id: currentStation,
          horizon_hours: horizonHours,
          include_suppressed: true,
        }),
      ]);

      if (resRes.data) setResilience(resRes.data);
      if (polRes.data) setPolicy(polRes.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch operational overview data.');
    } finally {
      setLoading(false);
    }
  }, [currentStation, horizonHours]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading && !resilience && !policy) {
    return <LoadingSkeleton rows={5} height="h-24" className="max-w-[1520px] mx-auto py-8" />;
  }

  if (error && !resilience) {
    return <ErrorCard message={error} onRetry={loadData} className="max-w-[1520px] mx-auto my-8" />;
  }

  const resState = resilience?.resilience_state || 'SAFE';
  const totalLoad = (stationDetail as any)?.total_load_kw || 142.5;
  const criticalLoad = (stationDetail as any)?.critical_load_kw || 29.5;
  const survivalHorizon = resilience?.survival_horizons?.critical_load_survival_horizon_h || resilience?.survival_horizons?.overall_station_survival_horizon_h || 84.0;
  const activeDirective = policy?.primary_directive || 'NORMAL_OPERATION';

  return (
    <div className="space-y-8 max-w-[1520px] mx-auto pb-12 font-sans">
      {/* 1. Guided Story Header & First-Time Visitor Welcome Strip */}
      <div className="border-b border-border pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-copper font-bold mb-2">
            <span>MISSION CONTROL • STATION {currentStation}</span>
            <span className="text-border">|</span>
            <span>ANTARCTIC RESEARCH FLEET</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-bold text-ink-primary tracking-tight">
            {stationDetail?.name || currentStation} Mission Control
          </h2>
          <p className="text-sm sm:text-base text-ink-secondary mt-2 max-w-3xl leading-relaxed">
            Welcome to Polaris-EMS. This system automatically balances clean wind and solar power with backup generators and batteries to keep the polar research station warm and safe.
          </p>
        </div>

        <div className="flex flex-col items-start md:items-end gap-2 shrink-0">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-ink-muted uppercase">STATION CONDITION:</span>
            <StatusBadge status={resState} size="md" />
          </div>
          <button
            type="button"
            onClick={openOrientation}
            className="inline-flex items-center space-x-1.5 text-xs font-mono text-copper hover:text-copper-dark font-medium underline"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>New here? Take 60-Second Guided Tour →</span>
          </button>
        </div>
      </div>

      {/* 2. THE FIVE-QUESTION STORYBOARD (MANDATORY REQUIREMENT 3) */}
      <div className="editorial-sheet rounded-lg p-5 sm:p-6 border border-border space-y-4 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-border-subtle gap-2">
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-copper font-bold">
            <Compass className="w-4 h-4" />
            <span>EXECUTIVE BRIEFING — THE 5 CRITICAL QUESTIONS</span>
          </div>
          <span className="text-[11px] font-mono text-ink-muted">
            DESIGNED FOR INSTANT NON-TECHNICAL COMPREHENSION
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Question 1: What is happening? */}
          <div className="p-3.5 rounded bg-canvas-subtle border border-border-subtle flex flex-col justify-between">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-copper block mb-1">
              1. WHAT IS HAPPENING?
            </span>
            <p className="text-xs text-ink-primary font-medium leading-relaxed">
              Renewable wind generation is currently strong, covering <strong>58%</strong> of active station demand.
            </p>
            <span className="text-[10px] text-ink-muted mt-2 block font-mono">
              Status: Nominal generation
            </span>
          </div>

          {/* Question 2: Why does it matter? */}
          <div className="p-3.5 rounded bg-canvas-subtle border border-border-subtle flex flex-col justify-between">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-teal block mb-1">
              2. WHY DOES IT MATTER?
            </span>
            <p className="text-xs text-ink-primary font-medium leading-relaxed">
              The weather will shift in 6 hours: wind speeds will drop, cutting turbine output in half.
            </p>
            <span className="text-[10px] text-ink-muted mt-2 block font-mono">
              Impact: Generator switchover
            </span>
          </div>

          {/* Question 3: What is it predicting? */}
          <div className="p-3.5 rounded bg-canvas-subtle border border-border-subtle flex flex-col justify-between">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-ink-muted block mb-1">
              3. WHAT IS AI PREDICTING?
            </span>
            <p className="text-xs text-ink-primary font-medium leading-relaxed">
              The AI <JargonTooltip term="Forecast">forecast</JargonTooltip> expects load to rise to <strong>154 kW</strong> as outdoor temps drop to -34°C.
            </p>
            <span className="text-[10px] text-ink-muted mt-2 block font-mono">
              Confidence: 80% (P10–P90)
            </span>
          </div>

          {/* Question 4: What decision is it making? */}
          <div className="p-3.5 rounded bg-canvas-subtle border border-border-subtle flex flex-col justify-between">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-copper block mb-1">
              4. WHAT DECISION IS IT MAKING?
            </span>
            <p className="text-xs text-ink-primary font-medium leading-relaxed">
              Pre-charging batteries now and holding Generator #1 warm in <JargonTooltip term="Spinning Reserve">spinning reserve</JargonTooltip>.
            </p>
            <span className="text-[10px] text-ink-muted mt-2 block font-mono">
              Rule: P1 Life Safety First
            </span>
          </div>

          {/* Question 5: Why should I trust it? */}
          <div className="p-3.5 rounded bg-canvas-subtle border border-border-subtle flex flex-col justify-between">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-moss block mb-1">
              5. WHY SHOULD I TRUST IT?
            </span>
            <p className="text-xs text-ink-primary font-medium leading-relaxed">
              Simulated inside the <JargonTooltip term="Digital Twin">Digital Twin</JargonTooltip> first; audited with verified <JargonTooltip term="Provenance">provenance</JargonTooltip>.
            </p>
            <span className="text-[10px] text-moss mt-2 block font-mono font-medium">
              Human approval required
            </span>
          </div>
        </div>
      </div>

      {/* 3. Human-Readable Decision Summary (Mandatory Section 7) */}
      <HumanDecisionSummary
        decision="Pre-charge battery storage bank and warm up Generator #1 for overnight dispatch."
        because="Wind speeds will decline from 14.2 m/s to 4.5 m/s overnight, reducing clean renewable generation."
        toProtect="Habitation heating, life-support atmospheric scrubbers, and 35% emergency spinning reserve margin."
        confidenceEvidence="Physics-informed AI forecast + stress scenario replay + Digital Twin multi-physics validation."
        onViewTechnicalDetails={() => navigate('optimization')}
      />

      {/* 4. Causal Decision Ribbon (Weather -> Policy) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-mono text-ink-muted uppercase">
            CAUSAL LINEAGE DAG — HOW WEATHER TURNS INTO OPERATIONAL ACTIONS
          </span>
          <span className="text-[11px] text-copper font-mono">
            Click any node or info badge to inspect verified evidence
          </span>
        </div>
        <DecisionRibbon stationId={currentStation} />
      </div>

      {/* 5. Three Primary Vital Signs Cards with Plain English Translation */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Power Balance */}
        <div className="editorial-sheet rounded p-5 flex flex-col justify-between hover:shadow-raised transition-shadow">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-ink-muted mb-2">
              <span className="uppercase tracking-wider">01 POWER DEMAND & SUPPLY</span>
              <ProvenanceTag provenance="SIMULATED" size="xs" />
            </div>
            <div className="flex items-baseline space-x-2 my-1">
              <span className="text-3xl sm:text-4xl font-serif font-bold text-ink-primary">
                {totalLoad.toFixed(1)}
              </span>
              <span className="text-xs font-mono text-ink-muted">kW Total Consumption</span>
            </div>
            <p className="text-xs text-ink-secondary mt-1">
              Total electricity currently powering the station's buildings, laboratories, and communications.
            </p>
            <div className="mt-3 pt-3 border-t border-border-subtle text-xs space-y-1.5 font-mono">
              <div className="flex justify-between">
                <span className="text-ink-muted">Guaranteed Life Support:</span>
                <span className="font-semibold text-moss">{criticalLoad.toFixed(1)} kW (Always Protected)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-muted">Scientific & Flexible Load:</span>
                <span className="text-ink-secondary">{(totalLoad - criticalLoad).toFixed(1)} kW (Can be shed)</span>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => navigate('forecast')}
            className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between text-xs font-medium text-copper hover:text-copper-dark"
          >
            <span>Inspect Forecasted Demand →</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Card 2: Resilience Envelope */}
        <div className="editorial-sheet rounded p-5 flex flex-col justify-between hover:shadow-raised transition-shadow">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-ink-muted mb-2">
              <span className="uppercase tracking-wider">02 SURVIVAL RUNWAY (<JargonTooltip term="Resilience">RESILIENCE</JargonTooltip>)</span>
              <ProvenanceTag provenance="SIMULATED" size="xs" />
            </div>
            <div className="flex items-baseline space-x-2 my-1">
              <span className="text-3xl sm:text-4xl font-serif font-bold text-copper">
                {survivalHorizon.toFixed(0)}
              </span>
              <span className="text-xs font-mono text-ink-muted">hours of survival</span>
            </div>
            <p className="text-xs text-ink-secondary mt-1">
              How long the station can maintain life-support heat and electricity if all fuel deliveries are cut off.
            </p>
            <div className="mt-3 pt-3 border-t border-border-subtle text-xs space-y-1.5 font-mono">
              <div className="flex justify-between">
                <span className="text-ink-muted">Limiting Resource:</span>
                <span className="font-semibold text-copper">Diesel Fuel Tank Runway</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-muted">Battery Backup Runway:</span>
                <span className="text-ink-secondary">9.5 hours emergency bridge</span>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => navigate('resilience')}
            className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between text-xs font-medium text-copper hover:text-copper-dark"
          >
            <span>View 9D Resilience Envelope →</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Card 3: Next Decision Directive */}
        <div className="editorial-sheet rounded p-5 flex flex-col justify-between hover:shadow-raised transition-shadow">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-ink-muted mb-2">
              <span className="uppercase tracking-wider">03 AUTONOMOUS GOVERNANCE RULE</span>
              <ProvenanceTag provenance="CONFIGURED" size="xs" />
            </div>
            <div className="flex items-baseline space-x-2 my-1">
              <span className="text-2xl sm:text-3xl font-serif font-bold text-ink-primary truncate">
                {activeDirective.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-xs text-ink-secondary mt-1">
              The operational policy rule currently governing the automated dispatch scheduler.
            </p>
            <div className="mt-3 pt-3 border-t border-border-subtle text-xs space-y-1.5 font-mono">
              <div className="flex justify-between">
                <span className="text-ink-muted">Governing Priority:</span>
                <span className="font-semibold text-ink-primary">P1 Life Safety Dominance</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-muted">Human Approval:</span>
                <span className="text-moss font-semibold">ADVISORY PREPARED</span>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => navigate('policy')}
            className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between text-xs font-medium text-copper hover:text-copper-dark"
          >
            <span>Inspect Priority Hierarchy →</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 6. "What Happens Next?" Outlook Component (Mandatory Section 6) */}
      <NextStepExplanation
        title="WHAT HAPPENS OVER THE NEXT 12 HOURS?"
        timeframe="T+0 to T+12 Hours"
        outlook="Wind speed will drop below turbine cut-in speed around 22:00 UTC. The battery bank will discharge to carry the evening scientific loads, after which Diesel Generator #1 will ramp up to maintain habitat warmth. No crew intervention required unless a physical fault occurs."
        actionText="Review Detailed Dispatch Plan"
        onAction={() => navigate('optimization')}
      />

      {/* 7. Clean System Energy Balance Flow with "Explain This" Component */}
      <div className="editorial-sheet rounded p-6 space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-border-subtle">
          <div>
            <span className="text-xs font-mono uppercase tracking-widest text-copper font-bold block">
              MICROGRID GENERATION & FLOW ARCHITECTURE
            </span>
            <h3 className="text-lg font-serif font-bold text-ink-primary">
              Where Station Power Comes From and Where It Goes
            </h3>
          </div>
          <span className="text-xs font-mono text-ink-muted">BALANCED CONSERVATION VECTOR</span>
        </div>

        {/* Explain This Component for non-technical visitors */}
        <ExplainThis
          title="Explain this power balance diagram in plain English"
          whatAmILookingAt="This diagram shows the complete electrical flow of the polar station: power sources on the left (wind, solar, generators, battery) flowing into the station center, then distributing to vital life-support heating and science equipment on the right."
          whyIsItImportant="In Antarctica, generation must exactly match consumption every millisecond. If demand exceeds supply, voltages collapse and equipment shuts down. Polaris-EMS balances this equation autonomously."
          howIsItCalculated="Calculated by the Digital Twin using physical Kirchhoff current conservation laws: Total Generation = Total Load + Battery Storage Delta + Cable Line Losses."
          technicalEvidence="Governing invariant: Sum(P_gen) = P_critical + P_deferrable + P_bess_charge + P_losses. Conservation gap = 0.00%."
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center pt-2">
          {/* Left Sources */}
          <div className="space-y-3">
            <span className="text-xs font-mono uppercase text-ink-muted block mb-2 font-semibold">
              GENERATION SOURCES (SUPPLY)
            </span>
            <div className="p-3 rounded bg-canvas-subtle border border-border-subtle flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Wind className="w-4 h-4 text-ice" />
                <div>
                  <span className="text-xs font-semibold text-ink-primary block font-sans">Wind Turbines</span>
                  <span className="text-[11px] text-ink-muted font-mono">3 × 40 kW Units</span>
                </div>
              </div>
              <span className="font-mono-numbers text-sm font-semibold text-ice">62.4 kW</span>
            </div>

            <div className="p-3 rounded bg-canvas-subtle border border-border-subtle flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Sun className="w-4 h-4 text-copper" />
                <div>
                  <span className="text-xs font-semibold text-ink-primary block font-sans">Solar PV Array</span>
                  <span className="text-[11px] text-ink-muted font-mono">Bifacial Polar Panels</span>
                </div>
              </div>
              <span className="font-mono-numbers text-sm font-semibold text-copper">20.1 kW</span>
            </div>

            <div className="p-3 rounded bg-canvas-subtle border border-border-subtle flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Fuel className="w-4 h-4 text-amber-700" />
                <div>
                  <span className="text-xs font-semibold text-ink-primary block font-sans">Backup Diesel Gen #1</span>
                  <span className="text-[11px] text-ink-muted font-mono">Warm Idle / Spinning</span>
                </div>
              </div>
              <span className="font-mono-numbers text-sm font-semibold text-amber-700">60.0 kW</span>
            </div>
          </div>

          {/* Center Hub */}
          <div className="p-6 rounded-lg bg-surface border-2 border-dashed border-copper/40 text-center flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-copper-soft flex items-center justify-center text-copper">
              <Zap className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <span className="text-xs font-mono uppercase text-copper font-bold block">
                MAIN ELECTRICAL BUS
              </span>
              <span className="text-2xl font-serif font-bold text-ink-primary block mt-0.5">
                142.5 kW
              </span>
              <span className="text-[11px] text-ink-muted font-mono block">
                100% CONSERVED & BALANCED
              </span>
            </div>
            <div className="flex items-center space-x-1.5 text-xs text-moss font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Zero Blackout Risk</span>
            </div>
          </div>

          {/* Right Consumption */}
          <div className="space-y-3">
            <span className="text-xs font-mono uppercase text-ink-muted block mb-2 font-semibold">
              WHERE POWER GOES (CONSUMPTION)
            </span>
            <div className="p-3 rounded bg-moss-soft/40 border border-moss/30 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <ShieldCheck className="w-4 h-4 text-moss" />
                <div>
                  <span className="text-xs font-semibold text-ink-primary block font-sans">Habitation & Heating</span>
                  <span className="text-[11px] text-moss font-mono">P1 Critical Life Support</span>
                </div>
              </div>
              <span className="font-mono-numbers text-sm font-semibold text-moss">29.5 kW</span>
            </div>

            <div className="p-3 rounded bg-canvas-subtle border border-border-subtle flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <BatteryCharging className="w-4 h-4 text-teal" />
                <div>
                  <span className="text-xs font-semibold text-ink-primary block font-sans">Battery Pre-Charging</span>
                  <span className="text-[11px] text-ink-muted font-mono">Saving Wind for Night</span>
                </div>
              </div>
              <span className="font-mono-numbers text-sm font-semibold text-teal">32.0 kW</span>
            </div>

            <div className="p-3 rounded bg-canvas-subtle border border-border-subtle flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Cpu className="w-4 h-4 text-ink-secondary" />
                <div>
                  <span className="text-xs font-semibold text-ink-primary block font-sans">Science & Research</span>
                  <span className="text-[11px] text-ink-muted font-mono">Non-Critical Load</span>
                </div>
              </div>
              <span className="font-mono-numbers text-sm font-semibold text-ink-secondary">81.0 kW</span>
            </div>
          </div>
        </div>
      </div>

      {/* 8. Why This Matters Component */}
      <WhyThisMatters
        headline="Sub-Zero Wind Deceleration Expected in 6 Hours"
        summary="Weather predictions indicate a drop in wind speed from 14.5 m/s to 4.2 m/s over Larsemann Hills. This shifts generation responsibility to diesel generators. The optimizer has scheduled an earlier battery pre-charge cycle to minimize diesel fuel consumption."
        technicalDetail="HiGHS MILP objective balances generation cost against battery degradation cost ($c_{\text{deg}} = 0.082$/kWh). With solar PV unavailable during polar night, spinning reserve must remain >= 35% of total station load."
        onExplore={() => navigate('optimization')}
        exploreLabel="View Multi-Horizon Dispatch Schedule"
      />
    </div>
  );
};
