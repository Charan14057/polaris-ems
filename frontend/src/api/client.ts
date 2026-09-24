/**
 * POLARIS-EMS — Typed API Client
 * SIH26061: Polar Energy Management & Resilience System
 * 
 * Centralized HTTP request handling, correlation ID injection,
 * and unified response envelope parsing for Phase 9 FastAPI backend.
 */

import { APIResponse } from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export class PolarisAPIError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public details?: any,
    public correlationId?: string
  ) {
    super(message);
    this.name = 'PolarisAPIError';
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<APIResponse<T>> {
  const reqId = `req-ui-${Math.random().toString(36).substring(2, 10)}`;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Request-ID': reqId,
    ...(options.headers as Record<string, string> || {}),
  };

  const url = `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const body: APIResponse<T> = await response.json();

    if (!response.ok) {
      const errCode = body?.error?.code || `HTTP_${response.status}`;
      const errMsg = body?.error?.message || response.statusText || 'API request failed';
      const correlationId = response.headers.get('x-request-id') || body?.request_id;
      throw new PolarisAPIError(errCode, errMsg, response.status, body?.error?.details, correlationId);
    }

    return body;
  } catch (err: any) {
    if (err instanceof PolarisAPIError) {
      throw err;
    }
    throw new PolarisAPIError('NETWORK_ERROR', err.message || 'Network connection failed', 0);
  }
}

export async function apiGet<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<APIResponse<T>> {
  return apiRequest<T>(endpoint, { ...options, method: 'GET' });
}

export async function apiPost<T>(
  endpoint: string,
  body: any,
  options: RequestInit = {}
): Promise<APIResponse<T>> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'POST',
    body: typeof body === 'string' ? body : JSON.stringify(body),
  });
}

// Phase 11 — Edge Domain API Helpers
import type {
  EdgeStateResponseData,
  DeviceSummary,
  DeviceHealthItem,
  ConnectivityResponseData,
  SyncResponseData,
  EdgeEvaluateResponseData
} from './types';

export const edgeApi = {
  getState: (stationId: string) => 
    apiGet<EdgeStateResponseData>(`/api/v1/edge/${stationId}/state`),
  
  getDevices: (stationId: string) => 
    apiGet<DeviceSummary[]>(`/api/v1/edge/${stationId}/devices`),
  
  getHealth: (stationId: string) => 
    apiGet<DeviceHealthItem[]>(`/api/v1/edge/${stationId}/health`),
  
  getConnectivity: (stationId: string) => 
    apiGet<ConnectivityResponseData>(`/api/v1/edge/${stationId}/connectivity`),
  
  syncBuffer: (stationId: string) => 
    apiPost<SyncResponseData>(`/api/v1/edge/${stationId}/sync`, {}),
  
  evaluateDecision: (stationId: string) => 
    apiPost<EdgeEvaluateResponseData>(`/api/v1/edge/${stationId}/evaluate`, {}),
  
  simulateCondition: (stationId: string, condition: string) => 
    apiPost<EdgeStateResponseData>(`/api/v1/edge/${stationId}/simulate-condition`, { condition }),
};

