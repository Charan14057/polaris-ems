/**
 * POLARIS-EMS — Real Base Station Ground Truth Photo Assets
 * 
 * Provides bundled Vite asset references and public path fallbacks for
 * authentic physical polar research stations (Bharati, Maitri, Himadri).
 */

import bharatiPhoto from '../../../assets/stations/bharati_real.jpg';
import maitriPhoto from '../../../assets/stations/maitri_real.jpg';
import himadriPhoto from '../../../assets/stations/himadri_real.jpg';

export const STATION_PHOTOS: Record<string, string> = {
  BHARATI: bharatiPhoto,
  MAITRI: maitriPhoto,
  HIMADRI: himadriPhoto,
};

export const PUBLIC_STATION_PHOTOS: Record<string, string> = {
  BHARATI: '/assets/stations/bharati_real.jpg',
  MAITRI: '/assets/stations/maitri_real.jpg',
  HIMADRI: '/assets/stations/himadri_real.jpg',
};

export function getStationPhoto(stationId: string): string {
  const norm = (stationId || 'BHARATI').toUpperCase();
  return STATION_PHOTOS[norm] || bharatiPhoto;
}

export function getPublicStationPhoto(stationId: string): string {
  const norm = (stationId || 'BHARATI').toUpperCase();
  return PUBLIC_STATION_PHOTOS[norm] || '/assets/stations/bharati_real.jpg';
}
