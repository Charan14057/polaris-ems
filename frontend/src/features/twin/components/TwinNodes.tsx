/**
 * POLARIS-EMS — Digital Twin Nodes Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders generation sources, Main AC switchboards, sub-distribution panels,
 * and electrical devices with category-colored rings and status indicators.
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
  };
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
  onSelectNode,
  onSelectDevice
}) => {
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

          if (node.id.includes('solar')) {
            genKw = powerSummary.solarGenerationKw;
            badgeText = `${genKw.toFixed(1)} kW`;
            sourceColor = '#D97706';
          } else if (node.id.includes('wind')) {
            genKw = powerSummary.windGenerationKw;
            badgeText = `${genKw.toFixed(1)} kW`;
            sourceColor = '#0F766E';
          } else if (node.id.includes('diesel')) {
            genKw = powerSummary.dieselGenerationKw;
            badgeText = `${genKw.toFixed(1)} kW`;
            sourceColor = '#B45309';
          } else if (node.id.includes('battery')) {
            badgeText = `${powerSummary.batterySocPct.toFixed(0)}% SOC`;
            sourceColor = '#0284C7';
          }

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
                x={x - 48}
                y={y - 24}
                width={96}
                height={48}
                rx={6}
                className={`transition-all duration-200 ${
                  isSelected
                    ? 'fill-surface stroke-copper stroke-2 shadow-md'
                    : 'fill-surface/95 hover:fill-surface stroke-border hover:stroke-ink-secondary stroke-1 shadow-xs'
                }`}
              />

              {/* Source Icon Emblem */}
              <g transform={`translate(${x - 38}, ${y - 12})`}>
                <circle cx={12} cy={12} r={12} fill={`${sourceColor}20`} />
                <g transform="translate(4, 4)" color={sourceColor}>
                  {renderIcon(node.iconKey, 'w-4 h-4')}
                </g>
              </g>

              {/* Source Label & Power Badge */}
              <text
                x={x - 8}
                y={y - 4}
                className="font-mono text-[9px] font-bold fill-ink-primary"
              >
                {node.label.split(' ')[0]}
              </text>
              <text
                x={x - 8}
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
          return (
            <g
              key={node.id}
              data-interactive="true"
              onClick={() => onSelectNode(node.id)}
              className="cursor-pointer group"
            >
              {/* Central Switchboard Enclosure */}
              <rect
                x={x - 65}
                y={y - 30}
                width={130}
                height={60}
                rx={8}
                className={`transition-all duration-200 ${
                  isSelected
                    ? 'fill-surface stroke-copper stroke-2 shadow-raised'
                    : 'fill-surface stroke-copper/70 hover:stroke-copper stroke-1.5 shadow-sm'
                }`}
              />

              {/* Main Bus Header Strip */}
              <rect
                x={x - 65}
                y={y - 30}
                width={130}
                height={18}
                rx={8}
                className="fill-copper-soft/80"
              />
              <text
                x={x}
                y={y - 18}
                textAnchor="middle"
                className="font-mono text-[9px] font-bold uppercase tracking-wider fill-copper"
              >
                400V 50Hz MAIN BUS
              </text>

              {/* Total Active Load & Status */}
              <text
                x={x}
                y={y + 6}
                textAnchor="middle"
                className="font-serif text-sm font-bold fill-ink-primary"
              >
                {powerSummary.totalLoadKw.toFixed(1)} kW
              </text>
              <text
                x={x}
                y={y + 20}
                textAnchor="middle"
                className="font-mono text-[8px] fill-moss font-semibold uppercase tracking-wide"
              >
                ● 100% BALANCED
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
                r={10}
                className="fill-surface stroke-border stroke-1.5 shadow-xs"
              />
              <circle cx={x} cy={y} r={3} className="fill-copper" />
              <text
                x={x}
                y={y - 14}
                textAnchor="middle"
                className="font-mono text-[8px] font-semibold fill-ink-muted uppercase"
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

          const categoryColor = isCritical ? '#166534' : device.category === 'IMPORTANT' ? '#0284C7' : '#71717A';

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
                  r={22}
                  fill="none"
                  stroke="#B45309"
                  strokeWidth={2}
                  strokeDasharray="3 2"
                  className="animate-spin-slow"
                />
              )}

              {/* Device Circular Pad */}
              <circle
                cx={x}
                cy={y}
                r={16}
                className={`transition-all duration-200 ${
                  isFault
                    ? 'fill-red-100 stroke-red-600 stroke-2'
                    : isSelected
                    ? 'fill-surface stroke-copper stroke-2 shadow-sm'
                    : 'fill-surface hover:fill-canvas stroke-border hover:stroke-ink-secondary stroke-1 shadow-xs'
                }`}
              />

              {/* Category Ring Indicator */}
              <circle
                cx={x}
                cy={y}
                r={14}
                fill="none"
                stroke={categoryColor}
                strokeWidth={isCritical ? 2 : 1}
                opacity={0.8}
              />

              {/* Device Icon */}
              <g transform={`translate(${x - 8}, ${y - 8})`} color={isFault ? '#DC2626' : categoryColor}>
                {renderIcon(node.iconKey, 'w-4 h-4')}
              </g>

              {/* Status Dot at top right */}
              <circle
                cx={x + 12}
                cy={y - 12}
                r={3.5}
                className={
                  isFault
                    ? 'fill-red-500 animate-ping'
                    : isOnline
                    ? 'fill-moss'
                    : 'fill-ink-muted'
                }
              />
              <circle
                cx={x + 12}
                cy={y - 12}
                r={3}
                className={
                  isFault
                    ? 'fill-red-500'
                    : isOnline
                    ? 'fill-moss'
                    : 'fill-ink-muted'
                }
              />

              {/* Device Name Label */}
              <text
                x={x}
                y={y + 25}
                textAnchor="middle"
                className="font-sans text-[9px] font-semibold fill-ink-primary pointer-events-none"
              >
                {device.name.length > 20 ? `${device.name.substring(0, 18)}...` : device.name}
              </text>

              {/* Device Power Telemetry Badge */}
              <text
                x={x}
                y={y + 36}
                textAnchor="middle"
                className={`font-mono text-[9px] font-bold pointer-events-none ${
                  isFault ? 'fill-red-600' : isOnline ? 'fill-ink-secondary' : 'fill-ink-muted'
                }`}
              >
                {isFault ? 'FAULT' : `${device.currentPowerKw.toFixed(1)} kW`}
              </text>
            </g>
          );
        }

        return null;
      })}
    </g>
  );
};
