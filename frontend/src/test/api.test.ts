import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiGet, apiPost, PolarisAPIError } from '../api/client';
import { ProvenanceTier } from '../api/types';

describe('Polaris API Client & Constraints', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('locked provenance taxonomy contains exactly the 6 allowed tiers', () => {
    const validTiers: ProvenanceTier[] = [
      'REAL',
      'CONFIGURED',
      'ASSUMED',
      'SYNTHETIC',
      'FORECAST',
      'SIMULATED',
    ];

    expect(validTiers).toHaveLength(6);
    expect(validTiers).toContain('REAL');
    expect(validTiers).toContain('CONFIGURED');
    expect(validTiers).toContain('ASSUMED');
    expect(validTiers).toContain('SYNTHETIC');
    expect(validTiers).toContain('FORECAST');
    expect(validTiers).toContain('SIMULATED');
    // Ensure prohibited tiers like LIVE or OPTIMIZED are absent
    expect((validTiers as string[])).not.toContain('LIVE');
    expect((validTiers as string[])).not.toContain('OPTIMIZED');
    expect((validTiers as string[])).not.toContain('REAL-TIME');
  });

  it('apiGet sets X-Request-ID and parses JSON response successfully', async () => {
    const mockData = {
      request_id: 'test-req-123',
      status: 'SUCCESS' as const,
      data: [{ station_id: 'BHARATI', name: 'Bharati Station' }],
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'x-request-id': 'test-req-123' }),
      json: async () => mockData,
    });
    globalThis.fetch = mockFetch;

    const result = await apiGet<any>('/api/v1/stations');
    expect(result).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe('/api/v1/stations');
    expect(options.headers).toBeDefined();
    expect(options.headers['X-Request-ID']).toMatch(/^req-ui-[a-z0-9-]+$/);
  });

  it('apiPost sends JSON payload and correlation headers', async () => {
    const mockResponse = {
      request_id: 'post-req-456',
      status: 'SUCCESS' as const,
      data: {
        status: 'OPTIMAL',
        total_cost_inr: 4200.5,
      },
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'x-request-id': 'post-req-456' }),
      json: async () => mockResponse,
    });
    globalThis.fetch = mockFetch;

    const payload = { station_id: 'BHARATI', mode: 'BALANCED' };
    const result = await apiPost('/api/v1/optimize', payload);

    expect(result).toEqual(mockResponse);
    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe('/api/v1/optimize');
    expect(options.method).toBe('POST');
    expect(options.body).toBe(JSON.stringify(payload));
  });

  it('apiGet throws PolarisAPIError on non-200 responses with detail', async () => {
    const mockErrorBody = {
      request_id: 'err-req-789',
      status: 'ERROR',
      error: {
        code: 'STATION_NOT_FOUND',
        message: 'Station XYZ not found',
        details: { station: 'XYZ' },
      },
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      headers: new Headers({ 'x-request-id': 'err-req-789' }),
      json: async () => mockErrorBody,
    });
    globalThis.fetch = mockFetch;

    await expect(apiGet('/api/v1/stations/XYZ')).rejects.toThrow(PolarisAPIError);
    try {
      await apiGet('/api/v1/stations/XYZ');
    } catch (err) {
      const apiErr = err as PolarisAPIError;
      expect(apiErr.status).toBe(404);
      expect(apiErr.code).toBe('STATION_NOT_FOUND');
      expect(apiErr.message).toBe('Station XYZ not found');
      expect(apiErr.correlationId).toBe('err-req-789');
    }
  });
});
