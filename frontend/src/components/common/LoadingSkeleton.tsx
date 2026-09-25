import React from 'react';

export const LoadingSkeleton: React.FC<{ rows?: number; height?: string; className?: string }> = ({
  rows = 3,
  height = 'h-16',
  className = '',
}) => {
  return (
    <div className={`space-y-3 animate-pulse ${className}`} role="status" aria-label="Loading data">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className={`bg-canvas-subtle border border-border-subtle rounded ${height} w-full`} />
      ))}
      <span className="sr-only">Loading operational telemetry...</span>
    </div>
  );
};
