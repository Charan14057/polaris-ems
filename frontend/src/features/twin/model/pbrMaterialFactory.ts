/**
 * POLARIS-EMS — Procedural PBR Material & Texture Factory
 * Phase 18: Operational 3D Digital Twin Engine
 * 
 * Generates lightweight, procedural canvas textures (corrugated metal, solar cells,
 * diamond tread plate, concrete, brushed steel) and physically accurate Three.js
 * PBR materials for an industrial research-station digital twin.
 * 
 * ZERO external network asset downloads. 100% self-contained WebGL procedural generation.
 */

import * as THREE from 'three';

// Cache generated procedural textures to avoid redundant canvas operations
let corrugatedTextureCache: THREE.CanvasTexture | null = null;
let solarCellTextureCache: THREE.CanvasTexture | null = null;
let diamondPlateTextureCache: THREE.CanvasTexture | null = null;
let concreteTextureCache: THREE.CanvasTexture | null = null;
let brushedMetalTextureCache: THREE.CanvasTexture | null = null;

function createProceduralTexture(
  width: number,
  height: number,
  drawFn: (ctx: CanvasRenderingContext2D) => void,
  repeatX: number = 1,
  repeatY: number = 1
): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  try {
    const ctx = canvas.getContext('2d');
    if (ctx) {
      drawFn(ctx);
    }
  } catch {
    // Graceful fallback for non-browser jsdom environments
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(repeatX, repeatY);
  return texture;
}

/**
 * 1. Corrugated Insulated Metal Cladding Texture
 * Creates alternating vertical shadow/highlight ribs for containers & station walls.
 */
export function getCorrugatedTexture(): THREE.CanvasTexture {
  if (corrugatedTextureCache) return corrugatedTextureCache;

  corrugatedTextureCache = createProceduralTexture(128, 128, (ctx) => {
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, 128, 128);

    const ribWidth = 16;
    for (let x = 0; x < 128; x += ribWidth) {
      const grad = ctx.createLinearGradient(x, 0, x + ribWidth, 0);
      grad.addColorStop(0.0, '#555555');
      grad.addColorStop(0.2, '#999999');
      grad.addColorStop(0.5, '#ffffff');
      grad.addColorStop(0.8, '#999999');
      grad.addColorStop(1.0, '#444444');
      ctx.fillStyle = grad;
      ctx.fillRect(x, 0, ribWidth - 2, 128);
    }
  }, 4, 2);

  return corrugatedTextureCache;
}

/**
 * 2. Monocrystalline Solar Photovoltaic Cell Texture
 * Deep silicon blue with anti-reflective busbars and thin contact fingers.
 */
export function getSolarCellTexture(): THREE.CanvasTexture {
  if (solarCellTextureCache) return solarCellTextureCache;

  solarCellTextureCache = createProceduralTexture(256, 256, (ctx) => {
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, 256, 256);

    const grad = ctx.createLinearGradient(0, 0, 256, 256);
    grad.addColorStop(0.0, '#1e293b');
    grad.addColorStop(0.5, '#0f172a');
    grad.addColorStop(1.0, '#1e3a8a');
    ctx.fillStyle = grad;
    ctx.fillRect(2, 2, 252, 252);

    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(64, 0); ctx.lineTo(64, 256);
    ctx.moveTo(128, 0); ctx.lineTo(128, 256);
    ctx.moveTo(192, 0); ctx.lineTo(192, 256);
    ctx.stroke();

    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 0.8;
    ctx.globalAlpha = 0.45;
    for (let y = 8; y < 256; y += 8) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(256, y);
      ctx.stroke();
    }
    ctx.globalAlpha = 1.0;
  }, 6, 4);

  return solarCellTextureCache;
}

/**
 * 3. Non-Slip Diamond Plate Steel Texture
 * Used for helipad, access stairs, gangways, and equipment skid bases.
 */
export function getDiamondPlateTexture(): THREE.CanvasTexture {
  if (diamondPlateTextureCache) return diamondPlateTextureCache;

  diamondPlateTextureCache = createProceduralTexture(128, 128, (ctx) => {
    ctx.fillStyle = '#64748b';
    ctx.fillRect(0, 0, 128, 128);

    ctx.fillStyle = '#94a3b8';
    for (let x = 8; x < 128; x += 32) {
      for (let y = 8; y < 128; y += 32) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(Math.PI / 4);
        ctx.fillRect(-6, -2, 12, 4);
        ctx.restore();

        ctx.save();
        ctx.translate(x + 16, y + 16);
        ctx.rotate(-Math.PI / 4);
        ctx.fillRect(-6, -2, 12, 4);
        ctx.restore();
      }
    }
  }, 8, 8);

  return diamondPlateTextureCache;
}

