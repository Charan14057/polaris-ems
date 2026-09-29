/**
 * POLARIS-EMS — Station 3D Architectural & Industrial Asset Mesh Builders
 * Phase 18: Operational 3D Digital Twin Engine (Visual Fidelity V2)
 * 
 * Provides reference-aligned procedural 3D models for:
 * 1. BHARATI (Elevated aerodynamic multi-deck station on structural stilts with bof-architekten profile)
 * 2. MAITRI (Modular living blocks linked by central heated spine corridor on elevated grillage)
 * 3. HIMADRI (Nordic 2-storey high-Arctic research facility in Ny-Ålesund, Svalbard with pitched roof)
 * 
 * Includes high-fidelity industrial engineering assets:
 * - Containerized BESS with HVAC chillers & DC disconnect
 * - Heavy acoustic enclosure Diesel Gensets with exhaust silencers & day tanks
 * - Main 415V Station Switchgear Bus Hub with cable trays & mimic panels
 * - Tilted solar PV racks with string inverters
 * - Aerodynamic polar wind turbines with aviation beacons
 * - Polar terrain with wind-carved sastrugi, ice sheen, crawler tracks, and helipad.
 */

import * as THREE from 'three';
import {
  createInsulatedCladdingMaterial,
  createStructuralSteelMaterial,
  createGalvanizedLegMaterial,
  createPhotovoltaicMaterial,
  createConcreteFoundationMaterial,
  createIndustrialGlassMaterial,
  createPolarCompositeMaterial,
  createPolarSnowMaterial,
  createBedrockMaterial,
  getDiamondPlateTexture,
  getCorrugatedTexture
} from './pbrMaterialFactory';

export interface StationMeshResult {
  architectureGroup: THREE.Group;
  terrainMesh: THREE.Object3D;
  interactiveMeshes: Map<string, THREE.Object3D>;
  turbines: { rotorGroup: THREE.Group; speedMultiplier: number }[];
  statusIndicators?: { mesh: THREE.Mesh; type: 'DG' | 'BESS' | 'WIND' | 'SOLAR' | 'BUS'; id: string }[];
}

// =============================================================================
// REUSABLE INDUSTRIAL ASSET BUILDERS
// =============================================================================

/**
 * Creates a photorealistic solar PV array rack with tilted solar panels,
 * extruded aluminum frame rails, string inverter enclosure, and galvanized pile legs.
 */
export function createSolarRack(
  width: number, 
  depth: number, 
  tiltAngleDeg: number = 40,
  wireframe: boolean = false
): THREE.Group {
  const rack = new THREE.Group();
  const tiltRad = (tiltAngleDeg * Math.PI) / 180;

  // 1. Tilted Photovoltaic Panel Surface with realistic solar cell grid map
  const panelGeo = new THREE.BoxGeometry(width, 0.08, depth);
  const panelMat = createPhotovoltaicMaterial({ wireframe });
  const panel = new THREE.Mesh(panelGeo, panelMat);
  panel.rotation.x = tiltRad;
  panel.position.y = (depth / 2) * Math.sin(tiltRad) + 0.6;
  panel.castShadow = true;
  panel.receiveShadow = true;
  rack.add(panel);

  // 2. Anodized Aluminum Panel Mounting Rails & Frame Edge
  const frameMat = createStructuralSteelMaterial(0x94a3b8, { wireframe });
  const railGeo = new THREE.BoxGeometry(width + 0.1, 0.06, 0.1);
  
  // Upper & Lower framing rails
  const topRail = new THREE.Mesh(railGeo, frameMat);
  topRail.position.set(0, (depth / 2) * Math.sin(tiltRad) + 0.6 + (depth / 2) * Math.sin(tiltRad), -(depth / 2) * Math.cos(tiltRad));
  topRail.rotation.x = tiltRad;
  rack.add(topRail);

  const bottomRail = new THREE.Mesh(railGeo, frameMat);
  bottomRail.position.set(0, 0.6, (depth / 2) * Math.cos(tiltRad));
  bottomRail.rotation.x = tiltRad;
  rack.add(bottomRail);

  // 3. Galvanized Steel Pile Support Legs with Ground Footing Pads
  const legMat = createGalvanizedLegMaterial({ wireframe });
  const footingMat = createConcreteFoundationMaterial({ wireframe });

  const numLegPairs = Math.max(2, Math.floor(width / 4));
  for (let i = 0; i < numLegPairs; i++) {
    const xPos = -width / 2 + (width / (numLegPairs - 1)) * i;

    // Rear tall leg
    const rearHeight = depth * Math.sin(tiltRad) + 0.6;
    const rearLeg = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, rearHeight, 8), legMat);
    rearLeg.position.set(xPos, rearHeight / 2, -(depth / 2) * Math.cos(tiltRad));
    rearLeg.castShadow = true;
    rack.add(rearLeg);

    // Front short leg
    const frontLeg = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.6, 8), legMat);
    frontLeg.position.set(xPos, 0.3, (depth / 2) * Math.cos(tiltRad));
    frontLeg.castShadow = true;
    rack.add(frontLeg);

    // Concrete ballast footing blocks
    const foot1 = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.25, 0.5), footingMat);
    foot1.position.set(xPos, 0.12, -(depth / 2) * Math.cos(tiltRad));
    foot1.receiveShadow = true;
    rack.add(foot1);

    const foot2 = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.25, 0.5), footingMat);
    foot2.position.set(xPos, 0.12, (depth / 2) * Math.cos(tiltRad));
    foot2.receiveShadow = true;
    rack.add(foot2);

    // Diagonal bracing member between front and rear leg
    const braceLen = Math.sqrt(rearHeight * rearHeight + (depth * Math.cos(tiltRad)) ** 2) * 0.8;
    const brace = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, braceLen, 6), legMat);
    brace.position.set(xPos, rearHeight / 2, 0);
    brace.rotation.x = Math.atan2(depth * Math.cos(tiltRad), rearHeight);
    rack.add(brace);
  }

  // 4. Integrated Industrial String Inverter Cabinet mounted behind array
  const invGroup = new THREE.Group();
  invGroup.position.set(width / 4, 1.2, -(depth / 2) * Math.cos(tiltRad) - 0.3);

  const invBox = new THREE.Mesh(
    new THREE.BoxGeometry(0.8, 1.0, 0.4),
    createStructuralSteelMaterial(0x334155, { wireframe })
  );
  invBox.castShadow = true;
  invGroup.add(invBox);

  // Inverter cooling heat sink fins on back
  const finMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.9, roughness: 0.3 });
  for (let f = -0.3; f <= 0.3; f += 0.08) {
    const fin = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.85, 0.08), finMat);
    fin.position.set(f, 0, -0.22);
    invGroup.add(fin);
  }

  // AC/DC Rotary Isolation Switch
  const switchGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.08, 12);
  const switchMesh = new THREE.Mesh(switchGeo, new THREE.MeshStandardMaterial({ color: 0xef4444, metalness: 0.4 }));
  switchMesh.rotation.x = Math.PI / 2;
  switchMesh.position.set(0.25, 0.2, 0.22);
  invGroup.add(switchMesh);

  // Inverter operational status LED (Green = Online, Amber = Standby/Fault)
  const ledGeo = new THREE.SphereGeometry(0.04, 8, 8);
  const ledMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
  const led = new THREE.Mesh(ledGeo, ledMat);
  led.position.set(-0.25, 0.35, 0.21);
  invGroup.add(led);

  rack.add(invGroup);
  return rack;
}

/**
 * Creates an aerodynamic Antarctic wind turbine with tapered mast,
 * teardrop nacelle, rotor hub, 3-blade prop assembly, and 1 Hz aviation beacon.
 */
