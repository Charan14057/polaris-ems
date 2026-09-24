import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { api } from '../api/endpoints';
import { PipelineAnalyzeResponseData, PipelineStageStatus } from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { 
  GitCommit, 
  CheckCircle2, 
  Clock, 
  Play, 
  ChevronDown, 
  ChevronRight, 
  HelpCircle,
  AlertTriangle,
  ArrowRight
} from 'lucide-react';

export const DecisionTraceView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();

  const [pipelineData, setPipelineData] = useState<PipelineAnalyzeResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedStage, setExpandedStage] = useState<string | null>('POLICY');

  const runPipeline = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.analyzePipeline({
        station_id: currentStation,
        horizon_hours: horizonHours,
        scenario_id: 'NORMAL_BASELINE',
        mode: 'EXPECTED',
      });
      if (res.data) {
        setPipelineData(res.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute end-to-end pipeline analysis');
    } finally {
      setLoading(false);
    }
  }, [currentStation, horizonHours]);

  useEffect(() => {
    runPipeline();
  }, [runPipeline]);

  const stages = pipelineData?.stages || [];

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-xl bg-polar-900/60 border border-polar-800">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold font-mono text-polar-100 uppercase tracking-wide">
              Explainable Decision Trace & Audit (Phases 3–8)
            </h2>
            <ProvenanceTag provenance="SIMULATED" size="xs" />
          </div>
          <p className="text-xs text-polar-400 mt-1">
            Complete sequential causal chain answering: <em className="text-polar-200">"Why did Polaris-EMS make this operational recommendation?"</em>
          </p>
        </div>

        <button
          onClick={runPipeline}
          disabled={loading}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-bold rounded-lg transition-all shadow-md shadow-cyan-950/30 shrink-0"
        >
          <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Executing Pipeline...' : 'Run Pipeline Audit'}</span>
        </button>
      </div>

      {loading ? (
        <LoadingSkeleton height="h-32" rows={3} />
      ) : error ? (
        <ErrorCard title="Pipeline Execution Error" message={error} onRetry={runPipeline} />
      ) : pipelineData ? (
        <div className="space-y-6">
          {/* Top Pipeline Overview Card */}
          <div className="p-5 rounded-xl bg-polar-900/70 border border-polar-800 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
            <div className="flex items-center space-x-4">
              <span className="text-polar-400">Run ID:</span>
              <span className="text-polar-100 font-bold">{pipelineData.pipeline_run_id}</span>
              <span className="text-polar-400">Station:</span>
              <span className="text-cyan-300 font-bold">{pipelineData.station_id}</span>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-polar-400">Pipeline Status:</span>
              <StatusBadge status={pipelineData.overall_status} size="sm" />
              <span className="text-polar-400">
                Total Latency: {stages.reduce((sum, s) => sum + s.duration_sec, 0).toFixed(3)}s
              </span>
            </div>
          </div>

          {/* Sequential Stage Flow Stepper */}
          <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-6">
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
              End-to-End Decision Chain Flow
            </h3>

            {/* Stepper Grid */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-xs font-mono">
              {stages.map((stg, idx) => {
                const isExpanded = expandedStage === stg.stage_name;
                return (
                  <button
                    key={stg.stage_name}
                    onClick={() => setExpandedStage(isExpanded ? null : stg.stage_name)}
                    className={`p-3 rounded-lg border text-left transition-all relative ${
                      isExpanded 
                        ? 'bg-polar-800 border-cyan-500 shadow-md shadow-cyan-950/20' 
                        : 'bg-polar-950/70 border-polar-800 hover:border-polar-700'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] text-polar-400">
                      <span>STEP #{idx + 1}</span>
                      <span>{stg.duration_sec.toFixed(3)}s</span>
                    </div>
                    <div className="font-bold text-polar-100 mt-1 uppercase truncate">
                      {stg.stage_name}
                    </div>
                    <div className="mt-2">
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        stg.status === 'COMPLETED'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30'
                          : stg.status === 'SKIPPED'
                          ? 'bg-polar-900 text-polar-500 border border-polar-800'
                          : 'bg-amber-950 text-amber-400 border border-amber-500/30'
                      }`}>
                        {stg.status}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Detailed Stage Inspector */}
            {expandedStage && (
              <div className="p-4 rounded-lg bg-polar-950/90 border border-polar-750 font-mono text-xs space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-polar-800">
                  <span className="font-bold text-cyan-300 text-sm uppercase">
                    Stage Diagnostic: {expandedStage}
                  </span>
                  <span className="text-polar-400 text-xs">
                    {stages.find(s => s.stage_name === expandedStage)?.message}
                  </span>
                </div>

                {/* Subsystem specific telemetry */}
                {expandedStage === 'OPTIMIZER' && pipelineData.optimizer && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] pt-1">
                    <div>Solver Status: <strong className="text-emerald-400">{pipelineData.optimizer.solver_status}</strong></div>
                    <div>Tier: <strong className="text-cyan-300">{pipelineData.optimizer.optimality_tier}</strong></div>
                    <div>MIP Gap: <strong className="text-polar-100">{pipelineData.optimizer.relative_gap != null ? `${(pipelineData.optimizer.relative_gap * 100).toFixed(2)}%` : '0%'}</strong></div>
                    <div>Twin Replay: <strong className="text-emerald-400">{pipelineData.optimizer.twin_replay_valid ? 'VALIDATED' : 'BYPASSED'}</strong></div>
                  </div>
                )}

                {expandedStage === 'RESILIENCE' && pipelineData.resilience && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] pt-1">
                    <div>State: <strong className="text-cyan-300">{pipelineData.resilience.resilience_state}</strong></div>
                    <div>Survival: <strong className="text-polar-100">{pipelineData.resilience.survival_horizons.overall_station_survival_horizon_h.toFixed(1)}h</strong></div>
                    <div>Binding Limit: <strong className="text-amber-400 uppercase">{pipelineData.resilience.survival_horizons.binding_subsystem}</strong></div>
                    <div>Index: <strong className="text-emerald-400">{pipelineData.resilience.dimensions?.composite_resilience_index.toFixed(1)}/100</strong></div>
                  </div>
                )}

                {expandedStage === 'POLICY' && pipelineData.policy && (
                  <div className="space-y-2 pt-1 text-[11px]">
                    <div>Active Directive: <strong className="text-cyan-300">{pipelineData.policy.primary_directive}</strong></div>
                    <div>Policy State: <strong className="text-polar-100">{pipelineData.policy.policy_state}</strong></div>
                    <div>Advisory Rationale: <span className="text-polar-300 font-sans">{pipelineData.policy.optimizer_handoff.advisory_rationale}</span></div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
};
