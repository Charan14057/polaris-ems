/**
 * POLARIS-EMS — Digital Twin 24-Hour Playback Controller
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Implements smooth temporal playback over trajectory states using requestAnimationFrame.
 * Manages timeline scrubbing, speed scaling, stepping, and timeline markers.
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { TimelineMarker } from '../model/twinTypes';

export interface UseTwinPlaybackOptions {
  trajectoryStates: Record<string, any>[];
  initialHorizon?: 24 | 48 | 168;
  onStepChange?: (index: number, state: Record<string, any>) => void;
}

export function useTwinPlayback(options: UseTwinPlaybackOptions) {
  const {
    trajectoryStates,
    initialHorizon = 24,
    onStepChange
  } = options;

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [speed, setSpeed] = useState<number>(1); // 1x, 2x, 5x, 10x
  const [selectedHorizon, setSelectedHorizon] = useState<24 | 48 | 168>(initialHorizon);

  const statesCount = trajectoryStates.length;
  const lastFrameTimeRef = useRef<number | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // Clamp current index when trajectory states update
  useEffect(() => {
    if (statesCount > 0 && currentIndex >= statesCount) {
      setCurrentIndex(statesCount - 1);
    }
  }, [statesCount, currentIndex]);

  // Notify parent on step change
  useEffect(() => {
    if (statesCount > 0 && trajectoryStates[currentIndex]) {
      onStepChange?.(currentIndex, trajectoryStates[currentIndex]);
    }
  }, [currentIndex, statesCount, trajectoryStates, onStepChange]);

  // Step advancement logic
  const stepForward = useCallback(() => {
    setCurrentIndex(prev => (prev + 1 < statesCount ? prev + 1 : 0));
  }, [statesCount]);

  const stepBackward = useCallback(() => {
    setCurrentIndex(prev => (prev - 1 >= 0 ? prev - 1 : statesCount - 1));
  }, [statesCount]);

  const seekTo = useCallback((index: number) => {
    const clamped = Math.max(0, Math.min(statesCount - 1, index));
    setCurrentIndex(clamped);
  }, [statesCount]);

  const togglePlay = useCallback(() => {
    setIsPlaying(prev => !prev);
  }, []);

  const play = useCallback(() => setIsPlaying(true), []);
  const pause = useCallback(() => setIsPlaying(false), []);

  // Animation frame loop
  useEffect(() => {
    if (!isPlaying || statesCount <= 1) {
      lastFrameTimeRef.current = null;
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      return;
    }

    // Interval between steps in milliseconds: base 1000ms / speed
    const stepDurationMs = 1200 / speed;

    const tick = (now: number) => {
      if (lastFrameTimeRef.current === null) {
        lastFrameTimeRef.current = now;
      }

      const elapsed = now - lastFrameTimeRef.current;
      if (elapsed >= stepDurationMs) {
        setCurrentIndex(prev => {
          if (prev + 1 >= statesCount) {
            // Loop or stop
            return 0;
          }
          return prev + 1;
        });
        lastFrameTimeRef.current = now;
      }

      animFrameRef.current = requestAnimationFrame(tick);
    };

    animFrameRef.current = requestAnimationFrame(tick);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPlaying, statesCount, speed]);

  // Derive Timeline Markers from trajectory data
  const timelineMarkers = useMemo<TimelineMarker[]>(() => {
    if (!trajectoryStates || trajectoryStates.length === 0) return [];
    const markers: TimelineMarker[] = [];

    // Find solar peak
    let maxSolar = -1;
    let maxSolarIdx = -1;
    let minWind = 999;
    let minWindIdx = -1;

    trajectoryStates.forEach((state, i) => {
      const solar = Number(state?.solar?.solar_generation_kw || 0);
      if (solar > maxSolar && solar > 5.0) {
        maxSolar = solar;
        maxSolarIdx = i;
      }
      const wind = Number(state?.wind?.wind_generation_kw || 0);
      if (wind < minWind) {
        minWind = wind;
        minWindIdx = i;
      }
    });

    if (maxSolarIdx >= 0) {
      markers.push({
        stepIndex: maxSolarIdx,
        timeLabel: `T+${maxSolarIdx}h`,
        title: 'Solar Peak Yield',
        description: `PV array generation peaks at ${maxSolar.toFixed(1)} kW.`,
        kind: 'SOLAR_PEAK'
      });
    }

    if (minWindIdx >= 0 && minWindIdx !== maxSolarIdx) {
      markers.push({
        stepIndex: minWindIdx,
        timeLabel: `T+${minWindIdx}h`,
        title: 'Wind Speed Lull',
        description: `Turbine generation eases to ${minWind.toFixed(1)} kW.`,
        kind: 'WIND_SHIFT'
      });
    }

    // Check battery night cycle
    const nightIndex = Math.min(trajectoryStates.length - 1, Math.max(18, Math.floor(trajectoryStates.length * 0.75)));
    if (nightIndex < trajectoryStates.length) {
      markers.push({
        stepIndex: nightIndex,
        timeLabel: `T+${nightIndex}h`,
        title: 'Overnight Battery Dispatch',
        description: 'BESS discharges to bridge low-sun polar evening.',
        kind: 'BATTERY_CYCLE'
      });
    }

    return markers;
  }, [trajectoryStates]);

  const currentState = trajectoryStates[currentIndex] || null;

  return {
    isPlaying,
    currentIndex,
    speed,
    selectedHorizon,
    statesCount,
    currentState,
    timelineMarkers,
    play,
    pause,
    togglePlay,
    stepForward,
    stepBackward,
    seekTo,
    setSpeed,
    setSelectedHorizon
  };
}
