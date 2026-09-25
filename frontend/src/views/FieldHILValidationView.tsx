import React, { useState, useEffect } from 'react';
import {
  Radio,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Wifi,
  WifiOff,
  Server,
  Shield,
  Clock,
  Database,
  GitBranch,
  Cpu,
  Zap,
  Info,
} from 'lucide-react';

/* --------------------------------------------------------------------------
   TYPE DEFINITIONS
   -------------------------------------------------------------------------- */

type EnvironmentTag = 'REAL' | 'HIL' | 'LAB' | 'EMULATOR' | 'SIMULATION';

interface DeviceEntry {
  device_id: string;
  device_type: string;
  adapter: string;
  environment: EnvironmentTag;
  health: string;
  connectivity: string;
  telemetry_quality: string;
}

interface FaultEntry {
  fault_type: string;
  fault_class: string;
  target: string;
  timestamp: string;
}

interface ValidationState {
  station_id: string;
  edge_mode: string;
  fallback_posture: string;
  connectivity_state: string;
  buffer_depth: number;
  reconciliation_status: string;
  devices: DeviceEntry[];
  active_faults: FaultEntry[];
  actuation_auth: boolean;
  last_actuation_outcome: string;
  trace_id: string;
  validation_result: string;
  environment: EnvironmentTag;
}

/* --------------------------------------------------------------------------
   MOCK DATA – deterministic simulation-only data
   All data is labelled SIMULATION unless noted otherwise.
   -------------------------------------------------------------------------- */

const MOCK_STATE: ValidationState = {
  station_id: 'BHARATI',
  edge_mode: 'CONNECTED_OPERATION',
  fallback_posture: 'WAIT_FOR_BACKEND_DECISION',
  connectivity_state: 'CONNECTED',
  buffer_depth: 0,
  reconciliation_status: 'IDLE',
  devices: [
    { device_id: 'gen-001', device_type: 'DIESEL_GENERATOR', adapter: 'SimulatorAdapter', environment: 'SIMULATION', health: 'HEALTHY', connectivity: 'CONNECTED', telemetry_quality: 'VALID' },
    { device_id: 'solar-001', device_type: 'SOLAR', adapter: 'SimulatorAdapter', environment: 'SIMULATION', health: 'HEALTHY', connectivity: 'CONNECTED', telemetry_quality: 'VALID' },
    { device_id: 'bat-001', device_type: 'BATTERY', adapter: 'EmulatorAdapter', environment: 'EMULATOR', health: 'DEGRADED', connectivity: 'DEGRADED', telemetry_quality: 'STALE' },
    { device_id: 'wind-001', device_type: 'WIND', adapter: 'HILAdapter', environment: 'HIL', health: 'HEALTHY', connectivity: 'CONNECTED', telemetry_quality: 'VALID' },
  ],
  active_faults: [
    { fault_type: 'STALE', fault_class: 'TELEMETRY', target: 'bat-001::voltage', timestamp: '2025-06-15T12:34:00Z' },
  ],
  actuation_auth: true,
  last_actuation_outcome: 'SIMULATED',
  trace_id: 'P16_BHARATI_a1b2c3d4',
  validation_result: 'PASS',
  environment: 'SIMULATION',
};

/* --------------------------------------------------------------------------
   HELPER COMPONENTS
   -------------------------------------------------------------------------- */

const envColors: Record<string, string> = {
  REAL: 'text-green-400 bg-green-950/40 border-green-700/40',
  HIL: 'text-amber-400 bg-amber-950/40 border-amber-700/40',
  LAB: 'text-purple-400 bg-purple-950/40 border-purple-700/40',
  EMULATOR: 'text-blue-400 bg-blue-950/40 border-blue-700/40',
  SIMULATION: 'text-cyan-400 bg-cyan-950/40 border-cyan-700/40',
};

