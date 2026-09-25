import React, { useState, useEffect } from 'react';
import { useStation } from '../../context/StationContext';
import { StationId } from '../../api/types';
import { useComprehension } from '../../context/ComprehensionContext';
import { 
  Compass, 
  Clock, 
  RotateCw, 
  Calendar,
  ChevronDown,
  Sparkles
} from 'lucide-react';

export const Header: React.FC = () => {
  const { 
    currentStation, 
    setStation, 
    horizonHours, 
    setHorizonHours, 
    loading, 
    refreshStationData,
    lastUpdated
  } = useStation();

  const { mode, setMode, openOrientation } = useComprehension();

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
    { id: 'BHARATI', label: 'Bharati Station', location: '69°S • Larsemann Hills, Antarctica' },
    { id: 'MAITRI', label: 'Maitri Station', location: '70°S • Schirmacher Oasis, Antarctica' },
    { id: 'HIMADRI', label: 'Himadri Station', location: '79°N • Ny-Ålesund, Svalbard, Arctic' },
  ];

  return (
    <header className="bg-surface border-b border-border sticky top-0 z-40 px-4 lg:px-6 py-3">
      <div className="max-w-[1520px] mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Brand & Editorial Title */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded bg-copper-soft border border-copper/30 flex items-center justify-center text-copper shadow-xs shrink-0">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-baseline space-x-2">
              <h1 className="text-xl font-serif font-bold text-ink-primary tracking-tight">
                POLARIS<span className="font-sans font-light text-copper text-lg tracking-normal"> • EMS</span>
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-canvas-subtle border border-border text-ink-secondary uppercase tracking-widest">
                MISSION CONTROL
              </span>
            </div>
            <p className="text-xs text-ink-muted">
              Polar Energy Management & Autonomous Resilience • SIH26061
            </p>
          </div>
        </div>

        {/* Global Controls: Tour + Mode + Station Selector + Horizon + UTC Clock */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* 60s Quick Tour Button */}
          <button
            type="button"
            onClick={openOrientation}
            className="flex items-center space-x-1.5 px-2.5 py-1.5 text-xs font-mono font-semibold rounded bg-copper-soft hover:bg-copper-soft/80 text-copper border border-copper/30 shadow-xs transition-colors shrink-0"
            title="What is Polaris-EMS? 60-second plain English orientation"
          >
            <Sparkles className="w-3.5 h-3.5 text-copper animate-pulse" />
            <span className="hidden sm:inline">60s Quick Tour</span>
            <span className="sm:hidden">Tour</span>
          </button>

          {/* Two-Layer Mode Toggle */}
          <div className="flex items-center rounded border border-border bg-canvas-subtle p-0.5 shadow-xs">
            <button
              type="button"
              onClick={() => setMode('simple')}
              className={`px-2 py-1 text-[11px] font-mono rounded transition-colors ${
                mode === 'simple'
                  ? 'bg-surface text-ink-primary shadow-xs border border-border-subtle font-bold'
                  : 'text-ink-muted hover:text-ink-primary'
              }`}
              title="Plain-language operational explanations for non-technical visitors"
            >
              Plain English
            </button>
            <button
              type="button"
              onClick={() => setMode('technical')}
              className={`px-2 py-1 text-[11px] font-mono rounded transition-colors ${
                mode === 'technical'
                  ? 'bg-surface text-copper shadow-xs border border-border-subtle font-bold'
                  : 'text-ink-muted hover:text-ink-primary'
              }`}
              title="Deep engineering formulas, solver constraints, and raw telemetry matrices"
            >
              Engineering
            </button>
          </div>

          {/* Station Selector */}
          <div className="relative">
            <label htmlFor="station-select" className="sr-only">Select Polar Station</label>
            <select
              id="station-select"
              value={currentStation}
              onChange={(e) => setStation(e.target.value as StationId)}
              className="appearance-none bg-canvas-subtle border border-border hover:border-copper/60 rounded px-3 py-1.5 pr-8 text-xs font-mono font-medium text-ink-primary cursor-pointer focus:outline-none focus:ring-1 focus:ring-copper transition-colors shadow-xs"
            >
              {stations.map((st) => (
                <option key={st.id} value={st.id}>
                  {st.label} ({st.id})
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-ink-muted absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Horizon Selector */}
          <div className="flex items-center rounded border border-border bg-canvas-subtle p-0.5 shadow-xs">
            <button
              onClick={() => setHorizonHours(48)}
              className={`px-2.5 py-1 text-xs font-mono font-medium rounded transition-colors ${
                horizonHours === 48
                  ? 'bg-surface text-ink-primary shadow-xs border border-border-subtle'
                  : 'text-ink-muted hover:text-ink-primary'
              }`}
              title="48-hour tactical dispatch horizon"
            >
              48h Horizon
            </button>
            <button
              onClick={() => setHorizonHours(168)}
              className={`px-2.5 py-1 text-xs font-mono font-medium rounded transition-colors ${
                horizonHours === 168
                  ? 'bg-surface text-ink-primary shadow-xs border border-border-subtle'
                  : 'text-ink-muted hover:text-ink-primary'
              }`}
              title="168-hour (7-day) strategic survival horizon"
            >
              168h Horizon
            </button>
          </div>

          {/* UTC Clock & Refresh */}
          <div className="flex items-center space-x-2 pl-2 border-l border-border text-ink-muted font-mono text-xs">
            <Clock className="w-3.5 h-3.5 text-ink-muted" />
            <span className="hidden sm:inline font-mono-numbers text-[11px] text-ink-secondary">
              {utcTime || 'UTC 00:00:00'}
            </span>
            <button
              onClick={refreshStationData}
              disabled={loading}
              className="p-1.5 rounded hover:bg-canvas-subtle text-ink-muted hover:text-copper transition-colors"
              title="Refresh telemetry snapshot"
              aria-label="Refresh telemetry snapshot"
            >
              <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-copper' : ''}`} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
