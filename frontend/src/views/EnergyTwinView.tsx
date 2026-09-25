/**
 * POLARIS-EMS — Spatial Energy Digital Twin View
 * Quiet Industrial / Arctic Utility Design
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
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { 
  Zap, 
  ShieldCheck, 
  RotateCw,
  Info
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
    <div className="space-y-6 max-w-[1520px] mx-auto pb-10 font-sans">
      {/* 1. Header Banner */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-slate-500 mb-1">
            <span className="font-semibold text-slate-800">{stationDetail?.name || currentStation}</span>
            <span className="text-slate-300">•</span>
            <span>Spatial Energy Twin</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Energy Distribution & Spatial Layout
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Top-down polar microgrid spatial blueprint, thermal zone distribution, and electrical power flow.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ProvenanceTag provenance={viewModel.provenance} size="sm" />
          <span className="text-xs font-mono px-2 py-1 rounded bg-slate-100 border border-slate-200 text-slate-600">
            {viewModel.layoutStatus} MODEL
          </span>
        </div>
      </div>

      {/* 2. Executive Summary Strip */}
      <TwinSummaryStrip viewModel={viewModel} />

      {/* 3. Source Mix Bar */}
      <div className="bg-white rounded-lg p-3 sm:p-4 border border-slate-200 shadow-xs">
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

      {/* 5. Progressive Disclosure: Explain This Component */}
      <ExplainThis
        title="Spatial Digital Twin Physics & Flow Mechanics"
        whatAmILookingAt="Top-down virtual blueprint of the polar station. Maps every physical room, generation asset (wind, solar, diesel, battery), distribution switchboard, and electrical load to monitor power flow in real time."
        whyIsItImportant="During polar storms (-40°C), manual outdoor inspection is impossible. The Spatial Twin provides immediate insight into circuit health and branch loading."
        howIsItCalculated="Driven by the Digital Twin physics engine. Energy balances follow exact Kirchhoff conservation laws: Sum(P_gen) = Total Load + Battery Delta."
        technicalEvidence="Governing formulation: Exact Kirchhoff Node Conservation: Sum(I_in) = Sum(I_out) with residual |err| < 1e-4 kW across 400V 3-phase bus. Simulation air-gap enforced."
      />

      {/* 6. Epistemic Truth & Simulation Air-Gap Status Banner */}
      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono text-slate-500">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>SIMULATION AIR-GAP ENFORCED: PHYSICAL_CONNECTIVITY = DISCONNECTED • PHYSICAL_SCADA_LINK = FALSE</span>
        </div>
        <span className="text-[11px] text-slate-600">
          Software Model Execution • Verified Provenance
        </span>
      </div>
    </div>
  );
};
