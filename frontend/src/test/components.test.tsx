import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { MetricCard } from '../components/common/MetricCard';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { Navbar, TabType } from '../components/layout/Navbar';
import { AlertRibbon } from '../components/layout/AlertRibbon';

describe('Common Polaris Components', () => {
  it('StatusBadge renders icons and accessible text labels (never color alone)', () => {
    const { unmount } = render(<StatusBadge status="SAFE" />);
    expect(screen.getByText('SAFE')).toBeInTheDocument();
    unmount();

    render(<StatusBadge status="CRITICAL" />);
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
  });

  it('StatusBadge supports all resilience and policy states', () => {
    const states = ['SAFE', 'WATCH', 'AT_RISK', 'THREATENED', 'CRITICAL', 'RECOVERY', 'BLOCKED', 'FALLBACK'];
    states.forEach((st) => {
      const { container, unmount } = render(<StatusBadge status={st} />);
      const expectedText = st.replace('_', ' ');
      expect(screen.getByText(expectedText)).toBeInTheDocument();
      // Ensure there is an SVG icon present alongside text
      const svg = container.querySelector('svg');
      expect(svg).not.toBeNull();
      unmount();
    });
  });

  it('ProvenanceTag renders locked provenance tiers with proper text', () => {
    const { rerender } = render(<ProvenanceTag provenance="REAL" />);
    expect(screen.getByText('REAL')).toBeInTheDocument();

    rerender(<ProvenanceTag provenance="CONFIGURED" />);
    expect(screen.getByText('CONFIGURED')).toBeInTheDocument();

    rerender(<ProvenanceTag provenance="FORECAST" />);
    expect(screen.getByText('FORECAST')).toBeInTheDocument();

    rerender(<ProvenanceTag provenance="SIMULATED" />);
    expect(screen.getByText('SIMULATED')).toBeInTheDocument();
  });

  it('MetricCard renders tabular values, units, and snapshot timestamps', () => {
    render(
      <MetricCard
        title="Battery SOC"
        value={74.5}
        unit="%"
        provenance="REAL"
        timestamp="2026-09-23T18:00:00Z"
      />
    );

    expect(screen.getByText('Battery SOC')).toBeInTheDocument();
    expect(screen.getByText('74.5')).toBeInTheDocument();
    expect(screen.getByText('%')).toBeInTheDocument();
    expect(screen.getByText(/Snapshot:/)).toBeInTheDocument();
    // Prohibit LIVE or REAL-TIME labels
    expect(screen.queryByText('LIVE')).toBeNull();
    expect(screen.queryByText('REAL-TIME')).toBeNull();
  });

  it('Navbar renders all 8 operational views with proper accessible roles', () => {
    let selectedTab: TabType = 'overview';
    const onSelect = (tab: TabType) => {
      selectedTab = tab;
    };

    render(<Navbar activeTab={selectedTab} onSelectTab={onSelect} />);

    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Energy Twin')).toBeInTheDocument();
    expect(screen.getByText('Forecast')).toBeInTheDocument();
    expect(screen.getByText('Scenarios')).toBeInTheDocument();
    expect(screen.getByText('Optimizer')).toBeInTheDocument();
    expect(screen.getByText('Resilience')).toBeInTheDocument();
    expect(screen.getByText('Policy')).toBeInTheDocument();
    expect(screen.getByText('Decision Trace')).toBeInTheDocument();
  });

  it('LoadingSkeleton renders with proper ARIA attributes', () => {
    render(<LoadingSkeleton rows={4} height="h-20" />);
    const status = screen.getByRole('status');
    expect(status).toBeInTheDocument();
    expect(screen.getByText('Loading operational telemetry...')).toBeInTheDocument();
  });

  it('ErrorCard displays custom title, message, code, and calls onRetry', () => {
    let retried = false;
    render(
      <ErrorCard
        title="Custom Error Title"
        message="Failure to connect to station twin"
        code="ERR_NETWORK"
        onRetry={() => { retried = true; }}
      />
    );

    expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
    expect(screen.getByText('Failure to connect to station twin')).toBeInTheDocument();
    expect(screen.getByText('ERR_NETWORK')).toBeInTheDocument();

    const retryBtn = screen.getByRole('button', { name: /retry/i });
    retryBtn.click();
    expect(retried).toBe(true);
  });

  it('AlertRibbon renders critical threats with alert role and trigger action', () => {
    let navigated = false;
    const threats = [
      {
        threat_type: 'HIGH_WIND_BLIZZARD',
        severity: 'CRITICAL' as const,
        trigger_condition: 'Wind speed exceeds 25 m/s cut-out',
        target_subsystem: 'GENERATION',
        affected_subsystems: ['GENERATION', 'ELECTRICAL'],
        time_to_threat_h: 2.0,
      },
      {
        threat_type: 'BATTERY_COLD_DERATE',
        severity: 'WARNING' as const,
        trigger_condition: 'Indoor battery ambient drops below -15C',
        target_subsystem: 'STORAGE',
        affected_subsystems: ['STORAGE'],
        time_to_threat_h: 6.0,
      },
    ];

    render(
      <AlertRibbon
        threats={threats}
        onNavigateToPolicy={() => { navigated = true; }}
      />
    );

    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(screen.getByText(/HIGH WIND BLIZZARD/)).toBeInTheDocument();
    expect(screen.getByText('Wind speed exceeds 25 m/s cut-out')).toBeInTheDocument();
    expect(screen.getByText('+1 more alert')).toBeInTheDocument();

    const btn = screen.getByRole('button', { name: /inspect/i });
    btn.click();
    expect(navigated).toBe(true);
  });
});
