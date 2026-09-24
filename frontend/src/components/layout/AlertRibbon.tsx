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
    ? 'bg-red-950/70 border-red-500/40 text-red-200'
    : isWarning
    ? 'bg-amber-950/70 border-amber-500/40 text-amber-200'
    : 'bg-blue-950/70 border-blue-500/40 text-blue-200';

  const icon = isCritical ? (
    <AlertOctagon className="w-4 h-4 text-red-400 shrink-0 animate-pulse" />
  ) : (
    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
  );

  const handleAction = onNavigateToPolicy || onInspect;

  return (
    <div 
      className={`px-4 py-2 border-b text-xs flex items-center justify-between gap-3 ${style}`}
      role="alert"
    >
      <div className="flex items-center space-x-2.5 overflow-hidden">
        {icon}
        <span className="font-semibold uppercase tracking-wider font-mono">
          [{topThreat.severity}] {topThreat.threat_type.replace(/_/g, ' ')}:
        </span>
        <span className="truncate">
          {topThreat.trigger_condition || topThreat.threat_type}
        </span>
      </div>

      {threats.length > 1 && (
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/30 whitespace-nowrap">
          +{threats.length - 1} more alert{threats.length > 2 ? 's' : ''}
        </span>
      )}

      {handleAction && (
        <button
          onClick={handleAction}
          className="inline-flex items-center space-x-1 font-semibold hover:underline shrink-0 text-cyan-300"
        >
          <span>Inspect Protocol</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};
