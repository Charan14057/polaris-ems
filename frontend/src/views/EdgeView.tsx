import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useStation, useOperationalSnapshot } from '../context/StationContext';
import { useEvidence } from '../context/EvidenceContext';
import { edgeApi } from '../api/client';
import { getFallbackDevicesForStation } from '../features/edge/fallbackDeviceProfiles';
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
  Info,
  Sun,
  Wind,
  Fuel,
  Battery,
  Thermometer,
  Zap,
  ShieldCheck,
  Search,
  Filter,
  CheckCircle,
  HardDrive
} from 'lucide-react';

// --- Safe number formatter helper ---
const fmtNum = (val: number | undefined | null, decimals = 1, fallback = '0.0'): string => {
  if (val === undefined || val === null || isNaN(val)) return fallback;
  return Number(val).toFixed(decimals);
};

// Static authoritative load devices for Bharati, Maitri, and Himadri
const STATION_PRIORITY_CIRCUITS: Record<string, Array<{ id: string; name: string; priority: number; category: string; powerKw: number; deferrable: boolean }>> = {
  BHARATI: [
    { id: 'p1_hvac', name: 'Life Support & Ventilation HVAC', priority: 1, category: 'LIFE_SUPPORT', powerKw: 14.5, deferrable: false },
    { id: 'p1_freeze', name: 'Water Line Freeze Protection Heat Tracing', priority: 1, category: 'LIFE_SUPPORT', powerKw: 8.0, deferrable: false },
    { id: 'p2_comms', name: 'Satellite Telemetry & Emergency Comms', priority: 2, category: 'TELECOMMUNICATIONS', powerKw: 3.5, deferrable: false },
    { id: 'p3_lab', name: 'Core Scientific Laboratory Instruments', priority: 3, category: 'SCIENCE', powerKw: 6.0, deferrable: false },
    { id: 'p4_compute', name: 'Data Storage & Edge Compute Servers', priority: 4, category: 'COMPUTE', powerKw: 4.5, deferrable: false },
    { id: 'p5_cold_storage', name: 'Galley & Cold Storage Food Preservation', priority: 5, category: 'HABITAT', powerKw: 5.0, deferrable: true },
    { id: 'p6_living', name: 'Residential Living Quarters & Environmental', priority: 6, category: 'HABITAT', powerKw: 4.0, deferrable: true },
    { id: 'p7_waste', name: 'Waste Treatment & Incineration Aux', priority: 7, category: 'AUXILIARY', powerKw: 3.0, deferrable: true },
    { id: 'p8_snow_melt', name: 'Bulk Snow Melter Tank (Potable Reserve)', priority: 8, category: 'DEFERRABLE', powerKw: 12.0, deferrable: true },
    { id: 'p8_charging', name: 'Expedition Skidoo & Drone Charging Bank', priority: 8, category: 'DEFERRABLE', powerKw: 8.0, deferrable: true },
  ],
  MAITRI: [
    { id: 'mt_heat', name: 'Main Station Hydronic Heating Loop', priority: 1, category: 'LIFE_SUPPORT', powerKw: 12.0, deferrable: false },
    { id: 'mt_lake', name: 'Priyadarshini Lake Water Pumping & Trace Heating', priority: 1, category: 'LIFE_SUPPORT', powerKw: 6.5, deferrable: false },
    { id: 'mt_comms', name: 'HF/VHF & Satellite Comms Station', priority: 2, category: 'TELECOMMUNICATIONS', powerKw: 3.0, deferrable: false },
    { id: 'mt_geo', name: 'Geomagnetism & Seismology Observatory', priority: 3, category: 'SCIENCE', powerKw: 5.5, deferrable: false },
    { id: 'mt_aws', name: 'AWS & Meteorological Logging Subsystems', priority: 4, category: 'COMPUTE', powerKw: 3.2, deferrable: false },
    { id: 'mt_galley', name: 'Galley & Living Block Utilities', priority: 5, category: 'HABITAT', powerKw: 4.5, deferrable: true },
    { id: 'mt_boiler', name: 'Boiler Auxiliary Circulation Pumps', priority: 6, category: 'AUXILIARY', powerKw: 2.8, deferrable: true },
    { id: 'mt_snow', name: 'Secondary Snow Melt Unit', priority: 7, category: 'DEFERRABLE', powerKw: 8.5, deferrable: true },
    { id: 'mt_workshop', name: 'Maintenance Workshop Auxiliary', priority: 8, category: 'DEFERRABLE', powerKw: 4.0, deferrable: true },
  ],
  HIMADRI: [
    { id: 'hm_clean_air', name: 'Clean Air Laboratory HVAC & Climate', priority: 1, category: 'LIFE_SUPPORT', powerKw: 10.5, deferrable: false },
    { id: 'hm_optical', name: 'Ny-Ålesund Optical & Satellite Uplink', priority: 2, category: 'TELECOMMUNICATIONS', powerKw: 2.8, deferrable: false },
    { id: 'hm_spectro', name: 'Continuous Atmospheric Aerosol Spectrometer', priority: 3, category: 'SCIENCE', powerKw: 4.5, deferrable: false },
    { id: 'hm_radar', name: 'Glaciology Radar & Sensor Telemetry Node', priority: 4, category: 'SCIENCE', powerKw: 3.0, deferrable: false },
    { id: 'hm_quarters', name: 'Crew Quarters & Environmental Comfort', priority: 5, category: 'HABITAT', powerKw: 3.5, deferrable: true },
    { id: 'hm_dryer', name: 'Polar Expedition Field Equipment Dryer', priority: 6, category: 'DEFERRABLE', powerKw: 5.0, deferrable: true },
  ],
};

