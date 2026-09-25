import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { STATIC_SPATIAL_PROFILES } from '../features/twin/model/spatialProfiles';
import { buildTwinViewModel } from '../features/twin/model/buildTwinViewModel';
import { TwinSummaryStrip } from '../features/twin/components/TwinSummaryStrip';
import { TwinSourceMix } from '../features/twin/components/TwinSourceMix';
import { TwinInspector } from '../features/twin/components/TwinInspector';
import { TwinTimeline } from '../features/twin/components/TwinTimeline';
import { TwinLegend } from '../features/twin/components/TwinLegend';
import { TwinCanvas } from '../features/twin/components/TwinCanvas';
import { EvidenceProvider } from '../context/EvidenceContext';
import { TwinState, StationProfileDetail } from '../api/types';

describe('Phase 18 Spatial Digital Twin Engine - Static Spatial Profiles', () => {
  it('loads authoritative spatial profiles for BHARATI, MAITRI, and HIMADRI', () => {
    expect(STATIC_SPATIAL_PROFILES.BHARATI).toBeDefined();
    expect(STATIC_SPATIAL_PROFILES.MAITRI).toBeDefined();
    expect(STATIC_SPATIAL_PROFILES.HIMADRI).toBeDefined();

    const bharati = STATIC_SPATIAL_PROFILES.BHARATI;
    expect(bharati.stationId).toBe('BHARATI');
    expect(bharati.layoutStatus).toBe('REPRESENTATIVE');
    expect(bharati.width).toBe(1000);
    expect(bharati.height).toBe(640);
    expect(bharati.zones.length).toBe(6);
    expect(bharati.nodes.length).toBeGreaterThanOrEqual(12);
    expect(bharati.edges.length).toBeGreaterThanOrEqual(12);
  });

  it('verifies Maitri and Himadri profiles have unique spatial nodes and circuits', () => {
    const maitri = STATIC_SPATIAL_PROFILES.MAITRI;
    const himadri = STATIC_SPATIAL_PROFILES.HIMADRI;

    expect(maitri.stationId).toBe('MAITRI');
    expect(himadri.stationId).toBe('HIMADRI');
    expect(maitri.nodes.some(n => n.id === 'node_mt_main_bus')).toBe(true);
    expect(himadri.nodes.some(n => n.id === 'node_hm_main_bus')).toBe(true);
  });
});

