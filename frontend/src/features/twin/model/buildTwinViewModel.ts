/**
 * POLARIS-EMS — Digital Twin View Model Builder
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Pure transformation layer: transforms authoritative backend TwinState / TwinTrajectory,
 * StationProfile, and SpatialProfile into a reactive visual model for the Spatial Twin canvas.
 * ZERO duplicated physics.
 */

import {
  TwinSpatialProfile,
  TwinZone,
  TwinSpatialNode,
  TwinFlowEdge,
  TwinSourceMix,
  StationDetail,
  ProvenanceTier
} from '../../../api/types';
import {
  TwinViewModel,
  TwinViewMode,
  TwinDeviceFilter,
  VisualDeviceState,
  VisualEdgeState,
  VisualZoneState
} from './twinTypes';

export interface BuildTwinViewModelParams {
  spatialProfile: TwinSpatialProfile;
  stationDetail?: StationDetail | null;
  twinState?: Record<string, any> | null;
  selectedNodeId?: string | null;
  selectedZoneId?: string | null;
  selectedDeviceId?: string | null;
  activeFilter?: TwinDeviceFilter;
  viewMode?: TwinViewMode;
  faultedCircuitIds?: Set<string>;
  tracePowerActive?: boolean;
  traceImpactActive?: boolean;
}