export function createWindTurbine(
  towerHeight: number,
  rotorDiameter: number,
  wireframe: boolean = false
): { group: THREE.Group; rotor: THREE.Group; beacon: THREE.Mesh } {
  const group = new THREE.Group();

  // 1. Heavy Reinforced Concrete Foundation Pedestal
  const footingMat = createConcreteFoundationMaterial({ wireframe });
  const footing = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 2.0, 0.6, 12), footingMat);
  footing.position.y = 0.3;
  footing.receiveShadow = true;
  group.add(footing);

  // 2. Tapered Flanged Tubular Steel Tower (polar off-white)
  const towerGeo = new THREE.CylinderGeometry(0.4, 0.85, towerHeight, 20);
  const towerMat = new THREE.MeshStandardMaterial({
    color: 0xf1f5f9,
    metalness: 0.35,
    roughness: 0.3,
    wireframe
  });
  const tower = new THREE.Mesh(towerGeo, towerMat);
  tower.position.y = towerHeight / 2 + 0.6;
  tower.castShadow = true;
  tower.receiveShadow = true;
  group.add(tower);

  // Horizontal Flanged Ring Joints (structural realism)
  const ringMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.7, roughness: 0.4 });
  [0.3, 0.6, 0.9].forEach(frac => {
    const ry = 0.6 + towerHeight * frac;
    const rRadius = 0.85 - (0.85 - 0.4) * frac + 0.03;
    const ring = new THREE.Mesh(new THREE.CylinderGeometry(rRadius, rRadius, 0.1, 20), ringMat);
    ring.position.y = ry;
    group.add(ring);
  });

  // Base Maintenance Door & High-Visibility Yellow Safety Ring
  const bandGeo = new THREE.CylinderGeometry(0.86, 0.86, 1.4, 20);
  const bandMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.45, metalness: 0.3 });
  const band = new THREE.Mesh(bandGeo, bandMat);
  band.position.y = 1.3;
  group.add(band);

  const doorMesh = new THREE.Mesh(
    new THREE.BoxGeometry(0.3, 1.0, 0.1),
    new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.6 })
  );
  doorMesh.position.set(0, 1.3, 0.86);
  group.add(doorMesh);

  // 3. Aerodynamic Nacelle & Machine Bed
  const nacelleMat = new THREE.MeshStandardMaterial({
    color: 0xf8fafc,
    metalness: 0.35,
    roughness: 0.28,
    wireframe
  });
  const nacelleGroup = new THREE.Group();
  nacelleGroup.position.set(0, towerHeight + 0.6 + 0.6, 0.3);

  // Nacelle main housing (streamlined shape)
  const nacelleGeo = new THREE.BoxGeometry(1.4, 1.2, 2.8);
  const nacelle = new THREE.Mesh(nacelleGeo, nacelleMat);
  nacelle.castShadow = true;
  nacelleGroup.add(nacelle);

  // Nacelle cooling radiator grille at rear
  const grillGeo = new THREE.PlaneGeometry(1.0, 0.8);
  const grillMat = new THREE.MeshBasicMaterial({ color: 0x1e293b, wireframe: true });
  const grill = new THREE.Mesh(grillGeo, grillMat);
  grill.position.set(0, 0, -1.41);
  grill.rotation.y = Math.PI;
  nacelleGroup.add(grill);

  // Anemometer & Wind Vane Sensor Mast on Nacelle Roof
  const sensorMast = new THREE.Mesh(
    new THREE.CylinderGeometry(0.04, 0.04, 0.9, 8),
    createStructuralSteelMaterial(0x334155)
  );
  sensorMast.position.set(0, 1.0, -0.8);
  nacelleGroup.add(sensorMast);

  // Red Pulsing Aviation Obstruction Warning Light (1 Hz pulse)
  const beaconGeo = new THREE.SphereGeometry(0.12, 8, 8);
  const beaconMat = new THREE.MeshBasicMaterial({ color: 0xef4444 });
  const beacon = new THREE.Mesh(beaconGeo, beaconMat);
  beacon.position.set(0, 1.45, -0.8);
  nacelleGroup.add(beacon);

  group.add(nacelleGroup);

  // 4. Rotor Hub Spinner with Blade Pitch Bearings
  const rotor = new THREE.Group();
  rotor.position.set(0, towerHeight + 1.2, 1.75);

  const hubGeo = new THREE.ConeGeometry(0.55, 1.0, 20);
  hubGeo.rotateX(Math.PI / 2);
  const hubMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.25, metalness: 0.4 });
  const hub = new THREE.Mesh(hubGeo, hubMat);
  hub.castShadow = true;
  rotor.add(hub);

  // 5. Three Aerodynamic Twisted Rotor Blades with Red Warning Tips
  const bladeLength = rotorDiameter / 2;
  const bladeMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.22, metalness: 0.2 });
  const tipMat = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.3 }); // Red safety tip

  for (let i = 0; i < 3; i++) {
    const bladeAngle = (i * Math.PI * 2) / 3;
    const bladeGroup = new THREE.Group();
    bladeGroup.rotation.z = bladeAngle;

    // Pitch bearing collar at root
    const collar = new THREE.Mesh(
      new THREE.CylinderGeometry(0.16, 0.16, 0.3, 12),
      createStructuralSteelMaterial(0x475569)
    );
    collar.position.y = 0.4;
    bladeGroup.add(collar);

    // Main aerodynamic airfoil blade
    const bladeGeo = new THREE.BoxGeometry(0.26, bladeLength * 0.78, 0.08);
    const bladeMesh = new THREE.Mesh(bladeGeo, bladeMat);
    bladeMesh.position.y = bladeLength * 0.42 + 0.4;
    bladeMesh.rotation.y = 0.18; // Aerodynamic pitch angle
    bladeMesh.castShadow = true;
    bladeGroup.add(bladeMesh);

    // Red high-visibility tip
    const tipGeo = new THREE.BoxGeometry(0.24, bladeLength * 0.22, 0.07);
    const tipMesh = new THREE.Mesh(tipGeo, tipMat);
    tipMesh.position.y = bladeLength * 0.9 + 0.4;
    tipMesh.rotation.y = 0.18;
    bladeGroup.add(tipMesh);

    rotor.add(bladeGroup);
  }

  group.add(rotor);
  return { group, rotor, beacon };
}

/**
 * Creates an industrial containerized Battery Energy Storage System (BESS)
 * with corrugated walls, exterior HVAC chillers, DC disconnect cabinet, and status beacon.
 */
export function createBessContainer(
  width: number = 6.0,
  height: number = 2.6,
  depth: number = 2.4,
  wireframe: boolean = false
): { group: THREE.Group; statusLed: THREE.Mesh } {
  const group = new THREE.Group();

  // 1. Concrete Pier Pedestals (Elevates BESS above snow accumulation)
  const pierMat = createConcreteFoundationMaterial({ wireframe });
  [-width / 2 + 0.6, width / 2 - 0.6].forEach(x => {
    [-depth / 2 + 0.4, depth / 2 - 0.4].forEach(z => {
      const pier = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.5, 0.8), pierMat);
      pier.position.set(x, 0.25, z);
      pier.receiveShadow = true;
      group.add(pier);
    });
  });

  // 2. ISO Container Main Body with Corrugated Insulated Cladding (Emerald Green / Industrial Grey)
  const containerMat = createInsulatedCladdingMaterial(0x047857, { wireframe }); // Deep industrial BESS emerald
  const bodyGeo = new THREE.BoxGeometry(width, height, depth);
  const body = new THREE.Mesh(bodyGeo, containerMat);
  body.position.y = height / 2 + 0.5;
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  // 3. Structural Steel Corner Post Castings
  const cornerMat = createStructuralSteelMaterial(0x1e293b, { wireframe });
  const cornerGeo = new THREE.BoxGeometry(0.18, height + 0.05, 0.18);
  [-width / 2, width / 2].forEach(cx => {
    [-depth / 2, depth / 2].forEach(cz => {
      const cPost = new THREE.Mesh(cornerGeo, cornerMat);
      cPost.position.set(cx, height / 2 + 0.5, cz);
      group.add(cPost);
    });
  });

  // 4. Exterior HVAC Thermal Management Chiller Units (Mounted on end bulkhead)
  const hvacGroup = new THREE.Group();
  hvacGroup.position.set(-width / 2 - 0.35, height / 2 + 0.5, 0);

  const hvacHousing = new THREE.Mesh(
    new THREE.BoxGeometry(0.7, 1.6, 1.8),
    createStructuralSteelMaterial(0x334155, { wireframe })
  );
  hvacHousing.castShadow = true;
  hvacGroup.add(hvacHousing);

  // Dual axial cooling fans
  const fanMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.3 });
  [-0.45, 0.45].forEach(fz => {
    const fanCowl = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.15, 16), fanMat);
    fanCowl.rotation.z = Math.PI / 2;
    fanCowl.position.set(-0.35, 0.2, fz);
    hvacGroup.add(fanCowl);

    // Protective wire mesh
    const cowlGrill = new THREE.Mesh(new THREE.CircleGeometry(0.3, 8), new THREE.MeshBasicMaterial({ color: 0x94a3b8, wireframe: true }));
    cowlGrill.rotation.y = -Math.PI / 2;
    cowlGrill.position.set(-0.43, 0.2, fz);
    hvacGroup.add(cowlGrill);
  });
  group.add(hvacGroup);

  // 5. High-Voltage DC Disconnect Cabinet with Handle
  const dcCabinet = new THREE.Mesh(
    new THREE.BoxGeometry(0.9, 1.2, 0.35),
    createStructuralSteelMaterial(0x1e293b, { wireframe })
  );
  dcCabinet.position.set(width / 4, height / 2 + 0.4, depth / 2 + 0.18);
  dcCabinet.castShadow = true;
  group.add(dcCabinet);

  // Rotary disconnect lever (Red handle on yellow warning plate)
  const warnPlate = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.2), new THREE.MeshBasicMaterial({ color: 0xfacc15 }));
  warnPlate.position.set(width / 4, height / 2 + 0.55, depth / 2 + 0.36);
  group.add(warnPlate);

  const lever = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.15, 0.08), new THREE.MeshBasicMaterial({ color: 0xef4444 }));
  lever.position.set(width / 4, height / 2 + 0.55, depth / 2 + 0.4);
  group.add(lever);

  // 6. Hazard Class 9 Placard (Lithium-Ion Energy Storage)
  const hazardSign = new THREE.Mesh(
    new THREE.PlaneGeometry(0.35, 0.35),
    new THREE.MeshBasicMaterial({ color: 0xffffff })
  );
  hazardSign.position.set(-width / 4, height / 2 + 0.6, depth / 2 + 0.01);
  group.add(hazardSign);

  // 7. Real-Time Operational Status Beacon (Breathing Green / Cyan / Amber)
  const beaconGeo = new THREE.SphereGeometry(0.14, 12, 12);
  const beaconMat = new THREE.MeshStandardMaterial({
    color: 0x10b981,
    emissive: 0x10b981,
    emissiveIntensity: 0.95,
    roughness: 0.2
  });
  const statusLed = new THREE.Mesh(beaconGeo, beaconMat);
  statusLed.position.set(width / 2 - 0.4, height + 0.65, depth / 2 - 0.4);
  group.add(statusLed);

  return { group, statusLed };
}

/**
 * Creates an industrial acoustic-enclosure Diesel Generator compound
 * with sound-attenuator louvers, twin exhaust flues, day tank, and radiator bank.
 */
