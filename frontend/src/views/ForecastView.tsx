import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { api } from '../api/endpoints';
import { ForecastResponseData, QuantilePoint } from '../api/types';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { TrendingUp, Sun, Wind, Activity, HelpCircle } from 'lucide-react';

export const ForecastView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();

  const [target, setTarget] = useState<'total_load_kw' | 'solar_generation_kw' | 'wind_generation_kw'>('total_load_kw');
  const [forecastData, setForecastData] = useState<ForecastResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<QuantilePoint | null>(null);

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
    { id: 'total_load_kw', label: 'Station Load (kW)', icon: <Activity className="w-3.5 h-3.5 text-orange-400" /> },
    { id: 'solar_generation_kw', label: 'Solar PV (kW)', icon: <Sun className="w-3.5 h-3.5 text-yellow-400" /> },
    { id: 'wind_generation_kw', label: 'Wind Turbine (kW)', icon: <Wind className="w-3.5 h-3.5 text-cyan-400" /> },
  ] as const;

  const points = forecastData?.quantiles || [];
  
  // Calculate chart boundaries
  const maxVal = Math.max(
    ...points.map(p => Math.max(p.p90 || 0, p.p95 || 0, p.point)),
    10
  );
  const peakVal = Math.max(...points.map(p => p.p50), 0);
  const avgVal = points.length > 0 ? (points.reduce((acc, p) => acc + p.p50, 0) / points.length) : 0;
  const minVal = points.length > 0 ? Math.min(...points.map(p => p.p10)) : 0;

  // Render SVG chart
  const width = 800;
  const height = 300;
  const padding = { top: 20, right: 30, bottom: 40, left: 50 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const getX = (idx: number) => padding.left + (idx / Math.max(points.length - 1, 1)) * chartW;
  const getY = (val: number) => padding.top + chartH - (val / (maxVal * 1.15)) * chartH;

  // Build P10-P90 polygon band
  const bandPoints = points.length > 1 ? [
    ...points.map((p, i) => `${getX(i)},${getY(p.p90)}`),
    ...[...points].reverse().map((p, i) => `${getX(points.length - 1 - i)},${getY(p.p10)}`),
  ].join(' ') : '';

  // Build P50 line path
  const p50Path = points.length > 1 ? points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.p50)}`).join(' ') : '';
  
  // Build Point forecast line path
  const pointPath = points.length > 1 ? points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.point)}`).join(' ') : '';

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Target Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-xl bg-polar-900/60 border border-polar-800">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold font-mono text-polar-100 uppercase tracking-wide">
              Probabilistic Operational Forecasting (Phase 3)
            </h2>
            <ProvenanceTag provenance="FORECAST" size="xs" />
          </div>
          <p className="text-xs text-polar-400 mt-1">
            XGBoost residual operational forecaster with Split Conformal Prediction uncertainty intervals.
          </p>
        </div>

        {/* Target Selector Tabs */}
        <div className="flex items-center bg-polar-950 p-1 rounded-lg border border-polar-800">
          {targets.map((t) => (
            <button
              key={t.id}
              onClick={() => setTarget(t.id)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
                target === t.id
                  ? 'bg-polar-800 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'text-polar-400 hover:text-polar-200'
              }`}
            >
              {t.icon}
              <span>{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton height="h-80" rows={1} />
      ) : error ? (
        <ErrorCard title="Forecast Retrieval Error" message={error} onRetry={fetchForecast} />
      ) : (
        <div className="space-y-6">
          {/* Main Forecast Chart Container */}
          <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4 text-xs font-mono">
                <span className="flex items-center space-x-1.5">
                  <span className="w-3 h-0.5 bg-cyan-400 inline-block" />
                  <span className="text-polar-200">P50 Expected</span>
                </span>
                <span className="flex items-center space-x-1.5">
                  <span className="w-3 h-2 bg-cyan-500/20 border border-cyan-500/40 inline-block rounded-xs" />
                  <span className="text-polar-300">P10 – P90 Conformal Band</span>
                </span>
                <span className="flex items-center space-x-1.5">
                  <span className="w-3 h-0.5 bg-amber-400/80 border-dashed inline-block" />
                  <span className="text-polar-400">Point Model</span>
                </span>
              </div>

              <div className="text-[11px] font-mono text-polar-400">
                Origin: {forecastData?.forecast_origin?.replace('T', ' ').substring(0, 16) || '2026-06-01'} UTC
              </div>
            </div>

            {/* SVG Chart */}
            <div className="w-full overflow-x-auto">
              <svg 
                viewBox={`0 0 ${width} ${height}`} 
                className="w-full h-auto min-w-[650px] overflow-visible"
              >
                {/* Grid Lines */}
                {[0, 0.25, 0.5, 0.75, 1.0].map((ratio, i) => {
                  const y = padding.top + chartH * ratio;
                  const val = (maxVal * 1.15 * (1 - ratio)).toFixed(0);
                  return (
                    <g key={i}>
                      <line 
                        x1={padding.left} 
                        y1={y} 
                        x2={width - padding.right} 
                        y2={y} 
                        stroke="#1e293b" 
                        strokeDasharray="4 4" 
                      />
                      <text 
                        x={padding.left - 8} 
                        y={y + 4} 
                        fill="#64748b" 
                        fontSize="10" 
                        textAnchor="end" 
                        fontFamily="monospace"
                      >
                        {val} kW
                      </text>
                    </g>
                  );
                })}

                {/* X Axis Timestep Labels */}
                {points.filter((_, i) => i % Math.max(Math.floor(points.length / 8), 1) === 0).map((p, i) => {
                  const idx = points.indexOf(p);
                  const x = getX(idx);
                  return (
                    <g key={i}>
                      <line x1={x} y1={padding.top} x2={x} y2={padding.top + chartH} stroke="#1e293b" strokeDasharray="2 4" />
                      <text 
                        x={x} 
                        y={height - padding.bottom + 18} 
                        fill="#64748b" 
                        fontSize="10" 
                        textAnchor="middle" 
                        fontFamily="monospace"
                      >
                        +{p.horizon_h}h
                      </text>
                    </g>
                  );
                })}

                {/* P10-P90 Conformal Band Polygon */}
                {bandPoints && (
                  <polygon 
                    points={bandPoints} 
                    fill="rgba(6, 182, 212, 0.15)" 
                    stroke="rgba(6, 182, 212, 0.4)" 
                    strokeWidth="1" 
                  />
                )}

                {/* Point Forecast Line */}
                {pointPath && (
                  <path 
                    d={pointPath} 
                    fill="none" 
                    stroke="#f59e0b" 
                    strokeWidth="1.5" 
                    strokeDasharray="3 3" 
                  />
                )}

                {/* P50 Expected Curve */}
                {p50Path && (
                  <path 
                    d={p50Path} 
                    fill="none" 
                    stroke="#06b6d4" 
                    strokeWidth="2.5" 
                  />
                )}

                {/* Hover Interaction Circles */}
                {points.map((p, idx) => (
                  <circle
                    key={idx}
                    cx={getX(idx)}
                    cy={getY(p.p50)}
                    r={hoveredPoint?.horizon_h === p.horizon_h ? 5 : 3}
                    fill={hoveredPoint?.horizon_h === p.horizon_h ? '#22d3ee' : '#0891b2'}
                    className="cursor-pointer transition-all"
                    onMouseEnter={() => setHoveredPoint(p)}
                  />
                ))}
              </svg>
            </div>

            {/* Hover Tooltip / Detail Panel */}
            {hoveredPoint && (
              <div className="p-3 bg-polar-950/90 rounded-lg border border-cyan-500/40 font-mono text-xs flex flex-wrap items-center justify-between gap-4">
                <span className="text-polar-200 font-bold">
                  Timestep: +{hoveredPoint.horizon_h}h ({hoveredPoint.timestamp})
                </span>
                <div className="flex items-center space-x-4">
                  <span className="text-cyan-300">P50 Expected: <strong>{hoveredPoint.p50.toFixed(2)} kW</strong></span>
                  <span className="text-polar-400">P10 Lower: {hoveredPoint.p10.toFixed(2)} kW</span>
                  <span className="text-polar-400">P90 Upper: {hoveredPoint.p90.toFixed(2)} kW</span>
                  {hoveredPoint.p95 && (
                    <span className="text-amber-400">P95 Conservative: {hoveredPoint.p95.toFixed(2)} kW</span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Statistical Metrics Row */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono text-xs">
            <div className="p-3.5 rounded-lg bg-polar-900/60 border border-polar-800">
              <div className="text-polar-400 text-[10px] uppercase">Peak Demand/Yield (P50)</div>
              <div className="text-xl font-bold font-mono-numbers text-polar-50 mt-1">{peakVal.toFixed(1)} kW</div>
            </div>
            <div className="p-3.5 rounded-lg bg-polar-900/60 border border-polar-800">
              <div className="text-polar-400 text-[10px] uppercase">Mean Output (P50)</div>
              <div className="text-xl font-bold font-mono-numbers text-polar-50 mt-1">{avgVal.toFixed(1)} kW</div>
            </div>
            <div className="p-3.5 rounded-lg bg-polar-900/60 border border-polar-800">
              <div className="text-polar-400 text-[10px] uppercase">P10 Minimum Bound</div>
              <div className="text-xl font-bold font-mono-numbers text-polar-50 mt-1">{minVal.toFixed(1)} kW</div>
            </div>
            <div className="p-3.5 rounded-lg bg-polar-900/60 border border-polar-800">
              <div className="text-polar-400 text-[10px] uppercase">Calibration Method</div>
              <div className="text-sm font-semibold text-cyan-300 mt-1 truncate">Split Conformal (P10-P95)</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