describe('Phase 18 Spatial Digital Twin Engine - buildTwinViewModel', () => {
  const sampleSpatial = STATIC_SPATIAL_PROFILES.BHARATI;

  const sampleStationDetail: any = {
    station_id: 'BHARATI',
    name: 'Bharati Antarctic Research Station',
    location: 'Larsemann Hills, Antarctica',
    coordinates: { lat: -69.41, lon: 76.19 },
    system_type: 'MICROGRID',
    nominal_voltage: 400,
    frequency_hz: 50,
    solar_capacity_kw: 65,
    wind_capacity_kw: 50,
    battery_capacity_kwh: 120,
    battery_max_discharge_kw: 60,
    generator_count: 2,
    generator_total_capacity_kw: 160,
    devices: [
      {
        id: 'bh_life_support',
        name: 'Habitat HVAC Life Support',
        category: 'CRITICAL',
        priority_rank: 1,
        nominal_power_kw: 18.5,
        deferrable: false
      },
      {
        id: 'bh_science_lab',
        name: 'Core Science Lab',
        category: 'SCIENCE',
        priority_rank: 4,
        nominal_power_kw: 10.0,
        deferrable: true
      }
    ]
  };

  const sampleTwinState: TwinState = {
    station_id: 'BHARATI',
    timestamp: '2026-09-25T12:00:00Z',
    provenance: 'SIMULATED',
    solar: {
      solar_generation_kw: 35.0,
      irradiance_w_m2: 600,
      cell_temp_c: -5.0,
      derating_factor: 0.95
    },
    wind: {
      wind_generation_kw: 20.0,
      wind_speed_m_s: 12.0,
      turbine_status: 'RUNNING'
    },
    diesel: {
      generator_power_kw: 0.0,
      fuel_consumption_l_h: 0.0,
      generator_status: 'OFF',
      co2_kg_h: 0.0
    },
    battery: {
      soc_pct: 0.82,
      charge_kw: 5.0,
      discharge_kw: 0.0,
      cell_temp_c: 18.0,
      cycle_count: 142
    },
    loads: {
      total_load_kw: 50.0,
      served_load_kw: 50.0,
      unserved_load_kw: 0.0,
      critical_load_kw: 18.5,
      shed_load_kw: 0.0
    },
    thermal: {
      indoor_temperature_c: 21.0,
      outdoor_temp_c: -24.0,
      heating_power_kw: 18.0
    },
    resilience: {
      threat_state: 'SAFE',
      continuity_horizon_hours: 84.0
    }
  };

  it('maps renewable generation, dominant source, and plain-language summary', () => {
    const vm = buildTwinViewModel({
      spatialProfile: sampleSpatial,
      twinState: sampleTwinState,
      stationDetail: sampleStationDetail,
      selectedDeviceId: null,
      selectedNodeId: null,
      selectedZoneId: null,
      activeFilter: 'ALL',
      viewMode: 'ARCHITECTURAL',
      faultedCircuitIds: new Set<string>(),
      tracePowerActive: false,
      traceImpactActive: false
    });

    expect(vm.stationId).toBe('BHARATI');
    expect(vm.powerSummary.solarGenerationKw).toBe(35.0);
    expect(vm.powerSummary.windGenerationKw).toBe(20.0);
    expect(vm.powerSummary.dieselGenerationKw).toBe(0.0);
    expect(vm.powerSummary.dominantSource).toBe('RENEWABLE');
    expect(vm.powerSummary.renewableFractionPct).toBe(100.0);
    expect(vm.provenance).toBe('SIMULATED');
  });

  it('enforces non-renewable flow rule when diesel generation is active', () => {
    const dieselTwinState: TwinState = {
      ...sampleTwinState,
      solar: { ...sampleTwinState.solar!, solar_generation_kw: 0.0 },
      wind: { ...sampleTwinState.wind!, wind_generation_kw: 5.0 },
      diesel: {
        generator_power_kw: 45.0,
        fuel_consumption_l_h: 12.0,
        generator_status: 'RUNNING',
        co2_kg_h: 31.5
      }
    };

    const vm = buildTwinViewModel({
      spatialProfile: sampleSpatial,
      twinState: dieselTwinState,
      stationDetail: sampleStationDetail,
      selectedDeviceId: null,
      selectedNodeId: null,
      selectedZoneId: null,
      activeFilter: 'ALL',
      viewMode: 'ARCHITECTURAL',
      faultedCircuitIds: new Set<string>(),
      tracePowerActive: false,
      traceImpactActive: false
    });

    expect(vm.powerSummary.dieselGenerationKw).toBe(45.0);
    expect(vm.powerSummary.dominantSource).toBe('DIESEL');

    // Feeder lines carrying diesel power should have state 'NON_RENEWABLE'
    const feederEdge = vm.edges.find(e => e.id === 'e_bus_sub_util');
    expect(feederEdge).toBeDefined();
    expect(feederEdge?.hasDieselContribution).toBe(true);
    expect(feederEdge?.flowSemantic).toBe('NON_RENEWABLE');
  });

  it('performs "Trace My Power" upstream lineage from device to sources', () => {
    const vm = buildTwinViewModel({
      spatialProfile: sampleSpatial,
      twinState: sampleTwinState,
      stationDetail: sampleStationDetail,
      selectedDeviceId: 'bh_life_support',
      selectedNodeId: 'node_bh_life_support',
      selectedZoneId: null,
      activeFilter: 'ALL',
      viewMode: 'ARCHITECTURAL',
      faultedCircuitIds: new Set<string>(),
      tracePowerActive: true,
      traceImpactActive: false
    });

    // The device node, its sub-bus, and the main bus should be in tracedPathNodeIds
    expect(vm.tracedPathNodeIds.has('node_bh_life_support')).toBe(true);
    expect(vm.tracedPathNodeIds.has('node_sub_util')).toBe(true);
    expect(vm.tracedPathNodeIds.has('node_main_bus')).toBe(true);

    // Active generating sources should also be traced
    expect(vm.tracedPathNodeIds.has('node_solar')).toBe(true);
    expect(vm.tracedPathNodeIds.has('node_wind')).toBe(true);

    // The edge connecting life support must be highlighted
    expect(vm.tracedPathEdgeIds.has('e_util_life_support')).toBe(true);
  });

  it('performs "Trace Impact" downstream lineage when a source is selected', () => {
    const vm = buildTwinViewModel({
      spatialProfile: sampleSpatial,
      twinState: sampleTwinState,
      stationDetail: sampleStationDetail,
      selectedDeviceId: null,
      selectedNodeId: 'node_solar',
      selectedZoneId: null,
      activeFilter: 'ALL',
      viewMode: 'ARCHITECTURAL',
      faultedCircuitIds: new Set<string>(),
      tracePowerActive: false,
      traceImpactActive: true
    });

    // From solar source, impact traces to main bus, feeders, and downstream nodes
    expect(vm.tracedPathNodeIds.has('node_solar')).toBe(true);
    expect(vm.tracedPathNodeIds.has('node_main_bus')).toBe(true);
    expect(vm.tracedPathNodeIds.size).toBeGreaterThan(3);
  });
});