export function createDieselGeneratorUnit(
  width: number = 7.0,
  height: number = 3.0,
  depth: number = 3.2,
  wireframe: boolean = false
): { group: THREE.Group; statusLed: THREE.Mesh; exhaustPipes: THREE.Vector3[] } {
  const group = new THREE.Group();

  // 1. Reinforced Concrete Equipment Pad
  const padMat = createConcreteFoundationMaterial({ wireframe });
  const pad = new THREE.Mesh(new THREE.BoxGeometry(width + 0.8, 0.4, depth + 0.8), padMat);
  pad.position.y = 0.2;
  pad.receiveShadow = true;
  group.add(pad);

  // 2. Heavy-Duty Acoustic Weather Canopy (Industrial Slate / Desert Tan)
  const canopyMat = createInsulatedCladdingMaterial(0x475569, { wireframe });
  const canopyGeo = new THREE.BoxGeometry(width, height, depth);
  const canopy = new THREE.Mesh(canopyGeo, canopyMat);
  canopy.position.y = height / 2 + 0.4;
  canopy.castShadow = true;
  canopy.receiveShadow = true;
  group.add(canopy);

  // 3. Acoustic Air Intake Louvers (Sound attenuator grilles)
  const louverMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8, roughness: 0.4 });
  const louverFront = new THREE.Mesh(new THREE.BoxGeometry(width * 0.45, height * 0.65, 0.05), louverMat);
  louverFront.position.set(-width * 0.2, height / 2 + 0.4, depth / 2 + 0.02);
  group.add(louverFront);

  // 4. Large Engine Radiator Bank & Cooling Discharge Plenums on Front End
  const radMesh = new THREE.Mesh(
    new THREE.BoxGeometry(0.1, height * 0.75, depth * 0.75),
    new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.8 })
  );
  radMesh.position.set(width / 2 + 0.05, height / 2 + 0.4, 0);
  group.add(radMesh);

  // Radiator fan guard mesh
  const fanGuard = new THREE.Mesh(new THREE.CircleGeometry(depth * 0.3, 16), new THREE.MeshBasicMaterial({ color: 0x64748b, wireframe: true }));
  fanGuard.rotation.y = Math.PI / 2;
  fanGuard.position.set(width / 2 + 0.11, height / 2 + 0.4, 0);
  group.add(fanGuard);

  // 5. Dual Stainless Steel Exhaust Silencer Mufflers & Vertical Flues
  const exhaustMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9, roughness: 0.2 });
  const exhaustPipes: THREE.Vector3[] = [];

  [-0.6, 0.6].forEach(zOff => {
    // Horizontal silencer cylinder on roof
    const muffler = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 2.2, 16), exhaustMat);
    muffler.rotation.z = Math.PI / 2;
    muffler.position.set(-width * 0.2, height + 0.75, zOff);
    muffler.castShadow = true;
    group.add(muffler);

    // Vertical flue pipe rising above roof
    const flue = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 1.8, 12), exhaustMat);
    flue.position.set(-width * 0.2 - 0.9, height + 1.6, zOff);
    flue.castShadow = true;
    group.add(flue);

    // Counterbalanced Rain Cap Flap
    const cap = new THREE.Mesh(new THREE.ConeGeometry(0.28, 0.18, 12), exhaustMat);
    cap.position.set(-width * 0.2 - 0.9, height + 2.55, zOff);
    group.add(cap);

    exhaustPipes.push(new THREE.Vector3(-width * 0.2 - 0.9, height + 2.55, zOff));
  });

  // 6. Integrated Sub-Base Fuel Day Tank Skid (1,000L)
  const tankMat = new THREE.MeshStandardMaterial({ color: 0xb45309, metalness: 0.4, roughness: 0.5 });
  const fuelSkid = new THREE.Mesh(new THREE.BoxGeometry(width - 0.4, 0.35, depth - 0.4), tankMat);
  fuelSkid.position.y = 0.55;
  group.add(fuelSkid);

  // Fuel level sight gauge & fill port
  const gauge = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.25, 0.05), new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));
  gauge.position.set(-width / 2 + 0.3, 0.55, depth / 2 + 0.01);
  group.add(gauge);

  // 7. Emergency Stop Mushroom Button & Generator Circuit Breaker Panel
  const eStopPanel = new THREE.Mesh(
    new THREE.BoxGeometry(0.8, 1.0, 0.15),
    createStructuralSteelMaterial(0x1e293b)
  );
  eStopPanel.position.set(width * 0.25, height / 2 + 0.4, depth / 2 + 0.08);
  group.add(eStopPanel);

  const eStopBtn = new THREE.Mesh(
    new THREE.CylinderGeometry(0.08, 0.08, 0.06, 12),
    new THREE.MeshBasicMaterial({ color: 0xef4444 })
  );
  eStopBtn.rotation.x = Math.PI / 2;
  eStopBtn.position.set(width * 0.25, height / 2 + 0.6, depth / 2 + 0.18);
  group.add(eStopBtn);

  // 8. Generator Operational Indicator Beacon
  const ledGeo = new THREE.SphereGeometry(0.14, 12, 12);
  const ledMat = new THREE.MeshStandardMaterial({
    color: 0xf59e0b,
    emissive: 0xf59e0b,
    emissiveIntensity: 0.9,
    roughness: 0.2
  });
  const statusLed = new THREE.Mesh(ledGeo, ledMat);
  statusLed.position.set(width / 2 - 0.4, height + 0.55, depth / 2 - 0.4);
  group.add(statusLed);

  return { group, statusLed, exhaustPipes };
}

/**
 * Creates an industrial 415V Main Station Switchgear Bus Hub
 * with glass/polycarbonate mimic inspection window, cable ladder trays, and phase status LEDs.
 */
export function createMainStationBusHub(
  width: number = 4.0,
  height: number = 2.4,
  depth: number = 1.6,
  wireframe: boolean = false
): { group: THREE.Group; busStatusLed: THREE.Mesh } {
  const group = new THREE.Group();

  // 1. Concrete Foundation Plinth
  const plinth = new THREE.Mesh(
    new THREE.BoxGeometry(width + 0.4, 0.25, depth + 0.4),
    createConcreteFoundationMaterial({ wireframe })
  );
  plinth.position.y = 0.12;
  group.add(plinth);

  // 2. Metal-Enclosed Switchgear Cubicles (NEMA / IEC 62271 Tiered Enclosure)
  const enclosureMat = createStructuralSteelMaterial(0x1e293b, { wireframe });
  const cubicle = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), enclosureMat);
  cubicle.position.y = height / 2 + 0.25;
  cubicle.castShadow = true;
  cubicle.receiveShadow = true;
  group.add(cubicle);

  // 3. Clear Polycarbonate Busbar Inspection Window with Copper Mimic Bus
  const windowMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(width * 0.7, height * 0.35),
    createIndustrialGlassMaterial(false, 0.2, { opacity: 0.5 })
  );
  windowMesh.position.set(0, height * 0.7 + 0.25, depth / 2 + 0.01);
  group.add(windowMesh);

  // Heavy Copper Busbar (Visible inside inspection window)
  const copperMat = new THREE.MeshStandardMaterial({ color: 0xd97706, metalness: 0.9, roughness: 0.2 });
  [-0.12, 0, 0.12].forEach(yOff => {
    const busbar = new THREE.Mesh(new THREE.BoxGeometry(width * 0.65, 0.05, 0.04), copperMat);
    busbar.position.set(0, height * 0.7 + 0.25 + yOff, depth / 2 - 0.15);
    group.add(busbar);
  });

  // 4. Three Phase Voltage Indicator LEDs (L1, L2, L3: Red, Yellow, Blue)
  const phaseColors = [0xef4444, 0xfacc15, 0x3b82f6];
  phaseColors.forEach((col, idx) => {
    const pip = new THREE.Mesh(new THREE.SphereGeometry(0.05, 8, 8), new THREE.MeshBasicMaterial({ color: col }));
    pip.position.set(-width * 0.25 + idx * 0.15, height * 0.92 + 0.25, depth / 2 + 0.02);
    group.add(pip);
  });

  // 5. Overhead Galvanized Cable Ladder Trays for incoming/outgoing feeder routing
  const trayMat = createStructuralSteelMaterial(0x94a3b8);
  const trayGeo = new THREE.BoxGeometry(width + 1.2, 0.1, 0.6);
  const cableTray = new THREE.Mesh(trayGeo, trayMat);
  cableTray.position.set(0, height + 0.5, 0);
  group.add(cableTray);

  // 6. Master Bus Status Beacon
  const ledGeo = new THREE.SphereGeometry(0.15, 12, 12);
  const ledMat = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    emissive: 0x38bdf8,
    emissiveIntensity: 0.95,
    roughness: 0.15
  });
  const busStatusLed = new THREE.Mesh(ledGeo, ledMat);
  busStatusLed.position.set(width / 2 - 0.3, height + 0.6, 0);
  group.add(busStatusLed);

  return { group, busStatusLed };
}

/**
 * Creates an industrial oil-cooled Step-Down Substation Transformer
 * with cooling radiator fins, high-voltage ribbed porcelain bushings, and grounding.
 */
export function createIndustrialTransformer(
  width: number = 2.4,
  height: number = 2.0,
  depth: number = 1.8,
  wireframe: boolean = false
): THREE.Group {
  const group = new THREE.Group();

  // Foundation Pad
  const pad = new THREE.Mesh(new THREE.BoxGeometry(width + 0.4, 0.25, depth + 0.4), createConcreteFoundationMaterial({ wireframe }));
  pad.position.y = 0.12;
  group.add(pad);

  // Main Transformer Core Tank
  const tank = new THREE.Mesh(new THREE.BoxGeometry(width, height * 0.7, depth), createStructuralSteelMaterial(0x334155, { wireframe }));
  tank.position.y = (height * 0.7) / 2 + 0.25;
  tank.castShadow = true;
  group.add(tank);

  // Cooling Radiator Fin Banks on sides
  const finMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8, roughness: 0.4 });
  [-depth / 2 - 0.15, depth / 2 + 0.15].forEach(zPos => {
    for (let f = -width / 2 + 0.2; f <= width / 2 - 0.2; f += 0.25) {
      const fin = new THREE.Mesh(new THREE.BoxGeometry(0.04, height * 0.6, 0.25), finMat);
      fin.position.set(f, (height * 0.7) / 2 + 0.25, zPos);
      group.add(fin);
    }
  });

  // Conservator Tank on Top
  const conservator = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, width * 0.7, 12), finMat);
  conservator.rotation.z = Math.PI / 2;
  conservator.position.set(0, height * 0.7 + 0.65, -depth * 0.25);
  group.add(conservator);

  // High-Voltage Ribbed Porcelain Bushings (3 Phase)
  const bushingMat = new THREE.MeshStandardMaterial({ color: 0x78350f, roughness: 0.2, metalness: 0.1 });
  [-0.5, 0, 0.5].forEach(xPos => {
    const bushing = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.45, 8), bushingMat);
    bushing.position.set(xPos, height * 0.7 + 0.45, depth * 0.25);
    group.add(bushing);
  });

  return group;
}

