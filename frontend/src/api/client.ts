/**
 * POLARIS-EMS — Typed API Client
 * Polaris-EMS — Polar Energy Management & Resilience System
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
  options: RequestInit = {},
  retries = 2,
  backoffMs = 1200
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

    // Auto-retry transient gateway cold-start errors (typical during Render deployments / wakeups)
    if ((response.status === 502 || response.status === 503 || response.status === 504) && retries > 0) {
      await new Promise((r) => setTimeout(r, backoffMs));
      return apiRequest<T>(endpoint, options, retries - 1, backoffMs * 1.5);
    }

    let body: APIResponse<T> | null = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    if (!response.ok) {
      const errCode = body?.error?.code || `HTTP_${response.status}`;
      let errMsg = body?.error?.message;
      if (!errMsg) {
        if (response.status === 502 || response.status === 503 || response.status === 504) {
          errMsg = 'Polaris-EMS service is initializing. Please wait a moment and retry.';
        } else if (response.status === 404) {
          errMsg = `Requested endpoint not found (${endpoint}).`;
        } else {
          errMsg = response.statusText || 'API request failed';
        }
      }
      const correlationId = response.headers.get('x-request-id') || body?.request_id;
      throw new PolarisAPIError(errCode, errMsg, response.status, body?.error?.details, correlationId);
    }

    if (!body) {
      throw new PolarisAPIError('PARSE_ERROR', 'Unexpected non-JSON response from server', response.status);
    }

    return body;
  } catch (err: any) {
    if (err instanceof PolarisAPIError) {
      throw err;
    }
    // Auto-retry transient network dropouts if server is warming up
    if (retries > 0) {
      await new Promise((r) => setTimeout(r, backoffMs));
      return apiRequest<T>(endpoint, options, retries - 1, backoffMs * 1.5);
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

