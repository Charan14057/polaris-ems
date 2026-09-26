/**
 * POLARIS-EMS — Station 3D Spatial Profiles & Geometry Registry
 * Phase 18: Operational 3D Digital Twin Engine
 * 
 * Configured representative 3D geometry for Bharati, Maitri, and Himadri research stations.
 * Structural basis derived from authoritative polar station architectural layouts.
 * 
 * STRICT EPISTEMIC CLASSIFICATION:
 * GEOMETRY BASIS: CONFIGURED / REPRESENTATIVE
 * NEVER CLAIM: EXACT FLOOR PLAN, SURVEYED MODEL, AS-BUILT MODEL.
 * Devices bound to StationProfileRegistry device IDs; unmatched objects marked SPATIAL_CONTEXT_ONLY.
 */

export type SpatialCategory3D = 
  | 'SOURCE'
  | 'STORAGE'
  | 'BUS'
  | 'FEEDER'
  | 'PANEL'
  | 'CRITICAL_LOAD'
  | 'IMPORTANT_LOAD'
  | 'OPERATIONAL_LOAD'
  | 'FLEXIBLE_LOAD'
  | 'UTILITY'
  | 'SCIENCE'
  | 'HABITATION'
  | 'COMMUNICATION'
  | 'EXTERNAL_INFRASTRUCTURE';

export type LoadImportance3D = 'CRITICAL' | 'IMPORTANT' | 'OPERATIONAL' | 'FLEXIBLE';

export interface SpatialObject3D {
  id: string;
  name: string;
  category: SpatialCategory3D;
  zone: string;
  position: [number, number, number]; // [x, y, z] in world meters
  dimensions: [number, number, number]; // [width, height, depth] in meters
  elevation: number;
  parentAsset?: string;
  deviceId?: string | null;
  circuitId?: string;
  importance: LoadImportance3D;
  nominalPowerKw: number;
  status: 'ONLINE' | 'STANDBY' | 'DEFERRED' | 'FAULT' | 'OFF' | 'SPATIAL_CONTEXT_ONLY';
  provenance: 'CONFIGURED' | 'ASSUMED' | 'SIMULATED';
  selectable: boolean;
  color?: string;
  meshType?: 'box' | 'cylinder' | 'turbine' | 'building' | 'bus' | 'line';
  realWorldContext?: string;
}

export interface StationDeck3D {
  id: string;
  name: string;
  elevation: number;
  bounds: { minX: number; maxX: number; minZ: number; maxZ: number };
  color: string;
  opacity: number;
  description: string;
}

export interface PowerFlowPath3D {
  id: string;
  name: string;
  fromId: string;
  toId: string;
  circuitId: string;
  type: 'SOURCE_FEED' | 'MAIN_BUS' | 'FEEDER' | 'BRANCH';
  points: [number, number, number][];
  defaultActive: boolean;
  nominalKw: number;
}

export interface StationSpatial3DProfile {
  stationId: 'BHARATI' | 'MAITRI' | 'HIMADRI';
  name: string;
  location: string;
  architectureDescription: string;
  geometryBasis: 'CONFIGURED / REPRESENTATIVE';
  elevationM: number;
  terrainType: 'BEDROCK_ICE' | 'ROCKY_OASIS' | 'ARCTIC_TUNDRA';
  groundColor: string;
  decks: StationDeck3D[];
  objects: SpatialObject3D[];
  powerFlowPaths: PowerFlowPath3D[];
}

