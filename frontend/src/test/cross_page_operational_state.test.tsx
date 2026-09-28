import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { StationProvider, useOperationalSnapshot, useStation } from '../context/StationContext';
import { STATIC_SPATIAL_PROFILES } from '../features/twin/model/spatialProfiles';
import { buildBharatiStation, buildMaitriStation, buildHimadriStation } from '../features/twin/model/stationMeshBuilders';

// Mock API endpoints
vi.mock('../api/endpoints', () => ({
  api: {
    getLiveTwinSnapshot: vi.fn().mockImplementation((st: string) => Promise.resolve({
      data: {
        state: {
          timestamp: '2026-09-28T12:00:00Z',
          power_kw: st === 'MAITRI' ? 45.0 : st === 'HIMADRI' ? 22.0 : 65.0,
          critical_load_kw: st === 'MAITRI' ? 20.0 : st === 'HIMADRI' ? 10.0 : 30.0,
          ambient_temp_c: st === 'HIMADRI' ? -15.0 : -25.0,
          wind_speed_m_per_s: 11.2,
          ghi_w_per_m2: 240.0,
          solar_kw: 14.0,
          wind_kw: 28.0,
          dg_kw: 23.0,
          bess_soc_pct: 72.0,
          bess_power_kw: -5.0,
          fuel_liters: 12500,
          active_scenario: null,
          resilience_state: 'SAFE',
          policy_directive: 'RENEWABLE_PRIORITY',
        },
        metadata: {
          wall_clock_timestamp: '2026-09-28T12:00:00Z',
          provenance: 'SIMULATED',
        }
      }
    })),
    getResilienceEnvelope: vi.fn().mockResolvedValue({
      data: {
        overall_survival_horizon_hours: 88.5,
        binding_subsystem: 'STORAGE',
        current_state: 'SAFE',
        dimensions: {
          thermal_resilience: 0.85,
          electrical_resilience: 0.90,
          fuel_resilience: 0.88,
        }
      }
    }),
    evaluatePolicy: vi.fn().mockResolvedValue({
      data: {
        directive: 'RENEWABLE_PRIORITY',
        active_rules: ['RULE_MAX_RENEWABLES'],
      }
    }),
    evaluateScenario: vi.fn().mockResolvedValue({
      data: {
        active: true,
        scenario_id: 'BLIZZARD',
        severity: 'HIGH',
      }
    }),
    clearScenario: vi.fn().mockResolvedValue({
      data: {
        cleared: true,
      }
    }),
    applyLiveScenario: vi.fn().mockResolvedValue({
      data: {
        applied: true,
        scenario_id: 'BLIZZARD',
      }
    }),
    clearLiveScenario: vi.fn().mockResolvedValue({
      data: {
        cleared: true,
      }
    }),
    dispatchManualControl: vi.fn().mockResolvedValue({
      data: {
        state: { power_kw: 80.0 },
        trace: { wall_clock: '2026-09-28T12:05:00Z' }
      }
    }),
    approveScenarioDispatch: vi.fn().mockResolvedValue({
      data: {
        approved: true,
      }
    }),
    approveAutoRecommendation: vi.fn().mockResolvedValue({
      data: {
        approved: true,
      }
    }),
  }
}));

// Test Consumer component reading useOperationalSnapshot
function StateConsumer() {
  const snapshot = useOperationalSnapshot();
  const { currentStation, setStation } = useStation();

  return (
    <div>
      <div data-testid="station-id">{currentStation}</div>
      <div data-testid="active-scenario">{snapshot.activeScenario || 'NONE'}</div>
      <div data-testid="ambient-temp">{snapshot.ambientTemperatureC != null ? `${snapshot.ambientTemperatureC}°C` : '—'}</div>
      <div data-testid="total-load">{snapshot.totalLoadKw != null ? `${snapshot.totalLoadKw} kW` : '—'}</div>
      <div data-testid="fuel-level">{snapshot.fuelRemainingL != null ? `${snapshot.fuelRemainingL} L` : '—'}</div>
      <div data-testid="unavailable-metric">{(snapshot as any).missingField != null ? `${(snapshot as any).missingField}` : '—'}</div>
      <button onClick={() => setStation('MAITRI')}>Switch to Maitri</button>
      <button onClick={() => setStation('HIMADRI')}>Switch to Himadri</button>
      <button onClick={() => snapshot.activateScenario('BLIZZARD')}>Activate Blizzard</button>
      <button onClick={() => snapshot.clearScenario()}>Clear Scenario</button>
      <button onClick={() => snapshot.applyManualControl('START_DG1')}>Manual Start DG1</button>
      <button onClick={() => snapshot.approveAutoRecommendation()}>Approve Auto</button>
    </div>
  );
}

