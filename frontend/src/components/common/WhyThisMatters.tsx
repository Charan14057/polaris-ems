import React, { useState } from 'react';
import { Sparkles, ChevronDown, ChevronUp, ArrowRight } from 'lucide-react';

export interface WhyThisMattersProps {
  headline?: string;
  summary: string;
  technicalDetail?: string;
  invariant?: string;
  stage?: string;
  onExplore?: () => void;
  exploreLabel?: string;
  className?: string;
}

export const WhyThisMatters: React.FC<WhyThisMattersProps> = ({
  headline,
  summary,
  technicalDetail,
  invariant,
  stage,
  onExplore,
  exploreLabel = 'Inspect Technical Evidence',
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  return (
    <div
      className={`p-4 sm:p-5 rounded border border-border bg-canvas-subtle transition-all duration-200 ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start space-x-3">
          <div className="p-1.5 rounded bg-copper-soft text-copper shrink-0 mt-0.5">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-mono uppercase tracking-widest text-[#B45309] font-semibold">
                WHY THIS MATTERS {stage ? `— ${stage}` : ''}
              </span>
            </div>
            {headline && (
              <h4 className="text-sm font-semibold text-[#1C1917] mt-0.5">
                {headline}
              </h4>
            )}
            <p className="text-xs sm:text-sm text-[#57534E] mt-1 leading-relaxed">
              {summary}
            </p>
          </div>
        </div>

        {(technicalDetail || invariant) && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded text-[#78716C] hover:text-[#1C1917] hover:bg-[#F6F3EC] transition-colors shrink-0"
            aria-expanded={isExpanded}
            aria-label="Toggle technical explanation"
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        )}
      </div>

      {isExpanded && (technicalDetail || invariant) && (
        <div className="mt-3 pt-3 border-t border-[#DDD6C6] pl-9 text-xs text-[#57534E] leading-relaxed font-mono space-y-1.5">
          {technicalDetail && (
            <div>
              <span className="text-[#1C1917] font-semibold block mb-0.5">Technical Invariant & Model Mechanics:</span>
              {technicalDetail}
            </div>
          )}
          {invariant && (
            <div className="text-[11px] text-[#B45309] font-medium bg-[#FEF3C7]/40 p-2 rounded border border-[#FDE68A]">
              {invariant}
            </div>
          )}
        </div>
      )}

      {onExplore && (
        <div className="mt-3 pt-2 pl-9">
          <button
            onClick={onExplore}
            className="inline-flex items-center text-xs font-medium text-copper hover:text-copper-dark transition-colors group"
          >
            <span>{exploreLabel}</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-0.5" />
          </button>
        </div>
      )}
    </div>
  );
};