describe('Phase 18 Spatial Digital Twin Engine - Components Rendering', () => {
  const sampleSpatial = STATIC_SPATIAL_PROFILES.BHARATI;

  const sampleStationDetail: any = {
    station_id: 'BHARATI',
    name: 'Bharati Antarctic Research Station',
    location: 'Larsemann Hills, Antarctica',
    coordinates: { lat: -69.41, lon: 76.19 },
    system_type: 'MICROGRID',
    nominal_voltage: 400,
    frequency_hz: 50,
    solar_capacity_kw: 65,
    wind_capacity_kw: 50,
    battery_capacity_kwh: 120,
    battery_max_discharge_kw: 60,
    generator_count: 2,
    generator_total_capacity_kw: 160,
    devices: [
      {
        id: 'bh_life_support',
        name: 'Habitat HVAC Life Support',
        category: 'CRITICAL',
        priority_rank: 1,
        nominal_power_kw: 18.5,
        deferrable: false
      }
    ]
  };

  const sampleTwinState: TwinState = {
    station_id: 'BHARATI',
    timestamp: '2026-09-25T12:00:00Z',
    provenance: 'SIMULATED',
    solar: { solar_generation_kw: 35.0 },
    wind: { wind_generation_kw: 20.0 },
    diesel: { generator_power_kw: 0.0 },
    battery: { soc_pct: 0.82, charge_kw: 5.0, discharge_kw: 0.0 },
    loads: { total_load_kw: 50.0, served_load_kw: 50.0, critical_load_kw: 18.5 },
    thermal: { indoor_temperature_c: 21.0, outdoor_temp_c: -24.0 },
    resilience: { threat_state: 'SAFE', continuity_horizon_hours: 84.0 }
  };

  const vm = buildTwinViewModel({
    spatialProfile: sampleSpatial,
    twinState: sampleTwinState,
    stationDetail: sampleStationDetail,
    selectedDeviceId: null,
    selectedNodeId: null,
    selectedZoneId: null,
    activeFilter: 'ALL',
    viewMode: 'ARCHITECTURAL',
    faultedCircuitIds: new Set<string>(),
    tracePowerActive: false,
    traceImpactActive: false
  });

  it('renders TwinSummaryStrip with operational narrative and vitals', () => {
    render(<TwinSummaryStrip viewModel={vm} />);

    expect(screen.getByText('WHAT IS HAPPENING?')).toBeInTheDocument();
    expect(screen.getByText('WHY THIS MATTERS')).toBeInTheDocument();
    expect(screen.getByText('OPERATIONAL TWIN SUMMARY • BHARATI')).toBeInTheDocument();
    expect(screen.getByText('PHYSICS CONSERVED')).toBeInTheDocument();
  });

  it('renders TwinSourceMix with generation metrics and total load', () => {
    render(
      <TwinSourceMix
        solarKw={vm.powerSummary.solarGenerationKw}
        windKw={vm.powerSummary.windGenerationKw}
        dieselKw={vm.powerSummary.dieselGenerationKw}
        batteryKw={vm.powerSummary.batteryPowerKw}
        totalLoadKw={vm.powerSummary.totalLoadKw}
      />
    );

    expect(screen.getByText('GENERATION SOURCE MIX')).toBeInTheDocument();
    expect(screen.getByText(/TOTAL LOAD:/)).toBeInTheDocument();
    expect(screen.getByText(/50.0 kW/)).toBeInTheDocument();
  });

  it('renders TwinLegend with toggleable map legend panel', () => {
    render(<TwinLegend />);

    const legendBtn = screen.getByText('MAP LEGEND');
    expect(legendBtn).toBeInTheDocument();

    fireEvent.click(legendBtn);
    expect(screen.getByText('ELECTRICAL POWER FLOWS')).toBeInTheDocument();
    expect(screen.getByText('Renewable Pure')).toBeInTheDocument();
    expect(screen.getByText('Diesel Contribution')).toBeInTheDocument();
  });

  it('renders TwinInspector with Layer 1 non-technical explanation and toggleable Layer 2 technical details', () => {
    const device = vm.devices['bh_life_support'];
    expect(device).toBeDefined();

    render(
      <EvidenceProvider>
        <TwinInspector
          device={device}
          zone={null}
          selectedNodeLabel={null}
          tracePowerActive={false}
          onToggleTracePower={vi.fn()}
          onClose={vi.fn()}
        />
      </EvidenceProvider>
    );

    // Layer 1
    expect(screen.getByText('WHAT THIS DOES')).toBeInTheDocument();
    expect(screen.getByText('CURRENT STATE')).toBeInTheDocument();
    expect(screen.getByText('WHY IT MATTERS')).toBeInTheDocument();

    // Toggle Layer 2
    const expandBtn = screen.getByText(/View Engineering Specs/i);
    fireEvent.click(expandBtn);

    expect(screen.getByText('Circuit ID:')).toBeInTheDocument();
    expect(screen.getByText('Bus Voltage:')).toBeInTheDocument();
    expect(screen.getByText('Rated Power:')).toBeInTheDocument();
  });

  it('renders TwinTimeline with playback controls and 24h scrubber', () => {
    const onTogglePlay = vi.fn();
    const onPlay = vi.fn();
    const onPause = vi.fn();
    const onStepForward = vi.fn();
    const onStepBackward = vi.fn();
    const onSeek = vi.fn();
    const onSetSpeed = vi.fn();
    const onSetHorizon = vi.fn();

    render(
      <TwinTimeline
        isPlaying={false}
        currentIndex={5}
        totalSteps={24}
        speed={1}
        selectedHorizon={24}
        currentTimestamp="2026-09-25T12:00:00Z"
        timelineMarkers={[]}
        onPlay={onPlay}
        onPause={onPause}
        onTogglePlay={onTogglePlay}
        onStepForward={onStepForward}
        onStepBackward={onStepBackward}
        onSeek={onSeek}
        onSetSpeed={onSetSpeed}
        onSetHorizon={onSetHorizon}
      />
    );

    expect(screen.getByText('T+00h START')).toBeInTheDocument();
    expect(screen.getByText('T+23h END')).toBeInTheDocument();

    const playBtn = screen.getByLabelText('Start simulation playback');
    fireEvent.click(playBtn);
    expect(onTogglePlay).toHaveBeenCalled();
  });

  it('renders TwinCanvas SVG structure without errors', () => {
    const { container } = render(
      <TwinCanvas
        viewModel={vm}
        activeFilter="ALL"
        viewMode="ARCHITECTURAL"
        onSelectNode={vi.fn()}
        onSelectZone={vi.fn()}
        onSelectDevice={vi.fn()}
        onFilterChange={vi.fn()}
        onViewModeChange={vi.fn()}
      />
    );

    const svg = container.querySelector('svg');
    expect(svg).not.toBeNull();
    // Check zones layer rendered
    expect(container.querySelectorAll('.twin-zones-layer').length).toBe(1);
    // Check flow layer rendered
    expect(container.querySelectorAll('.twin-flow-layer').length).toBe(1);
    // Check flow paths rendered
    expect(container.querySelectorAll('.twin-flow-path').length).toBeGreaterThan(0);
  });
});
