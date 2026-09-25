import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorCardProps {
  title?: string;
  message: string;
  code?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorCard: React.FC<ErrorCardProps> = ({
  title = 'Operational Data Unavailable',
  message,
  code,
  onRetry,
  className = '',
}) => {
  return (
    <div 
      className={`p-5 rounded bg-red-50/80 border border-red-200 text-ink-primary ${className}`}
      role="alert"
    >
      <div className="flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-sm text-red-900">{title}</h4>
            {code && (
              <span className="text-[10px] font-mono bg-white border border-red-200 px-2 py-0.5 rounded text-red-800 uppercase font-medium">
                {code}
              </span>
            )}
          </div>
          <p className="text-xs text-ink-secondary mt-1 leading-relaxed">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded bg-white hover:bg-canvas-subtle border border-border text-ink-primary transition-colors shadow-xs"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Request</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
