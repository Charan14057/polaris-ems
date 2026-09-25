/**
 * POLARIS-EMS — Digital Twin Zones Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders architectural room zones with warm parchment fills,
 * subtle structural partition boundaries, zone labels, and load telemetry badges.
 */

import React from 'react';
import { VisualZoneState } from '../model/twinTypes';

interface TwinZonesProps {
  zones: VisualZoneState[];
  selectedZoneId: string | null;
  onSelectZone: (zoneId: string) => void;
}

export const TwinZones: React.FC<TwinZonesProps> = ({
  zones,
  selectedZoneId,
  onSelectZone
}) => {
  return (
    <g className="twin-zones-layer select-none">
      {zones.map(zone => {
        const isSelected = selectedZoneId === zone.id;
        const { x, y, width, height } = zone.bounds;

        return (
          <g
            key={zone.id}
            data-interactive="true"
            onClick={() => onSelectZone(zone.id)}
            className="cursor-pointer group transition-all duration-200"
          >
            {/* Zone Room Base Fill */}
            <rect
              x={x}
              y={y}
              width={width}
              height={height}
              rx={6}
              className={`transition-colors duration-200 ${
                isSelected
                  ? 'fill-copper-soft/50 stroke-copper stroke-2'
                  : zone.hasFault
                  ? 'fill-red-50/50 stroke-red-400/80 stroke-1.5'
                  : 'fill-canvas-subtle/80 hover:fill-surface stroke-border-subtle hover:stroke-border stroke-1'
              }`}
            />

            {/* Architectural Grid Texture / Subtle corner brackets */}
            <path
              d={`M ${x + 8} ${y} L ${x} ${y} L ${x} ${y + 8} M ${x + width - 8} ${y} L ${x + width} ${y} L ${x + width} ${y + 8} M ${x} ${y + height - 8} L ${x} ${y + height} L ${x + 8} ${y + height} M ${x + width - 8} ${y + height} L ${x + width} ${y + height} L ${x + width} ${y + height - 8}`}
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className="text-border"
            />

            {/* Zone Header Label Banner */}
            <rect
              x={x}
              y={y}
              width={width}
              height={26}
              rx={6}
              className={`transition-colors ${
                isSelected ? 'fill-copper/10' : 'fill-border-subtle/30'
              }`}
            />
            <text
              x={x + 12}
              y={y + 17}
              className="font-mono text-[10px] font-bold uppercase tracking-wider fill-ink-primary"
            >
              {zone.label}
            </text>

            {/* Zone Operational Telemetry Badge */}
            <g transform={`translate(${x + width - 110}, ${y + 5})`}>
              <rect
                width={100}
                height={16}
                rx={3}
                className="fill-surface/90 stroke-border-subtle stroke-1 shadow-xs"
              />
              <text
                x={8}
                y={11.5}
                className="font-mono text-[9px] fill-ink-secondary"
              >
                LOAD: <tspan className="font-bold fill-copper">{zone.totalLoadKw.toFixed(1)} kW</tspan>
              </text>
            </g>

            {/* Zone Device Summary Tag at bottom left */}
            <text
              x={x + 12}
              y={y + height - 10}
              className="font-mono text-[9px] fill-ink-muted"
            >
              {zone.activeDeviceCount} of {zone.connectedDeviceCount} Systems Online
              {zone.criticalLoadKw > 0 && ` • ${zone.criticalLoadKw.toFixed(1)} kW P1 Critical`}
            </text>
          </g>
        );
      })}
    </g>
  );
};
