/**
 * POLARIS-EMS — Digital Twin Inspector Component
 * Quiet Industrial / Arctic Utility Design
 * 
 * Side drawer/panel displaying two-layer inspection for selected devices, zones, and sources.
 * Integrates Layer 1 Plain English explanations with Layer 2 engineering evidence.
 */

import React, { useState } from 'react';
import {
  X,
  Zap,
  Activity,
  ShieldCheck,
  ArrowRight,
  Layers,
  Sparkles,
  Info,
  CheckCircle,
  AlertTriangle,
  Compass,
  Cpu
} from 'lucide-react';
import { VisualDeviceState, VisualZoneState } from '../model/twinTypes';
import { ProvenanceTag } from '../../../components/common/ProvenanceTag';
import { StatusBadge } from '../../../components/common/StatusBadge';
import { useEvidence, EvidenceRecord } from '../../../context/EvidenceContext';

interface TwinInspectorProps {
  device?: VisualDeviceState | null;
  zone?: VisualZoneState | null;
  selectedNodeLabel?: string | null;
  tracePowerActive: boolean;
  onToggleTracePower: () => void;
  onClose: () => void;
}

export const TwinInspector: React.FC<TwinInspectorProps> = ({
  device,
  zone,
  selectedNodeLabel,
  tracePowerActive,
  onToggleTracePower,
  onClose
}) => {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const { inspectEvidence } = useEvidence();

  if (!device && !zone && !selectedNodeLabel) return null;

  const handleOpenEvidence = () => {
    if (!device) return;
    const record: EvidenceRecord = {
      title: `${device.name} Telemetry & Dispatch Evidence`,
      value: `${device.currentPowerKw} kW (${device.currentAmps !== null ? device.currentAmps + ' A' : '—'})`,
      unit: 'kW',
      source: 'Digital Twin Replay (Phase 4 Authority)',
      provenance: device.provenance,
      timestamp: new Date().toISOString(),
      station: 'BHARATI',
      modelOrSubsystem: 'Digital Twin Energy Flow Engine',
      mathematicalBasis: 'Kirchhoff Current Law + Inverter PF Model: I = P / (sqrt(3) * V * pf)',
      governingInvariant: 'Sum(P_gen) = P_served + P_bess_charge (Conservation of Energy)',
      decisionImpact: 'Validates electrical safety margin and feeder loading without physical SCADA connection'
    };
    inspectEvidence(record);
  };

  return (
    <div className="w-full lg:w-80 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col font-sans select-none overflow-hidden animate-in slide-in-from-right duration-200">
      {/* Inspector Header */}
      <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded bg-sky-100 text-sky-700">
            <Cpu className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="text-[9px] font-mono uppercase tracking-widest text-slate-500 font-bold block">
              SYSTEM INSPECTOR
            </span>
            <h4 className="text-xs font-bold text-slate-900 truncate max-w-[180px]">
              {device?.name || zone?.name || selectedNodeLabel || 'Selected Element'}
            </h4>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Close inspector"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Inspector Body */}
      <div className="p-4 space-y-4 overflow-y-auto max-h-[520px] text-xs">
        {device ? (
          <>
            {/* Status & Category Banner */}
            <div className="flex items-center justify-between">
              <span className={`text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded ${
                device.category === 'CRITICAL' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-700 border border-slate-200'
              }`}>
                {device.category} • RANK {device.priorityRank}
              </span>
              <StatusBadge status={device.status} size="sm" />
            </div>

            {/* LAYER 1: Operational Summary Section */}
            <div className="space-y-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200">
              <div>
                <span className="text-[10px] font-mono uppercase text-sky-700 font-bold block mb-0.5">
                  WHAT THIS DOES
                </span>
                <p className="text-xs text-slate-900 leading-relaxed font-medium">
                  {device.whatItDoes}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-teal-700 font-bold block mb-0.5">
                  CURRENT STATE
                </span>
                <p className="text-xs text-slate-900 font-mono">
                  {device.status === 'FAULT' ? (
                    <span className="text-red-600 font-bold">CIRCUIT TRIP • 0.0 kW (Offline)</span>
                  ) : (
                    <span>Drawing <strong className="text-slate-900 font-bold">{device.currentPowerKw.toFixed(1)} kW</strong> of {device.nominalPowerKw.toFixed(1)} kW capacity</span>
                  )}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block mb-0.5">
                  WHY IT MATTERS
                </span>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {device.whyItMatters}
                </p>
              </div>
            </div>

            {/* Trace My Power Signature Interaction */}
            <button
              type="button"
              onClick={onToggleTracePower}
              className={`w-full py-2 px-3 rounded-md flex items-center justify-between text-xs font-mono font-medium transition-all ${
                tracePowerActive
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'bg-white hover:bg-slate-50 border border-slate-200 hover:border-sky-300 text-slate-800'
              }`}
            >
              <span className="flex items-center space-x-1.5">
                <Compass className={`w-3.5 h-3.5 ${tracePowerActive ? 'text-white' : 'text-sky-600'}`} />
                <span>{tracePowerActive ? 'Stop Power Trace' : 'Trace My Power Route'}</span>
              </span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            {/* LAYER 2: Expandable Technical View */}
            <div className="border-t border-slate-100 pt-3">
              <button
                type="button"
                onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                className="w-full flex items-center justify-between text-slate-600 hover:text-slate-900 font-mono text-[11px] underline"
              >
                <span>{showTechnicalDetails ? 'Hide Technical Parameters' : 'View Engineering Specs →'}</span>
                <Layers className="w-3 h-3 text-sky-600" />
              </button>

              {showTechnicalDetails && (
                <div className="mt-3 space-y-2 font-mono text-[11px] text-slate-600 p-2.5 rounded-md bg-white border border-slate-200 animate-in fade-in duration-150">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Circuit ID:</span>
                    <span className="font-semibold text-slate-800">{device.circuitId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Bus Voltage:</span>
                    <span className="text-slate-800">{device.nominalVoltageV}V 3-Phase</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Rated Power:</span>
                    <span className="text-slate-800">{device.nominalPowerKw.toFixed(1)} kW</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Operating Current:</span>
                    <span className="text-slate-800">
                      {device.currentAmps !== null ? `${device.currentAmps.toFixed(1)} A (Derived)` : '—'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Location Zone:</span>
                    <span className="text-slate-800">{device.zoneName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Thermal Impact:</span>
                    <span className="text-slate-800">{device.thermalConsequence}</span>
                  </div>
                  <div className="flex justify-between items-center pt-1 border-t border-slate-100">
                    <span className="text-slate-400">Provenance:</span>
                    <ProvenanceTag provenance={device.provenance} size="xs" />
                  </div>
                </div>
              )}
            </div>

            {/* Evidence Drawer Trigger */}
            <div className="pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={handleOpenEvidence}
                className="w-full py-1.5 px-3 rounded-md bg-slate-50 hover:bg-slate-100 text-sky-700 font-mono text-[10px] font-semibold flex items-center justify-center space-x-1.5 border border-slate-200 transition-colors"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Open Full Evidence Record</span>
              </button>
            </div>
          </>
        ) : zone ? (
          /* Zone Summary Inspection */
          <div className="space-y-3 font-sans">
            <div>
              <span className="text-[10px] font-mono uppercase text-sky-700 font-bold block mb-0.5">
                ARCHITECTURAL ZONE
              </span>
              <h4 className="text-sm font-bold text-slate-900">
                {zone.name}
              </h4>
              <p className="text-xs text-slate-500 font-mono mt-0.5">
                CATEGORY: {zone.category}
              </p>
            </div>

            <div className="p-3 rounded-md bg-slate-50 border border-slate-200 space-y-2 font-mono text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Total Zone Load:</span>
                <span className="font-bold text-slate-900">{zone.totalLoadKw.toFixed(1)} kW</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Critical Load:</span>
                <span className="font-semibold text-emerald-700">{zone.criticalLoadKw.toFixed(1)} kW</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Connected Systems:</span>
                <span className="text-slate-800">{zone.connectedDeviceCount} Devices</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Online / Energized:</span>
                <span className="text-emerald-700 font-semibold">{zone.activeDeviceCount} Devices</span>
              </div>
            </div>

            {zone.hasFault && (
              <div className="p-2.5 rounded-md bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
                <span>Active circuit fault detected within this zone.</span>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-2 font-mono text-xs">
            <span className="text-[10px] font-mono uppercase text-sky-700 font-bold block">
              POWER SYSTEM ELEMENT
            </span>
            <p className="text-sm font-bold text-slate-900">
              {selectedNodeLabel}
            </p>
            <p className="text-slate-500 text-xs">
              Main switchboard distribution point connecting upstream generation sources to downstream building sub-panels.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
