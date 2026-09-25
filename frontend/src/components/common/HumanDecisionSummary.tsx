import React, { useState } from 'react';
import { ShieldCheck, ArrowRight, CheckCircle, ChevronDown, ChevronUp, Cpu, Sparkles } from 'lucide-react';
import { useEvidence, EvidenceRecord } from '../../context/EvidenceContext';

export interface HumanDecisionSummaryProps {
  decision: string;
  because: string;
  toProtect: string;
  confidenceEvidence: string;
  evidenceRecord?: EvidenceRecord;
  onViewTechnicalDetails?: () => void;
  className?: string;
}

export const HumanDecisionSummary: React.FC<HumanDecisionSummaryProps> = ({
  decision,
  because,
  toProtect,
  confidenceEvidence,
  evidenceRecord,
  onViewTechnicalDetails,
  className = '',
}) => {
  const [expanded, setExpanded] = useState(false);
  const { inspectEvidence } = useEvidence();

  return (
    <div className={`editorial-sheet rounded-lg p-5 sm:p-6 border-l-4 border-l-copper shadow-sm ${className}`}>
      <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-copper font-bold mb-3">
        <Sparkles className="w-3.5 h-3.5" />
        <span>HUMAN-READABLE DECISION SUMMARY</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. DECISION */}
        <div className="p-3 rounded bg-canvas-subtle border border-border-subtle flex flex-col justify-between">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-ink-muted block mb-1">
              DECISION
            </span>
            <p className="text-xs sm:text-sm font-semibold text-ink-primary font-sans leading-snug">
              {decision}
            </p>
          </div>
        </div>

        {/* 2. BECAUSE */}
        <div className="p-3 rounded bg-canvas-subtle border border-border-subtle flex flex-col justify-between">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-copper block mb-1">
              BECAUSE
            </span>
            <p className="text-xs text-ink-secondary font-sans leading-relaxed">
              {because}
            </p>
          </div>
        </div>

        {/* 3. TO PROTECT */}
        <div className="p-3 rounded bg-canvas-subtle border border-border-subtle flex flex-col justify-between">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-moss block mb-1">
              TO PROTECT
            </span>
            <p className="text-xs text-ink-secondary font-sans leading-relaxed">
              {toProtect}
            </p>
          </div>
        </div>

        {/* 4. CONFIDENCE / EVIDENCE */}
        <div className="p-3 rounded bg-canvas-subtle border border-border-subtle flex flex-col justify-between">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-teal block mb-1">
              CONFIDENCE & EVIDENCE
            </span>
            <p className="text-xs text-ink-secondary font-sans leading-relaxed">
              {confidenceEvidence}
            </p>
          </div>
        </div>
      </div>

      {/* Footer Navigation / Drawer trigger */}
      <div className="mt-4 pt-3 border-t border-border-subtle flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-2 text-[11px] font-mono text-ink-muted">
          <ShieldCheck className="w-3.5 h-3.5 text-moss" />
          <span>SUPERVISORY PROPOSAL • OPERATOR MUST AUTHORIZE BEFORE ACTUATION</span>
        </div>

        <div className="flex items-center space-x-3">
          {evidenceRecord && (
            <button
              type="button"
              onClick={() => inspectEvidence(evidenceRecord)}
              className="text-copper hover:text-copper-dark font-mono text-xs font-medium inline-flex items-center"
            >
              <span>Inspect Underlying Evidence</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </button>
          )}

          {onViewTechnicalDetails && (
            <button
              type="button"
              onClick={onViewTechnicalDetails}
              className="px-3 py-1 rounded bg-copper text-ink-inverse text-xs font-mono font-medium hover:bg-copper-dark transition-colors inline-flex items-center"
            >
              <span>View Technical Details →</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
