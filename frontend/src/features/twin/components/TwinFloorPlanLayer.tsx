/**
 * POLARIS-EMS — Authentic 2D Architectural Floor Plan & Hull Envelope Layer
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders the authentic architectural station footprint, aerodynamic hull silhouettes,
 * structural steel stilt column grids, airlocks, helipads, and utilidors
 * based on bof-architekten / NCPOR engineering drawings.
 */

import React from 'react';

interface TwinFloorPlanLayerProps {
  stationId: string;
  theme?: 'SCADA' | 'BLUEPRINT';
}

export const TwinFloorPlanLayer: React.FC<TwinFloorPlanLayerProps> = ({
  stationId,
  theme = 'SCADA'
}) => {
  const isScada = theme === 'SCADA';
  const station = stationId.toUpperCase();

  const hullStroke = isScada ? '#1e3a5f' : '#cbd5e1';
  const hullFill = isScada ? 'rgba(8, 17, 36, 0.45)' : 'rgba(248, 250, 252, 0.6)';
  const colStroke = isScada ? '#0284c7' : '#64748b';
  const colFill = isScada ? '#0f172a' : '#ffffff';
  const gridLineStroke = isScada ? 'rgba(30, 58, 95, 0.35)' : 'rgba(203, 213, 225, 0.6)';
  const cadTextFill = isScada ? '#64748b' : '#94a3b8';

  if (station === 'MAITRI') {
    return (
      <g className="twin-floorplan-layer pointer-events-none select-none">
        {/* Central Spine Corridor Footprint */}
        <rect
          x={30}
          y={255}
          width={940}
          height={30}
          rx={4}
          fill={hullFill}
          stroke={hullStroke}
          strokeWidth={1.5}
        />
        <text x={500} y={274} textAnchor="middle" className="font-mono text-[9px] font-bold tracking-widest" fill={cadTextFill}>
          MAITRI CENTRAL HEATED TRANSIT SPINE CORRIDOR (34.0m)
        </text>

        {/* Lake Priyadarshini Overland Insulated Pipeline */}
        <path
          d="M 680 440 L 960 440 L 960 560 L 980 560"
          fill="none"
          stroke={isScada ? '#0284c7' : '#38bdf8'}
          strokeWidth={2.5}
          strokeDasharray="6 3"
        />
        <text x={950} y={575} textAnchor="end" className="font-mono text-[8px] font-semibold" fill={cadTextFill}>
          LAKE PRIYADARSHINI WATER INTAKE TRESTLE
        </text>
      </g>
    );
  }

  if (station === 'HIMADRI') {
    return (
      <g className="twin-floorplan-layer pointer-events-none select-none">
        {/* Nordic Research Lodge Perimeter */}
        <rect
          x={50}
          y={40}
          width={900}
          height={560}
          rx={6}
          fill={hullFill}
          stroke={hullStroke}
          strokeWidth={1.5}
        />
        <text x={500} y={320} textAnchor="middle" className="font-mono text-[9px] font-bold tracking-widest" fill={cadTextFill}>
          NY-ÅLESUND HIMADRI TWO-STOREY TIMBER RESEARCH BASE
        </text>
      </g>
    );
  }

  // DEFAULT: BHARATI (Aerodynamic Pods & bof-architekten Hull Specification)
  return (
    <g className="twin-floorplan-layer pointer-events-none select-none">
      {/* 1. Structural Architectural Grid Lines (Axis A-H, 1-3) */}
      <g stroke={gridLineStroke} strokeWidth={1} strokeDasharray="3 3">
        {/* Horizontal Grids */}
        <line x1={20} y1={150} x2={980} y2={150} />
        <line x1={20} y1={270} x2={980} y2={270} />
        <line x1={20} y1={445} x2={980} y2={445} />

        {/* Vertical Grids */}
        <line x1={180} y1={20} x2={180} y2={610} />
        <line x1={340} y1={20} x2={340} y2={610} />
        <line x1={500} y1={20} x2={500} y2={610} />
        <line x1={660} y1={20} x2={660} y2={610} />
        <line x1={820} y1={20} x2={820} y2={610} />
      </g>

      {/* Grid Axis Labels */}
      <g className="font-mono text-[8px] font-bold" fill={cadTextFill}>
        <text x={26} y={154}>AXIS 1</text>
        <text x={26} y={274}>AXIS 2 (MAIN BUS)</text>
        <text x={26} y={449}>AXIS 3</text>
        <text x={180} y={32} textAnchor="middle">SEC-A</text>
        <text x={340} y={32} textAnchor="middle">SEC-B</text>
        <text x={500} y={32} textAnchor="middle">SEC-C</text>
        <text x={660} y={32} textAnchor="middle">SEC-D</text>
        <text x={820} y={32} textAnchor="middle">SEC-E</text>
      </g>

      {/* 2. Main Aerodynamic Outer Hull Perimeter Envelope (Bharati bof-architekten pod) */}
      {/* Outer Insulated Shell */}
      <path
        d="M 120 28 C 30 28, 20 120, 20 270 C 20 420, 30 612, 120 612 L 880 612 C 970 612, 980 420, 980 270 C 980 120, 970 28, 880 28 Z"
        fill={hullFill}
        stroke={hullStroke}
        strokeWidth={1.8}
      />

      {/* Inner Thermal Barrier Double Wall (200mm PIR Sandwich Composite) */}
      <path
        d="M 124 36 C 42 36, 28 124, 28 270 C 28 416, 42 604, 124 604 L 876 604 C 958 604, 972 416, 972 270 C 972 124, 958 36, 876 36 Z"
        fill="none"
        stroke={hullStroke}
        strokeWidth={1}
        strokeDasharray="4 2"
        opacity={0.7}
      />

      {/* 3. Structural Foundation Stilts (24 Heavy Tubular Steel Piles at Bedrock Anchor Points) */}
      {[
        { x: 100, y: 150 }, { x: 220, y: 150 }, { x: 340, y: 150 }, { x: 500, y: 150 }, { x: 660, y: 150 }, { x: 820, y: 150 },
        { x: 100, y: 270 }, { x: 220, y: 270 }, { x: 340, y: 270 }, { x: 500, y: 270 }, { x: 660, y: 270 }, { x: 820, y: 270 },
        { x: 100, y: 445 }, { x: 220, y: 445 }, { x: 340, y: 445 }, { x: 500, y: 445 }, { x: 660, y: 445 }, { x: 820, y: 445 }
      ].map((pt, idx) => (
        <g key={`stilt-${idx}`} transform={`translate(${pt.x}, ${pt.y})`}>
          <circle cx={0} cy={0} r={6} fill={colFill} stroke={colStroke} strokeWidth={1.2} />
          <line x1={-8} y1={0} x2={8} y2={0} stroke={colStroke} strokeWidth={0.8} />
          <line x1={0} y1={-8} x2={0} y2={8} stroke={colStroke} strokeWidth={0.8} />
        </g>
      ))}

      {/* 4. Exterior Pedestrian Access Gangway Ramp on South Elevation */}
      <g transform="translate(480, 595)">
        <rect x={-20} y={0} width={40} height={35} rx={3} fill={colFill} stroke={hullStroke} strokeWidth={1.5} />
        {/* Tread steps */}
        <line x1={-18} y1={8} x2={18} y2={8} stroke={hullStroke} strokeWidth={1} />
        <line x1={-18} y1={16} x2={18} y2={16} stroke={hullStroke} strokeWidth={1} />
        <line x1={-18} y1={24} x2={18} y2={24} stroke={hullStroke} strokeWidth={1} />
        <text x={0} y={32} textAnchor="middle" className="font-mono text-[7px] font-bold" fill={cadTextFill}>
          AIRLOCK 01
        </text>
      </g>

      {/* 5. Blue Insulated Seawater Intake utilidor route */}
      <path
        d="M 40 520 L 15 520 L 15 625 L 90 625"
        fill="none"
        stroke={isScada ? '#0284c7' : '#0369a1'}
        strokeWidth={2}
        strokeDasharray="4 2"
      />
      <text x={20} y={635} className="font-mono text-[7px] font-semibold" fill={isScada ? '#38bdf8' : '#0284c7'}>
        SEAWATER INTAKE UTILIDOR
      </text>

      {/* 6. Technical Drafting Notes Stamp (Bottom Left) */}
      <g transform="translate(45, 600)">
        <text className="font-mono text-[8px] font-bold uppercase tracking-wider" fill={cadTextFill}>
          STATION: BHARATI (BOF-ARCHITEKTEN SPEC • +4.2m ELEVATED STILTS)
        </text>
      </g>
    </g>
  );
};
