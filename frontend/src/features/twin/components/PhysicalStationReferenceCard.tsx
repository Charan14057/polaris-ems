import React, { useState } from 'react';
import { 
  Camera, 
  MapPin, 
  Calendar, 
  Layers, 
  ShieldCheck, 
  Maximize2, 
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sliders,
  CheckCircle2,
  Info
} from 'lucide-react';

interface PhysicalStationReferenceCardProps {
  stationId: string;
  onOpenComparisonModal: () => void;
}

interface StationGroundTruthData {
  name: string;
  nativeName: string;
  coordinates: string;
  elevation: string;
  commissioned: string;
  mandate: string;
  agency: string;
  envelope: string;
  imageSrc: string;
  caption: string;
  verifiedFeatures: string[];
}

const STATION_GROUND_TRUTH: Record<string, StationGroundTruthData> = {
  BHARATI: {
    name: 'Bharati Antarctic Research Station',
    nativeName: 'भारती अनुसंधान केंद्र',
    coordinates: '69°24′28″S, 76°11′14″E',
    elevation: '35 m ASL',
    commissioned: '18 March 2012 (31st ISEA)',
    mandate: 'Oceanography, continental breakup, atmospheric & space physics',
    agency: 'National Centre for Polar and Ocean Research (NCPOR)',
    envelope: 'Aerodynamic modular envelope on 24 heavy-duty stilts (134 standard shipping containers)',
    imageSrc: '/assets/stations/bharati_real.jpg',
    caption: 'Official field photographic record: Bharati elevated aerodynamic superstructure, Larsemann Hills.',
    verifiedFeatures: [
      'Stilt-mounted aerodynamic structure shedding severe katabatic snowdrifts',
      'Dual 25 kW Polar Wind Turbines on prominent ridge lines',
      '30 kW Tilted Roof Photovoltaic Array (35° inclination)',
      '120 kWh BESS thermal containment enclosure & tri-diesel powerhouse',
      'Rooftop high-gain satellite communication radomes & met mast'
    ]
  },
  MAITRI: {
    name: 'Maitri Antarctic Research Station',
    nativeName: 'मैत्री अनुसंधान केंद्र',
    coordinates: '70°45′57″S, 11°44′09″E',
    elevation: '117 m ASL',
    commissioned: '1989 (8th ISEA)',
    mandate: 'Geology, glaciology, terrestrial biology, human physiology',
    agency: 'National Centre for Polar and Ocean Research (NCPOR)',
    envelope: 'Central heated corridor connecting modular steel living & science blocks',
    imageSrc: '/assets/stations/maitri_real.jpg',
    caption: 'Official field photographic record: Maitri modular research habitat at Schirmacher Oasis.',
    verifiedFeatures: [
      'Central heated enclosed spine corridor linking living and operations blocks',
      'Lake Priyadarshini freshwater pumping pipeline and insulated intake house',
      'Detached powerhouse housing 3x Cummins-rated polar diesel gensets',
      '15 kW Wind turbine mast anchored into nunatak rock footing',
      'Modular containerized battery and equipment shelters'
    ]
  },
  HIMADRI: {
    name: 'Himadri Arctic Research Station',
    nativeName: 'हिमाद्रि अनुसंधान केंद्र',
    coordinates: '78°55′00″N, 11°56′00″E',
    elevation: '12 m ASL',
    commissioned: '1 July 2008 (Kings Bay, Spitsbergen)',
    mandate: 'Arctic climate change, marine biology, aerosol radiative forcing',
    agency: 'National Centre for Polar and Ocean Research (NCPOR)',
    envelope: 'Two-storey Nordic timber and steel research lodge with steep snow-shedding gables',
    imageSrc: '/assets/stations/himadri_real.jpg',
    caption: 'Official field photographic record: Himadri Arctic research station at Ny-Ålesund, Svalbard.',
    verifiedFeatures: [
      'Nordic timber research building with steep snow-shedding pitched roof',
      'Ny-Ålesund settlement 400V microgrid and district energy tie-in',
      'Roof aerosol intake stack, LIDAR optical port, and meteorological boom',
      'Coastal Arctic marine wind generation mast',
      'Dual clean chemistry labs, cold specimen archive, and computing desks'
    ]
  }
};

