/**
 * POLARIS-EMS — Digital Twin Source Mix Bar Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders proportional source contribution bar: Solar | Wind | Diesel | Battery.
 */

import React from 'react';

interface TwinSourceMixProps {
  solarKw: number;
  windKw: number;
  dieselKw: number;
  batteryKw: number; // positive = net supplier
  totalLoadKw: number;
}

export const TwinSourceMix: React.FC<TwinSourceMixProps> = ({
  solarKw,
  windKw,
  dieselKw,
  batteryKw,
  totalLoadKw
}) => {
  const batDischarge = Math.max(0, batteryKw);
  const totalSupply = Math.max(0.1, solarKw + windKw + dieselKw + batDischarge);

  const solarPct = (solarKw / totalSupply) * 100;
  const windPct = (windKw / totalSupply) * 100;
  const dieselPct = (dieselKw / totalSupply) * 100;
  const batPct = (batDischarge / totalSupply) * 100;

  return (
    <div className="space-y-1.5 font-mono text-xs">
      <div className="flex items-center justify-between text-[10px] text-ink-muted uppercase">
        <span>GENERATION SOURCE MIX</span>
        <span>TOTAL LOAD: <strong className="text-ink-primary font-bold">{totalLoadKw.toFixed(1)} kW</strong></span>
      </div>

      {/* Proportional Segmented Bar */}
      <div className="h-2.5 w-full rounded-sm bg-canvas-subtle overflow-hidden flex border border-border-subtle">
        {solarPct > 0 && (
          <div
            style={{ width: `${solarPct}%` }}
            className="bg-amber-500 transition-all duration-300"
            title={`Solar PV: ${solarKw.toFixed(1)} kW (${solarPct.toFixed(0)}%)`}
          />
        )}
        {windPct > 0 && (
          <div
            style={{ width: `${windPct}%` }}
            className="bg-teal transition-all duration-300"
            title={`Wind Turbines: ${windKw.toFixed(1)} kW (${windPct.toFixed(0)}%)`}
          />
        )}
        {batPct > 0 && (
          <div
            style={{ width: `${batPct}%` }}
            className="bg-ice transition-all duration-300"
            title={`Battery BESS: ${batDischarge.toFixed(1)} kW (${batPct.toFixed(0)}%)`}
          />
        )}
        {dieselPct > 0 && (
          <div
            style={{ width: `${dieselPct}%` }}
            className="bg-copper transition-all duration-300"
            title={`Diesel Gensets: ${dieselKw.toFixed(1)} kW (${dieselPct.toFixed(0)}%)`}
          />
        )}
      </div>

      {/* Numerical breakdown badges */}
      <div className="flex flex-wrap items-center justify-between text-[10px] pt-0.5 text-ink-secondary">
        <span className="flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
          <span>Solar: {solarKw.toFixed(1)} kW</span>
        </span>
        <span className="flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-teal"></span>
          <span>Wind: {windKw.toFixed(1)} kW</span>
        </span>
        <span className="flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-ice"></span>
          <span>Battery: {batteryKw > 0 ? `+${batteryKw.toFixed(1)}` : batteryKw.toFixed(1)} kW</span>
        </span>
        <span className="flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-copper"></span>
          <span>Diesel: {dieselKw.toFixed(1)} kW</span>
        </span>
      </div>
    </div>
  );
};