export const STATION_SPATIAL_3D_PROFILES: Record<string, StationSpatial3DProfile> = {
  // ===========================================================================
  // 1. BHARATI RESEARCH STATION (Larsemann Hills, East Antarctica)
  // Raised modular station on steel stilts, 3 levels, multi-deck layout
  // ===========================================================================
  BHARATI: {
    stationId: 'BHARATI',
    name: 'Bharati Antarctic Research Station',
    location: 'Larsemann Hills, East Antarctica (69°24′S, 76°11′E)',
    architectureDescription: 'Elevated multi-deck aerodynamic containerized structure mounted on structural steel pilings with separate fuel farm and seawater intake.',
    geometryBasis: 'CONFIGURED / REPRESENTATIVE',
    elevationM: 35,
    terrainType: 'BEDROCK_ICE',
    groundColor: '#cbd5e1',
    decks: [
      {
        id: 'bh_ground',
        name: 'Terrain & Foundation Level (0.0m)',
        elevation: 0.0,
        bounds: { minX: -35, maxX: 35, minZ: -25, maxZ: 25 },
        color: '#94a3b8',
        opacity: 0.35,
        description: 'Bedrock footing, structural columns, fuel containment berms, and snowmelt staging'
      },
      {
        id: 'bh_deck_1',
        name: 'Lower Engineering Deck (+3.5m)',
        elevation: 3.5,
        bounds: { minX: -22, maxX: 22, minZ: -14, maxZ: 14 },
        color: '#e2e8f0',
        opacity: 0.45,
        description: 'Diesel power generation, battery energy storage (BESS), water treatment, HVAC machinery, and workshops'
      },
      {
        id: 'bh_deck_2',
        name: 'Main Habitation & Operations Deck (+7.5m)',
        elevation: 7.5,
        bounds: { minX: -20, maxX: 20, minZ: -12, maxZ: 12 },
        color: '#f1f5f9',
        opacity: 0.5,
        description: 'Living quarters, dining galley, satellite communications bridge, and mission servers'
      },
      {
        id: 'bh_deck_3',
        name: 'Upper Science & Observation Deck (+11.5m)',
        elevation: 11.5,
        bounds: { minX: -14, maxX: 14, minZ: -8, maxZ: 8 },
        color: '#ffffff',
        opacity: 0.55,
        description: 'Atmospheric research labs, optical observation bridge, clean labs, and LIDAR platform'
      }
    ],
    objects: [
      // --- SOURCES & STORAGE ---
      {
        id: 'bh_obj_solar',
        name: 'Photovoltaic Array (30 kWp)',
        category: 'SOURCE',
        zone: 'bh_ground',
        position: [-26, 0.5, -16],
        dimensions: [12, 1.2, 8],
        elevation: 0.5,
        deviceId: 'solar_pv_array',
        circuitId: 'c_gen_solar',
        importance: 'OPERATIONAL',
        nominalPowerKw: 30.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#f59e0b',
        meshType: 'box',
        realWorldContext: 'Elevated bifacial solar panel array positioned to capture direct irradiance and albedo reflection'
      },
      {
        id: 'bh_obj_wind_1',
        name: 'Wind Turbine Mast 1 (15 kW)',
        category: 'SOURCE',
        zone: 'bh_ground',
        position: [-28, 6.0, 16],
        dimensions: [2, 12, 2],
        elevation: 6.0,
        deviceId: 'wind_turbine_1',
        circuitId: 'c_gen_wind',
        importance: 'OPERATIONAL',
        nominalPowerKw: 15.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#0284c7',
        meshType: 'turbine',
        realWorldContext: 'High-latitude polar katabatic wind turbine with cold-weather de-icing heating'
      },
      {
        id: 'bh_obj_wind_2',
        name: 'Wind Turbine Mast 2 (10 kW)',
        category: 'SOURCE',
        zone: 'bh_ground',
        position: [-20, 5.0, 18],
        dimensions: [2, 10, 2],
        elevation: 5.0,
        deviceId: 'wind_turbine_2',
        circuitId: 'c_gen_wind',
        importance: 'OPERATIONAL',
        nominalPowerKw: 10.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#0284c7',
        meshType: 'turbine',
        realWorldContext: 'Auxiliary polar wind turbine deployed on prevailing katabatic ridge'
      },
      {
        id: 'bh_obj_diesel_bank',
        name: 'Primary Diesel Gensets (3x80 kW)',
        category: 'SOURCE',
        zone: 'bh_deck_1',
        position: [-14, 4.2, -6],
        dimensions: [6, 2.5, 4],
        elevation: 4.2,
        deviceId: 'diesel_generator_1',
        circuitId: 'c_gen_diesel',
        importance: 'CRITICAL',
        nominalPowerKw: 80.0,
        status: 'STANDBY',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#b45309',
        meshType: 'box',
        realWorldContext: 'Acoustically isolated generator compartment with pre-heating heat recovery jackets'
      },
      {
        id: 'bh_obj_bess',
        name: 'Battery Energy Storage (120 kWh BESS)',
        category: 'STORAGE',
        zone: 'bh_deck_1',
        position: [-14, 4.2, 4],
        dimensions: [5, 2.4, 3.5],
        elevation: 4.2,
        deviceId: 'bess_bank_1',
        circuitId: 'c_gen_bess',
        importance: 'CRITICAL',
        nominalPowerKw: 50.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#059669',
        meshType: 'box',
        realWorldContext: 'Lithium Iron Phosphate (LFP) containerized battery with integrated thermal management'
      },
      // --- ELECTRICAL DISTRIBUTION (BUSES & PANELS) ---
      {
        id: 'bh_obj_main_bus',
        name: 'Main 400V AC Switchboard (SWB-1)',
        category: 'BUS',
        zone: 'bh_deck_1',
        position: [-4, 4.5, 0],
        dimensions: [4, 2.6, 1.5],
        elevation: 4.5,
        circuitId: 'c_main_bus',
        importance: 'CRITICAL',
        nominalPowerKw: 250.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#0284c7',
        meshType: 'bus',
        realWorldContext: 'Three-phase 400V 50Hz main distribution board with motorized tie-breakers'
      },
      {
        id: 'bh_obj_panel_util',
        name: 'Sub-Distribution Panel DB-1 (Utilities)',
        category: 'PANEL',
        zone: 'bh_deck_1',
        position: [4, 4.2, -6],
        dimensions: [1.5, 2.0, 0.8],
        elevation: 4.2,
        circuitId: 'c_feeder_util',
        importance: 'CRITICAL',
        nominalPowerKw: 60.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Life support and plant utility switchboard'
      },
      {
        id: 'bh_obj_panel_hab',
        name: 'Sub-Distribution Panel DB-2 (Habitation)',
        category: 'PANEL',
        zone: 'bh_deck_2',
        position: [4, 8.2, 2],
        dimensions: [1.5, 2.0, 0.8],
        elevation: 8.2,
        circuitId: 'c_feeder_hab',
        importance: 'IMPORTANT',
        nominalPowerKw: 45.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Living quarters and galley distribution panel'
      },
      {
        id: 'bh_obj_panel_ops',
        name: 'Sub-Distribution Panel DB-3 (Operations)',
        category: 'PANEL',
        zone: 'bh_deck_2',
        position: [-6, 8.2, -4],
        dimensions: [1.5, 2.0, 0.8],
        elevation: 8.2,
        circuitId: 'c_feeder_ops',
        importance: 'CRITICAL',
        nominalPowerKw: 35.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Comms, server, and navigation sub-panel'
      },
      {
        id: 'bh_obj_panel_sci',
        name: 'Sub-Distribution Panel DB-4 (Science)',
        category: 'PANEL',
        zone: 'bh_deck_3',
        position: [2, 12.2, 0],
        dimensions: [1.5, 2.0, 0.8],
        elevation: 12.2,
        circuitId: 'c_feeder_sci',
        importance: 'OPERATIONAL',
        nominalPowerKw: 40.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Laboratory instruments and clean bench panel'
      },
      {
        id: 'bh_obj_panel_work',
        name: 'Sub-Distribution Panel DB-5 (Workshop)',
        category: 'PANEL',
        zone: 'bh_deck_1',
        position: [14, 4.2, 6],
        dimensions: [1.5, 2.0, 0.8],
        elevation: 4.2,
        circuitId: 'c_feeder_work',
        importance: 'FLEXIBLE',
        nominalPowerKw: 30.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Workshop machinery and vehicle skid charging'
      },
      // --- OPERATIONAL LOADS (BOUND TO STATION PROFILE) ---
      {
        id: 'bh_obj_life_support',
        name: 'Life Support HVAC & Air Handling',
        category: 'CRITICAL_LOAD',
        zone: 'bh_deck_1',
        position: [8, 4.3, -6],
        dimensions: [3.5, 2.2, 2.5],
        elevation: 4.3,
        deviceId: 'bh_life_support',
        circuitId: 'c_bh_life_support',
        importance: 'CRITICAL',
        nominalPowerKw: 18.5,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#e11d48',
        meshType: 'box',
        realWorldContext: 'Dual-redundant air handling unit, fresh air intake heat exchanger, and habitat pressurization'
      },
      {
        id: 'bh_obj_water_freeze_prot',
        name: 'Seawater Pumps & Freeze Protection',
        category: 'CRITICAL_LOAD',
        zone: 'bh_deck_1',
        position: [14, 4.3, -6],
        dimensions: [3.0, 2.0, 2.0],
        elevation: 4.3,
        deviceId: 'bh_water_freeze_prot',
        circuitId: 'c_bh_water_freeze_prot',
        importance: 'CRITICAL',
        nominalPowerKw: 6.8,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#e11d48',
        meshType: 'box',
        realWorldContext: 'Electric heat-tracing tapes and intake pumps running along the 1.2 km seawater line'
      },
      {
        id: 'bh_obj_snow_melter',
        name: 'Bulk Snow Melter Tank',
        category: 'UTILITY',
        zone: 'bh_ground',
        position: [18, 1.2, -14],
        dimensions: [4.0, 2.4, 4.0],
        elevation: 1.2,
        deviceId: 'bh_snow_melter',
        circuitId: 'c_bh_snow_melter',
        importance: 'FLEXIBLE',
        nominalPowerKw: 12.0,
        status: 'STANDBY',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#38bdf8',
        meshType: 'cylinder',
        realWorldContext: 'Thermal snow melter delivering primary potable water; can be deferred up to 6 hours'
      },
      {
        id: 'bh_obj_satcom',
        name: 'Satellite Comms & Nav Bridge',
        category: 'COMMUNICATION',
        zone: 'bh_deck_2',
        position: [-12, 8.3, -4],
        dimensions: [3.0, 2.2, 2.5],
        elevation: 8.3,
        deviceId: 'bh_satcom_net',
        circuitId: 'c_bh_satcom_net',
        importance: 'CRITICAL',
        nominalPowerKw: 4.2,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#e11d48',
        meshType: 'box',
        realWorldContext: 'Geostationary and LEO satellite transceiver radome link for emergency data and telemedicine'
      },
      {
        id: 'bh_obj_servers',
        name: 'Mission Compute & Data Servers',
        category: 'OPERATIONAL_LOAD',
        zone: 'bh_deck_2',
        position: [-4, 8.3, -4],
        dimensions: [2.5, 2.2, 1.8],
        elevation: 8.3,
        deviceId: 'bh_data_servers',
        circuitId: 'c_bh_data_servers',
        importance: 'IMPORTANT',
        nominalPowerKw: 5.3,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#0284c7',
        meshType: 'box',
        realWorldContext: 'Scientific storage arrays, seismic data recorders, and station automated telemetry logging'
      },
      {
        id: 'bh_obj_res_light',
        name: 'Living Quarters Habitat Lighting',
        category: 'HABITATION',
        zone: 'bh_deck_2',
        position: [8, 8.3, 4],
        dimensions: [6.0, 2.4, 4.0],
        elevation: 8.3,
        deviceId: 'bh_residential_light',
        circuitId: 'c_bh_residential_light',
        importance: 'IMPORTANT',
        nominalPowerKw: 5.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#10b981',
        meshType: 'box',
        realWorldContext: 'Circadian LED lighting and climate air conditioning across 24 crew berths'
      },
      {
        id: 'bh_obj_galley',
        name: 'Galley & Cold Food Storage',
        category: 'HABITATION',
        zone: 'bh_deck_2',
        position: [14, 8.3, -2],
        dimensions: [4.0, 2.4, 3.5],
        elevation: 8.3,
        deviceId: 'bh_galley_storage',
        circuitId: 'c_bh_galley_storage',
        importance: 'IMPORTANT',
        nominalPowerKw: 6.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#10b981',
        meshType: 'box',
        realWorldContext: 'Commercial refrigeration, food preparation ovens, and water kettle circuits'
      },
      {
        id: 'bh_obj_science_lab',
        name: 'Core Environmental Science Lab',
        category: 'SCIENCE',
        zone: 'bh_deck_3',
        position: [-6, 12.3, 0],
        dimensions: [5.0, 2.3, 3.5],
        elevation: 12.3,
        deviceId: 'bh_science_lab',
        circuitId: 'c_bh_science_lab',
        importance: 'OPERATIONAL',
        nominalPowerKw: 7.5,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#8b5cf6',
        meshType: 'box',
        realWorldContext: 'Spectrophotometers, air sample particulate counters, gas chromatograph, and clean workstations'
      },
      {
        id: 'bh_obj_waste',
        name: 'Wastewater Treatment Auxiliaries',
        category: 'UTILITY',
        zone: 'bh_deck_1',
        position: [18, 4.3, 0],
        dimensions: [3.5, 2.2, 3.0],
        elevation: 4.3,
        deviceId: 'bh_waste_management',
        circuitId: 'c_bh_waste_management',
        importance: 'OPERATIONAL',
        nominalPowerKw: 3.8,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Biological wastewater recycling reactor and ultraviolet effluent sterilization'
      },
      {
        id: 'bh_obj_workshop',
        name: 'Maintenance Bay & EV Charger',
        category: 'FLEXIBLE_LOAD',
        zone: 'bh_deck_1',
        position: [14, 4.3, 8],
        dimensions: [5.0, 2.5, 4.0],
        elevation: 4.3,
        deviceId: 'bh_workshop_ev',
        circuitId: 'c_bh_workshop_ev',
        importance: 'FLEXIBLE',
        nominalPowerKw: 9.0,
        status: 'STANDBY',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#f59e0b',
        meshType: 'box',
        realWorldContext: 'Snowmobile and tracked vehicle electric pre-heating and auxiliary power tools'
      },
      // --- SPATIAL CONTEXT ONLY OBJECTS (NOT ELECTRICALLY ACTIVE) ---
      {
        id: 'bh_ctx_fuel_farm',
        name: 'Bulk Arctic Diesel Fuel Farm',
        category: 'EXTERNAL_INFRASTRUCTURE',
        zone: 'bh_ground',
        position: [-24, 1.0, 4],
        dimensions: [7, 2.2, 5],
        elevation: 1.0,
        importance: 'IMPORTANT',
        nominalPowerKw: 0.0,
        status: 'SPATIAL_CONTEXT_ONLY',
        provenance: 'ASSUMED',
        selectable: false,
        color: '#71717a',
        meshType: 'cylinder',
        realWorldContext: 'Double-walled polar diesel fuel tanks providing winter reserve'
      },
      {
        id: 'bh_ctx_lidar_dome',
        name: 'Atmospheric LIDAR Shelter',
        category: 'EXTERNAL_INFRASTRUCTURE',
        zone: 'bh_deck_3',
        position: [8, 13.0, 0],
        dimensions: [3, 2.5, 3],
        elevation: 13.0,
        importance: 'OPERATIONAL',
        nominalPowerKw: 0.0,
        status: 'SPATIAL_CONTEXT_ONLY',
        provenance: 'ASSUMED',
        selectable: false,
        color: '#cbd5e1',
        meshType: 'cylinder',
        realWorldContext: 'Roof optical dome for upper atmospheric aerosol and ozone laser profiling'
      }
    ],
    powerFlowPaths: [
      // Sources to Main Bus
      { id: 'bh_flow_solar', name: 'Solar PV Feed', fromId: 'bh_obj_solar', toId: 'bh_obj_main_bus', circuitId: 'c_gen_solar', type: 'SOURCE_FEED', points: [[-26, 0.8, -16], [-10, 0.8, -8], [-4, 4.5, 0]], defaultActive: true, nominalKw: 30.0 },
      { id: 'bh_flow_wind1', name: 'Wind Turbine 1 Feed', fromId: 'bh_obj_wind_1', toId: 'bh_obj_main_bus', circuitId: 'c_gen_wind', type: 'SOURCE_FEED', points: [[-28, 6.0, 16], [-14, 4.0, 8], [-4, 4.5, 0]], defaultActive: true, nominalKw: 15.0 },
      { id: 'bh_flow_wind2', name: 'Wind Turbine 2 Feed', fromId: 'bh_obj_wind_2', toId: 'bh_obj_main_bus', circuitId: 'c_gen_wind', type: 'SOURCE_FEED', points: [[-20, 5.0, 18], [-10, 4.0, 8], [-4, 4.5, 0]], defaultActive: true, nominalKw: 10.0 },
      { id: 'bh_flow_diesel', name: 'Diesel Genset Feed', fromId: 'bh_obj_diesel_bank', toId: 'bh_obj_main_bus', circuitId: 'c_gen_diesel', type: 'SOURCE_FEED', points: [[-14, 4.2, -6], [-4, 4.5, 0]], defaultActive: false, nominalKw: 80.0 },
      { id: 'bh_flow_bess', name: 'BESS Battery Feed', fromId: 'bh_obj_bess', toId: 'bh_obj_main_bus', circuitId: 'c_gen_bess', type: 'SOURCE_FEED', points: [[-14, 4.2, 4], [-4, 4.5, 0]], defaultActive: false, nominalKw: 50.0 },
      // Main Bus to Panels
      { id: 'bh_flow_feeder_util', name: 'Feeder F1 (Utilities)', fromId: 'bh_obj_main_bus', toId: 'bh_obj_panel_util', circuitId: 'c_feeder_util', type: 'FEEDER', points: [[-4, 4.5, 0], [4, 4.2, -6]], defaultActive: true, nominalKw: 60.0 },
      { id: 'bh_flow_feeder_hab', name: 'Feeder F2 (Habitation)', fromId: 'bh_obj_main_bus', toId: 'bh_obj_panel_hab', circuitId: 'c_feeder_hab', type: 'FEEDER', points: [[-4, 4.5, 0], [0, 8.2, 2], [4, 8.2, 2]], defaultActive: true, nominalKw: 45.0 },
      { id: 'bh_flow_feeder_ops', name: 'Feeder F3 (Operations)', fromId: 'bh_obj_main_bus', toId: 'bh_obj_panel_ops', circuitId: 'c_feeder_ops', type: 'FEEDER', points: [[-4, 4.5, 0], [-6, 8.2, -4]], defaultActive: true, nominalKw: 35.0 },
      { id: 'bh_flow_feeder_sci', name: 'Feeder F4 (Science)', fromId: 'bh_obj_main_bus', toId: 'bh_obj_panel_sci', circuitId: 'c_feeder_sci', type: 'FEEDER', points: [[-4, 4.5, 0], [0, 8.2, 0], [2, 12.2, 0]], defaultActive: true, nominalKw: 40.0 },
      { id: 'bh_flow_feeder_work', name: 'Feeder F5 (Workshop)', fromId: 'bh_obj_main_bus', toId: 'bh_obj_panel_work', circuitId: 'c_feeder_work', type: 'FEEDER', points: [[-4, 4.5, 0], [10, 4.2, 4], [14, 4.2, 6]], defaultActive: true, nominalKw: 30.0 },
      // Panels to Devices
      { id: 'bh_flow_dev_life', name: 'Life Support HVAC Circuit', fromId: 'bh_obj_panel_util', toId: 'bh_obj_life_support', circuitId: 'c_bh_life_support', type: 'BRANCH', points: [[4, 4.2, -6], [8, 4.3, -6]], defaultActive: true, nominalKw: 18.5 },
      { id: 'bh_flow_dev_water', name: 'Water Freeze Prot. Circuit', fromId: 'bh_obj_panel_util', toId: 'bh_obj_water_freeze_prot', circuitId: 'c_bh_water_freeze_prot', type: 'BRANCH', points: [[4, 4.2, -6], [14, 4.3, -6]], defaultActive: true, nominalKw: 6.8 },
      { id: 'bh_flow_dev_satcom', name: 'Satcom Circuit', fromId: 'bh_obj_panel_ops', toId: 'bh_obj_satcom', circuitId: 'c_bh_satcom_net', type: 'BRANCH', points: [[-6, 8.2, -4], [-12, 8.3, -4]], defaultActive: true, nominalKw: 4.2 },
      { id: 'bh_flow_dev_servers', name: 'Data Servers Circuit', fromId: 'bh_obj_panel_ops', toId: 'bh_obj_servers', circuitId: 'c_bh_data_servers', type: 'BRANCH', points: [[-6, 8.2, -4], [-4, 8.3, -4]], defaultActive: true, nominalKw: 5.3 },
      { id: 'bh_flow_dev_galley', name: 'Galley Storage Circuit', fromId: 'bh_obj_panel_hab', toId: 'bh_obj_galley', circuitId: 'c_bh_galley_storage', type: 'BRANCH', points: [[4, 8.2, 2], [14, 8.3, -2]], defaultActive: true, nominalKw: 6.0 },
      { id: 'bh_flow_dev_light', name: 'Crew Quarters Light Circuit', fromId: 'bh_obj_panel_hab', toId: 'bh_obj_res_light', circuitId: 'c_bh_residential_light', type: 'BRANCH', points: [[4, 8.2, 2], [8, 8.3, 4]], defaultActive: true, nominalKw: 5.0 },
      { id: 'bh_flow_dev_sci', name: 'Science Lab Circuit', fromId: 'bh_obj_panel_sci', toId: 'bh_obj_science_lab', circuitId: 'c_bh_science_lab', type: 'BRANCH', points: [[2, 12.2, 0], [-6, 12.3, 0]], defaultActive: true, nominalKw: 7.5 }
    ]
  },

  // ===========================================================================
  // 2. MAITRI RESEARCH STATION (Schirmacher Oasis, Queen Maud Land)
  // Living Blocks A & B connected by central spine corridor + lake pumping plant
  // ===========================================================================
  MAITRI: {
    stationId: 'MAITRI',
    name: 'Maitri Antarctic Research Station',
    location: 'Schirmacher Oasis, Queen Maud Land (70°46′S, 11°44′E)',
    architectureDescription: 'Twin living modules (Blocks A and B) connected by a central heated pipeline corridor, with dedicated power house and Priyadarshini Lake pumping manifold.',
    geometryBasis: 'CONFIGURED / REPRESENTATIVE',
    elevationM: 117,
    terrainType: 'ROCKY_OASIS',
    groundColor: '#94a3b8',
    decks: [
      {
        id: 'mt_ground',
        name: 'Oasis Rocky Foundation (0.0m)',
        elevation: 0.0,
        bounds: { minX: -40, maxX: 40, minZ: -30, maxZ: 30 },
        color: '#64748b',
        opacity: 0.35,
        description: 'Ice-free rocky plateau, foundation stilts, insulated pipeline supports'
      },
      {
        id: 'mt_main_level',
        name: 'Main Complex (+1.8m)',
        elevation: 1.8,
        bounds: { minX: -30, maxX: 30, minZ: -20, maxZ: 20 },
        color: '#e2e8f0',
        opacity: 0.5,
        description: 'Living Block A, Living Block B, Central Thermal Corridor, Power House'
      }
    ],
    objects: [
      // --- SOURCES & STORAGE ---
      {
        id: 'mt_obj_solar',
        name: 'Photovoltaic Array (18 kWp)',
        category: 'SOURCE',
        zone: 'mt_ground',
        position: [-24, 0.5, -18],
        dimensions: [10, 1.0, 6],
        elevation: 0.5,
        deviceId: 'solar_pv_array',
        circuitId: 'c_gen_solar',
        importance: 'OPERATIONAL',
        nominalPowerKw: 18.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#f59e0b',
        meshType: 'box',
        realWorldContext: 'Ground-mounted solar array facing north with snow clearing access'
      },
      {
        id: 'mt_obj_wind',
        name: 'Wind Turbine (15 kW)',
        category: 'SOURCE',
        zone: 'mt_ground',
        position: [-26, 6.0, 14],
        dimensions: [2, 12, 2],
        elevation: 6.0,
        deviceId: 'wind_turbine_1',
        circuitId: 'c_gen_wind',
        importance: 'OPERATIONAL',
        nominalPowerKw: 15.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#0284c7',
        meshType: 'turbine',
        realWorldContext: 'Polar wind generator mounted on bedrock ridge'
      },
      {
        id: 'mt_obj_diesel_house',
        name: 'Diesel Power House (3x62.5 kW Cummins)',
        category: 'SOURCE',
        zone: 'mt_main_level',
        position: [-16, 2.2, -6],
        dimensions: [8, 3.0, 6],
        elevation: 2.2,
        deviceId: 'diesel_generator_1',
        circuitId: 'c_gen_diesel',
        importance: 'CRITICAL',
        nominalPowerKw: 62.5,
        status: 'STANDBY',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#b45309',
        meshType: 'box',
        realWorldContext: 'Reinforced powerhouse building with 3x Kirloskar-Cummins engines and thermal heat exchanger'
      },
      {
        id: 'mt_obj_battery',
        name: 'BESS Battery Bank (90 kWh)',
        category: 'STORAGE',
        zone: 'mt_main_level',
        position: [-16, 2.2, 4],
        dimensions: [4, 2.2, 3],
        elevation: 2.2,
        deviceId: 'bess_bank_1',
        circuitId: 'c_gen_bess',
        importance: 'CRITICAL',
        nominalPowerKw: 40.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#059669',
        meshType: 'box',
        realWorldContext: 'Temperature-regulated battery room with fire suppression and ventilation'
      },
      // --- ELECTRICAL DISTRIBUTION ---
      {
        id: 'mt_obj_main_bus',
        name: 'Maitri Main 400V Switchboard',
        category: 'BUS',
        zone: 'mt_main_level',
        position: [-6, 2.5, 0],
        dimensions: [3.5, 2.4, 1.2],
        elevation: 2.5,
        circuitId: 'c_main_bus',
        importance: 'CRITICAL',
        nominalPowerKw: 200.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#0284c7',
        meshType: 'bus',
        realWorldContext: 'Main low-voltage switchgear distributing power to A/B blocks and water lines'
      },
      {
        id: 'mt_obj_panel_thermal',
        name: 'Heating & Boiler Sub-Panel (DB-1)',
        category: 'PANEL',
        zone: 'mt_main_level',
        position: [2, 2.2, -6],
        dimensions: [1.5, 2.0, 0.8],
        elevation: 2.2,
        circuitId: 'c_feeder_thermal',
        importance: 'CRITICAL',
        nominalPowerKw: 55.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Controls boiler circulation pumps and main hot water loops'
      },
      {
        id: 'mt_obj_panel_hab',
        name: 'Block A & B Living Panel (DB-4)',
        category: 'PANEL',
        zone: 'mt_main_level',
        position: [12, 2.2, 2],
        dimensions: [1.5, 2.0, 0.8],
        elevation: 2.2,
        circuitId: 'c_feeder_hab',
        importance: 'IMPORTANT',
        nominalPowerKw: 40.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Living quarters heating and galley power'
      },
      {
        id: 'mt_obj_panel_water',
        name: 'Lake Water Plant Panel (DB-5)',
        category: 'PANEL',
        zone: 'mt_main_level',
        position: [22, 2.2, -4],
        dimensions: [1.5, 2.0, 0.8],
        elevation: 2.2,
        circuitId: 'c_feeder_water',
        importance: 'CRITICAL',
        nominalPowerKw: 25.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Water pump house and trace-heating controllers'
      },
      // --- OPERATIONAL LOADS ---
      {
        id: 'mt_obj_heating_primary',
        name: 'Main Boiler Circulation Loop',
        category: 'CRITICAL_LOAD',
        zone: 'mt_main_level',
        position: [6, 2.3, -6],
        dimensions: [4, 2.2, 3],
        elevation: 2.3,
        deviceId: 'mt_heating_primary',
        circuitId: 'c_mt_heating_primary',
        importance: 'CRITICAL',
        nominalPowerKw: 22.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#e11d48',
        meshType: 'box',
        realWorldContext: 'Primary diesel-fired hot water boiler and circulation manifold keeping station above freezing'
      },
      {
        id: 'mt_obj_boiler_aux',
        name: 'Boiler Aux & Backup Heaters',
        category: 'CRITICAL_LOAD',
        zone: 'mt_main_level',
        position: [10, 2.3, -6],
        dimensions: [3, 2.0, 2],
        elevation: 2.3,
        deviceId: 'mt_boiler_aux',
        circuitId: 'c_mt_boiler_aux',
        importance: 'CRITICAL',
        nominalPowerKw: 8.5,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#e11d48',
        meshType: 'box',
        realWorldContext: 'Electric immersion heaters and auxiliary fuel booster pumps'
      },
      {
        id: 'mt_obj_comms',
        name: 'HF/VHF & Satellite Comms Station',
        category: 'COMMUNICATION',
        zone: 'mt_main_level',
        position: [2, 2.3, 6],
        dimensions: [3, 2.2, 2.5],
        elevation: 2.3,
        deviceId: 'mt_hf_comms',
        circuitId: 'c_mt_hf_comms',
        importance: 'CRITICAL',
        nominalPowerKw: 3.5,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#e11d48',
        meshType: 'box',
        realWorldContext: 'Long-range high-frequency radio and satellite telemetry bridge'
      },
      {
        id: 'mt_obj_lake_pump',
        name: 'Priyadarshini Lake Water Intake',
        category: 'CRITICAL_LOAD',
        zone: 'mt_main_level',
        position: [28, 1.0, -12],
        dimensions: [4, 2.0, 3],
        elevation: 1.0,
        deviceId: 'mt_lake_water_pump',
        circuitId: 'c_mt_lake_water_pump',
        importance: 'CRITICAL',
        nominalPowerKw: 7.2,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#e11d48',
        meshType: 'box',
        realWorldContext: 'Submersible water pump located at Priyadarshini Lake with 24/7 electric heat tracing'
      },
      {
        id: 'mt_obj_hab_heat',
        name: 'Block A Living Quarters Heating',
        category: 'HABITATION',
        zone: 'mt_main_level',
        position: [16, 2.3, 4],
        dimensions: [6, 2.4, 4],
        elevation: 2.3,
        deviceId: 'mt_living_quarters_heat',
        circuitId: 'c_mt_living_quarters_heat',
        importance: 'IMPORTANT',
        nominalPowerKw: 11.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#10b981',
        meshType: 'box',
        realWorldContext: 'Habitat climate radiator fan coils and lighting across crew living rooms'
      },
      {
        id: 'mt_obj_galley_freeze',
        name: 'Galley & Cold Storage Refrigerator',
        category: 'HABITATION',
        zone: 'mt_main_level',
        position: [12, 2.3, -2],
        dimensions: [3.5, 2.2, 3],
        elevation: 2.3,
        deviceId: 'mt_galley_freeze',
        circuitId: 'c_mt_galley_freeze',
        importance: 'IMPORTANT',
        nominalPowerKw: 4.8,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#10b981',
        meshType: 'box',
        realWorldContext: 'Crew mess kitchen cooking ovens and deep-freeze preservation units'
      },
      {
        id: 'mt_obj_brewer',
        name: 'Brewer Ozone Spectrophotometer',
        category: 'SCIENCE',
        zone: 'mt_ground',
        position: [24, 1.2, 14],
        dimensions: [2.5, 2.0, 2.5],
        elevation: 1.2,
        deviceId: 'mt_brewer_spectrometer',
        circuitId: 'c_mt_brewer_spectrometer',
        importance: 'OPERATIONAL',
        nominalPowerKw: 2.2,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#8b5cf6',
        meshType: 'box',
        realWorldContext: 'Automated spectrophotometer tracking the Antarctic stratospheric ozone hole'
      },
      {
        id: 'mt_obj_geomag',
        name: 'Geomagnetic & Seismic Sensor Array',
        category: 'SCIENCE',
        zone: 'mt_ground',
        position: [32, 1.0, 16],
        dimensions: [3.0, 1.8, 3.0],
        elevation: 1.0,
        deviceId: 'mt_geomag_sensor',
        circuitId: 'c_mt_geomag_sensor',
        importance: 'OPERATIONAL',
        nominalPowerKw: 3.1,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#8b5cf6',
        meshType: 'box',
        realWorldContext: 'Non-magnetic hut housing fluxgate magnetometers and broadband seismometers'
      },
      {
        id: 'mt_obj_workshop',
        name: 'Workshop Tools & Machinery',
        category: 'FLEXIBLE_LOAD',
        zone: 'mt_main_level',
        position: [6, 2.3, 10],
        dimensions: [4, 2.2, 3.5],
        elevation: 2.3,
        deviceId: 'mt_workshop_tools',
        circuitId: 'c_mt_workshop_tools',
        importance: 'FLEXIBLE',
        nominalPowerKw: 5.5,
        status: 'STANDBY',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#f59e0b',
        meshType: 'box',
        realWorldContext: 'Lathe, drill presses, welding equipment, and skidoo engine heaters'
      }
    ],
    powerFlowPaths: [
      { id: 'mt_flow_solar', name: 'Solar PV Feed', fromId: 'mt_obj_solar', toId: 'mt_obj_main_bus', circuitId: 'c_gen_solar', type: 'SOURCE_FEED', points: [[-24, 0.5, -18], [-12, 1.5, -6], [-6, 2.5, 0]], defaultActive: true, nominalKw: 18.0 },
      { id: 'mt_flow_wind', name: 'Wind Turbine Feed', fromId: 'mt_obj_wind', toId: 'mt_obj_main_bus', circuitId: 'c_gen_wind', type: 'SOURCE_FEED', points: [[-26, 6.0, 14], [-12, 2.5, 4], [-6, 2.5, 0]], defaultActive: true, nominalKw: 15.0 },
      { id: 'mt_flow_diesel', name: 'Diesel Generator Feed', fromId: 'mt_obj_diesel_house', toId: 'mt_obj_main_bus', circuitId: 'c_gen_diesel', type: 'SOURCE_FEED', points: [[-16, 2.2, -6], [-6, 2.5, 0]], defaultActive: false, nominalKw: 62.5 },
      { id: 'mt_flow_battery', name: 'Battery BESS Feed', fromId: 'mt_obj_battery', toId: 'mt_obj_main_bus', circuitId: 'c_gen_bess', type: 'SOURCE_FEED', points: [[-16, 2.2, 4], [-6, 2.5, 0]], defaultActive: false, nominalKw: 40.0 },
      { id: 'mt_flow_feeder_thermal', name: 'Feeder F1 (Thermal)', fromId: 'mt_obj_main_bus', toId: 'mt_obj_panel_thermal', circuitId: 'c_feeder_thermal', type: 'FEEDER', points: [[-6, 2.5, 0], [2, 2.2, -6]], defaultActive: true, nominalKw: 55.0 },
      { id: 'mt_flow_feeder_hab', name: 'Feeder F2 (Habitation)', fromId: 'mt_obj_main_bus', toId: 'mt_obj_panel_hab', circuitId: 'c_feeder_hab', type: 'FEEDER', points: [[-6, 2.5, 0], [6, 2.2, 0], [12, 2.2, 2]], defaultActive: true, nominalKw: 40.0 },
      { id: 'mt_flow_feeder_water', name: 'Feeder F3 (Water Plant)', fromId: 'mt_obj_main_bus', toId: 'mt_obj_panel_water', circuitId: 'c_feeder_water', type: 'FEEDER', points: [[-6, 2.5, 0], [14, 2.2, -4], [22, 2.2, -4]], defaultActive: true, nominalKw: 25.0 }
    ]
  },

  // ===========================================================================
  // 3. HIMADRI RESEARCH STATION (Ny-Ålesund, Spitsbergen, Svalbard)
  // Two-storey Arctic building with external settlement power connection
  // ===========================================================================
  HIMADRI: {
    stationId: 'HIMADRI',
    name: 'Himadri Arctic Research Station',
    location: 'Ny-Ålesund, Spitsbergen, Svalbard (78°55′N, 11°56′E)',
    architectureDescription: 'Two-storey wooden and composite Arctic laboratory station operating inside the Ny-Ålesund international research settlement.',
    geometryBasis: 'CONFIGURED / REPRESENTATIVE',
    elevationM: 15,
    terrainType: 'ARCTIC_TUNDRA',
    groundColor: '#94a3b8',
    decks: [
      {
        id: 'hm_ground_deck',
        name: 'Ground Level & Wet Labs (0.0m - 3.2m)',
        elevation: 0.0,
        bounds: { minX: -16, maxX: 16, minZ: -12, maxZ: 12 },
        color: '#e2e8f0',
        opacity: 0.45,
        description: 'Analytical labs, sample refrigeration, incubators, marine biology equipment, main switchgear'
      },
      {
        id: 'hm_upper_deck',
        name: 'Upper Habitation & Comms Floor (+3.5m)',
        elevation: 3.5,
        bounds: { minX: -15, maxX: 15, minZ: -11, maxZ: 11 },
        color: '#f8fafc',
        opacity: 0.55,
        description: 'Crew sleeping berths, telecommunications office, data gateway, and optical instruments'
      }
    ],
    objects: [
      // --- SOURCES & STORAGE ---
      {
        id: 'hm_obj_solar',
        name: 'Solar PV Array (12 kWp - Polar Day)',
        category: 'SOURCE',
        zone: 'hm_ground_deck',
        position: [-18, 0.5, -8],
        dimensions: [8, 1.0, 5],
        elevation: 0.5,
        deviceId: 'solar_pv_array',
        circuitId: 'c_gen_solar',
        importance: 'OPERATIONAL',
        nominalPowerKw: 12.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#f59e0b',
        meshType: 'box',
        realWorldContext: 'Rooftop and ground solar panels taking advantage of 24h Arctic summer polar day'
      },
      {
        id: 'hm_obj_district_grid',
        name: 'Settlement Grid / Diesel Feed (50 kW)',
        category: 'SOURCE',
        zone: 'hm_ground_deck',
        position: [-16, 1.5, 4],
        dimensions: [3, 2.2, 2],
        elevation: 1.5,
        deviceId: 'diesel_generator_1',
        circuitId: 'c_gen_diesel',
        importance: 'CRITICAL',
        nominalPowerKw: 50.0,
        status: 'STANDBY',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#b45309',
        meshType: 'box',
        realWorldContext: 'Interconnection terminal to Ny-Ålesund centralized microgrid with local backup generator'
      },
      {
        id: 'hm_obj_battery',
        name: 'Station BESS Buffer (60 kWh)',
        category: 'STORAGE',
        zone: 'hm_ground_deck',
        position: [-10, 1.2, 4],
        dimensions: [3, 2.0, 2],
        elevation: 1.2,
        deviceId: 'bess_bank_1',
        circuitId: 'c_gen_bess',
        importance: 'CRITICAL',
        nominalPowerKw: 25.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#059669',
        meshType: 'box',
        realWorldContext: 'Indoor lithium-ion rack with clean power conditioning for sensitive instruments'
      },
      // --- ELECTRICAL DISTRIBUTION ---
      {
        id: 'hm_obj_main_bus',
        name: 'Himadri Main 400V Switchboard',
        category: 'BUS',
        zone: 'hm_ground_deck',
        position: [-4, 1.5, 0],
        dimensions: [2.5, 2.2, 1.0],
        elevation: 1.5,
        circuitId: 'c_main_bus',
        importance: 'CRITICAL',
        nominalPowerKw: 100.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#0284c7',
        meshType: 'bus',
        realWorldContext: 'Primary distribution board with surge protection for scientific telemetry'
      },
      {
        id: 'hm_obj_panel_lab',
        name: 'Ground Floor Science Panel (DB-1)',
        category: 'PANEL',
        zone: 'hm_ground_deck',
        position: [2, 1.2, -4],
        dimensions: [1.2, 1.8, 0.6],
        elevation: 1.2,
        circuitId: 'c_feeder_lab',
        importance: 'CRITICAL',
        nominalPowerKw: 35.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Laboratories, sample deep-freezers, and environmental heaters'
      },
      {
        id: 'hm_obj_panel_upper',
        name: 'Upper Habitation & Comms Panel (DB-2)',
        category: 'PANEL',
        zone: 'hm_upper_deck',
        position: [2, 4.2, 2],
        dimensions: [1.2, 1.8, 0.6],
        elevation: 4.2,
        circuitId: 'c_feeder_upper',
        importance: 'IMPORTANT',
        nominalPowerKw: 25.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#64748b',
        meshType: 'box',
        realWorldContext: 'Crew accommodation, telemetry servers, and satellite link'
      },
      // --- OPERATIONAL LOADS ---
      {
        id: 'hm_obj_env_heat',
        name: 'Environmental Life-Support Heating',
        category: 'CRITICAL_LOAD',
        zone: 'hm_ground_deck',
        position: [8, 1.4, -4],
        dimensions: [3, 2.0, 2],
        elevation: 1.4,
        deviceId: 'hm_environmental_heat',
        circuitId: 'c_hm_environmental_heat',
        importance: 'CRITICAL',
        nominalPowerKw: 14.5,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#e11d48',
        meshType: 'box',
        realWorldContext: 'District heating heat exchanger and backup electric resistance blowers'
      },
      {
        id: 'hm_obj_incubators',
        name: 'Incubators & Sample Centrifuges',
        category: 'SCIENCE',
        zone: 'hm_ground_deck',
        position: [12, 1.2, -2],
        dimensions: [2.5, 1.8, 2],
        elevation: 1.2,
        deviceId: 'hm_lab_incubators',
        circuitId: 'c_hm_lab_incubators',
        importance: 'IMPORTANT',
        nominalPowerKw: 4.2,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#8b5cf6',
        meshType: 'box',
        realWorldContext: 'Refrigerated centrifuges, thermal cyclers, and microbial incubators'
      },
      {
        id: 'hm_obj_ult_freezer',
        name: 'Ultra-Low Temp (-80°C) Bio-Freezer',
        category: 'CRITICAL_LOAD',
        zone: 'hm_ground_deck',
        position: [12, 1.2, 4],
        dimensions: [2.0, 2.0, 1.8],
        elevation: 1.2,
        deviceId: 'hm_ult_freezer',
        circuitId: 'c_hm_ult_freezer',
        importance: 'CRITICAL',
        nominalPowerKw: 3.2,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#e11d48',
        meshType: 'box',
        realWorldContext: 'Critical scientific tissue and DNA sample archive requiring uninterruptible power'
      },
      {
        id: 'hm_obj_lidar',
        name: 'Atmospheric Aerosol LIDAR Platform',
        category: 'SCIENCE',
        zone: 'hm_upper_deck',
        position: [6, 4.4, -4],
        dimensions: [2.5, 2.0, 2],
        elevation: 4.4,
        deviceId: 'hm_atmospheric_lidar',
        circuitId: 'c_hm_atmospheric_lidar',
        importance: 'OPERATIONAL',
        nominalPowerKw: 4.8,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#8b5cf6',
        meshType: 'box',
        realWorldContext: 'Optical laser radar monitoring polar stratospheric clouds and black carbon'
      },
      {
        id: 'hm_obj_telemetry_gw',
        name: 'High Arctic Telemetry & Sat Gateway',
        category: 'COMMUNICATION',
        zone: 'hm_upper_deck',
        position: [-6, 4.4, 2],
        dimensions: [2.0, 2.0, 1.5],
        elevation: 4.4,
        deviceId: 'hm_telemetry_gw',
        circuitId: 'c_hm_telemetry_gw',
        importance: 'CRITICAL',
        nominalPowerKw: 2.8,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#e11d48',
        meshType: 'box',
        realWorldContext: 'Fiber optic settlement ring link and backup Inmarsat BGAN satellite terminal'
      },
      {
        id: 'hm_obj_hab_hvac',
        name: 'Upper Living Berths HVAC & Light',
        category: 'HABITATION',
        zone: 'hm_upper_deck',
        position: [8, 4.4, 3],
        dimensions: [5.0, 2.2, 3],
        elevation: 4.4,
        deviceId: 'hm_living_quarters_hvac',
        circuitId: 'c_hm_living_quarters_hvac',
        importance: 'IMPORTANT',
        nominalPowerKw: 6.0,
        status: 'ONLINE',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#10b981',
        meshType: 'box',
        realWorldContext: 'Thermal ventilation, radiators, and living quarters lighting for 8 researchers'
      },
      {
        id: 'hm_obj_equipment_charge',
        name: 'Field Gear & Snowmobile Charger Dock',
        category: 'FLEXIBLE_LOAD',
        zone: 'hm_ground_deck',
        position: [4, 1.2, 6],
        dimensions: [3.0, 1.8, 2],
        elevation: 1.2,
        deviceId: 'hm_equipment_charge',
        circuitId: 'c_hm_equipment_charge',
        importance: 'FLEXIBLE',
        nominalPowerKw: 4.5,
        status: 'STANDBY',
        provenance: 'CONFIGURED',
        selectable: true,
        color: '#f59e0b',
        meshType: 'box',
        realWorldContext: 'Portable field battery charging and heated camera/drone gear storage'
      }
    ],
    powerFlowPaths: [
      { id: 'hm_flow_solar', name: 'Solar PV Feed', fromId: 'hm_obj_solar', toId: 'hm_obj_main_bus', circuitId: 'c_gen_solar', type: 'SOURCE_FEED', points: [[-18, 0.5, -8], [-8, 1.2, -4], [-4, 1.5, 0]], defaultActive: true, nominalKw: 12.0 },
      { id: 'hm_flow_grid', name: 'Settlement Grid / Diesel Feed', fromId: 'hm_obj_district_grid', toId: 'hm_obj_main_bus', circuitId: 'c_gen_diesel', type: 'SOURCE_FEED', points: [[-16, 1.5, 4], [-4, 1.5, 0]], defaultActive: true, nominalKw: 50.0 },
      { id: 'hm_flow_bess', name: 'BESS Battery Feed', fromId: 'hm_obj_battery', toId: 'hm_obj_main_bus', circuitId: 'c_gen_bess', type: 'SOURCE_FEED', points: [[-10, 1.2, 4], [-4, 1.5, 0]], defaultActive: false, nominalKw: 25.0 },
      { id: 'hm_flow_feeder_lab', name: 'Feeder F1 (Lab & Heating)', fromId: 'hm_obj_main_bus', toId: 'hm_obj_panel_lab', circuitId: 'c_feeder_lab', type: 'FEEDER', points: [[-4, 1.5, 0], [2, 1.2, -4]], defaultActive: true, nominalKw: 35.0 },
      { id: 'hm_flow_feeder_upper', name: 'Feeder F2 (Upper Floor)', fromId: 'hm_obj_main_bus', toId: 'hm_obj_panel_upper', circuitId: 'c_feeder_upper', type: 'FEEDER', points: [[-4, 1.5, 0], [0, 4.2, 2], [2, 4.2, 2]], defaultActive: true, nominalKw: 25.0 }
    ]
  }
};
