import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { api } from '../api/endpoints';
import { 
  PipelineAnalyzeResponseData, 
  TraceSummary, 
  TraceDetail, 
  TraceEventItem, 
  DecisionExplanation, 
  DecisionDelta,
  ProvenanceTier,
  ValidationTier
} from '../api/types';
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
  ArrowRight,
  Download,
  GitCompare,
  Network,
  Cpu,
  ShieldCheck,
  FileText,
  RefreshCw,
  Search,
  Activity,
  Layers,
  Database
} from 'lucide-react';

export const DecisionTraceView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();

  // Active trace and pipeline state
  const [pipelineData, setPipelineData] = useState<PipelineAnalyzeResponseData | null>(null);
  const [traceHistory, setTraceHistory] = useState<TraceSummary[]>([]);
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [traceDetail, setTraceDetail] = useState<TraceDetail | null>(null);
  const [explanation, setExplanation] = useState<DecisionExplanation | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  // Comparison state
  const [compareTraceId, setCompareTraceId] = useState<string | null>(null);
  const [comparisonDelta, setComparisonDelta] = useState<DecisionDelta | null>(null);
  const [showCompareModal, setShowCompareModal] = useState<boolean>(false);

  // View tabs & raw inspector
  const [activeTab, setActiveTab] = useState<'timeline' | 'graph' | 'explanation' | 'comparison' | 'raw'>('timeline');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<boolean>(false);

  // Load trace history for the station
  const loadTraceHistory = useCallback(async () => {
    try {
      const res = await api.listTraces({ station_id: currentStation, limit: 20 });
      if (res.data) {
        setTraceHistory(res.data);
        if (res.data.length > 0 && !selectedTraceId) {
          setSelectedTraceId(res.data[0].decision_trace_id);
        }
      }
    } catch {
      // Non-blocking history fetch
    }
  }, [currentStation, selectedTraceId]);

  // Load detail and explanation for selected trace
  const loadTraceDetail = useCallback(async (traceId: string) => {
    try {
      const [detailRes, expRes] = await Promise.all([
        api.getTrace(traceId),
        api.getTraceExplanation(traceId)
      ]);
      if (detailRes.data) {
        setTraceDetail(detailRes.data);
        if (detailRes.data.events.length > 0) {
          setSelectedEventId(detailRes.data.events[0].event_id);
        }
      }
      if (expRes.data) {
        setExplanation(expRes.data);
      }
    } catch (err: any) {
      console.warn("Could not load trace detail:", err);
    }
  }, []);

  // Run pipeline analysis and immediately select new decision trace
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
        const newTraceId = res.data.decision_trace_id;
        if (newTraceId) {
          setSelectedTraceId(newTraceId);
          await loadTraceDetail(newTraceId);
        }
        await loadTraceHistory();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute end-to-end pipeline audit');
    } finally {
      setLoading(false);
    }
  }, [currentStation, horizonHours, loadTraceDetail, loadTraceHistory]);

  // Initial load: check history first for instant display, fallback to pipeline run
  useEffect(() => {
    let isMounted = true;
    const initTraceView = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.listTraces({ station_id: currentStation, limit: 20 });
        if (res.data && res.data.length > 0 && isMounted) {
          setTraceHistory(res.data);
          const latestId = res.data[0].decision_trace_id;
          setSelectedTraceId(latestId);
          await loadTraceDetail(latestId);
          setLoading(false);
          return;
        }
      } catch {
        // Fallback to pipeline execution below
      }
      if (isMounted) {
        await runPipeline();
      }
    };
    initTraceView();
    return () => { isMounted = false; };
  }, [currentStation, horizonHours, loadTraceDetail, runPipeline]);

  // When selectedTraceId changes manually, fetch details
  useEffect(() => {
    if (selectedTraceId) {
      loadTraceDetail(selectedTraceId);
    }
  }, [selectedTraceId, loadTraceDetail]);

  // Run comparison when compareTraceId is chosen
  const handleCompare = async (targetId: string) => {
    if (!selectedTraceId || !targetId) return;
    try {
      const res = await api.compareTraces(selectedTraceId, targetId);
      if (res.data) {
        setComparisonDelta(res.data);
        setCompareTraceId(targetId);
        setActiveTab('comparison');
      }
    } catch (err: any) {
      alert(`Comparison failed: ${err.message}`);
    }
  };

  // Export trace handler
  const handleExport = async (format: 'json' | 'csv') => {
    if (!selectedTraceId) return;
    setExporting(true);
    try {
      const content = await api.exportTrace(selectedTraceId, format);
      const blob = new Blob([content], { 
        type: format === 'json' ? 'application/json' : 'text/csv' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedTraceId}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  const selectedEvent = traceDetail?.events.find(e => e.event_id === selectedEventId) || traceDetail?.events[0];

  // Epistemic validation badge renderer
  const renderValidationBadge = (tier: ValidationTier) => {
    const colorMap: Record<ValidationTier, string> = {
      VALIDATED: 'bg-emerald-950 text-emerald-300 border-emerald-500/40',
      COMPUTED: 'bg-cyan-950 text-cyan-300 border-cyan-500/40',
      SIMULATED: 'bg-blue-950 text-blue-300 border-blue-500/40',
      ESTIMATED: 'bg-amber-950 text-amber-300 border-amber-500/40',
      ADVISORY: 'bg-purple-950 text-purple-300 border-purple-500/40',
      REQUESTED: 'bg-polar-900 text-polar-300 border-polar-700',
    };
    return (
      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${colorMap[tier] || 'bg-polar-800 text-polar-300 border-polar-700'}`}>
        {tier}
      </span>
    );
  };

  // Stage color mapper
  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'EDGE': return 'text-amber-400 border-amber-500/40 bg-amber-950/40';
      case 'FORECAST': return 'text-blue-400 border-blue-500/40 bg-blue-950/40';
      case 'SCENARIO': return 'text-indigo-400 border-indigo-500/40 bg-indigo-950/40';
      case 'OPTIMIZER': return 'text-cyan-400 border-cyan-500/40 bg-cyan-950/40';
      case 'TWIN_REPLAY': return 'text-emerald-400 border-emerald-500/40 bg-emerald-950/40';
      case 'RESILIENCE': return 'text-orange-400 border-orange-500/40 bg-orange-950/40';
      case 'POLICY': return 'text-purple-400 border-purple-500/40 bg-purple-950/40';
      default: return 'text-polar-300 border-polar-700 bg-polar-900/40';
    }
  };

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">
      {/* 1. Header Bar with Station Context & Execution Trigger */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-xl bg-polar-900/60 border border-polar-800 backdrop-blur-md">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold font-mono text-polar-100 uppercase tracking-wide flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-cyan-400" />
              Decision Trace & Auditability Workspace
            </h2>
            <ProvenanceTag provenance="SIMULATED" size="xs" />
          </div>
          <p className="text-xs text-polar-400 mt-1">
            End-to-end observational audit layer proving how Polaris-EMS reached its operational posture from evidence to policy.
          </p>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={() => loadTraceHistory()}
            title="Refresh Trace History"
            className="p-2 bg-polar-800 hover:bg-polar-700 text-polar-200 rounded-lg border border-polar-700 text-xs"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={runPipeline}
            disabled={loading}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-bold rounded-lg transition-all shadow-md shadow-cyan-950/30"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Auditing Pipeline...' : 'Run Pipeline Audit'}</span>
          </button>
        </div>
      </div>

      {loading && !traceDetail ? (
        <LoadingSkeleton height="h-64" rows={3} />
      ) : error ? (
        <ErrorCard title="Pipeline Audit Execution Error" message={error} onRetry={runPipeline} />
      ) : (
        <div className="space-y-6">
          {/* 2. Trace Selector Bar & Metadata Overview */}
          <div className="p-4 rounded-xl bg-polar-900/80 border border-polar-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs font-mono">
            {/* Trace History Dropdown */}
            <div className="flex items-center space-x-3 w-full md:w-auto">
              <span className="text-polar-400 uppercase tracking-wider font-bold">Active Trace:</span>
              <select
                value={selectedTraceId || ''}
                onChange={(e) => setSelectedTraceId(e.target.value)}
                className="bg-polar-950 border border-polar-700 text-cyan-300 font-bold px-3 py-1.5 rounded-lg focus:outline-none focus:border-cyan-500 text-xs"
              >
                {traceHistory.map((tr) => (
                  <option key={tr.decision_trace_id} value={tr.decision_trace_id}>
                    {tr.decision_trace_id} ({tr.execution_status} - {new Date(tr.creation_timestamp).toLocaleTimeString()})
                  </option>
                ))}
              </select>
            </div>

            {/* Quick Badge Summary */}
            {traceDetail && (
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-polar-400">Station: <strong className="text-polar-100">{traceDetail.station_id}</strong></span>
                <span className="text-polar-400">Mode: <strong className="text-cyan-300">{traceDetail.optimization_mode}</strong></span>
                <span className="text-polar-400">Policy: <strong className="text-purple-300">{traceDetail.policy_state || 'NOMINAL'}</strong></span>
                <span className="text-polar-400">Resilience: <strong className="text-emerald-300">{traceDetail.resilience_state || 'SAFE'}</strong></span>
                <StatusBadge status={traceDetail.execution_status} size="sm" />
              </div>
            )}

            {/* Export & Compare Actions */}
            <div className="flex items-center space-x-2 w-full md:w-auto justify-end">
              <button
                onClick={() => setShowCompareModal(true)}
                className="inline-flex items-center space-x-1 px-3 py-1.5 bg-polar-800 hover:bg-polar-700 text-polar-200 border border-polar-700 rounded-lg text-xs"
              >
                <GitCompare className="w-3.5 h-3.5 text-cyan-400" />
                <span>Compare</span>
              </button>

              <button
                onClick={() => handleExport('json')}
                disabled={exporting}
                className="inline-flex items-center space-x-1 px-2.5 py-1.5 bg-polar-800 hover:bg-polar-700 text-polar-200 border border-polar-700 rounded-lg text-xs"
                title="Export Trace JSON"
              >
                <Download className="w-3.5 h-3.5 text-emerald-400" />
                <span>JSON</span>
              </button>

              <button
                onClick={() => handleExport('csv')}
                disabled={exporting}
                className="inline-flex items-center space-x-1 px-2.5 py-1.5 bg-polar-800 hover:bg-polar-700 text-polar-200 border border-polar-700 rounded-lg text-xs"
                title="Export Trace CSV"
              >
                <Download className="w-3.5 h-3.5 text-blue-400" />
                <span>CSV</span>
              </button>
            </div>
          </div>

          {/* Navigation View Tabs */}
          <div className="flex border-b border-polar-800 text-xs font-mono">
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-4 py-2.5 font-bold uppercase tracking-wider transition-colors border-b-2 flex items-center space-x-2 ${
                activeTab === 'timeline'
                  ? 'border-cyan-500 text-cyan-400 bg-polar-800/40'
                  : 'border-transparent text-polar-400 hover:text-polar-200'
              }`}
            >
              <Clock className="w-4 h-4" />
              <span>Stage Timeline</span>
            </button>

            <button
              onClick={() => setActiveTab('graph')}
              className={`px-4 py-2.5 font-bold uppercase tracking-wider transition-colors border-b-2 flex items-center space-x-2 ${
                activeTab === 'graph'
                  ? 'border-cyan-500 text-cyan-400 bg-polar-800/40'
                  : 'border-transparent text-polar-400 hover:text-polar-200'
              }`}
            >
              <Network className="w-4 h-4" />
              <span>Lineage DAG</span>
            </button>

            <button
              onClick={() => setActiveTab('explanation')}
              className={`px-4 py-2.5 font-bold uppercase tracking-wider transition-colors border-b-2 flex items-center space-x-2 ${
                activeTab === 'explanation'
                  ? 'border-cyan-500 text-cyan-400 bg-polar-800/40'
                  : 'border-transparent text-polar-400 hover:text-polar-200'
              }`}
            >
              <HelpCircle className="w-4 h-4" />
              <span>"Why?" Explainer</span>
            </button>

            <button
              onClick={() => setActiveTab('comparison')}
              className={`px-4 py-2.5 font-bold uppercase tracking-wider transition-colors border-b-2 flex items-center space-x-2 ${
                activeTab === 'comparison'
                  ? 'border-cyan-500 text-cyan-400 bg-polar-800/40'
                  : 'border-transparent text-polar-400 hover:text-polar-200'
              }`}
            >
              <GitCompare className="w-4 h-4" />
              <span>Decision Delta</span>
            </button>

            <button
              onClick={() => setActiveTab('raw')}
              className={`px-4 py-2.5 font-bold uppercase tracking-wider transition-colors border-b-2 flex items-center space-x-2 ${
                activeTab === 'raw'
                  ? 'border-cyan-500 text-cyan-400 bg-polar-800/40'
                  : 'border-transparent text-polar-400 hover:text-polar-200'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Raw Record</span>
            </button>
          </div>

          {/* TAB 1: Stage Timeline & Evidence Inspector */}
          {activeTab === 'timeline' && traceDetail && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Sequential Stage Timeline Cards */}
              <div className="lg:col-span-7 space-y-3">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-polar-300 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  Sequential Pipeline Execution Stages ({traceDetail.events.length} Events)
                </h3>

                <div className="space-y-2.5">
                  {traceDetail.events.map((ev, idx) => {
                    const isSelected = selectedEventId === ev.event_id;
                    const stageColor = getStageColor(ev.stage);
                    return (
                      <div
                        key={ev.event_id}
                        onClick={() => setSelectedEventId(ev.event_id)}
                        className={`p-3.5 rounded-xl border transition-all cursor-pointer font-mono text-xs ${
                          isSelected
                            ? 'bg-polar-850 border-cyan-500 shadow-md shadow-cyan-950/30 ring-1 ring-cyan-500/50'
                            : 'bg-polar-900/70 border-polar-800 hover:border-polar-700'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-[10px] font-bold text-polar-500">#{idx + 1}</span>
                            <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${stageColor}`}>
                              {ev.stage}
                            </span>
                            <span className="font-bold text-polar-100 truncate">{ev.event_type}</span>
                          </div>

                          <div className="flex items-center space-x-2">
                            {renderValidationBadge(ev.validation_tier)}
                            <ProvenanceTag provenance={ev.provenance} size="xs" />
                          </div>
                        </div>

                        <p className="mt-2 text-polar-300 text-xs line-clamp-2 font-sans">
                          {ev.summary}
                        </p>

                        <div className="mt-2.5 flex items-center justify-between text-[10px] text-polar-400 pt-2 border-t border-polar-800/60">
                          <span className="text-cyan-400/90 font-bold">{ev.reason_code}</span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-polar-500" />
                            {ev.duration_ms.toFixed(1)} ms
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right Column: Detailed Evidence & Validation Inspector */}
              <div className="lg:col-span-5 space-y-4">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-polar-300 flex items-center gap-2">
                  <Database className="w-4 h-4 text-cyan-400" />
                  Stage Evidence & Validation Details
                </h3>

                {selectedEvent ? (
                  <div className="p-5 rounded-xl bg-polar-900/90 border border-polar-750 font-mono text-xs space-y-4 backdrop-blur-sm">
                    <div className="flex items-center justify-between pb-3 border-b border-polar-800">
                      <div>
                        <span className="text-[10px] text-polar-400 uppercase">Selected Event ID:</span>
                        <div className="font-bold text-cyan-300 text-xs">{selectedEvent.event_id}</div>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-[10px] text-polar-400 uppercase">Validation Tier:</span>
                        {renderValidationBadge(selectedEvent.validation_tier)}
                      </div>
                    </div>

                    {/* Summary Card */}
                    <div className="p-3 rounded-lg bg-polar-950/80 border border-polar-800 text-xs font-sans text-polar-200">
                      <strong className="text-polar-100 block font-mono text-[11px] mb-1 uppercase tracking-wider text-cyan-400">
                        Factual Finding:
                      </strong>
                      {selectedEvent.summary}
                    </div>

                    {/* Invariant Distinction Alert */}
                    {selectedEvent.stage === 'OPTIMIZER' && (
                      <div className="p-3 rounded-lg bg-blue-950/40 border border-blue-500/30 text-blue-200 text-xs font-sans">
                        <strong className="font-mono text-blue-300 block mb-1">PROPOSED DISPATCH:</strong>
                        This schedule represents optimizer-proposed dispatch under mathematical constraints. Physical validity is proven in the downstream Digital Twin stage.
                      </div>
                    )}

                    {selectedEvent.stage === 'TWIN_REPLAY' && (
                      <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 text-xs font-sans">
                        <strong className="font-mono text-emerald-300 block mb-1">PHYSICALLY VALIDATED:</strong>
                        Replayed through high-fidelity polar battery, diesel, and thermal physics equations to verify zero thermal or capacity breaches.
                      </div>
                    )}

                    {selectedEvent.stage === 'RESILIENCE' && (
                      <div className="p-3 rounded-lg bg-amber-950/40 border border-amber-500/30 text-amber-200 text-xs font-sans">
                        <strong className="font-mono text-amber-300 block mb-1">ESTIMATED RECOVERY HORIZON:</strong>
                        Assessed 5 survival dimensions. Projected recovery pathways carry ESTIMATED validation tier pending real-world confirmation.
                      </div>
                    )}

                    {/* Observed Outputs */}
                    <div>
                      <span className="text-[11px] font-bold text-polar-300 uppercase tracking-wider block mb-2">
                        Observed Stage Outputs:
                      </span>
                      <div className="p-3 rounded-lg bg-polar-950/90 border border-polar-800/80 space-y-1.5 text-[11px]">
                        {Object.entries(selectedEvent.outputs).map(([k, v]) => (
                          <div key={k} className="flex justify-between items-center py-0.5 border-b border-polar-900/60 last:border-0">
                            <span className="text-polar-400">{k}:</span>
                            <span className="text-polar-100 font-bold max-w-[240px] truncate text-right">
                              {typeof v === 'boolean' ? (v ? 'TRUE' : 'FALSE') : String(v)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Inputs & Lineage Metadata */}
                    <div className="pt-2 border-t border-polar-800 text-[10px] text-polar-400 space-y-1">
                      <div>Parent Event: <span className="text-polar-200">{selectedEvent.parent_event_id || 'NONE (ROOT NODE)'}</span></div>
                      <div>Engine Version: <span className="text-polar-200">{selectedEvent.engine_version}</span></div>
                      <div>Timestamp: <span className="text-polar-200">{selectedEvent.timestamp}</span></div>
                      <div>Reason Code: <span className="text-cyan-400 font-bold">{selectedEvent.reason_code}</span></div>
                    </div>
                  </div>
                ) : (
                  <div className="p-8 text-center text-polar-500 font-mono text-xs border border-dashed border-polar-800 rounded-xl">
                    Select an event to inspect its inputs, outputs, and validation tier.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: DAG Lineage Visualization */}
          {activeTab === 'graph' && traceDetail && (
            <div className="p-6 rounded-xl bg-polar-900/70 border border-polar-800 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-polar-100">
                    Decision Lineage Dependency DAG
                  </h3>
                  <p className="text-xs text-polar-400 mt-0.5">
                    Parent-to-child sequential validation graph showing exact execution order and terminal state.
                  </p>
                </div>
                <div className="text-xs font-mono text-polar-400">
                  Terminal Status: <strong className="text-emerald-400">{traceDetail.execution_status}</strong>
                </div>
              </div>

              {/* Graphical Lineage Sequence */}
              <div className="flex flex-col md:flex-row items-center justify-between gap-3 p-6 bg-polar-950/80 rounded-xl border border-polar-800 overflow-x-auto">
                {traceDetail.events.map((ev, idx) => (
                  <React.Fragment key={ev.event_id}>
                    <div 
                      onClick={() => {
                        setSelectedEventId(ev.event_id);
                        setActiveTab('timeline');
                      }}
                      className={`p-3.5 rounded-lg border text-center font-mono cursor-pointer transition-all min-w-[130px] shrink-0 ${
                        getStageColor(ev.stage)
                      }`}
                    >
                      <div className="text-[10px] text-polar-400 font-bold">NODE #{idx + 1}</div>
                      <div className="text-xs font-bold uppercase mt-1">{ev.stage}</div>
                      <div className="text-[9px] text-polar-300 mt-1 truncate">{ev.event_type}</div>
                      <div className="mt-2 text-[10px] font-bold text-polar-100">
                        {ev.status}
                      </div>
                    </div>

                    {idx < traceDetail.events.length - 1 && (
                      <div className="text-polar-600 hidden md:block">
                        <ArrowRight className="w-5 h-5 text-cyan-500/70" />
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>

              <div className="p-4 rounded-lg bg-polar-950/60 border border-polar-800/80 font-mono text-xs text-polar-400 space-y-2">
                <span className="font-bold text-polar-200 block uppercase">DAG Adjacency Map:</span>
                <pre className="text-[11px] text-cyan-300/80 overflow-x-auto p-2 bg-polar-900 rounded">
                  {JSON.stringify(traceDetail.lineage_graph, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* TAB 3: "Why?" Explanation Panel */}
          {activeTab === 'explanation' && explanation && (
            <div className="p-6 rounded-xl bg-polar-900/70 border border-polar-800 space-y-6">
              {/* Headline Banner */}
              <div className="p-4 rounded-xl bg-cyan-950/30 border border-cyan-500/30">
                <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold block mb-1">
                  Executive Decision Summary:
                </span>
                <p className="text-sm font-sans font-medium text-cyan-100">
                  {explanation.headline}
                </p>
              </div>

              {/* Core "Why?" Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
                <div className="p-4 rounded-xl bg-polar-950/80 border border-polar-800 space-y-2">
                  <div className="text-orange-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5" />
                    Why This State?
                  </div>
                  <p className="text-polar-300 font-sans text-xs leading-relaxed">
                    {explanation.why_this_state}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-polar-950/80 border border-polar-800 space-y-2">
                  <div className="text-purple-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Why This Policy?
                  </div>
                  <p className="text-polar-300 font-sans text-xs leading-relaxed">
                    {explanation.why_this_policy}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-polar-950/80 border border-polar-800 space-y-2">
                  <div className="text-cyan-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5" />
                    Why This Schedule?
                  </div>
                  <p className="text-polar-300 font-sans text-xs leading-relaxed">
                    {explanation.why_this_schedule}
                  </p>
                </div>
              </div>

              {/* Epistemic Breakdown (Validated vs Estimated vs Data Used) */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
                <div className="p-4 rounded-xl bg-polar-950/80 border border-polar-800 space-y-2">
                  <span className="text-polar-400 uppercase font-bold block text-[11px]">
                    What Data Was Used?
                  </span>
                  <ul className="space-y-1 text-polar-300 list-disc list-inside font-sans text-xs">
                    {explanation.what_data_used.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-polar-950/80 border border-polar-800 space-y-2">
                  <span className="text-emerald-400 uppercase font-bold block text-[11px]">
                    What Was Physically Validated?
                  </span>
                  <ul className="space-y-1 text-polar-300 list-disc list-inside font-sans text-xs">
                    {explanation.what_was_validated.map((v, i) => (
                      <li key={i}>{v}</li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-polar-950/80 border border-polar-800 space-y-2">
                  <span className="text-amber-400 uppercase font-bold block text-[11px]">
                    What Remains Estimated?
                  </span>
                  <ul className="space-y-1 text-polar-300 list-disc list-inside font-sans text-xs">
                    {explanation.what_remains_estimated.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Recommended Next Action */}
              <div className="p-4 rounded-xl bg-polar-950/90 border border-polar-750 font-mono text-xs">
                <span className="text-purple-400 uppercase font-bold block text-[11px] mb-1">
                  What Happens Next? (Operational Handoff)
                </span>
                <p className="text-polar-200 font-sans text-xs">
                  {explanation.what_is_next}
                </p>
              </div>
            </div>
          )}

          {/* TAB 4: Decision Delta / Comparison */}
          {activeTab === 'comparison' && (
            <div className="p-6 rounded-xl bg-polar-900/70 border border-polar-800 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-polar-100 flex items-center gap-2">
                    <GitCompare className="w-4 h-4 text-cyan-400" />
                    Factual Decision Delta (Before vs After)
                  </h3>
                  <p className="text-xs text-polar-400 mt-0.5">
                    Compares current trace against a baseline or previous decision without evaluative bias.
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono text-polar-400">Compare With:</span>
                  <select
                    value={compareTraceId || ''}
                    onChange={(e) => handleCompare(e.target.value)}
                    className="bg-polar-950 border border-polar-700 text-polar-200 text-xs px-3 py-1 rounded"
                  >
                    <option value="">Select Trace...</option>
                    {traceHistory.filter(t => t.decision_trace_id !== selectedTraceId).map(t => (
                      <option key={t.decision_trace_id} value={t.decision_trace_id}>
                        {t.decision_trace_id}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {comparisonDelta ? (
                <div className="space-y-4">
                  {/* Delta Narrative */}
                  <div className="p-4 rounded-xl bg-polar-950/80 border border-polar-800 text-xs font-sans text-polar-200">
                    <strong className="text-cyan-400 font-mono text-[11px] block uppercase mb-1">
                      Comparative Narrative:
                    </strong>
                    {comparisonDelta.summary_narrative}
                  </div>

                  {/* State Transitions Table */}
                  <div className="p-4 rounded-xl bg-polar-950/80 border border-polar-800 font-mono text-xs space-y-3">
                    <span className="font-bold text-polar-200 uppercase block text-[11px]">
                      Categorical State Transitions:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                      {Object.entries(comparisonDelta.state_transitions).map(([key, [prev, curr]]) => (
                        <div key={key} className="p-3 rounded bg-polar-900 border border-polar-800">
                          <span className="text-[10px] text-polar-400 uppercase block">{key}:</span>
                          <div className="mt-1 flex items-center space-x-2">
                            <span className="text-polar-400 line-through">{prev}</span>
                            <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
                            <span className="text-polar-100 font-bold">{curr}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Numerical Deltas */}
                  <div className="p-4 rounded-xl bg-polar-950/80 border border-polar-800 font-mono text-xs space-y-3">
                    <span className="font-bold text-polar-200 uppercase block text-[11px]">
                      Numerical Metric Shifts:
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {Object.entries(comparisonDelta.numerical_deltas).map(([k, val]) => (
                        <div key={k} className="p-3 rounded bg-polar-900 border border-polar-800 flex justify-between items-center">
                          <span className="text-polar-400 text-[11px]">{k}:</span>
                          <span className={`font-bold ${val > 0 ? 'text-amber-400' : val < 0 ? 'text-emerald-400' : 'text-polar-200'}`}>
                            {val > 0 ? `+${val.toFixed(2)}` : val.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-polar-500 font-mono text-xs border border-dashed border-polar-800 rounded-xl">
                  Select a comparison trace from the dropdown above to compute the factual decision delta.
                </div>
              )}
            </div>
          )}

          {/* TAB 5: Raw JSON Record */}
          {activeTab === 'raw' && traceDetail && (
            <div className="p-4 rounded-xl bg-polar-900/80 border border-polar-800 font-mono text-xs">
              <div className="flex justify-between items-center pb-2 border-b border-polar-800 mb-3">
                <span className="text-polar-300 font-bold uppercase">
                  Canonical Machine Trace JSON Record ({traceDetail.decision_trace_id})
                </span>
                <button
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(traceDetail, null, 2))}
                  className="px-2.5 py-1 bg-polar-800 hover:bg-polar-700 text-polar-200 rounded text-[11px]"
                >
                  Copy JSON
                </button>
              </div>
              <pre className="p-4 bg-polar-950 rounded-lg border border-polar-850 overflow-x-auto text-polar-300 text-[11px] max-h-[500px]">
                {JSON.stringify(traceDetail, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Modal: Compare Trace Selector */}
      {showCompareModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-polar-900 border border-polar-700 rounded-xl max-w-md w-full p-5 space-y-4 font-mono text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-polar-800">
              <h4 className="font-bold text-polar-100 uppercase">Select Trace to Compare</h4>
              <button
                onClick={() => setShowCompareModal(false)}
                className="text-polar-400 hover:text-polar-200"
              >
                ✕
              </button>
            </div>

            <p className="text-polar-400 text-[11px] font-sans">
              Choose an earlier or baseline decision trace to evaluate state transitions, schedule variations, and metric shifts.
            </p>

            <div className="space-y-2 max-h-60 overflow-y-auto">
              {traceHistory.map(tr => (
                <button
                  key={tr.decision_trace_id}
                  onClick={() => {
                    setShowCompareModal(false);
                    handleCompare(tr.decision_trace_id);
                  }}
                  disabled={tr.decision_trace_id === selectedTraceId}
                  className={`w-full p-2.5 rounded text-left border flex items-center justify-between transition-colors ${
                    tr.decision_trace_id === selectedTraceId
                      ? 'bg-polar-950 text-polar-600 border-polar-900 cursor-not-allowed'
                      : 'bg-polar-950/70 hover:bg-polar-800 text-polar-200 border-polar-800'
                  }`}
                >
                  <div>
                    <div className="font-bold text-cyan-300">{tr.decision_trace_id}</div>
                    <div className="text-[10px] text-polar-500">{new Date(tr.creation_timestamp).toLocaleString()}</div>
                  </div>
                  <StatusBadge status={tr.execution_status} size="sm" />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
