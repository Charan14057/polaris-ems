import React from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  AlertOctagon, 
  Flame, 
  RefreshCw, 
  Info, 
  Slash,
  CheckCircle2,
  Clock
} from 'lucide-react';
import { ResilienceState, PolicyState } from '../../api/types';

interface StatusBadgeProps {
  status: ResilienceState | PolicyState | string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ 
  status, 
  size = 'md', 
  showIcon = true,
  className = '' 
}) => {
  const norm = (status || '').toUpperCase();

  const getStyle = () => {
    switch (norm) {
      case 'SAFE':
      case 'NO_ACTION':
      case 'VALID':
      case 'APPROVED':
      case 'COMPLETED':
      case 'SUCCESS':
        return {
          bg: 'bg-emerald-950/80 border-emerald-500/40 text-emerald-400',
          dot: 'bg-emerald-400',
          icon: <ShieldCheck className="w-3.5 h-3.5" />,
          label: norm,
        };
      case 'WATCH':
      case 'MONITOR':
        return {
          bg: 'bg-blue-950/80 border-blue-500/40 text-blue-400',
          dot: 'bg-blue-400',
          icon: <Info className="w-3.5 h-3.5" />,
          label: norm,
        };
      case 'AT_RISK':
      case 'PREPARE':
      case 'WARNING':
        return {
          bg: 'bg-amber-950/80 border-amber-500/40 text-amber-400',
          dot: 'bg-amber-400',
          icon: <AlertTriangle className="w-3.5 h-3.5" />,
          label: norm.replace('_', ' '),
        };
      case 'THREATENED':
      case 'MITIGATE':
      case 'PROTECT':
        return {
          bg: 'bg-orange-950/80 border-orange-500/40 text-orange-400',
          dot: 'bg-orange-400',
          icon: <Flame className="w-3.5 h-3.5" />,
          label: norm,
        };
      case 'CRITICAL':
      case 'ESCALATE':
      case 'FAILED':
      case 'ERROR':
        return {
          bg: 'bg-red-950/80 border-red-500/40 text-red-400',
          dot: 'bg-red-400',
          icon: <AlertOctagon className="w-3.5 h-3.5" />,
          label: norm,
        };
      case 'RECOVERY':
      case 'RECOVER':
        return {
          bg: 'bg-purple-950/80 border-purple-500/40 text-purple-400',
          dot: 'bg-purple-400',
          icon: <RefreshCw className="w-3.5 h-3.5" />,
          label: norm,
        };
      case 'BLOCKED':
      case 'INFEASIBLE':
        return {
          bg: 'bg-slate-900 border-slate-600 text-slate-400',
          dot: 'bg-slate-400',
          icon: <Slash className="w-3.5 h-3.5" />,
          label: norm,
        };
      case 'FALLBACK':
      case 'PARTIAL':
        return {
          bg: 'bg-amber-950/60 border-amber-600/40 text-amber-300',
          dot: 'bg-amber-300',
          icon: <Clock className="w-3.5 h-3.5" />,
          label: norm,
        };
      default:
        return {
          bg: 'bg-slate-900 border-slate-700 text-slate-300',
          dot: 'bg-slate-400',
          icon: <CheckCircle2 className="w-3.5 h-3.5" />,
          label: norm,
        };
    }
  };

  const style = getStyle();

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 space-x-1',
    md: 'text-xs px-2.5 py-1 space-x-1.5',
    lg: 'text-sm px-3.5 py-1.5 space-x-2 font-medium',
  }[size];

  return (
    <span 
      className={`inline-flex items-center font-mono-numbers font-semibold border rounded-full uppercase tracking-wider ${style.bg} ${sizeClasses} ${className}`}
      role="status"
      aria-label={`Status: ${style.label}`}
    >
      {showIcon && style.icon}
      <span>{style.label}</span>
    </span>
  );
};
