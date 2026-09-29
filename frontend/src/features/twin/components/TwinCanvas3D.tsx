/**
 * POLARIS-EMS — 3D Spatial Digital Twin Canvas
 * Phase 18: Operational 3D Digital Twin Engine
 * 
 * High-performance, photorealistic WebGL / Three.js 3D spatial microgrid visualizer.
 * Renders reference-aligned polar station architecture (Bharati, Maitri, Himadri),
 * directional 3D power flow conduits, equipment models, and circuit lineage.
 * 
 * STRICT EPISTEMIC CLASSIFICATION:
 * GEOMETRY BASIS: CONFIGURED / REPRESENTATIVE
 * NEVER CLAIM: EXACT FLOOR PLAN, SURVEYED MODEL, AS-BUILT MODEL.
 * ZERO duplicated physics: driven strictly by TwinViewModel.
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as THREE from 'three';
import { 
  RotateCcw, 
  Maximize2, 
  Eye, 
  Layers, 
  Zap, 
  ShieldAlert, 
  Info, 
  Compass,
  Box,
  Activity,
  Sliders,
  Focus,
  Sun,
  Wind,
  BatteryCharging,
  Thermometer
} from 'lucide-react';
import { TwinViewModel, TwinDeviceFilter } from '../model/twinTypes';
import { 
  STATION_SPATIAL_3D_PROFILES, 
  StationSpatial3DProfile, 
  SpatialObject3D, 
  PowerFlowPath3D 
} from '../model/spatialProfiles3D';
import { 
  buildBharatiStation, 
  buildMaitriStation, 
  buildHimadriStation 
} from '../model/stationMeshBuilders';
import { createPolarEnvironment, PolarEnvironmentHandles } from '../model/polarEnvironment3D';
import { createStructuralSteelMaterial } from '../model/pbrMaterialFactory';
import { ReferenceComparisonModal } from './ReferenceComparisonModal';
import { getStationPhoto, getPublicStationPhoto, normalizeStationKey } from '../model/stationPhotos';

interface TwinCanvas3DProps {
  viewModel: TwinViewModel;
  activeFilter: TwinDeviceFilter;
  onSelectDevice: (deviceId: string) => void;
  onSelectNode?: (nodeId: string) => void;
  selectedDeviceId?: string | null;
  tracePowerActive?: boolean;
  traceImpactActive?: boolean;
  visualizationLayer?: 'ARCHITECTURE' | 'ENERGY' | 'IMPACT';
  onVisualizationLayerChange?: (layer: 'ARCHITECTURE' | 'ENERGY' | 'IMPACT') => void;
}

export const TwinCanvas3D: React.FC<TwinCanvas3DProps> = ({
  viewModel,
  activeFilter,
  onSelectDevice,
  onSelectNode,
  selectedDeviceId,
  tracePowerActive = false,
  traceImpactActive = false,
  visualizationLayer: controlledLayer,
  onVisualizationLayerChange
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [internalLayer, setInternalLayer] = useState<'ARCHITECTURE' | 'ENERGY' | 'IMPACT'>('ENERGY');
  const activeLayer = controlledLayer || internalLayer;
  const setLayer = (layer: 'ARCHITECTURE' | 'ENERGY' | 'IMPACT') => {
    setInternalLayer(layer);
    if (onVisualizationLayerChange) onVisualizationLayerChange(layer);
  };

  const [hoveredObject, setHoveredObject] = useState<SpatialObject3D | null>(null);
  const [cameraMode, setCameraMode] = useState<'ISOMETRIC' | 'RENEWABLES' | 'POWERHOUSE' | 'TOP' | 'FRONT'>('ISOMETRIC');
  const [wireframeOnly, setWireframeOnly] = useState<boolean>(false);
  const [webGlAvailable, setWebGlAvailable] = useState<boolean>(true);
  const [showReferenceModal, setShowReferenceModal] = useState<boolean>(false);
  const [twinSnapshotUrl, setTwinSnapshotUrl] = useState<string | null>(null);
  const [pipExpanded, setPipExpanded] = useState<boolean>(true);

  // Active 3D profile for the current station
  const stationProfile3D: StationSpatial3DProfile = 
    STATION_SPATIAL_3D_PROFILES[viewModel.stationId] || 
    STATION_SPATIAL_3D_PROFILES.BHARATI;

  // Refs for Three.js state
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const meshesRef = useRef<Map<string, THREE.Object3D>>(new Map());
  const flowLinesRef = useRef<THREE.Object3D[]>([]);
  const flowParticlesRef = useRef<{ 
    line: THREE.Object3D; 
    points: THREE.Vector3[]; 
    progress: number; 
    speed: number; 
    mesh: THREE.Mesh 
  }[]>([]);
  const turbinesRef = useRef<{ rotorGroup: THREE.Group; speedMultiplier: number }[]>([]);
  const statusIndicatorsRef = useRef<{ mesh: THREE.Mesh; type: 'DG' | 'BESS' | 'WIND' | 'SOLAR' | 'BUS'; id: string }[]>([]);
  const environmentRef = useRef<PolarEnvironmentHandles | null>(null);
  const animFrameIdRef = useRef<number | null>(null);

  // Mouse orbit & camera position state (with smooth glide interpolation)
  const isDraggingRef = useRef<boolean>(false);
  const isTransitioningRef = useRef<boolean>(false);
  const previousMousePositionRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const cameraSphericalRef = useRef<{ radius: number; theta: number; phi: number }>({
    radius: 54,
    theta: Math.PI / 4,
    phi: Math.PI / 3.2
  });
  const cameraTargetRef = useRef<THREE.Vector3>(new THREE.Vector3(0, 4.5, 0));
  const targetSphericalRef = useRef<{ radius: number; theta: number; phi: number }>({
    radius: 54,
    theta: Math.PI / 4,
    phi: Math.PI / 3.2
  });
  const targetTargetRef = useRef<THREE.Vector3>(new THREE.Vector3(0, 4.5, 0));

  // Initialize Three.js Scene
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    try {
      const width = container.clientWidth || 800;
      const height = container.clientHeight || 580;

      // 1. Scene with Photorealistic Polar Sky & Atmosphere
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x060c18); // Deep polar arctic twilight
      scene.fog = new THREE.FogExp2(0x0a1628, 0.0045);
      sceneRef.current = scene;

      // Create Real-World Celestial Environment, Mountains, Aurora & Weather Particles
      const envHandles = createPolarEnvironment(scene);
      environmentRef.current = envHandles;

      // 2. Camera
      const camera = new THREE.PerspectiveCamera(45, width / height, 0.5, 600);
      cameraRef.current = camera;
      updateCameraPosition();

      // 3. Renderer with ACES Filmic Tone Mapping and Soft PCF Shadows
      const renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: false,
        preserveDrawingBuffer: true,
        powerPreference: 'high-performance'
      });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.32;
      rendererRef.current = renderer;

      // 4. Lighting: Product-grade Polar Daylight with Natural Fill
      // Soft ambient light simulating polar diffuse sky reflection
      const ambientLight = new THREE.AmbientLight(0xdbeafe, 0.65);
      scene.add(ambientLight);

      // Warm low-angle Antarctic sunlight (18-30° grazing polar sun casting realistic shadows)
      const sunLight = new THREE.DirectionalLight(0xffedd5, 1.45);
      sunLight.position.set(45, 32, 28);
      sunLight.castShadow = true;
      sunLight.shadow.mapSize.width = 2048;
      sunLight.shadow.mapSize.height = 2048;
      sunLight.shadow.camera.near = 10;
      sunLight.shadow.camera.far = 180;
      sunLight.shadow.camera.left = -60;
      sunLight.shadow.camera.right = 60;
      sunLight.shadow.camera.top = 60;
      sunLight.shadow.camera.bottom = -60;
      sunLight.shadow.bias = -0.0003;
      scene.add(sunLight);

      // Cool glacial blue fill light
      const fillLight = new THREE.DirectionalLight(0x7dd3fc, 0.55);
      fillLight.position.set(-40, 20, -35);
      scene.add(fillLight);

      // Subtle upward ground bounce light from sastrugi snow crust
      const groundBounce = new THREE.HemisphereLight(0xbae6fd, 0x1e293b, 0.55);
      scene.add(groundBounce);

      // Handle Resize
      const handleResize = () => {
        if (!container || !renderer || !camera) return;
        const newWidth = container.clientWidth;
        const newHeight = container.clientHeight;
        camera.aspect = newWidth / newHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(newWidth, newHeight);
      };
      window.addEventListener('resize', handleResize);

      setWebGlAvailable(true);

      return () => {
        window.removeEventListener('resize', handleResize);
        if (animFrameIdRef.current) {
          cancelAnimationFrame(animFrameIdRef.current);
        }
        if (environmentRef.current) {
          environmentRef.current.dispose();
          environmentRef.current = null;
        }
        renderer.dispose();
      };
    } catch (e) {
      console.warn('WebGL initialization advisory:', e);
      setWebGlAvailable(false);
    }
  }, [stationProfile3D.stationId]);

  // Update Camera Matrix from Spherical coordinates
  const updateCameraPosition = useCallback(() => {
    if (!cameraRef.current) return;
    const { radius, theta, phi } = cameraSphericalRef.current;
    const target = cameraTargetRef.current;

    const x = target.x + radius * Math.sin(phi) * Math.sin(theta);
    const y = Math.max(1.5, target.y + radius * Math.cos(phi));
    const z = target.z + radius * Math.sin(phi) * Math.cos(theta);

    cameraRef.current.position.set(x, y, z);
    cameraRef.current.lookAt(target);
  }, []);

  // Build / Rebuild 3D Meshes for Station Architecture, Devices, and Power Flow
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    // Clear old station meshes
    meshesRef.current.forEach(mesh => scene.remove(mesh));
    meshesRef.current.clear();
    turbinesRef.current = [];

    // Clear flow lines & particles
    flowLinesRef.current.forEach(line => scene.remove(line));
    flowLinesRef.current = [];
    flowParticlesRef.current.forEach(p => scene.remove(p.mesh));
    flowParticlesRef.current = [];

    // 1. Render Reference-Aligned Procedural Station Architecture & Terrain
    const stationId = viewModel.stationId.toUpperCase();
    let stationResult;

    if (stationId === 'MAITRI') {
      stationResult = buildMaitriStation(activeLayer, wireframeOnly);
    } else if (stationId === 'HIMADRI') {
      stationResult = buildHimadriStation(activeLayer, wireframeOnly);
    } else {
      stationResult = buildBharatiStation(activeLayer, wireframeOnly);
    }

    scene.add(stationResult.terrainMesh);
    meshesRef.current.set('station_terrain', stationResult.terrainMesh);

    scene.add(stationResult.architectureGroup);
    meshesRef.current.set('station_architecture', stationResult.architectureGroup);

    turbinesRef.current = stationResult.turbines;
    statusIndicatorsRef.current = stationResult.statusIndicators || [];

    // Register interactive equipment meshes
    stationResult.interactiveMeshes.forEach((mesh, devId) => {
      meshesRef.current.set(`interactive_${devId}`, mesh);
    });

    // 2. Render Station Equipment & Spatial Objects from Spatial Profile
    stationProfile3D.objects.forEach(obj => {
      // Filter out if category is filtered
      if (activeFilter === 'CRITICAL' && obj.importance !== 'CRITICAL') return;
      if (activeFilter === 'LOADS' && !obj.category.includes('LOAD') && obj.category !== 'SCIENCE' && obj.category !== 'HABITATION') return;
      if (activeFilter === 'THERMAL' && !obj.id.includes('heat') && !obj.id.includes('boiler') && !obj.id.includes('life')) return;

      // If already registered as an interactive mesh in stationResult, bind metadata and skip redundant box creation
      const existingMesh = 
        (obj.deviceId && stationResult.interactiveMeshes.get(obj.deviceId)) ||
        stationResult.interactiveMeshes.get(obj.id);

      if (existingMesh) {
        existingMesh.userData = { ...existingMesh.userData, spatialObject: obj };
        meshesRef.current.set(`obj_${obj.id}`, existingMesh);
        return;
      }

      // Interior equipment racks, science benches, utility modules
      const group = new THREE.Group();
      group.position.set(obj.position[0], obj.position[1], obj.position[2]);

      const isSelected = selectedDeviceId && (obj.deviceId === selectedDeviceId || obj.id === selectedDeviceId);
      const isTraceActive = tracePowerActive || traceImpactActive || activeLayer === 'IMPACT';
      const isRelatedToSelection = isSelected || (selectedDeviceId && obj.circuitId && obj.circuitId.includes(selectedDeviceId));
      const objectOpacity = (isTraceActive && !isRelatedToSelection && selectedDeviceId) ? 0.25 : 1.0;

      // Realistic Industrial Equipment Cubicle / Server Enclosure
      const cabMat = createStructuralSteelMaterial(0x1e293b, {
        wireframe: wireframeOnly,
        transparent: objectOpacity < 1.0,
        opacity: objectOpacity
      });
      const cubicle = new THREE.Mesh(new THREE.BoxGeometry(obj.dimensions[0], obj.dimensions[1], obj.dimensions[2]), cabMat);
      cubicle.castShadow = true;
      cubicle.receiveShadow = true;
      group.add(cubicle);

      // Status display bezel
      const displayMat = new THREE.MeshBasicMaterial({
        color: obj.status === 'FAULT' ? 0xe11d48 : (obj.status === 'STANDBY' ? 0xf59e0b : 0x0284c7)
      });
      const disp = new THREE.Mesh(new THREE.PlaneGeometry(obj.dimensions[0] * 0.7, obj.dimensions[1] * 0.25), displayMat);
      disp.position.set(0, obj.dimensions[1] * 0.2, obj.dimensions[2] / 2 + 0.01);
      group.add(disp);

      // Status indicator LED pip on top
      const ledGeo = new THREE.SphereGeometry(0.12, 8, 8);
      const ledColor = obj.status === 'ONLINE' ? 0x10b981 : (obj.status === 'FAULT' ? 0xe11d48 : 0xf59e0b);
      const led = new THREE.Mesh(ledGeo, new THREE.MeshBasicMaterial({ color: ledColor }));
      led.position.set(0, obj.dimensions[1] / 2 + 0.15, 0);
      group.add(led);

      // If selected, add high-precision engineering CAD bracket corners
      if (isSelected) {
        const edgeGeo = new THREE.EdgesGeometry(new THREE.BoxGeometry(obj.dimensions[0] + 0.2, obj.dimensions[1] + 0.2, obj.dimensions[2] + 0.2));
        const edgeMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, linewidth: 2 });
        group.add(new THREE.LineSegments(edgeGeo, edgeMat));
      }

      group.userData = { spatialObject: obj };
      scene.add(group);
      meshesRef.current.set(`obj_${obj.id}`, group);
    });

    // 3. Render 3D Directional Power Flow Paths
    stationProfile3D.powerFlowPaths.forEach(path => {
      if (path.points.length < 2) return;

      const vPoints = path.points.map(p => new THREE.Vector3(p[0], p[1], p[2]));
      const curve = new THREE.CatmullRomCurve3(vPoints);

      // Determine power flow color and dynamic state based on circuit telemetry
      let lineColor = 0x38bdf8; // Sky blue
      let activeFlow = path.defaultActive;
      let powerKw = path.nominalKw;

      if (path.circuitId.includes('solar')) {
        lineColor = 0xf59e0b; // Gold
        activeFlow = viewModel.powerSummary.solarGenerationKw > 0.1;
        powerKw = viewModel.powerSummary.solarGenerationKw;
      } else if (path.circuitId.includes('wind')) {
        lineColor = 0x0284c7; // Deep blue
        activeFlow = viewModel.powerSummary.windGenerationKw > 0.1;
        powerKw = viewModel.powerSummary.windGenerationKw;
      } else if (path.circuitId.includes('diesel')) {
        lineColor = 0xb45309; // Amber
        activeFlow = viewModel.powerSummary.dieselGenerationKw > 0.1;
        powerKw = viewModel.powerSummary.dieselGenerationKw;
      } else if (path.circuitId.includes('bess')) {
        lineColor = 0x10b981; // Emerald
        activeFlow = Math.abs(viewModel.powerSummary.batteryPowerKw) > 0.1;
        powerKw = Math.abs(viewModel.powerSummary.batteryPowerKw);
      }

      const isTraceMode = tracePowerActive || traceImpactActive || activeLayer === 'IMPACT';
      const isRelevantCircuit = !selectedDeviceId || path.circuitId.includes(selectedDeviceId) || path.fromId.includes(selectedDeviceId) || path.toId.includes(selectedDeviceId);
      
      let pathOpacity = activeFlow ? 0.85 : 0.15;
      if (activeLayer === 'ARCHITECTURE') {
        pathOpacity = activeFlow ? 0.35 : 0.05;
      } else if (isTraceMode) {
        pathOpacity = isRelevantCircuit ? (activeFlow ? 0.95 : 0.4) : 0.06;
      }

      // 3D Tube for Power Conduits
      const tubeRadius = Math.max(0.08, Math.min(0.24, 0.08 + (powerKw / 250) * 0.16));
      const tubeGeo = new THREE.TubeGeometry(curve, 32, tubeRadius, 8, false);
      const tubeMat = new THREE.MeshStandardMaterial({
        color: activeFlow ? lineColor : 0x334155,
        emissive: activeFlow ? new THREE.Color(lineColor) : new THREE.Color(0x000000),
        emissiveIntensity: activeFlow ? 0.75 : 0.0,
        roughness: 0.35,
        metalness: 0.65,
        transparent: true,
        opacity: pathOpacity
      });

      const tubeMesh = new THREE.Mesh(tubeGeo, tubeMat);
      scene.add(tubeMesh);
      flowLinesRef.current.push(tubeMesh);

      // Active energy stream pulse particles along conduit
      if (activeFlow && (!isTraceMode || isRelevantCircuit)) {
        const points = curve.getPoints(50);
        const particleGeo = new THREE.SphereGeometry(activeLayer === 'ENERGY' ? 0.32 : 0.22, 8, 8);
        const particleMat = new THREE.MeshBasicMaterial({ color: lineColor });
        const particle = new THREE.Mesh(particleGeo, particleMat);
        particle.position.copy(points[0]);
        scene.add(particle);

        // Direction: If battery is charging, reverse particle flow direction!
        const isBessCharging = path.circuitId.includes('bess') && viewModel.powerSummary.batteryPowerKw < -0.1;
        const speed = (0.008 + Math.min(0.02, powerKw / 800)) * (isBessCharging ? -1 : 1);

        flowParticlesRef.current.push({
          line: tubeMesh,
          points,
          progress: Math.random(),
          speed,
          mesh: particle
        });
      }
    });

  }, [
    stationProfile3D, 
    activeFilter, 
    selectedDeviceId, 
    wireframeOnly, 
    activeLayer,
    tracePowerActive,
    traceImpactActive,
    viewModel.powerSummary.solarGenerationKw,
    viewModel.powerSummary.windGenerationKw,
    viewModel.powerSummary.dieselGenerationKw,
    viewModel.powerSummary.batteryPowerKw
  ]);

  // Animation Loop (Rotors, Dynamic Energy Particles, Render Loop & Smooth Camera Glide)
  useEffect(() => {
    const scene = sceneRef.current;
    const renderer = rendererRef.current;
    const camera = cameraRef.current;
    if (!scene || !renderer || !camera) return;

    const animate = () => {
      // 0. Smooth Camera Interpolation towards Target Presets
      if (isTransitioningRef.current) {
        const damp = 0.08;
        cameraSphericalRef.current.radius += (targetSphericalRef.current.radius - cameraSphericalRef.current.radius) * damp;
        cameraSphericalRef.current.theta += (targetSphericalRef.current.theta - cameraSphericalRef.current.theta) * damp;
        cameraSphericalRef.current.phi += (targetSphericalRef.current.phi - cameraSphericalRef.current.phi) * damp;
        cameraTargetRef.current.lerp(targetTargetRef.current, damp);

        const dr = Math.abs(targetSphericalRef.current.radius - cameraSphericalRef.current.radius);
        const dth = Math.abs(targetSphericalRef.current.theta - cameraSphericalRef.current.theta);
        const dphi = Math.abs(targetSphericalRef.current.phi - cameraSphericalRef.current.phi);
        const dTarget = cameraTargetRef.current.distanceTo(targetTargetRef.current);

        if (dr < 0.1 && dth < 0.01 && dphi < 0.01 && dTarget < 0.1) {
          isTransitioningRef.current = false;
        }
        updateCameraPosition();
      }

      // 1. Animate Wind Turbine Rotors (Rotational speed scales with wind generation kW)
      const windActive = viewModel.powerSummary.windGenerationKw > 0.1;
      const baseRotorSpeed = windActive ? 0.045 : 0.002;

      turbinesRef.current.forEach(t => {
        t.rotorGroup.rotation.z += baseRotorSpeed * t.speedMultiplier;
      });

      // 2. Animate Power Flow Particles along Circuit Lines
      flowParticlesRef.current.forEach(p => {
        p.progress += p.speed;
        if (p.progress >= 1.0) p.progress = 0.0;
        if (p.progress < 0.0) p.progress = 1.0;

        const idx = Math.floor(p.progress * (p.points.length - 1));
        const nextIdx = Math.min(idx + 1, p.points.length - 1);
        const segmentProgress = (p.progress * (p.points.length - 1)) - idx;

        const pos = new THREE.Vector3().lerpVectors(
          p.points[idx],
          p.points[nextIdx],
          segmentProgress
        );
        p.mesh.position.copy(pos);
      });

      // 3. Dynamic Real-Time Industrial Equipment Status LEDs
      statusIndicatorsRef.current.forEach(ind => {
        if (!ind.mesh || !ind.mesh.material) return;
        const mat = ind.mesh.material as THREE.MeshStandardMaterial;
        if (ind.type === 'DG') {
          const isDgOn = viewModel.powerSummary.dieselGenerationKw > 0.1;
          mat.color.setHex(isDgOn ? 0x10b981 : 0x475569);
          mat.emissive.setHex(isDgOn ? 0x10b981 : 0x000000);
          mat.emissiveIntensity = isDgOn ? 0.95 : 0.0;
        } else if (ind.type === 'BESS') {
          const p = viewModel.powerSummary.batteryPowerKw;
          if (p < -0.1) {
            mat.color.setHex(0x10b981);
            mat.emissive.setHex(0x10b981);
            mat.emissiveIntensity = 0.5 + Math.sin(Date.now() * 0.005) * 0.4;
          } else if (p > 0.1) {
            mat.color.setHex(0x38bdf8);
            mat.emissive.setHex(0x38bdf8);
            mat.emissiveIntensity = 0.5 + Math.sin(Date.now() * 0.005) * 0.4;
          } else {
            mat.color.setHex(0xf59e0b);
            mat.emissive.setHex(0xf59e0b);
            mat.emissiveIntensity = 0.6;
          }
        } else if (ind.type === 'BUS') {
          const hasPower = viewModel.powerSummary.totalGenerationKw > 0.1 || Math.abs(viewModel.powerSummary.batteryPowerKw) > 0.1;
          mat.color.setHex(hasPower ? 0x38bdf8 : 0xef4444);
          mat.emissive.setHex(hasPower ? 0x38bdf8 : 0xef4444);
          mat.emissiveIntensity = hasPower ? 0.85 : 0.4;
        }
      });

      // 4. Animate Polar Atmosphere, Weather Flurries, Aurora & Thermal Exhaust Plumes
      if (environmentRef.current) {
        const isBlizzard = viewModel.environment.stormState === 'BLIZZARD' || 
          (viewModel.environment.windSpeedMs > 18);
        const dieselActive = viewModel.powerSummary.dieselGenerationKw > 0.1;
        environmentRef.current.update(0.016, viewModel.environment.windSpeedMs || 10, isBlizzard, dieselActive);
      }

      renderer.render(scene, camera);
      animFrameIdRef.current = requestAnimationFrame(animate);
    };

    animFrameIdRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, [
    viewModel.powerSummary.windGenerationKw,
    viewModel.powerSummary.dieselGenerationKw,
    viewModel.powerSummary.batteryPowerKw,
    viewModel.powerSummary.totalGenerationKw,
    viewModel.environment.windSpeedMs,
    viewModel.environment.stormState,
    updateCameraPosition
  ]);

  // Mouse Orbit & Pan Controls
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    isDraggingRef.current = true;
    isTransitioningRef.current = false;
    previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const camera = cameraRef.current;
    const scene = sceneRef.current;
    if (!canvas || !camera || !scene) return;

    if (isDraggingRef.current) {
      isTransitioningRef.current = false;
      const deltaX = e.clientX - previousMousePositionRef.current.x;
      const deltaY = e.clientY - previousMousePositionRef.current.y;

      if (e.buttons === 1) {
        // Left button: Orbit
        cameraSphericalRef.current.theta -= deltaX * 0.008;
        cameraSphericalRef.current.phi = Math.max(
          0.1,
          Math.min(Math.PI / 2 - 0.05, cameraSphericalRef.current.phi - deltaY * 0.008)
        );
      } else if (e.buttons === 2 || e.shiftKey) {
        // Right button or Shift+Left: Pan Target
        const panSpeed = 0.06;
        cameraTargetRef.current.x -= deltaX * panSpeed;
        cameraTargetRef.current.z += deltaY * panSpeed;
      }

      targetSphericalRef.current.theta = cameraSphericalRef.current.theta;
      targetSphericalRef.current.phi = cameraSphericalRef.current.phi;
      targetSphericalRef.current.radius = cameraSphericalRef.current.radius;
      targetTargetRef.current.copy(cameraTargetRef.current);

      updateCameraPosition();
      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
    } else {
      // Raycasting Hover Detection
      const rect = canvas.getBoundingClientRect();
      const mouse = new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1
      );

      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(mouse, camera);

      const objectsToCheck = Array.from(meshesRef.current.values());
      const intersects = raycaster.intersectObjects(objectsToCheck, true);

      if (intersects.length > 0) {
        let parent = intersects[0].object;
        while (parent && !parent.userData?.spatialObject && !parent.userData?.deviceId && parent.parent) {
          parent = parent.parent;
        }

        if (parent?.userData?.spatialObject) {
          setHoveredObject(parent.userData.spatialObject);
          canvas.style.cursor = 'pointer';
          return;
        } else if (parent?.userData?.deviceId) {
          // Find matching spatial object
          const found = stationProfile3D.objects.find(o => o.deviceId === parent?.userData?.deviceId);
          if (found) {
            setHoveredObject(found);
            canvas.style.cursor = 'pointer';
            return;
          }
        }
      }
      setHoveredObject(null);
      canvas.style.cursor = 'grab';
    }
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    isTransitioningRef.current = false;
    const zoomFactor = e.deltaY * 0.035;
    cameraSphericalRef.current.radius = Math.max(
      14,
      Math.min(110, cameraSphericalRef.current.radius + zoomFactor)
    );
    targetSphericalRef.current.radius = cameraSphericalRef.current.radius;
    updateCameraPosition();
  };

  // Click to Select Device & Focus Camera
  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const camera = cameraRef.current;
    if (!canvas || !camera) return;

    const rect = canvas.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, camera);

    const objectsToCheck = Array.from(meshesRef.current.values());
    const intersects = raycaster.intersectObjects(objectsToCheck, true);

    if (intersects.length > 0) {
      let parent = intersects[0].object;
      while (parent && !parent.userData?.spatialObject && !parent.userData?.deviceId && parent.parent) {
        parent = parent.parent;
      }

      if (parent?.userData?.spatialObject) {
        const obj: SpatialObject3D = parent.userData.spatialObject;
        if (obj.selectable) {
          onSelectDevice(obj.deviceId || obj.id);
          if (onSelectNode) onSelectNode(obj.id);
        }
      } else if (parent?.userData?.deviceId) {
        onSelectDevice(parent.userData.deviceId);
      }
    }
  };

  // Camera Presets (Cinematic Hero, Renewables Field, Powerhouse BESS/DG, Overhead Drone, Elevation)
  const setCameraPreset = (preset: 'ISOMETRIC' | 'RENEWABLES' | 'POWERHOUSE' | 'TOP' | 'FRONT') => {
    setCameraMode(preset);
    isTransitioningRef.current = true;

    if (preset === 'ISOMETRIC') {
      targetTargetRef.current.set(0, 4.5, 0);
      targetSphericalRef.current = { radius: 54, theta: Math.PI / 4, phi: Math.PI / 3.2 };
    } else if (preset === 'RENEWABLES') {
      targetTargetRef.current.set(-24, 3.5, 2);
      targetSphericalRef.current = { radius: 38, theta: Math.PI / 2.8, phi: Math.PI / 3.5 };
    } else if (preset === 'POWERHOUSE') {
      targetTargetRef.current.set(22, 3.0, 0);
      targetSphericalRef.current = { radius: 34, theta: Math.PI / 5.5, phi: Math.PI / 3.4 };
    } else if (preset === 'TOP') {
      targetTargetRef.current.set(0, 0, 0);
      targetSphericalRef.current = { radius: 64, theta: 0, phi: 0.08 };
    } else if (preset === 'FRONT') {
      targetTargetRef.current.set(0, 6.0, 0);
      targetSphericalRef.current = { radius: 48, theta: 0, phi: Math.PI / 2 - 0.1 };
    }
  };

  // Focus on Selected Asset with Smooth Glide
  const focusSelection = () => {
    if (!selectedDeviceId) return;
    const selectedObj = stationProfile3D.objects.find(
      o => o.deviceId === selectedDeviceId || o.id === selectedDeviceId
    );
    if (selectedObj) {
      isTransitioningRef.current = true;
      targetTargetRef.current.set(
        selectedObj.position[0],
        Math.max(1.5, selectedObj.position[1]),
        selectedObj.position[2]
      );
      targetSphericalRef.current = {
        radius: 22,
        theta: cameraSphericalRef.current.theta,
        phi: Math.PI / 3.5
      };
    }
  };

  const resetView = () => {
    setCameraPreset('ISOMETRIC');
  };

  // Open Reference Comparison Modal and snapshot current 3D frame
  const handleOpenReferenceModal = () => {
    if (canvasRef.current) {
      try {
        const dataUrl = canvasRef.current.toDataURL('image/png');
        setTwinSnapshotUrl(dataUrl);
      } catch {
        setTwinSnapshotUrl(null);
      }
    }
    setShowReferenceModal(true);
  };

  if (!webGlAvailable) {
    return (
      <div className="bg-slate-900 rounded-lg p-8 border border-slate-800 text-center text-slate-300">
        <ShieldAlert className="w-8 h-8 text-amber-500 mx-auto mb-2" />
        <p className="font-semibold text-sm">WebGL Acceleration Unavailable</p>
        <p className="text-xs text-slate-400 mt-1">
          Please use the 2D Architectural schematic or Accessible Table view.
        </p>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className="relative w-full h-[640px] bg-slate-950 rounded-lg border border-slate-800 overflow-hidden select-none shadow-2xl"
    >
      {/* Three.js Canvas */}
      <canvas
        id="polaris-twin-canvas-3d"
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        onClick={handleClick}
        onContextMenu={e => e.preventDefault()}
        className="w-full h-full block cursor-grab active:cursor-grabbing"
      />

      {/* Top Left: Station & Architectural Specification Tag */}
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-1.5 font-mono text-[10px] pointer-events-none">
        <div className="flex items-center space-x-2 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-md border border-slate-700/80 shadow-md pointer-events-auto">
          <Compass className="w-3.5 h-3.5 text-sky-400" />
          <span className="font-bold text-white uppercase tracking-wider">
            {stationProfile3D.name}
          </span>
          <span className="text-slate-600">•</span>
          <span className="text-sky-400 font-semibold">{stationProfile3D.geometryBasis}</span>
        </div>
        <div className="bg-slate-900/85 backdrop-blur px-2.5 py-1 rounded text-slate-300 text-[9px] border border-slate-800 max-w-sm">
          {stationProfile3D.architectureDescription}
        </div>
      </div>

      {/* Top Center: Real-Time Polar Environmental & Telemetry HUD */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 hidden lg:flex items-center space-x-3 bg-slate-900/90 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-slate-700/80 shadow-lg font-mono text-[11px] pointer-events-none">
        <div className="flex items-center space-x-1 text-slate-300">
          <Thermometer className="w-3.5 h-3.5 text-cyan-400" />
          <span>{viewModel.environment.ambientTempC.toFixed(1)}°C</span>
        </div>
        <span className="text-slate-700">|</span>
        <div className="flex items-center space-x-1 text-slate-300">
          <Wind className="w-3.5 h-3.5 text-teal-400" />
          <span>{viewModel.environment.windSpeedMs.toFixed(1)} m/s</span>
        </div>
        <span className="text-slate-700">|</span>
        <div className="flex items-center space-x-1 text-amber-300 font-semibold">
          <Sun className="w-3.5 h-3.5 text-amber-400" />
          <span>{viewModel.powerSummary.solarGenerationKw.toFixed(1)} kW</span>
        </div>
        <span className="text-slate-700">|</span>
        <div className="flex items-center space-x-1 text-sky-300 font-semibold">
          <Wind className="w-3.5 h-3.5 text-sky-400" />
          <span>{viewModel.powerSummary.windGenerationKw.toFixed(1)} kW</span>
        </div>
        <span className="text-slate-700">|</span>
        <div className="flex items-center space-x-1 text-emerald-300 font-semibold">
          <BatteryCharging className="w-3.5 h-3.5 text-emerald-400" />
          <span>{viewModel.powerSummary.batterySocPct.toFixed(0)}%</span>
        </div>
        {viewModel.environment.stormState !== 'NORMAL' && (
          <>
            <span className="text-slate-700">|</span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse">
              {viewModel.environment.stormState}
            </span>
          </>
        )}
      </div>

      {/* Top Right: Camera Presets, Layer Selector & Comparison Modal Trigger */}
      <div className="absolute top-4 right-4 z-10 flex items-center space-x-1.5 bg-slate-900/90 backdrop-blur-md p-1 rounded-md border border-slate-700/80 shadow-md font-mono text-[10px]">
        {/* Layer Selector */}
        <div className="flex items-center rounded bg-slate-800/90 p-0.5 mr-1">
          <button
            type="button"
            onClick={() => setLayer('ARCHITECTURE')}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLayer === 'ARCHITECTURE' ? 'bg-white text-slate-950 font-bold shadow' : 'text-slate-400 hover:text-white'
            }`}
            title="Focus Structural Architecture & Envelope"
          >
            ARCH
          </button>
          <button
            type="button"
            onClick={() => setLayer('ENERGY')}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLayer === 'ENERGY' ? 'bg-sky-500 text-white font-bold shadow' : 'text-slate-400 hover:text-white'
            }`}
            title="Focus Electrical Microgrid Power Flow"
          >
            ENERGY
          </button>
          <button
            type="button"
            onClick={() => setLayer('IMPACT')}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLayer === 'IMPACT' ? 'bg-amber-500 text-slate-950 font-bold shadow' : 'text-slate-400 hover:text-white'
            }`}
            title="Focus Circuit Downstream Impact & Trips"
          >
            IMPACT
          </button>
        </div>

        <div className="w-[1px] h-4 bg-slate-700" />

        <button
          type="button"
          onClick={() => setCameraPreset('ISOMETRIC')}
          className={`px-2 py-1 rounded transition-colors ${
            cameraMode === 'ISOMETRIC' ? 'bg-sky-600 text-white font-bold' : 'text-slate-300 hover:bg-slate-800'
          }`}
          title="Cinematic Hero 3D Perspective"
        >
          HERO
        </button>

        <button
          type="button"
          onClick={() => setCameraPreset('RENEWABLES')}
          className={`px-2 py-1 rounded transition-colors ${
            cameraMode === 'RENEWABLES' ? 'bg-sky-600 text-white font-bold' : 'text-slate-300 hover:bg-slate-800'
          }`}
          title="Solar PV & Wind Turbines Array"
        >
          PV/WIND
        </button>

        <button
          type="button"
          onClick={() => setCameraPreset('POWERHOUSE')}
          className={`px-2 py-1 rounded transition-colors ${
            cameraMode === 'POWERHOUSE' ? 'bg-sky-600 text-white font-bold' : 'text-slate-300 hover:bg-slate-800'
          }`}
          title="BESS Storage & Diesel Generator Powerhouse"
        >
          BESS/DG
        </button>

        <button
          type="button"
          onClick={() => setCameraPreset('TOP')}
          className={`px-2 py-1 rounded transition-colors ${
            cameraMode === 'TOP' ? 'bg-sky-600 text-white font-bold' : 'text-slate-300 hover:bg-slate-800'
          }`}
          title="Top-Down Drone Plan View"
        >
          DRONE
        </button>

        <button
          type="button"
          onClick={() => setCameraPreset('FRONT')}
          className={`px-2 py-1 rounded transition-colors ${
            cameraMode === 'FRONT' ? 'bg-sky-600 text-white font-bold' : 'text-slate-300 hover:bg-slate-800'
          }`}
          title="Front Elevation View"
        >
          ELEVATION
        </button>

        {selectedDeviceId && (
          <button
            type="button"
            onClick={focusSelection}
            className="flex items-center gap-1 px-2 py-1 rounded bg-sky-950 text-sky-300 border border-sky-700 hover:bg-sky-900 transition-colors"
            title="Focus Camera on Selected Asset"
          >
            <Focus className="w-3 h-3" />
            <span>FOCUS</span>
          </button>
        )}

        <div className="w-[1px] h-4 bg-slate-700 mx-1" />

        <button
          type="button"
          onClick={handleOpenReferenceModal}
          className="flex items-center space-x-1 px-2.5 py-1 rounded text-xs transition-colors bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-xs"
          title="Open Side-by-Side Real Reference vs 3D Digital Twin Viewer"
        >
          <Layers className="w-3.5 h-3.5" />
          <span>REFERENCE ↔ TWIN</span>
        </button>

        <div className="w-[1px] h-4 bg-slate-700 mx-1" />

        <button
          type="button"
          onClick={() => setWireframeOnly(!wireframeOnly)}
          className={`p-1 rounded text-slate-400 hover:text-white transition-colors ${wireframeOnly ? 'bg-slate-700 text-white' : ''}`}
          title="Toggle Wireframe Shell"
        >
          <Box className="w-3.5 h-3.5" />
        </button>

        <button
          type="button"
          onClick={resetView}
          className="p-1 rounded text-slate-400 hover:text-white transition-colors"
          title="Reset Camera View"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Bottom Left Picture-in-Picture: Real Base Station Ground Truth Photo */}
      <div className="absolute bottom-14 left-4 z-20 font-sans">
        {pipExpanded ? (
          <div className="w-56 bg-slate-900/95 backdrop-blur-md rounded-lg border border-teal-500/40 p-2 shadow-2xl animate-in fade-in duration-150">
            <div className="flex items-center justify-between pb-1 mb-1 border-b border-slate-800 text-[10px] font-mono">
              <span className="text-teal-300 font-bold flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
                REAL BASE STATION
              </span>
              <button
                type="button"
                onClick={() => setPipExpanded(false)}
                className="text-slate-400 hover:text-white px-1 font-bold text-xs"
                title="Minimize Ground Truth PIP"
              >
                ✕
              </button>
            </div>
            <div 
              onClick={handleOpenReferenceModal}
              className="relative group cursor-pointer overflow-hidden rounded border border-slate-700 aspect-video bg-slate-950"
            >
              <img
                key={normalizeStationKey(viewModel.stationId)}
                src={getStationPhoto(viewModel.stationId)}
                alt="Real Station Ground Truth"
                onError={(e) => {
                  const target = e.currentTarget;
                  if (!target.dataset.fallback) {
                    target.dataset.fallback = 'true';
                    target.src = getPublicStationPhoto(viewModel.stationId);
                  }
                }}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
              />
              <div className="absolute inset-0 bg-slate-950/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-[11px] font-mono font-bold backdrop-blur-[1px]">
                Compare vs 3D
              </div>
            </div>
            <div className="mt-1.5 flex items-center justify-between text-[10px] font-mono">
              <span className="text-slate-400 truncate max-w-[130px]">{stationProfile3D.name}</span>
              <button
                type="button"
                onClick={handleOpenReferenceModal}
                className="text-teal-400 hover:text-teal-300 font-bold underline"
              >
                Compare
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setPipExpanded(true)}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-900/90 hover:bg-slate-800 text-teal-300 border border-teal-500/40 text-[10px] font-mono font-bold shadow-lg backdrop-blur-md transition-colors"
            title="Show Real Base Station Reference Photo"
          >
            <span className="w-2 h-2 rounded-full bg-teal-400" />
            <span>Real Photo PIP</span>
          </button>
        )}
      </div>

      {/* Bottom Left: Navigation & Provenance Hints */}
      <div className="absolute bottom-4 left-4 z-10 flex items-center space-x-2 text-[10px] font-mono text-slate-400 bg-slate-900/85 backdrop-blur px-2.5 py-1 rounded border border-slate-800 pointer-events-none">
        <span>LEFT-DRAG: Orbit</span>
        <span>•</span>
        <span>RIGHT-DRAG: Pan</span>
        <span>•</span>
        <span>WHEEL: Zoom</span>
        <span>•</span>
        <span>CLICK: Inspect Equipment</span>
      </div>

      {/* Floating Hover HUD Card with Provenance Inspector */}
      {hoveredObject && (
        <div className="absolute bottom-4 right-4 z-10 w-80 bg-slate-900/95 backdrop-blur-md rounded-lg border border-slate-700 p-3.5 shadow-2xl font-sans pointer-events-none text-slate-200 animate-in fade-in duration-150">
          <div className="flex items-center justify-between text-xs font-mono pb-1.5 border-b border-slate-800">
            <span className="font-bold text-white truncate">{hoveredObject.name}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
              hoveredObject.status === 'ONLINE' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' :
              hoveredObject.status === 'FAULT' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-slate-800 text-slate-400'
            }`}>
              {hoveredObject.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 text-[11px] font-mono">
            <div>
              <span className="text-[9px] text-slate-400 block uppercase">IMPORTANCE</span>
              <span className="font-bold text-slate-200">{hoveredObject.importance}</span>
            </div>
            <div>
              <span className="text-[9px] text-slate-400 block uppercase">POWER RATING</span>
              <span className="font-bold text-emerald-400">{hoveredObject.nominalPowerKw} kW</span>
            </div>
          </div>

          {/* Value Provenance Inspection (Prompt Rule 14) */}
          <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span className="flex items-center gap-1 text-sky-400">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              {hoveredObject.provenance}
            </span>
            <span>MODEL: TwinEngine</span>
          </div>

          {hoveredObject.realWorldContext && (
            <p className="text-[10px] text-slate-400 mt-1.5 font-sans leading-relaxed">
              {hoveredObject.realWorldContext}
            </p>
          )}
        </div>
      )}

      {/* Interactive Reference ↔ Digital Twin Comparison Modal */}
      <ReferenceComparisonModal
        stationId={viewModel.stationId}
        isOpen={showReferenceModal}
        onClose={() => setShowReferenceModal(false)}
        renderedTwinCanvasUrl={twinSnapshotUrl}
      />
    </div>
  );
};
