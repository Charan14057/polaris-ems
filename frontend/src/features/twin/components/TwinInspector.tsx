/**
 * POLARIS-EMS — Digital Twin Inspector Component
 * Phase 18: Spatial Digital Twin Engine
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
      modelOrSubsystem: 'Phase 4 Digital Twin Energy Flow Engine',
      mathematicalBasis: 'Kirchhoff Current Law + Inverter PF Model: I = P / (sqrt(3) * V * pf)',
      governingInvariant: 'Sum(P_gen) = P_served + P_bess_charge (Conservation of Energy)',
      decisionImpact: 'Validates electrical safety margin and feeder loading without physical SCADA connection'
    };
    inspectEvidence(record);
  };

  return (
    <div className="w-full lg:w-80 rounded-lg bg-surface border border-border shadow-raised flex flex-col font-sans select-none overflow-hidden animate-in slide-in-from-right duration-200">
      {/* Inspector Header */}
      <div className="px-4 py-3 border-b border-border bg-canvas-subtle flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded bg-copper-soft text-copper">
            <Cpu className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="text-[9px] font-mono uppercase tracking-widest text-copper font-bold block">
              SYSTEM INSPECTOR
            </span>
            <h4 className="text-xs font-serif font-bold text-ink-primary truncate max-w-[180px]">
              {device?.name || zone?.name || selectedNodeLabel || 'Selected Element'}
            </h4>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 rounded text-ink-muted hover:text-ink-primary hover:bg-canvas transition-colors"
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
                device.category === 'CRITICAL' ? 'bg-moss-soft text-moss' : 'bg-canvas-subtle text-ink-secondary'
              }`}>
                {device.category} • RANK {device.priorityRank}
              </span>
              <StatusBadge status={device.status} size="sm" />
            </div>

            {/* LAYER 1: Non-Technical Comprehension Section (Mandatory Section 20) */}
            <div className="space-y-2.5 p-3 rounded bg-canvas-subtle border border-border-subtle">
              <div>
                <span className="text-[10px] font-mono uppercase text-copper font-bold block mb-0.5">
                  WHAT THIS DOES
                </span>
                <p className="text-xs text-ink-primary leading-relaxed font-medium">
                  {device.whatItDoes}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-teal font-bold block mb-0.5">
                  CURRENT STATE
                </span>
                <p className="text-xs text-ink-primary font-mono">
                  {device.status === 'FAULT' ? (
                    <span className="text-red-600 font-bold">CIRCUIT TRIP • 0.0 kW (Offline)</span>
                  ) : (
                    <span>Drawing <strong className="text-copper">{device.currentPowerKw.toFixed(1)} kW</strong> of {device.nominalPowerKw.toFixed(1)} kW capacity</span>
                  )}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-ink-muted font-bold block mb-0.5">
                  WHY IT MATTERS
                </span>
                <p className="text-xs text-ink-secondary leading-relaxed">
                  {device.whyItMatters}
                </p>
              </div>
            </div>

            {/* Trace My Power Signature Interaction */}
            <button
              type="button"
              onClick={onToggleTracePower}
              className={`w-full py-2 px-3 rounded flex items-center justify-between text-xs font-mono font-medium transition-all ${
                tracePowerActive
                  ? 'bg-copper text-ink-inverse shadow-xs'
                  : 'bg-surface hover:bg-canvas border border-border hover:border-copper/70 text-ink-primary'
              }`}
            >
              <span className="flex items-center space-x-1.5">
                <Compass className="w-3.5 h-3.5 text-copper" />
                <span>{tracePowerActive ? 'Stop Power Trace' : 'Trace My Power Route'}</span>
              </span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            {/* LAYER 2: Expandable Technical View */}
            <div className="border-t border-border-subtle pt-3">
              <button
                type="button"
                onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                className="w-full flex items-center justify-between text-ink-secondary hover:text-ink-primary font-mono text-[11px] underline"
              >
                <span>{showTechnicalDetails ? 'Hide Technical Parameters' : 'View Engineering Specs →'}</span>
                <Layers className="w-3 h-3 text-copper" />
              </button>

              {showTechnicalDetails && (
                <div className="mt-3 space-y-2 font-mono text-[11px] text-ink-secondary p-2.5 rounded bg-surface border border-border-subtle animate-in fade-in duration-150">
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Circuit ID:</span>
                    <span className="font-semibold text-ink-primary">{device.circuitId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Bus Voltage:</span>
                    <span className="text-ink-primary">{device.nominalVoltageV}V 3-Phase</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Rated Power:</span>
                    <span className="text-ink-primary">{device.nominalPowerKw.toFixed(1)} kW</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Operating Current:</span>
                    <span className="text-ink-primary">
                      {device.currentAmps !== null ? `${device.currentAmps.toFixed(1)} A (Derived)` : '—'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Location Zone:</span>
                    <span className="text-ink-primary">{device.zoneName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Thermal Impact:</span>
                    <span className="text-ink-primary">{device.thermalConsequence}</span>
                  </div>
                  <div className="flex justify-between items-center pt-1 border-t border-border-subtle">
                    <span className="text-ink-muted">Provenance:</span>
                    <ProvenanceTag provenance={device.provenance} size="xs" />
                  </div>
                </div>
              )}
            </div>

            {/* Evidence Drawer Trigger */}
            <div className="pt-2 border-t border-border-subtle">
              <button
                type="button"
                onClick={handleOpenEvidence}
                className="w-full py-1.5 px-3 rounded bg-canvas-subtle hover:bg-canvas text-copper hover:text-copper-dark font-mono text-[10px] font-semibold flex items-center justify-center space-x-1.5 border border-border-subtle"
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
              <span className="text-[10px] font-mono uppercase text-copper font-bold block mb-0.5">
                ARCHITECTURAL ZONE
              </span>
              <h4 className="text-sm font-bold text-ink-primary font-serif">
                {zone.name}
              </h4>
              <p className="text-xs text-ink-muted font-mono mt-0.5">
                CATEGORY: {zone.category}
              </p>
            </div>

            <div className="p-3 rounded bg-canvas-subtle border border-border-subtle space-y-2 font-mono text-xs">
              <div className="flex justify-between">
                <span className="text-ink-muted">Total Zone Load:</span>
                <span className="font-bold text-copper">{zone.totalLoadKw.toFixed(1)} kW</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-muted">Critical Load:</span>
                <span className="font-semibold text-moss">{zone.criticalLoadKw.toFixed(1)} kW</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-muted">Connected Systems:</span>
                <span className="text-ink-primary">{zone.connectedDeviceCount} Devices</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-muted">Online / Energized:</span>
                <span className="text-moss font-semibold">{zone.activeDeviceCount} Devices</span>
              </div>
            </div>

            {zone.hasFault && (
              <div className="p-2.5 rounded bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
                <span>Active circuit fault detected within this zone.</span>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-2 font-mono text-xs">
            <span className="text-[10px] font-mono uppercase text-copper font-bold block">
              POWER SYSTEM ELEMENT
            </span>
            <p className="text-sm font-serif font-bold text-ink-primary">
              {selectedNodeLabel}
            </p>
            <p className="text-ink-secondary text-xs">
              Main switchboard distribution point connecting upstream generation sources to downstream building sub-panels.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
