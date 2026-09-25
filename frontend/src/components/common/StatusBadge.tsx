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
  Clock,
  Activity
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
          bg: 'bg-moss-soft border-moss/30 text-moss-dark',
          dot: 'bg-moss',
          icon: <ShieldCheck className="w-3.5 h-3.5 shrink-0" />,
          label: norm,
        };
      case 'WATCH':
      case 'MONITOR':
        return {
          bg: 'bg-ice-soft border-ice/30 text-ice-dark',
          dot: 'bg-ice',
          icon: <Info className="w-3.5 h-3.5 shrink-0" />,
          label: norm,
        };
      case 'AT_RISK':
      case 'PREPARE':
      case 'WARNING':
        return {
          bg: 'bg-copper-soft border-copper/30 text-copper-dark',
          dot: 'bg-copper',
          icon: <AlertTriangle className="w-3.5 h-3.5 shrink-0" />,
          label: norm.replace('_', ' '),
        };
      case 'THREATENED':
      case 'MITIGATE':
        return {
          bg: 'bg-orange-50 border-orange-200 text-orange-800',
          dot: 'bg-orange-600',
          icon: <Flame className="w-3.5 h-3.5 shrink-0" />,
          label: norm.replace('_', ' '),
        };
      case 'CRITICAL':
      case 'EMERGENCY':
      case 'DEFICIT':
      case 'FAILED':
      case 'ERROR':
        return {
          bg: 'bg-red-50 border-red-200 text-red-800',
          dot: 'bg-red-600',
          icon: <AlertOctagon className="w-3.5 h-3.5 shrink-0" />,
          label: norm,
        };
      case 'RECOVERY':
      case 'RECONCILING':
        return {
          bg: 'bg-indigo-50 border-indigo-200 text-indigo-800',
          dot: 'bg-indigo-600',
          icon: <RefreshCw className="w-3.5 h-3.5 shrink-0" />,
          label: norm,
        };
      case 'BLOCKED':
      case 'FALLBACK':
      case 'OVERRIDDEN':
        return {
          bg: 'bg-stone-100 border-stone-200 text-stone-700',
          dot: 'bg-stone-500',
          icon: <Slash className="w-3.5 h-3.5 shrink-0" />,
          label: norm,
        };
      default:
        return {
          bg: 'bg-canvas-subtle border-border text-ink-secondary',
          dot: 'bg-ink-muted',
          icon: <Clock className="w-3.5 h-3.5 shrink-0" />,
          label: norm.replace('_', ' '),
        };
    }
  };

  const style = getStyle();

  const sizeClasses = {
    sm: 'text-[10px] px-1.5 py-0.5 space-x-1',
    md: 'text-xs px-2.5 py-1 space-x-1.5',
    lg: 'text-sm px-3 py-1.5 space-x-2',
  }[size];

  return (
    <span 
      className={`inline-flex items-center font-mono font-medium rounded border shadow-xs tracking-wider transition-colors ${style.bg} ${sizeClasses} ${className}`}
      role="status"
    >
      {showIcon && (
        <span className="flex items-center">
          {style.icon}
        </span>
      )}
      <span>{style.label}</span>
    </span>
  );
};