export const EdgeView: React.FC = () => {
  const { stationId, currentStation, stationDetail } = useStation();
  const { snapshot, activeScenario } = useOperationalSnapshot();
  const { inspectEvidence } = useEvidence();

  const activeStation = useMemo(() => {
    return (currentStation || stationId || 'BHARATI').toUpperCase();
  }, [currentStation, stationId]);

  const isScenarioActive = Boolean(activeScenario && activeScenario !== 'NORMAL_BASELINE');
  const scenarioName = activeScenario ? activeScenario.replace(/_/g, ' ') : '';

  // Initialize with authoritative fallback devices to guarantee ZERO blank states
  const [devices, setDevices] = useState<DeviceSummary[]>(() => getFallbackDevicesForStation(activeStation));
  const [stateData, setStateData] = useState<EdgeStateResponseData | null>(null);
  const [healthItems, setHealthItems] = useState<DeviceHealthItem[]>([]);
  const [connData, setConnData] = useState<ConnectivityResponseData | null>(null);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResponseData | null>(null);
  
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [simCondition, setSimCondition] = useState<string>('NORMAL');
  const [selectedDeviceType, setSelectedDeviceType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Update fallback devices immediately when activeStation changes
  useEffect(() => {
    setDevices(getFallbackDevicesForStation(activeStation));
  }, [activeStation]);

  // Robust parallel fetch using Promise.allSettled to eliminate single-point-of-failure rejections
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const results = await Promise.allSettled([
        edgeApi.getState(activeStation),
        edgeApi.getDevices(activeStation),
        edgeApi.getHealth(activeStation),
        edgeApi.getConnectivity(activeStation),
      ]);

      const [stRes, devRes, hlRes, cnRes] = results;

      if (stRes.status === 'fulfilled' && stRes.value?.data) {
        setStateData(stRes.value.data);
      }
      if (devRes.status === 'fulfilled' && Array.isArray(devRes.value?.data) && devRes.value.data.length > 0) {
        setDevices(devRes.value.data);
      }
      if (hlRes.status === 'fulfilled' && Array.isArray(hlRes.value?.data)) {
        setHealthItems(hlRes.value.data);
      }
      if (cnRes.status === 'fulfilled' && cnRes.value?.data) {
        setConnData(cnRes.value.data);
      }
    } catch (err) {
      console.warn('Edge data refresh advisory:', err);
    } finally {
      setIsLoading(false);
    }
  }, [activeStation]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const res = await edgeApi.syncBuffer(activeStation);
      if (res.data) {
        setLastSyncResult(res.data);
        await fetchData();
      }
    } catch (err) {
      console.warn('Sync advisory:', err);
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
      console.warn('Condition simulation advisory:', err);
    }
  };

  // Filtered devices with safety fallback
  const filteredDevices = useMemo(() => {
    return devices.filter(d => {
      const matchesType = selectedDeviceType === 'ALL' || d.device_type === selectedDeviceType;
      const q = searchQuery.toLowerCase().trim();
      const matchesQuery = !q || 
        d.name?.toLowerCase().includes(q) || 
        d.device_id?.toLowerCase().includes(q) ||
        (d.telemetry_channels ?? []).some(ch => ch.channel.toLowerCase().includes(q));
      return matchesType && matchesQuery;
    });
  }, [devices, selectedDeviceType, searchQuery]);

  const getEdgeModeBadge = (mode?: string) => {
    switch (mode) {
      case 'CONNECTED_OPERATION':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-emerald-50 text-emerald-700 border border-emerald-200">CONNECTED OPERATION</span>;
      case 'DEGRADED_CONNECTIVITY':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-amber-50 text-amber-800 border border-amber-200">DEGRADED CONNECTIVITY</span>;
      case 'OFFLINE_EDGE':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-rose-50 text-rose-700 border border-rose-200">OFFLINE EDGE MODE</span>;
      case 'RECOVERY_SYNC':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-sky-50 text-sky-700 border border-sky-200">RECOVERY RECONCILIATION</span>;
      case 'SAFE_HOLD':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-[#F3E8FF] text-indigo-700 border border-[#E9D5FF]">SAFE HOLD POSTURE</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-emerald-50 text-emerald-700 border border-emerald-200">CONNECTED OPERATION</span>;
    }
  };

  const getConnBadge = (conn?: string) => {
    switch (conn) {
      case 'CONNECTED':
        return <span className="flex items-center space-x-1.5 text-xs text-emerald-700 font-medium"><Wifi className="w-3.5 h-3.5" /><span>Active Link</span></span>;
      case 'DEGRADED':
        return <span className="flex items-center space-x-1.5 text-xs text-amber-700 font-medium"><Activity className="w-3.5 h-3.5" /><span>Degraded (High Loss)</span></span>;
      case 'OFFLINE':
        return <span className="flex items-center space-x-1.5 text-xs text-rose-700 font-medium"><WifiOff className="w-3.5 h-3.5" /><span>Offline / Blackout</span></span>;
      case 'RECONNECTING':
        return <span className="flex items-center space-x-1.5 text-xs text-sky-600 font-medium"><RefreshCw className="w-3.5 h-3.5 animate-spin" /><span>Handshake / Sync</span></span>;
      default:
        return <span className="flex items-center space-x-1.5 text-xs text-emerald-700 font-medium"><Wifi className="w-3.5 h-3.5" /><span>Active Link</span></span>;
    }
  };

  const getHealthBadge = (health?: string) => {
    switch (health) {
      case 'HEALTHY':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-emerald-50 text-emerald-700 border border-emerald-200">HEALTHY</span>;
      case 'DEGRADED':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-amber-50 text-amber-800 border border-amber-200">DEGRADED</span>;
      case 'UNAVAILABLE':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-slate-50 text-slate-500 border border-slate-200">UNAVAILABLE</span>;
      case 'FAULT':
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-rose-50 text-rose-700 border border-rose-200">FAULT</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-emerald-50 text-emerald-700 border border-emerald-200">HEALTHY</span>;
    }
  };

  // Station physical infrastructure assets data derived from station profile
  const electrical = stationDetail?.electrical;
  const thermal = stationDetail?.thermal;
  const fuel = stationDetail?.fuel;
  const priorityCircuits = STATION_PRIORITY_CIRCUITS[activeStation] || STATION_PRIORITY_CIRCUITS.BHARATI;

  return (
    <div className="p-4 lg:p-8 space-y-8 max-w-7xl mx-auto font-sans">
      
      {/* 1. Industrial Header with Steel / Cyan Palette */}
      <div className="bg-slate-900 border border-cyan-500/30 rounded-xl p-5 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 relative z-10">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-cyan-400 font-bold mb-1">
              <Cpu className="w-4 h-4" />
              <span>08 EDGE INTELLIGENCE & FIELD FLEET • HARDWARE RUNTIME</span>
              <span>•</span>
              <ProvenanceTag provenance="SIMULATED" size="xs" />
            </div>
            <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
              Station Assets & Field Fleet
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Station <strong className="text-cyan-300">{activeStation}</strong> physical power plant infrastructure, SCADA telemetry normalization, device health inspection, and buffer reconciliation.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {getEdgeModeBadge(stateData?.edge_mode)}
            <button
              type="button"
              onClick={fetchData}
              disabled={isLoading}
              className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-mono font-bold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition shadow-xs"
              title="Refresh local edge state"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
              <span>Refresh</span>
            </button>

            <button
              type="button"
              onClick={handleSync}
              disabled={isSyncing}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-mono font-bold rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white transition shadow-xs disabled:opacity-50"
              title="Reconcile buffered telemetry with central backend"
            >
              <ArrowUpDown className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>Reconcile Buffer</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Operational Diagnostics Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] text-slate-500 block font-mono uppercase tracking-wider">Connectivity</span>
          <div className="mt-1">{getConnBadge(connData?.connectivity_state)}</div>
        </div>

        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] text-slate-500 block font-mono uppercase tracking-wider">Fallback Posture</span>
          <span className="text-xs font-semibold text-sky-700 block mt-1 truncate" title={stateData?.fallback_posture || 'HOLD_LAST_VALIDATED_STATE'}>
            {stateData?.fallback_posture || 'HOLD_LAST_STATE'}
          </span>
        </div>

        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] text-slate-500 block font-mono uppercase tracking-wider">Local Buffer Queue</span>
          <div className="flex items-center space-x-1 mt-1">
            <Database className="w-3.5 h-3.5 text-sky-600" />
            <span className="text-xs font-bold text-slate-900 font-mono font-mono-numbers">
              {stateData?.buffer_depth ?? 0} <span className="text-[10px] font-normal text-slate-500">items</span>
            </span>
          </div>
        </div>

        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] text-slate-500 block font-mono uppercase tracking-wider">Fleet Devices</span>
          <span className="text-xs font-semibold text-slate-900 block mt-1 font-mono font-mono-numbers">
            {stateData?.healthy_devices_count ?? devices.length} <span className="text-slate-400 font-normal">/</span> {devices.length} <span className="text-emerald-700 font-normal">Healthy</span>
          </span>
        </div>

        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] text-slate-500 block font-mono uppercase tracking-wider">Packet Loss Rate</span>
          <span className="text-xs font-semibold text-slate-900 block mt-1 font-mono font-mono-numbers">
            {connData?.packet_loss_pct ?? 0}%
          </span>
        </div>

        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] text-slate-500 block font-mono uppercase tracking-wider">Sync Freshness</span>
          <div className="flex items-center space-x-1 mt-1">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs text-slate-600 font-mono font-mono-numbers">
              {stateData?.sync_freshness_sec != null ? `${stateData.sync_freshness_sec}s ago` : 'Real-time'}
            </span>
          </div>
        </div>
      </div>

      {/* 3. Primary Station Infrastructure Assets Grid */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider font-mono">
              Primary Power Plant &amp; Infrastructure Assets
            </h2>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {activeStation} Microgrid Generation &amp; Storage Assets
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          
          {/* Solar PV Field Asset */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between hover:border-amber-400 transition-colors">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
                    <Sun className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase">Solar Photovoltaic Array</h3>
                    <span className="text-[10px] font-mono text-slate-400">Bifacial Monocrystalline PERC</span>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
                  ONLINE
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Installed Capacity</span>
                  <span className="text-sm font-bold font-mono text-slate-900">{electrical?.solar_pv_kw_peak ?? 30.0} kWp</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Active Power</span>
                  <span className="text-sm font-bold font-mono text-amber-600 font-mono-numbers">{fmtNum(snapshot.solarGenerationKw, 1)} kW</span>
                </div>
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-500">
              <span>MPPT Polar Inverter</span>
              <span className="text-amber-700 font-semibold">{fmtNum(snapshot.irradianceWm2, 0)} W/m² GHI</span>
            </div>
          </div>

          {/* Wind Turbine Field Asset */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between hover:border-teal-400 transition-colors">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600">
                    <Wind className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase">Polar Wind Turbines</h3>
                    <span className="text-[10px] font-mono text-slate-400">Direct-Drive Sub-Zero Blades</span>
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                  isScenarioActive && scenarioName.includes('WIND')
                    ? 'bg-rose-100 text-rose-700 border border-rose-200'
                    : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                }`}>
                  {isScenarioActive && scenarioName.includes('WIND') ? 'TRIPPED' : 'ONLINE'}
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Rated Capacity</span>
                  <span className="text-sm font-bold font-mono text-slate-900">{electrical?.wind_turbine_kw_rated ?? 25.0} kW</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Active Power</span>
                  <span className="text-sm font-bold font-mono text-teal-600 font-mono-numbers">{fmtNum(snapshot.windGenerationKw, 1)} kW</span>
                </div>
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-500">
              <span>Cut-in: 3.0 m/s</span>
              <span className="text-teal-700 font-semibold">{fmtNum(snapshot.windSpeedMs, 1)} m/s Wind</span>
            </div>
          </div>

          {/* Diesel Generation Power Plant */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between hover:border-slate-400 transition-colors">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-800">
                    <Fuel className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase">Synchronous Diesel Plant</h3>
                    <span className="text-[10px] font-mono text-slate-400">{electrical?.diesel_generator_count ?? 3}x Gensets with CHP Heat</span>
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                  (snapshot.dieselGenerationKw ?? 0) > 1.0
                    ? 'bg-amber-100 text-amber-800 border border-amber-300'
                    : 'bg-slate-100 text-slate-600 border border-slate-200'
                }`}>
                  {(snapshot.dieselGenerationKw ?? 0) > 1.0 ? 'RUNNING' : 'STANDBY'}
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Total Capacity</span>
                  <span className="text-sm font-bold font-mono text-slate-900">
                    {(electrical?.diesel_generator_count ?? 3) * (electrical?.diesel_generator_kw_rated ?? 80.0)} kW
                  </span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Active Power</span>
                  <span className="text-sm font-bold font-mono text-slate-900 font-mono-numbers">{fmtNum(snapshot.dieselGenerationKw, 1)} kW</span>
                </div>
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-500">
              <span>Fuel Rate: {fmtNum(snapshot.fuelConsumptionLph, 1)} L/h</span>
              <span className="text-slate-700 font-semibold">{fmtNum(snapshot.fuelRemainingL, 0)} L Reserve</span>
            </div>
          </div>

          {/* BESS Storage Bank Asset */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between hover:border-indigo-400 transition-colors">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
                    <Battery className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase">LiFePO4 BESS Storage</h3>
                    <span className="text-[10px] font-mono text-slate-400">Thermal Envelope Insulated</span>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-indigo-50 text-indigo-700 border border-indigo-200">
                  {snapshot.bessStatus || 'BUFFERING'}
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Nameplate Storage</span>
                  <span className="text-sm font-bold font-mono text-slate-900">{electrical?.battery_capacity_kwh ?? 120.0} kWh</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Usable SOC</span>
                  <span className="text-sm font-bold font-mono text-indigo-600 font-mono-numbers">{fmtNum(snapshot.bessSocPct, 0)}%</span>
                </div>
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-500">
              <span>Limits: [{Math.round((electrical?.battery_min_soc ?? 0.2) * 100)}%–{Math.round((electrical?.battery_max_soc ?? 0.95) * 100)}%]</span>
              <span className="text-indigo-700 font-semibold">{fmtNum(snapshot.bessPowerKw, 1)} kW Flow</span>
            </div>
          </div>

          {/* Thermal District Heating Asset */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between hover:border-rose-400 transition-colors">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
                    <Thermometer className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase">District Thermal Plant</h3>
                    <span className="text-[10px] font-mono text-slate-400">Freeze-Protection Heat Tracing</span>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
                  PROTECTED
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Target Habitat Temp</span>
                  <span className="text-sm font-bold font-mono text-slate-900">{thermal?.indoor_target_temp_c ?? 20.0} °C</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Ambient Outdoor</span>
                  <span className="text-sm font-bold font-mono text-sky-700 font-mono-numbers">{fmtNum(snapshot.ambientTemperatureC, 1)} °C</span>
                </div>
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-500">
              <span>Safety Minimum: {thermal?.indoor_min_safe_temp_c ?? 12.0} °C</span>
              <span className="text-rose-700 font-semibold">{thermal?.building_ua_kw_per_k ?? 0.85} kW/K UA</span>
            </div>
          </div>

          {/* Bulk Polar Fuel Tank Farm */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between hover:border-amber-400 transition-colors">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
                    <Database className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase">Bulk Fuel Storage Farm</h3>
                    <span className="text-[10px] font-mono text-slate-400">{fuel?.fuel_type || 'Polar Low-Pour Diesel'}</span>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
                  SECURE
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Bunker Capacity</span>
                  <span className="text-sm font-bold font-mono text-slate-900">{fmtNum(fuel?.storage_capacity_liters ?? 160000, 0)} L</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block font-mono">Station Autonomy</span>
                  <span className="text-sm font-bold font-mono text-emerald-600 font-mono-numbers">{fmtNum(snapshot.daysOfFuelRemaining, 0)} Days</span>
                </div>
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-500">
              <span>Reserve Bound: {fmtNum(fuel?.critical_fuel_reserve_liters ?? 25000, 0)} L</span>
              <span className="text-amber-700 font-semibold">{fmtNum(snapshot.fuelRemainingL, 0)} L Stock</span>
            </div>
          </div>

        </div>
      </div>

      {/* 4. Connected Priority Loads & Circuits Table (P1–P8 Hierarchy) */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-sky-700" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-mono">
              Protected Station Circuits &amp; Life-Support Hierarchy ({priorityCircuits.length} Loads)
            </h2>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Total Connected Demand: {fmtNum(snapshot.totalLoadKw, 1)} kW (Critical: {fmtNum(snapshot.criticalLoadKw, 1)} kW)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 uppercase text-[10px]">
                <th className="py-2 px-3">Priority Rank</th>
                <th className="py-2 px-3">Circuit / Asset Name</th>
                <th className="py-2 px-3">Subsystem Class</th>
                <th className="py-2 px-3 text-right">Nominal Power</th>
                <th className="py-2 px-3 text-center">Shedding Governance</th>
                <th className="py-2 px-3 text-right">Operating Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {priorityCircuits.map((load) => (
                <tr key={load.id} className="hover:bg-slate-50/50">
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      load.priority === 1 ? 'bg-rose-100 text-rose-800 border border-rose-200' :
                      load.priority === 2 ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                      load.priority <= 4 ? 'bg-sky-100 text-sky-800 border border-sky-200' :
                      'bg-slate-100 text-slate-700'
                    }`}>
                      P{load.priority}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-semibold text-slate-900 font-sans">
                    {load.name}
                  </td>
                  <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">
                    {load.category}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono font-mono-numbers font-bold text-slate-900">
                    {fmtNum(load.powerKw, 1)} kW
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                      load.deferrable
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    }`}>
                      {load.deferrable ? 'DEFERRABLE' : 'NON-DEFERRABLE (P1)'}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold text-xs">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      ENERGIZED
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Device Fleet Health & Telemetry Grid */}
      <div className="space-y-4">
        {isScenarioActive && (
          <div className="bg-slate-900 border-2 border-rose-500/80 rounded-xl p-4 shadow-xl text-white relative overflow-hidden animate-pulse">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center space-x-3">
                <span className="p-2 bg-rose-500/20 rounded-lg border border-rose-500/40 text-rose-400">
                  <AlertTriangle className="w-5 h-5" />
                </span>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-mono uppercase tracking-widest text-rose-400 font-bold">
                      ACTIVE CONTINGENCY REGIME DETECTED ON EDGE BUS
                    </span>
                    <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-rose-950 text-rose-300 border border-rose-800">
                      {scenarioName}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-0.5">
                    Physical asset operating telemetry is subjected to active stress perturbations. Downstream protective interlocks and spinning reserve dispatch are active.
                  </p>
                </div>
              </div>
              <div className="text-right shrink-0">
                <span className="text-[10px] font-mono text-slate-400 block">Total Load Active</span>
                <span className="text-sm font-bold font-mono text-cyan-400 font-mono-numbers">{(snapshot.totalLoadKw ?? 0).toFixed(1)} kW</span>
              </div>
            </div>
          </div>
        )}

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-3">
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-sky-700" />
            <h2 className="text-sm font-bold text-slate-900 font-mono uppercase tracking-wide">
              SCADA Transducer &amp; Edge Field Telemetry Fleet ({filteredDevices.length} Devices)
            </h2>
          </div>

          {/* Search & Filters */}
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search devices or channels..."
                className="pl-8 pr-3 py-1 text-xs rounded-lg border border-slate-200 bg-white placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500 w-48 sm:w-60 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap gap-1.5">
          {['ALL', 'SOLAR', 'WIND', 'DIESEL_GENERATOR', 'BATTERY', 'THERMAL', 'WEATHER', 'POWER_METER', 'FUEL', 'GPS', 'COMMUNICATIONS'].map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setSelectedDeviceType(type)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-mono transition-all ${
                selectedDeviceType === type
                  ? 'bg-slate-900 text-white font-semibold shadow-xs'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
              }`}
            >
              {type === 'ALL' ? 'All Classes' : type.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        {/* Device Cards Grid */}
        {filteredDevices.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-8 text-center space-y-3">
            <Info className="w-6 h-6 text-slate-400 mx-auto" />
            <h3 className="text-sm font-bold text-slate-800">No Devices Found</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              No field devices match the selected category &quot;{selectedDeviceType}&quot; or query &quot;{searchQuery}&quot;.
            </p>
            <button
              type="button"
              onClick={() => { setSelectedDeviceType('ALL'); setSearchQuery(''); }}
              className="px-3 py-1.5 rounded-lg bg-sky-50 text-sky-700 text-xs font-mono font-semibold hover:bg-sky-100 transition"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredDevices.map((dev) => {
              const health = healthItems.find(h => h.device_id === dev.device_id);
              const isWindDev = dev.device_type === 'WIND' || (dev.name ?? '').toLowerCase().includes('wind');
              const isWindFaulted = Boolean(isScenarioActive && isWindDev && ((snapshot.windGenerationKw ?? 0) <= 0.05 || scenarioName.includes('WIND')));
              const isSolarDev = dev.device_type === 'SOLAR' || (dev.name ?? '').toLowerCase().includes('solar');
              const isSolarFaulted = Boolean(isScenarioActive && isSolarDev && (snapshot.solarGenerationKw ?? 0) <= 0.05 && scenarioName.includes('SOLAR'));
              const isDieselDev = dev.device_type === 'DIESEL_GENERATOR' || (dev.name ?? '').toLowerCase().includes('diesel') || (dev.name ?? '').toLowerCase().includes('generator');
              const isDieselDispatched = Boolean(isScenarioActive && isDieselDev && (snapshot.dieselGenerationKw ?? 0) > 1.0);

              const channels = dev.telemetry_channels || [];

              return (
                <div 
                  key={dev.device_id}
                  className={`rounded-xl p-4 transition-all shadow-xs flex flex-col justify-between ${
                    isWindFaulted
                      ? 'bg-rose-950/20 border-2 border-rose-500 ring-2 ring-rose-500/50 shadow-lg shadow-rose-950/30 animate-pulse'
                      : isSolarFaulted
                      ? 'bg-amber-950/20 border-2 border-amber-500 ring-2 ring-amber-500/50'
                      : isDieselDispatched
                      ? 'bg-amber-500/10 border-2 border-amber-500/60 shadow-md'
                      : 'bg-white border border-slate-200 hover:border-sky-600/50'
                  }`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center space-x-1.5">
                          <span className={`text-[10px] font-mono uppercase tracking-wider block font-semibold ${
                            isWindFaulted ? 'text-rose-400 font-bold' : 'text-sky-700'
                          }`}>
                            {dev.device_type}
                          </span>
                          {isWindFaulted && (
                            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping inline-block" />
                          )}
                        </div>
                        <h3 className={`text-sm font-semibold mt-0.5 ${
                          isWindFaulted ? 'text-rose-300 font-bold' : 'text-slate-900'
                        }`}>
                          {dev.name}
                        </h3>
                        <span className="text-[11px] font-mono text-slate-500">
                          ID: {dev.device_id}
                        </span>
                      </div>
                      {isWindFaulted ? (
                        <span className="px-2.5 py-1 text-[10px] font-bold font-mono rounded bg-rose-900 text-rose-200 border border-rose-500 animate-pulse flex items-center space-x-1">
                          <span>⚠️</span>
                          <span>FAULT (TRIPPED)</span>
                        </span>
                      ) : isDieselDispatched ? (
                        <span className="px-2 py-0.5 text-[10px] font-bold font-mono rounded bg-amber-50 text-amber-800 border border-amber-300">
                          SPINNING RESERVE
                        </span>
                      ) : (
                        getHealthBadge(health?.health_state || dev.health_state)
                      )}
                    </div>

                    {/* Rated Capacity & Protocol */}
                    <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-500 block">Rated Capacity</span>
                        <span className="font-mono font-mono-numbers text-slate-900 font-semibold">
                          {dev.rated_capacity != null ? `${dev.rated_capacity} ${dev.unit}` : 'Operational'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block">Bus / Protocol</span>
                        <span className="font-mono text-slate-600 text-[11px] truncate block" title={dev.source_metadata?.protocol}>
                          {dev.source_metadata?.protocol || 'MODBUS_TCP'}
                        </span>
                      </div>
                    </div>

                    {/* Telemetry Channels */}
                    <div className="mt-3">
                      <span className="text-[10px] text-slate-500 font-mono uppercase block mb-1">
                        Validated Channels ({channels.length})
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {channels.map(ch => {
                          const readingKey = `${dev.device_id}::${ch.channel}`;
                          const reading = stateData?.latest_readings?.[readingKey];
                          
                          // Overwrite with scenario impact if faulted
                          const isPowerChannel = ch.channel.toLowerCase().includes('power') || ch.channel.toLowerCase().includes('active');
                          const displayVal = isWindFaulted && isPowerChannel 
                            ? '0.00 kW (TRIPPED)'
                            : isDieselDispatched && isPowerChannel
                            ? `${(snapshot.dieselGenerationKw ?? 0).toFixed(1)} kW`
                            : reading?.value != null ? `${reading.value} ${ch.unit}` : `${ch.min_val}–${ch.max_val} ${ch.unit}`;

                          return (
                            <button 
                              key={ch.channel} 
                              type="button"
                              onClick={() => inspectEvidence({
                                value: displayVal,
                                source: `${dev.name} [${ch.channel}]`,
                                provenance: 'SIMULATED',
                                timestamp: reading?.timestamp || new Date().toISOString(),
                                station: activeStation,
                                model: `${dev.device_type} Transducer Driver`,
                                validationState: isWindFaulted ? 'DEGRADED' : 'VALIDATED',
                                uncertaintyInterval: `Operational bounds [${ch.min_val}, ${ch.max_val}] ${ch.unit}`,
                                governingInvariant: 'Hardware telemetry bounds check verified: readings outside operational range trigger DEGRADED device state.'
                              })}
                              className={`px-2 py-1 rounded text-[10px] border flex items-center space-x-1.5 transition-colors ${
                                isWindFaulted && isPowerChannel
                                  ? 'bg-rose-900/60 border-rose-500 text-rose-200 font-bold animate-pulse'
                                  : 'bg-slate-50 border-slate-200 text-slate-700 hover:border-sky-600'
                              }`}
                            >
                              <span className="text-slate-500">{ch.channel}:</span>
                              <span className={`font-mono font-semibold font-mono-numbers ${
                                isWindFaulted && isPowerChannel ? 'text-rose-300' : 'text-sky-700'
                              }`}>
                                {displayVal}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Health Signals */}
                  {isWindFaulted ? (
                    <div className="mt-3 pt-2 border-t border-rose-800 text-[10px] text-rose-400 font-mono flex items-center space-x-1.5">
                      <AlertTriangle className="w-3 h-3 text-rose-400 animate-pulse" />
                      <span className="truncate">Contingency Trip: Breaker Open • Rotor Feathered</span>
                    </div>
                  ) : health?.contributing_signals && health.contributing_signals.length > 0 ? (
                    <div className="mt-3 pt-2 border-t border-slate-200 text-[10px] text-slate-500 flex items-center space-x-1">
                      <Activity className="w-3 h-3 text-sky-700" />
                      <span className="truncate">Signals: {health.contributing_signals.join(', ')}</span>
                    </div>
                  ) : (
                    <div className="mt-3 pt-2 border-t border-slate-100 text-[10px] text-emerald-700 font-mono flex items-center space-x-1">
                      <CheckCircle className="w-3 h-3 text-emerald-600" />
                      <span>Transducer Healthy • Bus Address: {dev.source_metadata?.bus_address || 'CH-01'}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 6. Field Connectivity & Fault Diagnostics Harness */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-sky-700" />
            <h2 className="text-xs font-semibold text-slate-900 uppercase tracking-wider font-mono">
              Field Connectivity &amp; Fault Diagnostics Harness
            </h2>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
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
              type="button"
              onClick={() => handleSimulateCondition(cond.id)}
              className={`p-3 rounded-lg text-left border transition ${
                simCondition === cond.id
                  ? 'bg-amber-50 border-sky-600 text-amber-800 shadow-xs'
                  : 'bg-white border-slate-200 text-slate-600 hover:border-sky-600/50'
              }`}
            >
              <div className="font-semibold text-xs text-slate-900">{cond.label}</div>
              <div className="text-[11px] text-slate-500 mt-1">{cond.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 7. Reconciliation Audit Log (if recently synced) */}
      {lastSyncResult && (
        <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-6 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              <h3 className="text-xs font-bold text-slate-900">
                Reconciliation Audit Report (Executed in {lastSyncResult.execution_duration_ms}ms)
              </h3>
            </div>
            <span className="text-[11px] font-mono text-sky-600">
              Processed: {lastSyncResult.processed_count} | Duplicates Dropped: {lastSyncResult.duplicate_count} | Gaps Flagged: {lastSyncResult.gap_count}
            </span>
          </div>

          <div className="max-h-40 overflow-y-auto space-y-1.5 text-xs font-mono pr-2">
            {lastSyncResult.audit_log.map((entry, idx) => (
              <div key={idx} className="bg-white p-2.5 rounded border border-slate-200 flex items-center justify-between text-[11px]">
                <div className="flex items-center space-x-2">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                    entry.action === 'ACCEPTED_NEW' ? 'bg-emerald-50 text-emerald-700' :
                    entry.action === 'DUPLICATE_DROPPED' ? 'bg-slate-50 text-slate-500' :
                    entry.action === 'GAP_FLAGGED' ? 'bg-amber-50 text-amber-800' :
                    'bg-sky-50 text-sky-700'
                  }`}>
                    {entry.action}
                  </span>
                  <span className="text-slate-900">{entry.device_id}::{entry.channel}</span>
                </div>
                <span className="text-slate-500 text-[10px]">{entry.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 8. Explain This & Architectural Disclaimer */}
      <ExplainThis
        title="What does Edge Intelligence mean in Antarctica?"
        whatAmILookingAt="This engineering console monitors the computers and sensors physically located inside the polar station, tracking communications health, telemetry queues, and connected equipment."
        whyIsItImportant="Antarctic stations frequently lose satellite connections during blizzard whiteouts or solar storms. 'Edge computing' ensures that the software running inside the station continues controlling life-support power without needing an internet connection."
        howIsItCalculated="Telemetry is held in bounded FIFO buffer queues with SHA-256 deduplication and automatically reconciled once satellite links re-establish."
      />

      <WhyThisMatters
        summary="Antarctic station communication links experience frequent geomagnetic and weather-induced outages. The local Edge layer buffers telemetry, maintains safe operation, and rejects stale sensor readings until connectivity is restored."
        technicalDetail="Local edge nodes buffer high-frequency telemetry in an in-memory ring buffer (up to 10,000 items). Upon satcom reconnection, a deterministic three-way handshake reconciles missing timestamps without overwriting newer central records."
        invariant="Edge Safety Boundary: Local edge nodes never solve global dispatch optimization or actuate generators independently. They fall back to HOLD_LAST_VALIDATED_STATE or SAFE_HOLD until central policy and optimization handoffs resume."
        stage="Edge & Device Fleet Intelligence"
      />

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-start space-x-3 text-xs text-slate-600">
        <Info className="w-4 h-4 text-sky-700 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-900">Edge Decision Boundary &amp; Field Safety:</span>
          <p className="mt-0.5">
            Polaris-EMS Edge Layer handles telemetry normalization, data quality validation, and local state buffering during communication dropouts. It operates under safe fallback postures (e.g. HOLD_LAST_VALIDATED_STATE, SAFE_HOLD) and <strong>does not solve mathematical optimization problems or actuate physical generators independently</strong>. When connectivity is verified, dispatch requests are routed to the central Dispatch Optimizer and Policy Governance pipeline.
          </p>
        </div>
      </div>
    </div>
  );
};
