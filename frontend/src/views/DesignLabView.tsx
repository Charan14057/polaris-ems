import React, { useState } from 'react';
import { Palette, CheckCircle2, Shield, Eye, Layers, Compass, Sparkles, BookOpen } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';

interface DesignDirection {
  id: string;
  name: string;
  subtitle: string;
  tagline: string;
  isAdopted: boolean;
  colors: { name: string; hex: string; role: string }[];
  typography: { display: string; interface: string; metrics: string };
  philosophy: string;
  evaluation: {
    legibility: string;
    usability: string;
    accessibility: string;
    premiumCharacter: string;
    indianIdentity: string;
    polarIdentity: string;
    feasibility: string;
  };
}

export const DesignLabView: React.FC = () => {
  const directions: DesignDirection[] = [
    {
      id: 'copper_ice',
      name: 'Direction 1: Copper × Ice',
      subtitle: 'Editorial Control Room',
      tagline: 'Burnished Indian copper accents meeting glacial Antarctic blue on warm alabaster sheets.',
      isAdopted: true,
      colors: [
        { name: 'Warm Canvas', hex: '#FBF9F5', role: 'Primary background' },
        { name: 'Parchment', hex: '#F6F3EC', role: 'Inset panel surface' },
        { name: 'Burnished Copper', hex: '#B45309', role: 'Thermal & primary action accent' },
        { name: 'Glacial Ice', hex: '#0284C7', role: 'Wind, telemetry & telemetry state' },
        { name: 'Mineral Charcoal', hex: '#1C1917', role: 'High-contrast typography' },
        { name: 'Lichen Moss', hex: '#15803D', role: 'Safe state & renewable generation' },
      ],
      typography: {
        display: 'Cormorant Garamond (Editorial Serif)',
        interface: 'IBM Plex Sans / Inter',
        metrics: 'JetBrains Mono (Tabular Nums)',
      },
      philosophy:
        'Combines the quiet precision of an Antarctic scientific research log with the restrained warmth of Indian architectural craftsmanship. Generous whitespace, razor-thin borders, and crisp tabular numbers prevent cognitive fatigue in 24/7 mission control.',
      evaluation: {
        legibility: 'Exceptional. Crisp dark text on warm ivory surfaces eliminates eye strain.',
        usability: 'Mission-critical hierarchy clearly separates primary decisions from deep evidence.',
        accessibility: 'Fully compliant with WCAG 2.1 AA contrast thresholds.',
        premiumCharacter: 'High-end editorial feel akin to an industrial monograph.',
        indianIdentity: 'Subtle burnished copper and terracotta material tones without decorative ornaments.',
        polarIdentity: 'Deep ice blues, cold-wind indicators, and calm sub-zero operational palettes.',
        feasibility: 'Immediate drop-in implementation using existing Tailwind & React component architecture.',
      },
    },
    {
      id: 'monsoon_mineral',
      name: 'Direction 2: Monsoon Mineral',
      subtitle: 'Geological Field Station',
      tagline: 'Himalayan slate, wet graphite, and misted green lichen.',
      isAdopted: false,
      colors: [
        { name: 'Chalk White', hex: '#F8FAF9', role: 'Canvas' },
        { name: 'Misty Slate', hex: '#E5ECE8', role: 'Panels' },
        { name: 'Deep Graphite', hex: '#2D3748', role: 'Typography' },
        { name: 'Lichen Olive', hex: '#4D6B53', role: 'Accents' },
        { name: 'Basalt Grey', hex: '#718096', role: 'Borders' },
      ],
      typography: {
        display: 'Fraunces Variable',
        interface: 'Inter',
        metrics: 'Fira Code',
      },
      philosophy:
        'Focuses on geological longevity, drawing inspiration from weathered rock and alpine meteorological observatories.',
      evaluation: {
        legibility: 'High, though muted greens occasionally blend into grey dividers.',
        usability: 'Solid information hierarchy but slower scanning speed for emergency thresholds.',
        accessibility: 'Meets AA with careful tuning of slate tones.',
        premiumCharacter: 'Organic and architectural.',
        indianIdentity: 'Himalayan mineral sensibility.',
        polarIdentity: 'Subtle permafrost rock tones.',
        feasibility: 'Straightforward, but less visually distinct than Copper × Ice.',
      },
    },
    {
      id: 'indigo_ledger',
      name: 'Direction 3: Indigo Ledger',
      subtitle: 'Mathematical Registry',
      tagline: 'Deep vegetable indigo ink, handmade paper textures, and calligraphic rule structures.',
      isAdopted: false,
      colors: [
        { name: 'Cream Wove Paper', hex: '#FAF6EF', role: 'Canvas' },
        { name: 'Indigo Ink', hex: '#1E2958', role: 'Headlines & rules' },
        { name: 'Saffron Ochre', hex: '#C27803', role: 'Action highlight' },
        { name: 'Faded Ultramarine', hex: '#E0E7FF', role: 'Active row highlight' },
      ],
      typography: {
        display: 'Instrument Serif',
        interface: 'Source Sans 3',
        metrics: 'JetBrains Mono',
      },
      philosophy:
        'Inspired by classical archival ledgers and astronomical observatories (Jantar Mantar). Emphasizes immutable record-keeping.',
      evaluation: {
        legibility: 'High contrast between indigo and warm cream.',
        usability: 'Dense tabular layouts well-suited for validation tables.',
        accessibility: 'AA compliant.',
        premiumCharacter: 'Strong academic and archival feel.',
        indianIdentity: 'Evocative historic trade and observatory references.',
        polarIdentity: 'Weak polar connection; feels more temperate/scholarly.',
        feasibility: 'High, but feels slightly nostalgic rather than forward-looking.',
      },
    },
    {
      id: 'himalayan_instrument',
      name: 'Direction 4: Himalayan Instrument',
      subtitle: 'Alpine Precision Metric',
      tagline: 'High-altitude brass calipers, raw titanium, and meteorological field notebooks.',
      isAdopted: false,
      colors: [
        { name: 'Chalk Stone', hex: '#F5F5F0', role: 'Canvas' },
        { name: 'Weathered Brass', hex: '#9A7B38', role: 'Metric anchors' },
        { name: 'Titanium Grey', hex: '#3E424B', role: 'Headings' },
        { name: 'Glacial Cerulean', hex: '#007AA6', role: 'Telemetry' },
      ],
      typography: {
        display: 'Cinzel / Serif Display',
        interface: 'IBM Plex Sans',
        metrics: 'IBM Plex Mono',
      },
      philosophy:
        'Draws from physical survey instruments used across Karakoram and Antarctic traverse expeditions.',
      evaluation: {
        legibility: 'Good, though brass highlights require dark backdrops to maintain high contrast.',
        usability: 'Effective for instrument panels.',
        accessibility: 'Requires high-contrast borders for brass elements.',
        premiumCharacter: 'Substantial tactile weight.',
        indianIdentity: 'Expeditionary tradition.',
        polarIdentity: 'High polar resonance.',
        feasibility: 'Moderate complexity in balancing brass and grey values.',
      },
    },
    {
      id: 'polar_atelier',
      name: 'Direction 5: Polar Atelier',
      subtitle: 'Minimalist Architectural Studio',
      tagline: 'Bleached cedar, stainless hardware, and clean Scandinavian/Japanese/Indian synthesis.',
      isAdopted: false,
      colors: [
        { name: 'Pure Chalk', hex: '#FFFFFF', role: 'Canvas' },
        { name: 'Bleached Linen', hex: '#F7F7F6', role: 'Cards' },
        { name: 'Smoked Iron', hex: '#191919', role: 'Typography' },
        { name: 'Pure Crimson', hex: '#C53030', role: 'Emergency accent only' },
      ],
      typography: {
        display: 'Syne / Sans Display',
        interface: 'Inter',
        metrics: 'Space Mono',
      },
      philosophy:
        'Extreme architectural minimalism where color is forbidden except for active emergency state changes.',
      evaluation: {
        legibility: 'Maximum contrast.',
        usability: 'Very clean, but lacks emotional warmth during prolonged monitoring shifts.',
        accessibility: 'Passes AAA easily.',
        premiumCharacter: 'Contemporary gallery aesthetic.',
        indianIdentity: 'Low.',
        polarIdentity: 'High (snowfield minimalism).',
        feasibility: 'Easy, but risks feeling sterile or cold.',
      },
    },
  ];

  const [selectedDirection, setSelectedDirection] = useState<string>('copper_ice');
  const active = directions.find((d) => d.id === selectedDirection) || directions[0];

  return (
    <div className="space-y-8 max-w-[1520px] mx-auto pb-12">
      {/* Editorial Header */}
      <div className="border-b border-slate-200 pb-6">
        <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-sky-600 font-bold mb-2">
          <Palette className="w-4 h-4" />
          <span>DESIGN DIRECTION LAB & EVALUATION PLATFORM</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-sans font-bold text-slate-900 tracking-tight">
          Visual System Directions for Polaris-EMS
        </h2>
        <p className="text-sm sm:text-base text-slate-600 mt-2 max-w-3xl leading-relaxed">
          Five visual philosophies were explored to replace the generic cyber-dashboard template with an editorial, human-designed, and mission-critical design language.
        </p>
      </div>

      {/* Direction Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {directions.map((dir) => (
          <button
            key={dir.id}
            onClick={() => setSelectedDirection(dir.id)}
            className={`p-4 rounded border text-left transition-all ${
              selectedDirection === dir.id
                ? 'bg-white border-sky-600 shadow-raised ring-1 ring-copper/30'
                : 'bg-slate-50 border-slate-100 hover:border-slate-200 hover:bg-white'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-mono text-slate-500 uppercase">OPTION</span>
              {dir.isAdopted && (
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-sky-600 text-white font-bold">
                  ADOPTED
                </span>
              )}
            </div>
            <div className="text-sm font-semibold text-slate-900 font-sans">{dir.name.split(':')[1]}</div>
            <div className="text-xs text-slate-500 mt-0.5">{dir.subtitle}</div>
          </button>
        ))}
      </div>

      {/* Detailed Direction Deep-Dive */}
      <div className="bg-white border border-slate-200 shadow-xs rounded p-6 sm:p-8 space-y-8">
        {/* Title & Tagline */}
        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between border-b border-slate-100 pb-4 gap-2">
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-2xl font-sans font-bold text-slate-900">{active.name}</h3>
              {active.isAdopted && (
                <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-moss-soft text-moss border border-moss/30 flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>PRODUCTION SYSTEM BASELINE</span>
                </span>
              )}
            </div>
            <p className="text-sm text-slate-600 mt-1 font-sans">{active.tagline}</p>
          </div>
          <span className="text-xs font-mono text-slate-500">{active.subtitle}</span>
        </div>

        {/* Color Palette Swatches */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3 font-semibold">
            MATERIAL PALETTE SWATCHES
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {active.colors.map((c) => (
              <div key={c.name} className="p-3 rounded border border-slate-200 bg-white shadow-xs">
                <div
                  className="w-full h-12 rounded border border-slate-100 mb-2 shadow-inner"
                  style={{ backgroundColor: c.hex }}
                />
                <div className="text-xs font-medium text-slate-900 font-sans">{c.name}</div>
                <div className="text-[10px] font-mono text-slate-500">{c.hex}</div>
                <div className="text-[10px] text-slate-500 mt-1 leading-tight">{c.role}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Typography System */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3 font-semibold">
            TYPOGRAPHIC PAIRING
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded bg-slate-50 border border-slate-100 text-xs">
            <div>
              <span className="text-slate-500 block text-[10px] font-mono uppercase">Editorial Display:</span>
              <span className="font-semibold text-slate-900 font-sans font-semibold text-base">{active.typography.display}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] font-mono uppercase">Interface UI:</span>
              <span className="font-semibold text-slate-900 font-sans text-sm">{active.typography.interface}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] font-mono uppercase">Data & Lineage:</span>
              <span className="font-semibold text-slate-900 font-mono text-xs">{active.typography.metrics}</span>
            </div>
          </div>
        </div>

        {/* Component Previews */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3 font-semibold">
            EXAMPLE COMPONENT SPECIMENS
          </h4>
          <div className="p-5 rounded bg-canvas border border-slate-200 space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status="SAFE" />
              <StatusBadge status="WATCH" />
              <StatusBadge status="AT_RISK" />
              <StatusBadge status="CRITICAL" />
              <ProvenanceTag provenance="REAL" />
              <ProvenanceTag provenance="FORECAST" />
              <ProvenanceTag provenance="SIMULATED" />
            </div>

            <div className="p-4 rounded bg-white border border-slate-200 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-500 font-mono uppercase">BATTERY BANK SOC</span>
                <div className="text-2xl font-sans font-bold text-slate-900">68.4 <span className="text-xs font-mono font-normal text-slate-500">%</span></div>
              </div>
              <button className="px-3 py-1.5 rounded bg-sky-600 text-white text-xs font-mono font-medium hover:bg-sky-600-dark transition-colors">
                Inspect Battery Horizon →
              </button>
            </div>
          </div>
        </div>

        {/* Qualitative Evaluation Ledger */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3 font-semibold">
            QUALITATIVE EVALUATION SCORECARD
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {Object.entries(active.evaluation).map(([k, v]) => (
              <div key={k} className="p-3 rounded bg-slate-50 border border-slate-100">
                <span className="font-mono text-sky-600 font-medium uppercase text-[11px] block mb-0.5">
                  {k.replace(/([A-Z])/g, ' $1')}:
                </span>
                <span className="text-slate-600 leading-relaxed font-sans">{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
