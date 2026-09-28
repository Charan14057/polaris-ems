/**
 * POLARIS-EMS — Station 3D Architectural Mesh Builders
 * Phase 18: Operational 3D Digital Twin Engine
 * 
 * Provides reference-aligned procedural 3D architectural models for:
 * 1. BHARATI (Elevated aerodynamic multi-deck station on structural stilts)
 * 2. MAITRI (Modular living blocks linked by central heated spine corridor)
 * 3. HIMADRI (Nordic 2-storey high-Arctic research facility with pitched roof)
 * 
 * Includes realistic polar terrain environments (snow/bedrock, rocky oasis, tundra),
 * realistic PBR materials (metallic cladding, architectural glass, structural steel),
 * and contextual equipment (solar racks, wind turbines, fuel farms, seawater intake).
 */

import * as THREE from 'three';

export interface StationMeshResult {
  architectureGroup: THREE.Group;
  terrainMesh: THREE.Object3D;
  interactiveMeshes: Map<string, THREE.Object3D>;
  turbines: { rotorGroup: THREE.Group; speedMultiplier: number }[];
}

// =============================================================================
// REUSABLE PROCEDURAL ASSET BUILDERS
// =============================================================================

/**
 * Creates a photorealistic solar PV array rack with tilted solar panels,
 * aluminum frames, and galvanized steel ground supports.
 */
export function createSolarRack(
  width: number, 
  depth: number, 
  tiltAngleDeg: number = 40,
  wireframe: boolean = false
): THREE.Group {
  const rack = new THREE.Group();
  const tiltRad = (tiltAngleDeg * Math.PI) / 180;

  // 1. Tilted Panel Surface (Photovoltaic dark blue monocrystalline)
  const panelGeo = new THREE.BoxGeometry(width, 0.1, depth);
  const panelMat = new THREE.MeshStandardMaterial({
    color: 0x1e3a8a, // Dark royal solar blue
    metalness: 0.8,
    roughness: 0.2,
    wireframe
  });
  const panel = new THREE.Mesh(panelGeo, panelMat);
  panel.rotation.x = tiltRad;
  panel.position.y = (depth / 2) * Math.sin(tiltRad) + 0.6;
  panel.castShadow = true;
  panel.receiveShadow = true;
  rack.add(panel);

  // 2. Solar cell grid lines on top of panel
  const gridMat = new THREE.LineBasicMaterial({ color: 0x60a5fa, transparent: true, opacity: 0.4 });
  const rows = 4;
  const cols = 8;
  for (let r = 1; r < rows; r++) {
    const points = [
      new THREE.Vector3(-width / 2, 0.06, -depth / 2 + (r * depth) / rows),
      new THREE.Vector3(width / 2, 0.06, -depth / 2 + (r * depth) / rows)
    ];
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    const line = new THREE.Line(geo, gridMat);
    line.rotation.x = tiltRad;
    line.position.copy(panel.position);
    rack.add(line);
  }
  for (let c = 1; c < cols; c++) {
    const points = [
      new THREE.Vector3(-width / 2 + (c * width) / cols, 0.06, -depth / 2),
      new THREE.Vector3(-width / 2 + (c * width) / cols, 0.06, depth / 2)
    ];
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    const line = new THREE.Line(geo, gridMat);
    line.rotation.x = tiltRad;
    line.position.copy(panel.position);
    rack.add(line);
  }

  // 3. Galvanized Steel Support Legs
  const legMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.7, roughness: 0.4 });
  const legGeo = new THREE.CylinderGeometry(0.08, 0.08, panel.position.y * 1.5, 6);
  
  const leg1 = new THREE.Mesh(legGeo, legMat);
  leg1.position.set(-width / 2 + 0.5, panel.position.y / 2, depth / 2 * Math.cos(tiltRad) - 0.2);
  leg1.castShadow = true;
  rack.add(leg1);

  const leg2 = new THREE.Mesh(legGeo, legMat);
  leg2.position.set(width / 2 - 0.5, panel.position.y / 2, depth / 2 * Math.cos(tiltRad) - 0.2);
  leg2.castShadow = true;
  rack.add(leg2);

  return rack;
}

/**
 * Creates an aerodynamic Antarctic wind turbine with tapered mast,
 * teardrop nacelle, nose spinner, and 3-blade prop assembly.
 */
