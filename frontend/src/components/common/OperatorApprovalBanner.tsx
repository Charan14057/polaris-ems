import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

interface OperatorApprovalBannerProps {
  onNavigateToOptimization?: () => void;
  onNavigateToTwin?: () => void;
}

export type ApprovalState = 'ADVISORY_PENDING' | 'ACKNOWLEDGED' | 'REJECTED_FOR_AUDIT';

export const OperatorApprovalBanner: React.FC<OperatorApprovalBannerProps> = ({
  onNavigateToOptimization,
  onNavigateToTwin,
}) => {
  const [approvalState, setApprovalState] = useState<ApprovalState>('ADVISORY_PENDING');
  const [acknowledgedAt, setAcknowledgedAt] = useState<string | null>(null);

  const handleAcknowledge = () => {
    setApprovalState('ACKNOWLEDGED');
    setAcknowledgedAt(new Date().toUTCString().replace('GMT', 'UTC'));
  };

  const handleReject = () => {
    setApprovalState('REJECTED_FOR_AUDIT');
    setAcknowledgedAt(new Date().toUTCString().replace('GMT', 'UTC'));
  };

  return (
    <div className="bg-canvas-subtle border-b border-border px-4 lg:px-6 py-2 text-xs flex flex-wrap items-center justify-between gap-3 text-ink-secondary">
      <div className="flex items-center space-x-2.5">
        <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-surface border border-border text-[11px] font-mono font-medium text-ink-primary">
          <ShieldCheck className="w-3.5 h-3.5 text-copper" />
          <span>OPERATOR BOUNDARY:</span>
        </div>

        {approvalState === 'ADVISORY_PENDING' && (
          <span className="flex items-center space-x-1.5 text-copper font-mono text-[11px] font-semibold">
            <span className="w-2 h-2 rounded-full bg-copper animate-pulse"></span>
            <span>SUPERVISOR REVIEW REQUIRED • ADVISORY POSTURE</span>
          </span>
        )}

        {approvalState === 'ACKNOWLEDGED' && (
          <span className="flex items-center space-x-1.5 text-moss font-mono text-[11px] font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5 text-moss" />
            <span>DISPATCH ACKNOWLEDGED BY OPERATOR ({acknowledgedAt})</span>
          </span>
        )}

        {approvalState === 'REJECTED_FOR_AUDIT' && (
          <span className="flex items-center space-x-1.5 text-red-700 font-mono text-[11px] font-semibold">
            <XCircle className="w-3.5 h-3.5 text-red-600" />
            <span>HELD FOR AUDIT / REJECTION RECORDED ({acknowledgedAt})</span>
          </span>
        )}

        <span className="hidden md:inline text-border">|</span>
        <span className="hidden md:inline text-[11px] text-ink-muted">
          Physical actuation requires human authorization. No physical polar SCADA connected.
        </span>
      </div>

      <div className="flex items-center space-x-2">
        {approvalState === 'ADVISORY_PENDING' && (
          <>
            <button
              onClick={handleAcknowledge}
              className="px-2.5 py-1 rounded bg-copper text-ink-inverse text-xs font-mono font-medium hover:bg-copper-dark transition-colors shadow-xs"
            >
              Acknowledge Dispatch
            </button>
            <button
              onClick={handleReject}
              className="px-2.5 py-1 rounded bg-surface border border-border text-ink-secondary text-xs font-mono font-medium hover:bg-canvas transition-colors"
            >
              Hold for Review
            </button>
          </>
        )}
        {onNavigateToOptimization && (
          <button
            onClick={onNavigateToOptimization}
            className="text-copper hover:text-copper-dark font-mono text-[11px] underline ml-1"
          >
            Review Dispatch →
          </button>
        )}
      </div>
    </div>
  );
};
