import React, { useState } from 'react';
import { ShieldCheck, UserCheck, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';

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
    <div className="bg-polar-900/90 border-b border-polar-800 px-4 py-2 text-xs flex flex-wrap items-center justify-between gap-3 text-polar-300">
      <div className="flex items-center space-x-2.5">
        <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-polar-800 text-[11px] font-mono font-medium text-polar-200">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>OPERATOR BOUNDARY:</span>
        </div>

        {approvalState === 'ADVISORY_PENDING' && (
          <span className="flex items-center space-x-1 text-amber-300 font-mono text-[11px]">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
            <span>SUPERVISOR REVIEW REQUIRED • ADVISORY POSTURE</span>
          </span>
        )}

        {approvalState === 'ACKNOWLEDGED' && (
          <span className="flex items-center space-x-1 text-emerald-300 font-mono text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>DISPATCH ACKNOWLEDGED BY OPERATOR ({acknowledgedAt})</span>
          </span>
        )}

        {approvalState === 'REJECTED_FOR_AUDIT' && (
          <span className="flex items-center space-x-1 text-rose-300 font-mono text-[11px]">
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            <span>HELD FOR AUDIT / REJECTION RECORDED ({acknowledgedAt})</span>
          </span>
        )}

        <span className="hidden md:inline text-polar-500">|</span>
        <span className="hidden md:inline text-[11px] text-polar-400">
          Physical actuation requires human authorization. No physical polar SCADA connected.
        </span>
      </div>

      <div className="flex items-center space-x-2">
        {approvalState === 'ADVISORY_PENDING' ? (
          <>
            <button
              onClick={handleAcknowledge}
              className="px-2.5 py-1 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-[11px] font-mono transition-colors"
              title="Acknowledge recommended dispatch for simulated execution"
            >
              Acknowledge Advisory
            </button>
            <button
              onClick={handleReject}
              className="px-2.5 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-[11px] font-mono transition-colors"
              title="Hold dispatch and review diagnostics"
            >
              Reject / Audit
            </button>
          </>
        ) : (
          <button
            onClick={() => setApprovalState('ADVISORY_PENDING')}
            className="px-2 py-0.5 rounded bg-polar-800 hover:bg-polar-700 text-polar-300 border border-polar-700 text-[10px] font-mono transition-colors"
          >
            Reset Posture
          </button>
        )}
      </div>
    </div>
  );
};
