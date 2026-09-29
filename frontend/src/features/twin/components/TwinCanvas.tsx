/**
 * POLARIS-EMS — Digital Twin Interactive Master Canvas
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Unites Zones, Wireways, Dynamic FlowLayer, Nodes, Junctions, Faults,
 * Minimap, and Viewport controls in an industrial SCADA control room drawing environment.
 * Supports SCADA Dark and Blueprint Light themes with live dynamic energy flows.
 */

import React, { useRef, useEffect, useState } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  RotateCcw, 
  Filter, 
  Layers,
  Compass,
  Monitor,
  FileCode
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
  const [canvasTheme, setCanvasTheme] = useState<'SCADA' | 'BLUEPRINT'>('SCADA');

  const isScada = canvasTheme === 'SCADA';

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
    { id: 'CRITICAL', label: 'P1 Life Support' },
    { id: 'ACTIVE', label: 'Online Only' },
    { id: 'FAULTED', label: 'Faulted Circuits' },
    { id: 'LOADS', label: 'Station Loads' },
    { id: 'THERMAL', label: 'Heating & Climate' },
  ];

  return (
    <div className="space-y-3 font-sans select-none">
      {/* Top Filter and Display Mode Toolbar */}
      <div className={`flex flex-wrap items-center justify-between gap-3 p-2.5 rounded-lg border shadow-xs text-xs font-mono transition-colors ${
        isScada ? 'bg-slate-900 border-slate-800 text-slate-300' : 'bg-white border-slate-200 text-slate-800'
      }`}>
        {/* Device Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] flex items-center space-x-1 mr-1 text-slate-400">
            <Filter className="w-3 h-3 text-sky-400" />
            <span>FILTER:</span>
          </span>
          {filterOptions.map(opt => (
            <button
              key={opt.id}
              type="button"
              onClick={() => onFilterChange(opt.id)}
              className={`px-2.5 py-1 rounded transition-colors ${
                activeFilter === opt.id
                  ? 'bg-sky-600 text-white font-semibold shadow-xs'
                  : isScada
                  ? 'bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 border border-slate-700'
                  : 'bg-slate-50 text-slate-700 hover:text-slate-900 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Right side: SCADA/Blueprint Theme Toggle & View Mode Switcher */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Theme Toggle (SCADA vs Blueprint) */}
          <div className={`flex items-center rounded border p-0.5 ${
            isScada ? 'bg-slate-950 border-slate-700' : 'bg-slate-50 border-slate-200'
          }`}>
            <button
              type="button"
              onClick={() => setCanvasTheme('SCADA')}
              className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold transition-colors ${
                canvasTheme === 'SCADA'
                  ? 'bg-sky-500 text-slate-950 shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="SCADA Dark Control Room Mode"
            >
              <Monitor className="w-3 h-3" />
              <span>SCADA</span>
            </button>
            <button
              type="button"
              onClick={() => setCanvasTheme('BLUEPRINT')}
              className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold transition-colors ${
                canvasTheme === 'BLUEPRINT'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
              title="Technical Blueprint Paper Mode"
            >
              <FileCode className="w-3 h-3" />
              <span>BLUEPRINT</span>
            </button>
          </div>

          {/* View Mode Buttons */}
          <div className={`flex items-center rounded border p-0.5 ${
            isScada ? 'bg-slate-950 border-slate-700' : 'bg-slate-50 border-slate-200'
          }`}>
            <button
              type="button"
              onClick={() => onViewModeChange('3D_SPATIAL')}
              className="px-2.5 py-0.5 rounded text-[11px] text-slate-400 hover:text-white transition-colors"
            >
              3D Spatial
            </button>
            <button
              type="button"
              onClick={() => onViewModeChange('ARCHITECTURAL')}
              className={`px-2.5 py-0.5 rounded text-[11px] transition-colors ${
                viewMode === 'ARCHITECTURAL'
                  ? 'bg-sky-600 text-white font-bold shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              2D Architectural
            </button>
            <button
              type="button"
              onClick={() => onViewModeChange('SCHEMATIC')}
              className={`px-2.5 py-0.5 rounded text-[11px] transition-colors ${
                viewMode === 'SCHEMATIC'
                  ? 'bg-sky-600 text-white font-bold shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Schematic Bus
            </button>
            <button
              type="button"
              onClick={() => onViewModeChange('ACCESSIBLE_TABLE')}
              className="px-2.5 py-0.5 rounded text-[11px] text-slate-400 hover:text-white transition-colors"
            >
              Table
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
        className={`rounded-lg border relative overflow-hidden min-h-[580px] h-[640px] cursor-grab active:cursor-grabbing transition-colors ${
          isScada 
            ? 'bg-slate-950 border-slate-800 shadow-2xl' 
            : 'bg-white border-slate-200 shadow-xs'
        }`}
      >
        {/* Floating Viewport Navigation Toolbar (Bottom Left) */}
        <div className={`absolute bottom-4 left-4 z-20 flex items-center space-x-1.5 p-1 rounded-md border shadow-lg backdrop-blur-md ${
          isScada ? 'bg-slate-900/90 border-slate-700 text-slate-300' : 'bg-white/95 border-slate-200 text-slate-600'
        }`}>
          <button
            type="button"
            onClick={zoomIn}
            className={`p-1.5 rounded transition-colors ${isScada ? 'hover:bg-slate-800 hover:text-white' : 'hover:bg-slate-100 hover:text-slate-900'}`}
            title="Zoom In (+)"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={zoomOut}
            className={`p-1.5 rounded transition-colors ${isScada ? 'hover:bg-slate-800 hover:text-white' : 'hover:bg-slate-100 hover:text-slate-900'}`}
            title="Zoom Out (-)"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => fitToView(containerRef.current?.clientWidth, containerRef.current?.clientHeight)}
            className={`p-1.5 rounded transition-colors ${isScada ? 'hover:bg-slate-800 hover:text-white' : 'hover:bg-slate-100 hover:text-slate-900'}`}
            title="Fit to View"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={reset}
            className={`p-1.5 rounded transition-colors ${isScada ? 'hover:bg-slate-800 hover:text-white' : 'hover:bg-slate-100 hover:text-slate-900'}`}
            title="Reset Viewport"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Floating Architectural Information Tag (Top Left) */}
        <div className={`absolute top-4 left-4 z-20 flex items-center space-x-2 font-mono text-[10px] px-3 py-1.5 rounded-md border shadow-md backdrop-blur-md ${
          isScada ? 'bg-slate-900/90 border-slate-700 text-slate-300' : 'bg-white/95 border-slate-200 text-slate-600'
        }`}>
          <Compass className="w-3.5 h-3.5 text-sky-400" />
          <span className="font-bold uppercase tracking-wider" style={{ color: isScada ? '#ffffff' : '#0f172a' }}>
            {viewModel.stationId} DIGITAL TWIN
          </span>
          <span className="text-slate-500">•</span>
          <span className="text-teal-400 font-semibold">{viewModel.geometryBasis}</span>
          <span className="text-slate-500">•</span>
          <span>SCALE 1:250 • {canvasTheme}</span>
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

        {/* Master SVG Canvas with SCADA Cybernetic Grid */}
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${containerRef.current?.clientWidth || 1000} ${containerRef.current?.clientHeight || 640}`}
          className="w-full h-full"
        >
          <defs>
            {/* High-tech SCADA grid pattern */}
            <pattern id="scada-grid-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#0f1d36" strokeWidth="1" />
              <circle cx="0" cy="0" r="1.2" fill="#1e3a5f" />
            </pattern>
            {/* Blueprint grid pattern */}
            <pattern id="blueprint-grid-pattern" width="30" height="30" patternUnits="userSpaceOnUse">
              <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#e2e8f0" strokeWidth="0.8" />
            </pattern>
          </defs>

          {/* Background Grid */}
          <rect
            width="100%"
            height="100%"
            fill={isScada ? "url(#scada-grid-pattern)" : "url(#blueprint-grid-pattern)"}
          />

          <g transform={`translate(${viewport.panX}, ${viewport.panY}) scale(${viewport.zoom})`}>
            {/* 1. Architectural Zones & Room Partitions */}
            {viewMode === 'ARCHITECTURAL' && (
              <TwinZones
                zones={viewModel.zones}
                selectedZoneId={viewModel.selectedZoneId}
                theme={canvasTheme}
                onSelectZone={onSelectZone}
              />
            )}

            {/* 2. Physical Conduits & Animated Dynamic Flow Paths with Moving Electrons */}
            <TwinFlowLayer
              edges={viewModel.edges}
              theme={canvasTheme}
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

            {/* 5. Physical Nodes (Sources, Main Bus, Panels, Devices with Live Glyphs) */}
            <TwinNodes
              nodes={viewModel.nodes}
              devices={viewModel.devices}
              selectedNodeId={viewModel.selectedNodeId}
              selectedDeviceId={viewModel.selectedDeviceId}
              activeFilter={activeFilter}
              powerSummary={viewModel.powerSummary}
              theme={canvasTheme}
              onSelectNode={onSelectNode}
              onSelectDevice={onSelectDevice}
            />
          </g>
        </svg>
      </div>
    </div>
  );
};