/**
 * 4. Concrete Foundation & Equipment Pedestal Texture
 */
export function getConcreteTexture(): THREE.CanvasTexture {
  if (concreteTextureCache) return concreteTextureCache;

  concreteTextureCache = createProceduralTexture(128, 128, (ctx) => {
    ctx.fillStyle = '#94a3b8';
    ctx.fillRect(0, 0, 128, 128);

    for (let i = 0; i < 600; i++) {
      const x = Math.random() * 128;
      const y = Math.random() * 128;
      const gray = Math.floor(80 + Math.random() * 60);
      ctx.fillStyle = `rgb(${gray},${gray},${gray})`;
      ctx.fillRect(x, y, 1.5, 1.5);
    }

    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, 64); ctx.lineTo(128, 64);
    ctx.moveTo(64, 0); ctx.lineTo(64, 128);
    ctx.stroke();
  }, 2, 2);

  return concreteTextureCache;
}

/**
 * 5. Brushed Galvanized Steel Texture
 */
export function getBrushedMetalTexture(): THREE.CanvasTexture {
  if (brushedMetalTextureCache) return brushedMetalTextureCache;

  brushedMetalTextureCache = createProceduralTexture(128, 128, (ctx) => {
    ctx.fillStyle = '#cbd5e1';
    ctx.fillRect(0, 0, 128, 128);

    ctx.fillStyle = '#94a3b8';
    for (let i = 0; i < 400; i++) {
      const y = Math.random() * 128;
      ctx.fillRect(0, y, 128, 0.8);
    }
  }, 1, 4);

  return brushedMetalTextureCache;
}

// =============================================================================
// STANDARDIZED PBR MATERIAL CREATORS
// =============================================================================

export interface MaterialOptions {
  wireframe?: boolean;
  transparent?: boolean;
  opacity?: number;
}

export function createInsulatedCladdingMaterial(
  color: number,
  options: MaterialOptions = {}
): THREE.MeshStandardMaterial {
  const bump = getCorrugatedTexture();
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.42,
    metalness: 0.35,
    bumpMap: bump,
    bumpScale: 0.04,
    wireframe: options.wireframe ?? false,
    transparent: options.transparent ?? false,
    opacity: options.opacity ?? 1.0
  });
}

export function createStructuralSteelMaterial(
  color: number = 0x475569,
  options: MaterialOptions = {}
): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.38,
    metalness: 0.78,
    wireframe: options.wireframe ?? false,
    transparent: options.transparent ?? false,
    opacity: options.opacity ?? 1.0
  });
}

export function createGalvanizedLegMaterial(
  options: MaterialOptions = {}
): THREE.MeshStandardMaterial {
  const map = getBrushedMetalTexture();
  return new THREE.MeshStandardMaterial({
    color: 0x94a3b8,
    roughness: 0.32,
    metalness: 0.85,
    bumpMap: map,
    bumpScale: 0.02,
    wireframe: options.wireframe ?? false
  });
}

export function createPhotovoltaicMaterial(
  options: MaterialOptions = {}
): THREE.MeshStandardMaterial {
  const map = getSolarCellTexture();
  return new THREE.MeshStandardMaterial({
    color: 0x1d4ed8,
    roughness: 0.18,
    metalness: 0.75,
    map,
    wireframe: options.wireframe ?? false
  });
}

export function createConcreteFoundationMaterial(
  options: MaterialOptions = {}
): THREE.MeshStandardMaterial {
  const map = getConcreteTexture();
  return new THREE.MeshStandardMaterial({
    color: 0x64748b,
    roughness: 0.88,
    metalness: 0.08,
    map,
    wireframe: options.wireframe ?? false
  });
}

export function createIndustrialGlassMaterial(
  warmGlow: boolean = true,
  glowIntensity: number = 0.65,
  options: MaterialOptions = {}
): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color: 0x0f172a,
    emissive: warmGlow ? 0xfef08a : 0x38bdf8,
    emissiveIntensity: glowIntensity,
    roughness: 0.12,
    metalness: 0.85,
    transparent: true,
    opacity: options.opacity ?? 0.85,
    wireframe: options.wireframe ?? false
  });
}

/**
 * 6. High-Fidelity Polar Aerodynamic Composite Cladding Texture
 * Generates realistic architectural composite cassette panels with recessed joints & rivets.
 */
