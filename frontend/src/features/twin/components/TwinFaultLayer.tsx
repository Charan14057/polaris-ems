/**
 * POLARIS-EMS — Digital Twin Fault Overlay Layer
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders localized, non-obtrusive fault overlays and alarm markers on affected circuits.
 * Enforces restrained visual treatment: soft danger wash and warning symbol without screen strobing.
 */

import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { VisualZoneState, VisualDeviceState } from '../model/twinTypes';

interface TwinFaultLayerProps {
  zones: VisualZoneState[];
  devices: Record<string, VisualDeviceState>;
  faultedCircuitIds: Set<string>;
}

export const TwinFaultLayer: React.FC<TwinFaultLayerProps> = ({
  zones,
  devices,
  faultedCircuitIds
}) => {
  if (faultedCircuitIds.size === 0) return null;

  // Find faulted devices and zones
  const faultedDevices = Object.values(devices).filter(d => faultedCircuitIds.has(d.circuitId));
  const faultedZoneIds = new Set(faultedDevices.map(d => d.zoneId));

  return (
    <g className="twin-fault-layer select-none pointer-events-none">
      {/* Soft Danger Wash on Faulted Zones */}
      {zones.filter(z => faultedZoneIds.has(z.id)).map(zone => {
        const { x, y, width, height } = zone.bounds;
        return (
          <g key={`fault-wash-${zone.id}`}>
            <rect
              x={x}
              y={y}
              width={width}
              height={height}
              rx={6}
              fill="#FEE2E2"
              fillOpacity={0.35}
              stroke="#EF4444"
              strokeWidth={1.5}
              strokeDasharray="6 4"
            />
            {/* Small corner warning emblem */}
            <g transform={`translate(${x + width - 30}, ${y + height - 30})`}>
              <circle cx={12} cy={12} r={12} fill="#EF4444" fillOpacity={0.9} />
              <g transform="translate(4, 4)" color="#FFFFFF">
                <AlertTriangle className="w-4 h-4" />
              </g>
            </g>
          </g>
        );
      })}
    </g>
  );
};