/**
 * Creates an industrial HVAC Heat Recovery & Ventilation Module
 * with twin axial fan cowls and insulated aluminum-jacketed thermal piping.
 */
export function createHvacChillerUnit(
  width: number = 3.2,
  height: number = 1.8,
  depth: number = 1.8,
  wireframe: boolean = false
): THREE.Group {
  const group = new THREE.Group();

  const body = new THREE.Mesh(
    new THREE.BoxGeometry(width, height, depth),
    createStructuralSteelMaterial(0x475569, { wireframe })
  );
  body.position.y = height / 2;
  body.castShadow = true;
  group.add(body);

  // Twin axial ventilation fan cowls on roof
  const fanMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.3 });
  [-width * 0.25, width * 0.25].forEach(xPos => {
    const cowl = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.25, 16), fanMat);
    cowl.position.set(xPos, height + 0.12, 0);
    group.add(cowl);

    const guard = new THREE.Mesh(new THREE.CircleGeometry(0.38, 8), new THREE.MeshBasicMaterial({ color: 0x94a3b8, wireframe: true }));
    guard.rotation.x = -Math.PI / 2;
    guard.position.set(xPos, height + 0.26, 0);
    group.add(guard);
  });

  // Insulated refrigeration lines wrapped in aluminum jacketing
  const pipeMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.85, roughness: 0.25 });
  const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, depth + 0.4, 8), pipeMat);
  pipe.rotation.x = Math.PI / 2;
  pipe.position.set(-width / 2 + 0.2, height * 0.5, 0);
  group.add(pipe);

  return group;
}

/**
 * Creates a double-walled polar diesel fuel storage farm with containment berm,
 * cylindrical tanks on concrete cradles, access stairs, and pipe manifold.
 */
export function createFuelFarm(wireframe: boolean = false): THREE.Group {
  const farm = new THREE.Group();

  // 1. Concrete Containment Berm (Bund Wall)
  const bermWidth = 14;
  const bermDepth = 10;
  const wallHeight = 1.2;
  const wallThick = 0.4;
  const wallMat = createConcreteFoundationMaterial({ wireframe });
  
  // Outer bund walls
  const wallFront = new THREE.Mesh(new THREE.BoxGeometry(bermWidth, wallHeight, wallThick), wallMat);
  wallFront.position.set(0, wallHeight / 2, bermDepth / 2);
  farm.add(wallFront);

  const wallBack = new THREE.Mesh(new THREE.BoxGeometry(bermWidth, wallHeight, wallThick), wallMat);
  wallBack.position.set(0, wallHeight / 2, -bermDepth / 2);
  farm.add(wallBack);

  const wallLeft = new THREE.Mesh(new THREE.BoxGeometry(wallThick, wallHeight, bermDepth), wallMat);
  wallLeft.position.set(-bermWidth / 2, wallHeight / 2, 0);
  farm.add(wallLeft);

  const wallRight = new THREE.Mesh(new THREE.BoxGeometry(wallThick, wallHeight, bermDepth), wallMat);
  wallRight.position.set(bermWidth / 2, wallHeight / 2, 0);
  farm.add(wallRight);

  // Gravel floor inside bund
  const gravelFloor = new THREE.Mesh(
    new THREE.BoxGeometry(bermWidth - 0.2, 0.2, bermDepth - 0.2),
    new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.95 })
  );
  gravelFloor.position.y = 0.1;
  gravelFloor.receiveShadow = true;
  farm.add(gravelFloor);

  // 2. Horizontal Double-Walled Cylindrical Fuel Tanks
  const tankMat = new THREE.MeshStandardMaterial({
    color: 0xd97706, // High-visibility Antarctic fuel amber/orange
    metalness: 0.5,
    roughness: 0.35,
    wireframe
  });
  const cradleMat = createConcreteFoundationMaterial({ wireframe });

  const tankCount = 3;
  const tankRadius = 1.2;
  const tankLength = 7.0;

  for (let i = 0; i < tankCount; i++) {
    const tankGroup = new THREE.Group();
    const xPos = -4.2 + i * 4.2;
    tankGroup.position.set(xPos, tankRadius + 0.6, 0);

    // Main tank cylinder (rotated horizontal along Z-axis)
    const tankGeo = new THREE.CylinderGeometry(tankRadius, tankRadius, tankLength, 24);
    tankGeo.rotateX(Math.PI / 2);
    const tank = new THREE.Mesh(tankGeo, tankMat);
    tank.castShadow = true;
    tankGroup.add(tank);

    // Dished end caps
    const capGeo = new THREE.SphereGeometry(tankRadius, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2);
    const capFront = new THREE.Mesh(capGeo, tankMat);
    capFront.rotation.x = Math.PI / 2;
    capFront.position.z = tankLength / 2;
    tankGroup.add(capFront);

    const capBack = new THREE.Mesh(capGeo, tankMat);
    capBack.rotation.x = -Math.PI / 2;
    capBack.position.z = -tankLength / 2;
    tankGroup.add(capBack);

    // Concrete Saddle Cradles
    const cradle1 = new THREE.Mesh(new THREE.BoxGeometry(tankRadius * 2.2, 0.6, 0.8), cradleMat);
    cradle1.position.set(0, -tankRadius - 0.3, -tankLength / 3);
    tankGroup.add(cradle1);

    const cradle2 = new THREE.Mesh(new THREE.BoxGeometry(tankRadius * 2.2, 0.6, 0.8), cradleMat);
    cradle2.position.set(0, -tankRadius - 0.3, tankLength / 3);
    tankGroup.add(cradle2);

    farm.add(tankGroup);
  }

  return farm;
}

/**
 * Creates a geodesic radome on elevated structural platform.
 */
export function createRadome(radius: number = 2.0, wireframe: boolean = false): THREE.Group {
  const domeGroup = new THREE.Group();

  // Elevated steel platform
  const platMat = createStructuralSteelMaterial(0x475569);
  const platform = new THREE.Mesh(new THREE.CylinderGeometry(radius * 1.2, radius * 1.2, 0.3, 16), platMat);
  platform.position.y = 0.15;
  platform.castShadow = true;
  domeGroup.add(platform);

  // Safety railing around perimeter
  const railGeo = new THREE.CylinderGeometry(radius * 1.15, radius * 1.15, 0.8, 16, 1, true);
  const railMat = new THREE.MeshBasicMaterial({ color: 0x94a3b8, wireframe: true });
  const railing = new THREE.Mesh(railGeo, railMat);
  railing.position.y = 0.6;
  domeGroup.add(railing);

  // Geodesic Radome Shell (Translucent white composite)
  const domeGeo = new THREE.IcosahedronGeometry(radius, 3);
  const domeMat = new THREE.MeshStandardMaterial({
    color: 0xf8fafc,
    roughness: 0.25,
    metalness: 0.1,
    wireframe
  });
  const dome = new THREE.Mesh(domeGeo, domeMat);
  dome.position.y = radius * 0.9;
  dome.castShadow = true;
  domeGroup.add(dome);

  // Subtle wireframe line overlay to emphasize geodesic facets
  const wireMat = new THREE.LineBasicMaterial({ color: 0x94a3b8, transparent: true, opacity: 0.35 });
  const wireGeo = new THREE.WireframeGeometry(domeGeo);
  const wire = new THREE.LineSegments(wireGeo, wireMat);
  wire.position.copy(dome.position);
  domeGroup.add(wire);

  return domeGroup;
}

// =============================================================================
// TERRAIN BUILDER (Realistic Polar Topography with Sastrugi, Nunataks & Helipad)
// =============================================================================

