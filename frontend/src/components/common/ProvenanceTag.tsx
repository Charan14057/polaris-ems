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
          bg: 'bg-moss-soft border-moss/30 text-moss-dark',
          icon: <Database className="w-3 h-3 text-moss" />,
          label: 'REAL',
          title: 'Direct sensor measurement / validated weather station record (provenance: REAL)',
        };
      case 'CONFIGURED':
        return {
          bg: 'bg-ice-soft border-ice/30 text-ice-dark',
          icon: <FileText className="w-3 h-3 text-ice" />,
          label: 'CONFIGURED',
          title: 'Authoritative station engineering specification & asset limits (provenance: CONFIGURED)',
        };
      case 'ASSUMED':
        return {
          bg: 'bg-stone-100 border-stone-200 text-stone-700',
          icon: <Cpu className="w-3 h-3 text-stone-600" />,
          label: 'ASSUMED',
          title: 'Stated engineering approximation / baseline heuristic (provenance: ASSUMED)',
        };
      case 'SYNTHETIC':
        return {
          bg: 'bg-teal-50 border-teal-200 text-teal-800',
          icon: <Sparkles className="w-3 h-3 text-teal" />,
          label: 'SYNTHETIC',
          title: 'Physics-informed synthetic environment model (provenance: SYNTHETIC)',
        };
      case 'FORECAST':
        return {
          bg: 'bg-copper-soft border-copper/30 text-copper-dark',
          icon: <TrendingUp className="w-3 h-3 text-copper" />,
          label: 'FORECAST',
          title: 'Machine learning prediction with calibrated conformal uncertainty (provenance: FORECAST)',
        };
      case 'SIMULATED':
      default:
        return {
          bg: 'bg-purple-50 border-purple-200 text-purple-800',
          icon: <Activity className="w-3 h-3 text-purple-700" />,
          label: 'DIGITAL TWIN',
          title: 'Computed dynamic physics trajectory (provenance: SIMULATED)',
        };
    }
  };

  const meta = getMeta();

  const sizeClasses = {
    xs: 'text-[10px] px-1.5 py-0.5 space-x-1',
    sm: 'text-xs px-2 py-0.5 space-x-1.5',
    md: 'text-xs px-2.5 py-1 space-x-1.5',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-mono font-medium rounded border tracking-wider transition-colors select-none ${meta.bg} ${sizeClasses} ${className}`}
      title={meta.title}
    >
      <span className="shrink-0">{meta.icon}</span>
      <span>{meta.label}</span>
    </span>
  );
};
