/**
 * POLARIS-EMS — Digital Twin Interactive Master Canvas
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Unites Zones, Wireways, Dynamic FlowLayer, Nodes, Junctions, Faults,
 * Minimap, and Viewport controls in an editorial control room drawing environment.
 */

import React, { useRef, useEffect } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  RotateCcw, 
  Filter, 
  Layers,
  Compass
} from 'lucide-react';
import { TwinViewModel, TwinDeviceFilter, TwinViewMode } from '../model/twinTypes';
import { useTwinViewport } from '../hooks/useTwinViewport';
import { TwinZones } from './TwinZones';
import { TwinFlowLayer } from './TwinFlowLayer';
import { TwinJunctions } from './TwinJunctions';
import { TwinNodes } from './TwinNodes';
import { TwinFaultLayer } from './TwinFaultLayer';
import { TwinLegend } from './TwinLegend';
import { TwinMinimap } from './TwinMinimap';

interface TwinCanvasProps {
  viewModel: TwinViewModel;
  activeFilter: TwinDeviceFilter;
  viewMode: TwinViewMode;
  onSelectNode: (nodeId: string) => void;
  onSelectZone: (zoneId: string) => void;
  onSelectDevice: (deviceId: string) => void;
  onSelectEdge?: (edgeId: string) => void;
  onFilterChange: (filter: TwinDeviceFilter) => void;
  onViewModeChange: (mode: TwinViewMode) => void;
}

