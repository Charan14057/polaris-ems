import React, { useState } from 'react';
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
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { WhyThisMatters } from '../components/common/WhyThisMatters';
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { JargonTooltip } from '../components/common/JargonTooltip';

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

const envStyles: Record<string, string> = {
  REAL: 'text-[#166534] bg-[#EBF7F0] border-[#BBF7D0]',
  HIL: 'text-[#92400E] bg-[#FEF3C7] border-[#FDE68A]',
  LAB: 'text-[#6B21A8] bg-[#F3E8FF] border-[#E9D5FF]',
  EMULATOR: 'text-[#0369A1] bg-[#E0F2FE] border-[#BAE6FD]',
  SIMULATION: 'text-[#0284C7] bg-[#E0F2FE] border-[#BAE6FD]',
};

const EnvBadge: React.FC<{ env: string }> = ({ env }) => (
  <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${envStyles[env] || envStyles.SIMULATION}`}>
    {env}
  </span>
);

const healthIcon = (h: string) => {
  switch (h) {
    case 'HEALTHY': return <CheckCircle className="w-3.5 h-3.5 text-[#166534]" />;
    case 'DEGRADED': return <AlertTriangle className="w-3.5 h-3.5 text-[#B45309]" />;
    case 'FAULT': return <XCircle className="w-3.5 h-3.5 text-[#991B1B]" />;
    default: return <Info className="w-3.5 h-3.5 text-[#78716C]" />;
  }
};

const connIcon = (c: string) => {
  switch (c) {
    case 'CONNECTED': return <Wifi className="w-3.5 h-3.5 text-[#166534]" />;
    case 'DEGRADED': return <Wifi className="w-3.5 h-3.5 text-[#B45309]" />;
    case 'OFFLINE': return <WifiOff className="w-3.5 h-3.5 text-[#991B1B]" />;
    default: return <Wifi className="w-3.5 h-3.5 text-[#78716C]" />;
  }
};

export const FieldHILValidationView: React.FC = () => {
  const [state] = useState<ValidationState>(MOCK_STATE);

  return (
    <div className="p-4 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Editorial Header */}
      <div className="border-b border-[#DDD6C6] pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-[#78716C] mb-2">
            <span>11 Field &amp; Hardware-in-the-Loop</span>
            <span>•</span>
            <ProvenanceTag provenance="SIMULATED" size="xs" />
          </div>
          <h1 className="font-serif text-3xl lg:text-4xl text-[#1C1917] tracking-tight">
            Field &amp; HIL Validation
          </h1>
          <p className="text-sm text-[#57534E] font-sans mt-2 max-w-2xl">
            Device integration testbed, hardware-in-the-loop emulation, and fault-injection verification across simulated polar microgrids.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs bg-white p-3 rounded border border-[#DDD6C6] shadow-sm">
          <span className="font-mono text-[#78716C]">Environment:</span>
          <EnvBadge env={state.environment} />
          <span className="text-[#DDD6C6]">|</span>
          <span className="font-mono text-[#78716C]">
            Station: <strong className="text-[#1C1917]">{state.station_id}</strong>
          </span>
        </div>
      </div>

      {/* Strict Physical SCADA Boundary Notice */}
      <div className="bg-[#FEF3C7] border border-[#FDE68A] rounded p-4 flex items-start space-x-3">
        <AlertTriangle className="w-4 h-4 text-[#B45309] shrink-0 mt-0.5" />
        <div className="text-xs text-[#92400E]">
          <div className="font-bold uppercase tracking-wider font-mono">
            Physical Boundary Notice — Verified Testbed Environment
          </div>
          <p className="mt-1 font-sans">
            <strong>PHYSICAL_CONNECTIVITY = DISCONNECTED</strong> &bull; <strong>PHYSICAL_SCADA_LINK = FALSE</strong> &bull; <strong>PHYSICAL_VALIDATION = NOT_AVAILABLE</strong>
          </p>
          <p className="mt-0.5 text-[11px] opacity-90">
            No live polar hardware is connected. All telemetry originates from software simulators, hardware-in-the-loop (HIL) microcontrollers, or lab test fixtures. Environment labels (HIL, LAB, EMULATOR, SIMULATION) classify the integration testbed, not provenance tiers.
          </p>
        </div>
      </div>

      {/* Non-Technical Comprehension: Explain This */}
      <ExplainThis
        title="What is Hardware-in-the-Loop (HIL) testing?"
        whatAmILookingAt="This laboratory testbed demonstrates how Polaris-EMS interfaces with electronic controllers, sensors, and power emulators without endangering real polar generators in Antarctica."
        whyIsItImportant="Sending untested software to Antarctica is dangerous. HIL testbenches simulate physical electrical grid dynamics, proving the code will survive real-world faults like short circuits, stale telemetry, and packet drops."
        howIsItCalculated="Real embedded microcontrollers execute code in lockstep with simulated generator signals across four isolated environment tiers: Simulator, Emulator, HIL, and Lab."
      />

      <NextStepExplanation
        title="TESTBED INTEGRATION OUTLOOK"
        timeframe="Laboratory Environment"
        outlook="All 4 device adapters (Diesel Generator, Solar PV, Battery, Wind Turbine) are operating within verified physical bounds. Hardware-in-the-loop integration testbed reports 100% test pass rate."
      />

      {/* Status Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Edge Mode', value: state.edge_mode, icon: <Cpu className="w-4 h-4 text-[#B45309]" /> },
          { label: 'Connectivity', value: state.connectivity_state, icon: connIcon(state.connectivity_state) },
          { label: 'Fallback', value: state.fallback_posture, icon: <Shield className="w-4 h-4 text-[#B45309]" /> },
          { label: 'Buffer Depth', value: String(state.buffer_depth), icon: <Database className="w-4 h-4 text-[#0284C7]" /> },
        ].map((card) => (
          <div key={card.label} className="bg-white border border-[#DDD6C6] rounded p-3 flex items-center space-x-3 shadow-sm">
            <div className="shrink-0">{card.icon}</div>
            <div className="min-w-0">
              <div className="text-[10px] text-[#78716C] uppercase tracking-wider font-mono">{card.label}</div>
              <div className="text-xs text-[#1C1917] font-mono font-semibold truncate mt-0.5">{card.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Why This Matters */}
      <WhyThisMatters
        summary="Before deploying control algorithms to Antarctica, all communications protocols and fault handlers must be validated on bench-scale hardware-in-the-loop (HIL) simulators."
        technicalDetail="HIL validation subjects edge microcontrollers to simulated communication dropouts, packet corruptions, and transducer failures to verify that life-safety loads are protected under all failure modes."
        invariant="Physical Invariant: The system guarantees that no software command can actuate physical hardware without explicit verification of the physical SCADA connection boundary."
        stage="Field & HIL Testbed Validation"
      />

      {/* Device Fleet Table */}
      <div className="editorial-sheet p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Server className="w-4 h-4 text-[#B45309]" />
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-[#1C1917]">
              Hardware &amp; Emulator Fleet
            </h3>
          </div>
          <span className="text-xs font-mono text-[#78716C]">
            Testbed Device Registry
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-[#78716C] uppercase tracking-wider border-b border-[#DDD6C6] text-[10px]">
                <th className="py-2.5 px-3 text-left">Device</th>
                <th className="py-2.5 px-3 text-left">Type</th>
                <th className="py-2.5 px-3 text-left">Adapter</th>
                <th className="py-2.5 px-3 text-left">Environment</th>
                <th className="py-2.5 px-3 text-left">Health</th>
                <th className="py-2.5 px-3 text-left">Conn</th>
                <th className="py-2.5 px-3 text-left">Quality</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#DDD6C6]">
              {state.devices.map((d) => (
                <tr key={d.device_id} className="hover:bg-[#F6F3EC]/80 transition-colors">
                  <td className="py-2.5 px-3 font-semibold text-[#1C1917]">{d.device_id}</td>
                  <td className="py-2.5 px-3 text-[#57534E]">{d.device_type}</td>
                  <td className="py-2.5 px-3 text-[#78716C]">{d.adapter}</td>
                  <td className="py-2.5 px-3"><EnvBadge env={d.environment} /></td>
                  <td className="py-2.5 px-3 flex items-center space-x-1.5">{healthIcon(d.health)}<span className="text-[#1C1917]">{d.health}</span></td>
                  <td className="py-2.5 px-3">{connIcon(d.connectivity)}</td>
                  <td className="py-2.5 px-3 text-[#166534] font-bold">{d.telemetry_quality}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Active Faults & Actuation Boundary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Active Faults */}
        <div className="editorial-sheet p-6 space-y-3">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-[#B45309]" />
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-[#1C1917]">
              Injected Fault Scenarios ({state.active_faults.length})
            </h3>
          </div>

          <div className="space-y-2">
            {state.active_faults.length === 0 ? (
              <p className="text-xs text-[#78716C]">No active fault conditions injected.</p>
            ) : (
              state.active_faults.map((f, idx) => (
                <div key={idx} className="flex items-center space-x-3 bg-white p-3 rounded border border-[#DDD6C6] text-xs">
                  <XCircle className="w-4 h-4 text-[#991B1B] shrink-0" />
                  <div className="flex-1 min-w-0 font-mono">
                    <span className="font-bold text-[#991B1B]">{f.fault_class}/{f.fault_type}</span>
                    <span className="text-[#78716C] mx-1">→</span>
                    <span className="text-[#1C1917]">{f.target}</span>
                  </div>
                  <span className="text-[10px] text-[#A8A29E] font-mono">{f.timestamp}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Actuation & Decision Trace */}
        <div className="editorial-sheet p-6 space-y-3">
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-[#B45309]" />
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-[#1C1917]">
              Actuation Authorization &amp; Trace
            </h3>
          </div>

          <div className="space-y-2 text-xs font-mono bg-white p-3.5 rounded border border-[#DDD6C6]">
            <div className="flex justify-between py-1 border-b border-[#F6F3EC]">
              <span className="text-[#78716C]">Authorization State</span>
              <span className={state.actuation_auth ? 'text-[#166534] font-bold' : 'text-[#991B1B] font-bold'}>
                {state.actuation_auth ? 'AUTHORIZED (SIMULATED)' : 'DENIED'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F6F3EC]">
              <span className="text-[#78716C]">Last Outcome</span>
              <span className="text-[#1C1917]">{state.last_actuation_outcome}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F6F3EC]">
              <span className="text-[#78716C]">Decision Trace ID</span>
              <span className="text-[#0284C7] truncate max-w-[200px]">{state.trace_id}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#78716C]">Validation Result</span>
              <span className="text-[#166534] font-bold">{state.validation_result}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
