/**
 * POLARIS-EMS — Digital Twin Selection & Tracing Hook
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Manages interactive node/zone/device selection, category filtering,
 * Trace My Power mode, Trace Impact mode, and fault injection toggles.
 */

import { useState, useCallback } from 'react';
import { TwinDeviceFilter } from '../model/twinTypes';

export function useTwinSelection() {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<TwinDeviceFilter>('ALL');
  const [tracePowerActive, setTracePowerActive] = useState<boolean>(false);
  const [traceImpactActive, setTraceImpactActive] = useState<boolean>(false);
  const [faultedCircuitIds, setFaultedCircuitIds] = useState<Set<string>>(new Set<string>());

  const selectNode = useCallback((nodeId: string | null) => {
    setSelectedNodeId(nodeId);
    if (!nodeId) {
      setSelectedDeviceId(null);
      setTracePowerActive(false);
      setTraceImpactActive(false);
    }
  }, []);

  const selectZone = useCallback((zoneId: string | null) => {
    setSelectedZoneId(zoneId);
  }, []);

  const selectDevice = useCallback((deviceId: string | null) => {
    setSelectedDeviceId(deviceId);
    if (!deviceId) {
      setTracePowerActive(false);
    }
  }, []);

  const toggleTracePower = useCallback(() => {
    setTracePowerActive(prev => !prev);
    setTraceImpactActive(false);
  }, []);

  const toggleTraceImpact = useCallback(() => {
    setTraceImpactActive(prev => !prev);
    setTracePowerActive(false);
  }, []);

  const toggleCircuitFault = useCallback((circuitId: string) => {
    setFaultedCircuitIds(prev => {
      const next = new Set(prev);
      if (next.has(circuitId)) {
        next.delete(circuitId);
      } else {
        next.add(circuitId);
      }
      return next;
    });
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedNodeId(null);
    setSelectedZoneId(null);
    setSelectedDeviceId(null);
    setTracePowerActive(false);
    setTraceImpactActive(false);
  }, []);

  return {
    selectedNodeId,
    selectedZoneId,
    selectedDeviceId,
    activeFilter,
    tracePowerActive,
    traceImpactActive,
    faultedCircuitIds,
    selectNode,
    selectZone,
    selectDevice,
    setActiveFilter,
    toggleTracePower,
    toggleTraceImpact,
    toggleCircuitFault,
    clearSelection
  };
}