export const TwinCanvas: React.FC<TwinCanvasProps> = ({
  viewModel,
  activeFilter,
  viewMode,
  onSelectNode,
  onSelectZone,
  onSelectDevice,
  onSelectEdge,
  onFilterChange,
  onViewModeChange
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { width = 1000, height = 640 } = viewModel.dimensions;

  const {
    viewport,
    handleWheel,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    zoomIn,
    zoomOut,
    reset,
    fitToView
  } = useTwinViewport({
    canvasWidth: width,
    canvasHeight: height
  });

  // Fit to view on initial mount and when station changes
  useEffect(() => {
    if (containerRef.current) {
      fitToView(containerRef.current.clientWidth, containerRef.current.clientHeight);
    }
  }, [viewModel.stationId, fitToView]);

  const filterOptions: { id: TwinDeviceFilter; label: string }[] = [
    { id: 'ALL', label: 'All Systems' },
    { id: 'CRITICAL', label: 'P1 Critical Life Support' },
    { id: 'ACTIVE', label: 'Online Only' },
    { id: 'FAULTED', label: 'Faulted Circuits' },
    { id: 'LOADS', label: 'Station Loads' },
    { id: 'THERMAL', label: 'Heating & Climate' },
  ];

  return (
    <div className="space-y-3 font-sans select-none">
      {/* Top Filter and Display Mode Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 rounded-lg bg-surface border border-border shadow-xs text-xs font-mono">
        {/* Device Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-ink-muted text-[11px] flex items-center space-x-1 mr-1">
            <Filter className="w-3 h-3 text-copper" />
            <span>FILTER:</span>
          </span>
          {filterOptions.map(opt => (
            <button
              key={opt.id}
              type="button"
              onClick={() => onFilterChange(opt.id)}
              className={`px-2.5 py-1 rounded transition-colors ${
                activeFilter === opt.id
                  ? 'bg-copper text-ink-inverse font-semibold shadow-xs'
                  : 'bg-canvas-subtle text-ink-secondary hover:text-ink-primary hover:bg-canvas border border-border-subtle'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* View Mode (Architectural vs Schematic) */}
        <div className="flex items-center space-x-2">
          <span className="text-ink-muted text-[11px] hidden sm:inline">VIEW:</span>
          <div className="flex items-center rounded border border-border bg-canvas-subtle p-0.5">
            <button
              type="button"
              onClick={() => onViewModeChange('ARCHITECTURAL')}
              className={`px-2.5 py-0.5 rounded text-[11px] transition-colors ${
                viewMode === 'ARCHITECTURAL'
                  ? 'bg-surface text-ink-primary font-bold shadow-xs'
                  : 'text-ink-muted hover:text-ink-primary'
              }`}
            >
              2D Architectural
            </button>
            <button
              type="button"
              onClick={() => onViewModeChange('SCHEMATIC')}
              className={`px-2.5 py-0.5 rounded text-[11px] transition-colors ${
                viewMode === 'SCHEMATIC'
                  ? 'bg-surface text-ink-primary font-bold shadow-xs'
                  : 'text-ink-muted hover:text-ink-primary'
              }`}
            >
              Schematic Bus
            </button>
          </div>
        </div>
      </div>

      {/* Main Drafting SVG Canvas Container */}
      <div
        ref={containerRef}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        className="editorial-sheet rounded-lg border border-border relative overflow-hidden texture-subtle-grid min-h-[580px] h-[640px] cursor-grab active:cursor-grabbing shadow-sheet"
      >
        {/* Floating Viewport Navigation Toolbar (Bottom Left) */}
        <div className="absolute bottom-4 left-4 z-20 flex items-center space-x-1.5 p-1 rounded bg-surface/90 border border-border shadow-md backdrop-blur-xs">
          <button
            type="button"
            onClick={zoomIn}
            className="p-1.5 rounded hover:bg-canvas text-ink-secondary hover:text-ink-primary transition-colors"
            title="Zoom In (+)"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={zoomOut}
            className="p-1.5 rounded hover:bg-canvas text-ink-secondary hover:text-ink-primary transition-colors"
            title="Zoom Out (-)"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => fitToView(containerRef.current?.clientWidth, containerRef.current?.clientHeight)}
            className="p-1.5 rounded hover:bg-canvas text-ink-secondary hover:text-ink-primary transition-colors"
            title="Fit to View"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={reset}
            className="p-1.5 rounded hover:bg-canvas text-ink-secondary hover:text-ink-primary transition-colors"
            title="Reset Viewport"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Floating Architectural Information Tag (Top Left) */}
        <div className="absolute top-4 left-4 z-20 flex items-center space-x-2 font-mono text-[10px] text-ink-muted bg-surface/90 px-3 py-1.5 rounded border border-border shadow-xs backdrop-blur-xs">
          <Compass className="w-3.5 h-3.5 text-copper" />
          <span className="font-bold text-ink-primary uppercase tracking-wide">
            {viewModel.stationId} SPATIAL MODEL
          </span>
          <span>•</span>
          <span className="text-copper">{viewModel.geometryBasis}</span>
          <span>•</span>
          <span>SCALE 1:250</span>
        </div>

        {/* Map Legend */}
        <TwinLegend />

        {/* Minimap (Bottom Right) */}
        <TwinMinimap
          zones={viewModel.zones}
          viewport={viewport}
          canvasWidth={width}
          canvasHeight={height}
          containerWidth={containerRef.current?.clientWidth || 900}
          containerHeight={containerRef.current?.clientHeight || 600}
        />

        {/* Master SVG Canvas */}
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${containerRef.current?.clientWidth || 1000} ${containerRef.current?.clientHeight || 640}`}
          className="w-full h-full"
        >
          <g transform={`translate(${viewport.panX}, ${viewport.panY}) scale(${viewport.zoom})`}>
            {/* 1. Architectural Zones & Room Partitions */}
            {viewMode === 'ARCHITECTURAL' && (
              <TwinZones
                zones={viewModel.zones}
                selectedZoneId={viewModel.selectedZoneId}
                onSelectZone={onSelectZone}
              />
            )}

            {/* 2. Physical Conduits & Animated Dynamic Flow Paths */}
            <TwinFlowLayer
              edges={viewModel.edges}
              onSelectEdge={onSelectEdge}
            />

            {/* 3. Wireway Junction Points */}
            <TwinJunctions edges={viewModel.edges} />

            {/* 4. Fault Overlays */}
            <TwinFaultLayer
              zones={viewModel.zones}
              devices={viewModel.devices}
              faultedCircuitIds={viewModel.activeFaultCircuitIds}
            />

            {/* 5. Physical Nodes (Sources, Main Bus, Panels, Devices) */}
            <TwinNodes
              nodes={viewModel.nodes}
              devices={viewModel.devices}
              selectedNodeId={viewModel.selectedNodeId}
              selectedDeviceId={viewModel.selectedDeviceId}
              activeFilter={activeFilter}
              powerSummary={viewModel.powerSummary}
              onSelectNode={onSelectNode}
              onSelectDevice={onSelectDevice}
            />
          </g>
        </svg>
      </div>
    </div>
  );
};