export const PhysicalStationReferenceCard: React.FC<PhysicalStationReferenceCardProps> = ({
  stationId,
  onOpenComparisonModal
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const data = STATION_GROUND_TRUTH[stationId.toUpperCase()] || STATION_GROUND_TRUTH.BHARATI;

  return (
    <div className="bg-white rounded-xl border border-teal-500/20 shadow-sm overflow-hidden font-sans transition-all">
      {/* Header Bar with Station Provenance */}
      <div className="bg-gradient-to-r from-slate-900 via-teal-950 to-slate-900 text-white p-3.5 px-4 flex items-center justify-between border-b border-teal-500/30">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 rounded-lg bg-teal-500/20 text-teal-300 border border-teal-500/40">
            <Camera className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-bold tracking-wider uppercase text-teal-300">
                PHYSICAL GROUND TRUTH REFERENCE
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-teal-500/30 text-teal-200 border border-teal-400/40 font-bold">
                REAL PHOTO
              </span>
            </div>
            <div className="text-sm font-bold text-white leading-tight">
              {data.name} <span className="text-teal-200/70 text-xs font-normal">({data.nativeName})</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={onOpenComparisonModal}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-mono font-bold transition-all shadow-xs"
            title="Launch Interactive 3D Twin vs Ground Truth Comparison"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Compare 3D vs Real</span>
          </button>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 text-slate-300 hover:text-white hover:bg-white/10 rounded-md transition-colors"
            title={isExpanded ? 'Collapse ground truth card' : 'Expand ground truth card'}
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-4 space-y-4 bg-slate-50/60">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start">
            {/* Medium-Sized Authentic Photo */}
            <div className="md:col-span-6 relative group overflow-hidden rounded-lg border border-slate-200 shadow-xs bg-slate-900">
              <img
                src={data.imageSrc}
                alt={data.name}
                className="w-full h-56 sm:h-64 object-cover object-center group-hover:scale-102 transition-transform duration-300"
                loading="eager"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent pointer-events-none" />
              
              <div className="absolute bottom-2 left-2 right-2 text-white text-[11px] font-sans flex items-center justify-between">
                <span className="font-mono text-[10px] text-teal-300 bg-slate-950/70 px-2 py-0.5 rounded border border-teal-500/30">
                  {data.coordinates}
                </span>
                <button
                  type="button"
                  onClick={onOpenComparisonModal}
                  className="bg-teal-600/90 hover:bg-teal-500 text-white text-[10px] font-mono px-2 py-0.5 rounded flex items-center space-x-1 shadow-xs transition-colors"
                >
                  <Maximize2 className="w-3 h-3" />
                  <span>Enlarge</span>
                </button>
              </div>
            </div>

            {/* Factual Ground Truth Specifications */}
            <div className="md:col-span-6 space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <div className="flex items-center space-x-1 text-slate-400 text-[10px] uppercase font-bold">
                    <MapPin className="w-3 h-3 text-teal-600" />
                    <span>Coordinates</span>
                  </div>
                  <div className="font-bold text-slate-800 mt-0.5 truncate">{data.coordinates}</div>
                </div>

                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <div className="flex items-center space-x-1 text-slate-400 text-[10px] uppercase font-bold">
                    <Calendar className="w-3 h-3 text-teal-600" />
                    <span>Commissioned</span>
                  </div>
                  <div className="font-bold text-slate-800 mt-0.5 truncate">{data.commissioned}</div>
                </div>

                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <div className="flex items-center space-x-1 text-slate-400 text-[10px] uppercase font-bold">
                    <Layers className="w-3 h-3 text-teal-600" />
                    <span>Elevation</span>
                  </div>
                  <div className="font-bold text-slate-800 mt-0.5 truncate">{data.elevation}</div>
                </div>

                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <div className="flex items-center space-x-1 text-slate-400 text-[10px] uppercase font-bold">
                    <ShieldCheck className="w-3 h-3 text-teal-600" />
                    <span>Operating Agency</span>
                  </div>
                  <div className="font-bold text-slate-800 mt-0.5 truncate">NCPOR / MoES</div>
                </div>
              </div>

              {/* Architectural Typology Note */}
              <div className="p-2.5 rounded-lg bg-teal-50/80 border border-teal-200/80 text-xs text-slate-700">
                <span className="font-bold text-teal-900 block mb-0.5 font-mono text-[10px] uppercase">
                  Station Architectural Envelope:
                </span>
                <span className="text-[11px] leading-relaxed">{data.envelope}</span>
              </div>

              {/* Verified Digital Twin Parity Checklist */}
              <div className="space-y-1 bg-white p-3 rounded-lg border border-slate-200 text-[11px]">
                <span className="font-bold text-slate-800 font-mono text-[10px] uppercase block mb-1">
                  3D Digital Twin Physical Model Parity:
                </span>
                <ul className="space-y-1">
                  {data.verifiedFeatures.slice(0, 3).map((feat, idx) => (
                    <li key={idx} className="flex items-start space-x-1.5 text-slate-600">
                      <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0 mt-0.5" />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