export function buildPolarTerrain(
  terrainType: 'BEDROCK_ICE' | 'ROCKY_OASIS' | 'ARCTIC_TUNDRA',
  wireframe: boolean = false
): THREE.Object3D {
  const terrainGroup = new THREE.Group();

  const width = 160;
  const depth = 160;
  const segments = 64;

  const geo = new THREE.PlaneGeometry(width, depth, segments, segments);
  geo.rotateX(-Math.PI / 2);

  // Procedural height elevation based on polar station environment
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const z = pos.getZ(i);

    // Keep immediate station foundation (central 50x40m) relatively level for structural realism
    const distCenter = Math.sqrt((x * 0.8) ** 2 + (z * 1.1) ** 2);
    const flatFactor = Math.min(1.0, Math.max(0.0, (distCenter - 22) / 30));

    let height = 0;
    if (terrainType === 'BEDROCK_ICE') {
      // Bharati: Larsemann Hills coastal granite knolls and sastrugi snowdrifts
      height = (Math.sin(x * 0.05) * 2.2 + Math.cos(z * 0.06) * 1.8 + Math.sin((x + z) * 0.03) * 3.5) * flatFactor;
      if (x < -20 && z < -15) height -= 2.5 * flatFactor;
    } else if (terrainType === 'ROCKY_OASIS') {
      // Maitri: Schirmacher Oasis rugged rocky undulating ridge
      height = (Math.sin(x * 0.08) * 3.2 + Math.cos(z * 0.09) * 2.8 + Math.sin(x * 0.15) * 1.2) * flatFactor;
      if (x > 18 && z > 15) height -= 3.2 * flatFactor;
    } else {
      // Himadri: Ny-Ålesund gentle coastal Arctic tundra with snowdrifts
      height = (Math.sin(x * 0.04) * 1.2 + Math.cos(z * 0.04) * 0.9) * flatFactor;
    }

    pos.setY(i, height);
  }
  geo.computeVertexNormals();

  let mat: THREE.MeshStandardMaterial;
  if (terrainType === 'BEDROCK_ICE') {
    mat = createPolarSnowMaterial({ wireframe });
  } else if (terrainType === 'ROCKY_OASIS') {
    mat = createBedrockMaterial({ wireframe });
  } else {
    mat = new THREE.MeshStandardMaterial({
      color: 0xcfd8dc,
      roughness: 0.88,
      metalness: 0.08,
      wireframe
    });
  }

  const terrainMesh = new THREE.Mesh(geo, mat);
  terrainMesh.position.y = -0.1;
  terrainMesh.receiveShadow = true;
  terrainGroup.add(terrainMesh);

  // 1. SCATTERED GRANITE BEDROCK NUNATAK BOULDERS
  const boulderMat = createBedrockMaterial({ wireframe });
  const boulderCoords = [
    [-38, -25, 2.5], [-44, 18, 3.2], [42, -28, 4.0], [50, 15, 3.5],
    [-18, 42, 2.8], [25, 45, 3.0], [-52, -8, 4.5], [38, -45, 5.0]
  ];
  boulderCoords.forEach(([bx, bz, bscale]) => {
    const bGeo = new THREE.DodecahedronGeometry(bscale, 1);
    const bMesh = new THREE.Mesh(bGeo, boulderMat);
    bMesh.position.set(bx, bscale * 0.45, bz);
    bMesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);
    bMesh.castShadow = true;
    bMesh.receiveShadow = true;
    terrainGroup.add(bMesh);
  });

  // 2. REALISTIC POLAR HELIPAD (Landing Pad with perimeter LED beacons)
  const padGroup = new THREE.Group();
  padGroup.position.set(36, 0.25, 24);

  const padGeo = new THREE.CylinderGeometry(8.5, 9.0, 0.4, 8);
  const padMat = new THREE.MeshStandardMaterial({
    color: 0x475569,
    roughness: 0.8,
    metalness: 0.2
  });
  const padMesh = new THREE.Mesh(padGeo, padMat);
  padMesh.castShadow = true;
  padMesh.receiveShadow = true;
  padGroup.add(padMesh);

  // Painted yellow landing circle & inner 'H' cross
  const ringGeo = new THREE.RingGeometry(6.0, 6.5, 32);
  ringGeo.rotateX(-Math.PI / 2);
  const markMat = new THREE.MeshBasicMaterial({ color: 0xfacc15, side: THREE.DoubleSide });
  const ringMesh = new THREE.Mesh(ringGeo, markMat);
  ringMesh.position.y = 0.22;
  padGroup.add(ringMesh);

  const hBar1 = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 5.0), markMat);
  hBar1.rotateX(-Math.PI / 2);
  hBar1.position.set(-1.8, 0.23, 0);
  padGroup.add(hBar1);

  const hBar2 = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 5.0), markMat);
  hBar2.rotateX(-Math.PI / 2);
  hBar2.position.set(1.8, 0.23, 0);
  padGroup.add(hBar2);

  const hCross = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 0.8), markMat);
  hCross.rotateX(-Math.PI / 2);
  hCross.position.set(0, 0.23, 0);
  padGroup.add(hCross);

  // 8 Perimeter LED landing beacons
  const beaconMat = new THREE.MeshStandardMaterial({
    color: 0x10b981,
    emissive: 0x10b981,
    emissiveIntensity: 0.9,
    roughness: 0.2
  });
  const pylonMat = createStructuralSteelMaterial(0x1e293b);
  for (let b = 0; b < 8; b++) {
    const bAngle = (b / 8) * Math.PI * 2;
    const bx = Math.sin(bAngle) * 8.2;
    const bz = Math.cos(bAngle) * 8.2;

    const pylon = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 0.6, 6), pylonMat);
    pylon.position.set(bx, 0.5, bz);
    padGroup.add(pylon);

    const led = new THREE.Mesh(new THREE.SphereGeometry(0.18, 8, 8), beaconMat);
    led.position.set(bx, 0.85, bz);
    padGroup.add(led);
  }
  terrainGroup.add(padGroup);

  // 3. VEHICLE CRAWLER SNOW TRACKS (PistenBully / Snowcat twin tread depressions)
  const trackMat = new THREE.LineBasicMaterial({ color: 0x94a3b8, transparent: true, opacity: 0.45 });
  const trackPoints1 = [
    new THREE.Vector3(20, 0.05, 4),
    new THREE.Vector3(26, 0.08, 12),
    new THREE.Vector3(34, 0.12, 18)
  ];
  const trackPoints2 = [
    new THREE.Vector3(21.2, 0.05, 4),
    new THREE.Vector3(27.2, 0.08, 12),
    new THREE.Vector3(35.2, 0.12, 18)
  ];
  terrainGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(trackPoints1), trackMat));
  terrainGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(trackPoints2), trackMat));

  // If Maitri, add frozen Lake Priyadarshini water plane
  if (terrainType === 'ROCKY_OASIS') {
    const lakeGeo = new THREE.PlaneGeometry(50, 50);
    lakeGeo.rotateX(-Math.PI / 2);
    const lakeMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      roughness: 0.15,
      metalness: 0.6,
      transparent: true,
      opacity: 0.75
    });
    const lakeMesh = new THREE.Mesh(lakeGeo, lakeMat);
    lakeMesh.position.set(38, -0.6, 35);
    lakeMesh.receiveShadow = true;
    terrainGroup.add(lakeMesh);
  }

  return terrainGroup;
}

// =============================================================================
// 1. BHARATI STATION PROCEDURAL 3D ARCHITECTURE
// =============================================================================

