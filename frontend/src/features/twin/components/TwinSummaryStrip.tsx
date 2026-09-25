/**
 * POLARIS-EMS — Digital Twin Summary Strip & Narrative Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders the top executive operational summary strip and plain-language narrative.
 */

import React from 'react';
import { 
  Zap, 
  Wind, 
  Sun, 
  Fuel, 
  BatteryCharging, 
  Thermometer, 
  ShieldCheck, 
  Sparkles,
  Info
} from 'lucide-react';
import { TwinViewModel } from '../model/twinTypes';
import { StatusBadge } from '../../../components/common/StatusBadge';
import { ProvenanceTag } from '../../../components/common/ProvenanceTag';
import { JargonTooltip } from '../../../components/common/JargonTooltip';

interface TwinSummaryStripProps {
  viewModel: TwinViewModel;
  onInspectEvidence?: () => void;
}

export const TwinSummaryStrip: React.FC<TwinSummaryStripProps> = ({
  viewModel,
  onInspectEvidence
}) => {
  const { powerSummary, environment, thermal, resilience, stationId } = viewModel;

  // Plain-language narrative derivation from real Twin data
  let whatIsHappening = `Renewable generation is supplying ${powerSummary.renewableFractionPct.toFixed(0)}% of station electrical load.`;
  let whyThisMatters = `Keeping clean wind and solar dominant preserves precious shipped-in diesel fuel in station tanks.`;

  if (powerSummary.dieselGenerationKw > 10.0) {
    whatIsHappening = `Diesel generators are engaged (${powerSummary.dieselGenerationKw.toFixed(1)} kW) to support renewable generation during low sun/wind.`;
    whyThisMatters = `Ensures 35% spinning reserve is continuously maintained to prevent polar habitat freezing.`;
  } else if (powerSummary.batteryPowerKw < -5.0) {
    whatIsHappening = `Excess renewable generation is currently pre-charging the battery bank at ${Math.abs(powerSummary.batteryPowerKw).toFixed(1)} kW.`;
    whyThisMatters = `Storing clean energy now ensures nighttime and blizzard heating can run without burning fuel.`;
  }

  return (
    <div className="space-y-4 select-none">
      {/* 1. Human-Readable Twin Narrative Box (Mandatory Section 33) */}
      <div className="editorial-sheet rounded-lg p-4 sm:p-5 border-l-4 border-l-copper shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-border-subtle">
          <div className="flex items-center space-x-2 text-xs font-mono font-bold uppercase tracking-wider text-copper">
            <Sparkles className="w-3.5 h-3.5" />
            <span>OPERATIONAL TWIN SUMMARY • {stationId}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-mono text-ink-muted">MODEL STATUS:</span>
            <span className="text-[10px] font-mono font-bold text-moss uppercase px-1.5 py-0.5 rounded bg-moss-soft">
              PHYSICS CONSERVED
            </span>
            <ProvenanceTag provenance={viewModel.provenance} size="xs" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 font-sans">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-copper block mb-0.5">
              WHAT IS HAPPENING?
            </span>
            <p className="text-xs text-ink-primary font-medium leading-relaxed">
              {whatIsHappening}
            </p>
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-teal block mb-0.5">
              WHY THIS MATTERS
            </span>
            <p className="text-xs text-ink-secondary leading-relaxed">
              {whyThisMatters}
            </p>
          </div>
        </div>
      </div>

      {/* 2. Executive Metric Vitals Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Demand */}
        <div className="editorial-sheet rounded p-3">
          <span className="text-[9px] font-mono uppercase text-ink-muted block">TOTAL DEMAND</span>
          <div className="text-lg font-serif font-bold text-ink-primary mt-0.5">
            {powerSummary.totalLoadKw.toFixed(1)} <span className="text-[10px] font-mono text-ink-muted font-normal">kW</span>
          </div>
          <span className="text-[9px] font-mono text-moss block">
            {powerSummary.criticalLoadKw.toFixed(1)} kW P1 Critical
          </span>
        </div>

        {/* Renewable Share */}
        <div className="editorial-sheet rounded p-3">
          <span className="text-[9px] font-mono uppercase text-ink-muted block">RENEWABLE SHARE</span>
          <div className="text-lg font-serif font-bold text-teal mt-0.5">
            {powerSummary.renewableFractionPct.toFixed(0)}%
          </div>
          <span className="text-[9px] font-mono text-ink-muted block">
            {(powerSummary.solarGenerationKw + powerSummary.windGenerationKw).toFixed(1)} kW Clean
          </span>
        </div>

        {/* Diesel Active */}
        <div className="editorial-sheet rounded p-3">
          <span className="text-[9px] font-mono uppercase text-ink-muted block">DIESEL OUTPUT</span>
          <div className={`text-lg font-serif font-bold mt-0.5 ${powerSummary.dieselGenerationKw > 0.05 ? 'text-copper' : 'text-ink-muted'}`}>
            {powerSummary.dieselGenerationKw.toFixed(1)} <span className="text-[10px] font-mono text-ink-muted font-normal">kW</span>
          </div>
          <span className="text-[9px] font-mono text-ink-muted block">
            {powerSummary.dieselGenerationKw > 0.05 ? 'Genset Online' : 'Warm Standby'}
          </span>
        </div>

        {/* Battery SOC */}
        <div className="editorial-sheet rounded p-3">
          <span className="text-[9px] font-mono uppercase text-ink-muted block"><JargonTooltip term="State of Charge">BATTERY SOC</JargonTooltip></span>
          <div className="text-lg font-serif font-bold text-ice mt-0.5">
            {powerSummary.batterySocPct.toFixed(0)}%
          </div>
          <span className="text-[9px] font-mono text-ink-muted block">
            {powerSummary.batteryPowerKw < -0.1 ? `Charging ${Math.abs(powerSummary.batteryPowerKw).toFixed(1)} kW` : powerSummary.batteryPowerKw > 0.1 ? `Discharging ${powerSummary.batteryPowerKw.toFixed(1)} kW` : 'Float Mode'}
          </span>
        </div>

        {/* Indoor Habitat Temp */}
        <div className="editorial-sheet rounded p-3">
          <span className="text-[9px] font-mono uppercase text-ink-muted block">HABITAT TEMP</span>
          <div className="text-lg font-serif font-bold text-ink-primary mt-0.5">
            {thermal.indoorTempC.toFixed(1)}°C
          </div>
          <span className="text-[9px] font-mono text-moss block">
            Setpoint {thermal.targetTempC.toFixed(0)}°C (Safe)
          </span>
        </div>

        {/* Survival Runway */}
        <div className="editorial-sheet rounded p-3">
          <span className="text-[9px] font-mono uppercase text-ink-muted block"><JargonTooltip term="Resilience">SURVIVAL RUNWAY</JargonTooltip></span>
          <div className="text-lg font-serif font-bold text-copper mt-0.5">
            {resilience.survivalHorizonHours.toFixed(0)}h
          </div>
          <span className="text-[9px] font-mono text-ink-muted block truncate">
            {resilience.threatState}
          </span>
        </div>
      </div>
    </div>
  );
};
