/**
 * POLARIS-EMS — Digital Twin Electrical Flow Layer Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders physical electrical conduits and dynamic source-to-load flow paths.
 * Enforces the non-renewable flow rule: lines with diesel contribution turn copper/alert.
 * Implements SVG path dash animations with directional awareness.
 */

import React from 'react';
import { VisualEdgeState } from '../model/twinTypes';

interface TwinFlowLayerProps {
  edges: VisualEdgeState[];
  onSelectEdge?: (edgeId: string) => void;
}

export const TwinFlowLayer: React.FC<TwinFlowLayerProps> = ({
  edges,
  onSelectEdge
}) => {
  const getPathData = (geometry: VisualEdgeState['geometry']): string => {
    if (geometry.type === 'path' && geometry.d) {
      return geometry.d;
    }
    if (geometry.type === 'polyline' && geometry.points && geometry.points.length > 0) {
      return geometry.points.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`).join(' ');
    }
    return '';
  };

  const getFlowStrokeColor = (edge: VisualEdgeState): string => {
    switch (edge.flowSemantic) {
      case 'FAULT':
        return '#DC2626'; // Danger Red
      case 'NON_RENEWABLE':
        return '#B45309'; // Burnished Copper (Diesel active)
      case 'BATTERY':
        return '#0284C7'; // Glacial Ice
      case 'RENEWABLE':
        return '#0F766E'; // Deep Teal / Polar Moss
      case 'DORMANT':
      default:
        return '#CBD5E1'; // Muted Stone
    }
  };

  return (
    <g className="twin-flow-layer select-none">
      <defs>
        {/* SVG Marker for Flow Direction Arrows */}
        <marker
          id="flow-arrow-teal"
          viewBox="0 0 10 10"
          refX="6"
          refY="5"
          markerWidth="4"
          markerHeight="4"
          orient="auto-start-reverse"
        >
          <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#0F766E" />
        </marker>
        <marker
          id="flow-arrow-copper"
          viewBox="0 0 10 10"
          refX="6"
          refY="5"
          markerWidth="4"
          markerHeight="4"
          orient="auto-start-reverse"
        >
          <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#B45309" />
        </marker>
        <marker
          id="flow-arrow-ice"
          viewBox="0 0 10 10"
          refX="6"
          refY="5"
          markerWidth="4"
          markerHeight="4"
          orient="auto-start-reverse"
        >
          <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#0284C7" />
        </marker>
      </defs>

      {/* Layer 1: Passive Physical Wireways / Conduit Trays (Background) */}
      {edges.map(edge => {
        const pathData = getPathData(edge.geometry);
        if (!pathData) return null;

        return (
          <path
            key={`conduit-${edge.id}`}
            d={pathData}
            fill="none"
            stroke="#E2E8F0"
            strokeWidth={edge.lineWidthPx + 2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            className="transition-opacity duration-300"
            opacity={edge.dimmed ? 0.2 : 0.9}
          />
        );
      })}

      {/* Layer 2: Active Dynamic Power Flow Lines */}
      {edges.map(edge => {
        const pathData = getPathData(edge.geometry);
        if (!pathData) return null;

        const color = getFlowStrokeColor(edge);
        const isActive = edge.active && edge.direction !== 'NONE';
        const isReverse = edge.direction === 'REVERSE';

        return (
          <g
            key={`flow-${edge.id}`}
            data-interactive="true"
            onClick={() => onSelectEdge?.(edge.id)}
            className="cursor-pointer group"
          >
            {/* Click hit area */}
            <path
              d={pathData}
              fill="none"
              stroke="transparent"
              strokeWidth={14}
            />

            {/* Base electrical conductor line */}
            <path
              d={pathData}
              fill="none"
              stroke={color}
              strokeWidth={edge.lineWidthPx}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={edge.dimmed ? 0.15 : (edge.highlighted ? 1.0 : 0.85)}
              className="transition-all duration-200"
            />

            {/* Dynamic pulsating animated flow overlay (active lines only) */}
            {isActive && (
              <path
                d={pathData}
                fill="none"
                stroke={color}
                strokeWidth={edge.lineWidthPx}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray="8 6"
                className={`twin-flow-path transition-opacity duration-300 ${
                  edge.dimmed ? 'opacity-20' : 'opacity-100'
                }`}
                style={{
                  animation: `twinFlow 1.2s linear infinite ${isReverse ? 'reverse' : 'normal'}`
                }}
              />
            )}

            {/* Fault indicator line pattern */}
            {edge.flowSemantic === 'FAULT' && (
              <path
                d={pathData}
                fill="none"
                stroke="#DC2626"
                strokeWidth={edge.lineWidthPx + 1}
                strokeDasharray="4 4"
                className="animate-pulse"
              />
            )}
          </g>
        );
      })}
    </g>
  );
};
