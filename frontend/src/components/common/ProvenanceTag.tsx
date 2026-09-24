import React from 'react';
import { ProvenanceTier } from '../../api/types';
import { Database, FileText, Cpu, Sparkles, TrendingUp, Activity } from 'lucide-react';

interface ProvenanceTagProps {
  provenance: ProvenanceTier | string;
  size?: 'xs' | 'sm' | 'md';
  className?: string;
}

export const ProvenanceTag: React.FC<ProvenanceTagProps> = ({ 
  provenance, 
  size = 'xs',
  className = '' 
}) => {
  const norm = (provenance || 'CONFIGURED').toUpperCase() as ProvenanceTier;

  const getMeta = () => {
    switch (norm) {
      case 'REAL':
        return {
          bg: 'bg-emerald-950/60 border-emerald-500/30 text-emerald-400',
          icon: <Database className="w-3 h-3" />,
          label: 'REAL',
          title: 'Direct sensor measurement / validated weather station record',
        };
      case 'CONFIGURED':
        return {
          bg: 'bg-cyan-950/60 border-cyan-500/30 text-cyan-400',
          icon: <FileText className="w-3 h-3" />,
          label: 'CONFIGURED',
          title: 'Authoritative station engineering specification & asset limits',
        };
      case 'ASSUMED':
        return {
          bg: 'bg-indigo-950/60 border-indigo-500/30 text-indigo-400',
          icon: <Cpu className="w-3 h-3" />,
          label: 'ASSUMED',
          title: 'Stated engineering approximation / baseline heuristic',
        };
      case 'SYNTHETIC':
        return {
          bg: 'bg-teal-950/60 border-teal-500/30 text-teal-400',
          icon: <Sparkles className="w-3 h-3" />,
          label: 'CALIBRATED MODEL',
          title: 'Physics-informed calibrated environment model (provenance: SYNTHETIC)',
        };
      case 'FORECAST':
        return {
          bg: 'bg-amber-950/60 border-amber-500/30 text-amber-400',
          icon: <TrendingUp className="w-3 h-3" />,
          label: 'FORECAST',
          title: 'Machine learning prediction with calibrated conformal uncertainty',
        };
      case 'SIMULATED':
      default:
        return {
          bg: 'bg-purple-950/60 border-purple-500/30 text-purple-400',
          icon: <Activity className="w-3 h-3" />,
          label: 'DIGITAL TWIN',
          title: 'Digital Twin simulation / MILP optimization schedule (provenance: SIMULATED)',
        };
    }
  };

  const meta = getMeta();

  const sizeClasses = {
    xs: 'text-[10px] px-1.5 py-0.5 space-x-1',
    sm: 'text-xs px-2 py-0.5 space-x-1',
    md: 'text-xs px-2.5 py-1 space-x-1.5 font-medium',
  }[size];

  return (
    <span 
      className={`inline-flex items-center border rounded font-mono font-medium uppercase tracking-wider ${meta.bg} ${sizeClasses} ${className}`}
      title={meta.title}
      aria-label={`Provenance: ${meta.label}`}
    >
      {meta.icon}
      <span>{meta.label}</span>
    </span>
  );
};
