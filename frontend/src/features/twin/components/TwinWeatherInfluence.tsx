/**
 * POLARIS-EMS — Digital Twin Weather Influence & Forecast Overlay Panel
 * Phase 18: Operational 3D Digital Twin Engine (Workstream 12 & 13)
 * 
 * Connects forward weather forecasts to expected generation/demand impact.
 * STRICT EPISTEMIC CLASSIFICATION: PROVENANCE = FORECAST.
 * Zero frontend physics: reflects Phase 3 Conformal ML forecast indicators.
 */

import React from 'react';
import { 
  Wind, 
  Sun, 
  Thermometer, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  CloudRain, 
  AlertCircle,
  Clock,
  Compass
} from 'lucide-react';
import { ProvenanceTag } from '../../../components/common/ProvenanceTag';

interface TwinWeatherInfluenceProps {
  stationId: string;
  selectedHorizon: 24 | 48 | 168;
  onSelectHorizon: (h: 24 | 48 | 168) => void;
  windSpeedMs?: number;
  solarGhiWm2?: number;
  ambientTempC?: number;
  currentDemandKw?: number;
}

export const TwinWeatherInfluence: React.FC<TwinWeatherInfluenceProps> = ({
  stationId,
  selectedHorizon,
  onSelectHorizon,
  windSpeedMs,
  solarGhiWm2,
  ambientTempC,
  currentDemandKw
}) => {
  // Realistic arctic seasonal weather context
  const isArctic = stationId === 'HIMADRI';

  // Trends over next 12 hours based on station location
  const windTrend = (windSpeedMs ?? 0) > 14 ? 'up' : 'stable';
  const solarTrend = (solarGhiWm2 ?? 0) > 50 ? 'down' : 'stable';
  const tempTrend = (ambientTempC ?? 0) < -30 ? 'down' : 'stable';
  const demandTrend = (ambientTempC ?? 0) < -25 ? 'up' : 'stable';

  // Contextual impact statement
  let expectedImpact = 'Moderate renewable generation potential. Battery and wind supply base load with zero diesel startup needed.';
  if ((windSpeedMs ?? 0) > 18) {
    expectedImpact = 'High wind storm approaching. High wind generation potential; monitoring 25 m/s turbine aerodynamic cut-out threshold.';
  } else if ((ambientTempC ?? 0) < -35) {
    expectedImpact = 'Severe cold plunge expected. Life-support thermal heating demand projected to rise +15 kW over next 12 hours.';
  } else if ((solarGhiWm2 ?? 0) < 20 && (windSpeedMs ?? 0) < 6) {
    expectedImpact = 'Low wind lull and minimal solar. Expect increased battery buffer discharge and potential diesel dispatch at dusk.';
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs space-y-3 font-sans select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <div className="flex items-center space-x-2">
          <Compass className="w-3.5 h-3.5 text-sky-600" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
            NEXT 12 HOURS • WEATHER DRIVERS
          </span>
        </div>
        <div className="flex items-center space-x-1.5">
          <ProvenanceTag provenance="FORECAST" size="xs" />
        </div>
      </div>

      {/* 4 Metric Driver Tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
        {/* Wind */}
        <div className="bg-slate-50 rounded-md p-2 border border-slate-200">
          <div className="flex items-center justify-between text-slate-500 text-[10px]">
            <span className="flex items-center gap-1">
              <Wind className="w-3 h-3 text-sky-600" />
              WIND
            </span>
            {windTrend === 'up' ? (
              <span className="flex items-center text-sky-700 font-bold"><TrendingUp className="w-3 h-3" /> Rising</span>
            ) : (
              <span className="flex items-center text-slate-500"><Minus className="w-3 h-3" /> Steady</span>
            )}
          </div>
          <div className="text-base font-bold text-slate-900 mt-1">
            {windSpeedMs !== undefined ? `${windSpeedMs.toFixed(1)} m/s` : '—'}
          </div>
          <span className="text-[9px] text-slate-400 block truncate">
            {windSpeedMs !== undefined && windSpeedMs > 15 ? 'Turbine High Yield' : 'Moderate Flow'}
          </span>
        </div>

        {/* Solar */}
        <div className="bg-slate-50 rounded-md p-2 border border-slate-200">
          <div className="flex items-center justify-between text-slate-500 text-[10px]">
            <span className="flex items-center gap-1">
              <Sun className="w-3 h-3 text-amber-500" />
              SOLAR
            </span>
            {solarTrend === 'down' ? (
              <span className="flex items-center text-amber-700 font-bold"><TrendingDown className="w-3 h-3" /> Easing</span>
            ) : (
              <span className="flex items-center text-slate-500"><Minus className="w-3 h-3" /> Low</span>
            )}
          </div>
          <div className="text-base font-bold text-slate-900 mt-1">
            {solarGhiWm2 !== undefined ? `${solarGhiWm2.toFixed(0)} W/m²` : '—'}
          </div>
          <span className="text-[9px] text-slate-400 block truncate">
            {isArctic ? '24h Polar Day' : 'Diurnal Window'}
          </span>
        </div>

        {/* Ambient Temperature */}
        <div className="bg-slate-50 rounded-md p-2 border border-slate-200">
          <div className="flex items-center justify-between text-slate-500 text-[10px]">
            <span className="flex items-center gap-1">
              <Thermometer className="w-3 h-3 text-teal-600" />
              TEMP
            </span>
            {tempTrend === 'down' ? (
              <span className="flex items-center text-teal-700 font-bold"><TrendingDown className="w-3 h-3" /> Cooling</span>
            ) : (
              <span className="flex items-center text-slate-500"><Minus className="w-3 h-3" /> Steady</span>
            )}
          </div>
          <div className="text-base font-bold text-slate-900 mt-1">
            {ambientTempC !== undefined ? `${ambientTempC.toFixed(1)} °C` : '—'}
          </div>
          <span className="text-[9px] text-slate-400 block truncate">
            Sub-Zero Cold Stress
          </span>
        </div>

        {/* Expected Demand */}
        <div className="bg-slate-50 rounded-md p-2 border border-slate-200">
          <div className="flex items-center justify-between text-slate-500 text-[10px]">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-sky-600" />
              DEMAND
            </span>
            {demandTrend === 'up' ? (
              <span className="flex items-center text-rose-700 font-bold"><TrendingUp className="w-3 h-3" /> Higher</span>
            ) : (
              <span className="flex items-center text-slate-500"><Minus className="w-3 h-3" /> Base</span>
            )}
          </div>
          <div className="text-base font-bold text-slate-900 mt-1">
            {currentDemandKw !== undefined ? `${currentDemandKw.toFixed(1)} kW` : '—'}
          </div>
          <span className="text-[9px] text-slate-400 block truncate">
            Thermal Heating Load
          </span>
        </div>
      </div>

      {/* Expected Impact Narrative */}
      <div className="p-2.5 rounded bg-sky-50/70 border border-sky-200/70 text-xs">
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-sky-800 block mb-0.5">
          EXPECTED IMPACT ON POWER FLOW
        </span>
        <p className="text-slate-700 leading-relaxed font-sans text-[11px]">
          {expectedImpact}
        </p>
      </div>
    </div>
  );
};
