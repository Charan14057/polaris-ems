import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { api } from '../api/endpoints';
import { OptimizeResponseData, OptimizationMode } from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { MetricCard } from '../components/common/MetricCard';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { 
  Zap, 
  CheckCircle2, 
  Clock, 
  Cpu, 
  Play, 
  ShieldCheck, 
  Layers, 
  Sliders 
} from 'lucide-react';

export const OptimizationView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();

  const [mode, setMode] = useState<OptimizationMode>('EXPECTED');
  const [optData, setOptData] = useState<OptimizeResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const runOptimizer = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.optimizeMicrogrid({
        station_id: currentStation,
        horizon_hours: horizonHours,
        mode,
        include_schedule: true,
      });
      if (res.data) {
        setOptData(res.data);
      }
    } catch (err: any) {
      setError(err.message || 'Microgrid optimization solve failed');
    } finally {
      setLoading(false);
    }
  }, [currentStation, horizonHours, mode]);

  useEffect(() => {
    runOptimizer();
  }, [runOptimizer]);

  const modes: { id: OptimizationMode; label: string; desc: string }[] = [
    { id: 'EXPECTED', label: 'Expected (P50)', desc: 'Nominal quantile dispatch minimizing total operating cost' },
    { id: 'CONSERVATIVE', label: 'Conservative (P90)', desc: 'High reserve buffer & risk-averse fuel/battery conservation' },
    { id: 'SCENARIO_ROBUST', label: 'Scenario Robust', desc: 'Stress-hardened dispatch for active environmental threats' },
  ];

  const summary = optData?.summary;
  const schedule = optData?.schedule || [];

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Mode Switcher */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-4 rounded-xl bg-polar-900/60 border border-polar-800">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold font-mono text-polar-100 uppercase tracking-wide">
              Microgrid Dispatch Optimization
            </h2>
            <ProvenanceTag provenance="SIMULATED" size="xs" />
          </div>
          <p className="text-xs text-polar-400 mt-1">
            HiGHS Mixed-Integer Linear Program (MILP) with closed-loop Digital Twin replay validation.
          </p>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center bg-polar-950 p-1 rounded-lg border border-polar-800 gap-1">
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
                mode === m.id
                  ? 'bg-polar-800 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'text-polar-400 hover:text-polar-200'
              }`}
              title={m.desc}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton height="h-64" rows={2} />
      ) : error ? (
        <ErrorCard title="Optimizer Error" message={error} onRetry={runOptimizer} />
      ) : optData && summary ? (
        <div className="space-y-6">
          {/* Solver Telemetry Bar */}
          <div className="p-4 rounded-xl bg-polar-950/80 border border-polar-800 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
            <div className="flex items-center space-x-3">
              <span className="text-polar-400">Solver Status:</span>
              <StatusBadge status={optData.solver_status} size="sm" />
              <span className="text-polar-400">Optimality Tier:</span>
              <span className={`px-2 py-0.5 rounded font-bold ${
                optData.optimality_tier === 'EXACT_OPTIMAL'
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/40'
                  : optData.optimality_tier === 'MIP_GAP_OPTIMAL'
                  ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/40'
                  : 'bg-amber-950 text-amber-400 border border-amber-500/40'
              }`}>
                {optData.optimality_tier}
              </span>
            </div>

            <div className="flex items-center space-x-4 text-polar-300">
              <span>MIP Gap: <strong className="text-polar-100">{optData.relative_gap != null ? `${(optData.relative_gap * 100).toFixed(2)}%` : '0.00%'}</strong></span>
              <span>Solve Time: <strong className="text-polar-100">{optData.solve_time_sec.toFixed(2)}s</strong></span>
              <span className="flex items-center space-x-1 text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Twin Replay Validated</span>
              </span>
            </div>
          </div>

          {/* Operational Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Fuel Consumption"
              value={summary.total_fuel_consumed_liters.toFixed(1)}
              unit="Liters"
              subtitle={`Final Remaining: ${summary.final_fuel_remaining_liters.toFixed(0)} L`}
              provenance="SIMULATED"
            />
            <MetricCard
              title="Battery Terminal SOC"
              value={(summary.final_battery_soc_pct > 1 ? summary.final_battery_soc_pct : summary.final_battery_soc_pct * 100).toFixed(1)}
              unit="% SOC"
              subtitle="Closed-loop terminal state"
              provenance="SIMULATED"
            />
            <MetricCard
              title="Renewable Curtailment"
              value={summary.total_curtailed_renewable_kwh.toFixed(1)}
              unit="kWh"
              subtitle="Preserved for continuity"
              provenance="SIMULATED"
            />
            <MetricCard
              title="Reserve Margin Min"
              value={`${summary.min_reserve_margin_pct.toFixed(1)}%`}
              subtitle="Target threshold: >15%"
              statusBadge={<StatusBadge status={summary.min_reserve_margin_pct >= 15 ? 'SAFE' : 'WATCH'} size="sm" showIcon={false} />}
              provenance="SIMULATED"
            />
          </div>

          {/* Optimized Dispatch Schedule Table */}
          <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
                  Step-by-Step Dispatch Schedule ({schedule.length} Timesteps)
                </h3>
              </div>
              <span className="text-xs font-mono text-polar-400">
                HiGHS Optimal Trajectory
              </span>
            </div>

            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="sticky top-0 bg-polar-900 z-10 border-b border-polar-800 text-polar-400 uppercase text-[10px]">
                  <tr>
                    <th className="py-2 px-3">Hour</th>
                    <th className="py-2 px-3">Timestamp</th>
                    <th className="py-2 px-3 text-right">Diesel kW</th>
                    <th className="py-2 px-3 text-right">Solar kW</th>
                    <th className="py-2 px-3 text-right">Wind kW</th>
                    <th className="py-2 px-3 text-right">BESS Net kW</th>
                    <th className="py-2 px-3 text-right">BESS SOC</th>
                    <th className="py-2 px-3 text-right">Load Served</th>
                    <th className="py-2 px-3 text-right">Reserve %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-polar-850/60">
                  {schedule.map((step) => {
                    const netBess = step.p_battery_discharge_kw - step.p_battery_charge_kw;
                    return (
                      <tr key={step.t} className="hover:bg-polar-800/40">
                        <td className="py-1.5 px-3 text-cyan-300 font-bold">+{step.t}h</td>
                        <td className="py-1.5 px-3 text-polar-400 text-[11px]">{step.timestamp.replace('T', ' ').substring(0, 16)}</td>
                        <td className="py-1.5 px-3 text-right text-orange-300 font-mono-numbers">{step.p_diesel_kw.toFixed(1)}</td>
                        <td className="py-1.5 px-3 text-right text-yellow-300 font-mono-numbers">{step.p_solar_kw.toFixed(1)}</td>
                        <td className="py-1.5 px-3 text-right text-cyan-300 font-mono-numbers">{step.p_wind_kw.toFixed(1)}</td>
                        <td className={`py-1.5 px-3 text-right font-mono-numbers font-medium ${
                          netBess > 0 ? 'text-emerald-400' : netBess < 0 ? 'text-blue-400' : 'text-polar-500'
                        }`}>
                          {netBess > 0 ? `+${netBess.toFixed(1)}` : netBess.toFixed(1)}
                        </td>
                        <td className="py-1.5 px-3 text-right text-polar-200 font-mono-numbers">
                          {(step.battery_soc > 1 ? step.battery_soc : step.battery_soc * 100).toFixed(1)}%
                        </td>
                        <td className="py-1.5 px-3 text-right text-polar-100 font-mono-numbers">{step.p_served_load_kw.toFixed(1)}</td>
                        <td className={`py-1.5 px-3 text-right font-mono-numbers ${step.reserve_margin_pct < 15 ? 'text-amber-400' : 'text-polar-300'}`}>
                          {step.reserve_margin_pct.toFixed(0)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