const EnvBadge: React.FC<{ env: string }> = ({ env }) => (
  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${envColors[env] || envColors.SIMULATION}`}>
    {env}
  </span>
);

const healthIcon = (h: string) => {
  switch (h) {
    case 'HEALTHY': return <CheckCircle className="w-3.5 h-3.5 text-green-400" />;
    case 'DEGRADED': return <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />;
    case 'FAULT': return <XCircle className="w-3.5 h-3.5 text-red-400" />;
    default: return <Info className="w-3.5 h-3.5 text-polar-500" />;
  }
};

const connIcon = (c: string) => {
  switch (c) {
    case 'CONNECTED': return <Wifi className="w-3.5 h-3.5 text-green-400" />;
    case 'DEGRADED': return <Wifi className="w-3.5 h-3.5 text-amber-400" />;
    case 'OFFLINE': return <WifiOff className="w-3.5 h-3.5 text-red-400" />;
    default: return <Wifi className="w-3.5 h-3.5 text-polar-500" />;
  }
};

/* --------------------------------------------------------------------------
   MAIN VIEW
   -------------------------------------------------------------------------- */

export const FieldHILValidationView: React.FC = () => {
  const [state, setState] = useState<ValidationState>(MOCK_STATE);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-cyan-950/60 via-polar-900/60 to-purple-950/40 border border-polar-700/40 rounded-xl p-5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
              <Radio className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-polar-100 tracking-tight">
                Field &amp; HIL Validation
              </h2>
              <p className="text-xs text-polar-400 mt-0.5">
                Phase 16 — Device integration, fault injection &amp; reliability validation
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3 text-xs">
            <EnvBadge env={state.environment} />
            <span className="font-mono text-polar-400">
              Station: <span className="text-polar-200 font-semibold">{state.station_id}</span>
            </span>
          </div>
        </div>

        {/* SCADA Disclaimer */}
        <div className="mt-4 flex items-center space-x-2 bg-amber-950/30 border border-amber-700/30 rounded-lg px-3 py-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="text-xs text-amber-300/90 font-medium">
            SCADA: SIMULATION ONLY — No live polar hardware is connected. Physical connectivity: DISCONNECTED.
          </span>
        </div>
      </div>

      {/* Status Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Edge Mode', value: state.edge_mode, icon: <Cpu className="w-4 h-4" /> },
          { label: 'Connectivity', value: state.connectivity_state, icon: connIcon(state.connectivity_state) },
          { label: 'Fallback', value: state.fallback_posture, icon: <Shield className="w-4 h-4 text-amber-400" /> },
          { label: 'Buffer Depth', value: String(state.buffer_depth), icon: <Database className="w-4 h-4 text-blue-400" /> },
        ].map((card) => (
          <div key={card.label} className="bg-polar-900/60 border border-polar-800 rounded-lg p-3 flex items-center space-x-3">
            <div className="text-polar-400">{card.icon}</div>
            <div>
              <div className="text-[10px] text-polar-500 uppercase tracking-wider">{card.label}</div>
              <div className="text-sm text-polar-200 font-mono font-semibold truncate">{card.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Devices Table */}
      <div className="bg-polar-900/50 border border-polar-800 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-polar-800 flex items-center space-x-2">
          <Server className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-polar-200">Device Fleet</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-polar-500 uppercase tracking-wider border-b border-polar-800/50">
                <th className="px-4 py-2 text-left">Device</th>
                <th className="px-4 py-2 text-left">Type</th>
                <th className="px-4 py-2 text-left">Adapter</th>
                <th className="px-4 py-2 text-left">Environment</th>
                <th className="px-4 py-2 text-left">Health</th>
                <th className="px-4 py-2 text-left">Conn</th>
                <th className="px-4 py-2 text-left">Quality</th>
              </tr>
            </thead>
            <tbody>
              {state.devices.map((d) => (
                <tr key={d.device_id} className="border-b border-polar-800/30 hover:bg-polar-800/20 transition-colors">
                  <td className="px-4 py-2 font-mono text-polar-200">{d.device_id}</td>
                  <td className="px-4 py-2 text-polar-400">{d.device_type}</td>
                  <td className="px-4 py-2 text-polar-400">{d.adapter}</td>
                  <td className="px-4 py-2"><EnvBadge env={d.environment} /></td>
                  <td className="px-4 py-2 flex items-center space-x-1">{healthIcon(d.health)}<span className="text-polar-300">{d.health}</span></td>
                  <td className="px-4 py-2 flex items-center space-x-1">{connIcon(d.connectivity)}<span className="text-polar-300">{d.connectivity}</span></td>
                  <td className="px-4 py-2 text-polar-300">{d.telemetry_quality}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Active Faults */}
      <div className="bg-polar-900/50 border border-polar-800 rounded-xl">
        <div className="px-4 py-3 border-b border-polar-800 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <h3 className="text-sm font-semibold text-polar-200">Active Faults</h3>
          <span className="text-[10px] bg-red-950/50 text-red-400 border border-red-800/40 px-1.5 py-0.5 rounded font-mono">
            {state.active_faults.length}
          </span>
        </div>
        <div className="p-4 space-y-2">
          {state.active_faults.length === 0 ? (
            <p className="text-xs text-polar-500">No active faults.</p>
          ) : (
            state.active_faults.map((f, idx) => (
              <div key={idx} className="flex items-center space-x-3 bg-red-950/20 border border-red-900/30 rounded-lg px-3 py-2">
                <XCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-mono text-red-300">{f.fault_class}/{f.fault_type}</span>
                  <span className="text-polar-500 mx-1">→</span>
                  <span className="text-xs text-polar-400">{f.target}</span>
                </div>
                <span className="text-[10px] text-polar-500">{f.timestamp}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Actuation & Trace */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Authorization / Actuation */}
        <div className="bg-polar-900/50 border border-polar-800 rounded-xl p-4">
          <div className="flex items-center space-x-2 mb-3">
            <Zap className="w-4 h-4 text-yellow-400" />
            <h3 className="text-sm font-semibold text-polar-200">Actuation Boundary</h3>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-polar-500">Authorization</span>
              <span className={state.actuation_auth ? 'text-green-400' : 'text-red-400'}>
                {state.actuation_auth ? 'AUTHORIZED' : 'DENIED'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-polar-500">Last Outcome</span>
              <span className="text-polar-300 font-mono">{state.last_actuation_outcome}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-polar-500">Reconciliation</span>
              <span className="text-polar-300 font-mono">{state.reconciliation_status}</span>
            </div>
          </div>
        </div>

        {/* Trace */}
        <div className="bg-polar-900/50 border border-polar-800 rounded-xl p-4">
          <div className="flex items-center space-x-2 mb-3">
            <GitBranch className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-polar-200">Decision Trace</h3>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-polar-500">Trace ID</span>
              <span className="text-purple-300 font-mono">{state.trace_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-polar-500">Validation Result</span>
              <span className={state.validation_result === 'PASS' ? 'text-green-400 font-semibold' : 'text-red-400 font-semibold'}>
                {state.validation_result}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-polar-500">Provenance</span>
              <span className="text-cyan-400 font-mono">SIMULATED</span>
            </div>
          </div>
        </div>
      </div>

      {/* Physical Boundary Disclaimer */}
      <div className="bg-polar-900/40 border border-polar-800/50 rounded-lg p-3 flex items-start space-x-2">
        <Info className="w-4 h-4 text-polar-500 shrink-0 mt-0.5" />
        <div className="text-[11px] text-polar-500 space-y-0.5">
          <p><strong className="text-polar-400">Physical Status:</strong> PHYSICAL_CONNECTIVITY = DISCONNECTED | PHYSICAL_SCADA_LINK = FALSE | PHYSICAL_VALIDATION = NOT_AVAILABLE</p>
          <p>All data shown is from software simulation, emulator, or HIL test infrastructure. No live polar SCADA telemetry is present.</p>
          <p>Environment labels (HIL, LAB, EMULATOR, SIMULATION) are source classifications, NOT provenance tiers.</p>
        </div>
      </div>
    </div>
  );
};
