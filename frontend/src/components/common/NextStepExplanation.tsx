import React from 'react';
import { ArrowRight, Compass, Clock, Sparkles } from 'lucide-react';

export interface NextStepExplanationProps {
  title?: string;
  timeframe?: string;
  outlook: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const NextStepExplanation: React.FC<NextStepExplanationProps> = ({
  title = 'WHAT HAPPENS NEXT?',
  timeframe,
  outlook,
  actionText,
  onAction,
  className = '',
}) => {
  return (
    <div className={`p-4 rounded border border-copper/30 bg-copper-soft/30 text-xs text-ink-primary font-sans ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div className="space-y-1 max-w-2xl">
          <div className="flex items-center space-x-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-copper opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-copper"></span>
            </span>
            <span className="text-[11px] font-mono font-bold uppercase tracking-widest text-copper">
              {title}
            </span>
            {timeframe && (
              <span className="flex items-center space-x-1 text-[10px] font-mono text-ink-muted bg-surface px-1.5 py-0.2 rounded border border-border-subtle">
                <Clock className="w-2.5 h-2.5" />
                <span>{timeframe}</span>
              </span>
            )}
          </div>
          <p className="text-xs text-ink-secondary leading-relaxed pt-0.5">
            {outlook}
          </p>
        </div>

        {actionText && onAction && (
          <button
            type="button"
            onClick={onAction}
            className="inline-flex items-center space-x-1 px-3 py-1.5 rounded bg-surface hover:bg-canvas border border-border hover:border-copper/60 text-ink-primary font-mono text-xs font-medium transition-colors shrink-0 shadow-xs self-start"
          >
            <span>{actionText}</span>
            <ArrowRight className="w-3.5 h-3.5 text-copper" />
          </button>
        )}
      </div>
    </div>
  );
};
