import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { MetricCard } from '../components/common/MetricCard';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { Navbar, TabType } from '../components/layout/Navbar';
import { AlertRibbon } from '../components/layout/AlertRibbon';
import { WhyThisMatters } from '../components/common/WhyThisMatters';
import { OperatorApprovalBanner } from '../components/common/OperatorApprovalBanner';
import { ExplainThis } from '../components/common/ExplainThis';
import { NextStepExplanation } from '../components/common/NextStepExplanation';
import { HumanDecisionSummary } from '../components/common/HumanDecisionSummary';
import { JargonTooltip } from '../components/common/JargonTooltip';
import { QuickOrientationModal } from '../components/common/QuickOrientationModal';
import { EvidenceProvider } from '../context/EvidenceContext';

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
    expect(screen.getByText('DIGITAL TWIN')).toBeInTheDocument();
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

  it('WhyThisMatters component renders headline, summary, and progressive disclosure toggle', () => {
    render(
      <WhyThisMatters
        headline="Turbine De-rating Active"
        summary="Wind speed exceeds normal operating envelope, forcing generation curtailment."
        technicalDetail="Betz limit calculation adjusted for air density at -35C."
        invariant="Conservation of momentum in aerodynamic boundary layer."
      />
    );

    expect(screen.getByText('Turbine De-rating Active')).toBeInTheDocument();
    expect(screen.getByText(/Wind speed exceeds normal operating envelope/)).toBeInTheDocument();
    expect(screen.getByText(/WHY THIS MATTERS/)).toBeInTheDocument();

    // Verify toggle expands technical detail
    const toggleBtn = screen.getByRole('button', { name: /toggle technical explanation/i });
    expect(screen.queryByText(/Betz limit calculation/)).toBeNull();
    fireEvent.click(toggleBtn);
    expect(screen.getByText(/Betz limit calculation/)).toBeInTheDocument();
    expect(screen.getByText(/Conservation of momentum/)).toBeInTheDocument();
  });

  it('OperatorApprovalBanner renders supervisory controls and boundary notice', () => {
    let optNavigated = false;
    render(
      <OperatorApprovalBanner
        onNavigateToOptimization={() => { optNavigated = true; }}
      />
    );

    expect(screen.getByText(/OPERATOR BOUNDARY:/)).toBeInTheDocument();
    expect(screen.getByText(/SUPERVISOR REVIEW REQUIRED/)).toBeInTheDocument();
    const reviewBtn = screen.getByRole('button', { name: /Review Dispatch/i });
    fireEvent.click(reviewBtn);
    expect(optNavigated).toBe(true);
  });

  it('ExplainThis renders non-technical questions and toggles open/close', () => {
    render(
      <EvidenceProvider>
        <ExplainThis
          title="Explain this power balance diagram in plain English"
          whatAmILookingAt="This diagram shows the complete electrical flow of the station."
          whyIsItImportant="Generation must match consumption in Antarctica."
          howIsItCalculated="Calculated by Kirchhoff laws."
        />
      </EvidenceProvider>
    );

    expect(screen.getByText('Explain this power balance diagram in plain English')).toBeInTheDocument();
    expect(screen.getByText('Explain This')).toBeInTheDocument();

    // Toggle open
    const toggleBtn = screen.getByRole('button', { name: /explain this/i });
    fireEvent.click(toggleBtn);

    expect(screen.getByText(/1. WHAT AM I LOOKING AT\?/)).toBeInTheDocument();
    expect(screen.getByText(/This diagram shows the complete electrical flow/)).toBeInTheDocument();
    expect(screen.getByText(/2. WHY IS IT IMPORTANT\?/)).toBeInTheDocument();
    expect(screen.getByText(/3. HOW IS IT CALCULATED\?/)).toBeInTheDocument();
  });

  it('NextStepExplanation renders proactive outlook and action trigger', () => {
    let triggered = false;
    render(
      <NextStepExplanation
        title="WHAT HAPPENS OVER THE NEXT 12 HOURS?"
        timeframe="Next 12 Hours"
        outlook="Wind speed will decline tonight; diesel will take over."
        actionText="Review Plan"
        onAction={() => { triggered = true; }}
      />
    );

    expect(screen.getByText('WHAT HAPPENS OVER THE NEXT 12 HOURS?')).toBeInTheDocument();
    expect(screen.getByText('Next 12 Hours')).toBeInTheDocument();
    expect(screen.getByText(/Wind speed will decline tonight/)).toBeInTheDocument();

    const actionBtn = screen.getByRole('button', { name: /Review Plan/i });
    fireEvent.click(actionBtn);
    expect(triggered).toBe(true);
  });

  it('HumanDecisionSummary renders 4-part operational explanation', () => {
    render(
      <EvidenceProvider>
        <HumanDecisionSummary
          decision="Deploy dual diesel generators in asymmetric split."
          because="Wind drop expected overnight."
          toProtect="Habitation heating and life support."
          confidenceEvidence="HiGHS solver certified with zero gap."
        />
      </EvidenceProvider>
    );

    expect(screen.getByText(/HUMAN-READABLE DECISION SUMMARY/)).toBeInTheDocument();
    expect(screen.getByText('Deploy dual diesel generators in asymmetric split.')).toBeInTheDocument();
    expect(screen.getByText('Wind drop expected overnight.')).toBeInTheDocument();
    expect(screen.getByText('Habitation heating and life support.')).toBeInTheDocument();
    expect(screen.getByText('HiGHS solver certified with zero gap.')).toBeInTheDocument();
  });

  it('JargonTooltip displays plain-language definition on interaction', () => {
    render(
      <JargonTooltip term="Digital Twin">Digital Twin</JargonTooltip>
    );

    expect(screen.getByText('Digital Twin')).toBeInTheDocument();
    // Hover/click to open tooltip
    const trigger = screen.getByLabelText(/Plain language explanation for Digital Twin/);
    fireEvent.mouseEnter(trigger);

    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    expect(screen.getByText(/A computer simulation that mimics how the polar station/)).toBeInTheDocument();
  });

  it('QuickOrientationModal renders 60-second tour when open and can advance', () => {
    let closed = false;
    const { rerender } = render(
      <QuickOrientationModal isOpen={false} onClose={() => { closed = true; }} />
    );

    expect(screen.queryByText(/60-SECOND ORIENTATION GUIDE/)).toBeNull();

    rerender(
      <QuickOrientationModal isOpen={true} onClose={() => { closed = true; }} />
    );

    expect(screen.getByText(/60-SECOND ORIENTATION GUIDE/)).toBeInTheDocument();
    expect(screen.getByText(/Why do polar research stations need an autonomous energy system\?/)).toBeInTheDocument();

    // Click next point
    const nextBtn = screen.getByRole('button', { name: /Next Point/i });
    fireEvent.click(nextBtn);

    expect(screen.getByText(/What actually is this application\?/)).toBeInTheDocument();
  });
});

