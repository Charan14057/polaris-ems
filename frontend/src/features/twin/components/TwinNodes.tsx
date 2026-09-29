/**
 * POLARIS-EMS — Digital Twin Nodes Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders generation sources, Main AC switchboards, sub-distribution panels,
 * and electrical devices with animated rotating wind rotors, pulsing solar glint,
 * engine indicators, and dynamic SCADA/Blueprint styling.
 */

import React from 'react';
import {
  Sun,
  Wind,
  Fuel,
  Battery,
  Zap,
  Grid,
  Activity,
  Droplets,
  Flame,
  Radio,
  Server,
  Lightbulb,
  Refrigerator,
  Microscope,
  Trash,
  BatteryCharging,
  Wrench,
  AlertTriangle,
  Compass
} from 'lucide-react';
import { TwinSpatialNode } from '../../../api/types';
import { VisualDeviceState, TwinDeviceFilter } from '../model/twinTypes';

interface TwinNodesProps {
  nodes: TwinSpatialNode[];
  devices: Record<string, VisualDeviceState>;
  selectedNodeId: string | null;
  selectedDeviceId: string | null;
  activeFilter: TwinDeviceFilter;
  powerSummary: {
    solarGenerationKw: number;
    windGenerationKw: number;
    dieselGenerationKw: number;
    batteryPowerKw: number;
    batterySocPct: number;
    totalLoadKw: number;
    totalGenerationKw?: number;
  };
  theme?: 'SCADA' | 'BLUEPRINT';
  onSelectNode: (nodeId: string) => void;
  onSelectDevice: (deviceId: string) => void;
}

