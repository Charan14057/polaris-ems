import React, { useEffect } from 'react';
import { useEvidence } from '../../context/EvidenceContext';
import { ProvenanceTag } from './ProvenanceTag';
import { X, ShieldCheck, Database, Calendar, Cpu, Activity, Info, FileCode } from 'lucide-react';

export const EvidenceDrawer: React.FC = () => {
  const { activeEvidence, isOpen, closeEvidence } = useEvidence();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        closeEvidence();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, closeEvidence]);

  if (!isOpen || !activeEvidence) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-ink-primary/20 backdrop-blur-xs transition-opacity"
      role="dialog"
      aria-modal="true"
      aria-labelledby="evidence-drawer-title"
      onClick={closeEvidence}
    >
      <div
        className="w-full max-w-lg bg-surface border-l border-border shadow-floating p-6 sm:p-8 flex flex-col justify-between overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div>
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border pb-4 mb-6">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-copper" />
              <span className="text-xs uppercase tracking-widest font-mono text-ink-muted">
                SCIENTIFIC AUDIT & PROVENANCE
              </span>
            </div>
            <button
              onClick={closeEvidence}
              className="p-1.5 rounded text-ink-muted hover:text-ink-primary hover:bg-canvas-subtle transition-colors"
              aria-label="Close evidence inspection drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Metric Headline */}
          <div className="mb-6">
            <h2 id="evidence-drawer-title" className="text-sm font-medium text-ink-secondary mb-1">
              {activeEvidence.title}
            </h2>
            <div className="flex items-baseline space-x-2">
              <span className="text-4xl font-serif text-ink-primary font-bold tracking-tight">
                {activeEvidence.value}
              </span>
              {activeEvidence.unit && (
                <span className="text-lg font-mono text-ink-muted">{activeEvidence.unit}</span>
              )}
            </div>
            <div className="mt-3 flex items-center space-x-2">
              <ProvenanceTag provenance={activeEvidence.provenance} />
              {activeEvidence.station && (
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-canvas-subtle border border-border text-ink-secondary">
                  STATION: {activeEvidence.station}
                </span>
              )}
            </div>
          </div>

          {/* Detailed Verification Ledger */}
          <div className="space-y-4 border-t border-border-subtle pt-4 text-sm">
            {/* Source */}
            <div className="flex items-start space-x-3 p-3 rounded bg-canvas-subtle border border-border-subtle">
              <Database className="w-4 h-4 text-copper mt-0.5 shrink-0" />
              <div className="flex-1">
                <span className="text-xs font-mono uppercase text-ink-muted block">Data Source</span>
                <span className="font-medium text-ink-primary">{activeEvidence.source}</span>
              </div>
            </div>

            {/* Model / Subsystem */}
            {activeEvidence.modelOrSubsystem && (
              <div className="flex items-start space-x-3 p-3 rounded bg-canvas-subtle border border-border-subtle">
                <Cpu className="w-4 h-4 text-ice mt-0.5 shrink-0" />
                <div className="flex-1">
                  <span className="text-xs font-mono uppercase text-ink-muted block">Model / Computational Engine</span>
                  <span className="font-medium text-ink-primary">{activeEvidence.modelOrSubsystem}</span>
                </div>
              </div>
            )}

            {/* Uncertainty Interval */}
            {activeEvidence.uncertainty && (
              <div className="flex items-start space-x-3 p-3 rounded bg-canvas-subtle border border-border-subtle">
                <Activity className="w-4 h-4 text-teal mt-0.5 shrink-0" />
                <div className="flex-1">
                  <span className="text-xs font-mono uppercase text-ink-muted block">Conformal Uncertainty ($P_{10}–P_{90}$)</span>
                  <span className="font-mono text-ink-primary text-xs font-medium">{activeEvidence.uncertainty}</span>
                </div>
              </div>
            )}

            {/* Mathematical Basis / Physical Invariant */}
            {activeEvidence.mathematicalBasis && (
              <div className="flex items-start space-x-3 p-3 rounded bg-canvas-subtle border border-border-subtle">
                <FileCode className="w-4 h-4 text-moss mt-0.5 shrink-0" />
                <div className="flex-1">
                  <span className="text-xs font-mono uppercase text-ink-muted block">Governing Physical Invariant</span>
                  <span className="text-ink-secondary text-xs">{activeEvidence.mathematicalBasis}</span>
                </div>
              </div>
            )}

            {/* Decision Impact */}
            {activeEvidence.decisionImpact && (
              <div className="flex items-start space-x-3 p-3 rounded bg-canvas-subtle border border-border-subtle">
                <Info className="w-4 h-4 text-copper mt-0.5 shrink-0" />
                <div className="flex-1">
                  <span className="text-xs font-mono uppercase text-ink-muted block">Decision Consequence</span>
                  <span className="text-ink-secondary text-xs">{activeEvidence.decisionImpact}</span>
                </div>
              </div>
            )}

            {/* Timestamp */}
            {activeEvidence.timestamp && (
              <div className="flex items-start space-x-3 p-3 rounded bg-canvas-subtle border border-border-subtle">
                <Calendar className="w-4 h-4 text-ink-muted mt-0.5 shrink-0" />
                <div className="flex-1">
                  <span className="text-xs font-mono uppercase text-ink-muted block">Telemetry Snapshot Timestamp</span>
                  <span className="font-mono text-ink-secondary text-xs">{activeEvidence.timestamp}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Guarantee */}
        <div className="mt-8 pt-4 border-t border-border flex items-center justify-between text-xs text-ink-muted">
          <div className="flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-moss" />
            <span>Immutable 6-Tier Data Contract</span>
          </div>
          <span className="font-mono text-[10px]">POLARIS-EVIDENCE-V1</span>
        </div>
      </div>
    </div>
  );
};
