/**
 * POLARIS-EMS — Spatial Energy Digital Twin View
 * Phase 18: Master Implementation — Spatial Digital Twin Engine
 * 
 * Top-down architectural microgrid floor-plan, thermal zone layout,
 * and physical source-to-load electrical flow platform.
 * 
 * Consumes authoritative Phase 4 TwinEngine forward simulation states.
 * STRICT EPISTEMIC BOUNDARY: PHYSICAL_CONNECTIVITY = DISCONNECTED, PHYSICAL_SCADA_LINK = FALSE.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useStation } from '../context/StationContext';
import { useComprehension } from '../context/ComprehensionContext';
import { api } from '../api/endpoints';
import { TwinSpatialProfile, TwinTrajectoryResponseData } from '../api/types';
import { STATIC_SPATIAL_PROFILES } from '../features/twin/model/spatialProfiles';
import { buildTwinViewModel } from '../features/twin/model/buildTwinViewModel';
import { useTwinPlayback } from '../features/twin/hooks/useTwinPlayback';
import { useTwinSelection } from '../features/twin/hooks/useTwinSelection';
import { TwinViewMode } from '../features/twin/model/twinTypes';
import { TwinCanvas } from '../features/twin/components/TwinCanvas';
import { TwinTimeline } from '../features/twin/components/TwinTimeline';
import { TwinSummaryStrip } from '../features/twin/components/TwinSummaryStrip';
import { TwinSourceMix } from '../features/twin/components/TwinSourceMix';
import { TwinInspector } from '../features/twin/components/TwinInspector';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { 
  Boxes, 
  Layers, 
  Compass, 
  MapPin, 
  ShieldCheck, 
  Sliders, 
  Sparkles,
  Info,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';

export const EnergyTwinView: React.FC = () => {
  const { currentStation, stationDetail } = useStation();
  const { mode: comprehensionMode } = useComprehension();

  const [spatialProfile, setSpatialProfile] = useState<TwinSpatialProfile>(
    STATIC_SPATIAL_PROFILES[currentStation] || STATIC_SPATIAL_PROFILES['BHARATI']
  );
  const [trajectoryData, setTrajectoryData] = useState<TwinTrajectoryResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<TwinViewMode>('ARCHITECTURAL');

  // Interactive Selection Hook
  const {
    selectedNodeId,
    selectedZoneId,
    selectedDeviceId,
    activeFilter,
    tracePowerActive,
    traceImpactActive,
    faultedCircuitIds,
    selectNode,
    selectZone,
    selectDevice,
    setActiveFilter,
    toggleTracePower,
    toggleTraceImpact,
    toggleCircuitFault,
    clearSelection
  } = useTwinSelection();

  // Reset selection and load spatial profile & trajectory on station change
  const loadStationData = useCallback(async () => {
    setLoading(true);
    setError(null);
    clearSelection();

    // 1. Load Spatial Profile (with immediate static fallback)
    const fallbackProfile = STATIC_SPATIAL_PROFILES[currentStation] || STATIC_SPATIAL_PROFILES['BHARATI'];
    setSpatialProfile(fallbackProfile);

    try {
      const [spatialRes, trajectoryRes] = await Promise.all([
        api.getTwinSpatialProfile(currentStation).catch(() => ({ data: fallbackProfile })),
        api.simulateTwinTrajectory({
          station_id: currentStation,
          horizon_hours: 24,
          mode: 'EXPECTED'
        }).catch(() => null)
      ]);

      if (spatialRes?.data) {
        setSpatialProfile(spatialRes.data);
      }
      if (trajectoryRes?.data) {
        setTrajectoryData(trajectoryRes.data);
      }
    } catch (err: any) {
      // Non-blocking: keep fallback profile
      console.warn('Twin API load advisory:', err.message);
    } finally {
      setLoading(false);
    }
  }, [currentStation, clearSelection]);

  useEffect(() => {
    loadStationData();
  }, [loadStationData]);

  // Trajectory Playback Hook
  const trajectoryStates = useMemo(() => {
    return trajectoryData?.states || [];
  }, [trajectoryData]);

  const {
    isPlaying,
    currentIndex,
    speed,
    selectedHorizon,
    statesCount,
    currentState,
    timelineMarkers,
    play,
    pause,
    togglePlay,
    stepForward,
    stepBackward,
    seekTo,
    setSpeed,
    setSelectedHorizon
  } = useTwinPlayback({
    trajectoryStates,
    initialHorizon: 24
  });

  // Handle horizon changes by requesting new trajectory
  const handleHorizonChange = async (newHorizon: 24 | 48 | 168) => {
    setSelectedHorizon(newHorizon);
    try {
      const res = await api.simulateTwinTrajectory({
        station_id: currentStation,
        horizon_hours: newHorizon,
        mode: 'EXPECTED'
      });
      if (res?.data) {
        setTrajectoryData(res.data);
      }
    } catch (e) {
      console.warn('Horizon shift simulation advisory:', e);
    }
  };

  // Build reactive View Model
  const viewModel = useMemo(() => {
    return buildTwinViewModel({
      spatialProfile,
      stationDetail,
      twinState: currentState,
      selectedNodeId,
      selectedZoneId,
      selectedDeviceId,
      activeFilter,
      viewMode,
      faultedCircuitIds,
      tracePowerActive,
      traceImpactActive
    });
  }, [
    spatialProfile,
    stationDetail,
    currentState,
    selectedNodeId,
    selectedZoneId,
    selectedDeviceId,
    activeFilter,
    viewMode,
    faultedCircuitIds,
    tracePowerActive,
    traceImpactActive
  ]);

  const selectedDevice = selectedDeviceId ? viewModel.devices[selectedDeviceId] : null;
  const selectedZone = selectedZoneId ? viewModel.zones.find(z => z.id === selectedZoneId) : null;
  const selectedNode = selectedNodeId ? viewModel.nodes.find(n => n.id === selectedNodeId) : null;

  return (
    <div className="space-y-6 max-w-[1520px] mx-auto pb-12 font-sans">
      {/* 1. Editorial Header */}
      <div className="border-b border-border pb-6 flex flex-col sm:flex-row sm:items-baseline justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-copper font-bold mb-2">
            <Boxes className="w-4 h-4" />
            <span>03 SPATIAL DIGITAL TWIN ENGINE • {currentStation}</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-serif font-bold text-ink-primary tracking-tight">
            Spatial Energy Digital Twin
          </h2>
          <p className="text-sm text-ink-secondary mt-1 font-sans">
            Top-down architectural microgrid floor-plan, thermal zone layout, and physical power flow platform.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <ProvenanceTag provenance={viewModel.provenance} size="sm" />
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-canvas-subtle border border-border text-ink-muted">
            TARGET: {stationDetail?.name || currentStation}
          </span>
        </div>
      </div>

      {/* 2. Executive Summary Strip & Narrative */}
      <TwinSummaryStrip viewModel={viewModel} />

      {/* 3. Source Mix Bar */}
      <div className="editorial-sheet rounded-lg p-3 sm:p-4 border border-border shadow-xs">
        <TwinSourceMix
          solarKw={viewModel.powerSummary.solarGenerationKw}
          windKw={viewModel.powerSummary.windGenerationKw}
          dieselKw={viewModel.powerSummary.dieselGenerationKw}
          batteryKw={viewModel.powerSummary.batteryPowerKw}
          totalLoadKw={viewModel.powerSummary.totalLoadKw}
        />
      </div>

      {/* 4. Main Spatial Canvas & Side Inspector Layout */}
      <div className="flex flex-col lg:flex-row gap-5 items-start">
        {/* Canvas & Timeline Column */}
        <div className="flex-1 w-full space-y-4">
          <TwinCanvas
            viewModel={viewModel}
            activeFilter={activeFilter}
            viewMode={viewMode}
            onSelectNode={selectNode}
            onSelectZone={selectZone}
            onSelectDevice={selectDevice}
            onFilterChange={setActiveFilter}
            onViewModeChange={setViewMode}
          />

          {/* 24-Hour / 48-Hour Replay Timeline Rail */}
          <TwinTimeline
            isPlaying={isPlaying}
            currentIndex={currentIndex}
            totalSteps={statesCount}
            currentTimestamp={currentState?.timestamp || viewModel.timestamp}
            speed={speed}
            selectedHorizon={selectedHorizon}
            timelineMarkers={timelineMarkers}
            onPlay={play}
            onPause={pause}
            onTogglePlay={togglePlay}
            onStepForward={stepForward}
            onStepBackward={stepBackward}
            onSeek={seekTo}
            onSetSpeed={setSpeed}
            onSetHorizon={handleHorizonChange}
          />
        </div>

        {/* Side Inspector Drawer */}
        {(selectedDevice || selectedZone || selectedNode) && (
          <div className="w-full lg:w-80 shrink-0">
            <TwinInspector
              device={selectedDevice}
              zone={selectedZone}
              selectedNodeLabel={selectedNode?.label}
              tracePowerActive={tracePowerActive}
              onToggleTracePower={toggleTracePower}
              onClose={clearSelection}
            />
          </div>
        )}
      </div>

      {/* 5. Non-Technical "Explain This" Component */}
      <ExplainThis
        title="How does the Spatial Digital Twin work in plain English?"
        whatAmILookingAt="This is a top-down virtual blueprint of the polar station. It maps every physical building, generation source (wind, solar, diesel, battery), distribution switchboard, and electrical load so operators can watch electricity flow through the station in real time."
        whyIsItImportant="In extreme polar cold (-40°C), physical access between station outposts is impossible during storms. The Spatial Twin gives engineers an immediate visual view of which circuits are powered, where energy is flowing, and whether any equipment has tripped."
        howIsItCalculated="Driven strictly by the Phase 4 Digital Twin physics engine. Energy balances follow exact Kirchhoff conservation laws: Sum(P_gen) = Total Load + Battery Delta. Line colors update dynamically: green for renewable power, glacial blue for battery, and copper/alert when diesel generators contribute."
        technicalEvidence="Governing formulation: Exact Kirchhoff Node Conservation: Sum(I_in) = Sum(I_out) with residual |err| < 1e-4 kW across 400V 3-phase bus. Simulation air-gap enforced."
      />

      {/* 6. "What Happens Next?" Outlook */}
      <NextStepExplanation
        title="WHAT HAPPENS OVER THE REPLAY TIMELINE?"
        timeframe={`T+${currentIndex}h to T+${statesCount > 0 ? statesCount - 1 : 24}h Horizon`}
        outlook="As weather conditions evolve across the 24-hour cycle, the Twin simulates how generator dispatch and battery state adapt to maintain habitat warmth. Scrubber controls allow you to step forward in time to observe evening battery discharge or morning solar ramps."
      />

      {/* 7. Epistemic Truth & Simulation Air-Gap Status Banner */}
      <div className="p-3 rounded-lg bg-surface border border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono text-ink-muted">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-moss" />
          <span>SIMULATION AIR-GAP ENFORCED: PHYSICAL_CONNECTIVITY = DISCONNECTED • PHYSICAL_SCADA_LINK = FALSE</span>
        </div>
        <span className="text-[11px] text-ink-secondary">
          Phase 18 Spatial Digital Twin Engine Active
        </span>
      </div>
    </div>
  );
};
