import React, { useState, useEffect } from 'react';
import { useStation } from '../context/StationContext';
import { edgeApi } from '../api/client';
import { 
  EdgeStateResponseData, 
  DeviceSummary, 
  DeviceHealthItem, 
  ConnectivityResponseData,
  SyncResponseData
} from '../api/types';
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
  Server, 
  ShieldCheck, 
  Layers, 
  ArrowUpDown, 
  Info 
} from 'lucide-react';

export const EdgeView: React.FC = () => {
  const { stationId } = useStation();

  const [stateData, setStateData] = useState<EdgeStateResponseData | null>(null);
  const [devices, setDevices] = useState<DeviceSummary[]>([]);
  const [healthItems, setHealthItems] = useState<DeviceHealthItem[]>([]);
  const [connData, setConnData] = useState<ConnectivityResponseData | null>(null);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResponseData | null>(null);
  
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [simCondition, setSimCondition] = useState<string>('NORMAL');
  const [selectedDeviceType, setSelectedDeviceType] = useState<string>('ALL');

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [stRes, devRes, hlRes, cnRes] = await Promise.all([
        edgeApi.getState(stationId),
        edgeApi.getDevices(stationId),
        edgeApi.getHealth(stationId),
        edgeApi.getConnectivity(stationId),
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
  }, [stationId]);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const res = await edgeApi.syncBuffer(stationId);
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
      await edgeApi.simulateCondition(stationId, cond);
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
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">CONNECTED OPERATION</span>;
      case 'DEGRADED_CONNECTIVITY':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">DEGRADED CONNECTIVITY</span>;
      case 'OFFLINE_EDGE':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">OFFLINE EDGE MODE</span>;
      case 'RECOVERY_SYNC':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">RECOVERY RECONCILIATION</span>;
      case 'SAFE_HOLD':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">SAFE HOLD POSTURE</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-polar-800 text-polar-300">UNKNOWN</span>;
    }
  };

  const getConnBadge = (conn?: string) => {
    switch (conn) {
      case 'CONNECTED':
        return <span className="flex items-center space-x-1.5 text-xs text-emerald-400 font-medium"><Wifi className="w-3.5 h-3.5" /><span>Active Link</span></span>;
      case 'DEGRADED':
        return <span className="flex items-center space-x-1.5 text-xs text-amber-400 font-medium"><Activity className="w-3.5 h-3.5" /><span>Degraded (High Loss)</span></span>;
      case 'OFFLINE':
        return <span className="flex items-center space-x-1.5 text-xs text-rose-400 font-medium"><WifiOff className="w-3.5 h-3.5" /><span>Offline / Blackout</span></span>;
      case 'RECONNECTING':
        return <span className="flex items-center space-x-1.5 text-xs text-cyan-400 font-medium"><RefreshCw className="w-3.5 h-3.5 animate-spin" /><span>Handshake / Sync</span></span>;
      default:
        return <span className="text-xs text-polar-400">Unknown</span>;
    }
  };

  const getHealthBadge = (health?: string) => {
    switch (health) {
      case 'HEALTHY':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">HEALTHY</span>;
      case 'DEGRADED':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">DEGRADED</span>;
      case 'UNAVAILABLE':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-polar-700/50 text-polar-300 border border-polar-600">UNAVAILABLE</span>;
      case 'FAULT':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">FAULT</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-polar-800 text-polar-400">UNKNOWN</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Operational Posture Header */}
      <div className="bg-polar-900/80 border border-polar-800 rounded-xl p-5 backdrop-blur shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="p-3 bg-cyan-950/60 border border-cyan-800/40 rounded-lg text-cyan-400">
              <Radio className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h1 className="text-xl font-bold text-polar-100 tracking-tight">
                  Edge & Field Device Intelligence
                </h1>
                {getEdgeModeBadge(stateData?.edge_mode)}
              </div>
              <p className="text-xs text-polar-400 mt-1 max-w-2xl">
                Station <strong className="text-polar-200">{stationId}</strong> local node telemetry normalization, data quality validation, device fleet health, and bounded buffer reconciliation.
              </p>
            </div>
          </div>

          {/* Quick Actions & Simulation Control */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={fetchData}
              disabled={isLoading}
              className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-polar-800 hover:bg-polar-700 text-polar-200 border border-polar-700 transition"
              title="Refresh local edge state"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>

            <button
              onClick={handleSync}
              disabled={isSyncing || (stateData?.buffer_depth === 0 && !connData?.sync_in_progress)}
              className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white transition disabled:opacity-50"
              title="Reconcile buffered telemetry with central backend"
            >
              <ArrowUpDown className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>Reconcile Buffer</span>
            </button>
          </div>
        </div>

        {/* Operational Diagnostics Ribbon */}
        <div className="mt-4 pt-4 border-t border-polar-800/80 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
          <div className="bg-polar-950/60 p-2.5 rounded-lg border border-polar-800">
            <span className="text-[10px] text-polar-400 block font-mono uppercase tracking-wider">Connectivity</span>
            <div className="mt-1">{getConnBadge(connData?.connectivity_state)}</div>
          </div>

          <div className="bg-polar-950/60 p-2.5 rounded-lg border border-polar-800">
            <span className="text-[10px] text-polar-400 block font-mono uppercase tracking-wider">Fallback Posture</span>
            <span className="text-xs font-semibold text-amber-300 block mt-1 truncate" title={stateData?.fallback_posture}>
              {stateData?.fallback_posture || 'HOLD_LAST_STATE'}
            </span>
          </div>

          <div className="bg-polar-950/60 p-2.5 rounded-lg border border-polar-800">
            <span className="text-[10px] text-polar-400 block font-mono uppercase tracking-wider">Local Buffer Queue</span>
            <div className="flex items-center space-x-1 mt-1">
              <Database className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-xs font-bold text-polar-200">
                {stateData?.buffer_depth ?? 0} <span className="text-[10px] font-normal text-polar-400">items</span>
              </span>
            </div>
          </div>

          <div className="bg-polar-950/60 p-2.5 rounded-lg border border-polar-800">
            <span className="text-[10px] text-polar-400 block font-mono uppercase tracking-wider">Fleet Devices</span>
            <span className="text-xs font-semibold text-polar-200 block mt-1">
              {stateData?.healthy_devices_count ?? 0} <span className="text-polar-500 font-normal">/</span> {stateData?.active_devices_count ?? 0} <span className="text-emerald-400 font-normal">Healthy</span>
            </span>
          </div>

          <div className="bg-polar-950/60 p-2.5 rounded-lg border border-polar-800">
            <span className="text-[10px] text-polar-400 block font-mono uppercase tracking-wider">Packet Loss Rate</span>
            <span className="text-xs font-semibold text-polar-200 block mt-1">
              {connData?.packet_loss_pct ?? 0}%
            </span>
          </div>

          <div className="bg-polar-950/60 p-2.5 rounded-lg border border-polar-800">
            <span className="text-[10px] text-polar-400 block font-mono uppercase tracking-wider">Sync Freshness</span>
            <div className="flex items-center space-x-1 mt-1">
              <Clock className="w-3.5 h-3.5 text-polar-400" />
              <span className="text-xs text-polar-300 font-mono">
                {stateData?.sync_freshness_sec != null ? `${stateData.sync_freshness_sec}s ago` : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Field Resilience Diagnostics & Hardware Testing */}
      <div className="bg-polar-900/60 border border-polar-800/80 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h2 className="text-xs font-semibold text-polar-200 uppercase tracking-wider">
              Field Connectivity &amp; Fault Diagnostics Harness
            </h2>
          </div>
          <span className="text-[10px] text-polar-500 font-mono">
            PROTOCOL TESTING // VERIFIED EDGE HARNESS
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {[
            { id: 'NORMAL', label: 'Nominal Field (Connected)', desc: 'Full satcom link, normal reporting' },
            { id: 'DEGRADED', label: 'Storm Degradation', desc: '45% packet loss, delayed heartbeat' },
            { id: 'OFFLINE', label: 'Satcom Blackout', desc: 'Link offline, local buffer queue growth' },
            { id: 'SAFE_HOLD', label: 'Force Safe Hold', desc: 'Life-safety posture, noncritical shed' },
          ].map((cond) => (
            <button
              key={cond.id}
              onClick={() => handleSimulateCondition(cond.id)}
              className={`px-3 py-2 rounded-lg text-xs font-medium text-left border transition ${
                simCondition === cond.id
                  ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 shadow-sm shadow-cyan-950/40'
                  : 'bg-polar-950/40 border-polar-800 text-polar-400 hover:text-polar-200 hover:bg-polar-900/60'
              }`}
            >
              <div className="font-semibold">{cond.label}</div>
              <div className="text-[10px] text-polar-500 mt-0.5">{cond.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Reconciliation Audit Log (if recently synced) */}
      {lastSyncResult && (
        <div className="bg-polar-900/80 border border-cyan-800/40 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-polar-200">
                Reconciliation Audit Report (Executed in {lastSyncResult.execution_duration_ms}ms)
              </h3>
            </div>
            <span className="text-[11px] font-mono text-cyan-400">
              Processed: {lastSyncResult.processed_count} | Duplicates Dropped: {lastSyncResult.duplicate_count} | Gaps Flagged: {lastSyncResult.gap_count}
            </span>
          </div>

          <div className="max-h-40 overflow-y-auto space-y-1.5 text-xs font-mono pr-2">
            {lastSyncResult.audit_log.map((entry, idx) => (
              <div key={idx} className="bg-polar-950/70 p-2 rounded border border-polar-800/60 flex items-center justify-between text-[11px]">
                <div className="flex items-center space-x-2">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                    entry.action === 'ACCEPTED_NEW' ? 'bg-emerald-500/20 text-emerald-300' :
                    entry.action === 'DUPLICATE_DROPPED' ? 'bg-polar-800 text-polar-400' :
                    entry.action === 'GAP_FLAGGED' ? 'bg-amber-500/20 text-amber-300' :
                    'bg-cyan-500/20 text-cyan-300'
                  }`}>
                    {entry.action}
                  </span>
                  <span className="text-polar-300">{entry.device_id}::{entry.channel}</span>
                </div>
                <span className="text-polar-500 text-[10px]">{entry.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Device Fleet Health & Telemetry Grid */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-polar-100">
              Station Device Fleet Catalog ({filteredDevices.length} Devices)
            </h2>
          </div>

          {/* Device Type Filter */}
          <div className="flex flex-wrap gap-1">
            {['ALL', 'DIESEL_GENERATOR', 'SOLAR', 'WIND', 'BATTERY', 'THERMAL', 'WEATHER', 'POWER_METER', 'FUEL'].map((type) => (
              <button
                key={type}
                onClick={() => setSelectedDeviceType(type)}
                className={`px-2 py-1 rounded text-[11px] font-medium transition ${
                  selectedDeviceType === type
                    ? 'bg-polar-700 text-cyan-300 font-semibold'
                    : 'bg-polar-900/60 text-polar-400 hover:text-polar-200'
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
                className="bg-polar-900/60 border border-polar-800 rounded-xl p-4 hover:border-polar-700 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider block">
                        {dev.device_type}
                      </span>
                      <h3 className="text-sm font-semibold text-polar-100 mt-0.5">
                        {dev.name}
                      </h3>
                      <span className="text-[11px] font-mono text-polar-400">
                        ID: {dev.device_id}
                      </span>
                    </div>
                    {getHealthBadge(health?.health_state || dev.health_state)}
                  </div>

                  {/* Rated Capacity & Protocol */}
                  <div className="mt-3 pt-3 border-t border-polar-800/60 grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[10px] text-polar-500 block">Rated Capacity</span>
                      <span className="font-mono text-polar-200">
                        {dev.rated_capacity != null ? `${dev.rated_capacity} ${dev.unit}` : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-polar-500 block">Bus / Protocol</span>
                      <span className="font-mono text-polar-300 text-[11px] truncate block" title={dev.source_metadata.protocol}>
                        {dev.source_metadata.protocol || 'LOCAL_BUS'}
                      </span>
                    </div>
                  </div>

                  {/* Telemetry Channels */}
                  <div className="mt-3">
                    <span className="text-[10px] text-polar-500 font-mono uppercase block mb-1">
                      Validated Channels ({dev.telemetry_channels.length})
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {dev.telemetry_channels.map(ch => {
                        const readingKey = `${dev.device_id}::${ch.channel}`;
                        const reading = stateData?.latest_readings?.[readingKey];
                        return (
                          <div 
                            key={ch.channel} 
                            className="bg-polar-950/80 px-2 py-1 rounded text-[10px] border border-polar-800/80 flex items-center space-x-1.5"
                          >
                            <span className="text-polar-400">{ch.channel}:</span>
                            <span className="font-mono font-semibold text-cyan-300">
                              {reading?.value != null ? `${reading.value} ${ch.unit}` : `${ch.min_val}–${ch.max_val} ${ch.unit}`}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Health Signals */}
                {health?.contributing_signals && health.contributing_signals.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-polar-800/40 text-[10px] text-polar-400 flex items-center space-x-1">
                    <Activity className="w-3 h-3 text-cyan-400" />
                    <span className="truncate">Signals: {health.contributing_signals.join(', ')}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Architectural Disclaimer Banner */}
      <div className="bg-polar-950/80 border border-polar-800 rounded-xl p-4 flex items-start space-x-3 text-xs text-polar-400">
        <Info className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-polar-200">Edge Decision Boundary & Field Safety:</span>
          <p className="mt-0.5">
            Polaris-EMS Edge Layer handles telemetry normalization, data quality validation, and local state buffering during communication dropouts. It operates under safe fallback postures (e.g. HOLD_LAST_VALIDATED_STATE, SAFE_HOLD) and <strong>does not solve mathematical optimization problems or actuate physical generators independently</strong>. When connectivity is verified, dispatch requests are routed to the central Dispatch Optimizer and Policy Governance pipeline.
          </p>
        </div>
      </div>
    </div>
  );
};
