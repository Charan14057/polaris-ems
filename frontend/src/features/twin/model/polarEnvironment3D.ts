/**
 * POLARIS-EMS — Real-World Polar Atmospheric 3D Environment Engine
 * Photorealistic Celestial Sky Dome, Distant Mountain Nunataks, Aurora Curtains,
 * Volumetric Snow Flurries & Dynamic Weather Particles for Three.js Digital Twin.
 */

import * as THREE from 'three';

export interface PolarEnvironmentHandles {
  skyDome: THREE.Mesh;
  mountainRange: THREE.Group;
  starField: THREE.Points;
  auroraMesh: THREE.Mesh;
  snowParticles: THREE.Points;
  exhaustParticles: THREE.Points;
  beaconLights: THREE.Mesh[];
  update: (deltaSeconds: number, windSpeedMs: number, isBlizzard: boolean, dieselActive: boolean) => void;
  dispose: () => void;
}

export function createPolarEnvironment(scene: THREE.Scene): PolarEnvironmentHandles {
  const envGroup = new THREE.Group();
  scene.add(envGroup);

  // 1. CELESTIAL SKY DOME (High-Latitude Twilight / Horizon Scattering)
  const skyRadius = 240;
  const skyGeo = new THREE.SphereGeometry(skyRadius, 32, 24, 0, Math.PI * 2, 0, Math.PI / 2);
  skyGeo.scale(-1, 1, 1); // Render inside

  // Procedural gradient canvas texture for high-altitude polar sky
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    const grad = ctx.createLinearGradient(0, 0, 0, 512);
    grad.addColorStop(0.0, '#040714'); // Deep cosmic arctic navy zenith
    grad.addColorStop(0.4, '#09152e'); // Cold twilight blue
    grad.addColorStop(0.75, '#122b4a'); // Cyan/navy atmospheric transition
    grad.addColorStop(0.92, '#1e3a5f'); // Horizon glow
    grad.addColorStop(1.0, '#2d4a6e'); // Distant icy horizon line
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 512);
  }
  const skyTexture = new THREE.CanvasTexture(canvas);

  const skyMat = new THREE.MeshBasicMaterial({
    map: skyTexture,
    side: THREE.BackSide,
    depthWrite: false
  });
  const skyDome = new THREE.Mesh(skyGeo, skyMat);
  skyDome.position.y = -5;
  envGroup.add(skyDome);

  // 2. DISTANT ANTARCTIC NUNATAK MOUNTAIN RIDGES (360-Degree Silhouette)
  const mountainGroup = new THREE.Group();
  const numPeaks = 48;
  const mountainRadius = 210;

  const mtnGeo = new THREE.BufferGeometry();
  const mtnVertices: number[] = [];
  const mtnIndices: number[] = [];

  // Generate a ring of jagged peaks
  for (let i = 0; i <= numPeaks; i++) {
    const angle = (i / numPeaks) * Math.PI * 2;
    const distVariation = mountainRadius + Math.sin(i * 1.7) * 15 + Math.cos(i * 3.1) * 10;
    const x = Math.sin(angle) * distVariation;
    const z = Math.cos(angle) * distVariation;

    // Peak height variation with dramatic jagged nunataks
    const peakHeight = Math.max(12, 28 + Math.sin(i * 1.4) * 18 + Math.cos(i * 2.8) * 12 + ((i % 5 === 0) ? 22 : 0));
    
    // Bottom vertex at horizon
    mtnVertices.push(x, 0, z);
    // Peak vertex
    mtnVertices.push(x * 0.96, peakHeight, z * 0.96);
  }

  for (let i = 0; i < numPeaks; i++) {
    const b1 = i * 2;
    const t1 = i * 2 + 1;
    const b2 = (i + 1) * 2;
    const t2 = (i + 1) * 2 + 1;

    mtnIndices.push(b1, t1, b2);
    mtnIndices.push(b2, t1, t2);
  }

  mtnGeo.setAttribute('position', new THREE.Float32BufferAttribute(mtnVertices, 3));
  mtnGeo.setIndex(mtnIndices);
  mtnGeo.computeVertexNormals();

  const mtnMat = new THREE.MeshStandardMaterial({
    color: 0x1e293b, // Dark nunatak bedrock with snow dust
    roughness: 0.9,
    metalness: 0.1,
    flatShading: true
  });
  const mountains = new THREE.Mesh(mtnGeo, mtnMat);
  mountainGroup.add(mountains);

  // Snow-capped peak highlight overlay
  const snowCapMat = new THREE.MeshStandardMaterial({
    color: 0xe2e8f0, // Glacial summit ice
    roughness: 0.4,
    metalness: 0.3,
    flatShading: true
  });
  const snowCapMesh = new THREE.Mesh(mtnGeo, snowCapMat);
  snowCapMesh.position.y = 1.5;
  snowCapMesh.scale.set(0.99, 1.05, 0.99);
  mountainGroup.add(snowCapMesh);

  envGroup.add(mountainGroup);

  // 3. POLAR STARFIELD (Twinkling southern/northern constellations)
  const starCount = 1200;
  const starGeo = new THREE.BufferGeometry();
  const starPositions = new Float32Array(starCount * 3);
  const starColors = new Float32Array(starCount * 3);

  for (let i = 0; i < starCount; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.random() * (Math.PI / 2.2); // Upper sky only
    const r = 230 + Math.random() * 8;

    starPositions[i * 3] = r * Math.sin(phi) * Math.sin(theta);
    starPositions[i * 3 + 1] = r * Math.cos(phi) + 10;
    starPositions[i * 3 + 2] = r * Math.sin(phi) * Math.cos(theta);

    // Subtle star color temperatures (ice blue, white, warm amber)
    const colType = Math.random();
    if (colType > 0.8) {
      starColors[i * 3] = 0.7; starColors[i * 3 + 1] = 0.85; starColors[i * 3 + 2] = 1.0;
    } else if (colType > 0.6) {
      starColors[i * 3] = 1.0; starColors[i * 3 + 1] = 0.9; starColors[i * 3 + 2] = 0.7;
    } else {
      starColors[i * 3] = 1.0; starColors[i * 3 + 1] = 1.0; starColors[i * 3 + 2] = 1.0;
    }
  }

  starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
  starGeo.setAttribute('color', new THREE.BufferAttribute(starColors, 3));

  const starMat = new THREE.PointsMaterial({
    size: 1.4,
    vertexColors: true,
    transparent: true,
    opacity: 0.85,
    depthWrite: false
  });
  const starField = new THREE.Points(starGeo, starMat);
  envGroup.add(starField);

  // 4. DYNAMIC AURORA CURTAIN (Aurora Australis / Borealis)
  const auroraSegments = 40;
  const auroraGeo = new THREE.PlaneGeometry(160, 45, auroraSegments, 4);
  auroraGeo.rotateX(Math.PI / 3);

  const auroraMat = new THREE.MeshBasicMaterial({
    color: 0x34d399, // Luminous Emerald-Cyan Polar Aurora
    transparent: true,
    opacity: 0.35,
    side: THREE.DoubleSide,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  });
  const auroraMesh = new THREE.Mesh(auroraGeo, auroraMat);
  auroraMesh.position.set(0, 95, -70);
  envGroup.add(auroraMesh);

  // 5. VOLUMETRIC POLAR SNOW STORM PARTICLES
  const snowCount = 1400;
  const snowGeo = new THREE.BufferGeometry();
  const snowPositions = new Float32Array(snowCount * 3);
  const snowVelocities = new Float32Array(snowCount * 3);

  for (let i = 0; i < snowCount; i++) {
    snowPositions[i * 3] = (Math.random() - 0.5) * 140;
    snowPositions[i * 3 + 1] = Math.random() * 45;
    snowPositions[i * 3 + 2] = (Math.random() - 0.5) * 140;

    // Velocity: downward + wind drift
    snowVelocities[i * 3] = -0.2 - Math.random() * 0.4; // Initial drift X
    snowVelocities[i * 3 + 1] = -0.15 - Math.random() * 0.25; // Fall Y
    snowVelocities[i * 3 + 2] = -0.05 + Math.random() * 0.1; // Drift Z
  }

  snowGeo.setAttribute('position', new THREE.BufferAttribute(snowPositions, 3));

  const snowMat = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 0.65,
    transparent: true,
    opacity: 0.75,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });
  const snowParticles = new THREE.Points(snowGeo, snowMat);
  scene.add(snowParticles);

  // 6. POWERHOUSE EXHAUST PARTICLES (Thermal plume when generators run)
  const exhaustCount = 80;
  const exhaustGeo = new THREE.BufferGeometry();
  const exhaustPositions = new Float32Array(exhaustCount * 3);
  const exhaustLifetimes = new Float32Array(exhaustCount);

  for (let i = 0; i < exhaustCount; i++) {
    exhaustPositions[i * 3] = 16.0 + (Math.random() - 0.5) * 0.8;
    exhaustPositions[i * 3 + 1] = 14.5 + Math.random() * 6.0;
    exhaustPositions[i * 3 + 2] = -12.0 + (Math.random() - 0.5) * 0.8;
    exhaustLifetimes[i] = Math.random();
  }

  exhaustGeo.setAttribute('position', new THREE.BufferAttribute(exhaustPositions, 3));

  const exhaustMat = new THREE.PointsMaterial({
    color: 0x94a3b8,
    size: 1.2,
    transparent: true,
    opacity: 0.25,
    depthWrite: false
  });
  const exhaustParticles = new THREE.Points(exhaustGeo, exhaustMat);
  scene.add(exhaustParticles);

  // 7. BEACON LIGHTS LIST
  const beaconLights: THREE.Mesh[] = [];

  // Animation Update Function
  let auroraPhase = 0;
  let beaconTimer = 0;

  const update = (
    deltaSeconds: number,
    windSpeedMs: number,
    isBlizzard: boolean,
    dieselActive: boolean
  ) => {
    // A. Animate Aurora Undulation
    auroraPhase += deltaSeconds * 0.8;
    const aPos = auroraGeo.attributes.position;
    for (let i = 0; i < aPos.count; i++) {
      const u = aPos.getX(i);
      const wave = Math.sin(u * 0.05 + auroraPhase) * 6.0 + Math.cos(u * 0.12 - auroraPhase * 0.6) * 3.5;
      aPos.setZ(i, wave);
    }
    aPos.needsUpdate = true;
    auroraMat.opacity = isBlizzard ? 0.08 : 0.42;

    // B. Animate Falling & Blowing Snow
    const sPos = snowGeo.attributes.position;
    const windMultiplier = Math.max(1.0, windSpeedMs / 5.0) * (isBlizzard ? 2.8 : 1.0);
    const blowX = -0.35 * windMultiplier;
    const blowY = -(0.2 + (isBlizzard ? 0.35 : 0.05));

    for (let i = 0; i < snowCount; i++) {
      let x = sPos.getX(i) + blowX;
      let y = sPos.getY(i) + blowY;
      let z = sPos.getZ(i) + (Math.sin(x * 0.1) * 0.05);

      // Wrap around bounding box
      if (y < 0.1) {
        y = 42 + Math.random() * 5;
        x = 65 + Math.random() * 10;
        z = (Math.random() - 0.5) * 130;
      }
      if (x < -70) {
        x = 70;
      }

      sPos.setXYZ(i, x, y, z);
    }
    sPos.needsUpdate = true;
    snowMat.size = isBlizzard ? 0.95 : 0.6;
    snowMat.opacity = isBlizzard ? 0.95 : 0.65;

    // C. Animate Generator Exhaust Plumes
    exhaustParticles.visible = dieselActive;
    if (dieselActive) {
      const exPos = exhaustGeo.attributes.position;
      for (let i = 0; i < exhaustCount; i++) {
        let ey = exPos.getY(i) + 0.12;
        let ex = exPos.getX(i) + blowX * 0.18;
        if (ey > 22.0) {
          ey = 14.5;
          ex = 16.0 + (Math.random() - 0.5) * 0.8;
        }
        exPos.setXY(i, ex, ey);
      }
      exPos.needsUpdate = true;
    }

    // D. Animate Pulsing Aviation Warning Beacons (1 Hz sync blink)
    beaconTimer += deltaSeconds;
    const beaconState = Math.sin(beaconTimer * Math.PI * 2) > 0.0;
    beaconLights.forEach(b => {
      if (b.material && (b.material as THREE.MeshBasicMaterial).opacity !== undefined) {
        (b.material as THREE.MeshBasicMaterial).opacity = beaconState ? 1.0 : 0.2;
      }
    });
  };

  const dispose = () => {
    scene.remove(envGroup);
    scene.remove(snowParticles);
    scene.remove(exhaustParticles);
    skyGeo.dispose();
    skyMat.dispose();
    mtnGeo.dispose();
    mtnMat.dispose();
    starGeo.dispose();
    starMat.dispose();
    auroraGeo.dispose();
    auroraMat.dispose();
    snowGeo.dispose();
    snowMat.dispose();
    exhaustGeo.dispose();
    exhaustMat.dispose();
  };

  return {
    skyDome,
    mountainRange: mountainGroup,
    starField,
    auroraMesh,
    snowParticles,
    exhaustParticles,
    beaconLights,
    update,
    dispose
  };
}
