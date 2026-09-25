import React, { useState, useEffect } from 'react';
import { useStation } from '../context/StationContext';
import { useEvidence } from '../context/EvidenceContext';
import { edgeApi } from '../api/client';
import { 
  EdgeStateResponseData, 
  DeviceSummary, 
  DeviceHealthItem, 
  ConnectivityResponseData,
  SyncResponseData
} from '../api/types';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { WhyThisMatters } from '../components/common/WhyThisMatters';
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { JargonTooltip } from '../components/common/JargonTooltip';
import { 
  Radio, 
  Cpu, 
  Activity, 
  Wifi, 
  WifiOff, 
  RefreshCw, 
  Database, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Layers, 
  ArrowUpDown, 
  Info 
} from 'lucide-react';

export const EdgeView: React.FC = () => {
  const { stationId, currentStation } = useStation();
  const { inspectEvidence } = useEvidence();

  const [stateData, setStateData] = useState<EdgeStateResponseData | null>(null);
  const [devices, setDevices] = useState<DeviceSummary[]>([]);
  const [healthItems, setHealthItems] = useState<DeviceHealthItem[]>([]);
  const [connData, setConnData] = useState<ConnectivityResponseData | null>(null);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResponseData | null>(null);
  
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [simCondition, setSimCondition] = useState<string>('NORMAL');
  const [selectedDeviceType, setSelectedDeviceType] = useState<string>('ALL');

  const activeStation = stationId || currentStation || 'BHARATI';

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [stRes, devRes, hlRes, cnRes] = await Promise.all([
        edgeApi.getState(activeStation),
        edgeApi.getDevices(activeStation),
        edgeApi.getHealth(activeStation),
        edgeApi.getConnectivity(activeStation),
      ]);

      if (stRes.data) setStateData(stRes.data);
      if (devRes.data) setDevices(devRes.data);
      if (hlRes.data) setHealthItems(hlRes.data);
      if (cnRes.data) setConnData(cnRes.data);
    } catch (err) {
      console.error('Failed to load edge intelligence data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeStation]);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const res = await edgeApi.syncBuffer(activeStation);
      if (res.data) {
        setLastSyncResult(res.data);
        await fetchData();
      }
    } catch (err) {
      console.error('Sync failed:', err);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSimulateCondition = async (cond: string) => {
    setSimCondition(cond);
    try {
      await edgeApi.simulateCondition(activeStation, cond);
      await fetchData();
    } catch (err) {
      console.error('Failed to apply simulation condition:', err);
    }
  };

  const filteredDevices = selectedDeviceType === 'ALL'
    ? devices
    : devices.filter(d => d.device_type === selectedDeviceType);

  const getEdgeModeBadge = (mode?: string) => {
    switch (mode) {
      case 'CONNECTED_OPERATION':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-[#EBF7F0] text-[#166534] border border-[#BBF7D0]">CONNECTED OPERATION</span>;
      case 'DEGRADED_CONNECTIVITY':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-[#FEF3C7] text-[#92400E] border border-[#FDE68A]">DEGRADED CONNECTIVITY</span>;
      case 'OFFLINE_EDGE':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-[#FEE2E2] text-[#991B1B] border border-[#FECACA]">OFFLINE EDGE MODE</span>;
      case 'RECOVERY_SYNC':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-[#E0F2FE] text-[#0369A1] border border-[#BAE6FD]">RECOVERY RECONCILIATION</span>;
      case 'SAFE_HOLD':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-[#F3E8FF] text-[#6B21A8] border border-[#E9D5FF]">SAFE HOLD POSTURE</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-[#F6F3EC] text-[#78716C] border border-[#DDD6C6]">UNKNOWN</span>;
    }
  };

  const getConnBadge = (conn?: string) => {
    switch (conn) {
      case 'CONNECTED':
        return <span className="flex items-center space-x-1.5 text-xs text-[#166534] font-medium"><Wifi className="w-3.5 h-3.5" /><span>Active Link</span></span>;
      case 'DEGRADED':
        return <span className="flex items-center space-x-1.5 text-xs text-[#B45309] font-medium"><Activity className="w-3.5 h-3.5" /><span>Degraded (High Loss)</span></span>;
      case 'OFFLINE':
        return <span className="flex items-center space-x-1.5 text-xs text-[#991B1B] font-medium"><WifiOff className="w-3.5 h-3.5" /><span>Offline / Blackout</span></span>;
      case 'RECONNECTING':
        return <span className="flex items-center space-x-1.5 text-xs text-[#0284C7] font-medium"><RefreshCw className="w-3.5 h-3.5 animate-spin" /><span>Handshake / Sync</span></span>;
      default:
        return <span className="text-xs text-[#78716C]">Unknown</span>;
    }
  };

  const getHealthBadge = (health?: string) => {
    switch (health) {
      case 'HEALTHY':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-[#EBF7F0] text-[#166534] border border-[#BBF7D0]">HEALTHY</span>;
      case 'DEGRADED':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-[#FEF3C7] text-[#92400E] border border-[#FDE68A]">DEGRADED</span>;
      case 'UNAVAILABLE':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-[#F6F3EC] text-[#78716C] border border-[#DDD6C6]">UNAVAILABLE</span>;
      case 'FAULT':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-[#FEE2E2] text-[#991B1B] border border-[#FECACA]">FAULT</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-[#F6F3EC] text-[#A8A29E]">UNKNOWN</span>;
    }
  };

  return (
    <div className="p-4 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Editorial Header */}
      <div className="border-b border-[#DDD6C6] pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-[#78716C] mb-2">
            <span>08 Edge Intelligence & Devices</span>
            <span>•</span>
            <ProvenanceTag provenance="SIMULATED" size="xs" />
          </div>
          <h1 className="font-serif text-3xl lg:text-4xl text-[#1C1917] tracking-tight">
            Edge Intelligence & Field Fleet
          </h1>
          <p className="text-sm text-[#57534E] font-sans mt-2 max-w-2xl">
            Station <strong className="text-[#1C1917]">{activeStation}</strong> local node telemetry normalization, data quality validation, device fleet health, and bounded buffer reconciliation.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {getEdgeModeBadge(stateData?.edge_mode)}
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded bg-white hover:bg-[#F6F3EC] text-[#1C1917] border border-[#DDD6C6] transition shadow-sm"
            title="Refresh local edge state"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleSync}
            disabled={isSyncing || (stateData?.buffer_depth === 0 && !connData?.sync_in_progress)}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded bg-[#B45309] hover:bg-[#92400E] text-white transition shadow-sm disabled:opacity-50"
            title="Reconcile buffered telemetry with central backend"
          >
            <ArrowUpDown className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
            <span>Reconcile Buffer</span>
          </button>
        </div>
      </div>

      {/* Non-Technical Comprehension: Explain This */}
      <ExplainThis
        title="What does Edge Intelligence mean in Antarctica?"
        whatAmILookingAt="This engineering console monitors the computers and sensors physically located inside the polar station, tracking communications health, telemetry queues, and connected equipment."
        whyIsItImportant="Antarctic stations frequently lose satellite connections during blizzard whiteouts or solar storms. 'Edge computing' ensures that the software running inside the station continues controlling life-support power without needing an internet connection."
        howIsItCalculated="Telemetry is held in bounded FIFO buffer queues with SHA-256 deduplication and automatically reconciled once satellite links re-establish."
      />

      <NextStepExplanation
        title="COMMUNICATIONS & RECONCILIATION OUTLOOK"
        timeframe="Live Edge Buffer Status"
        outlook={
          stateData?.edge_mode === 'OFFLINE_EDGE'
            ? 'Station is currently operating in autonomous offline mode. All local sensors are safely logging to high-durability internal memory.'
            : 'Station communications uplink is active. Telemetry buffer queue depth is nominal with zero dropped frames.'
        }
      />

      {/* Operational Diagnostics Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-3 rounded border border-[#DDD6C6] shadow-sm">
          <span className="text-[10px] text-[#78716C] block font-mono uppercase tracking-wider">Connectivity</span>
          <div className="mt-1">{getConnBadge(connData?.connectivity_state)}</div>
        </div>

        <div className="bg-white p-3 rounded border border-[#DDD6C6] shadow-sm">
          <span className="text-[10px] text-[#78716C] block font-mono uppercase tracking-wider">Fallback Posture</span>
          <span className="text-xs font-semibold text-[#B45309] block mt-1 truncate" title={stateData?.fallback_posture}>
            {stateData?.fallback_posture || 'HOLD_LAST_STATE'}
          </span>
        </div>

        <div className="bg-white p-3 rounded border border-[#DDD6C6] shadow-sm">
          <span className="text-[10px] text-[#78716C] block font-mono uppercase tracking-wider">Local Buffer Queue</span>
          <div className="flex items-center space-x-1 mt-1">
            <Database className="w-3.5 h-3.5 text-[#0284C7]" />
            <span className="text-xs font-bold text-[#1C1917] font-mono-numbers">
              {stateData?.buffer_depth ?? 0} <span className="text-[10px] font-normal text-[#78716C]">items</span>
            </span>
          </div>
        </div>

        <div className="bg-white p-3 rounded border border-[#DDD6C6] shadow-sm">
          <span className="text-[10px] text-[#78716C] block font-mono uppercase tracking-wider">Fleet Devices</span>
          <span className="text-xs font-semibold text-[#1C1917] block mt-1 font-mono-numbers">
            {stateData?.healthy_devices_count ?? 0} <span className="text-[#A8A29E] font-normal">/</span> {stateData?.active_devices_count ?? 0} <span className="text-[#166534] font-normal">Healthy</span>
          </span>
        </div>

        <div className="bg-white p-3 rounded border border-[#DDD6C6] shadow-sm">
          <span className="text-[10px] text-[#78716C] block font-mono uppercase tracking-wider">Packet Loss Rate</span>
          <span className="text-xs font-semibold text-[#1C1917] block mt-1 font-mono-numbers">
            {connData?.packet_loss_pct ?? 0}%
          </span>
        </div>

        <div className="bg-white p-3 rounded border border-[#DDD6C6] shadow-sm">
          <span className="text-[10px] text-[#78716C] block font-mono uppercase tracking-wider">Sync Freshness</span>
          <div className="flex items-center space-x-1 mt-1">
            <Clock className="w-3.5 h-3.5 text-[#78716C]" />
            <span className="text-xs text-[#57534E] font-mono font-mono-numbers">
              {stateData?.sync_freshness_sec != null ? `${stateData.sync_freshness_sec}s ago` : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Why This Matters */}
      <WhyThisMatters
        summary="Antarctic station communication links experience frequent geomagnetic and weather-induced outages. The local Edge layer buffers telemetry, maintains safe operation, and rejects stale sensor readings until connectivity is restored."
        technicalDetail="Local edge nodes buffer high-frequency telemetry in an in-memory ring buffer (up to 10,000 items). Upon satcom reconnection, a deterministic three-way handshake reconciles missing timestamps without overwriting newer central records."
        invariant="Edge Safety Boundary: Local edge nodes never solve global dispatch optimization or actuate generators independently. They fall back to HOLD_LAST_VALIDATED_STATE or SAFE_HOLD until central policy and optimization handoffs resume."
        stage="Edge & Device Fleet Intelligence"
      />

      {/* Field Connectivity & Fault Diagnostics Harness */}
      <div className="editorial-sheet p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-[#B45309]" />
            <h2 className="text-xs font-semibold text-[#1C1917] uppercase tracking-wider font-mono">
              Field Connectivity &amp; Fault Diagnostics Harness
            </h2>
          </div>
          <span className="text-[10px] text-[#78716C] font-mono">
            PROTOCOL TESTING // VERIFIED EDGE HARNESS
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { id: 'NORMAL', label: 'Nominal Field (Connected)', desc: 'Full satcom link, normal reporting' },
            { id: 'DEGRADED', label: 'Storm Degradation', desc: '45% packet loss, delayed heartbeat' },
            { id: 'OFFLINE', label: 'Satcom Blackout', desc: 'Link offline, local buffer queue growth' },
            { id: 'SAFE_HOLD', label: 'Force Safe Hold', desc: 'Life-safety posture, noncritical shed' },
          ].map((cond) => (
            <button
              key={cond.id}
              onClick={() => handleSimulateCondition(cond.id)}
              className={`p-3 rounded text-left border transition ${
                simCondition === cond.id
                  ? 'bg-[#FEF3C7] border-[#B45309] text-[#92400E] shadow-sm'
                  : 'bg-white border-[#DDD6C6] text-[#57534E] hover:border-[#B45309]/50'
              }`}
            >
              <div className="font-semibold text-xs text-[#1C1917]">{cond.label}</div>
              <div className="text-[11px] text-[#78716C] mt-1">{cond.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Reconciliation Audit Log (if recently synced) */}
      {lastSyncResult && (
        <div className="editorial-sheet p-6 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-[#166534]" />
              <h3 className="text-xs font-bold text-[#1C1917]">
                Reconciliation Audit Report (Executed in {lastSyncResult.execution_duration_ms}ms)
              </h3>
            </div>
            <span className="text-[11px] font-mono text-[#0284C7]">
              Processed: {lastSyncResult.processed_count} | Duplicates Dropped: {lastSyncResult.duplicate_count} | Gaps Flagged: {lastSyncResult.gap_count}
            </span>
          </div>

          <div className="max-h-40 overflow-y-auto space-y-1.5 text-xs font-mono pr-2">
            {lastSyncResult.audit_log.map((entry, idx) => (
              <div key={idx} className="bg-white p-2.5 rounded border border-[#DDD6C6] flex items-center justify-between text-[11px]">
                <div className="flex items-center space-x-2">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                    entry.action === 'ACCEPTED_NEW' ? 'bg-[#EBF7F0] text-[#166534]' :
                    entry.action === 'DUPLICATE_DROPPED' ? 'bg-[#F6F3EC] text-[#78716C]' :
                    entry.action === 'GAP_FLAGGED' ? 'bg-[#FEF3C7] text-[#92400E]' :
                    'bg-[#E0F2FE] text-[#0369A1]'
                  }`}>
                    {entry.action}
                  </span>
                  <span className="text-[#1C1917]">{entry.device_id}::{entry.channel}</span>
                </div>
                <span className="text-[#78716C] text-[10px]">{entry.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Device Fleet Health & Telemetry Grid */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-[#B45309]" />
            <h2 className="text-sm font-bold text-[#1C1917] font-mono uppercase tracking-wide">
              Station Device Fleet Catalog ({filteredDevices.length} Devices)
            </h2>
          </div>

          {/* Device Type Filter */}
          <div className="flex flex-wrap gap-1">
            {['ALL', 'DIESEL_GENERATOR', 'SOLAR', 'WIND', 'BATTERY', 'THERMAL', 'WEATHER', 'POWER_METER', 'FUEL'].map((type) => (
              <button
                key={type}
                onClick={() => setSelectedDeviceType(type)}
                className={`px-2.5 py-1 rounded text-[11px] font-mono transition ${
                  selectedDeviceType === type
                    ? 'bg-[#1C1917] text-white font-semibold'
                    : 'bg-white text-[#78716C] border border-[#DDD6C6] hover:bg-[#F6F3EC]'
                }`}
              >
                {type === 'ALL' ? 'All Classes' : type.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Device Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDevices.map((dev) => {
            const health = healthItems.find(h => h.device_id === dev.device_id);
            return (
              <div 
                key={dev.device_id}
                className="bg-white border border-[#DDD6C6] rounded p-4 hover:border-[#B45309]/50 transition-colors shadow-sm flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-mono text-[#B45309] uppercase tracking-wider block font-semibold">
                        {dev.device_type}
                      </span>
                      <h3 className="text-sm font-semibold text-[#1C1917] mt-0.5">
                        {dev.name}
                      </h3>
                      <span className="text-[11px] font-mono text-[#78716C]">
                        ID: {dev.device_id}
                      </span>
                    </div>
                    {getHealthBadge(health?.health_state || dev.health_state)}
                  </div>

                  {/* Rated Capacity & Protocol */}
                  <div className="mt-3 pt-3 border-t border-[#DDD6C6] grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[10px] text-[#78716C] block">Rated Capacity</span>
                      <span className="font-mono font-mono-numbers text-[#1C1917]">
                        {dev.rated_capacity != null ? `${dev.rated_capacity} ${dev.unit}` : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#78716C] block">Bus / Protocol</span>
                      <span className="font-mono text-[#57534E] text-[11px] truncate block" title={dev.source_metadata.protocol}>
                        {dev.source_metadata.protocol || 'LOCAL_BUS'}
                      </span>
                    </div>
                  </div>

                  {/* Telemetry Channels */}
                  <div className="mt-3">
                    <span className="text-[10px] text-[#78716C] font-mono uppercase block mb-1">
                      Validated Channels ({dev.telemetry_channels.length})
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {dev.telemetry_channels.map(ch => {
                        const readingKey = `${dev.device_id}::${ch.channel}`;
                        const reading = stateData?.latest_readings?.[readingKey];
                        return (
                          <button 
                            key={ch.channel} 
                            onClick={() => inspectEvidence({
                              value: reading?.value != null ? `${reading.value} ${ch.unit}` : `${ch.min_val}–${ch.max_val} ${ch.unit}`,
                              source: `${dev.name} [${ch.channel}]`,
                              provenance: 'SIMULATED',
                              timestamp: reading?.timestamp || new Date().toISOString(),
                              station: activeStation,
                              model: `${dev.device_type} Transducer Driver`,
                              validationState: 'VALIDATED',
                              uncertaintyInterval: `Operational bounds [${ch.min_val}, ${ch.max_val}] ${ch.unit}`,
                              governingInvariant: 'Hardware telemetry bounds check verified: readings outside operational range trigger DEGRADED device state.'
                            })}
                            className="bg-[#F6F3EC] px-2 py-1 rounded text-[10px] border border-[#DDD6C6] flex items-center space-x-1.5 hover:border-[#B45309] transition-colors"
                          >
                            <span className="text-[#78716C]">{ch.channel}:</span>
                            <span className="font-mono font-semibold text-[#B45309] font-mono-numbers">
                              {reading?.value != null ? `${reading.value} ${ch.unit}` : `${ch.min_val}–${ch.max_val} ${ch.unit}`}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Health Signals */}
                {health?.contributing_signals && health.contributing_signals.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-[#DDD6C6] text-[10px] text-[#78716C] flex items-center space-x-1">
                    <Activity className="w-3 h-3 text-[#B45309]" />
                    <span className="truncate">Signals: {health.contributing_signals.join(', ')}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Architectural Disclaimer Banner */}
      <div className="bg-[#F6F3EC] border border-[#DDD6C6] rounded p-4 flex items-start space-x-3 text-xs text-[#57534E]">
        <Info className="w-4 h-4 text-[#B45309] flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-[#1C1917]">Edge Decision Boundary & Field Safety:</span>
          <p className="mt-0.5">
            Polaris-EMS Edge Layer handles telemetry normalization, data quality validation, and local state buffering during communication dropouts. It operates under safe fallback postures (e.g. HOLD_LAST_VALIDATED_STATE, SAFE_HOLD) and <strong>does not solve mathematical optimization problems or actuate physical generators independently</strong>. When connectivity is verified, dispatch requests are routed to the central Dispatch Optimizer and Policy Governance pipeline.
          </p>
        </div>
      </div>
    </div>
  );
};
