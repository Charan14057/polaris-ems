/**
 * POLARIS-EMS — Real Base Station Ground Truth Photo Assets
 * 
 * Provides bundled Vite asset references and public path fallbacks for
 * authentic physical polar research stations (Bharati, Maitri, Himadri).
 */

import bharatiPhoto from '../../../assets/stations/bharati_real.jpg';
import maitriPhoto from '../../../assets/stations/maitri_real.jpg';
import himadriPhoto from '../../../assets/stations/himadri_real.jpg';

export type StationKey = 'BHARATI' | 'MAITRI' | 'HIMADRI';

export function normalizeStationKey(stationId?: string | null): StationKey {
  if (!stationId) return 'BHARATI';
  const upper = stationId.trim().toUpperCase();
  if (upper.includes('MAITRI')) return 'MAITRI';
  if (upper.includes('HIMADRI')) return 'HIMADRI';
  return 'BHARATI';
}

export const STATION_PHOTOS: Record<StationKey, string> = {
  BHARATI: bharatiPhoto,
  MAITRI: maitriPhoto,
  HIMADRI: himadriPhoto,
};

export const PUBLIC_STATION_PHOTOS: Record<StationKey, string> = {
  BHARATI: '/assets/stations/bharati_real.jpg',
  MAITRI: '/assets/stations/maitri_real.jpg',
  HIMADRI: '/assets/stations/himadri_real.jpg',
};

export function getStationPhoto(stationId?: string | null): string {
  const key = normalizeStationKey(stationId);
  return STATION_PHOTOS[key] || bharatiPhoto;
}

export function getPublicStationPhoto(stationId?: string | null): string {
  const key = normalizeStationKey(stationId);
  return PUBLIC_STATION_PHOTOS[key] || '/assets/stations/bharati_real.jpg';
}