let compositePanelTextureCache: THREE.CanvasTexture | null = null;
export function getCompositePanelTexture(): THREE.CanvasTexture {
  if (compositePanelTextureCache) return compositePanelTextureCache;

  compositePanelTextureCache = createProceduralTexture(256, 256, (ctx) => {
    // Base metallic panel sheen
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, 256, 256);

    // Subtle brushed horizontal gradient
    const grad = ctx.createLinearGradient(0, 0, 0, 256);
    grad.addColorStop(0.0, 'rgba(255,255,255,0.4)');
    grad.addColorStop(0.5, 'rgba(200,215,230,0.1)');
    grad.addColorStop(1.0, 'rgba(150,170,190,0.3)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 256, 256);

    // Panel Seams / Reveals
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 2.5;
    ctx.strokeRect(2, 2, 252, 252);
    ctx.beginPath();
    ctx.moveTo(128, 0); ctx.lineTo(128, 256);
    ctx.moveTo(0, 128); ctx.lineTo(256, 128);
    ctx.stroke();

    // Rivet / fastener points
    ctx.fillStyle = '#475569';
    const rivets = [
      [8, 8], [120, 8], [136, 8], [248, 8],
      [8, 120], [120, 120], [136, 120], [248, 120],
      [8, 136], [120, 136], [136, 136], [248, 136],
      [8, 248], [120, 248], [136, 248], [248, 248]
    ];
    rivets.forEach(([rx, ry]) => {
      ctx.beginPath();
      ctx.arc(rx, ry, 2, 0, Math.PI * 2);
      ctx.fill();
    });
  }, 4, 2);

  return compositePanelTextureCache;
}

/**
 * 7. Wind-Carved Sastrugi Snow & Ice Crust Texture
 */
let sastrugiTextureCache: THREE.CanvasTexture | null = null;
export function getSastrugiTexture(): THREE.CanvasTexture {
  if (sastrugiTextureCache) return sastrugiTextureCache;

  sastrugiTextureCache = createProceduralTexture(256, 256, (ctx) => {
    ctx.fillStyle = '#e2e8f0';
    ctx.fillRect(0, 0, 256, 256);

    // Wind wave streaks (sastrugi drifts)
    for (let y = 0; y < 256; y += 12) {
      const grad = ctx.createLinearGradient(0, y, 256, y + 8);
      grad.addColorStop(0.0, '#ffffff');
      grad.addColorStop(0.4, '#dbeafe');
      grad.addColorStop(0.7, '#cbd5e1');
      grad.addColorStop(1.0, '#f1f5f9');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.bezierCurveTo(80, y + Math.sin(y) * 4, 180, y - Math.cos(y) * 4, 256, y);
      ctx.lineTo(256, y + 10);
      ctx.bezierCurveTo(180, y + 10, 80, y + 10, 0, y + 10);
      ctx.closePath();
      ctx.fill();
    }
  }, 8, 8);

  return sastrugiTextureCache;
}

/**
 * 8. Antarctic Gneiss & Charnockite Bedrock Texture
 */
let bedrockTextureCache: THREE.CanvasTexture | null = null;
export function getBedrockTexture(): THREE.CanvasTexture {
  if (bedrockTextureCache) return bedrockTextureCache;

  bedrockTextureCache = createProceduralTexture(256, 256, (ctx) => {
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, 256, 256);

    // Speckles of feldspar & quartz crystals
    for (let i = 0; i < 800; i++) {
      const x = Math.random() * 256;
      const y = Math.random() * 256;
      const r = Math.random() * 2;
      const c = Math.floor(100 + Math.random() * 120);
      ctx.fillStyle = `rgb(${c},${c - 15},${c - 20})`;
      ctx.fillRect(x, y, r, r);
    }
  }, 4, 4);

  return bedrockTextureCache;
}

export function createPolarCompositeMaterial(
  color: number,
  options: MaterialOptions = {}
): THREE.MeshStandardMaterial {
  const bump = getCompositePanelTexture();
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.35,
    metalness: 0.45,
    bumpMap: bump,
    bumpScale: 0.03,
    wireframe: options.wireframe ?? false,
    transparent: options.transparent ?? false,
    opacity: options.opacity ?? 1.0
  });
}

export function createPolarSnowMaterial(
  options: MaterialOptions = {}
): THREE.MeshStandardMaterial {
  const bump = getSastrugiTexture();
  return new THREE.MeshStandardMaterial({
    color: 0xeff6ff,
    roughness: 0.72,
    metalness: 0.08,
    bumpMap: bump,
    bumpScale: 0.06,
    wireframe: options.wireframe ?? false
  });
}

export function createBedrockMaterial(
  options: MaterialOptions = {}
): THREE.MeshStandardMaterial {
  const bump = getBedrockTexture();
  return new THREE.MeshStandardMaterial({
    color: 0x334155,
    roughness: 0.92,
    metalness: 0.15,
    bumpMap: bump,
    bumpScale: 0.05,
    wireframe: options.wireframe ?? false
  });
}

