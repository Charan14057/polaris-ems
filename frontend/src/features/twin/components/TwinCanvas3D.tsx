/**
 * POLARIS-EMS — 3D Spatial Digital Twin Canvas
 * Phase 18: Operational 3D Digital Twin Engine
 * 
 * High-performance, lightweight WebGL / Three.js 3D spatial microgrid visualizer.
 * Renders representative polar station geometry (Bharati, Maitri, Himadri),
 * directional 3D power flow streams, equipment models, and circuit lineage.
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
  Activity
} from 'lucide-react';
import { TwinViewModel, TwinDeviceFilter } from '../model/twinTypes';
import { 
  STATION_SPATIAL_3D_PROFILES, 
  StationSpatial3DProfile, 
  SpatialObject3D, 
  PowerFlowPath3D 
} from '../model/spatialProfiles3D';

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
  const [cameraMode, setCameraMode] = useState<'ISOMETRIC' | 'TOP' | 'FRONT'>('ISOMETRIC');
  const [wireframeOnly, setWireframeOnly] = useState<boolean>(false);
  const [webGlAvailable, setWebGlAvailable] = useState<boolean>(true);

  // Active 3D profile for the current station
  const stationProfile3D: StationSpatial3DProfile = 
    STATION_SPATIAL_3D_PROFILES[viewModel.stationId] || 
    STATION_SPATIAL_3D_PROFILES.BHARATI;

  // Refs for Three.js state
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const meshesRef = useRef<Map<string, THREE.Object3D>>(new Map());
  const flowLinesRef = useRef<THREE.Line[]>([]);
  const flowParticlesRef = useRef<{ line: THREE.Line; points: THREE.Vector3[]; progress: number; speed: number; mesh: THREE.Mesh }[]>([]);
  const turbinesRef = useRef<THREE.Group[]>([]);
  const animFrameIdRef = useRef<number | null>(null);

  // Mouse interaction state
  const isDraggingRef = useRef<boolean>(false);
  const previousMousePositionRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const cameraSphericalRef = useRef<{ radius: number; theta: number; phi: number }>({
    radius: 48,
    theta: Math.PI / 4,
    phi: Math.PI / 3
  });
  const cameraTargetRef = useRef<THREE.Vector3>(new THREE.Vector3(0, 4, 0));

  // Initialize Three.js Scene
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    try {
      const width = container.clientWidth || 800;
      const height = container.clientHeight || 580;

      // 1. Scene
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xf8fafc); // Slate-50 background
      scene.fog = new THREE.FogExp2(0xf8fafc, 0.008);
      sceneRef.current = scene;

      // 2. Camera
      const camera = new THREE.PerspectiveCamera(45, width / height, 0.5, 500);
      cameraRef.current = camera;
      updateCameraPosition();

      // 3. Renderer
      const renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: false,
        powerPreference: 'high-performance'
      });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      rendererRef.current = renderer;

      // 4. Lighting (Clean Industrial Control Room Daylight)
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
      scene.add(ambientLight);

      const sunLight = new THREE.DirectionalLight(0xfff7ed, 1.1);
      sunLight.position.set(30, 60, 40);
      sunLight.castShadow = true;
      sunLight.shadow.mapSize.width = 1024;
      sunLight.shadow.mapSize.height = 1024;
      sunLight.shadow.camera.near = 10;
      sunLight.shadow.camera.far = 150;
      sunLight.shadow.camera.left = -40;
      sunLight.shadow.camera.right = 40;
      sunLight.shadow.camera.top = 40;
      sunLight.shadow.camera.bottom = -40;
      scene.add(sunLight);

      const fillLight = new THREE.DirectionalLight(0xe0f2fe, 0.4);
      fillLight.position.set(-30, 20, -30);
      scene.add(fillLight);

      // 5. Polar Ground Plane & Grid
      const groundGeo = new THREE.PlaneGeometry(160, 160);
      const groundMat = new THREE.MeshLambertMaterial({ 
        color: new THREE.Color(stationProfile3D.groundColor),
        side: THREE.DoubleSide 
      });
      const ground = new THREE.Mesh(groundGeo, groundMat);
      ground.rotation.x = -Math.PI / 2;
      ground.position.y = -0.05;
      ground.receiveShadow = true;
      scene.add(ground);

      const gridHelper = new THREE.GridHelper(120, 60, 0x94a3b8, 0xe2e8f0);
      gridHelper.position.y = 0.01;
      scene.add(gridHelper);

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
        renderer.dispose();
      };
    } catch (e) {
      console.warn('WebGL init advisory:', e);
      setWebGlAvailable(false);
    }
  }, [stationProfile3D.groundColor]);

  // Update Camera Matrix from Spherical coordinates
  const updateCameraPosition = useCallback(() => {
    if (!cameraRef.current) return;
    const { radius, theta, phi } = cameraSphericalRef.current;
    const target = cameraTargetRef.current;

    const x = target.x + radius * Math.sin(phi) * Math.sin(theta);
    const y = target.y + radius * Math.cos(phi);
    const z = target.z + radius * Math.sin(phi) * Math.cos(theta);

    cameraRef.current.position.set(x, y, z);
    cameraRef.current.lookAt(target);
  }, []);

  // Build / Rebuild 3D Meshes for Station Decks, Devices, and Flow Lines
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

    // 1. Render Station Decks (Architectural Volumes)
    stationProfile3D.decks.forEach(deck => {
      const b = deck.bounds;
      const width = b.maxX - b.minX;
      const depth = b.maxZ - b.minZ;
      const height = 0.4;
      const centerX = (b.minX + b.maxX) / 2;
      const centerZ = (b.minZ + b.maxZ) / 2;

      // In ARCHITECTURE layer, decks are more prominent; in ENERGY/IMPACT they are subtle backdrops
      const deckOpacity = activeLayer === 'ARCHITECTURE' 
        ? Math.min(0.85, deck.opacity * 1.5) 
        : deck.opacity * 0.7;

      // Deck Slab
      const slabGeo = new THREE.BoxGeometry(width, height, depth);
      const slabMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(deck.color),
        transparent: true,
        opacity: deckOpacity,
        roughness: 0.6,
        wireframe: wireframeOnly
      });
      const slabMesh = new THREE.Mesh(slabGeo, slabMat);
      slabMesh.position.set(centerX, deck.elevation + height / 2, centerZ);
      slabMesh.receiveShadow = true;
      scene.add(slabMesh);
      meshesRef.current.set(`deck_${deck.id}`, slabMesh);

      // Deck Perimeter Edges (Outline)
      const edgeGeo = new THREE.EdgesGeometry(slabGeo);
      const edgeMat = new THREE.LineBasicMaterial({ 
        color: activeLayer === 'ARCHITECTURE' ? 0x64748b : 0x94a3b8, 
        linewidth: 1 
      });
      const edgeLine = new THREE.LineSegments(edgeGeo, edgeMat);
      edgeLine.position.copy(slabMesh.position);
      scene.add(edgeLine);
      meshesRef.current.set(`deck_edges_${deck.id}`, edgeLine);

      // If elevated deck (Bharati stilts), render structural steel pilings
      if (deck.elevation > 1.0 && stationProfile3D.stationId === 'BHARATI') {
        const pillarGeo = new THREE.CylinderGeometry(0.35, 0.35, deck.elevation, 8);
        const pillarMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.6, roughness: 0.4 });

        const pillarPositions = [
          [b.minX + 2, b.minZ + 2],
          [b.maxX - 2, b.minZ + 2],
          [b.minX + 2, b.maxZ - 2],
          [b.maxX - 2, b.maxZ - 2],
          [centerX, b.minZ + 2],
          [centerX, b.maxZ - 2],
          [b.minX + 2, centerZ],
          [b.maxX - 2, centerZ]
        ];

        pillarPositions.forEach(([px, pz], idx) => {
          const pillar = new THREE.Mesh(pillarGeo, pillarMat);
          pillar.position.set(px, deck.elevation / 2, pz);
          pillar.castShadow = true;
          scene.add(pillar);
          meshesRef.current.set(`pillar_${deck.id}_${idx}`, pillar);
        });
      }
    });

    // 2. Render Station Equipment & Spatial Objects
    stationProfile3D.objects.forEach(obj => {
      // Filter out if category is filtered
      if (activeFilter === 'CRITICAL' && obj.importance !== 'CRITICAL') return;
      if (activeFilter === 'LOADS' && !obj.category.includes('LOAD') && obj.category !== 'SCIENCE' && obj.category !== 'HABITATION') return;
      if (activeFilter === 'THERMAL' && !obj.id.includes('heat') && !obj.id.includes('boiler') && !obj.id.includes('life')) return;

      const group = new THREE.Group();
      group.position.set(obj.position[0], obj.position[1], obj.position[2]);

      // Determine object color & dynamic state
      let hexColor = obj.color ? parseInt(obj.color.replace('#', '0x')) : 0x0284c7;
      if (obj.status === 'FAULT') hexColor = 0xe11d48;
      if (obj.status === 'STANDBY') hexColor = 0x94a3b8;

      const isSelected = selectedDeviceId && (obj.deviceId === selectedDeviceId || obj.id === selectedDeviceId);
      
      // Determine if object is part of active trace
      const isTraceActive = tracePowerActive || traceImpactActive || activeLayer === 'IMPACT';
      const isRelatedToSelection = isSelected || (selectedDeviceId && obj.circuitId && obj.circuitId.includes(selectedDeviceId));
      const objectOpacity = (isTraceActive && !isRelatedToSelection && selectedDeviceId) ? 0.25 : 1.0;

      if (obj.meshType === 'turbine') {
        // Wind Turbine: Mast + Nacelle + 3-Blade Rotor
        const mastGeo = new THREE.CylinderGeometry(0.3, 0.5, obj.dimensions[1], 12);
        const mastMat = new THREE.MeshStandardMaterial({ 
          color: 0xe2e8f0, 
          roughness: 0.3,
          transparent: objectOpacity < 1.0,
          opacity: objectOpacity
        });
        const mast = new THREE.Mesh(mastGeo, mastMat);
        mast.position.y = 0;
        mast.castShadow = true;
        group.add(mast);

        // Nacelle
        const nacelleGeo = new THREE.BoxGeometry(1.2, 0.8, 2.0);
        const nacelle = new THREE.Mesh(nacelleGeo, mastMat);
        nacelle.position.set(0, obj.dimensions[1] / 2, 0);
        group.add(nacelle);

        // Rotor Blades Group (Animated in RAF)
        const rotorGroup = new THREE.Group();
        rotorGroup.position.set(0, obj.dimensions[1] / 2, 1.1);

        const bladeGeo = new THREE.BoxGeometry(0.2, 3.8, 0.08);
        const bladeMat = new THREE.MeshStandardMaterial({ 
          color: 0x38bdf8,
          transparent: objectOpacity < 1.0,
          opacity: objectOpacity
        });

        for (let i = 0; i < 3; i++) {
          const blade = new THREE.Mesh(bladeGeo, bladeMat);
          blade.rotation.z = (i * Math.PI * 2) / 3;
          blade.position.y = 1.6 * Math.cos((i * Math.PI * 2) / 3);
          blade.position.x = 1.6 * Math.sin((i * Math.PI * 2) / 3);
          rotorGroup.add(blade);
        }
        group.add(rotorGroup);
        turbinesRef.current.push(rotorGroup);

      } else if (obj.meshType === 'cylinder') {
        // Tank / Radome / Cylinder
        const geo = new THREE.CylinderGeometry(obj.dimensions[0] / 2, obj.dimensions[0] / 2, obj.dimensions[1], 16);
        const mat = new THREE.MeshStandardMaterial({
          color: hexColor,
          roughness: 0.4,
          wireframe: wireframeOnly,
          transparent: objectOpacity < 1.0,
          opacity: objectOpacity
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        group.add(mesh);

      } else {
        // Box / Architectural Module / Panel / Generator
        const geo = new THREE.BoxGeometry(obj.dimensions[0], obj.dimensions[1], obj.dimensions[2]);
        const mat = new THREE.MeshStandardMaterial({
          color: hexColor,
          roughness: 0.5,
          wireframe: wireframeOnly,
          emissive: isSelected ? new THREE.Color(0x0284c7) : new THREE.Color(0x000000),
          emissiveIntensity: isSelected ? 0.35 : 0.0,
          transparent: objectOpacity < 1.0,
          opacity: objectOpacity
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        group.add(mesh);

        // Edges
        const edgeGeo = new THREE.EdgesGeometry(geo);
        const edgeMat = new THREE.LineBasicMaterial({
          color: isSelected ? 0x0284c7 : 0x475569,
          linewidth: isSelected ? 2 : 1,
          transparent: objectOpacity < 1.0,
          opacity: objectOpacity
        });
        const edgeLine = new THREE.LineSegments(edgeGeo, edgeMat);
        group.add(edgeLine);

        // Status indicator LED pip on top of equipment
        const ledGeo = new THREE.SphereGeometry(0.2, 8, 8);
        const ledColor = obj.status === 'ONLINE' ? 0x10b981 : (obj.status === 'FAULT' ? 0xe11d48 : 0xf59e0b);
        const ledMat = new THREE.MeshBasicMaterial({ color: ledColor });
        const led = new THREE.Mesh(ledGeo, ledMat);
        led.position.set(0, obj.dimensions[1] / 2 + 0.25, 0);
        group.add(led);
      }

      // Attach metadata for raycasting
      group.userData = { spatialObject: obj };
      scene.add(group);
      meshesRef.current.set(`obj_${obj.id}`, group);
    });

    // 3. Render 3D Directional Power Flow Paths
    stationProfile3D.powerFlowPaths.forEach(path => {
      if (path.points.length < 2) return;

      const vPoints = path.points.map(p => new THREE.Vector3(p[0], p[1], p[2]));
      const curve = new THREE.CatmullRomCurve3(vPoints);
      const points = curve.getPoints(50);
      const geo = new THREE.BufferGeometry().setFromPoints(points);

      // Determine power flow color based on circuit
      let lineColor = 0x0284c7; // Default sky-600
      let activeFlow = path.defaultActive;
      let powerKw = path.nominalKw;

      if (path.circuitId.includes('solar')) {
        lineColor = 0xf59e0b; // Gold
        activeFlow = viewModel.powerSummary.solarGenerationKw > 0.1;
        powerKw = viewModel.powerSummary.solarGenerationKw;
      } else if (path.circuitId.includes('wind')) {
        lineColor = 0x0284c7; // Blue
        activeFlow = viewModel.powerSummary.windGenerationKw > 0.1;
        powerKw = viewModel.powerSummary.windGenerationKw;
      } else if (path.circuitId.includes('diesel')) {
        lineColor = 0xb45309; // Amber
        activeFlow = viewModel.powerSummary.dieselGenerationKw > 0.1;
        powerKw = viewModel.powerSummary.dieselGenerationKw;
      } else if (path.circuitId.includes('bess')) {
        lineColor = 0x059669; // Emerald
        activeFlow = Math.abs(viewModel.powerSummary.batteryPowerKw) > 0.1;
        powerKw = Math.abs(viewModel.powerSummary.batteryPowerKw);
      }

      // Dim unrelated circuits during Trace Power / Trace Impact or Impact layer
      const isTraceMode = tracePowerActive || traceImpactActive || activeLayer === 'IMPACT';
      const isRelevantCircuit = !selectedDeviceId || path.circuitId.includes(selectedDeviceId) || path.fromId.includes(selectedDeviceId) || path.toId.includes(selectedDeviceId);
      
      let pathOpacity = activeFlow ? 0.85 : 0.2;
      if (activeLayer === 'ARCHITECTURE') {
        pathOpacity = activeFlow ? 0.35 : 0.08;
      } else if (isTraceMode) {
        pathOpacity = isRelevantCircuit ? (activeFlow ? 0.95 : 0.4) : 0.08;
      }

      const mat = new THREE.LineBasicMaterial({
        color: activeFlow ? lineColor : 0x94a3b8,
        transparent: true,
        opacity: pathOpacity,
        linewidth: Math.max(1, Math.min(4, Math.round(powerKw / 10)))
      });

      const line = new THREE.Line(geo, mat);
      scene.add(line);
      flowLinesRef.current.push(line);

      // Active energy stream particle marker along flow path (only if activeFlow and not dimmed away)
      if (activeFlow && (!isTraceMode || isRelevantCircuit)) {
        const particleGeo = new THREE.SphereGeometry(activeLayer === 'ENERGY' ? 0.3 : 0.22, 8, 8);
        const particleMat = new THREE.MeshBasicMaterial({ color: lineColor });
        const particle = new THREE.Mesh(particleGeo, particleMat);
        particle.position.copy(points[0]);
        scene.add(particle);

        flowParticlesRef.current.push({
          line,
          points,
          progress: Math.random(),
          speed: 0.006 + Math.min(0.015, powerKw / 1000),
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

  // Animation Loop (Rotors, Energy Flow Particles, Camera Smoothing)
  useEffect(() => {
    const scene = sceneRef.current;
    const renderer = rendererRef.current;
    const camera = cameraRef.current;
    if (!scene || !renderer || !camera) return;

    const animate = () => {
      // 1. Animate Wind Turbine Rotors (RPM scales with wind generation)
      const windActive = viewModel.powerSummary.windGenerationKw > 0.1;
      const rotorSpeed = windActive ? 0.045 : 0.005;
      turbinesRef.current.forEach(rotor => {
        rotor.rotation.z += rotorSpeed;
      });

      // 2. Animate Power Flow Particles along Circuit Lines
      flowParticlesRef.current.forEach(p => {
        p.progress += p.speed;
        if (p.progress >= 1.0) p.progress = 0.0;

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

      renderer.render(scene, camera);
      animFrameIdRef.current = requestAnimationFrame(animate);
    };

    animFrameIdRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, [viewModel.powerSummary.windGenerationKw]);

  // Mouse Orbit & Pan Controls
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    isDraggingRef.current = true;
    previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const camera = cameraRef.current;
    const scene = sceneRef.current;
    if (!canvas || !camera || !scene) return;

    if (isDraggingRef.current) {
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
        const panSpeed = 0.05;
        cameraTargetRef.current.x -= deltaX * panSpeed;
        cameraTargetRef.current.z += deltaY * panSpeed;
      }

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
        while (parent && !parent.userData?.spatialObject && parent.parent) {
          parent = parent.parent;
        }

        if (parent?.userData?.spatialObject) {
          setHoveredObject(parent.userData.spatialObject);
          canvas.style.cursor = 'pointer';
          return;
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
    const zoomFactor = e.deltaY * 0.03;
    cameraSphericalRef.current.radius = Math.max(
      12,
      Math.min(100, cameraSphericalRef.current.radius + zoomFactor)
    );
    updateCameraPosition();
  };

  // Click to Select Device
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
      while (parent && !parent.userData?.spatialObject && parent.parent) {
        parent = parent.parent;
      }

      if (parent?.userData?.spatialObject) {
        const obj: SpatialObject3D = parent.userData.spatialObject;
        if (obj.selectable) {
          onSelectDevice(obj.deviceId || obj.id);
          if (onSelectNode) onSelectNode(obj.id);
        }
      }
    }
  };

  // View Presets
  const setCameraPreset = (preset: 'ISOMETRIC' | 'TOP' | 'FRONT') => {
    setCameraMode(preset);
    cameraTargetRef.current.set(0, 4, 0);

    if (preset === 'ISOMETRIC') {
      cameraSphericalRef.current = { radius: 48, theta: Math.PI / 4, phi: Math.PI / 3 };
    } else if (preset === 'TOP') {
      cameraSphericalRef.current = { radius: 52, theta: 0, phi: 0.1 };
    } else if (preset === 'FRONT') {
      cameraSphericalRef.current = { radius: 45, theta: 0, phi: Math.PI / 2 - 0.1 };
    }
    updateCameraPosition();
  };

  const resetView = () => {
    setCameraPreset('ISOMETRIC');
  };

  if (!webGlAvailable) {
    return (
      <div className="bg-slate-100 rounded-lg p-8 border border-slate-200 text-center text-slate-600">
        <ShieldAlert className="w-8 h-8 text-amber-600 mx-auto mb-2" />
        <p className="font-semibold text-sm">WebGL Acceleration Unavailable</p>
        <p className="text-xs text-slate-500 mt-1">Please use the 2D Architectural schematic or Accessible Table view.</p>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className="relative w-full h-[640px] bg-slate-50 rounded-lg border border-slate-200 overflow-hidden select-none shadow-xs"
    >
      {/* Three.js Canvas */}
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        onClick={handleClick}
        onContextMenu={e => e.preventDefault()}
        className="w-full h-full block cursor-grab active:cursor-grabbing"
      />

      {/* Top Left: Station & Representative Model Disclaimer */}
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-1.5 font-mono text-[10px] pointer-events-none">
        <div className="flex items-center space-x-2 bg-white/95 px-3 py-1.5 rounded-md border border-slate-200 shadow-xs pointer-events-auto">
          <Compass className="w-3.5 h-3.5 text-sky-600" />
          <span className="font-bold text-slate-900 uppercase">
            {stationProfile3D.name}
          </span>
          <span className="text-slate-300">•</span>
          <span className="text-sky-700 font-semibold">{stationProfile3D.geometryBasis}</span>
        </div>
        <div className="bg-white/90 px-2.5 py-1 rounded text-slate-500 text-[9px] border border-slate-200 max-w-sm">
          {stationProfile3D.architectureDescription}
        </div>
      </div>

      {/* Top Right: Camera Presets, Layer Selector & View Controls */}
      <div className="absolute top-4 right-4 z-10 flex items-center space-x-1.5 bg-white/95 p-1 rounded-md border border-slate-200 shadow-xs font-mono text-[10px]">
        {/* Layer Selector */}
        <div className="flex items-center rounded bg-slate-100 p-0.5 mr-1">
          <button
            type="button"
            onClick={() => setLayer('ARCHITECTURE')}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLayer === 'ARCHITECTURE' ? 'bg-white text-slate-900 font-bold shadow-2xs' : 'text-slate-500 hover:text-slate-800'
            }`}
            title="Structural Architecture Focus"
          >
            ARCH
          </button>
          <button
            type="button"
            onClick={() => setLayer('ENERGY')}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLayer === 'ENERGY' ? 'bg-sky-600 text-white font-bold shadow-2xs' : 'text-slate-500 hover:text-slate-800'
            }`}
            title="Electrical Power Flow Focus"
          >
            ENERGY
          </button>
          <button
            type="button"
            onClick={() => setLayer('IMPACT')}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLayer === 'IMPACT' ? 'bg-amber-600 text-white font-bold shadow-2xs' : 'text-slate-500 hover:text-slate-800'
            }`}
            title="Downstream Network Impact Focus"
          >
            IMPACT
          </button>
        </div>
        <div className="w-[1px] h-4 bg-slate-200" />
        <button
          type="button"
          onClick={() => setCameraPreset('ISOMETRIC')}
          className={`px-2 py-1 rounded transition-colors ${
            cameraMode === 'ISOMETRIC' ? 'bg-sky-600 text-white font-bold' : 'text-slate-600 hover:bg-slate-100'
          }`}
          title="Isometric 3D Perspective"
        >
          3D ISO
        </button>
        <button
          type="button"
          onClick={() => setCameraPreset('TOP')}
          className={`px-2 py-1 rounded transition-colors ${
            cameraMode === 'TOP' ? 'bg-sky-600 text-white font-bold' : 'text-slate-600 hover:bg-slate-100'
          }`}
          title="Top-Down Plan View"
        >
          TOP
        </button>
        <button
          type="button"
          onClick={() => setCameraPreset('FRONT')}
          className={`px-2 py-1 rounded transition-colors ${
            cameraMode === 'FRONT' ? 'bg-sky-600 text-white font-bold' : 'text-slate-600 hover:bg-slate-100'
          }`}
          title="Front Elevation View"
        >
          ELEVATION
        </button>
        <div className="w-[1px] h-4 bg-slate-200 mx-1" />
        <button
          type="button"
          onClick={() => setWireframeOnly(!wireframeOnly)}
          className={`p-1 rounded text-slate-600 hover:text-slate-900 transition-colors ${wireframeOnly ? 'bg-slate-200' : ''}`}
          title="Toggle Wireframe Architecture"
        >
          <Box className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={resetView}
          className="p-1 rounded text-slate-600 hover:text-slate-900 transition-colors"
          title="Reset Camera Target"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Bottom Left: Navigation Hints */}
      <div className="absolute bottom-4 left-4 z-10 flex items-center space-x-2 text-[10px] font-mono text-slate-400 bg-white/90 px-2.5 py-1 rounded border border-slate-200 pointer-events-none">
        <span>LEFT-DRAG: Rotate</span>
        <span>•</span>
        <span>RIGHT-DRAG: Pan</span>
        <span>•</span>
        <span>SCROLL: Zoom</span>
        <span>•</span>
        <span>CLICK: Inspect Asset</span>
      </div>

      {/* Floating Hover HUD Card */}
      {hoveredObject && (
        <div className="absolute bottom-4 right-4 z-10 w-72 bg-white/95 rounded-lg border border-slate-200 p-3 shadow-lg font-sans pointer-events-none">
          <div className="flex items-center justify-between text-xs font-mono pb-1 border-b border-slate-100">
            <span className="font-bold text-slate-900 truncate">{hoveredObject.name}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
              hoveredObject.status === 'ONLINE' ? 'bg-emerald-50 text-emerald-700' :
              hoveredObject.status === 'FAULT' ? 'bg-rose-50 text-rose-700' : 'bg-slate-100 text-slate-600'
            }`}>
              {hoveredObject.status}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 pt-2 text-[11px] font-mono">
            <div>
              <span className="text-[9px] text-slate-400 block uppercase">IMPORTANCE</span>
              <span className="font-bold text-slate-800">{hoveredObject.importance}</span>
            </div>
            <div>
              <span className="text-[9px] text-slate-400 block uppercase">NOMINAL POWER</span>
              <span className="font-bold text-slate-800">{hoveredObject.nominalPowerKw} kW</span>
            </div>
          </div>
          {hoveredObject.realWorldContext && (
            <p className="text-[10px] text-slate-500 mt-2 font-sans leading-tight">
              {hoveredObject.realWorldContext}
            </p>
          )}
        </div>
      )}
    </div>
  );
};
