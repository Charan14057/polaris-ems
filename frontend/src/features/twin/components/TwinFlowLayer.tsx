/**
 * POLARIS-EMS — Digital Twin Electrical Flow Layer Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders physical electrical conduits and dynamic source-to-load flow paths.
 * Enforces the non-renewable flow rule: lines with diesel contribution turn copper/alert.
 * Implements SVG path dash animations with directional awareness and moving electron energy packets.
 */

import React from 'react';
import { VisualEdgeState } from '../model/twinTypes';

interface TwinFlowLayerProps {
  edges: VisualEdgeState[];
  theme?: 'SCADA' | 'BLUEPRINT';
  onSelectEdge?: (edgeId: string) => void;
}

export const TwinFlowLayer: React.FC<TwinFlowLayerProps> = ({
  edges,
  theme = 'SCADA',
  onSelectEdge
}) => {
  const isScada = theme === 'SCADA';

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
        return '#EF4444'; // Danger Red
      case 'NON_RENEWABLE':
        return isScada ? '#F59E0B' : '#B45309'; // Warm Amber / Burnished Copper
      case 'BATTERY':
        return isScada ? '#38BDF8' : '#0284C7'; // Cyan / Glacial Ice
      case 'RENEWABLE':
        return isScada ? '#34D399' : '#0F766E'; // Polar Emerald / Teal
      case 'DORMANT':
      default:
        return isScada ? '#334155' : '#CBD5E1'; // Muted Stone / Slate
    }
  };

  return (
    <g className="twin-flow-layer select-none">
      <defs>
        {/* Glow filter for neon SCADA conduits and electron pulses */}
        <filter id="flow-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

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
          <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#10B981" />
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
          <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#F59E0B" />
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
          <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#38BDF8" />
        </marker>
      </defs>

      {/* Layer 1: Passive Physical Wireways / Conduit Trays (Background) */}
      {edges.map(edge => {
        const pathData = getPathData(edge.geometry);
        if (!pathData) return null;

        const trayColor = isScada ? '#1e293b' : '#E2E8F0';

        return (
          <path
            key={`conduit-${edge.id}`}
            d={pathData}
            fill="none"
            stroke={trayColor}
            strokeWidth={edge.lineWidthPx + 3}
            strokeLinecap="round"
            strokeLinejoin="round"
            className="transition-opacity duration-300"
            opacity={edge.dimmed ? 0.2 : (isScada ? 0.8 : 0.9)}
          />
        );
      })}

      {/* Layer 2: Active Dynamic Power Flow Lines & Electron Pulses */}
      {edges.map(edge => {
        const pathData = getPathData(edge.geometry);
        if (!pathData) return null;

        const color = getFlowStrokeColor(edge);
        const isActive = edge.active && edge.direction !== 'NONE';
        const isReverse = edge.direction === 'REVERSE';
        const powerKw = edge.powerKw || 0;

        // Flow duration scales smoothly with power level: higher kW = faster animation
        const baseDuration = Math.max(0.5, Math.min(1.8, 1.4 - (powerKw / 120)));

        return (
          <g
            key={`flow-${edge.id}`}
            data-interactive="true"
            onClick={() => onSelectEdge?.(edge.id)}
            className="cursor-pointer group"
          >
            {/* Expanded Hit Area */}
            <path
              d={pathData}
              fill="none"
              stroke="transparent"
              strokeWidth={16}
            />

            {/* Base electrical conductor line */}
            <path
              d={pathData}
              fill="none"
              stroke={color}
              strokeWidth={edge.lineWidthPx}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={edge.dimmed ? 0.15 : (edge.highlighted ? 1.0 : (isScada ? 0.85 : 0.75))}
              className="transition-all duration-200"
            />

            {/* Dynamic pulsating animated flow overlay (active lines only) */}
            {isActive && (
              <path
                d={pathData}
                fill="none"
                stroke={color}
                strokeWidth={edge.lineWidthPx + 0.5}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray="8 6"
                filter={isScada ? "url(#flow-glow)" : undefined}
                className={`twin-flow-path transition-opacity duration-300 ${
                  edge.dimmed ? 'opacity-20' : 'opacity-100'
                }`}
                style={{
                  animation: `twinFlow ${baseDuration}s linear infinite ${isReverse ? 'reverse' : 'normal'}`
                }}
              />
            )}

            {/* Moving Electron Energy Packets along Active Conduits */}
            {isActive && powerKw > 0.2 && (
              <g pointerEvents="none">
                <circle
                  r={Math.min(3.5, Math.max(2.2, edge.lineWidthPx * 0.7))}
                  fill={isScada ? '#ffffff' : color}
                  stroke={color}
                  strokeWidth={1}
                  filter="url(#flow-glow)"
                >
                  <animateMotion
                    path={pathData}
                    dur={`${baseDuration * 1.6}s`}
                    repeatCount="indefinite"
                    keyPoints={isReverse ? "1;0" : "0;1"}
                    keyTimes="0;1"
                  />
                </circle>

                {powerKw > 15 && (
                  <circle
                    r={Math.min(2.8, Math.max(1.8, edge.lineWidthPx * 0.55))}
                    fill={color}
                    opacity={0.85}
                  >
                    <animateMotion
                      path={pathData}
                      dur={`${baseDuration * 1.6}s`}
                      begin={`${(baseDuration * 1.6) / 2}s`}
                      repeatCount="indefinite"
                      keyPoints={isReverse ? "1;0" : "0;1"}
                      keyTimes="0;1"
                    />
                  </circle>
                )}
              </g>
            )}

            {/* Fault indicator line pattern */}
            {edge.flowSemantic === 'FAULT' && (
              <path
                d={pathData}
                fill="none"
                stroke="#EF4444"
                strokeWidth={edge.lineWidthPx + 1.5}
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