export function buildBharatiStation(
  activeLayer: 'ARCHITECTURE' | 'ENERGY' | 'IMPACT',
  wireframe: boolean = false
): StationMeshResult {
  const architectureGroup = new THREE.Group();
  const interactiveMeshes = new Map<string, THREE.Object3D>();
  const turbines: { rotorGroup: THREE.Group; speedMultiplier: number }[] = [];
  const statusIndicators: { mesh: THREE.Mesh; type: 'DG' | 'BESS' | 'WIND' | 'SOLAR' | 'BUS'; id: string }[] = [];

  const isArchMode = activeLayer === 'ARCHITECTURE';
  const hullOpacity = isArchMode ? 0.98 : 0.42;

  // PBR Materials (bof Architekten / NCPOR Architectural Specs)
  const hullOrangeMat = createPolarCompositeMaterial(0xea580c, {
    wireframe,
    transparent: !isArchMode,
    opacity: hullOpacity
  });

  const hullSilverMat = createPolarCompositeMaterial(0xf1f5f9, {
    wireframe,
    transparent: !isArchMode,
    opacity: hullOpacity
  });

  const darkSteelMat = createStructuralSteelMaterial(0x334155, { wireframe });
  const windowFrameMat = createStructuralSteelMaterial(0x0f172a, { wireframe });
  const glassMat = createIndustrialGlassMaterial(true, isArchMode ? 0.92 : 0.65, {
    wireframe,
    opacity: isArchMode ? 0.9 : 0.55
  });

  // --- A. HEAVY STEEL FOUNDATION STILTS (24 Heavy Columns with Cross-Bracing) ---
  const stiltGroup = new THREE.Group();
  const colHeight = 3.8;
  const colRadius = 0.35;
  const colGeo = new THREE.CylinderGeometry(colRadius, colRadius, colHeight, 16);
  const footingMat = createConcreteFoundationMaterial({ wireframe });
  const footingGeo = new THREE.BoxGeometry(1.6, 0.5, 1.6);

  const stiltGridX = [-20, -14, -8, -2, 4, 10, 16, 20];
  const stiltGridZ = [-10, 0, 10];

  stiltGridX.forEach(x => {
    stiltGridZ.forEach(z => {
      const col = new THREE.Mesh(colGeo, darkSteelMat);
      col.position.set(x, colHeight / 2, z);
      col.castShadow = true;
      stiltGroup.add(col);

      // Steel flange collar
      const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.48, 0.15, 16), darkSteelMat);
      collar.position.set(x, 0.45, z);
      stiltGroup.add(collar);

      const footing = new THREE.Mesh(footingGeo, footingMat);
      footing.position.set(x, 0.25, z);
      footing.receiveShadow = true;
      stiltGroup.add(footing);
    });
  });

  // Diagonal steel cross-bracing along perimeter columns
  for (let i = 0; i < stiltGridX.length - 1; i++) {
    const x1 = stiltGridX[i];
    const x2 = stiltGridX[i + 1];
    [-10, 10].forEach(z => {
      const p1 = [new THREE.Vector3(x1, 0.45, z), new THREE.Vector3(x2, colHeight, z)];
      const p2 = [new THREE.Vector3(x1, colHeight, z), new THREE.Vector3(x2, 0.45, z)];
      stiltGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(p1), new THREE.LineBasicMaterial({ color: 0x64748b })));
      stiltGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(p2), new THREE.LineBasicMaterial({ color: 0x64748b })));
    });
  }
  architectureGroup.add(stiltGroup);

  // --- B. AERODYNAMIC MAIN HULL SUPERSTRUCTURE ---
  // Authentic Bharati Design: Orange Aerodynamic Pods on both ends, silver insulated panels in center!
  const hullGroup = new THREE.Group();

  const totalLength = 46;
  const centerLength = 26;
  const podLength = 10;
  const hullWidth = 24;

  // Deck 1 (Lower Engineering Level, +3.8m to +7.4m)
  // Center silver insulated block
  const d1Center = new THREE.Mesh(new THREE.BoxGeometry(centerLength, 3.6, hullWidth), hullSilverMat);
  d1Center.position.set(0, 3.8 + 1.8, 0);
  d1Center.castShadow = true;
  d1Center.receiveShadow = true;
  hullGroup.add(d1Center);

  // Northwest curved aerodynamic orange bow pod
  const bowOrange = new THREE.Mesh(new THREE.BoxGeometry(podLength, 3.6, hullWidth), hullOrangeMat);
  bowOrange.position.set(-centerLength / 2 - podLength / 2, 3.8 + 1.8, 0);
  bowOrange.castShadow = true;
  bowOrange.receiveShadow = true;
  hullGroup.add(bowOrange);

  // Southeast curved aerodynamic orange stern pod
  const sternOrange = new THREE.Mesh(new THREE.BoxGeometry(podLength, 3.6, hullWidth), hullOrangeMat);
  sternOrange.position.set(centerLength / 2 + podLength / 2, 3.8 + 1.8, 0);
  sternOrange.castShadow = true;
  sternOrange.receiveShadow = true;
  hullGroup.add(sternOrange);

  // Aerodynamic nose chamfer bevel on front
  const noseConeGeo = new THREE.CylinderGeometry(5.0, 5.0, 3.6, 16, 1, false, 0, Math.PI);
  const noseCone = new THREE.Mesh(noseConeGeo, hullOrangeMat);
  noseCone.rotation.y = -Math.PI / 2;
  noseCone.position.set(-totalLength / 2, 3.8 + 1.8, 0);
  noseCone.castShadow = true;
  hullGroup.add(noseCone);

  const tailCone = new THREE.Mesh(noseConeGeo, hullOrangeMat);
  tailCone.rotation.y = Math.PI / 2;
  tailCone.position.set(totalLength / 2, 3.8 + 1.8, 0);
  tailCone.castShadow = true;
  hullGroup.add(tailCone);

  // Deck 2 (Middle Habitation & Mission Operations Bridge, +7.4m to +11.0m)
  const d2Center = new THREE.Mesh(new THREE.BoxGeometry(centerLength, 3.6, hullWidth - 1.5), hullSilverMat);
  d2Center.position.set(0, 7.4 + 1.8, 0);
  d2Center.castShadow = true;
  d2Center.receiveShadow = true;
  hullGroup.add(d2Center);

  const d2Bow = new THREE.Mesh(new THREE.BoxGeometry(podLength, 3.6, hullWidth - 1.5), hullOrangeMat);
  d2Bow.position.set(-centerLength / 2 - podLength / 2, 7.4 + 1.8, 0);
  d2Bow.castShadow = true;
  hullGroup.add(d2Bow);

  const d2Stern = new THREE.Mesh(new THREE.BoxGeometry(podLength, 3.6, hullWidth - 1.5), hullOrangeMat);
  d2Stern.position.set(centerLength / 2 + podLength / 2, 7.4 + 1.8, 0);
  d2Stern.castShadow = true;
  hullGroup.add(d2Stern);

  // Recessed Ribbon Observation Windows on Habitation Level with Individual Mullions
  const winZOffset = (hullWidth - 1.5) / 2 + 0.08;
  const winStripGeo = new THREE.BoxGeometry(centerLength + 8, 1.4, 0.2);
  const winStripFront = new THREE.Mesh(winStripGeo, glassMat);
  winStripFront.position.set(0, 9.2, winZOffset);
  hullGroup.add(winStripFront);

  const winStripBack = new THREE.Mesh(winStripGeo, glassMat);
  winStripBack.position.set(0, 9.2, -winZOffset);
  hullGroup.add(winStripBack);

  // Individual dark window frame mullions
  for (let mx = -16; mx <= 16; mx += 2.4) {
    const mullionGeo = new THREE.BoxGeometry(0.12, 1.45, 0.25);
    const mFront = new THREE.Mesh(mullionGeo, windowFrameMat);
    mFront.position.set(mx, 9.2, winZOffset);
    hullGroup.add(mFront);
    const mBack = new THREE.Mesh(mullionGeo, windowFrameMat);
    mBack.position.set(mx, 9.2, -winZOffset);
    hullGroup.add(mBack);
  }

  // Deck 3 (Upper Science Observatory & Clean Labs, +11.0m to +14.2m)
  const d3Length = 30;
  const d3Width = 17;
  const d3Height = 3.2;
  const d3Mesh = new THREE.Mesh(new THREE.BoxGeometry(d3Length, d3Height, d3Width), hullSilverMat);
  d3Mesh.position.set(1, 11.0 + d3Height / 2, 0);
  d3Mesh.castShadow = true;
  hullGroup.add(d3Mesh);

  // Deck 3 Orange Accent Facade Trim
  const d3Trim = new THREE.Mesh(new THREE.BoxGeometry(d3Length + 0.2, 0.45, d3Width + 0.2), hullOrangeMat);
  d3Trim.position.set(1, 11.0 + d3Height + 0.2, 0);
  hullGroup.add(d3Trim);

  // Deck 3 Panoramic Science Windows
  const obsWindowFront = new THREE.Mesh(new THREE.BoxGeometry(d3Length - 4, 1.6, 0.2), glassMat);
  obsWindowFront.position.set(1, 12.6, d3Width / 2 + 0.08);
  hullGroup.add(obsWindowFront);

  // --- C. ELEVATED PEDESTRIAN ACCESS BRIDGE & STAIRS ---
  // In the real station photo, an impressive steel bridge leads down to ground
  const bridgeMat = createStructuralSteelMaterial(0x475569);
  const bridgeTreadMat = createGalvanizedLegMaterial();
  const bridgeFloor = new THREE.Mesh(new THREE.BoxGeometry(16, 0.3, 2.2), bridgeTreadMat);
  bridgeFloor.position.set(18, 4.8, 14);
  bridgeFloor.rotation.y = 0.55;
  bridgeFloor.rotation.z = -0.32;
  bridgeFloor.castShadow = true;
  hullGroup.add(bridgeFloor);

  // Bridge Support Stilts
  [12, 18, 24].forEach((bx, idx) => {
    const bHeight = Math.max(1.0, 7.2 - idx * 2.2);
    const bStilt = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, bHeight, 10), darkSteelMat);
    bStilt.position.set(bx, bHeight / 2, 10 + idx * 2.8);
    hullGroup.add(bStilt);
  });

  // Blue Insulated Seawater Intake Pipeline
  const pipeMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.4, metalness: 0.6 });
  const pipeGeo = new THREE.CylinderGeometry(0.22, 0.22, 18, 12);
  const pipeMesh = new THREE.Mesh(pipeGeo, pipeMat);
  pipeMesh.position.set(-16, 2.4, -14);
  pipeMesh.rotation.z = 0.45;
  pipeMesh.rotation.x = -0.3;
  hullGroup.add(pipeMesh);

  architectureGroup.add(hullGroup);

  // --- D. ROOFTOP MULTI-DOME RADOME COMPLEX & COMMS TOWER ---
  // 1. Primary White Geodesic Satellite Radome (North forward deck)
  const radomeMain = createRadome(2.5, wireframe);
  radomeMain.position.set(5, 14.4, -1);
  architectureGroup.add(radomeMain);

  // 2. Secondary Bright Yellow Radome Dome (Exact match to official ground truth photo!)
  const yellowDomeMat = new THREE.MeshStandardMaterial({
    color: 0xfacc15, // High-vis polar yellow
    roughness: 0.35,
    metalness: 0.25,
    wireframe
  });
  const yellowDomeGeo = new THREE.SphereGeometry(1.8, 20, 16, 0, Math.PI * 2, 0, Math.PI * 0.55);
  const yellowDome = new THREE.Mesh(yellowDomeGeo, yellowDomeMat);
  yellowDome.position.set(-6, 14.4, 2.5);
  yellowDome.castShadow = true;
  architectureGroup.add(yellowDome);

  const yellowDomeBase = new THREE.Mesh(new THREE.CylinderGeometry(1.85, 1.85, 0.4, 16), darkSteelMat);
  yellowDomeBase.position.set(-6, 14.4, 2.5);
  architectureGroup.add(yellowDomeBase);

  // 3. Tertiary Pale Grey Dome
  const greyDomeMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, roughness: 0.4, metalness: 0.3 });
  const greyDome = new THREE.Mesh(new THREE.SphereGeometry(1.2, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.55), greyDomeMat);
  greyDome.position.set(12, 14.4, 3);
  greyDome.castShadow = true;
  architectureGroup.add(greyDome);

  // 4. Structural Steel Communications Tower with Aviation Warning Beacon
  const towerGroup = new THREE.Group();
  towerGroup.position.set(-2, 14.4, -4);
  const mastCore = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.2, 7.5, 8), darkSteelMat);
  mastCore.position.y = 3.75;
  mastCore.castShadow = true;
  towerGroup.add(mastCore);

  // Lattice cross arms
  [-1.5, 0, 1.5].forEach(dy => {
    const arm = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.08, 0.08), darkSteelMat);
    arm.position.y = 4.5 + dy;
    towerGroup.add(arm);
  });

  // Red blinking aviation warning beacon at tip
  const beaconMat = new THREE.MeshBasicMaterial({ color: 0xef4444 });
  const beacon = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 8), beaconMat);
  beacon.position.y = 7.6;
  towerGroup.add(beacon);
  architectureGroup.add(towerGroup);

  // --- D. POWERHOUSE COMPOUND: DIESEL GENSET & BESS CONTAINER ---
  // Heavy Acoustic Diesel Genset Compound on East Pad
  const dgUnit = createDieselGeneratorUnit(7.5, 3.2, 3.5, wireframe);
  dgUnit.group.position.set(22, 0, -10);
  dgUnit.group.userData = { deviceId: 'diesel_generator_1', label: 'Primary Diesel Gensets (3x80 kW)' };
  interactiveMeshes.set('diesel_generator_1', dgUnit.group);
  statusIndicators.push({ mesh: dgUnit.statusLed, type: 'DG', id: 'diesel_generator_1' });
  architectureGroup.add(dgUnit.group);

  // Containerized BESS Battery Storage on Southeast Pad
  const bessUnit = createBessContainer(6.5, 2.8, 2.6, wireframe);
  bessUnit.group.position.set(22, 0, 8);
  bessUnit.group.userData = { deviceId: 'bess_bank_1', label: 'Battery Energy Storage (120 kWh BESS)' };
  interactiveMeshes.set('bess_bank_1', bessUnit.group);
  statusIndicators.push({ mesh: bessUnit.statusLed, type: 'BESS', id: 'bess_bank_1' });
  architectureGroup.add(bessUnit.group);

  // 415V Main Station Switchgear Bus Hub
  const busHub = createMainStationBusHub(4.2, 2.6, 1.8, wireframe);
  busHub.group.position.set(12, 0, -2);
  busHub.group.userData = { deviceId: 'bh_obj_main_bus', label: 'Main Station 415V Busbar Switchgear' };
  interactiveMeshes.set('bh_obj_main_bus', busHub.group);
  statusIndicators.push({ mesh: busHub.busStatusLed, type: 'BUS', id: 'bh_obj_main_bus' });
  architectureGroup.add(busHub.group);

  // --- E. EXTERNAL FUEL STORAGE FARM ---
  const fuelFarm = createFuelFarm(wireframe);
  fuelFarm.position.set(28, 0, -24);
  fuelFarm.userData = { deviceId: 'fuel_farm', label: 'Bulk Diesel Fuel Storage' };
  interactiveMeshes.set('fuel_farm', fuelFarm);
  architectureGroup.add(fuelFarm);

  // --- F. SOLAR PV ARRAYS (Bifacial ground-mounted tilted racks) ---
  const solarRack1 = createSolarRack(14, 5, 42, wireframe);
  solarRack1.position.set(-24, 0, -14);
  solarRack1.userData = { deviceId: 'solar_pv_array', label: 'Photovoltaic Array 1 (18 kWp)' };
  interactiveMeshes.set('solar_pv_array', solarRack1);
  architectureGroup.add(solarRack1);

  const solarRack2 = createSolarRack(14, 5, 42, wireframe);
  solarRack2.position.set(-24, 0, -6);
  solarRack2.userData = { deviceId: 'solar_pv_array', label: 'Photovoltaic Array 2 (12 kWp)' };
  architectureGroup.add(solarRack2);

  // --- G. WIND TURBINES (Katabatic high-latitude turbines) ---
  const t1 = createWindTurbine(14, 6.5, wireframe);
  t1.group.position.set(-28, 0, 16);
  t1.group.userData = { deviceId: 'wind_turbine_1', label: 'Wind Turbine 1 (15 kW)' };
  interactiveMeshes.set('wind_turbine_1', t1.group);
  turbines.push({ rotorGroup: t1.rotor, speedMultiplier: 1.0 });
  architectureGroup.add(t1.group);

  const t2 = createWindTurbine(12, 5.5, wireframe);
  t2.group.position.set(-18, 0, 20);
  t2.group.userData = { deviceId: 'wind_turbine_2', label: 'Wind Turbine 2 (10 kW)' };
  interactiveMeshes.set('wind_turbine_2', t2.group);
  turbines.push({ rotorGroup: t2.rotor, speedMultiplier: 1.15 });
  architectureGroup.add(t2.group);

  // Terrain
  const terrainMesh = buildPolarTerrain('BEDROCK_ICE', wireframe);

  return { architectureGroup, terrainMesh, interactiveMeshes, turbines, statusIndicators };
}

