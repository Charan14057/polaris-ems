/**
 * POLARIS-EMS — Digital Twin Minimap Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders a compact corner minimap illustrating station zones and current viewport bounding box.
 */

import React from 'react';
import { VisualZoneState } from '../model/twinTypes';
import { ViewportState } from '../hooks/useTwinViewport';

interface TwinMinimapProps {
  zones: VisualZoneState[];
  viewport: ViewportState;
  canvasWidth: number;
  canvasHeight: number;
  containerWidth: number;
  containerHeight: number;
}

export const TwinMinimap: React.FC<TwinMinimapProps> = ({
  zones,
  viewport,
  canvasWidth,
  canvasHeight,
  containerWidth,
  containerHeight
}) => {
  // Minimap dimensions
  const miniWidth = 140;
  const miniHeight = 90;
  const scaleX = miniWidth / canvasWidth;
  const scaleY = miniHeight / canvasHeight;

  // Viewport box in canvas coordinates:
  // viewport.panX, viewport.panY, viewport.zoom
  // container visible width in canvas coordinates = containerWidth / viewport.zoom
  const visibleW = Math.min(canvasWidth, containerWidth / Math.max(0.1, viewport.zoom));
  const visibleH = Math.min(canvasHeight, containerHeight / Math.max(0.1, viewport.zoom));
  const visibleX = Math.max(0, -viewport.panX / Math.max(0.1, viewport.zoom));
  const visibleY = Math.max(0, -viewport.panY / Math.max(0.1, viewport.zoom));

  return (
    <div className="absolute bottom-4 right-4 z-20 p-2 rounded bg-surface/90 border border-border shadow-md backdrop-blur-xs select-none hidden sm:block">
      <div className="text-[9px] font-mono font-bold uppercase text-ink-muted mb-1 flex items-center justify-between">
        <span>MINIMAP</span>
        <span>{(viewport.zoom * 100).toFixed(0)}%</span>
      </div>

      <svg width={miniWidth} height={miniHeight} className="rounded bg-canvas-subtle border border-border-subtle">
        {/* Simplified Zone Blocks */}
        {zones.map(zone => (
          <rect
            key={`mini-${zone.id}`}
            x={zone.bounds.x * scaleX}
            y={zone.bounds.y * scaleY}
            width={zone.bounds.width * scaleX}
            height={zone.bounds.height * scaleY}
            fill="#E2E8F0"
            stroke="#CBD5E1"
            strokeWidth={0.5}
            rx={1}
          />
        ))}

        {/* Viewport Indicator Box */}
        <rect
          x={visibleX * scaleX}
          y={visibleY * scaleY}
          width={visibleW * scaleX}
          height={visibleH * scaleY}
          fill="#B45309"
          fillOpacity={0.15}
          stroke="#B45309"
          strokeWidth={1}
          rx={1}
        />
      </svg>
    </div>
  );
};
