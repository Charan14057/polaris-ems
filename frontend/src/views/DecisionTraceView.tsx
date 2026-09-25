import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { useEvidence } from '../context/EvidenceContext';
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
import { WhyThisMatters } from '../components/common/WhyThisMatters';
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { JargonTooltip } from '../components/common/JargonTooltip';
import { 
  ShieldCheck, 
  Clock, 
  Play, 
  HelpCircle,
  AlertTriangle,
  ArrowRight,
  Download,
  GitCompare,
  Network,
  Cpu,
  FileText,
  RefreshCw,
  Activity,
  Layers,
  Database
} from 'lucide-react';

export const DecisionTraceView: React.FC = () => {
  const { currentStation, horizonHours } = useStation();
  const { inspectEvidence } = useEvidence();

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
      VALIDATED: 'bg-[#EBF7F0] text-[#166534] border-[#BBF7D0]',
      COMPUTED: 'bg-[#E0F2FE] text-[#0369A1] border-[#BAE6FD]',
      SIMULATED: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]',
      ESTIMATED: 'bg-[#FEF3C7] text-[#92400E] border-[#FDE68A]',
      ADVISORY: 'bg-[#F3E8FF] text-[#6B21A8] border-[#E9D5FF]',
      REQUESTED: 'bg-[#F6F3EC] text-[#78716C] border-[#DDD6C6]',
    };
    return (
      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${colorMap[tier] || 'bg-[#F6F3EC] text-[#78716C] border-[#DDD6C6]'}`}>
        {tier}
      </span>
    );
  };

  // Stage color mapper in warm tones
  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'EDGE': return 'text-[#B45309] border-[#FDE68A] bg-[#FEF3C7]';
      case 'FORECAST': return 'text-[#0284C7] border-[#BAE6FD] bg-[#E0F2FE]';
      case 'SCENARIO': return 'text-[#4338CA] border-[#C7D2FE] bg-[#EEF2FF]';
      case 'OPTIMIZER': return 'text-[#0F766E] border-[#99F6E4] bg-[#CCFBF1]';
      case 'TWIN_REPLAY': return 'text-[#15803D] border-[#BBF7D0] bg-[#DCFCE7]';
      case 'RESILIENCE': return 'text-[#C2410C] border-[#FFEDD5] bg-[#FFF7ED]';
      case 'POLICY': return 'text-[#7E22CE] border-[#E9D5FF] bg-[#FAF5FF]';
      default: return 'text-[#57534E] border-[#DDD6C6] bg-[#F6F3EC]';
    }
  };

  return (
    <div className="p-4 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* 1. Header Bar with Station Context & Execution Trigger */}
      <div className="border-b border-[#DDD6C6] pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-[#78716C] mb-2">
            <span>09 Decision Trace &amp; Auditability</span>
            <span>•</span>
            <ProvenanceTag provenance="SIMULATED" size="xs" />
          </div>
          <h1 className="font-serif text-3xl lg:text-4xl text-[#1C1917] tracking-tight">
            Decision Trace &amp; Auditability
          </h1>
          <p className="text-sm text-[#57534E] font-sans mt-2 max-w-2xl">
            End-to-end observational audit layer proving how Polaris-EMS reached its operational posture from evidence to policy.
          </p>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={() => loadTraceHistory()}
            title="Refresh Trace History"
            className="p-2 bg-white hover:bg-[#F6F3EC] text-[#1C1917] rounded border border-[#DDD6C6] text-xs shadow-sm transition"
          >
            <RefreshCw className="w-4 h-4 text-[#78716C]" />
          </button>

          <button
            onClick={runPipeline}
            disabled={loading}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-[#B45309] hover:bg-[#92400E] text-white text-xs font-mono font-bold rounded transition shadow-sm"
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
          <div className="p-4 rounded bg-white border border-[#DDD6C6] flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs font-mono shadow-sm">
            {/* Trace History Dropdown */}
            <div className="flex items-center space-x-3 w-full md:w-auto">
              <span className="text-[#78716C] uppercase tracking-wider font-bold">Active Trace:</span>
              <select
                value={selectedTraceId || ''}
                onChange={(e) => setSelectedTraceId(e.target.value)}
                className="bg-[#F6F3EC] border border-[#DDD6C6] text-[#B45309] font-bold px-3 py-1.5 rounded focus:outline-none focus:border-[#B45309] text-xs"
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
                <span className="text-[#78716C]">Station: <strong className="text-[#1C1917]">{traceDetail.station_id}</strong></span>
                <span className="text-[#78716C]">Mode: <strong className="text-[#0284C7]">{traceDetail.optimization_mode}</strong></span>
                <span className="text-[#78716C]">Policy: <strong className="text-[#7E22CE]">{traceDetail.policy_state || 'NOMINAL'}</strong></span>
                <span className="text-[#78716C]">Resilience: <strong className="text-[#15803D]">{traceDetail.resilience_state || 'SAFE'}</strong></span>
                <StatusBadge status={traceDetail.execution_status} size="sm" />
              </div>
            )}

            {/* Export & Compare Actions */}
            <div className="flex items-center space-x-2 w-full md:w-auto justify-end">
              <button
                onClick={() => setShowCompareModal(true)}
                className="inline-flex items-center space-x-1 px-3 py-1.5 bg-white hover:bg-[#F6F3EC] text-[#1C1917] border border-[#DDD6C6] rounded text-xs transition"
              >
                <GitCompare className="w-3.5 h-3.5 text-[#B45309]" />
                <span>Compare</span>
              </button>

              <button
                onClick={() => handleExport('json')}
                disabled={exporting}
                className="inline-flex items-center space-x-1 px-2.5 py-1.5 bg-white hover:bg-[#F6F3EC] text-[#1C1917] border border-[#DDD6C6] rounded text-xs transition"
                title="Export Trace JSON"
              >
                <Download className="w-3.5 h-3.5 text-[#166534]" />
                <span>JSON</span>
              </button>

              <button
                onClick={() => handleExport('csv')}
                disabled={exporting}
                className="inline-flex items-center space-x-1 px-2.5 py-1.5 bg-white hover:bg-[#F6F3EC] text-[#1C1917] border border-[#DDD6C6] rounded text-xs transition"
                title="Export Trace CSV"
              >
                <Download className="w-3.5 h-3.5 text-[#0284C7]" />
                <span>CSV</span>
              </button>
            </div>
          </div>

          {/* Non-Technical Comprehension: Explain This */}
          <ExplainThis
            title="What is a Decision Trace in Polaris-EMS?"
            whatAmILookingAt="This workspace is the 'black box flight recorder' of the energy management system. It logs every single calculation, decision, and safety check made by the software in chronological order."
            whyIsItImportant="If a generator turns on or a scientific heater turns off, human operators need to know exactly WHY. Was it a forecasted storm? A tripped sensor? A policy rule? The decision trace eliminates 'black box AI' mysteries."
            howIsItCalculated="Every calculation step creates an immutable cryptographically linked record connecting inputs to outputs."
          />

          <NextStepExplanation
            title="AUDIT TRAIL VERIFICATION"
            timeframe="Observational Pipeline Trace"
            outlook="All 7 pipeline stages (Edge Telemetry → ML Forecast → Stress Scenario → HiGHS Optimizer → Twin Replay → Resilience Calculus → Policy Governance) have completed with zero validation violations."
          />

          {/* Why This Matters */}
          <WhyThisMatters
            summary="Autonomous polar energy systems must produce tamper-evident proof for every dispatch decision. The Decision Trace captures the causal dependency DAG from sensor inputs through optimizer solve to policy enforcement."
            technicalDetail="Every execution step generates an immutable event record with cryptographic parent linkage, elapsed execution wall time, validation tier, and reason codes. Invariants ensure optimizer proposals are distinguished from physically validated twin outcomes."
            invariant="Audit Invariant: Every dispatch recommendation has a deterministic causal lineage tracing back to validated weather observations, non-confidential physical constraints, and active policy rules."
            stage="Decision Trace & Observability"
          />

          {/* Navigation View Tabs */}
          <div className="flex border-b border-[#DDD6C6] text-xs font-mono">
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-4 py-2.5 font-bold uppercase tracking-wider transition-colors border-b-2 flex items-center space-x-2 ${
                activeTab === 'timeline'
                  ? 'border-[#B45309] text-[#B45309] bg-white'
                  : 'border-transparent text-[#78716C] hover:text-[#1C1917]'
              }`}
            >
              <Clock className="w-4 h-4" />
              <span>Stage Timeline</span>
            </button>

            <button
              onClick={() => setActiveTab('graph')}
              className={`px-4 py-2.5 font-bold uppercase tracking-wider transition-colors border-b-2 flex items-center space-x-2 ${
                activeTab === 'graph'
                  ? 'border-[#B45309] text-[#B45309] bg-white'
                  : 'border-transparent text-[#78716C] hover:text-[#1C1917]'
              }`}
            >
              <Network className="w-4 h-4" />
              <span>Lineage DAG</span>
            </button>

            <button
              onClick={() => setActiveTab('explanation')}
              className={`px-4 py-2.5 font-bold uppercase tracking-wider transition-colors border-b-2 flex items-center space-x-2 ${
                activeTab === 'explanation'
                  ? 'border-[#B45309] text-[#B45309] bg-white'
                  : 'border-transparent text-[#78716C] hover:text-[#1C1917]'
              }`}
            >
              <HelpCircle className="w-4 h-4" />
              <span>"Why?" Explainer</span>
            </button>

            <button
              onClick={() => setActiveTab('comparison')}
              className={`px-4 py-2.5 font-bold uppercase tracking-wider transition-colors border-b-2 flex items-center space-x-2 ${
                activeTab === 'comparison'
                  ? 'border-[#B45309] text-[#B45309] bg-white'
                  : 'border-transparent text-[#78716C] hover:text-[#1C1917]'
              }`}
            >
              <GitCompare className="w-4 h-4" />
              <span>Decision Delta</span>
            </button>

            <button
              onClick={() => setActiveTab('raw')}
              className={`px-4 py-2.5 font-bold uppercase tracking-wider transition-colors border-b-2 flex items-center space-x-2 ${
                activeTab === 'raw'
                  ? 'border-[#B45309] text-[#B45309] bg-white'
                  : 'border-transparent text-[#78716C] hover:text-[#1C1917]'
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
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                  <Activity className="w-4 h-4 text-[#B45309]" />
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
                        className={`p-3.5 rounded border transition-all cursor-pointer font-mono text-xs ${
                          isSelected
                            ? 'bg-white border-[#B45309] shadow-md ring-1 ring-[#B45309]/30'
                            : 'bg-white border-[#DDD6C6] hover:border-[#B45309]/50'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-[10px] font-bold text-[#A8A29E]">#{idx + 1}</span>
                            <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${stageColor}`}>
                              {ev.stage}
                            </span>
                            <span className="font-bold text-[#1C1917] truncate">{ev.event_type}</span>
                          </div>

                          <div className="flex items-center space-x-2">
                            {renderValidationBadge(ev.validation_tier)}
                            <ProvenanceTag provenance={ev.provenance} size="xs" />
                          </div>
                        </div>

                        <p className="mt-2 text-[#57534E] text-xs line-clamp-2 font-sans">
                          {ev.summary}
                        </p>

                        <div className="mt-2.5 flex items-center justify-between text-[10px] text-[#78716C] pt-2 border-t border-[#F6F3EC]">
                          <span className="text-[#B45309] font-bold">{ev.reason_code}</span>
                          <span className="flex items-center gap-1 font-mono-numbers">
                            <Clock className="w-3 h-3 text-[#A8A29E]" />
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
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                  <Database className="w-4 h-4 text-[#B45309]" />
                  Stage Evidence &amp; Validation Details
                </h3>

                {selectedEvent ? (
                  <div className="p-5 rounded bg-white border border-[#DDD6C6] font-mono text-xs space-y-4 shadow-sm">
                    <div className="flex items-center justify-between pb-3 border-b border-[#DDD6C6]">
                      <div>
                        <span className="text-[10px] text-[#78716C] uppercase">Selected Event ID:</span>
                        <div className="font-bold text-[#B45309] text-xs">{selectedEvent.event_id}</div>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-[10px] text-[#78716C] uppercase">Validation Tier:</span>
                        {renderValidationBadge(selectedEvent.validation_tier)}
                      </div>
                    </div>

                    {/* Summary Card */}
                    <div className="p-3 rounded bg-[#F6F3EC] border border-[#DDD6C6] text-xs font-sans text-[#1C1917]">
                      <strong className="text-[#B45309] block font-mono text-[11px] mb-1 uppercase tracking-wider">
                        Factual Finding:
                      </strong>
                      {selectedEvent.summary}
                    </div>

                    {/* Invariant Distinction Alert */}
                    {selectedEvent.stage === 'OPTIMIZER' && (
                      <div className="p-3 rounded bg-[#E0F2FE] border border-[#BAE6FD] text-[#0369A1] text-xs font-sans">
                        <strong className="font-mono text-[#0284C7] block mb-1">PROPOSED DISPATCH:</strong>
                        This schedule represents optimizer-proposed dispatch under mathematical constraints. Physical validity is proven in the downstream Digital Twin stage.
                      </div>
                    )}

                    {selectedEvent.stage === 'TWIN_REPLAY' && (
                      <div className="p-3 rounded bg-[#EBF7F0] border border-[#BBF7D0] text-[#166534] text-xs font-sans">
                        <strong className="font-mono text-[#15803D] block mb-1">PHYSICALLY VALIDATED:</strong>
                        Replayed through high-fidelity polar battery, diesel, and thermal physics equations to verify zero thermal or capacity breaches.
                      </div>
                    )}

                    {selectedEvent.stage === 'RESILIENCE' && (
                      <div className="p-3 rounded bg-[#FEF3C7] border border-[#FDE68A] text-[#92400E] text-xs font-sans">
                        <strong className="font-mono text-[#B45309] block mb-1">ESTIMATED RECOVERY HORIZON:</strong>
                        Assessed 5 survival dimensions. Projected recovery pathways carry ESTIMATED validation tier pending real-world confirmation.
                      </div>
                    )}

                    {/* Observed Outputs */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-bold text-[#1C1917] uppercase tracking-wider">
                          Observed Stage Outputs:
                        </span>
                        <button
                          onClick={() => inspectEvidence({
                            value: JSON.stringify(selectedEvent.outputs),
                            source: `${selectedEvent.stage}::${selectedEvent.event_type}`,
                            provenance: selectedEvent.provenance,
                            timestamp: selectedEvent.timestamp,
                            station: traceDetail.station_id,
                            model: selectedEvent.engine_version,
                            validationState: selectedEvent.validation_tier,
                            uncertaintyInterval: 'Exact Computed Event',
                            governingInvariant: `Reason Code: ${selectedEvent.reason_code}. Stage verified under non-confidential telemetry protocol.`
                          })}
                          className="text-[10px] font-mono text-[#0284C7] hover:underline"
                        >
                          Inspect Full Evidence →
                        </button>
                      </div>
                      <div className="p-3 rounded bg-[#F6F3EC] border border-[#DDD6C6] space-y-1.5 text-[11px]">
                        {Object.entries(selectedEvent.outputs).map(([k, v]) => (
                          <div key={k} className="flex justify-between items-center py-0.5 border-b border-[#DDD6C6]/50 last:border-0">
                            <span className="text-[#78716C]">{k}:</span>
                            <span className="text-[#1C1917] font-bold max-w-[240px] truncate text-right font-mono-numbers">
                              {typeof v === 'boolean' ? (v ? 'TRUE' : 'FALSE') : String(v)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Inputs & Lineage Metadata */}
                    <div className="pt-2 border-t border-[#DDD6C6] text-[10px] text-[#78716C] space-y-1">
                      <div>Parent Event: <span className="text-[#1C1917]">{selectedEvent.parent_event_id || 'NONE (ROOT NODE)'}</span></div>
                      <div>Engine Version: <span className="text-[#1C1917]">{selectedEvent.engine_version}</span></div>
                      <div>Timestamp: <span className="text-[#1C1917] font-mono-numbers">{selectedEvent.timestamp}</span></div>
                      <div>Reason Code: <span className="text-[#B45309] font-bold">{selectedEvent.reason_code}</span></div>
                    </div>
                  </div>
                ) : (
                  <div className="p-8 text-center text-[#A8A29E] font-mono text-xs border border-dashed border-[#DDD6C6] rounded bg-white">
                    Select an event to inspect its inputs, outputs, and validation tier.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: DAG Lineage Visualization */}
          {activeTab === 'graph' && traceDetail && (
            <div className="editorial-sheet p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-[#1C1917]">
                    Decision Lineage Dependency DAG
                  </h3>
                  <p className="text-xs text-[#57534E] mt-0.5">
                    Parent-to-child sequential validation graph showing exact execution order and terminal state.
                  </p>
                </div>
                <div className="text-xs font-mono text-[#78716C]">
                  Terminal Status: <strong className="text-[#166534]">{traceDetail.execution_status}</strong>
                </div>
              </div>

              {/* Graphical Lineage Sequence */}
              <div className="flex flex-col md:flex-row items-center justify-between gap-3 p-6 bg-white rounded border border-[#DDD6C6] overflow-x-auto shadow-sm">
                {traceDetail.events.map((ev, idx) => (
                  <React.Fragment key={ev.event_id}>
                    <div 
                      onClick={() => {
                        setSelectedEventId(ev.event_id);
                        setActiveTab('timeline');
                      }}
                      className={`p-3.5 rounded border text-center font-mono cursor-pointer transition-all min-w-[130px] shrink-0 ${
                        getStageColor(ev.stage)
                      }`}
                    >
                      <div className="text-[10px] text-[#78716C] font-bold">NODE #{idx + 1}</div>
                      <div className="text-xs font-bold uppercase mt-1">{ev.stage}</div>
                      <div className="text-[9px] text-[#57534E] mt-1 truncate">{ev.event_type}</div>
                      <div className="mt-2 text-[10px] font-bold text-[#1C1917]">
                        {ev.status}
                      </div>
                    </div>

                    {idx < traceDetail.events.length - 1 && (
                      <div className="text-[#A8A29E] hidden md:block">
                        <ArrowRight className="w-5 h-5 text-[#B45309]" />
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>

              <div className="p-4 rounded bg-white border border-[#DDD6C6] font-mono text-xs text-[#78716C] space-y-2">
                <span className="font-bold text-[#1C1917] block uppercase">DAG Adjacency Map:</span>
                <pre className="text-[11px] text-[#57534E] overflow-x-auto p-2 bg-[#F6F3EC] rounded border border-[#DDD6C6]">
                  {JSON.stringify(traceDetail.lineage_graph, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* TAB 3: "Why?" Explanation Panel */}
          {activeTab === 'explanation' && explanation && (
            <div className="editorial-sheet p-6 space-y-6">
              {/* Headline Banner */}
              <div className="p-5 rounded bg-[#FEF3C7] border border-[#FDE68A]">
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#B45309] font-bold block mb-1">
                  Executive Decision Summary:
                </span>
                <p className="text-base font-serif font-medium text-[#1C1917] leading-relaxed">
                  {explanation.headline}
                </p>
              </div>

              {/* Core "Why?" Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
                <div className="p-4 rounded bg-white border border-[#DDD6C6] space-y-2 shadow-sm">
                  <div className="text-[#C2410C] font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5" />
                    Why This State?
                  </div>
                  <p className="text-[#57534E] font-sans text-xs leading-relaxed">
                    {explanation.why_this_state}
                  </p>
                </div>

                <div className="p-4 rounded bg-white border border-[#DDD6C6] space-y-2 shadow-sm">
                  <div className="text-[#7E22CE] font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Why This Policy?
                  </div>
                  <p className="text-[#57534E] font-sans text-xs leading-relaxed">
                    {explanation.why_this_policy}
                  </p>
                </div>

                <div className="p-4 rounded bg-white border border-[#DDD6C6] space-y-2 shadow-sm">
                  <div className="text-[#0F766E] font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5" />
                    Why This Schedule?
                  </div>
                  <p className="text-[#57534E] font-sans text-xs leading-relaxed">
                    {explanation.why_this_schedule}
                  </p>
                </div>
              </div>

              {/* Epistemic Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
                <div className="p-4 rounded bg-white border border-[#DDD6C6] space-y-2 shadow-sm">
                  <span className="text-[#78716C] uppercase font-bold block text-[11px]">
                    What Data Was Used?
                  </span>
                  <ul className="space-y-1 text-[#57534E] list-disc list-inside font-sans text-xs">
                    {explanation.what_data_used.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded bg-white border border-[#DDD6C6] space-y-2 shadow-sm">
                  <span className="text-[#166534] uppercase font-bold block text-[11px]">
                    What Was Physically Validated?
                  </span>
                  <ul className="space-y-1 text-[#57534E] list-disc list-inside font-sans text-xs">
                    {explanation.what_was_validated.map((v, i) => (
                      <li key={i}>{v}</li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded bg-white border border-[#DDD6C6] space-y-2 shadow-sm">
                  <span className="text-[#92400E] uppercase font-bold block text-[11px]">
                    What Remains Estimated?
                  </span>
                  <ul className="space-y-1 text-[#57534E] list-disc list-inside font-sans text-xs">
                    {explanation.what_remains_estimated.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Recommended Next Action */}
              <div className="p-4 rounded bg-white border border-[#DDD6C6] font-mono text-xs shadow-sm">
                <span className="text-[#7E22CE] uppercase font-bold block text-[11px] mb-1">
                  What Happens Next? (Operational Handoff)
                </span>
                <p className="text-[#1C1917] font-sans text-xs leading-relaxed">
                  {explanation.what_is_next}
                </p>
              </div>
            </div>
          )}

          {/* TAB 4: Decision Delta / Comparison */}
          {activeTab === 'comparison' && (
            <div className="editorial-sheet p-6 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                    <GitCompare className="w-4 h-4 text-[#B45309]" />
                    Factual Decision Delta (Before vs After)
                  </h3>
                  <p className="text-xs text-[#57534E] mt-0.5">
                    Compares current trace against a baseline or previous decision without evaluative bias.
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono text-[#78716C]">Compare With:</span>
                  <select
                    value={compareTraceId || ''}
                    onChange={(e) => handleCompare(e.target.value)}
                    className="bg-white border border-[#DDD6C6] text-[#1C1917] text-xs px-3 py-1 rounded"
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
                  <div className="p-4 rounded bg-white border border-[#DDD6C6] text-xs font-sans text-[#1C1917] shadow-sm">
                    <strong className="text-[#B45309] font-mono text-[11px] block uppercase mb-1">
                      Comparative Narrative:
                    </strong>
                    {comparisonDelta.summary_narrative}
                  </div>

                  {/* State Transitions Table */}
                  <div className="p-4 rounded bg-white border border-[#DDD6C6] font-mono text-xs space-y-3 shadow-sm">
                    <span className="font-bold text-[#1C1917] uppercase block text-[11px]">
                      Categorical State Transitions:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                      {Object.entries(comparisonDelta.state_transitions).map(([key, [prev, curr]]) => (
                        <div key={key} className="p-3 rounded bg-[#F6F3EC] border border-[#DDD6C6]">
                          <span className="text-[10px] text-[#78716C] uppercase block">{key}:</span>
                          <div className="mt-1 flex items-center space-x-2">
                            <span className="text-[#A8A29E] line-through">{prev}</span>
                            <ArrowRight className="w-3.5 h-3.5 text-[#B45309]" />
                            <span className="text-[#1C1917] font-bold">{curr}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Numerical Deltas */}
                  <div className="p-4 rounded bg-white border border-[#DDD6C6] font-mono text-xs space-y-3 shadow-sm">
                    <span className="font-bold text-[#1C1917] uppercase block text-[11px]">
                      Numerical Metric Shifts:
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {Object.entries(comparisonDelta.numerical_deltas).map(([k, val]) => (
                        <div key={k} className="p-3 rounded bg-[#F6F3EC] border border-[#DDD6C6] flex justify-between items-center">
                          <span className="text-[#78716C] text-[11px]">{k}:</span>
                          <span className={`font-bold font-mono-numbers ${val > 0 ? 'text-[#B45309]' : val < 0 ? 'text-[#166534]' : 'text-[#1C1917]'}`}>
                            {val > 0 ? `+${val.toFixed(2)}` : val.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-[#A8A29E] font-mono text-xs border border-dashed border-[#DDD6C6] rounded bg-white">
                  Select a comparison trace from the dropdown above to compute the factual decision delta.
                </div>
              )}
            </div>
          )}

          {/* TAB 5: Raw JSON Record */}
          {activeTab === 'raw' && traceDetail && (
            <div className="editorial-sheet p-6 font-mono text-xs">
              <div className="flex justify-between items-center pb-2 border-b border-[#DDD6C6] mb-3">
                <span className="text-[#1C1917] font-bold uppercase">
                  Canonical Machine Trace JSON Record ({traceDetail.decision_trace_id})
                </span>
                <button
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(traceDetail, null, 2))}
                  className="px-2.5 py-1 bg-white hover:bg-[#F6F3EC] text-[#1C1917] rounded text-[11px] border border-[#DDD6C6] shadow-sm"
                >
                  Copy JSON
                </button>
              </div>
              <pre className="p-4 bg-white rounded border border-[#DDD6C6] overflow-x-auto text-[#1C1917] text-[11px] max-h-[500px]">
                {JSON.stringify(traceDetail, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Modal: Compare Trace Selector */}
      {showCompareModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white border border-[#DDD6C6] rounded-xl max-w-md w-full p-5 space-y-4 font-mono text-xs shadow-2xl">
            <div className="flex justify-between items-center pb-2 border-b border-[#DDD6C6]">
              <h4 className="font-bold text-[#1C1917] uppercase">Select Trace to Compare</h4>
              <button
                onClick={() => setShowCompareModal(false)}
                className="text-[#78716C] hover:text-[#1C1917]"
              >
                ✕
              </button>
            </div>

            <p className="text-[#57534E] text-[11px] font-sans">
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
                      ? 'bg-[#F6F3EC] text-[#A8A29E] border-[#DDD6C6] cursor-not-allowed'
                      : 'bg-white hover:bg-[#F6F3EC] text-[#1C1917] border-[#DDD6C6]'
                  }`}
                >
                  <div>
                    <div className="font-bold text-[#B45309]">{tr.decision_trace_id}</div>
                    <div className="text-[10px] text-[#78716C] font-mono-numbers">{new Date(tr.creation_timestamp).toLocaleString()}</div>
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
