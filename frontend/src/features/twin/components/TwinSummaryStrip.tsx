/**
 * POLARIS-EMS — Digital Twin Summary Strip & Narrative Component
 * Quiet Industrial / Arctic Utility Design
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
  let whatIsHappening = `Renewable generation is supplying ${powerSummary.renewableFractionPct.toFixed(0)}% of active station electrical load.`;
  let whyThisMatters = `Maximizing clean wind and solar preserves precious shipped-in diesel fuel in station tanks.`;

  if (powerSummary.dieselGenerationKw > 10.0) {
    whatIsHappening = `Diesel generators are engaged (${powerSummary.dieselGenerationKw.toFixed(1)} kW) to support renewable generation during low sun/wind.`;
    whyThisMatters = `Ensures 35% spinning reserve is continuously maintained to prevent polar habitat freezing.`;
  } else if (powerSummary.batteryPowerKw < -5.0) {
    whatIsHappening = `Excess renewable generation is currently pre-charging the battery bank at ${Math.abs(powerSummary.batteryPowerKw).toFixed(1)} kW.`;
    whyThisMatters = `Storing clean energy now ensures nighttime and blizzard heating can run without burning fuel.`;
  }

  return (
    <div className="space-y-3 select-none">
      {/* 1. Operational Twin Narrative Box */}
      <div className="bg-white rounded-lg p-3.5 sm:p-4 border border-slate-200 border-l-4 border-l-sky-600 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-2 border-b border-slate-100">
          <div className="flex items-center space-x-2 text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
            <span className="w-2 h-2 rounded-full bg-sky-600" />
            <span>OPERATIONAL TWIN SUMMARY • {stationId}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-mono font-bold text-emerald-700 uppercase px-1.5 py-0.5 rounded bg-emerald-50 border border-emerald-200">
              PHYSICS CONSERVED
            </span>
            <ProvenanceTag provenance={viewModel.provenance} size="xs" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 font-sans">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-sky-700 block mb-0.5">
              WHAT IS HAPPENING?
            </span>
            <p className="text-xs text-slate-900 font-medium leading-relaxed">
              {whatIsHappening}
            </p>
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-teal-700 block mb-0.5">
              WHY THIS MATTERS
            </span>
            <p className="text-xs text-slate-600 leading-relaxed">
              {whyThisMatters}
            </p>
          </div>
        </div>
      </div>

      {/* 2. Executive Metric Vitals Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Demand */}
        <div className="bg-white rounded-lg border border-slate-200 p-3 shadow-xs">
          <span className="text-[9px] font-mono uppercase text-slate-400 block">TOTAL DEMAND</span>
          <div className="text-lg font-bold font-mono-numbers text-slate-900 mt-0.5">
            {powerSummary.totalLoadKw.toFixed(1)} <span className="text-[10px] font-mono text-slate-400 font-normal">kW</span>
          </div>
          <span className="text-[9px] font-mono text-emerald-700 block truncate">
            {powerSummary.criticalLoadKw.toFixed(1)} kW P1 Critical
          </span>
        </div>

        {/* Renewable Share */}
        <div className="bg-white rounded-lg border border-slate-200 p-3 shadow-xs">
          <span className="text-[9px] font-mono uppercase text-slate-400 block">RENEWABLE SHARE</span>
          <div className="text-lg font-bold font-mono-numbers text-teal-700 mt-0.5">
            {powerSummary.renewableFractionPct.toFixed(0)}%
          </div>
          <span className="text-[9px] font-mono text-slate-400 block truncate">
            {(powerSummary.solarGenerationKw + powerSummary.windGenerationKw).toFixed(1)} kW Clean
          </span>
        </div>

        {/* Diesel Active */}
        <div className="bg-white rounded-lg border border-slate-200 p-3 shadow-xs">
          <span className="text-[9px] font-mono uppercase text-slate-400 block">DIESEL OUTPUT</span>
          <div className={`text-lg font-bold font-mono-numbers mt-0.5 ${powerSummary.dieselGenerationKw > 0.05 ? 'text-amber-700' : 'text-slate-400'}`}>
            {powerSummary.dieselGenerationKw.toFixed(1)} <span className="text-[10px] font-mono text-slate-400 font-normal">kW</span>
          </div>
          <span className="text-[9px] font-mono text-slate-400 block truncate">
            {powerSummary.dieselGenerationKw > 0.05 ? 'Genset Online' : 'Warm Standby'}
          </span>
        </div>

        {/* Battery SOC */}
        <div className="bg-white rounded-lg border border-slate-200 p-3 shadow-xs">
          <span className="text-[9px] font-mono uppercase text-slate-400 block"><JargonTooltip term="State of Charge">BATTERY SOC</JargonTooltip></span>
          <div className="text-lg font-bold font-mono-numbers text-sky-700 mt-0.5">
            {powerSummary.batterySocPct.toFixed(0)}%
          </div>
          <span className="text-[9px] font-mono text-slate-400 block truncate">
            {powerSummary.batteryPowerKw < -0.1 ? `Charging ${Math.abs(powerSummary.batteryPowerKw).toFixed(1)} kW` : powerSummary.batteryPowerKw > 0.1 ? `Discharging ${powerSummary.batteryPowerKw.toFixed(1)} kW` : 'Float Mode'}
          </span>
        </div>

        {/* Indoor Habitat Temp */}
        <div className="bg-white rounded-lg border border-slate-200 p-3 shadow-xs">
          <span className="text-[9px] font-mono uppercase text-slate-400 block">HABITAT TEMP</span>
          <div className="text-lg font-bold font-mono-numbers text-slate-900 mt-0.5">
            {thermal.indoorTempC.toFixed(1)}°C
          </div>
          <span className="text-[9px] font-mono text-emerald-700 block truncate">
            Setpoint {thermal.targetTempC.toFixed(0)}°C (Safe)
          </span>
        </div>

        {/* Survival Runway */}
        <div className="bg-white rounded-lg border border-slate-200 p-3 shadow-xs">
          <span className="text-[9px] font-mono uppercase text-slate-400 block"><JargonTooltip term="Resilience">SURVIVAL RUNWAY</JargonTooltip></span>
          <div className="text-lg font-bold font-mono-numbers text-slate-900 mt-0.5">
            {resilience.survivalHorizonHours.toFixed(0)}h
          </div>
          <span className="text-[9px] font-mono text-slate-400 block truncate">
            {resilience.threatState}
          </span>
        </div>
      </div>
    </div>
  );
};
