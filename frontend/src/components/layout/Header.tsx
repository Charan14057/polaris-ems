import React, { useState, useEffect } from 'react';
import { useStation } from '../../context/StationContext';
import { StationId } from '../../api/types';
import { 
  Compass, 
  Clock, 
  Activity, 
  RotateCw, 
  Layers, 
  Radio
} from 'lucide-react';

export const Header: React.FC = () => {
  const { 
    currentStation, 
    setStation, 
    horizonHours, 
    setHorizonHours, 
    stationDetail,
    readiness, 
    loading, 
    refreshStationData,
    lastUpdated
  } = useStation();

  const [utcTime, setUtcTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const stations: { id: StationId; label: string; location: string }[] = [
    { id: 'BHARATI', label: 'Bharati', location: 'Larsemann Hills (Antarctica)' },
    { id: 'MAITRI', label: 'Maitri', location: 'Schirmacher Oasis (Antarctica)' },
    { id: 'HIMADRI', label: 'Himadri', location: 'Ny-Ålesund, Svalbard (Arctic)' },
  ];

  return (
    <header className="bg-polar-950/90 border-b border-polar-800/80 sticky top-0 z-50 backdrop-blur-md px-4 lg:px-6 py-2.5">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Brand & Subtitle */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-sm shadow-cyan-900/30">
            <Compass className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold text-polar-50 tracking-wider font-mono">
                POLARIS<span className="text-cyan-400 font-sans font-light">EMS</span>
              </h1>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 font-medium">
                PRODUCTION
              </span>
              <span className="hidden sm:inline text-[10px] font-mono px-1.5 py-0.5 rounded bg-polar-800 border border-polar-700 text-polar-300">
                ADVISORY
              </span>
            </div>
            <p className="text-[11px] text-polar-400">
              Polar Energy Management &amp; Resilience System • Mission Control
            </p>
          </div>
        </div>

        {/* Station Selector, Horizon Switcher, Clocks & Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Station Selector Buttons */}
          <div className="flex items-center bg-polar-900/90 border border-polar-750 p-0.5 rounded-lg">
            {stations.map((stn) => (
              <button
                key={stn.id}
                onClick={() => setStation(stn.id)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                  currentStation === stn.id
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-polar-400 hover:text-polar-200'
                }`}
                title={stn.location}
              >
                {stn.label}
              </button>
            ))}
          </div>

          {/* Horizon Switcher: 48h vs 168h */}
          <div className="flex items-center bg-polar-900/90 border border-polar-750 p-0.5 rounded-lg" title="Planning Horizon">
            <button
              onClick={() => setHorizonHours(48)}
              className={`px-2.5 py-1 text-xs font-mono rounded-md transition-all ${
                horizonHours === 48
                  ? 'bg-polar-700 text-polar-100 font-semibold'
                  : 'text-polar-400 hover:text-polar-200'
              }`}
            >
              48h Ops
            </button>
            <button
              onClick={() => setHorizonHours(168)}
              className={`px-2.5 py-1 text-xs font-mono rounded-md transition-all ${
                horizonHours === 168
                  ? 'bg-polar-700 text-polar-100 font-semibold'
                  : 'text-polar-400 hover:text-polar-200'
              }`}
            >
              168h Strategic
            </button>
          </div>

          {/* Live UTC & Snapshot Clock */}
          <div className="hidden xl:flex items-center space-x-2 text-[11px] font-mono bg-polar-900/60 border border-polar-800 px-2.5 py-1 rounded-md text-polar-300">
            <Clock className="w-3.5 h-3.5 text-polar-400" />
            <span className="font-mono-numbers">{utcTime}</span>
          </div>

          {/* SCADA Hardware Status Disclaimer */}
          <div 
            className="hidden lg:flex items-center space-x-1.5 px-2 py-1 rounded-md text-[11px] font-mono border bg-amber-950/30 border-amber-500/30 text-amber-300"
            title="Current deployment constraint: Zero physical polar SCADA connected; operating in physics-calibrated digital twin mode."
          >
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
            <span>SCADA: SIMULATION ONLY</span>
          </div>

          {/* Readiness Probe Status */}
          <div 
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-mono border ${
              readiness?.ready
                ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400'
                : 'bg-red-950/40 border-red-500/30 text-red-400'
            }`}
            title={`Readiness: ${readiness?.ready ? 'All 3 stations & 14 scenarios online' : 'System Degraded'}`}
          >
            <Radio className="w-3 h-3 animate-pulse" />
            <span>{readiness?.ready ? 'API ONLINE' : 'DISCONNECTED'}</span>
          </div>

          {/* Refresh Button */}
          <button
            onClick={refreshStationData}
            disabled={loading}
            className="p-1.5 text-polar-400 hover:text-polar-200 hover:bg-polar-800 rounded-md transition-colors border border-polar-800"
            title={`Last Updated: ${lastUpdated}. Click to refresh.`}
            aria-label="Refresh Station Data"
          >
            <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
