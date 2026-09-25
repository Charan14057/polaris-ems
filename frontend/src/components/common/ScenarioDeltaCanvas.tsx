import React from 'react';
import { ArrowRight, Wind, AlertCircle, Zap, ShieldAlert, Cpu } from 'lucide-react';

export interface ScenarioDeltaProps {
  scenarioName?: string;
  category?: string;
  baselineGen?: { wind: number; solar: number; diesel: number };
  scenarioGen?: { wind: number; solar: number; diesel: number };
  baselineResilience?: string;
  scenarioResilience?: string;
  baselineHorizon?: number;
  scenarioHorizon?: number;
  className?: string;
}

export const ScenarioDeltaCanvas: React.FC<ScenarioDeltaProps> = ({
  scenarioName = 'BLIZZARD STORM (28 m/s)',
  category = 'Severe Weather Perturbation',
  baselineGen = { wind: 65, solar: 22, diesel: 40 },
  scenarioGen = { wind: 0, solar: 0, diesel: 110 },
  baselineResilience = 'SAFE',
  scenarioResilience = 'WATCH',
  baselineHorizon = 142.0,
  scenarioHorizon = 84.0,
  className = '',
}) => {
  return (
    <div className={`editorial-sheet rounded p-5 sm:p-6 ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-5 border-b border-border-subtle gap-2">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-copper font-bold block">
            SCENARIO DELTA CANVAS
          </span>
          <h3 className="text-base font-serif font-bold text-ink-primary">
            Causal Impact: Baseline vs. {scenarioName}
          </h3>
        </div>
        <span className="text-xs font-mono text-ink-muted">CATEGORY: {category}</span>
      </div>

      {/* 4-Step Causal Canvas Chain */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
        {/* Step 1: Injected Disturbance */}
        <div className="p-4 rounded bg-canvas-subtle border border-border-subtle">
          <div className="flex items-center space-x-2 text-xs font-mono text-copper font-bold mb-2">
            <Wind className="w-4 h-4" />
            <span>01 DISTURBANCE</span>
          </div>
          <div className="text-sm font-semibold text-ink-primary font-sans mb-1">
            Wind Exceeds Cut-Out
          </div>
          <p className="text-xs text-ink-secondary leading-relaxed">
            Gusts reach 28.5 m/s. Wind turbines enter aerodynamic storm cut-out to prevent mechanical blade failure.
          </p>
          <div className="mt-3 text-[11px] font-mono text-ink-muted bg-surface p-2 rounded border border-border-subtle">
            Wind power drops: <span className="text-danger font-semibold">65 kW → 0 kW</span>
          </div>
        </div>

        {/* Step 2: Generation Deficit */}
        <div className="p-4 rounded bg-canvas-subtle border border-border-subtle">
          <div className="flex items-center space-x-2 text-xs font-mono text-ice-dark font-bold mb-2">
            <Zap className="w-4 h-4" />
            <span>02 GENERATION DELTA</span>
          </div>
          <div className="text-sm font-semibold text-ink-primary font-sans mb-1">
            Loss of Renewables
          </div>
          <p className="text-xs text-ink-secondary leading-relaxed">
            Zero renewable contribution. Net microgrid deficit of 87 kW transferred to thermal/fuel generation.
          </p>
          <div className="mt-3 text-[11px] font-mono text-ink-muted bg-surface p-2 rounded border border-border-subtle">
            Renewables: <span className="text-danger font-semibold">60% → 0%</span>
          </div>
        </div>

        {/* Step 3: Dispatch Compensation */}
        <div className="p-4 rounded bg-canvas-subtle border border-border-subtle">
          <div className="flex items-center space-x-2 text-xs font-mono text-teal font-bold mb-2">
            <Cpu className="w-4 h-4" />
            <span>03 OPTIMIZER ACTION</span>
          </div>
          <div className="text-sm font-semibold text-ink-primary font-sans mb-1">
            Dual Genset Ramp-Up
          </div>
          <p className="text-xs text-ink-secondary leading-relaxed">
            HiGHS MILP ramps Diesel 1 to 65 kW and Diesel 2 to 45 kW with battery discharge support (30 kW).
          </p>
          <div className="mt-3 text-[11px] font-mono text-ink-muted bg-surface p-2 rounded border border-border-subtle">
            Diesel output: <span className="text-copper font-semibold">40 kW → 110 kW</span>
          </div>
        </div>

        {/* Step 4: Resilience Consequence */}
        <div className="p-4 rounded bg-copper-subtle border border-copper/30">
          <div className="flex items-center space-x-2 text-xs font-mono text-copper font-bold mb-2">
            <ShieldAlert className="w-4 h-4" />
            <span>04 RESILIENCE OUTCOME</span>
          </div>
          <div className="text-sm font-semibold text-ink-primary font-sans mb-1">
            Accelerated Fuel Burn
          </div>
          <p className="text-xs text-ink-secondary leading-relaxed">
            Station posture shifts from {baselineResilience} to {scenarioResilience}. Critical loads remain 100% powered, but fuel runway shortens.
          </p>
          <div className="mt-3 text-[11px] font-mono text-ink-muted bg-surface p-2 rounded border border-border-subtle">
            Runway: <span className="text-copper font-bold">{baselineHorizon}h → {scenarioHorizon}h</span>
          </div>
        </div>
      </div>
    </div>
  );
};
