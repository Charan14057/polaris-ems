import React, { useState, useEffect, useCallback } from 'react';
import { useStation, useOperationalSnapshot } from '../context/StationContext';
import { useEvidence } from '../context/EvidenceContext';
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
  Compass, 
  Play, 
  Wind, 
  Flame, 
  ShieldAlert, 
  BatteryCharging, 
  AlertTriangle,
  Info,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Sun,
  RotateCcw,
  Zap,
  Activity,
  Layers,
  Thermometer
} from 'lucide-react';

export const ScenariosView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();
  const { snapshot, activeScenario, activateScenario, clearScenario } = useOperationalSnapshot();
  const { inspectEvidence } = useEvidence();

  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('BLIZZARD');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [scenarioDetail, setScenarioDetail] = useState<ScenarioDetail | null>(null);
  const [evaluateResult, setEvaluateResult] = useState<ScenarioEvaluateResponseData | null>(null);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [isActivating, setIsActivating] = useState<boolean>(false);
  const [isClearing, setIsClearing] = useState<boolean>(false);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    if (!selectedScenarioId) return;
    api.getScenarioDetail(selectedScenarioId)
      .then(res => {
        if (res.data) setScenarioDetail(res.data);
      })
      .catch(() => {});
  }, [selectedScenarioId]);

  // Evaluate scenario for simulation trajectory deltas preview
  const handleEvaluatePreview = async () => {
    if (!selectedScenarioId) return;
    setEvaluating(true);
    try {
      const res = await api.evaluateScenario({
        station_id: currentStation,
        scenario_id: selectedScenarioId,
        horizon_hours: horizonHours,
      });
      if (res.data) {
        setEvaluateResult(res.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute scenario evaluation');
    } finally {
      setEvaluating(false);
    }
  };

  // ACTIVATE SCENARIO AUTHORITATIVELY: Propagates through backend live session & system state
  const handleActivateSystemScenario = async () => {
    if (!selectedScenarioId) return;
    setIsActivating(true);
    setError(null);
    try {
      await activateScenario(selectedScenarioId);
      await handleEvaluatePreview();
    } catch (err: any) {
      setError(err.message || 'Failed to activate scenario in system');
    } finally {
      setIsActivating(false);
    }
  };

  // CLEAR SCENARIO & RESTORE BASELINE
  const handleClearSystemScenario = async () => {
    setIsClearing(true);
    setError(null);
    try {
      await clearScenario();
      setEvaluateResult(null);
    } catch (err: any) {
      setError(err.message || 'Failed to restore baseline');
    } finally {
      setIsClearing(false);
    }
  };

  const getCategory = (id: string): string => {
    if (['BLIZZARD', 'EXTREME_COLD', 'POLAR_NIGHT', 'CLOUD_SURGE', 'HIGH_WIND', 'UNFORESEEN_WEATHER'].includes(id)) {
      return 'Severe Weather';
    }
    if (['SOLAR_GENERATION_FAILURE', 'WIND_GENERATION_FAILURE', 'GENERATOR_OUTAGE', 'INVERTER_TRIP'].includes(id)) {
      return 'Generation Faults';
    }
    if (['BATTERY_DEGRADATION', 'BATTERY_COLD_DERATE', 'THERMAL_BREACH'].includes(id)) {
      return 'Storage & Thermal';
    }
    if (['FUEL_RESUPPLY_DELAY', 'COMBINED_POLAR_STRESS'].includes(id)) {
      return 'Logistics & Compound';
    }
    return 'Exploration & Custom';
  };

  const categories = ['ALL', 'Severe Weather', 'Generation Faults', 'Storage & Thermal', 'Logistics & Compound', 'Exploration & Custom'];

  const filteredScenarios = scenarios.filter(
    (s) => selectedCategory === 'ALL' || getCategory(s.scenario_id || (s as any).id) === selectedCategory
  );

  const isCurrentlyActive = activeScenario === selectedScenarioId;

  // Dynamic explanation mapping per scenario
  const getDynamicExplanations = (scenId: string) => {
    switch (scenId) {
      case 'BLIZZARD':
        return {
          whatChanges: 'Ambient temperature drops by -10°C, wind speeds double (2.0x) pushing toward 25 m/s storm cut-out, and blowing snow causes zero solar irradiance.',
          whyItMatters: 'Tests coupled aerodynamic cut-out risks and massive heating demand surge while renewables are unavailable.',
          expectedEffect: 'Solar drops to 0 kW, wind turbine may cut out under gale gusts, battery discharges rapidly to support building heating, and primary diesel generator DG-1 must ramp up.',
          currentEffect: activeScenario === 'BLIZZARD' 
            ? `Active in station: Total load at ${snapshot.totalLoadKw?.toFixed(1) || '—'} kW, diesel dispatched at ${snapshot.dieselGenerationKw?.toFixed(1) || '—'} kW, threat state: ${snapshot.resilienceState}.`
            : 'Inactive (Previewing theoretical response).',
          recoveryResult: 'When cleared, ambient conditions return to seasonal forecast, wind normalizes, and spinning reserves return to baseline equilibrium.'
        };
      case 'UNFORESEEN_WEATHER':
        return {
          whatChanges: 'Abrupt katabatic cold front: -12°C plunge, wind squalls increase by 1.8x, cloud cover surges to 85%, and solar irradiance drops by 60%.',
          whyItMatters: 'Tests rapid unpredicted dispatch adaptation when weather deviates abruptly from nominal forecast trajectory.',
          expectedEffect: 'Renewable deficit offset by automatic BESS discharge or generator startup; heating load ramps up dynamically.',
          currentEffect: activeScenario === 'UNFORESEEN_WEATHER'
            ? `Active in station: Ambient temp ${snapshot.ambientTemperatureC?.toFixed(1) || '—'}°C, wind ${snapshot.windSpeedMs?.toFixed(1) || '—'} m/s, resilience state: ${snapshot.resilienceState}.`
            : 'Inactive (Previewing theoretical response).',
          recoveryResult: 'When cleared, baseline meteorological trajectory is restored with zero compounding model drift.'
        };
      case 'EXTREME_COLD':
        return {
          whatChanges: 'Mid-winter polar vortex causes -20°C ambient temperature depression down to -35°C to -45°C.',
          whyItMatters: 'Evaluates building thermal envelope insulation, hydronic loop heat loss, and battery cold temperature derating.',
          expectedEffect: 'Thermal demand surges by 40%, battery usable capacity decreases, diesel fuel heat tracing becomes critical.',
          currentEffect: activeScenario === 'EXTREME_COLD'
            ? `Active in station: Ambient temp ${snapshot.ambientTemperatureC?.toFixed(1) || '—'}°C, critical load ${snapshot.criticalLoadKw?.toFixed(1) || '—'} kW.`
            : 'Inactive (Previewing theoretical response).',
          recoveryResult: 'When cleared, temperature returns to nominal winter baseline.'
        };
      case 'SOLAR_GENERATION_FAILURE':
        return {
          whatChanges: 'Main solar PV inverter breaker trips, immediately reducing solar generation availability to 0.0.',
          whyItMatters: 'Tests instantaneous microgrid inertial stability and reserve transfer during sunny peak daytime hours.',
          expectedEffect: 'Instantaneous power deficit transferred to BESS discharge; if battery SOC low, DG-1 automatically starts.',
          currentEffect: activeScenario === 'SOLAR_GENERATION_FAILURE'
            ? `Active in station: Solar generation forced to 0.0 kW; BESS power: ${snapshot.bessPowerKw?.toFixed(1) || '—'} kW.`
            : 'Inactive (Previewing theoretical response).',
          recoveryResult: 'When cleared, solar inverter breaker resets and generation ramps back to available solar irradiance.'
        };
      case 'WIND_GENERATION_FAILURE':
        return {
          whatChanges: 'Wind turbine pitch actuator jam or mechanical gearbox fault forces emergency mechanical shutdown (0.0 kW).',
          whyItMatters: 'Tests station autonomy during prolonged periods without wind generation.',
          expectedEffect: 'Wind power ceases; diesel genset and battery storage take over base load.',
          currentEffect: activeScenario === 'WIND_GENERATION_FAILURE'
            ? `Active in station: Wind power is 0.0 kW; diesel output: ${snapshot.dieselGenerationKw?.toFixed(1) || '—'} kW.`
            : 'Inactive (Previewing theoretical response).',
          recoveryResult: 'When cleared, wind turbine pitch actuators release and generation resumes.'
        };
      case 'BATTERY_DEGRADATION':
        return {
          whatChanges: 'Electrochemical degradation reduces usable battery storage capacity to 65% of rated nameplate.',
          whyItMatters: 'Validates optimizer dispatch when storage buffer is constrained by sub-zero cycling wear.',
          expectedEffect: 'Reduced overnight storage autonomy; requires higher diesel commitment to avoid battery over-discharge.',
          currentEffect: activeScenario === 'BATTERY_DEGRADATION'
            ? `Active in station: Battery capacity constrained; current SOC: ${snapshot.bessSocPct || '—'}%.`
            : 'Inactive (Previewing theoretical response).',
          recoveryResult: 'When cleared, battery rated capacity restores to nominal 100% specification.'
        };
      case 'FUEL_RESUPPLY_DELAY':
        return {
          whatChanges: 'Sea ice congestion or weather blocks resupply vessel/convoy for +168 hours (7 days).',
          whyItMatters: 'Verifies strict fuel stock survival horizon enforcement in the Phase 6 MILP optimizer.',
          expectedEffect: 'Optimizer enforces conservative fuel conservation mode, maximizing renewable capture and shedding non-critical loads.',
          currentEffect: activeScenario === 'FUEL_RESUPPLY_DELAY'
            ? `Active in station: Fuel remaining ${snapshot.fuelRemainingL?.toLocaleString() || '—'} L; survival horizon: ${snapshot.survivalHorizons?.criticalLoadSurvivalH || '—'} h.`
            : 'Inactive (Previewing theoretical response).',
          recoveryResult: 'When cleared, standard resupply delivery window is restored.'
        };
      case 'COMBINED_POLAR_STRESS':
        return {
          whatChanges: 'Multi-vector disaster: -15°C cold front, 30 m/s blizzard winds with turbine cut-out, solar outage, and 7-day resupply delay.',
          whyItMatters: 'Worst-case black-sky survivability benchmark testing priority life-support isolation.',
          expectedEffect: 'All renewables offline; station runs in emergency diesel + battery survival mode; P3 flexible loads shed.',
          currentEffect: activeScenario === 'COMBINED_POLAR_STRESS'
            ? `Active in station: Emergency mode active, threat state: ${snapshot.resilienceState}.`
            : 'Inactive (Previewing theoretical response).',
          recoveryResult: 'When cleared, all multi-vector perturbations cease and station returns to standard baseline.'
        };
      default:
        return {
          whatChanges: scenarioDetail?.description || 'Standard polar environmental or asset disturbance profile.',
          whyItMatters: scenarioDetail?.rationale || 'Controlled testing of microgrid operational limits and autonomous governance.',
          expectedEffect: 'Dynamic rebalancing of generation assets and storage reserves to maintain zero unserved critical load.',
          currentEffect: isCurrentlyActive
            ? `Active in station: Resilience state is ${snapshot.resilienceState}, demand is ${snapshot.totalLoadKw?.toFixed(1) || '—'} kW.`
            : 'Inactive (Previewing theoretical response).',
          recoveryResult: 'When cleared, station physical state resets to baseline nominal trajectory.'
        };
    }
  };

  const dynamicInfo = getDynamicExplanations(selectedScenarioId);

  return (
    <div className="space-y-8 max-w-[1520px] mx-auto pb-12 font-sans">
      
      {/* 1. Header & Active System Status Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-amber-400 font-bold mb-1">
            <Compass className="w-4 h-4" />
            <span>04 STRESS SCENARIO STUDIO • 15 CANONICAL PRESETS</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            System-Wide Operational Perturbations
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Inject verified stress conditions into the authoritative station state. Changes immediately propagate across the Digital Twin, Forecasts, Resilience Engine, and Optimization.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-800 border border-slate-700 rounded-lg px-3.5 py-2 text-right">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest block">Active System State</span>
            <span className="text-xs font-mono font-bold text-amber-400">
              {activeScenario || 'NORMAL_BASELINE (CLEAN)'}
            </span>
          </div>

          {activeScenario && (
            <button
              onClick={handleClearSystemScenario}
              disabled={isClearing}
              className="px-3.5 py-2 rounded-lg bg-red-600/80 hover:bg-red-600 text-white text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
              title="Clear Active Scenario and Restore Clean Baseline"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${isClearing ? 'animate-spin' : ''}`} />
              <span>Restore Baseline</span>
            </button>
          )}
        </div>
      </div>

      {error && <ErrorCard title="Scenario Operation Error" message={error} onRetry={loadCatalog} />}

      {/* 2. Category Filter & Scenario Grid */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-mono">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg border transition-colors whitespace-nowrap ${
                selectedCategory === cat
                  ? 'bg-amber-500 text-slate-950 font-bold border-amber-600 shadow-sm'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {loadingList ? (
          <LoadingSkeleton rows={3} height="h-28" />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
            {filteredScenarios.map((scen) => {
              const sid = scen.scenario_id || (scen as any).id;
              const isSelected = selectedScenarioId === sid;
              const isActive = activeScenario === sid;

              return (
                <button
                  key={sid}
                  onClick={() => setSelectedScenarioId(sid)}
                  className={`p-3.5 rounded-xl border text-left transition-all relative overflow-hidden flex flex-col justify-between ${
                    isSelected
                      ? 'bg-white border-amber-500 ring-2 ring-amber-500/20 shadow-md'
                      : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-xs'
                  }`}
                >
                  {isActive && (
                    <span className="absolute top-2 right-2 flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                    </span>
                  )}

                  <div>
                    <span className="text-[10px] font-mono text-slate-400 block mb-1 uppercase">
                      {scen.category || 'POLAR'}
                    </span>
                    <h3 className="text-xs font-bold text-slate-900 font-sans line-clamp-1">
                      {scen.name}
                    </h3>
                    <p className="text-[11px] text-slate-500 font-sans mt-1 line-clamp-2 leading-relaxed">
                      {scen.description}
                    </p>
                  </div>

                  <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono">
                    <span className="text-slate-400">{scen.duration_hours || 48}h Horizon</span>
                    {isActive ? (
                      <span className="text-amber-600 font-bold">ACTIVE SYSTEM</span>
                    ) : (
                      <span className={isSelected ? 'text-amber-600 font-semibold' : 'text-slate-400'}>
                        {isSelected ? 'Selected' : 'View'}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* 3. Detail & Control Station */}
      {selectedScenarioId && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-6">
          
          {/* Action Row */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 uppercase">
                  {scenarioDetail?.category || 'ENVIRONMENTAL'}
                </span>
                <span className="text-xs font-mono text-slate-400">ID: {selectedScenarioId}</span>
                {isCurrentlyActive && (
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
                    CURRENTLY ACTIVE IN SYSTEM
                  </span>
                )}
              </div>
              <h2 className="text-xl font-bold text-slate-900 mt-1">
                {scenarioDetail?.name || selectedScenarioId}
              </h2>
            </div>

            <div className="flex items-center gap-2.5">
              {isCurrentlyActive ? (
                <button
                  onClick={handleClearSystemScenario}
                  disabled={isClearing}
                  className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
                >
                  <RotateCcw className={`w-3.5 h-3.5 ${isClearing ? 'animate-spin' : ''}`} />
                  <span>Clear Scenario (Restore Baseline)</span>
                </button>
              ) : (
                <button
                  onClick={handleActivateSystemScenario}
                  disabled={isActivating}
                  className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-mono font-bold flex items-center gap-1.5 transition-colors shadow-xs"
                >
                  <Play className={`w-3.5 h-3.5 fill-current ${isActivating ? 'animate-spin' : ''}`} />
                  <span>Activate Scenario in System</span>
                </button>
              )}

              <button
                onClick={handleEvaluatePreview}
                disabled={evaluating}
                className="px-3.5 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-mono font-medium transition-colors"
              >
                {evaluating ? 'Simulating...' : 'Simulate Trajectory'}
              </button>
            </div>
          </div>

          {/* DYNAMIC 5-STAGE EXPLANATION MATRIX */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3.5 text-xs">
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] font-mono uppercase tracking-wider text-amber-700 font-bold block mb-1">
                01 WHAT CHANGES
              </span>
              <p className="text-slate-700 font-sans leading-relaxed">{dynamicInfo.whatChanges}</p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] font-mono uppercase tracking-wider text-sky-700 font-bold block mb-1">
                02 WHY IT MATTERS
              </span>
              <p className="text-slate-700 font-sans leading-relaxed">{dynamicInfo.whyItMatters}</p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] font-mono uppercase tracking-wider text-teal-700 font-bold block mb-1">
                03 EXPECTED SYSTEM EFFECT
              </span>
              <p className="text-slate-700 font-sans leading-relaxed">{dynamicInfo.expectedEffect}</p>
            </div>

            <div className={`p-3.5 rounded-lg border ${
              isCurrentlyActive ? 'bg-amber-50/70 border-amber-300 text-amber-950' : 'bg-slate-50 border-slate-200 text-slate-700'
            }`}>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-800 font-bold block mb-1">
                04 CURRENT SYSTEM EFFECT
              </span>
              <p className="font-sans leading-relaxed">{dynamicInfo.currentEffect}</p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-700 font-bold block mb-1">
                05 RECOVERY / CLEAR RESULT
              </span>
              <p className="text-slate-700 font-sans leading-relaxed">{dynamicInfo.recoveryResult}</p>
            </div>
          </div>

          {/* Parameter Transforms Ledger */}
          {scenarioDetail?.transforms && scenarioDetail.transforms.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                Deterministic Parameter Transformations
              </span>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-400 text-[10px] uppercase">
                      <th className="py-2 px-3">Parameter</th>
                      <th className="py-2 px-3">Operator</th>
                      <th className="py-2 px-3">Value</th>
                      <th className="py-2 px-3">Unit</th>
                      <th className="py-2 px-3">Engineering Rationale</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scenarioDetail.transforms.map((t, i) => (
                      <tr key={i} className="border-b border-slate-100 text-slate-700 hover:bg-slate-50/50">
                        <td className="py-2 px-3 font-semibold text-slate-900">{t.parameter}</td>
                        <td className="py-2 px-3 text-sky-700">{t.operator}</td>
                        <td className="py-2 px-3 font-bold">{t.value}</td>
                        <td className="py-2 px-3 text-slate-500">{t.unit}</td>
                        <td className="py-2 px-3 text-slate-600 font-sans text-[11px]">{t.rationale}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Forward Evaluation Trajectory Deltas (if computed) */}
          {evaluateResult && (
            <div className="space-y-3 pt-3 border-t border-slate-100">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
                  Forward Trajectory Impact Deltas ({evaluateResult.duration_hours || 48}h Horizon)
                </span>
                <span className="text-xs font-mono font-bold text-slate-700">
                  Failure Status: {evaluateResult.impact_metrics?.failure_occurred ? 'FAILURE OCCURRED' : 'SURVIVED'}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 text-[10px] block uppercase">Critical Unserved</span>
                  <span className="text-sm font-bold text-red-600">
                    {evaluateResult.impact_metrics?.delta_critical_unserved_kwh !== undefined 
                      ? `${evaluateResult.impact_metrics.delta_critical_unserved_kwh.toFixed(1)} kWh` 
                      : '0.0 kWh'}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 text-[10px] block uppercase">Diesel Fuel Delta</span>
                  <span className="text-sm font-bold text-slate-800">
                    {evaluateResult.impact_metrics?.delta_diesel_fuel_liters !== undefined 
                      ? `${evaluateResult.impact_metrics.delta_diesel_fuel_liters.toFixed(1)} L` 
                      : '0.0 L'}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 text-[10px] block uppercase">Min Temp Delta</span>
                  <span className="text-sm font-bold text-sky-600">
                    {evaluateResult.impact_metrics?.delta_min_indoor_temp_c !== undefined 
                      ? `${evaluateResult.impact_metrics.delta_min_indoor_temp_c.toFixed(1)}°C` 
                      : '0.0°C'}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 text-[10px] block uppercase">Battery Min SOC Delta</span>
                  <span className="text-sm font-bold text-emerald-600">
                    {evaluateResult.impact_metrics?.delta_min_battery_soc !== undefined 
                      ? `${(evaluateResult.impact_metrics.delta_min_battery_soc * 100).toFixed(1)}%` 
                      : '0.0%'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