// =============================================================================
// 2. MAITRI STATION PROCEDURAL 3D ARCHITECTURE
// =============================================================================

export function buildMaitriStation(
  activeLayer: 'ARCHITECTURE' | 'ENERGY' | 'IMPACT',
  wireframe: boolean = false
): StationMeshResult {
  const architectureGroup = new THREE.Group();
  const interactiveMeshes = new Map<string, THREE.Object3D>();
  const turbines: { rotorGroup: THREE.Group; speedMultiplier: number }[] = [];
  const statusIndicators: { mesh: THREE.Mesh; type: 'DG' | 'BESS' | 'WIND' | 'SOLAR' | 'BUS'; id: string }[] = [];

  const isArchMode = activeLayer === 'ARCHITECTURE';
  const blockOpacity = isArchMode ? 0.96 : 0.45;

  // Maitri Color Palette (High-visibility Antarctic Yellow, Navy Blue Trim)
  const yellowBlockMat = createInsulatedCladdingMaterial(0xf59e0b, {
    wireframe,
    transparent: !isArchMode,
    opacity: blockOpacity
  });

  const blueTrimMat = createStructuralSteelMaterial(0x1e3a8a, { wireframe });
  const spineMat = createInsulatedCladdingMaterial(0xe2e8f0, {
    wireframe,
    transparent: !isArchMode,
    opacity: blockOpacity
  });

  // --- A. THE ICONIC CENTRAL ENCLOSED SPINAL CORRIDOR ---
  const spineLength = 34;
  const spineWidth = 2.8;
  const spineHeight = 3.0;

  const spineMesh = new THREE.Mesh(new THREE.BoxGeometry(spineLength, spineHeight, spineWidth), spineMat);
  spineMesh.position.set(0, spineHeight / 2 + 0.4, 0);
  spineMesh.castShadow = true;
  spineMesh.receiveShadow = true;
  architectureGroup.add(spineMesh);

  // Corridor stilt supports
  for (let x = -14; x <= 14; x += 7) {
    const postGeo = new THREE.CylinderGeometry(0.18, 0.18, 0.8, 8);
    const postMat = createStructuralSteelMaterial(0x334155);
    const post1 = new THREE.Mesh(postGeo, postMat);
    post1.position.set(x, 0.4, -1.2);
    architectureGroup.add(post1);
    const post2 = new THREE.Mesh(postGeo, postMat);
    post2.position.set(x, 0.4, 1.2);
    architectureGroup.add(post2);
  }

  // --- B. LIVING BLOCK A & LIVING BLOCK B ---
  const blockGeo = new THREE.BoxGeometry(14, 5.4, 8);

  // Living Block A (Habitation, Galley, Medical)
  const blockA = new THREE.Mesh(blockGeo, yellowBlockMat);
  blockA.position.set(-10, 2.7 + 0.4, -6.5);
  blockA.castShadow = true;
  blockA.receiveShadow = true;
  blockA.userData = { deviceId: 'mt_galley_kitchen', label: 'Living Block A (Crew & Galley)' };
  interactiveMeshes.set('mt_galley_kitchen', blockA);
  architectureGroup.add(blockA);

  const trimA = new THREE.Mesh(new THREE.BoxGeometry(14.2, 0.4, 8.2), blueTrimMat);
  trimA.position.set(-10, 5.4 + 0.4, -6.5);
  architectureGroup.add(trimA);

  // Living Block B (Quarters & Recreation)
  const blockB = new THREE.Mesh(blockGeo, yellowBlockMat);
  blockB.position.set(10, 2.7 + 0.4, -6.5);
  blockB.castShadow = true;
  blockB.receiveShadow = true;
  blockB.userData = { deviceId: 'mt_galley_kitchen', label: 'Living Block B (Quarters)' };
  interactiveMeshes.set('mt_galley_kitchen', blockB);
  architectureGroup.add(blockB);

  const trimB = new THREE.Mesh(new THREE.BoxGeometry(14.2, 0.4, 8.2), blueTrimMat);
  trimB.position.set(10, 5.4 + 0.4, -6.5);
  architectureGroup.add(trimB);

  // --- C. DEDICATED MAITRI POWER HOUSE & BESS COMPOUND ---
  const dgUnit = createDieselGeneratorUnit(9.0, 3.8, 4.2, wireframe);
  dgUnit.group.position.set(-12, 0, 8.5);
  dgUnit.group.userData = { deviceId: 'mt_diesel', label: 'Maitri Power House (3x62.5 kW Gensets)' };
  interactiveMeshes.set('mt_diesel', dgUnit.group);
  statusIndicators.push({ mesh: dgUnit.statusLed, type: 'DG', id: 'mt_diesel' });
  architectureGroup.add(dgUnit.group);

  // Maitri BESS Storage Unit
  const bessUnit = createBessContainer(5.5, 2.6, 2.4, wireframe);
  bessUnit.group.position.set(10, 0, 7.5);
  bessUnit.group.userData = { deviceId: 'mt_bess', label: 'Maitri BESS Storage (80 kWh)' };
  interactiveMeshes.set('mt_bess', bessUnit.group);
  statusIndicators.push({ mesh: bessUnit.statusLed, type: 'BESS', id: 'mt_bess' });
  architectureGroup.add(bessUnit.group);

  // Central 415V Main Busbar PDC Hub
  const busHub = createMainStationBusHub(3.6, 2.4, 1.6, wireframe);
  busHub.group.position.set(0, 0, 4.5);
  busHub.group.userData = { deviceId: 'node_mt_main_bus', label: 'Maitri 415V Station Distribution Bus' };
  interactiveMeshes.set('node_mt_main_bus', busHub.group);
  statusIndicators.push({ mesh: busHub.busStatusLed, type: 'BUS', id: 'node_mt_main_bus' });
  architectureGroup.add(busHub.group);

  // --- D. LAKE PRIYADARSHINI WATER PUMP HOUSE & OVERLAND PIPELINE ---
  const waterPumpHouse = new THREE.Mesh(
    new THREE.BoxGeometry(5.5, 3.2, 5),
    createInsulatedCladdingMaterial(0x0284c7, { wireframe })
  );
  waterPumpHouse.position.set(26, 1.6, 22);
  waterPumpHouse.castShadow = true;
  waterPumpHouse.userData = { deviceId: 'mt_pribarshini_water', label: 'Lake Priyadarshini Water Pump' };
  interactiveMeshes.set('mt_pribarshini_water', waterPumpHouse);
  architectureGroup.add(waterPumpHouse);

  // Insulated water pipeline on A-frame trestles
  const waterPipePoints = [
    new THREE.Vector3(26, 2.0, 22),
    new THREE.Vector3(18, 2.2, 14),
    new THREE.Vector3(10, 2.4, 6),
    new THREE.Vector3(0, 2.4, 3)
  ];
  const waterPipeGeo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(waterPipePoints), 24, 0.18, 8, false);
  const waterPipe = new THREE.Mesh(waterPipeGeo, new THREE.MeshStandardMaterial({ color: 0x38bdf8, roughness: 0.3 }));
  architectureGroup.add(waterPipe);

  // --- E. RENEWABLES & EXPEDITION ASSETS ---
  const solarRack = createSolarRack(12, 4.5, 38, wireframe);
  solarRack.position.set(-22, 0, -12);
  solarRack.userData = { deviceId: 'node_mt_solar', label: 'Maitri Solar PV Array (18 kWp)' };
  interactiveMeshes.set('node_mt_solar', solarRack);
  architectureGroup.add(solarRack);

  const turbine = createWindTurbine(13, 6.0, wireframe);
  turbine.group.position.set(-22, 0, 14);
  turbine.group.userData = { deviceId: 'node_mt_wind', label: 'Maitri Wind Turbine (15 kW)' };
  interactiveMeshes.set('node_mt_wind', turbine.group);
  turbines.push({ rotorGroup: turbine.rotor, speedMultiplier: 1.0 });
  architectureGroup.add(turbine.group);

  // Terrain
  const terrainMesh = buildPolarTerrain('ROCKY_OASIS', wireframe);

  return { architectureGroup, terrainMesh, interactiveMeshes, turbines, statusIndicators };
}

