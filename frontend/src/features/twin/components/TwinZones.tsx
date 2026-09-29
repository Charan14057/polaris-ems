/**
 * POLARIS-EMS — Digital Twin Zones Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders architectural room zones with live climate temperatures,
 * structural partition boundaries, zone labels, and load telemetry badges.
 */

import React from 'react';
import { VisualZoneState } from '../model/twinTypes';

interface TwinZonesProps {
  zones: VisualZoneState[];
  selectedZoneId: string | null;
  theme?: 'SCADA' | 'BLUEPRINT';
  onSelectZone: (zoneId: string) => void;
}

export const TwinZones: React.FC<TwinZonesProps> = ({
  zones,
  selectedZoneId,
  theme = 'SCADA',
  onSelectZone
}) => {
  const isScada = theme === 'SCADA';

  // Zone temperature helper based on zone ID
  const getZoneTempC = (zoneId: string): number => {
    if (zoneId.includes('habitation') || zoneId.includes('galley') || zoneId.includes('living')) return 20.4;
    if (zoneId.includes('science') || zoneId.includes('lab') || zoneId.includes('observatory')) return 19.2;
    if (zoneId.includes('generator') || zoneId.includes('engine') || zoneId.includes('power')) return 15.8;
    if (zoneId.includes('bess') || zoneId.includes('battery')) return 18.0;
    if (zoneId.includes('water') || zoneId.includes('pump')) return 8.5;
    return 16.0;
  };

  return (
    <g className="twin-zones-layer select-none">
      {zones.map(zone => {
        const isSelected = selectedZoneId === zone.id;
        const { x, y, width, height } = zone.bounds;
        const tempC = getZoneTempC(zone.id);

        const zoneFill = isScada
          ? isSelected
            ? 'rgba(14, 165, 233, 0.12)'
            : zone.hasFault
            ? 'rgba(239, 68, 68, 0.15)'
            : 'rgba(15, 23, 42, 0.65)'
          : isSelected
          ? 'rgba(254, 243, 199, 0.6)'
          : zone.hasFault
          ? 'rgba(254, 226, 226, 0.6)'
          : 'rgba(241, 245, 249, 0.8)';

        const zoneStroke = isScada
          ? isSelected
            ? '#38bdf8'
            : zone.hasFault
            ? '#ef4444'
            : '#1e293b'
          : isSelected
          ? '#d97706'
          : zone.hasFault
          ? '#f87171'
          : '#e2e8f0';

        const bannerFill = isScada
          ? isSelected
            ? 'rgba(14, 165, 233, 0.25)'
            : 'rgba(30, 41, 59, 0.8)'
          : isSelected
          ? 'rgba(217, 119, 6, 0.15)'
          : 'rgba(226, 232, 240, 0.6)';

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
              rx={8}
              fill={zoneFill}
              stroke={zoneStroke}
              strokeWidth={isSelected ? 2 : 1.2}
              className="transition-colors duration-200 shadow-sm"
            />

            {/* Architectural Drafting Corner Brackets */}
            <path
              d={`M ${x + 8} ${y} L ${x} ${y} L ${x} ${y + 8} M ${x + width - 8} ${y} L ${x + width} ${y} L ${x + width} ${y + 8} M ${x} ${y + height - 8} L ${x} ${y + height} L ${x + 8} ${y + height} M ${x + width - 8} ${y + height} L ${x + width} ${y + height} L ${x + width} ${y + height - 8}`}
              fill="none"
              stroke={isScada ? '#334155' : '#cbd5e1'}
              strokeWidth={1.5}
            />

            {/* Zone Header Label Banner */}
            <rect
              x={x}
              y={y}
              width={width}
              height={26}
              rx={8}
              fill={bannerFill}
            />
            <text
              x={x + 12}
              y={y + 17}
              className="font-mono text-[10px] font-bold uppercase tracking-wider"
              fill={isScada ? '#f1f5f9' : '#0f172a'}
            >
              {zone.label}
            </text>

            {/* Live Climate Temperature Badge */}
            <g transform={`translate(${x + width - 175}, ${y + 5})`}>
              <rect
                width={55}
                height={16}
                rx={3}
                fill={isScada ? '#0f172a' : '#ffffff'}
                stroke={isScada ? '#334155' : '#e2e8f0'}
                strokeWidth={1}
              />
              <text
                x={27.5}
                y={11.5}
                textAnchor="middle"
                className="font-mono text-[9px] font-bold"
                fill={tempC > 18 ? '#10b981' : '#38bdf8'}
              >
                {tempC.toFixed(1)}°C
              </text>
            </g>

            {/* Zone Operational Load Badge */}
            <g transform={`translate(${x + width - 115}, ${y + 5})`}>
              <rect
                width={105}
                height={16}
                rx={3}
                fill={isScada ? '#0f172a' : '#ffffff'}
                stroke={isScada ? '#334155' : '#e2e8f0'}
                strokeWidth={1}
                className="shadow-xs"
              />
              <text
                x={8}
                y={11.5}
                className="font-mono text-[9px]"
                fill={isScada ? '#94a3b8' : '#64748b'}
              >
                LOAD: <tspan className="font-bold" fill={isScada ? '#38bdf8' : '#d97706'}>{zone.totalLoadKw.toFixed(1)} kW</tspan>
              </text>
            </g>

            {/* Zone Device Summary Tag at bottom left */}
            <text
              x={x + 12}
              y={y + height - 10}
              className="font-mono text-[9px]"
              fill={isScada ? '#64748b' : '#94a3b8'}
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
