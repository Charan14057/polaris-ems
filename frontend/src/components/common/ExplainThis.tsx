import React, { useState } from 'react';
import { HelpCircle, ChevronDown, ChevronUp, ArrowRight, BookOpen, Layers } from 'lucide-react';
import { useEvidence, EvidenceRecord } from '../../context/EvidenceContext';

export interface ExplainThisProps {
  title?: string;
  whatAmILookingAt: string;
  whyIsItImportant: string;
  howIsItCalculated?: string;
  technicalEvidence?: string;
  evidenceRecord?: EvidenceRecord;
  className?: string;
  defaultExpanded?: boolean;
}

export const ExplainThis: React.FC<ExplainThisProps> = ({
  title = 'What am I looking at?',
  whatAmILookingAt,
  whyIsItImportant,
  howIsItCalculated,
  technicalEvidence,
  evidenceRecord,
  className = '',
  defaultExpanded = false,
}) => {
  const [isOpen, setIsOpen] = useState(defaultExpanded);
  const [showTechnicalMath, setShowTechnicalMath] = useState(false);
  const { inspectEvidence } = useEvidence();

  return (
    <div className={`rounded border border-border-subtle bg-surface/90 overflow-hidden text-xs transition-all ${className}`}>
      {/* Header bar */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 flex items-center justify-between bg-canvas-subtle hover:bg-canvas text-left transition-colors font-sans"
        aria-expanded={isOpen}
      >
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded bg-copper-soft text-copper shrink-0">
            <BookOpen className="w-3.5 h-3.5" />
          </div>
          <span className="font-semibold text-ink-primary text-xs">
            {title}
          </span>
          <span className="text-[10px] font-mono text-copper uppercase tracking-wider px-1.5 py-0.2 rounded bg-copper-soft/60">
            Plain English
          </span>
        </div>
        <div className="flex items-center space-x-1.5 text-ink-muted">
          <span className="text-[11px] font-mono">{isOpen ? 'Hide Explanation' : 'Explain This'}</span>
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {/* Expanded Explanation Body */}
      {isOpen && (
        <div className="p-4 space-y-3 font-sans border-t border-border-subtle bg-canvas/30 animate-in fade-in duration-150">
          {/* Question 1: What am I looking at? */}
          <div className="space-y-1">
            <div className="flex items-center space-x-1.5 text-[11px] font-mono font-semibold text-copper uppercase tracking-wide">
              <span>1. WHAT AM I LOOKING AT?</span>
            </div>
            <p className="text-xs text-ink-secondary leading-relaxed pl-3 border-l-2 border-copper/30">
              {whatAmILookingAt}
            </p>
          </div>

          {/* Question 2: Why is it important? */}
          <div className="space-y-1">
            <div className="flex items-center space-x-1.5 text-[11px] font-mono font-semibold text-teal uppercase tracking-wide">
              <span>2. WHY IS IT IMPORTANT?</span>
            </div>
            <p className="text-xs text-ink-secondary leading-relaxed pl-3 border-l-2 border-teal/30">
              {whyIsItImportant}
            </p>
          </div>

          {/* Question 3: How is it calculated? (Expandable Progressive Disclosure) */}
          {howIsItCalculated && (
            <div className="space-y-1">
              <div className="flex items-center space-x-1.5 text-[11px] font-mono font-semibold text-ink-muted uppercase tracking-wide">
                <span>3. HOW IS IT CALCULATED?</span>
              </div>
              <p className="text-xs text-ink-muted leading-relaxed pl-3 border-l-2 border-border">
                {howIsItCalculated}
              </p>
            </div>
          )}

          {/* Footer Actions: Technical Math + Provenance Drawer Link */}
          <div className="pt-2 border-t border-border-subtle flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono">
            {technicalEvidence && (
              <button
                type="button"
                onClick={() => setShowTechnicalMath(!showTechnicalMath)}
                className="text-ink-secondary hover:text-ink-primary flex items-center space-x-1 underline"
              >
                <Layers className="w-3 h-3 text-copper" />
                <span>{showTechnicalMath ? 'Hide Math & Invariant' : 'Inspect Mathematical Invariant'}</span>
              </button>
            )}

            {evidenceRecord && (
              <button
                type="button"
                onClick={() => inspectEvidence(evidenceRecord)}
                className="inline-flex items-center text-copper hover:text-copper-dark font-medium space-x-1"
              >
                <span>View Full Technical Evidence Drawer</span>
                <ArrowRight className="w-3 h-3 ml-0.5" />
              </button>
            )}
          </div>

          {/* Deeper Math / Model Invariant Drawer */}
          {showTechnicalMath && technicalEvidence && (
            <div className="mt-2 p-2.5 rounded bg-surface border border-border text-[11px] font-mono text-ink-secondary space-y-1">
              <div className="text-ink-primary font-semibold text-[10px] uppercase text-copper">
                GOVERNING ENGINEERING INVARIANT
              </div>
              <p className="leading-relaxed">
                {technicalEvidence}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