export const TwinNodes: React.FC<TwinNodesProps> = ({
  nodes,
  devices,
  selectedNodeId,
  selectedDeviceId,
  activeFilter,
  powerSummary,
  theme = 'SCADA',
  onSelectNode,
  onSelectDevice
}) => {
  const isScada = theme === 'SCADA';

  const renderIcon = (iconKey?: string, className = 'w-4 h-4') => {
    switch (iconKey) {
      case 'Sun': return <Sun className={className} />;
      case 'Wind': return <Wind className={className} />;
      case 'Fuel': return <Fuel className={className} />;
      case 'Battery': return <Battery className={className} />;
      case 'Zap': return <Zap className={className} />;
      case 'Activity': return <Activity className={className} />;
      case 'Droplets': return <Droplets className={className} />;
      case 'Flame': return <Flame className={className} />;
      case 'Radio': return <Radio className={className} />;
      case 'Server': return <Server className={className} />;
      case 'Lightbulb': return <Lightbulb className={className} />;
      case 'Refrigerator': return <Refrigerator className={className} />;
      case 'Microscope': return <Microscope className={className} />;
      case 'Trash': return <Trash className={className} />;
      case 'BatteryCharging': return <BatteryCharging className={className} />;
      case 'Wrench': return <Wrench className={className} />;
      case 'Compass': return <Compass className={className} />;
      case 'Grid':
      default:
        return <Grid className={className} />;
    }
  };

  return (
    <g className="twin-nodes-layer select-none">
      {nodes.map(node => {
        const { x, y } = node.position;
        const isNodeSelected = selectedNodeId === node.id;
        const device = node.deviceId ? devices[node.deviceId] : null;
        const isDeviceSelected = device ? selectedDeviceId === device.id : false;
        const isSelected = isNodeSelected || isDeviceSelected;

        // Apply device filter dimming
        let isFilteredOut = false;
        if (device && activeFilter !== 'ALL') {
          if (activeFilter === 'CRITICAL' && device.category !== 'CRITICAL') isFilteredOut = true;
          if (activeFilter === 'ACTIVE' && device.status !== 'ONLINE') isFilteredOut = true;
          if (activeFilter === 'FAULTED' && device.status !== 'FAULT') isFilteredOut = true;
          if (activeFilter === 'LOADS' && node.kind !== 'DEVICE') isFilteredOut = true;
          if (activeFilter === 'THERMAL' && !device.name.toLowerCase().includes('heat') && !device.name.toLowerCase().includes('hvac')) isFilteredOut = true;
        }

        // 1. SOURCE NODES (Solar, Wind, Diesel, Battery)
        if (node.kind === 'SOURCE' || node.kind === 'STORAGE') {
          let genKw = 0;
          let badgeText = '';
          let sourceColor = '#B45309';
          let isSourceActive = false;

          if (node.id.includes('solar')) {
            genKw = powerSummary.solarGenerationKw;
            isSourceActive = genKw > 0.1;
            badgeText = `${genKw.toFixed(1)} kW`;
            sourceColor = isScada ? '#F59E0B' : '#D97706';
          } else if (node.id.includes('wind')) {
            genKw = powerSummary.windGenerationKw;
            isSourceActive = genKw > 0.1;
            badgeText = `${genKw.toFixed(1)} kW`;
            sourceColor = isScada ? '#34D399' : '#0F766E';
          } else if (node.id.includes('diesel')) {
            genKw = powerSummary.dieselGenerationKw;
            isSourceActive = genKw > 0.1;
            badgeText = `${genKw.toFixed(1)} kW`;
            sourceColor = isScada ? '#F97316' : '#B45309';
          } else if (node.id.includes('battery')) {
            const p = powerSummary.batteryPowerKw;
            isSourceActive = Math.abs(p) > 0.1;
            const flowTag = p < -0.1 ? ' [CHG]' : p > 0.1 ? ' [DIS]' : '';
            badgeText = `${powerSummary.batterySocPct.toFixed(0)}% SOC${flowTag}`;
            sourceColor = isScada ? '#38BDF8' : '#0284C7';
          }

          const boxBg = isScada ? '#0f172a' : '#ffffff';
          const boxStroke = isSelected ? '#38bdf8' : (isScada ? '#1e293b' : '#e2e8f0');

          return (
            <g
              key={node.id}
              data-interactive="true"
              onClick={() => onSelectNode(node.id)}
              className="cursor-pointer group"
              opacity={isFilteredOut ? 0.3 : 1.0}
            >
              {/* Outer Pad Box */}
              <rect
                x={x - 52}
                y={y - 25}
                width={104}
                height={50}
                rx={8}
                fill={boxBg}
                stroke={boxStroke}
                strokeWidth={isSelected ? 2 : 1.5}
                className="transition-all duration-200 shadow-sm"
              />

              {/* Source Icon Emblem with Live Animation */}
              <g transform={`translate(${x - 42}, ${y - 12})`}>
                <circle cx={12} cy={12} r={14} fill={`${sourceColor}25`} />

                {/* Animated spinning wind turbine rotor blades with SVG native animateTransform */}
                {node.id.includes('wind') && isSourceActive ? (
                  <g transform="translate(12, 12)">
                    <g>
                      <animateTransform
                        attributeName="transform"
                        type="rotate"
                        from="0 0 0"
                        to="360 0 0"
                        dur={`${Math.max(0.6, 2.2 - (genKw / 25) * 1.4)}s`}
                        repeatCount="indefinite"
                      />
                      <line x1="0" y1="0" x2="0" y2="-10" stroke={sourceColor} strokeWidth="2.5" strokeLinecap="round" />
                      <line x1="0" y1="0" x2="8.6" y2="5" stroke={sourceColor} strokeWidth="2.5" strokeLinecap="round" />
                      <line x1="0" y1="0" x2="-8.6" y2="5" stroke={sourceColor} strokeWidth="2.5" strokeLinecap="round" />
                      <circle cx="0" cy="0" r="3" fill="#ffffff" stroke={sourceColor} strokeWidth="1" />
                    </g>
                  </g>
                ) : node.id.includes('solar') && isSourceActive ? (
                  /* Animated Solar Glint with Shimmering Photons */
                  <g transform="translate(4, 4)" color={sourceColor}>
                    <circle cx="8" cy="8" r="10" fill="none" stroke={sourceColor} strokeWidth="1" opacity="0.6">
                      <animate attributeName="r" values="8;13;8" dur="2s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.7;0.1;0.7" dur="2s" repeatCount="indefinite" />
                    </circle>
                    {renderIcon(node.iconKey, 'w-4 h-4')}
                  </g>
                ) : node.id.includes('diesel') && isSourceActive ? (
                  /* Animated Diesel Running with Acoustic Shockwave Rings */
                  <g transform="translate(4, 4)" color={sourceColor}>
                    <circle cx="8" cy="8" r="8" fill="none" stroke="#f97316" strokeWidth="1.2">
                      <animate attributeName="r" from="8" to="16" dur="0.9s" repeatCount="indefinite" />
                      <animate attributeName="opacity" from="0.9" to="0" dur="0.9s" repeatCount="indefinite" />
                    </circle>
                    {renderIcon(node.iconKey, 'w-4 h-4')}
                  </g>
                ) : node.id.includes('battery') ? (
                  /* Animated Battery with Inward Charging Rings */
                  <g transform="translate(4, 4)" color={sourceColor}>
                    {powerSummary.batteryPowerKw < -0.1 && (
                      <circle cx="8" cy="8" r="8" fill="none" stroke="#10b981" strokeWidth="1.2">
                        <animate attributeName="r" from="15" to="7" dur="1.2s" repeatCount="indefinite" />
                        <animate attributeName="opacity" from="0.1" to="0.9" dur="1.2s" repeatCount="indefinite" />
                      </circle>
                    )}
                    {renderIcon(node.iconKey, 'w-4 h-4')}
                  </g>
                ) : (
                  <g transform="translate(4, 4)" color={sourceColor}>
                    {renderIcon(node.iconKey, 'w-4 h-4')}
                  </g>
                )}
              </g>

              {/* Source Label & Power Badge */}
              <text
                x={x - 6}
                y={y - 4}
                className="font-mono text-[9px] font-bold"
                fill={isScada ? '#f1f5f9' : '#0f172a'}
              >
                {node.label.split(' ')[0]}
              </text>
              <text
                x={x - 6}
                y={y + 12}
                className="font-mono text-[10px] font-bold"
                fill={sourceColor}
              >
                {badgeText}
              </text>
            </g>
          );
        }

        // 2. MAIN AC SWITCHBOARD BUS
        if (node.kind === 'BUS' && node.id === 'node_main_bus') {
          const busBg = isScada ? '#0b1329' : '#ffffff';
          const busStroke = isSelected ? '#38bdf8' : (isScada ? '#0284c7' : '#d97706');
          const totalLoad = powerSummary.totalLoadKw;

          return (
            <g
              key={node.id}
              data-interactive="true"
              onClick={() => onSelectNode(node.id)}
              className="cursor-pointer group"
            >
              {/* Electric Corona Field Glow */}
              <rect
                x={x - 76}
                y={y - 36}
                width={152}
                height={72}
                rx={10}
                fill="none"
                stroke="#38bdf8"
                strokeWidth={1}
                opacity={0.4}
                filter="url(#flow-glow)"
              >
                <animate attributeName="opacity" values="0.25;0.65;0.25" dur="2.4s" repeatCount="indefinite" />
              </rect>

              {/* Central Switchboard Enclosure */}
              <rect
                x={x - 72}
                y={y - 32}
                width={144}
                height={64}
                rx={8}
                fill={busBg}
                stroke={busStroke}
                strokeWidth={isSelected ? 2.5 : 1.8}
                className="transition-all duration-200 shadow-md"
              />

              {/* Main Bus Header Strip */}
              <rect
                x={x - 72}
                y={y - 32}
                width={144}
                height={18}
                rx={8}
                fill={isScada ? '#0369a1' : '#fef3c7'}
              />
              <text
                x={x}
                y={y - 20}
                textAnchor="middle"
                className="font-mono text-[9px] font-bold uppercase tracking-wider"
                fill={isScada ? '#e0f2fe' : '#92400e'}
              >
                400V 50Hz MAIN BUSBAR
              </text>

              {/* 3-Phase Status LEDs (Red, Yellow, Blue) */}
              <circle cx={x - 52} cy={y + 19} r={2.5} fill="#ef4444" />
              <circle cx={x - 44} cy={y + 19} r={2.5} fill="#eab308" />
              <circle cx={x - 36} cy={y + 19} r={2.5} fill="#3b82f6" />

              {/* Total Active Load & Status */}
              <text
                x={x}
                y={y + 6}
                textAnchor="middle"
                className="font-mono text-sm font-bold"
                fill={isScada ? '#38bdf8' : '#0f172a'}
              >
                {totalLoad.toFixed(1)} kW
              </text>
              <text
                x={x + 10}
                y={y + 22}
                textAnchor="middle"
                className="font-mono text-[8px] font-semibold uppercase tracking-wider"
                fill="#10b981"
              >
                ● 100% BALANCED • 3-PHASE
              </text>
            </g>
          );
        }

        // 3. SUB-DISTRIBUTION PANELS
        if (node.kind === 'BUS') {
          return (
            <g
              key={node.id}
              className="cursor-default select-none"
              opacity={isFilteredOut ? 0.3 : 0.9}
            >
              <circle
                cx={x}
                cy={y}
                r={11}
                fill={isScada ? '#0f172a' : '#ffffff'}
                stroke={isScada ? '#38bdf8' : '#94a3b8'}
                strokeWidth={1.5}
                className="shadow-xs"
              />
              <circle cx={x} cy={y} r={3.5} fill={isScada ? '#38bdf8' : '#b45309'} />
              <text
                x={x}
                y={y - 15}
                textAnchor="middle"
                className="font-mono text-[8px] font-semibold uppercase"
                fill={isScada ? '#94a3b8' : '#64748b'}
              >
                {node.label.split(' ')[0]}
              </text>
            </g>
          );
        }

        // 4. ELECTRICAL DEVICE NODES
        if (node.kind === 'DEVICE' && device) {
          const isCritical = device.category === 'CRITICAL';
          const isFault = device.status === 'FAULT';
          const isOnline = device.status === 'ONLINE';

          const categoryColor = isCritical 
            ? (isScada ? '#34d399' : '#166534') 
            : device.category === 'IMPORTANT' 
            ? (isScada ? '#38bdf8' : '#0284c7') 
            : '#94a3b8';

          const padBg = isFault 
            ? (isScada ? '#450a0a' : '#fee2e2') 
            : (isScada ? '#0f172a' : '#ffffff');

          return (
            <g
              key={node.id}
              data-interactive="true"
              onClick={() => onSelectDevice(device.id)}
              className="cursor-pointer group"
              opacity={isFilteredOut ? 0.25 : 1.0}
            >
              {/* Outer Glow Ring on Selection */}
              {isSelected && (
                <circle
                  cx={x}
                  cy={y}
                  r={23}
                  fill="none"
                  stroke={isScada ? '#38bdf8' : '#b45309'}
                  strokeWidth={2}
                  strokeDasharray="4 3"
                  className="animate-spin"
                  style={{ animationDuration: '8s' }}
                />
              )}

              {/* Device Circular Pad */}
              <circle
                cx={x}
                cy={y}
                r={16}
                fill={padBg}
                stroke={isFault ? '#ef4444' : isSelected ? '#38bdf8' : (isScada ? '#334155' : '#cbd5e1')}
                strokeWidth={isFault ? 2 : isSelected ? 2 : 1}
                className="transition-all duration-200 shadow-xs"
              />

              {/* Category Ring Indicator */}
              <circle
                cx={x}
                cy={y}
                r={13.5}
                fill="none"
                stroke={categoryColor}
                strokeWidth={isCritical ? 2 : 1}
                opacity={0.85}
              />

              {/* Device Icon */}
              <g transform={`translate(${x - 8}, ${y - 8})`} color={isFault ? '#ef4444' : categoryColor}>
                {renderIcon(node.iconKey, 'w-4 h-4')}
              </g>

              {/* Status Dot at top right */}
              <circle
                cx={x + 12}
                cy={y - 12}
                r={3}
                fill={isFault ? '#ef4444' : isOnline ? '#10b981' : '#64748b'}
                className={isFault ? 'animate-ping' : undefined}
              />

              {/* Device Name Label */}
              <text
                x={x}
                y={y + 26}
                textAnchor="middle"
                className="font-sans text-[9px] font-semibold pointer-events-none"
                fill={isScada ? '#e2e8f0' : '#0f172a'}
              >
                {device.name.length > 20 ? `${device.name.substring(0, 18)}...` : device.name}
              </text>

              {/* Device Power Telemetry Badge */}
              <text
                x={x}
                y={y + 37}
                textAnchor="middle"
                className="font-mono text-[9px] font-bold pointer-events-none"
                fill={isFault ? '#ef4444' : isOnline ? (isScada ? '#38bdf8' : '#334155') : '#64748b'}
              >
                {isFault ? 'TRIPPED' : `${device.currentPowerKw.toFixed(1)} kW`}
              </text>
            </g>
          );
        }

        return null;
      })}
    </g>
  );
};