// =============================================================================
// 3. HIMADRI STATION PROCEDURAL 3D ARCHITECTURE
// =============================================================================

export function buildHimadriStation(
  activeLayer: 'ARCHITECTURE' | 'ENERGY' | 'IMPACT',
  wireframe: boolean = false
): StationMeshResult {
  const architectureGroup = new THREE.Group();
  const interactiveMeshes = new Map<string, THREE.Object3D>();
  const turbines: { rotorGroup: THREE.Group; speedMultiplier: number }[] = [];
  const statusIndicators: { mesh: THREE.Mesh; type: 'DG' | 'BESS' | 'WIND' | 'SOLAR' | 'BUS'; id: string }[] = [];

  const isArchMode = activeLayer === 'ARCHITECTURE';
  const wallOpacity = isArchMode ? 0.96 : 0.45;

  // Traditional Nordic Ny-Ålesund Architecture (Falun Red Timber, Slate Pitch Roof, White Trim)
  const redTimberMat = createInsulatedCladdingMaterial(0x991b1b, {
    wireframe,
    transparent: !isArchMode,
    opacity: wallOpacity
  });

  const whiteTrimMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.35,
    metalness: 0.2,
    wireframe
  });

  const darkRoofMat = createStructuralSteelMaterial(0x1e293b, { wireframe });
  const windowGlassMat = createIndustrialGlassMaterial(true, isArchMode ? 0.75 : 0.4, {
    wireframe,
    opacity: isArchMode ? 0.8 : 0.4
  });

  // --- A. TWO-STOREY NORDIC RESEARCH LODGE ---
  const houseWidth = 16;
  const houseDepth = 12;
  const groundFloorHeight = 3.6;
  const upperFloorHeight = 3.4;
  const totalWallHeight = groundFloorHeight + upperFloorHeight;

  // Main Wall Body
  const walls = new THREE.Mesh(new THREE.BoxGeometry(houseWidth, totalWallHeight, houseDepth), redTimberMat);
  walls.position.set(0, totalWallHeight / 2 + 0.3, 0);
  walls.castShadow = true;
  walls.receiveShadow = true;
  architectureGroup.add(walls);

  // White Corner Trim Posts
  const postWidth = 0.35;
  const corners = [
    [-houseWidth / 2, -houseDepth / 2],
    [houseWidth / 2, -houseDepth / 2],
    [-houseWidth / 2, houseDepth / 2],
    [houseWidth / 2, houseDepth / 2]
  ];
  corners.forEach(([cx, cz]) => {
    const post = new THREE.Mesh(new THREE.BoxGeometry(postWidth, totalWallHeight + 0.1, postWidth), whiteTrimMat);
    post.position.set(cx, totalWallHeight / 2 + 0.3, cz);
    architectureGroup.add(post);
  });

  // Horizontal Floor Divider Trim
  const floorTrim = new THREE.Mesh(new THREE.BoxGeometry(houseWidth + 0.1, 0.3, houseDepth + 0.1), whiteTrimMat);
  floorTrim.position.set(0, groundFloorHeight + 0.3, 0);
  architectureGroup.add(floorTrim);

  // --- B. STEEP PITCHED GABLE ROOF (Snow Shedding) ---
  const roofHeight = 4.2;
  const roofShape = new THREE.Shape();
  roofShape.moveTo(-houseDepth / 2 - 0.6, 0);
  roofShape.lineTo(0, roofHeight);
  roofShape.lineTo(houseDepth / 2 + 0.6, 0);
  roofShape.closePath();

  const roofExtrudeSettings = {
    steps: 1,
    depth: houseWidth + 1.2,
    bevelEnabled: false
  };
  const roofGeo = new THREE.ExtrudeGeometry(roofShape, roofExtrudeSettings);
  roofGeo.rotateY(Math.PI / 2);
  roofGeo.translate(-houseWidth / 2 - 0.6, totalWallHeight + 0.3, 0);

  const roofMesh = new THREE.Mesh(roofGeo, darkRoofMat);
  roofMesh.castShadow = true;
  architectureGroup.add(roofMesh);

  // --- C. GLAZED WINDOWS WITH WHITE MULLIONS ---
  for (let x = -5; x <= 5; x += 5) {
    const win = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.4, 0.15), windowGlassMat);
    win.position.set(x, 2.0, houseDepth / 2 + 0.08);
    architectureGroup.add(win);

    const frame = new THREE.Mesh(new THREE.BoxGeometry(1.8, 1.6, 0.12), whiteTrimMat);
    frame.position.copy(win.position);
    architectureGroup.add(frame);
  }

  // --- D. POWER & DISTRICT ENERGY ASSETS ---
  // Microgrid Backup Genset
  const dgUnit = createDieselGeneratorUnit(6.0, 2.6, 2.8, wireframe);
  dgUnit.group.position.set(-14, 0, 5);
  dgUnit.group.userData = { deviceId: 'node_hm_diesel', label: 'Himadri Backup Diesel Generator (40 kW)' };
  interactiveMeshes.set('node_hm_diesel', dgUnit.group);
  statusIndicators.push({ mesh: dgUnit.statusLed, type: 'DG', id: 'node_hm_diesel' });
  architectureGroup.add(dgUnit.group);

  // Himadri Microgrid BESS
  const bessUnit = createBessContainer(5.0, 2.4, 2.2, wireframe);
  bessUnit.group.position.set(-14, 0, -4);
  bessUnit.group.userData = { deviceId: 'node_hm_bess', label: 'Himadri BESS Storage (50 kWh)' };
  interactiveMeshes.set('node_hm_bess', bessUnit.group);
  statusIndicators.push({ mesh: bessUnit.statusLed, type: 'BESS', id: 'node_hm_bess' });
  architectureGroup.add(bessUnit.group);

  // Ny-Ålesund District 400V Grid Interconnect Kiosk
  const distBus = createMainStationBusHub(3.2, 2.2, 1.5, wireframe);
  distBus.group.position.set(-6, 0, -10);
  distBus.group.userData = { deviceId: 'node_hm_main_bus', label: 'District Energy & 400V Tie-in Bus' };
  interactiveMeshes.set('node_hm_main_bus', distBus.group);
  statusIndicators.push({ mesh: distBus.busStatusLed, type: 'BUS', id: 'node_hm_main_bus' });
  architectureGroup.add(distBus.group);

  // --- E. RENEWABLES & EXPEDITION GEAR ---
  const solarRack = createSolarRack(10, 3.8, 48, wireframe);
  solarRack.position.set(14, 0, -6);
  solarRack.userData = { deviceId: 'node_hm_solar', label: 'Himadri Solar PV (12 kWp)' };
  interactiveMeshes.set('node_hm_solar', solarRack);
  architectureGroup.add(solarRack);

  const turbine = createWindTurbine(11, 5.0, wireframe);
  turbine.group.position.set(15, 0, 10);
  turbine.group.userData = { deviceId: 'node_hm_wind', label: 'Himadri Wind Turbine (10 kW)' };
  interactiveMeshes.set('node_hm_wind', turbine.group);
  turbines.push({ rotorGroup: turbine.rotor, speedMultiplier: 1.0 });
  architectureGroup.add(turbine.group);

  // Terrain
  const terrainMesh = buildPolarTerrain('ARCTIC_TUNDRA', wireframe);

  return { architectureGroup, terrainMesh, interactiveMeshes, turbines, statusIndicators };
}