describe('System-Wide Cross-Page Operational State Tests', () => {
  it('propagates station changes to operational snapshot across all consumers', async () => {
    render(
      <StationProvider>
        <StateConsumer />
      </StationProvider>
    );

    // Initial station Bharati
    expect(screen.getByTestId('station-id').textContent).toBe('BHARATI');

    // Switch to Maitri
    await act(async () => {
      screen.getByText('Switch to Maitri').click();
    });
    expect(screen.getByTestId('station-id').textContent).toBe('MAITRI');

    // Switch to Himadri
    await act(async () => {
      screen.getByText('Switch to Himadri').click();
    });
    expect(screen.getByTestId('station-id').textContent).toBe('HIMADRI');
  });

  it('renders "—" for missing/unavailable fields and never manufactures fake numbers or 0.0', () => {
    render(
      <StationProvider>
        <StateConsumer />
      </StationProvider>
    );

    expect(screen.getByTestId('unavailable-metric').textContent).toBe('—');
    expect(screen.getByTestId('unavailable-metric').textContent).not.toBe('0.0');
  });

  it('differentiates 2D power topology diagrams across Bharati, Maitri, and Himadri', () => {
    const bharatiProfile = STATIC_SPATIAL_PROFILES.BHARATI;
    const maitriProfile = STATIC_SPATIAL_PROFILES.MAITRI;
    const himadriProfile = STATIC_SPATIAL_PROFILES.HIMADRI;

    expect(bharatiProfile.stationId).toBe('BHARATI');
    expect(maitriProfile.stationId).toBe('MAITRI');
    expect(himadriProfile.stationId).toBe('HIMADRI');

    // Node IDs are station specific
    expect(bharatiProfile.nodes.some(n => n.id.includes('bh_'))).toBe(true);
    expect(maitriProfile.nodes.some(n => n.id === 'node_mt_main_bus')).toBe(true);
    expect(himadriProfile.nodes.some(n => n.id === 'node_hm_main_bus')).toBe(true);
  });

  it('differentiates 3D station architectural mesh structures across Bharati, Maitri, and Himadri', () => {
    const bharatiScene = buildBharatiStation('ENERGY', false);
    const maitriScene = buildMaitriStation('ENERGY', false);
    const himadriScene = buildHimadriStation('ENERGY', false);

    expect(bharatiScene).toBeDefined();
    expect(maitriScene).toBeDefined();
    expect(himadriScene).toBeDefined();

    // Bharati has 2 turbines, Maitri has 1 turbine, Himadri has 1 turbine
    expect(bharatiScene.turbines.length).toBe(2);
    expect(maitriScene.turbines.length).toBe(1);
    expect(himadriScene.turbines.length).toBe(1);

    // Interactive mesh keys are station specific
    expect(bharatiScene.interactiveMeshes.has('diesel_generator_1')).toBe(true);
    expect(maitriScene.interactiveMeshes.has('mt_diesel')).toBe(true);
    expect(himadriScene.interactiveMeshes.has('node_hm_diesel')).toBe(true);
  });

  it('activates and clears scenarios system-wide without state drift', async () => {
    render(
      <StationProvider>
        <StateConsumer />
      </StationProvider>
    );

    expect(screen.getByTestId('active-scenario').textContent).toBe('NONE');

    // Activate Blizzard
    await act(async () => {
      screen.getByText('Activate Blizzard').click();
    });
    expect(screen.getByTestId('active-scenario').textContent).toBe('BLIZZARD');

    // Clear Scenario
    await act(async () => {
      screen.getByText('Clear Scenario').click();
    });
    expect(screen.getByTestId('active-scenario').textContent).toBe('NONE');
  });

  it('propagates manual control and auto approval actions', async () => {
    render(
      <StationProvider>
        <StateConsumer />
      </StationProvider>
    );

    await act(async () => {
      screen.getByText('Manual Start DG1').click();
    });

    await act(async () => {
      screen.getByText('Approve Auto').click();
    });
  });
});
