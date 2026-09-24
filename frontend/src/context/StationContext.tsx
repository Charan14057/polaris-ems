import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { StationId, StationDetail, StationSummary, ReadinessResponse, ThreatIndicator } from '../api/types';
import { api } from '../api/endpoints';

interface StationContextType {
  currentStation: StationId;
  stationId: StationId;
  setStation: (station: StationId) => void;
  horizonHours: 48 | 168;
  setHorizonHours: (hours: 48 | 168) => void;
  stationDetail: StationDetail | null;
  stationSummaries: StationSummary[];
  readiness: ReadinessResponse | null;
  activeThreats: ThreatIndicator[];
  loading: boolean;
  error: string | null;
  lastUpdated: string;
  refreshStationData: () => Promise<void>;
}

const StationContext = createContext<StationContextType | undefined>(undefined);

export const StationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentStation, setCurrentStation] = useState<StationId>('BHARATI');
  const [horizonHours, setHorizonHours] = useState<48 | 168>(48);
  const [stationDetail, setStationDetail] = useState<StationDetail | null>(null);
  const [stationSummaries, setStationSummaries] = useState<StationSummary[]>([]);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [activeThreats, setActiveThreats] = useState<ThreatIndicator[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>(new Date().toISOString());

  const fetchStationData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [readinessRes, listRes, detailRes, resilienceRes] = await Promise.all([
        api.getReadiness().catch(() => null),
        api.listStations().catch(() => null),
        api.getStationDetail(currentStation).catch(() => null),
        api.evaluateResilience({ station_id: currentStation, horizon_hours: horizonHours }).catch(() => null),
      ]);

      if (readinessRes?.data) setReadiness(readinessRes.data);
      if (listRes?.data) setStationSummaries(listRes.data);
      if (detailRes?.data) setStationDetail(detailRes.data);
      if (resilienceRes?.data?.threat_decomposition) {
        setActiveThreats(resilienceRes.data.threat_decomposition);
      } else {
        setActiveThreats([]);
      }

      setLastUpdated(new Date().toISOString());
    } catch (err: any) {
      setError(err.message || 'Failed to connect to Polaris-EMS API');
    } finally {
      setLoading(false);
    }
  }, [currentStation, horizonHours]);

  useEffect(() => {
    fetchStationData();
  }, [fetchStationData]);

  const value: StationContextType = {
    currentStation,
    stationId: currentStation,
    setStation: (s: StationId) => setCurrentStation(s),
    horizonHours,
    setHorizonHours,
    stationDetail,
    stationSummaries,
    readiness,
    activeThreats,
    loading,
    error,
    lastUpdated,
    refreshStationData: fetchStationData,
  };

  return <StationContext.Provider value={value}>{children}</StationContext.Provider>;
};

export const useStation = () => {
  const context = useContext(StationContext);
  if (!context) {
    throw new Error('useStation must be used within a StationProvider');
  }
  return context;
};
