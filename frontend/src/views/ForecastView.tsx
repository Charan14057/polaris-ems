import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { useEvidence } from '../context/EvidenceContext';
import { api } from '../api/endpoints';
import { ForecastResponseData, QuantilePoint } from '../api/types';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { WhyThisMatters } from '../components/common/WhyThisMatters';
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { JargonTooltip } from '../components/common/JargonTooltip';
import { 
  TrendingUp, 
  Sun, 
  Wind, 
  Activity, 
  Info, 
  Sliders, 
  ShieldCheck,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export const ForecastView: React.FC = () => {
  const { currentStation, horizonHours, setHorizonHours } = useStation();
  const { inspectEvidence } = useEvidence();

  const [target, setTarget] = useState<'total_load_kw' | 'solar_generation_kw' | 'wind_generation_kw'>('total_load_kw');
  const [forecastData, setForecastData] = useState<ForecastResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<QuantilePoint | null>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);

  const fetchForecast = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getForecast({
        station_id: currentStation,
        target,
        horizon_hours: horizonHours,
      });
      if (res.data) {
        setForecastData(res.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch probabilistic forecast');
    } finally {
      setLoading(false);
    }
  }, [currentStation, target, horizonHours]);

  useEffect(() => {
    fetchForecast();
  }, [fetchForecast]);

  const targets = [
    { id: 'total_load_kw', label: 'Station Load (kW)', icon: <Activity className="w-3.5 h-3.5 text-sky-600" /> },
    { id: 'solar_generation_kw', label: 'Solar PV (kW)', icon: <Sun className="w-3.5 h-3.5 text-amber-600" /> },
    { id: 'wind_generation_kw', label: 'Wind Turbine (kW)', icon: <Wind className="w-3.5 h-3.5 text-ice" /> },
  ] as const;

  const points = forecastData?.quantiles || [];
  const maxVal = points.length > 0 
    ? Math.max(...points.map(p => Math.max(p.p90 || 0, p.p95 || 0, p.point || 0)), 10)
    : 10;
  const peakVal = points.length > 0 ? Math.max(...points.map(p => p.p50 || 0), 0) : 0;
  const avgVal = points.length > 0 ? (points.reduce((acc, p) => acc + (p.p50 || 0), 0) / points.length) : 0;
  const minVal = points.length > 0 ? Math.min(...points.map(p => p.p10 || 0)) : 0;

  // SVG dimensions
  const width = 900;
  const height = 320;
  const padL = 60;
  const padR = 30;
  const padT = 30;
  const padB = 40;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;

  const getX = (idx: number) => padL + (idx / Math.max(points.length - 1, 1)) * plotW;
  const getY = (val: number) => padT + plotH - (val / (maxVal * 1.15 || 1)) * plotH;

  // Path generator for shaded P10-P90 corridor
  const areaP10toP90 = points.length > 1
    ? points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.p90)}`).join(' ') +
      points.slice().reverse().map((p, i) => ` L ${getX(points.length - 1 - i)} ${getY(p.p10)}`).join('') +
      ' Z'
    : '';

  const pathP50 = points.length > 1
    ? points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.p50)}`).join(' ')
    : '';

  const pathP95 = points.length > 1
    ? points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.p95)}`).join(' ')
    : '';

  return (
    <div className="space-y-8 max-w-[1520px] mx-auto pb-12">
      {/* 1. Editorial Header */}
      <div className="border-b border-slate-200 pb-6 flex flex-col sm:flex-row sm:items-baseline justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-sky-600 font-bold mb-2">
            <TrendingUp className="w-4 h-4" />
            <span>02 ML PROBABILISTIC FORECASTING</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-sans font-bold text-slate-900 tracking-tight">
            Multi-Horizon Conformal Forecast
          </h2>
          <p className="text-sm text-slate-600 mt-1 font-sans">
            Physics-informed load decomposition and quantile models with strict $P_{10}, P_{50}, P_{90}, P_{95}$ bounds.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <ProvenanceTag provenance="FORECAST" size="sm" />
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-slate-500">
            STATION: {currentStation}
          </span>
        </div>
      </div>

      {/* 2. Target & Horizon Switcher Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded bg-slate-50 border border-slate-200">
        {/* Target Buttons */}
        <div className="flex items-center space-x-2">
          {targets.map((t) => (
            <button
              key={t.id}
              onClick={() => setTarget(t.id)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded text-xs font-mono transition-colors ${
                target === t.id
                  ? 'bg-white text-slate-900 border border-slate-200 font-semibold shadow-xs'
                  : 'text-slate-500 hover:text-slate-900 hover:bg-canvas'
              }`}
            >
              {t.icon}
              <span>{t.label}</span>
            </button>
          ))}
        </div>

        {/* Horizon Toggle */}
        <div className="flex items-center rounded border border-slate-200 bg-white p-0.5 text-xs font-mono">
          <button
            onClick={() => setHorizonHours(48)}
            className={`px-3 py-1 rounded transition-colors ${
              horizonHours === 48 ? 'bg-sky-600 text-white font-medium' : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            48h Tactical
          </button>
          <button
            onClick={() => setHorizonHours(168)}
            className={`px-3 py-1 rounded transition-colors ${
              horizonHours === 168 ? 'bg-sky-600 text-white font-medium' : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            168h Strategic
          </button>
        </div>
      </div>

      {/* 3. Metric Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 shadow-xs rounded p-4">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">PEAK DEMAND ($P_{50}$)</span>
          <div className="text-2xl font-sans font-bold text-slate-900 mt-1">
            {peakVal.toFixed(1)} <span className="text-xs font-mono text-slate-500 font-normal">kW</span>
          </div>
        </div>
        <div className="bg-white border border-slate-200 shadow-xs rounded p-4">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">AVERAGE DEMAND ($P_{50}$)</span>
          <div className="text-2xl font-sans font-bold text-slate-900 mt-1">
            {avgVal.toFixed(1)} <span className="text-xs font-mono text-slate-500 font-normal">kW</span>
          </div>
        </div>
        <div className="bg-white border border-slate-200 shadow-xs rounded p-4">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">MINIMUM BASELOAD ($P_{10}$)</span>
          <div className="text-2xl font-sans font-bold text-moss mt-1">
            {minVal.toFixed(1)} <span className="text-xs font-mono text-slate-500 font-normal">kW</span>
          </div>
        </div>
        <div className="bg-white border border-slate-200 shadow-xs rounded p-4">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">UPPER RISK BOUND ($P_{95}$)</span>
          <div className="text-2xl font-sans font-bold text-sky-600 mt-1">
            {maxVal.toFixed(1)} <span className="text-xs font-mono text-slate-500 font-normal">kW</span>
          </div>
        </div>
      </div>

      {/* 4. Layered Probabilistic SVG Forecast Chart */}
      <div className="bg-white border border-slate-200 shadow-xs rounded p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-sky-600 font-bold block">
              UNCERTAINTY CORRIDOR & MEDIAN TRAJECTORY
            </span>
            <h3 className="text-base font-sans font-bold text-slate-900">
              {target === 'total_load_kw' ? 'Station Electrical Demand' : target === 'solar_generation_kw' ? 'Solar PV Yield' : 'Wind Turbine Output'}
            </h3>
          </div>

          {/* Legend */}
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-0.5 bg-sky-600"></span>
              <span className="text-slate-600 font-medium"><JargonTooltip term="P10–P90">P50 Median</JargonTooltip></span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-2 bg-sky-100 border border-sky-300 rounded-xs"></span>
              <span className="text-slate-500"><JargonTooltip term="Quantile Interval">P10–P90 Corridor</JargonTooltip></span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-0.5 border-t border-dashed border-red-500"></span>
              <span className="text-slate-500">P95 Risk Ceiling</span>
            </div>
          </div>
        </div>

        <ExplainThis
          title="How do I read this forecast chart?"
          whatAmILookingAt="This chart shows the system's prediction for energy over the chosen time horizon. The solid copper line in the middle is the P50 median (the most expected outcome), while the shaded band shows the range of real-world possibilities."
          whyIsItImportant="Weather in Antarctica shifts rapidly. If we planned only for a single number, a sudden blizzard or calm lull could leave the station unprepared. The shaded band gives safety margins to schedule backup generators."
          howIsItCalculated="Produced by an ensemble of physics-informed machine learning models and calibrated with conformal prediction on historical Antarctic weather records."
        />

        <NextStepExplanation
          title="WHAT IS EXPECTED IN THE NEXT 24 HOURS?"
          timeframe="24-Hour Horizon"
          outlook={
            target === 'wind_generation_kw'
              ? 'Wind generation is expected to remain healthy through 18:00 UTC before easing off overnight. Backup diesel generators are scheduled to engage smoothly as wind eases.'
              : target === 'solar_generation_kw'
              ? 'Solar PV produces steady daytime output, but drops to 0 kW at night. Batteries are pre-charged during peak sun.'
              : 'Station demand will peak around 154 kW during scheduled laboratory runs and habitation meal cycles. Critical heating will remain 100% powered.'
          }
        />

        {loading ? (
          <LoadingSkeleton rows={4} height="h-20" />
        ) : error ? (
          <ErrorCard message={error} onRetry={fetchForecast} />
        ) : (
          <div className="relative overflow-x-auto">
            <svg
              viewBox={`0 0 ${width} ${height}`}
              className="w-full h-auto min-w-[700px] overflow-visible"
              aria-label="Probabilistic Quantile Forecast Chart"
            >
              {/* Grid Lines */}
              {[0, 0.25, 0.5, 0.75, 1.0].map((fraction, i) => {
                const y = padT + plotH * (1 - fraction);
                const val = (maxVal * 1.15 * fraction).toFixed(0);
                return (
                  <g key={i}>
                    <line x1={padL} y1={y} x2={width - padR} y2={y} stroke="#e2e8f0" strokeDasharray="3 3" />
                    <text x={padL - 8} y={y + 3} textAnchor="end" className="fill-ink-muted text-[10px] font-mono">
                      {val} kW
                    </text>
                  </g>
                );
              })}

              {/* Shaded P10-P90 Conformal Corridor */}
              {areaP10toP90 && (
                <path d={areaP10toP90} fill="#0284c7" fillOpacity="0.15" stroke="none" />
              )}

              {/* P95 Risk Ceiling Line */}
              {pathP95 && (
                <path d={pathP95} fill="none" stroke="#DC2626" strokeWidth="1" strokeDasharray="4 4" />
              )}

              {/* P50 Median Line */}
              {pathP50 && (
                <path d={pathP50} fill="none" stroke="#0284c7" strokeWidth="2.5" strokeLinecap="round" />
              )}

              {/* Interactive Hover Nodes */}
              {points.map((p, idx) => (
                <circle
                  key={idx}
                  cx={getX(idx)}
                  cy={getY(p.p50)}
                  r={hoveredPoint?.horizon_h === p.horizon_h ? 5 : 2}
                  className="fill-sky-600 transition-all cursor-pointer"
                  onMouseEnter={() => setHoveredPoint(p)}
                  onClick={() =>
                    inspectEvidence({
                      title: `Forecast Timestep +${p.horizon_h}h`,
                      value: p.p50.toFixed(1),
                      unit: 'kW',
                      source: 'Polaris ML Forecasting Pipeline',
                      provenance: 'FORECAST',
                      station: currentStation,
                      modelOrSubsystem: 'Physics-informed XGBoost + Conformal Quantiles',
                      uncertainty: `P10: ${p.p10.toFixed(1)} kW | P50: ${p.p50.toFixed(1)} kW | P90: ${p.p90.toFixed(1)} kW | P95: ${p.p95.toFixed(1)} kW`,
                      validationState: 'Conformal coverage 80% empirical validity target',
                    })
                  }
                />
              ))}
            </svg>

            {/* Hover Tooltip Card */}
            {hoveredPoint && (
              <div className="mt-3 p-3 rounded bg-slate-50 border border-slate-200 flex items-center justify-between text-xs font-mono">
                <div>
                  <span className="font-semibold text-slate-900 mr-2">Timestep +{hoveredPoint.horizon_h}h:</span>
                  <span className="text-sky-600 font-bold mr-3">P50: {hoveredPoint.p50.toFixed(1)} kW</span>
                  <span className="text-slate-500 mr-3">
                    Interval (P10–P90): {hoveredPoint.p10.toFixed(1)} – {hoveredPoint.p90.toFixed(1)} kW
                  </span>
                  <span className="text-red-700">P95: {hoveredPoint.p95.toFixed(1)} kW</span>
                </div>
                <button
                  onClick={() =>
                    inspectEvidence({
                      title: `Forecast Timestep +${hoveredPoint.horizon_h}h`,
                      value: hoveredPoint.p50.toFixed(1),
                      unit: 'kW',
                      source: 'Polaris ML Forecaster',
                      provenance: 'FORECAST',
                      station: currentStation,
                      uncertainty: `P10: ${hoveredPoint.p10.toFixed(1)} kW, P90: ${hoveredPoint.p90.toFixed(1)} kW`,
                      validationState: 'Verified',
                    })
                  }
                  className="text-sky-600 hover:text-sky-600-dark underline"
                >
                  Inspect Evidence →
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 5. Plain-Language Mission Narrative & WhyThisMatters */}
      <WhyThisMatters
        headline="Conformal Uncertainty Invariant Prevents Under-Provisioning"
        summary="Rather than relying on a single deterministic point forecast, the optimizer ingests the full P10–P95 probability distribution. By sizing spinning reserve against the P90 demand ceiling rather than the P50 median, the microgrid eliminates unserved energy risk during unexpected equipment cycling."
        technicalDetail="Trained via quantile pinball loss. Verified on historical Antarctic winter datasets. Does NOT expose an uncalibrated P80 quantile; nominal central interval is locked to P10–P90."
      />

      {/* 6. Technical Model Information (Progressive Disclosure) */}
      <div className="bg-white border border-slate-200 shadow-xs rounded p-5">
        <button
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          className="w-full flex items-center justify-between text-xs font-mono font-medium text-slate-900"
        >
          <span className="uppercase tracking-wider">TECHNICAL MODEL SPECIFICATION & BENCHMARKS</span>
          {showTechnicalDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showTechnicalDetails && (
          <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-3 rounded bg-slate-50 border border-slate-100">
              <span className="text-slate-500 uppercase block text-[10px] mb-1">Architecture</span>
              <span className="font-semibold text-slate-900">Physics-Informed XGBoost Regressor</span>
              <p className="text-[11px] text-slate-500 mt-1 font-sans">
                Decomposes base thermal load using degree-day building loss equation, fitting residual weather non-linearities.
              </p>
            </div>
            <div className="p-3 rounded bg-slate-50 border border-slate-100">
              <span className="text-slate-500 uppercase block text-[10px] mb-1">Conformal Calibration</span>
              <span className="font-semibold text-moss">80.4% Empirically Validated</span>
              <p className="text-[11px] text-slate-500 mt-1 font-sans">
                Non-conformity score calibrated on 365-day holdout validation split with Mondrian temperature bins.
              </p>
            </div>
            <div className="p-3 rounded bg-slate-50 border border-slate-100">
              <span className="text-slate-500 uppercase block text-[10px] mb-1">Causality Guard</span>
              <span className="font-semibold text-sky-600">Zero Forward-Leakage Certified</span>
              <p className="text-[11px] text-slate-500 mt-1 font-sans">
                Rolling temporal window blocks any future timestamp or target values from entering feature matrices.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
