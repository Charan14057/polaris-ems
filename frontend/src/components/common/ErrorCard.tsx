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
      className={`p-5 rounded-lg bg-red-950/20 border border-red-500/30 text-polar-200 ${className}`}
      role="alert"
    >
      <div className="flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-sm text-red-300">{title}</h4>
            {code && (
              <span className="text-[10px] font-mono bg-red-950/80 border border-red-700/50 px-2 py-0.5 rounded text-red-300 uppercase">
                {code}
              </span>
            )}
          </div>
          <p className="text-xs text-polar-300 mt-1 leading-relaxed">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded bg-polar-800 hover:bg-polar-700 border border-polar-600 text-polar-100 transition-colors"
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