export function buildTwinViewModel(params: BuildTwinViewModelParams): TwinViewModel {
  const {
    spatialProfile,
    stationDetail,
    twinState,
    selectedNodeId = null,
    selectedZoneId = null,
    selectedDeviceId = null,
    activeFilter = 'ALL',
    viewMode = 'ARCHITECTURAL',
    faultedCircuitIds = new Set<string>(),
    tracePowerActive = false,
    traceImpactActive = false
  } = params;

  const stationId = spatialProfile.stationId || 'BHARATI';
  const timestamp = twinState?.timestamp || new Date().toISOString();
  const provenance: ProvenanceTier = (twinState?.provenance as ProvenanceTier) || 'SIMULATED';

  // 1. Physical Generation & Balance
  const solarGen = Number(twinState?.solar?.solar_generation_kw || 0.0);
  const windGen = Number(twinState?.wind?.wind_generation_kw || 0.0);
  const dieselGen = Number(twinState?.diesel?.generator_power_kw || 0.0);
  const batCharge = Number(twinState?.battery?.charge_kw || 0.0);
  const batDischarge = Number(twinState?.battery?.discharge_kw || 0.0);
  const batPower = batDischarge - batCharge; // positive = net supplier to bus, negative = load
  const batSoc = Number(twinState?.battery?.soc_pct !== undefined ? twinState?.battery?.soc_pct : 0.65);

  // 2. Build Device Visual Registry
  const stationDevices = stationDetail?.devices || [];

  const totalNominalLoad = stationDevices.reduce((acc, d) => acc + d.nominal_power_kw, 0) || 42.0;
  const criticalNominalLoad = stationDevices
    .filter(d => d.category === 'CRITICAL')
    .reduce((acc, d) => acc + d.nominal_power_kw, 0) || 16.0;

  const totalLoad = Number(twinState?.loads?.total_load_kw || totalNominalLoad);
  const servedLoad = Number(twinState?.loads?.served_load_kw || totalLoad);
  const unservedLoad = Number(twinState?.loads?.unserved_load_kw || 0.0);
  const criticalLoad = Number(twinState?.loads?.critical_load_kw || criticalNominalLoad);

  const totalGen = solarGen + windGen + dieselGen + Math.max(0, batPower);
  const renewableGen = solarGen + windGen;
  const renewableFraction = totalGen > 0.1 ? (renewableGen / totalGen) * 100.0 : 0.0;
  const conservationGap = Math.abs(totalGen - (servedLoad + Math.max(0, -batPower)));

  let dominantSource: 'RENEWABLE' | 'BATTERY' | 'DIESEL' | 'BALANCED' = 'RENEWABLE';
  if (dieselGen > renewableGen && dieselGen > batDischarge) {
    dominantSource = 'DIESEL';
  } else if (batDischarge > renewableGen && batDischarge > dieselGen) {
    dominantSource = 'BATTERY';
  } else if (Math.abs(renewableGen - dieselGen) < 5.0 && dieselGen > 5.0) {
    dominantSource = 'BALANCED';
  }
  const devicesMap: Record<string, VisualDeviceState> = {};

  spatialProfile.nodes.forEach(node => {
    if (node.kind === 'DEVICE' && node.deviceId) {
      const devProfile = stationDevices.find(d => d.id === node.deviceId);
      const isFaulted = faultedCircuitIds.has(node.circuitId || '');
      const nominalPower = devProfile?.nominal_power_kw || 5.0;
      
      // Determine operational current power based on twin served load ratio
      const servedRatio = totalLoad > 0.1 ? Math.min(1.0, servedLoad / totalLoad) : 1.0;
      const isOnline = !isFaulted && (devProfile?.category === 'CRITICAL' || servedRatio > 0.85);
      const currentPower = isFaulted ? 0.0 : (isOnline ? nominalPower * servedRatio : 0.0);

      // Estimate AC current: I = (P * 1000) / (sqrt(3) * 400 * 0.9)
      const voltage = stationDetail?.electrical?.nominal_voltage_v || 400;
      const currentAmps = currentPower > 0.05
        ? Math.round(((currentPower * 1000) / (Math.sqrt(3) * voltage * 0.90)) * 10) / 10
        : null;

      // Plain language explanations
      let whatItDoes = `Provides dedicated ${devProfile?.category.toLowerCase() || 'station'} power to ${node.label}.`;
      let whyItMatters = `Essential for mission continuity and safe operational condition.`;

      if (node.deviceId.includes('life_support') || node.deviceId.includes('heating')) {
        whatItDoes = 'Maintains habitable indoor temperatures, air circulation, and life-support atmosphere.';
        whyItMatters = 'In polar winter (-40°C), temperature drops to freezing within hours if heating is lost.';
      } else if (node.deviceId.includes('water') || node.deviceId.includes('melt')) {
        whatItDoes = 'Pumps drinking water and prevents water pipelines from freezing solid in extreme cold.';
        whyItMatters = 'Frozen pipes cause catastrophic mechanical bursting and eliminate station potable water.';
      } else if (node.deviceId.includes('comms') || node.deviceId.includes('satcom') || node.deviceId.includes('uplink')) {
        whatItDoes = 'Transmits scientific telemetry and maintains emergency satellite voice/data link.';
        whyItMatters = 'Sole communications lifeline connecting the isolated polar outpost to mainland operations.';
      } else if (node.deviceId.includes('lab') || node.deviceId.includes('sci') || node.deviceId.includes('spectrometer')) {
        whatItDoes = 'Powers sensitive atmospheric, seismic, and geomagnetic scientific sensor arrays.';
        whyItMatters = 'Primary research mission of the station; deferrable during severe power emergencies.';
      } else if (node.deviceId.includes('ev') || node.deviceId.includes('workshop')) {
        whatItDoes = 'Supplies power for equipment repairs and charges electric transport skidoos.';
        whyItMatters = 'Flexible auxiliary load that can be shed first to protect habitat warmth.';
      }

      devicesMap[node.deviceId] = {
        id: node.deviceId,
        name: devProfile?.name || node.label,
        category: devProfile?.category || 'OPERATIONAL',
        priorityRank: devProfile?.priority_rank || 5,
        nominalPowerKw: nominalPower,
        currentPowerKw: Math.round(currentPower * 10) / 10,
        currentAmps,
        nominalVoltageV: voltage,
        status: isFaulted ? 'FAULT' : (isOnline ? 'ONLINE' : 'DEFERRED'),
        zoneId: node.zoneId || '',
        zoneName: spatialProfile.zones.find(z => z.id === node.zoneId)?.name || 'General',
        circuitId: node.circuitId || '',
        deferrable: devProfile?.deferrable || false,
        thermalConsequence: (devProfile as any)?.thermal_consequence || 'LOW',
        provenance,
        whatItDoes,
        whyItMatters,
        upstreamNodeIds: [],
        upstreamEdgeIds: []
      };
    }
  });

  // 3. Upstream & Downstream Lineage Graph Resolution
  // Trace Power: Device -> Circuit Edge -> Sub-DB Node -> Feeder Edge -> Main Bus -> Generator Edges
  // Trace Impact: Source/Fault -> Bus -> Feeders -> Sub-DBs -> Branch Edges -> Devices
  const tracedPathEdgeIds = new Set<string>();
  const tracedPathNodeIds = new Set<string>();

  const activeDeviceId = selectedDeviceId || (selectedNodeId && devicesMap[selectedNodeId]?.id) || null;

  if (activeDeviceId && devicesMap[activeDeviceId]) {
    const dev = devicesMap[activeDeviceId];
    const devNode = spatialProfile.nodes.find(n => n.deviceId === dev.id);
    if (devNode) {
      tracedPathNodeIds.add(devNode.id);
      
      // Find edge connecting to this device
      const branchEdge = spatialProfile.edges.find(e => e.toNodeId === devNode.id || e.fromNodeId === devNode.id);
      if (branchEdge) {
        tracedPathEdgeIds.add(branchEdge.id);
        const subBusId = branchEdge.fromNodeId === devNode.id ? branchEdge.toNodeId : branchEdge.fromNodeId;
        tracedPathNodeIds.add(subBusId);

        // Find feeder edge from Main Bus to Sub-DB
        const feederEdge = spatialProfile.edges.find(e => 
          (e.toNodeId === subBusId && e.fromNodeId === 'node_main_bus') ||
          (e.fromNodeId === subBusId && e.toNodeId === 'node_main_bus')
        );
        if (feederEdge) {
          tracedPathEdgeIds.add(feederEdge.id);
          tracedPathNodeIds.add('node_main_bus');

          // Highlight currently active source feeds to main bus
          spatialProfile.edges.forEach(e => {
            if (e.toNodeId === 'node_main_bus' || e.fromNodeId === 'node_main_bus') {
              if (e.id.includes('solar') && solarGen > 0.05) {
                tracedPathEdgeIds.add(e.id);
                tracedPathNodeIds.add(e.fromNodeId);
              }
              if (e.id.includes('wind') && windGen > 0.05) {
                tracedPathEdgeIds.add(e.id);
                tracedPathNodeIds.add(e.fromNodeId);
              }
              if (e.id.includes('diesel') && dieselGen > 0.05) {
                tracedPathEdgeIds.add(e.id);
                tracedPathNodeIds.add(e.fromNodeId);
              }
              if (e.id.includes('battery') && batDischarge > 0.05) {
                tracedPathEdgeIds.add(e.id);
                tracedPathNodeIds.add(e.fromNodeId);
              }
            }
          });
        }
      }
    }
  }

  // If a source node is selected for Trace Impact:
  if (selectedNodeId && (selectedNodeId.includes('solar') || selectedNodeId.includes('wind') || selectedNodeId.includes('diesel') || selectedNodeId.includes('battery'))) {
    tracedPathNodeIds.add(selectedNodeId);
    
    // Find the bus connected to this source
    const genEdge = spatialProfile.edges.find(e => e.fromNodeId === selectedNodeId || e.toNodeId === selectedNodeId);
    const busId = genEdge ? (genEdge.toNodeId === selectedNodeId ? genEdge.fromNodeId : genEdge.toNodeId) : 'node_main_bus';
    tracedPathNodeIds.add(busId);
    if (genEdge) tracedPathEdgeIds.add(genEdge.id);

    // Trace downstream feeder lines leaving the bus to sub-distribution panels
    spatialProfile.edges.forEach(e => {
      if (e.fromNodeId === busId) {
        tracedPathEdgeIds.add(e.id);
        tracedPathNodeIds.add(e.toNodeId);
      }
    });
  }

  // 4. Transform Edges (Power Flow, Source Mix, Direction, Line Width)
  const edges: VisualEdgeState[] = spatialProfile.edges.map(edge => {
    let powerKw = 0.0;
    let direction: 'FORWARD' | 'REVERSE' | 'NONE' = edge.direction;
    const isFaulted = faultedCircuitIds.has(edge.circuitId || '');

    // Source feeds
    if (edge.id.includes('solar')) {
      powerKw = solarGen;
      direction = solarGen > 0.05 ? 'FORWARD' : 'NONE';
    } else if (edge.id.includes('wind')) {
      powerKw = windGen;
      direction = windGen > 0.05 ? 'FORWARD' : 'NONE';
    } else if (edge.id.includes('diesel')) {
      powerKw = dieselGen;
      direction = dieselGen > 0.05 ? 'FORWARD' : 'NONE';
    } else if (edge.id.includes('battery')) {
      if (batCharge > 0.05) {
        powerKw = batCharge;
        direction = 'FORWARD'; // Bus -> Battery (charging)
      } else if (batDischarge > 0.05) {
        powerKw = batDischarge;
        direction = 'REVERSE'; // Battery -> Bus (discharging)
      } else {
        powerKw = 0.0;
        direction = 'NONE';
      }
    } else {
      // Find destination device load if branch edge
      const destNode = spatialProfile.nodes.find(n => n.id === edge.toNodeId);
      if (destNode?.deviceId && devicesMap[destNode.deviceId]) {
        powerKw = devicesMap[destNode.deviceId].currentPowerKw;
        direction = powerKw > 0.05 ? 'FORWARD' : 'NONE';
      } else {
        // Sub-feeder line: aggregate load of downstream devices
        const subBusId = edge.toNodeId;
        const connectedEdges = spatialProfile.edges.filter(e => e.fromNodeId === subBusId);
        powerKw = connectedEdges.reduce((acc, ce) => {
          const dn = spatialProfile.nodes.find(n => n.id === ce.toNodeId);
          return acc + (dn?.deviceId && devicesMap[dn.deviceId] ? devicesMap[dn.deviceId].currentPowerKw : 0);
        }, 0);
        direction = powerKw > 0.05 ? 'FORWARD' : 'NONE';
      }
    }

    if (isFaulted) {
      powerKw = 0.0;
      direction = 'NONE';
    }

    // Source mix attribution
    const totalSourceGen = Math.max(0.1, totalGen);
    const solarShare = solarGen / totalSourceGen;
    const windShare = windGen / totalSourceGen;
    const dieselShare = dieselGen / totalSourceGen;
    const batteryShare = Math.max(0, batDischarge) / totalSourceGen;

    const sourceMix: TwinSourceMix = {
      solarKw: Math.round(powerKw * solarShare * 10) / 10,
      windKw: Math.round(powerKw * windShare * 10) / 10,
      dieselKw: Math.round(powerKw * dieselShare * 10) / 10,
      batteryKw: Math.round(powerKw * batteryShare * 10) / 10
    };

    const hasDieselContribution = sourceMix.dieselKw > 0.05;
    const isBatteryCharge = edge.id.includes('battery') && direction === 'FORWARD';
    const isBatteryDischarge = edge.id.includes('battery') && direction === 'REVERSE';
    const isRenewableDominant = (sourceMix.solarKw + sourceMix.windKw) >= sourceMix.dieselKw;

    let flowSemantic: 'RENEWABLE' | 'NON_RENEWABLE' | 'BATTERY' | 'DORMANT' | 'FAULT' = 'RENEWABLE';
    if (isFaulted) {
      flowSemantic = 'FAULT';
    } else if (powerKw <= 0.05) {
      flowSemantic = 'DORMANT';
    } else if (hasDieselContribution) {
      flowSemantic = 'NON_RENEWABLE';
    } else if (isBatteryCharge || isBatteryDischarge) {
      flowSemantic = 'BATTERY';
    } else {
      flowSemantic = 'RENEWABLE';
    }

    // Line width: 1.5px dormant, 2.5px normal, 4px high flow
    let lineWidthPx = 1.5;
    if (powerKw > 30.0) lineWidthPx = 4.0;
    else if (powerKw > 15.0) lineWidthPx = 3.0;
    else if (powerKw > 0.05) lineWidthPx = 2.2;

    const isTraced = tracedPathEdgeIds.has(edge.id);
    const isDimmed = (tracePowerActive || traceImpactActive) && !isTraced;

    return {
      ...edge,
      direction,
      powerKw: Math.round(powerKw * 10) / 10,
      sourceMix,
      hasDieselContribution,
      isRenewableDominant,
      isBatteryCharge,
      isBatteryDischarge,
      flowSemantic,
      lineWidthPx,
      highlighted: isTraced,
      dimmed: isDimmed,
      active: powerKw > 0.05 && !isFaulted
    };
  });

  // 5. Transform Zones with Aggregated Load & Fault Status
  const zones: VisualZoneState[] = spatialProfile.zones.map(zone => {
    const zoneDevices = Object.values(devicesMap).filter(d => d.zoneId === zone.id);
    const totalZoneLoad = zoneDevices.reduce((acc, d) => acc + d.currentPowerKw, 0);
    const criticalZoneLoad = zoneDevices
      .filter(d => d.category === 'CRITICAL')
      .reduce((acc, d) => acc + d.currentPowerKw, 0);
    const activeCount = zoneDevices.filter(d => d.status === 'ONLINE').length;
    const hasFault = zoneDevices.some(d => d.status === 'FAULT');
    const isSelected = selectedZoneId === zone.id;

    return {
      ...zone,
      totalLoadKw: Math.round(totalZoneLoad * 10) / 10,
      criticalLoadKw: Math.round(criticalZoneLoad * 10) / 10,
      connectedDeviceCount: zoneDevices.length,
      activeDeviceCount: activeCount,
      hasFault,
      highlighted: isSelected
    };
  });

  return {
    stationId,
    timestamp,
    viewMode,
    layoutStatus: spatialProfile.layoutStatus || 'REPRESENTATIVE',
    geometryBasis: spatialProfile.geometryBasis || 'REPRESENTATIVE / CONFIGURED',
    dimensions: {
      width: spatialProfile.width || 1000,
      height: spatialProfile.height || 640
    },
    powerSummary: {
      totalGenerationKw: Math.round(totalGen * 10) / 10,
      solarGenerationKw: Math.round(solarGen * 10) / 10,
      windGenerationKw: Math.round(windGen * 10) / 10,
      dieselGenerationKw: Math.round(dieselGen * 10) / 10,
      batteryPowerKw: Math.round(batPower * 10) / 10,
      batterySocPct: Math.round(batSoc * 1000) / 10, // e.g. 65.2%
      totalLoadKw: Math.round(totalLoad * 10) / 10,
      servedLoadKw: Math.round(servedLoad * 10) / 10,
      unservedLoadKw: Math.round(unservedLoad * 10) / 10,
      criticalLoadKw: Math.round(criticalLoad * 10) / 10,
      renewableFractionPct: Math.round(renewableFraction * 10) / 10,
      dominantSource,
      conservationGapKw: Math.round(conservationGap * 100) / 100
    },
    environment: {
      ambientTempC: Number(twinState?.environment?.ambient_temperature_c ?? -22.5),
      windSpeedMs: Number(twinState?.environment?.wind_speed_ms ?? 9.2),
      irradianceWm2: Number(twinState?.environment?.irradiance_wm2 ?? 115.0),
      stormState: String(twinState?.environment?.storm_state || 'NORMAL')
    },
    thermal: {
      indoorTempC: Number(twinState?.thermal?.indoor_temperature_c ?? 19.8),
      targetTempC: Number(twinState?.thermal?.thermal_setpoint_c ?? 20.0),
      minSafeTempC: Number(twinState?.thermal?.indoor_min_safe_temp_c ?? 12.0),
      isSafe: Boolean(twinState?.thermal?.is_safe ?? true),
      heatingPowerKw: Number(twinState?.thermal?.heating_power_kw ?? 14.5)
    },
    resilience: {
      threatState: String(twinState?.resilience?.threat_state || 'SAFE'),
      survivalHorizonHours: Number(twinState?.resilience?.continuity_horizon_hours ?? 84.0),
      limitingResource: 'Diesel Fuel Tank Runway'
    },
    zones,
    nodes: spatialProfile.nodes,
    edges,
    devices: devicesMap,
    selectedNodeId,
    selectedZoneId,
    selectedDeviceId,
    tracedPathEdgeIds,
    tracedPathNodeIds,
    activeFaultCircuitIds: faultedCircuitIds,
    provenance
  };
}
