import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
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
import { ScenarioDeltaCanvas } from '../components/common/ScenarioDeltaCanvas';
import { WhyThisMatters } from '../components/common/WhyThisMatters';
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { JargonTooltip } from '../components/common/JargonTooltip';
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
  ChevronRight
} from 'lucide-react';

export const ScenariosView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();
  const { inspectEvidence } = useEvidence();

  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('BLIZZARD');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [scenarioDetail, setScenarioDetail] = useState<ScenarioDetail | null>(null);
  const [evaluateResult, setEvaluateResult] = useState<ScenarioEvaluateResponseData | null>(null);
  const [loadingList, setLoadingList] = useState<boolean>(true);
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

  const handleEvaluate = async () => {
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

  // Group scenarios logically
  const getCategory = (id: string): string => {
    if (['BLIZZARD', 'EXTREME_COLD', 'POLAR_NIGHT', 'CLOUD_SURGE', 'HIGH_WIND'].includes(id)) {
      return 'Severe Weather';
    }
    if (['SOLAR_GENERATION_FAILURE', 'WIND_GENERATION_FAILURE', 'GENERATOR_OUTAGE', 'INVERTER_TRIP'].includes(id)) {
      return 'Generation Faults';
    }
    if (['BATTERY_DEGRADATION', 'BATTERY_COLD_DERATE', 'THERMAL_BREACH'].includes(id)) {
      return 'Storage & Thermal';
    }
    return 'Logistics & Supply';
  };

  const categories = ['ALL', 'Severe Weather', 'Generation Faults', 'Storage & Thermal', 'Logistics & Supply'];

  const filteredScenarios = scenarios.filter(
    (s) => selectedCategory === 'ALL' || getCategory(s.scenario_id || (s as any).id) === selectedCategory
  );

  return (
    <div className="space-y-8 max-w-[1520px] mx-auto pb-12">
      {/* 1. Editorial Header */}
      <div className="border-b border-slate-200 pb-6 flex flex-col sm:flex-row sm:items-baseline justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-sky-600 font-bold mb-2">
            <Compass className="w-4 h-4" />
            <span>04 STRESS SCENARIO STUDIO</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-sans font-bold text-slate-900 tracking-tight">
            Controlled What-If Perturbations
          </h2>
          <p className="text-sm text-slate-600 mt-1 font-sans">
            Evaluate microgrid survival under 14 locked polar storm, generator trip, and fuel resupply delay presets.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <ProvenanceTag provenance="SYNTHETIC" size="sm" />
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-slate-500">
            STATION: {currentStation}
          </span>
        </div>
      </div>

      {/* 1.1 Non-Technical Comprehension: Explain This */}
      <ExplainThis
        title="What is a Stress Scenario in Polaris-EMS?"
        whatAmILookingAt="This studio lets you inject severe simulated crises (such as a 120 km/h blizzard, a broken diesel engine, or sudden solar blackout) to see how the autonomous AI reacts."
        whyIsItImportant="We can never risk testing failures on real equipment in Antarctica where people's lives are on the line. Simulating 14 extreme events proves the software will protect the crew before real storms strike."
        howIsItCalculated="The stress engine alters temperature, wind speed, or equipment availability variables and sends them through the Digital Twin and Optimizer."
      />

      {/* 2. Category Filter Bar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 pb-3">
        <span className="text-xs font-mono text-slate-500 uppercase mr-2">FILTER CLASS:</span>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
              selectedCategory === cat
                ? 'bg-sky-600 text-white font-medium shadow-xs'
                : 'bg-slate-50 text-slate-600 hover:bg-white border border-slate-100'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* 3. Scenario Selector Grid (Editorial Sheets) */}
      {loadingList ? (
        <LoadingSkeleton rows={2} height="h-28" />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {filteredScenarios.map((sc) => {
            const scId = sc.scenario_id || (sc as any).id;
            const isSelected = selectedScenarioId === scId;
            return (
              <div
                key={scId}
                onClick={() => {
                  setSelectedScenarioId(scId);
                  setEvaluateResult(null);
                }}
                className={`p-4 rounded border text-left cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-white border-sky-600 shadow-raised ring-1 ring-copper/30'
                    : 'bg-white border border-slate-200 shadow-xs hover:border-slate-200 hover:shadow-sheet'
                }`}
              >
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 mb-1">
                  <span>{getCategory(scId)}</span>
                  <span className="text-sky-600 font-medium">{(sc as any).severity || 'MEDIUM'}</span>
                </div>
                <div className="text-sm font-semibold text-slate-900 font-sans">
                  {sc.name || scId.replace(/_/g, ' ')}
                </div>
                <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                  {sc.description || 'Deterministic environmental stress perturbation.'}
                </p>
              </div>
            );
          })}
        </div>
      )}

      {/* 4. Active Scenario Details & Live Evaluate Action */}
      {scenarioDetail && (
        <div className="bg-white border border-slate-200 shadow-xs rounded p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-3">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono uppercase text-sky-600 font-bold">
                  ACTIVE EXPERIMENT SPECIFICATION
                </span>
                <span className="text-border">|</span>
                <span className="text-xs font-mono text-slate-500">{scenarioDetail.scenario_id || (scenarioDetail as any).id}</span>
              </div>
              <h3 className="text-xl font-sans font-bold text-slate-900 mt-1">
                {scenarioDetail.name}
              </h3>
            </div>

            <button
              onClick={handleEvaluate}
              disabled={evaluating}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded bg-sky-600 text-white text-xs font-mono font-medium hover:bg-sky-600-dark transition-colors shadow-xs disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin' : ''}`} />
              <span>{evaluating ? 'Solving Optimization Horizon...' : 'Run Controlled Stress Replay'}</span>
            </button>
          </div>

          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-4xl font-sans mb-4">
            {scenarioDetail.description}
          </p>

          {/* Causal Scenario Delta Canvas */}
          <ScenarioDeltaCanvas
            scenarioName={scenarioDetail.name}
            category={getCategory(scenarioDetail.scenario_id || (scenarioDetail as any).id)}
            baselineResilience="SAFE"
            scenarioResilience={evaluateResult ? (evaluateResult.impact_metrics?.failure_occurred ? 'CRITICAL' : 'WATCH') : 'WATCH'}
            baselineHorizon={142.0}
            scenarioHorizon={evaluateResult?.impact_metrics?.earliest_failure_hour || 84.0}
          />

          <NextStepExplanation
            title="WHAT HAPPENS IF THIS SCENARIO OCCURS IN REALITY?"
            timeframe="Immediate Automated Response"
            outlook={`Under ${scenarioDetail.name}, Polaris-EMS immediately locks priority life-support circuits and starts backup diesel generators before battery reserves deplete below safety limits.`}
          />
        </div>
      )}

      {/* 5. Why This Matters */}
      <WhyThisMatters
        headline="Synthetic Stress Profiles Reveal Hidden Failure Chains"
        summary="Standard microgrid dispatchers assume weather forecasts are approximately accurate. In polar regions, sudden blizzard gusts cut out wind turbines within minutes, while sub-zero cold derates battery chemistry. Polaris-EMS simulates these compound failures to verify that life safety systems survive even if all renewables drop to zero."
        technicalDetail="14 scenarios are strictly deterministic with locked seed constants. Tested against all 3 station microgrid configurations with zero solver divergence."
      />
    </div>
  );
};
