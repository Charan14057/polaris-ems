import React from 'react';
import { ThreatIndicator } from '../../api/types';
import { AlertTriangle, AlertOctagon, ChevronRight } from 'lucide-react';

interface AlertRibbonProps {
  threats?: ThreatIndicator[];
  onInspect?: () => void;
  onNavigateToPolicy?: () => void;
}

export const AlertRibbon: React.FC<AlertRibbonProps> = ({ threats = [], onInspect, onNavigateToPolicy }) => {
  if (!threats || threats.length === 0) {
    return null;
  }

  const topThreat = threats[0];
  const isCritical = topThreat.severity === 'CRITICAL';
  const isWarning = topThreat.severity === 'WARNING';

  const style = isCritical
    ? 'bg-red-50 border-red-200 text-red-900'
    : isWarning
    ? 'bg-amber-50 border-amber-200 text-amber-900'
    : 'bg-ice-subtle border-border text-ink-primary';

  const icon = isCritical ? (
    <AlertOctagon className="w-4 h-4 text-red-600 shrink-0" />
  ) : (
    <AlertTriangle className="w-4 h-4 text-copper shrink-0" />
  );

  const handleAction = onNavigateToPolicy || onInspect;

  return (
    <div 
      className={`px-4 lg:px-6 py-2.5 border-b text-xs flex items-center justify-between gap-3 ${style}`}
      role="alert"
    >
      <div className="flex items-center space-x-2.5 overflow-hidden">
        {icon}
        <span className="font-semibold uppercase tracking-wider font-mono">
          [{topThreat.severity}] {topThreat.threat_type.replace(/_/g, ' ')}:
        </span>
        <span className="truncate text-ink-secondary">
          {topThreat.trigger_condition || topThreat.threat_type}
        </span>
      </div>

      <div className="flex items-center space-x-3 shrink-0">
        {threats.length > 1 && (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-border-subtle text-ink-muted whitespace-nowrap">
            +{threats.length - 1} more alert{threats.length > 2 ? 's' : ''}
          </span>
        )}

        {handleAction && (
          <button
            onClick={handleAction}
            className="inline-flex items-center space-x-1 font-semibold hover:underline shrink-0 text-copper hover:text-copper-dark"
          >
            <span>Inspect Protocol</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
