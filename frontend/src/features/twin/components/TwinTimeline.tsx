/**
 * POLARIS-EMS — Digital Twin 24-Hour Timeline Rail Component
 * Quiet Industrial / Arctic Utility Design
 * 
 * Renders the timeline playback controller, scrubber slider, speed selectors,
 * horizon switcher (24h/48h/168h), and data-driven event markers.
 */

import React from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Clock,
  Zap,
  Sparkles,
  Sun,
  Wind,
  BatteryCharging,
  AlertTriangle
} from 'lucide-react';
import { TimelineMarker } from '../model/twinTypes';

interface TwinTimelineProps {
  isPlaying: boolean;
  currentIndex: number;
  totalSteps: number;
  currentTimestamp: string;
  speed: number;
  selectedHorizon: 24 | 48 | 168;
  timelineMarkers: TimelineMarker[];
  onPlay: () => void;
  onPause: () => void;
  onTogglePlay: () => void;
  onStepForward: () => void;
  onStepBackward: () => void;
  onSeek: (index: number) => void;
  onSetSpeed: (speed: number) => void;
  onSetHorizon: (horizon: 24 | 48 | 168) => void;
}

export const TwinTimeline: React.FC<TwinTimelineProps> = ({
  isPlaying,
  currentIndex,
  totalSteps,
  currentTimestamp,
  speed,
  selectedHorizon,
  timelineMarkers = [],
  onPlay,
  onPause,
  onTogglePlay,
  onStepForward,
  onStepBackward,
  onSeek,
  onSetSpeed,
  onSetHorizon
}) => {
  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      if (isNaN(d.getTime())) return `T+${currentIndex}h`;
      return `${d.getUTCHours().toString().padStart(2, '0')}:00 UTC`;
    } catch {
      return `T+${currentIndex}h`;
    }
  };

  return (
    <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-xs space-y-3 font-sans select-none">
      {/* Top Playback Controls & Timestamp Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-100">
        {/* Play / Step Buttons */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={onTogglePlay}
            className="w-8 h-8 rounded-md bg-sky-600 hover:bg-sky-700 text-white flex items-center justify-center transition-colors shadow-xs"
            aria-label={isPlaying ? 'Pause simulation playback' : 'Start simulation playback'}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
          </button>

          <button
            type="button"
            onClick={onStepBackward}
            className="p-1.5 rounded-md hover:bg-slate-100 text-slate-600 hover:text-slate-900 transition-colors border border-slate-200"
            title="Step 1 hour backward"
          >
            <SkipBack className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={onStepForward}
            className="p-1.5 rounded-md hover:bg-slate-100 text-slate-600 hover:text-slate-900 transition-colors border border-slate-200"
            title="Step 1 hour forward"
          >
            <SkipForward className="w-3.5 h-3.5" />
          </button>

          {/* Speed Multiplier Switcher */}
          <div className="flex items-center space-x-1 pl-2 font-mono text-[10px]">
            {[1, 2, 5, 10].map(s => (
              <button
                key={`speed-${s}`}
                type="button"
                onClick={() => onSetSpeed(s)}
                className={`px-1.5 py-0.5 rounded border transition-colors ${
                  speed === s
                    ? 'bg-sky-600 text-white border-sky-600 font-bold'
                    : 'bg-white text-slate-500 border-slate-200 hover:text-slate-900'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>

        {/* Current Replay Timestamp & Step Indicator */}
        <div className="flex items-center space-x-3 font-mono text-xs">
          <div className="flex items-center space-x-1.5 text-sky-700 font-bold">
            <Clock className="w-3.5 h-3.5" />
            <span>T+{currentIndex}h • {formatTime(currentTimestamp)}</span>
          </div>

          {/* Horizon Selection */}
          <div className="flex items-center rounded-md border border-slate-200 bg-slate-50 p-0.5 text-[10px]">
            <button
              type="button"
              onClick={() => onSetHorizon(24)}
              className={`px-2 py-0.5 rounded transition-colors ${
                selectedHorizon === 24 ? 'bg-white text-slate-900 font-bold shadow-xs' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              24h
            </button>
            <button
              type="button"
              onClick={() => onSetHorizon(48)}
              className={`px-2 py-0.5 rounded transition-colors ${
                selectedHorizon === 48 ? 'bg-white text-slate-900 font-bold shadow-xs' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              48h
            </button>
            <button
              type="button"
              onClick={() => onSetHorizon(168)}
              className={`px-2 py-0.5 rounded transition-colors ${
                selectedHorizon === 168 ? 'bg-white text-slate-900 font-bold shadow-xs' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              168h
            </button>
          </div>
        </div>
      </div>

      {/* Scrubber Slider with Integrated Timeline Event Markers */}
      <div className="relative pt-1 pb-1">
        {/* Scrubber Range Input */}
        <input
          type="range"
          min={0}
          max={Math.max(1, totalSteps - 1)}
          value={currentIndex}
          onChange={(e) => onSeek(Number(e.target.value))}
          className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-sky-600 border border-slate-200"
          aria-label="Simulation timeline scrubber"
        />

        {/* Timeline Marker Pins */}
        {timelineMarkers.map((marker, idx) => {
          const leftPercent = (marker.stepIndex / Math.max(1, totalSteps - 1)) * 100;
          return (
            <div
              key={`marker-${idx}`}
              style={{ left: `${leftPercent}%` }}
              onClick={() => onSeek(marker.stepIndex)}
              className="absolute -top-1 -translate-x-1/2 cursor-pointer group z-10"
              title={`${marker.title}: ${marker.description}`}
            >
              <div className="w-2.5 h-2.5 rounded-full bg-sky-600 border border-white shadow-xs group-hover:scale-125 transition-transform" />
              <div className="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 bg-white border border-slate-200 rounded shadow-md text-[10px] font-mono text-slate-900 whitespace-nowrap z-20">
                <span className="font-bold text-sky-700 block">{marker.timeLabel}: {marker.title}</span>
                <span className="text-slate-600 text-[9px]">{marker.description}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom Marker Legends */}
      <div className="flex flex-wrap items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
        <span>T+00h START</span>
        <div className="flex items-center space-x-3">
          {timelineMarkers.slice(0, 3).map((m, i) => (
            <button
              key={`pin-${i}`}
              type="button"
              onClick={() => onSeek(m.stepIndex)}
              className="hover:text-sky-600 transition-colors"
            >
              ● {m.timeLabel} {m.title}
            </button>
          ))}
        </div>
        <span>T+{totalSteps > 0 ? totalSteps - 1 : 24}h END</span>
      </div>
    </div>
  );
};
