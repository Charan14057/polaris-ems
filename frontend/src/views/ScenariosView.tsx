import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { api } from '../api/endpoints';
import { 
  ScenarioSummary, 
  ScenarioDetail, 
  ScenarioEvaluateResponseData 
} from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { 
  AlertTriangle, 
  Flame, 
  ShieldAlert, 
  CheckCircle2, 
  Play, 
  Info, 
  ChevronRight,
  TrendingDown
} from 'lucide-react';

export const ScenariosView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();

  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('BLIZZARD');
  const [scenarioDetail, setScenarioDetail] = useState<ScenarioDetail | null>(null);
  const [evaluateResult, setEvaluateResult] = useState<ScenarioEvaluateResponseData | null>(null);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load scenarios catalog
  const loadCatalog = useCallback(async () => {
    setLoadingList(true);
    setError(null);
    try {
      const res = await api.listScenarios();
      if (res.data) {
        setScenarios(res.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load scenario catalog');
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  // Load scenario detail when selection changes
  useEffect(() => {
    if (!selectedScenarioId) return;
    api.getScenarioDetail(selectedScenarioId)
      .then(res => {
        if (res.data) setScenarioDetail(res.data);
      })
      .catch(() => {});
  }, [selectedScenarioId]);

  // Run scenario stress test
  const handleEvaluate = async () => {
    if (!selectedScenarioId) return;
    setEvaluating(true);
    setError(null);
    try {
      const res = await api.evaluateScenario({
        station_id: currentStation,
        scenario_id: selectedScenarioId,
        horizon_hours: horizonHours,
        forecast_mode: 'EXPECTED',
      });
      if (res.data) {
        setEvaluateResult(res.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to evaluate stress test');
    } finally {
      setEvaluating(false);
    }
  };

  const categories = ['ALL', 'ENVIRONMENTAL', 'ASSET_FAILURE', 'LOGISTICAL', 'COMPOUND'];
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  const filteredScenarios = selectedCategory === 'ALL'
    ? scenarios
    : scenarios.filter(s => s.category.toUpperCase().includes(selectedCategory));

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-xl bg-polar-900/60 border border-polar-800">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold font-mono text-polar-100 uppercase tracking-wide">
              Polar Stress Scenarios (Phase 5)
            </h2>
            <ProvenanceTag provenance="CONFIGURED" size="xs" />
          </div>
          <p className="text-xs text-polar-400 mt-1">
            Deterministic catalog of 14 locked polar threat scenarios replayed through closed-loop Digital Twin.
          </p>
        </div>

        {/* Category Filters */}
        <div className="flex flex-wrap items-center bg-polar-950 p-1 rounded-lg border border-polar-800 gap-1">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded text-[11px] font-mono transition-all ${
                selectedCategory === cat
                  ? 'bg-polar-800 text-cyan-300 font-semibold'
                  : 'text-polar-400 hover:text-polar-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {loadingList ? (
        <LoadingSkeleton height="h-32" rows={3} />
      ) : error ? (
        <ErrorCard title="Scenario Error" message={error} onRetry={loadCatalog} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: 14 Scenario Catalog Cards */}
          <div className="space-y-3 max-h-[750px] overflow-y-auto pr-1">
            <div className="text-xs font-mono text-polar-400 font-medium px-1">
              Select Scenario ({filteredScenarios.length} Available):
            </div>
            {filteredScenarios.map((scen) => {
              const isSelected = selectedScenarioId === scen.scenario_id;
              return (
                <div
                  key={scen.scenario_id}
                  onClick={() => setSelectedScenarioId(scen.scenario_id)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-polar-800/90 border-cyan-500/50 shadow-md shadow-cyan-950/20'
                      : 'bg-polar-900/50 border-polar-800 hover:border-polar-700'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-mono font-bold text-polar-100">
                      {scen.name}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-polar-950 text-polar-400 border border-polar-800">
                      {scen.category}
                    </span>
                  </div>
                  <p className="text-xs text-polar-300 line-clamp-2 leading-relaxed">
                    {scen.description}
                  </p>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-polar-850 text-[10px] font-mono text-polar-400">
                    <span>Duration: {scen.duration_hours}h</span>
                    <span>{scen.active_effects?.length || 0} Stress Effects</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Column: Scenario Detail & Live Stress Test Runner */}
          <div className="lg:col-span-2 space-y-6">
            {scenarioDetail && (
              <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-polar-800">
                  <div>
                    <h3 className="text-base font-bold font-mono text-polar-50">
                      {scenarioDetail.name}
                    </h3>
                    <p className="text-xs text-polar-400 mt-0.5">
                      {scenarioDetail.description}
                    </p>
                  </div>
                  <button
                    onClick={handleEvaluate}
                    disabled={evaluating}
                    className="inline-flex items-center space-x-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-bold rounded-lg transition-all shadow-md shadow-cyan-950/30 shrink-0"
                  >
                    <Play className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin' : ''}`} />
                    <span>{evaluating ? 'Simulating Replay...' : 'Run Stress Test'}</span>
                  </button>
                </div>

                {/* Explicit Parameter Transforms Table */}
                <div className="space-y-2">
                  <div className="text-xs font-mono text-polar-300 font-semibold uppercase">
                    Parameter Transformations:
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                    {scenarioDetail.transforms?.map((t, idx) => (
                      <div key={idx} className="p-2.5 rounded bg-polar-950/60 border border-polar-800">
                        <div className="flex items-center justify-between text-cyan-300 font-bold">
                          <span>{t.parameter}</span>
                          <span className="text-amber-400">{t.operator} {t.value} {t.unit}</span>
                        </div>
                        <p className="text-[11px] text-polar-400 mt-1 font-sans">
                          {t.rationale}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Stress Test Replay Consequence Metrics */}
            {evaluateResult && (
              <div className="p-5 rounded-xl bg-polar-900/70 border border-polar-750 space-y-4 shadow-xl">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <ShieldAlert className="w-4 h-4 text-orange-400" />
                    <h4 className="text-sm font-bold font-mono text-polar-100 uppercase tracking-wide">
                      Digital Twin Impact Assessment ({evaluateResult.scenario_id})
                    </h4>
                  </div>
                  <ProvenanceTag provenance={evaluateResult.provenance} size="xs" />
                </div>

                {/* Consequence Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                  <div className="p-3 rounded-lg bg-polar-950 border border-polar-800">
                    <span className="text-polar-400 text-[10px] uppercase">Unserved Energy</span>
                    <div className="text-lg font-bold font-mono-numbers text-polar-50 mt-1">
                      {evaluateResult.impact_metrics.delta_unserved_energy_kwh.toFixed(1)} kWh
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-polar-950 border border-polar-800">
                    <span className="text-polar-400 text-[10px] uppercase">Critical Deficit</span>
                    <div className="text-lg font-bold font-mono-numbers text-polar-50 mt-1">
                      {evaluateResult.impact_metrics.delta_critical_unserved_kwh.toFixed(1)} kWh
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-polar-950 border border-polar-800">
                    <span className="text-polar-400 text-[10px] uppercase">Fuel Burn Delta</span>
                    <div className="text-lg font-bold font-mono-numbers text-polar-50 mt-1">
                      {evaluateResult.impact_metrics.delta_diesel_fuel_liters > 0 ? '+' : ''}
                      {evaluateResult.impact_metrics.delta_diesel_fuel_liters.toFixed(1)} L
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-polar-950 border border-polar-800">
                    <span className="text-polar-400 text-[10px] uppercase">Indoor Temp Delta</span>
                    <div className="text-lg font-bold font-mono-numbers text-polar-50 mt-1">
                      {evaluateResult.impact_metrics.delta_min_indoor_temp_c.toFixed(1)} °C
                    </div>
                  </div>
                </div>

                {/* Failure Signatures & Violated Constraints */}
                <div className="p-3.5 rounded-lg bg-polar-950/80 border border-polar-800 space-y-2 text-xs font-mono">
                  <div className="flex items-center justify-between">
                    <span className="text-polar-400">Primary Failure Signature:</span>
                    <span className="text-orange-400 font-bold uppercase">
                      {evaluateResult.impact_metrics.primary_failure_mode || 'NONE (Station Absorbs Stress)'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-polar-400">Earliest Breach Hour:</span>
                    <span className="text-polar-200">
                      {evaluateResult.impact_metrics.earliest_failure_hour != null 
                        ? `Hour +${evaluateResult.impact_metrics.earliest_failure_hour}` 
                        : 'No Failure Triggered'}
                    </span>
                  </div>
                  {evaluateResult.violated_constraints?.length > 0 && (
                    <div className="pt-2 border-t border-polar-800">
                      <span className="text-red-400 font-bold">Violated Physical Constraints:</span>
                      <ul className="list-disc list-inside mt-1 text-polar-300 text-[11px] space-y-0.5">
                        {evaluateResult.violated_constraints.map((c, i) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