export function createWindTurbine(
  towerHeight: number,
  rotorDiameter: number,
  wireframe: boolean = false
): { group: THREE.Group; rotor: THREE.Group } {
  const group = new THREE.Group();

  // 1. Tapered Tubular Steel Tower
  const towerGeo = new THREE.CylinderGeometry(0.35, 0.7, towerHeight, 16);
  const towerMat = new THREE.MeshStandardMaterial({
    color: 0xf1f5f9, // Arctic white / off-white
    metalness: 0.3,
    roughness: 0.35,
    wireframe
  });
  const tower = new THREE.Mesh(towerGeo, towerMat);
  tower.position.y = towerHeight / 2;
  tower.castShadow = true;
  tower.receiveShadow = true;
  group.add(tower);

  // Tower service door & yellow base band
  const bandGeo = new THREE.CylinderGeometry(0.71, 0.71, 1.2, 16);
  const bandMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.5 });
  const band = new THREE.Mesh(bandGeo, bandMat);
  band.position.y = 0.6;
  group.add(band);

  // 2. Streamlined Nacelle
  const nacelleGeo = new THREE.BoxGeometry(1.4, 1.1, 2.6);
  const nacelle = new THREE.Mesh(nacelleGeo, towerMat);
  nacelle.position.set(0, towerHeight + 0.55, 0.3);
  nacelle.castShadow = true;
  group.add(nacelle);

  // Anemometer mast on nacelle roof
  const sensorGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.8, 6);
  const sensorMat = new THREE.MeshStandardMaterial({ color: 0x334155 });
  const sensor = new THREE.Mesh(sensorGeo, sensorMat);
  sensor.position.set(0, towerHeight + 1.4, -0.6);
  group.add(sensor);

  // 3. Rotor Hub Spinner
  const rotor = new THREE.Group();
  rotor.position.set(0, towerHeight + 0.55, 1.65);

  const hubGeo = new THREE.ConeGeometry(0.5, 0.9, 16);
  hubGeo.rotateX(Math.PI / 2);
  const hubMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.3 });
  const hub = new THREE.Mesh(hubGeo, hubMat);
  rotor.add(hub);

  // 4. Three Aerodynamic Twisted Rotor Blades
  const bladeLength = rotorDiameter / 2;
  const bladeMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.25 });
  const tipMat = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.3 }); // Red safety tip

  for (let i = 0; i < 3; i++) {
    const bladeAngle = (i * Math.PI * 2) / 3;
    const bladeGroup = new THREE.Group();
    bladeGroup.rotation.z = bladeAngle;

    // Main airfoil blade body
    const bladeGeo = new THREE.BoxGeometry(0.24, bladeLength * 0.8, 0.08);
    const bladeMesh = new THREE.Mesh(bladeGeo, bladeMat);
    bladeMesh.position.y = bladeLength * 0.4 + 0.3;
    bladeMesh.rotation.y = 0.15; // Aerodynamic pitch angle
    bladeMesh.castShadow = true;
    bladeGroup.add(bladeMesh);

    // Red high-visibility tip
    const tipGeo = new THREE.BoxGeometry(0.22, bladeLength * 0.2, 0.07);
    const tipMesh = new THREE.Mesh(tipGeo, tipMat);
    tipMesh.position.y = bladeLength * 0.9 + 0.3;
    tipMesh.rotation.y = 0.15;
    bladeGroup.add(tipMesh);

    rotor.add(bladeGroup);
  }

  group.add(rotor);
  return { group, rotor };
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

  const wallMat = new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.8, wireframe });
  
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
    new THREE.MeshStandardMaterial({ color: 0x475569, roughness: 0.95 })
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
  const cradleMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.7 });

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

    // Domed end caps
    const capGeo = new THREE.SphereGeometry(tankRadius, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2);
    const capFront = new THREE.Mesh(capGeo, tankMat);
    capFront.rotation.x = Math.PI / 2;
    capFront.position.z = tankLength / 2;
    tankGroup.add(capFront);

    const capBack = new THREE.Mesh(capGeo, tankMat);
    capBack.rotation.x = -Math.PI / 2;
    capBack.position.z = -tankLength / 2;
    tankGroup.add(capBack);

    // Inspection dome & safety pressure relief valve
    const manholeGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.4, 12);
    const manhole = new THREE.Mesh(manholeGeo, cradleMat);
    manhole.position.set(0, tankRadius + 0.15, 0);
    tankGroup.add(manhole);

    // Concrete Support Saddles
    const saddle1 = new THREE.Mesh(new THREE.BoxGeometry(tankRadius * 2.2, 0.6, 0.8), cradleMat);
    saddle1.position.set(xPos, 0.3, -tankLength * 0.3);
    saddle1.castShadow = true;
    farm.add(saddle1);

    const saddle2 = new THREE.Mesh(new THREE.BoxGeometry(tankRadius * 2.2, 0.6, 0.8), cradleMat);
    saddle2.position.set(xPos, 0.3, tankLength * 0.3);
    saddle2.castShadow = true;
    farm.add(saddle2);

    farm.add(tankGroup);
  }

  // 3. Fuel Distribution Header Pipe
  const pipeMat = new THREE.MeshStandardMaterial({ color: 0xfbbf24, metalness: 0.6, roughness: 0.3 });
  const headerPipeGeo = new THREE.CylinderGeometry(0.12, 0.12, bermWidth - 2, 12);
  headerPipeGeo.rotateZ(Math.PI / 2);
  const headerPipe = new THREE.Mesh(headerPipeGeo, pipeMat);
  headerPipe.position.set(0, 1.8, bermDepth / 2 - 1.2);
  farm.add(headerPipe);

  return farm;
}

