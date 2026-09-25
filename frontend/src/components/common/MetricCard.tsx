import React, { ReactNode } from 'react';
import { ProvenanceTier } from '../../api/types';
import { ProvenanceTag } from './ProvenanceTag';
import { useEvidence } from '../../context/EvidenceContext';
import { Info } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  icon?: ReactNode;
  provenance?: ProvenanceTier | string;
  timestamp?: string;
  statusBadge?: ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  highlight?: boolean;
  className?: string;
  inspectable?: boolean;
  source?: string;
  station?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  icon,
  provenance,
  timestamp,
  statusBadge,
  trend,
  highlight = false,
  className = '',
  inspectable = true,
  source = 'Polaris Station Instrumentation Subsystem',
  station,
}) => {
  const { inspectEvidence } = useEvidence();

  const handleInspect = (e: React.MouseEvent) => {
    e.stopPropagation();
    inspectEvidence({
      title,
      value,
      unit,
      source,
      provenance: (provenance as any) || 'CONFIGURED',
      timestamp: timestamp || new Date().toISOString(),
      station,
      mathematicalBasis: 'Physical measurement or computational model state',
    });
  };

  return (
    <div 
      className={`p-4 sm:p-5 rounded transition-all duration-200 ${
        highlight 
          ? 'bg-surface border border-copper shadow-raised' 
          : 'editorial-sheet hover:border-border hover:shadow-raised'
      } ${className}`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center space-x-2 text-ink-muted text-xs font-mono uppercase tracking-wider">
          {icon && <span className="text-copper">{icon}</span>}
          <span>{title}</span>
        </div>
        <div className="flex items-center space-x-1.5">
          {statusBadge}
          {provenance && <ProvenanceTag provenance={provenance} size="xs" />}
          {inspectable && (
            <button
              type="button"
              onClick={handleInspect}
              className="text-ink-muted hover:text-copper p-0.5 rounded transition-colors"
              title={`Inspect evidence for ${title}`}
              aria-label={`Inspect evidence for ${title}`}
            >
              <Info className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="flex items-baseline space-x-1.5 my-1">
        <span className="text-2xl sm:text-3xl font-bold font-mono-numbers text-ink-primary tracking-tight">
          {value}
        </span>
        {unit && (
          <span className="text-xs font-mono text-ink-muted font-normal">
            {unit}
          </span>
        )}
      </div>

      {(subtitle || trend || timestamp) && (
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-border-subtle text-[11px] text-ink-muted">
          <span>{subtitle}</span>
          {trend && (
            <span className={`font-mono font-medium ${trend.isPositive ? 'text-moss' : 'text-copper'}`}>
              {trend.value}
            </span>
          )}
          {timestamp && (
            <span className="font-mono text-[10px] text-ink-muted">
              Snapshot: {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
