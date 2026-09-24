import React, { ReactNode } from 'react';
import { ProvenanceTier } from '../../api/types';
import { ProvenanceTag } from './ProvenanceTag';

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
}) => {
  return (
    <div 
      className={`p-4 rounded-lg transition-all duration-200 ${
        highlight 
          ? 'bg-polar-900/90 border border-cyan-500/40 shadow-lg shadow-cyan-950/20' 
          : 'bg-polar-900/60 border border-polar-750/60 hover:border-polar-600/60'
      } ${className}`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center space-x-2 text-polar-400 text-xs font-medium uppercase tracking-wider">
          {icon && <span className="text-polar-300">{icon}</span>}
          <span>{title}</span>
        </div>
        <div className="flex items-center space-x-1.5">
          {statusBadge}
          {provenance && <ProvenanceTag provenance={provenance} size="xs" />}
        </div>
      </div>

      <div className="flex items-baseline space-x-1.5 my-1">
        <span className="text-2xl font-bold font-mono-numbers text-polar-50 tracking-tight">
          {value}
        </span>
        {unit && (
          <span className="text-xs font-mono text-polar-400 font-normal">
            {unit}
          </span>
        )}
      </div>

      {(subtitle || trend || timestamp) && (
        <div className="flex items-center justify-between text-[11px] text-polar-400 mt-2 pt-2 border-t border-polar-800/80">
          <div>
            {trend && (
              <span className={`font-mono mr-1.5 ${trend.isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                {trend.value}
              </span>
            )}
            {subtitle && <span>{subtitle}</span>}
          </div>
          {timestamp && (
            <span className="text-[10px] font-mono text-polar-500" title={`Timestamp: ${timestamp}`}>
              Snapshot: {timestamp.includes('T') ? timestamp.split('T')[1].substring(0, 5) : timestamp}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