/**
 * Creates a geodesic satellite communications radome on an elevated platform.
 */
export function createRadome(radius: number = 2.0, wireframe: boolean = false): THREE.Group {
  const domeGroup = new THREE.Group();

  // Elevated steel platform
  const platMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.6, roughness: 0.5 });
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
// TERRAIN BUILDER (Subtle, realistic polar topography)
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

    // Keep the immediate station foundation (central 50x40m) relatively level
    const distCenter = Math.sqrt((x * 0.8) ** 2 + (z * 1.1) ** 2);
    const flatFactor = Math.min(1.0, Math.max(0.0, (distCenter - 22) / 30));

    let height = 0;
    if (terrainType === 'BEDROCK_ICE') {
      // Bharati: Larsemann Hills coastal granite knolls and snowdrifts
      height = (Math.sin(x * 0.05) * 2.2 + Math.cos(z * 0.06) * 1.8 + Math.sin((x + z) * 0.03) * 3.5) * flatFactor;
      // Slight coastal depression to the northwest
      if (x < -20 && z < -15) {
        height -= 2.5 * flatFactor;
      }
    } else if (terrainType === 'ROCKY_OASIS') {
      // Maitri: Schirmacher Oasis rugged rocky undulating ridge
      height = (Math.sin(x * 0.08) * 3.2 + Math.cos(z * 0.09) * 2.8 + Math.sin(x * 0.15) * 1.2) * flatFactor;
      // Lake Priyadarshini depression to the northeast
      if (x > 18 && z > 15) {
        height -= 3.2 * flatFactor;
      }
    } else {
      // Himadri: Ny-Ålesund gentle coastal Arctic tundra with snowdrifts
      height = (Math.sin(x * 0.04) * 1.2 + Math.cos(z * 0.04) * 0.9) * flatFactor;
    }

    pos.setY(i, height);
  }
  geo.computeVertexNormals();

  let groundColor = 0xdbeafe; // Snowy polar ice
  let roughness = 0.85;
  let metalness = 0.05;

  if (terrainType === 'ROCKY_OASIS') {
    groundColor = 0x78716c; // Schirmacher Oasis warm stone grey/brown
    roughness = 0.95;
    metalness = 0.02;
  } else if (terrainType === 'ARCTIC_TUNDRA') {
    groundColor = 0xcfd8dc; // High Arctic tundra gravel & snow
    roughness = 0.9;
  }

  const mat = new THREE.MeshStandardMaterial({
    color: groundColor,
    roughness,
    metalness,
    wireframe
  });

  const terrainMesh = new THREE.Mesh(geo, mat);
  terrainMesh.position.y = -0.1;
  terrainMesh.receiveShadow = true;
  terrainGroup.add(terrainMesh);

  // 1. SCATTERED GRANITE BEDROCK NUNATAK BOULDERS
  const boulderMat = new THREE.MeshStandardMaterial({
    color: 0x334155, // Dark Antarctic gneiss / charnockite bedrock
    roughness: 0.9,
    metalness: 0.15,
    flatShading: true
  });
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

  // Octagonal concrete / steel reinforced landing platform
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

  // 'H' marking geometry
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

  // 8 Perimeter LED landing beacons (pulsing green/amber)
  const beaconMat = new THREE.MeshStandardMaterial({
    color: 0x10b981, // Emerald landing beacon
    emissive: 0x10b981,
    emissiveIntensity: 0.9,
    roughness: 0.2
  });
  const pylonMat = new THREE.MeshStandardMaterial({ color: 0x1e293b });
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
      color: 0x0284c7, // Glacial blue lake ice
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

  const isArchMode = activeLayer === 'ARCHITECTURE';
  const hullOpacity = isArchMode ? 0.96 : 0.42;

  // Material Palettes (bof Architekten / NCPOR Architectural Specs)
  const hullWhiteMat = new THREE.MeshStandardMaterial({
    color: 0xf8fafc,
    roughness: 0.35,
    metalness: 0.65,
    transparent: !isArchMode,
    opacity: hullOpacity,
    wireframe
  });

  const orangeStripeMat = new THREE.MeshStandardMaterial({
    color: 0xea580c, // Bharati expedition safety orange accent
    roughness: 0.4,
    metalness: 0.5,
    transparent: !isArchMode,
    opacity: hullOpacity,
    wireframe
  });

  const darkSteelMat = new THREE.MeshStandardMaterial({
    color: 0x334155,
    roughness: 0.5,
    metalness: 0.8,
    wireframe
  });

  // Warm tungsten glowing interior glass (contrasting against dark polar night)
  const glassMat = new THREE.MeshStandardMaterial({
    color: 0x1e293b,
    emissive: 0xfef08a, // Warm 2700K tungsten glow from interior labs/habitation
    emissiveIntensity: isArchMode ? 0.85 : 0.6,
    roughness: 0.12,
    metalness: 0.4,
    transparent: true,
    opacity: isArchMode ? 0.85 : 0.5,
    wireframe
  });

  // --- A. HEAVY STEEL FOUNDATION STILTS (24 Heavy Columns with Cross-Bracing) ---
  const stiltGroup = new THREE.Group();
  const colHeight = 3.6;
  const colRadius = 0.32;
  const colGeo = new THREE.CylinderGeometry(colRadius, colRadius, colHeight, 12);
  const footingGeo = new THREE.BoxGeometry(1.2, 0.4, 1.2);
  const footingMat = new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.9 });

  const stiltGridX = [-20, -14, -8, -2, 4, 10, 16, 20];
  const stiltGridZ = [-10, 0, 10];

  stiltGridX.forEach(x => {
    stiltGridZ.forEach(z => {
      // Stilt column
      const col = new THREE.Mesh(colGeo, darkSteelMat);
      col.position.set(x, colHeight / 2, z);
      col.castShadow = true;
      stiltGroup.add(col);

      // Bedrock concrete footing pad
      const footing = new THREE.Mesh(footingGeo, footingMat);
      footing.position.set(x, 0.2, z);
      footing.receiveShadow = true;
      stiltGroup.add(footing);
    });
  });

  // Longitudinal & transverse diagonal lattice bracing
  const braceMat = new THREE.LineBasicMaterial({ color: 0x475569, linewidth: 2 });
  for (let i = 0; i < stiltGridX.length - 1; i++) {
    const x1 = stiltGridX[i];
    const x2 = stiltGridX[i + 1];
    [-10, 10].forEach(z => {
      const p1 = [new THREE.Vector3(x1, 0.3, z), new THREE.Vector3(x2, colHeight, z)];
      const p2 = [new THREE.Vector3(x1, colHeight, z), new THREE.Vector3(x2, 0.3, z)];
      stiltGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(p1), braceMat));
      stiltGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(p2), braceMat));
    });
  }
  architectureGroup.add(stiltGroup);

  // --- B. AERODYNAMIC MAIN HULL SUPERSTRUCTURE ---
  // The Bharati envelope consists of an elevated, faceted containerized volume
  const hullGroup = new THREE.Group();

  // Deck 1 (Lower Engineering Level, +3.6m to +7.2m)
  const d1Length = 43;
  const d1Width = 24;
  const d1Height = 3.6;
  const d1Mesh = new THREE.Mesh(new THREE.BoxGeometry(d1Length, d1Height, d1Width), hullWhiteMat);
  d1Mesh.position.set(0, 3.6 + d1Height / 2, 0);
  d1Mesh.castShadow = true;
  d1Mesh.receiveShadow = true;
  hullGroup.add(d1Mesh);

  // Orange identification band between Deck 1 and Deck 2
  const bandMesh = new THREE.Mesh(new THREE.BoxGeometry(d1Length + 0.1, 0.5, d1Width + 0.1), orangeStripeMat);
  bandMesh.position.set(0, 7.2, 0);
  hullGroup.add(bandMesh);

  // Deck 2 (Middle Habitation & Operations Level, +7.2m to +10.8m)
  const d2Length = 41;
  const d2Width = 22;
  const d2Height = 3.6;
  const d2Mesh = new THREE.Mesh(new THREE.BoxGeometry(d2Length, d2Height, d2Width), hullWhiteMat);
  d2Mesh.position.set(0, 7.2 + d2Height / 2, 0);
  d2Mesh.castShadow = true;
  hullGroup.add(d2Mesh);

  // Ribbon Windows on Habitation Level (Operations bridge & living quarters)
  const winFront = new THREE.Mesh(new THREE.BoxGeometry(32, 1.2, 0.2), glassMat);
  winFront.position.set(0, 8.8, d2Width / 2 + 0.05);
  hullGroup.add(winFront);

  const winBack = new THREE.Mesh(new THREE.BoxGeometry(32, 1.2, 0.2), glassMat);
  winBack.position.set(0, 8.8, -d2Width / 2 - 0.05);
  hullGroup.add(winBack);

  // Deck 3 (Upper Science & Observation Deck, +10.8m to +14.2m)
  const d3Length = 28;
  const d3Width = 16;
  const d3Height = 3.2;
  const d3Mesh = new THREE.Mesh(new THREE.BoxGeometry(d3Length, d3Height, d3Width), hullWhiteMat);
  d3Mesh.position.set(2, 10.8 + d3Height / 2, 0);
  d3Mesh.castShadow = true;
  hullGroup.add(d3Mesh);

  // Upper Panoramic Science Observation Bridge Window (North-facing towards sea)
  const obsWindow = new THREE.Mesh(new THREE.BoxGeometry(0.2, 1.8, 14), glassMat);
  obsWindow.position.set(d3Length / 2 + 2.05, 12.4, 0);
  hullGroup.add(obsWindow);

  // Aerodynamic nose chamfer (Windward aerodynamic bevel on northwest edge)
  const noseGeo = new THREE.CylinderGeometry(4.0, 4.0, 7.2, 8, 1, false, 0, Math.PI);
  const noseMesh = new THREE.Mesh(noseGeo, hullWhiteMat);
  noseMesh.rotation.y = -Math.PI / 2;
  noseMesh.position.set(d1Length / 2 - 1, 7.2, 0);
  hullGroup.add(noseMesh);

  // Perimeter Roof Safety Railings on Deck 3
  const railGeo = new THREE.CylinderGeometry(15, 15, 1.0, 16, 1, true);
  const rail = new THREE.Mesh(railGeo, new THREE.MeshBasicMaterial({ color: 0x94a3b8, wireframe: true }));
  rail.position.set(2, 14.5, 0);
  hullGroup.add(rail);

  architectureGroup.add(hullGroup);

  // --- C. ROOFTOP RADOME & COMMUNICATIONS ---
  const radome = createRadome(2.4, wireframe);
  radome.position.set(6, 14.0, 0);
  architectureGroup.add(radome);

  // Meteorological instrumentation mast
  const mastGeo = new THREE.CylinderGeometry(0.08, 0.12, 6.0, 8);
  const mast = new THREE.Mesh(mastGeo, darkSteelMat);
  mast.position.set(-6, 17.0, -3);
  architectureGroup.add(mast);

  // --- D. EXTERIOR SEAWATER INTAKE & PIPE BRIDGE ---
  const pumpHouse = new THREE.Mesh(
    new THREE.BoxGeometry(4.5, 3.2, 4.0),
    new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.5 })
  );
  pumpHouse.position.set(-32, 1.6, -24);
  pumpHouse.castShadow = true;
  pumpHouse.userData = { deviceId: 'bh_water_freeze_prot', label: 'Seawater Intake & Pump' };
  interactiveMeshes.set('bh_water_freeze_prot', pumpHouse);
  architectureGroup.add(pumpHouse);

  // Insulated seawater pipe bridge from pump house to station engineering deck
  const pipePoints = [
    new THREE.Vector3(-32, 2.8, -24),
    new THREE.Vector3(-24, 3.2, -18),
    new THREE.Vector3(-14, 4.2, -12)
  ];
  const pipeGeo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pipePoints), 20, 0.22, 8, false);
  const pipeMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, roughness: 0.3 });
  const intakePipe = new THREE.Mesh(pipeGeo, pipeMat);
  architectureGroup.add(intakePipe);

  // --- E. EXTERNAL FUEL STORAGE FARM ---
  const fuelFarm = createFuelFarm(wireframe);
  fuelFarm.position.set(28, 0, -18);
  fuelFarm.userData = { deviceId: 'diesel_generator_1', label: 'Bulk Diesel Fuel Storage' };
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

  return { architectureGroup, terrainMesh, interactiveMeshes, turbines };
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

  const isArchMode = activeLayer === 'ARCHITECTURE';
  const blockOpacity = isArchMode ? 0.95 : 0.45;

  // Maitri Color Palette (High-visibility Antarctic Yellow, Navy Blue Trim)
  const yellowBlockMat = new THREE.MeshStandardMaterial({
    color: 0xf59e0b, // Maitri Antarctic Yellow
    roughness: 0.45,
    metalness: 0.3,
    transparent: !isArchMode,
    opacity: blockOpacity,
    wireframe
  });

  const blueTrimMat = new THREE.MeshStandardMaterial({
    color: 0x1e3a8a, // Navy trim
    roughness: 0.4,
    metalness: 0.5,
    wireframe
  });

  const spineMat = new THREE.MeshStandardMaterial({
    color: 0xe2e8f0, // Insulated galvanized transit corridor
    roughness: 0.35,
    metalness: 0.6,
    transparent: !isArchMode,
    opacity: blockOpacity,
    wireframe
  });

  // --- A. THE ICONIC CENTRAL ENCLOSED SPINAL CORRIDOR ---
  // Connects living blocks to utility modules and powerhouse
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
    const postMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.7 });
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

  // Roof & Blue accent trim
  const trimA = new THREE.Mesh(new THREE.BoxGeometry(14.2, 0.4, 8.2), blueTrimMat);
  trimA.position.set(-10, 5.4 + 0.4, -6.5);
  architectureGroup.add(trimA);

  // Living Block B (Quarters & Recreation)
  const blockB = new THREE.Mesh(blockGeo, yellowBlockMat);
  blockB.position.set(10, 2.7 + 0.4, -6.5);
  blockB.castShadow = true;
  blockB.receiveShadow = true;
  blockB.userData = { deviceId: 'mt_galley_kitchen', label: 'Living Block B (Quarters)' };
  architectureGroup.add(blockB);

  const trimB = new THREE.Mesh(new THREE.BoxGeometry(14.2, 0.4, 8.2), blueTrimMat);
  trimB.position.set(10, 5.4 + 0.4, -6.5);
  architectureGroup.add(trimB);

  // --- C. DEDICATED POWER HOUSE (Tri-Diesel Generators & Switchboards) ---
  const powerHouseGeo = new THREE.BoxGeometry(11, 4.8, 9);
  const powerHouse = new THREE.Mesh(powerHouseGeo, new THREE.MeshStandardMaterial({
    color: 0x64748b, // Industrial slate power house
    roughness: 0.5,
    metalness: 0.5,
    wireframe
  }));
  powerHouse.position.set(-11, 2.4 + 0.4, 7.5);
  powerHouse.castShadow = true;
  powerHouse.userData = { deviceId: 'mt_diesel', label: 'Maitri Power House (3x62.5 kW Gensets)' };
  interactiveMeshes.set('mt_diesel', powerHouse);
  architectureGroup.add(powerHouse);

  // 3 Vertical Stainless Steel Generator Exhaust Stacks
  const stackMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9, roughness: 0.2 });
  for (let s = 0; s < 3; s++) {
    const stackGeo = new THREE.CylinderGeometry(0.16, 0.16, 2.8, 12);
    const stack = new THREE.Mesh(stackGeo, stackMat);
    stack.position.set(-13 + s * 2.0, 5.8, 11);
    stack.castShadow = true;
    architectureGroup.add(stack);

    // Weather rain cap
    const capGeo = new THREE.ConeGeometry(0.32, 0.25, 12);
    const cap = new THREE.Mesh(capGeo, stackMat);
    cap.position.set(-13 + s * 2.0, 7.3, 11);
    architectureGroup.add(cap);
  }

  // --- D. CENTRAL BOILER & THERMAL HEATING LOOP ---
  const boilerHouse = new THREE.Mesh(
    new THREE.BoxGeometry(7, 3.8, 6),
    new THREE.MeshStandardMaterial({ color: 0xb45309, roughness: 0.4, metalness: 0.4, wireframe })
  );
  boilerHouse.position.set(0, 1.9 + 0.4, 6.0);
  boilerHouse.castShadow = true;
  boilerHouse.userData = { deviceId: 'mt_heating_primary', label: 'Central Boiler & Heating Aux' };
  interactiveMeshes.set('mt_heating_primary', boilerHouse);
  architectureGroup.add(boilerHouse);

  // Exterior elevated insulated thermal pipe rack running across the spine
  const pipePoints = [
    new THREE.Vector3(0, 4.0, 6.0),
    new THREE.Vector3(0, 4.0, 0),
    new THREE.Vector3(-10, 4.0, 0),
    new THREE.Vector3(-10, 4.0, -2.5)
  ];
  const heatPipeGeo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pipePoints), 16, 0.16, 8, false);
  const heatPipe = new THREE.Mesh(heatPipeGeo, new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.4 }));
  architectureGroup.add(heatPipe);

  // --- E. LAKE PRIYADARSHINI WATER PUMP HOUSE & OVERLAND PIPELINE ---
  const waterPumpHouse = new THREE.Mesh(
    new THREE.BoxGeometry(5.5, 3.2, 5),
    new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.4, metalness: 0.5 })
  );
  waterPumpHouse.position.set(26, 1.6, 22);
  waterPumpHouse.castShadow = true;
  waterPumpHouse.userData = { deviceId: 'mt_pribarshini_water', label: 'Lake Priyadarshini Water Pump' };
  interactiveMeshes.set('mt_pribarshini_water', waterPumpHouse);
  architectureGroup.add(waterPumpHouse);

  // Long insulated water pipeline on A-frame support trestles
  const waterPipePoints = [
    new THREE.Vector3(26, 2.0, 22),
    new THREE.Vector3(18, 2.2, 14),
    new THREE.Vector3(10, 2.4, 6),
    new THREE.Vector3(0, 2.4, 3)
  ];
  const waterPipeGeo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(waterPipePoints), 24, 0.18, 8, false);
  const waterPipe = new THREE.Mesh(waterPipeGeo, new THREE.MeshStandardMaterial({ color: 0x38bdf8, roughness: 0.3 }));
  architectureGroup.add(waterPipe);

  // A-Frame pipe supports along the path
  const trestleMat = new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.7 });
  for (let t = 1; t <= 3; t++) {
    const trestlePos = new THREE.Vector3().lerpVectors(waterPipePoints[0], waterPipePoints[3], t / 4);
    const trestle = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.15, trestlePos.y, 6), trestleMat);
    trestle.position.set(trestlePos.x, trestlePos.y / 2, trestlePos.z);
    architectureGroup.add(trestle);
  }

  // --- F. GEOMAGNETIC OBSERVATORY HUT (Non-magnetic isolated hut) ---
  const geomagHut = new THREE.Mesh(
    new THREE.BoxGeometry(4.5, 3.0, 4.5),
    new THREE.MeshStandardMaterial({ color: 0xa16207, roughness: 0.85 })
  );
  geomagHut.position.set(22, 1.5, -16);
  geomagHut.castShadow = true;
  geomagHut.userData = { deviceId: 'mt_geomag_lab', label: 'Geomagnetic & Seismic Lab' };
  interactiveMeshes.set('mt_geomag_lab', geomagHut);
  architectureGroup.add(geomagHut);

  // --- G. RENEWABLE GENERATION ---
  // Solar PV rack
  const solarRack = createSolarRack(12, 4.5, 38, wireframe);
  solarRack.position.set(-22, 0, -12);
  solarRack.userData = { deviceId: 'node_mt_solar', label: 'Maitri Solar PV Array (18 kWp)' };
  interactiveMeshes.set('node_mt_solar', solarRack);
  architectureGroup.add(solarRack);

  // Wind turbine
  const turbine = createWindTurbine(13, 6.0, wireframe);
  turbine.group.position.set(-22, 0, 14);
  turbine.group.userData = { deviceId: 'node_mt_wind', label: 'Maitri Wind Turbine (15 kW)' };
  interactiveMeshes.set('node_mt_wind', turbine.group);
  turbines.push({ rotorGroup: turbine.rotor, speedMultiplier: 1.0 });
  architectureGroup.add(turbine.group);

  // Terrain (Schirmacher Oasis rocky ground + Lake Priyadarshini water)
  const terrainMesh = buildPolarTerrain('ROCKY_OASIS', wireframe);

  return { architectureGroup, terrainMesh, interactiveMeshes, turbines };
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

  const isArchMode = activeLayer === 'ARCHITECTURE';
  const wallOpacity = isArchMode ? 0.95 : 0.45;

  // Traditional Nordic Ny-Ålesund Architecture (Falun Red Timber, Slate Pitch Roof, White Trim)
  const redTimberMat = new THREE.MeshStandardMaterial({
    color: 0x991b1b, // Nordic Falun Red
    roughness: 0.65,
    metalness: 0.1,
    transparent: !isArchMode,
    opacity: wallOpacity,
    wireframe
  });

  const whiteTrimMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.35,
    metalness: 0.2,
    wireframe
  });

  const darkRoofMat = new THREE.MeshStandardMaterial({
    color: 0x1e293b, // Dark charcoal standing-seam metal roof
    roughness: 0.45,
    metalness: 0.5,
    wireframe
  });

  const windowGlassMat = new THREE.MeshStandardMaterial({
    color: 0x0284c7,
    emissive: 0xfef08a, // Warm interior laboratory lighting glow
    emissiveIntensity: 0.3,
    roughness: 0.1,
    metalness: 0.9,
    transparent: true,
    opacity: isArchMode ? 0.7 : 0.25
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

  // Horizontal Floor Divider Trim (Separates Ground Lab from Upper Living)
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

  // --- C. MULTI-PANE GLAZED WINDOWS WITH WHITE MULLIONS ---
  // Ground Floor Science Lab Windows
  for (let x = -5; x <= 5; x += 5) {
    const win = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.4, 0.15), windowGlassMat);
    win.position.set(x, 2.0, houseDepth / 2 + 0.08);
    architectureGroup.add(win);

    const frame = new THREE.Mesh(new THREE.BoxGeometry(1.8, 1.6, 0.12), whiteTrimMat);
    frame.position.copy(win.position);
    architectureGroup.add(frame);
  }

  // Upper Floor Living Quarters Windows
  for (let x = -5; x <= 5; x += 5) {
    const win = new THREE.Mesh(new THREE.BoxGeometry(1.4, 1.2, 0.15), windowGlassMat);
    win.position.set(x, 5.4, houseDepth / 2 + 0.08);
    architectureGroup.add(win);
  }

  // --- D. RAISED WOODEN ENTRANCE PORCH & TUNDRA BOARDWALK ---
  const porchMat = new THREE.MeshStandardMaterial({ color: 0x78350f, roughness: 0.9 });
  const porch = new THREE.Mesh(new THREE.BoxGeometry(4.0, 0.3, 3.0), porchMat);
  porch.position.set(0, 0.3, houseDepth / 2 + 1.5);
  porch.receiveShadow = true;
  architectureGroup.add(porch);

  // Tundra protection boardwalk extending towards the settlement path
  const boardwalk = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.25, 14), porchMat);
  boardwalk.position.set(0, 0.25, houseDepth / 2 + 8.5);
  boardwalk.receiveShadow = true;
  architectureGroup.add(boardwalk);

  // --- E. ROOFTOP ATMOSPHERIC SCIENCE PLATFORM & RADOME ---
  // Atmospheric aerosol spectrometer chimney
  const aerosolStack = new THREE.Mesh(
    new THREE.CylinderGeometry(0.12, 0.12, 2.5, 12),
    new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8 })
  );
  aerosolStack.position.set(-4, totalWallHeight + roofHeight + 0.5, 0);
  aerosolStack.userData = { deviceId: 'hm_aerosol_spectrometer', label: 'Aerosol Spectrometer Sampling Inlet' };
  interactiveMeshes.set('hm_aerosol_spectrometer', aerosolStack);
  architectureGroup.add(aerosolStack);

  // Rooftop Satellite Radome
  const radome = createRadome(1.5, wireframe);
  radome.position.set(4, totalWallHeight + roofHeight - 1.2, 0);
  radome.userData = { deviceId: 'hm_satellite_uplink', label: 'Ny-Ålesund Satellite Link' };
  interactiveMeshes.set('hm_satellite_uplink', radome);
  architectureGroup.add(radome);

  // --- F. DISTRICT ENERGY INTERCONNECTION (Ny-Ålesund 400V Grid & Heating Tie-in) ---
  const districtJunction = new THREE.Mesh(
    new THREE.BoxGeometry(2.4, 2.0, 1.8),
    new THREE.MeshStandardMaterial({ color: 0x059669, roughness: 0.5 })
  );
  districtJunction.position.set(-11, 1.0, -4);
  districtJunction.castShadow = true;
  districtJunction.userData = { deviceId: 'node_hm_main_bus', label: 'District Energy & 400V Tie-in' };
  interactiveMeshes.set('node_hm_main_bus', districtJunction);
  architectureGroup.add(districtJunction);

  // Insulated conduit running from settlement into the building
  const conduitGeo = new THREE.CylinderGeometry(0.18, 0.18, 5, 8);
  conduitGeo.rotateZ(Math.PI / 2);
  const conduit = new THREE.Mesh(conduitGeo, new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.5 }));
  conduit.position.set(-8.5, 0.4, -4);
  architectureGroup.add(conduit);

  // --- G. RENEWABLES & EXPEDITION GEAR ---
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

  // Terrain (Ny-Ålesund Arctic tundra)
  const terrainMesh = buildPolarTerrain('ARCTIC_TUNDRA', wireframe);

  return { architectureGroup, terrainMesh, interactiveMeshes, turbines };
}
