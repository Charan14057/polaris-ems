# POLARIS-EMS — SPATIAL DATA MODEL SPECIFICATION
## Phase 18 Schema, Coordinate Systems, and Station Profiles

---

## 1. Spatial Model Philosophy & Epistemic Boundaries

In polar research environments (Larsemann Hills, Schirmacher Oasis, Ny-Ålesund), surveyed CAD blueprints of station interiors are classified, proprietary, or evolving due to seasonal container reconfigurations.

Therefore, Polaris-EMS implements a **representative operational spatial schematic**:
- **Geometry Basis**: Clearly labeled as `REPRESENTATIVE / CONFIGURED` in the UI.
- **Epistemic Truth**: The UI explicitly states `Representative spatial model • Geometry basis: CONFIG_ASSUMED`. No claim is made of a millimeter-surveyed CAD installation.
- **Extensible Configuration**: All spatial layouts are decoupled into `configs/station_spatial_profiles.json` and mirrored in `frontend/src/features/twin/model/spatialProfiles.ts`. Surveyed geometric drawings can be dropped in at any future point without modifying the SVG rendering engine.

---

## 2. Spatial Data Model Interfaces

The spatial model adheres strictly to the configuration schema specified in Phase 18:

```ts
export interface TwinSpatialProfile {
  stationId: 'BHARATI' | 'MAITRI' | 'HIMADRI';
  version: string;
  layoutStatus: 'REPRESENTATIVE' | 'CONFIGURED';
  geometryBasis: string;
  width: number;
  height: number;
  zones: TwinZone[];
  nodes: TwinSpatialNode[];
  edges: TwinFlowEdge[];
}

export interface TwinZone {
  id: string;
  name: string;
  label: string;
  category: 
    | 'POWER' 
    | 'OPERATIONS' 
    | 'SCIENCE' 
    | 'MECHANICAL' 
    | 'HABITATION' 
    | 'STORAGE' 
    | 'COMMUNICATIONS';
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface TwinSpatialNode {
  id: string;
  kind: 'SOURCE' | 'BUS' | 'STORAGE' | 'LOAD' | 'THERMAL' | 'DEVICE';
  label: string;
  zoneId?: string;
  deviceId?: string;
  circuitId?: string;
  position: { x: number; y: number };
  iconKey?: string;
  selectable: boolean;
}

export interface TwinFlowEdge {
  id: string;
  fromNodeId: string;
  toNodeId: string;
  circuitId?: string;
  geometry: 
    | { type: 'polyline'; points: Array<{ x: number; y: number }> }
    | { type: 'path'; d: string };
  direction: 'FORWARD' | 'REVERSE' | 'NONE';
  powerKw: number;
  sourceMix: {
    solarKw: number;
    windKw: number;
    dieselKw: number;
    batteryKw: number;
  };
  active: boolean;
}
```

---

## 3. Station Layout Profiles

### 1. Bharati Antarctic Research Station (`BHARATI`)
- **Dimensions**: 1000 × 640 drafting units
- **Zones (6)**:
  - `z_generation`: Power & Generation Bay (Solar 30 kWp, Wind 25 kW, Diesel 3x80 kW, BESS 120 kWh)
  - `z_operations`: Mission Operations & Comms (Satcom Uplink, Data Servers)
  - `z_science`: Environmental Science Labs (Core Lab, Waste Aux)
  - `z_utilities`: Life Support & Water Plant (Habitat Life Support, Water Freeze Protection, Snow Melter)
  - `z_habitation`: Living Quarters & Galley (Residential Lighting, Galley Cold Storage)
  - `z_workshop`: Maintenance & EV Charging Bay (Vehicle Charging Skidoos)
- **Distribution**: Central Main 400V AC Switchboard (`node_main_bus`) feeding 5 Sub-DB panels (`DB-1` to `DB-5`).

### 2. Maitri Antarctic Station (`MAITRI`)
- **Dimensions**: 1000 × 640 drafting units
- **Zones (6)**:
  - `z_mt_gen`: Diesel Power House & Fuel Vault (Diesel Gensets 3x62.5 kW, Wind 15 kW, Solar 18 kWp, BESS 90 kWh)
  - `z_mt_comms`: Comms & Weather Station (HF/VHF Satcom, AWS Meteorology Logging)
  - `z_mt_sci`: Geomagnetism Observatory (Geomagnetic & Seismic Instrumentation)
  - `z_mt_thermal`: Central Boiler & Heating Loop (Primary Boiler Loop, Aux Circ Pumps)
  - `z_mt_hab`: Crew Living Block & Galley (Kitchen Utilities, Habitat Heaters)
  - `z_mt_water`: Priyadarshini Lake Water Plant (Priyadarshini Lake Pump, Snow Melter, Workshop)
- **Distribution**: Maitri 400V AC Switchboard (`node_mt_main_bus`) feeding 5 localized Sub-DB panels.

### 3. Himadri Arctic Research Station (`HIMADRI`)
- **Dimensions**: 1000 × 640 drafting units
- **Zones (5)**:
  - `z_hm_gen`: Micro-Gen & Battery Vault (Solar 12 kWp, Wind 10 kW, Diesel 2x45 kW, BESS 50 kWh)
  - `z_hm_sci`: Atmospheric Aerosol Lab (Aerosol Spectrometer, Optical Sensors)
  - `z_hm_comms`: Ny-Ålesund Satellite Link (Telecom & Radar Uplink)
  - `z_hm_hab`: Living Quarters & Climate HVAC (Clean Room HVAC, Crew Habitat Heaters)
  - `z_hm_expedition`: Glaciology & Field Staging (Glaciology Radar, Field Gear Dryer)
- **Distribution**: Himadri 400V Microgrid Bus (`node_hm_main_bus`) feeding 2 localized distribution sub-buses.
