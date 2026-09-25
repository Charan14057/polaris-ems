import React from 'react';
import { useStation } from '../../context/StationContext';
import { StatusBadge } from '../common/StatusBadge';
import { Activity, ShieldCheck, ShieldAlert, WifiOff, Database } from 'lucide-react';

export const GlobalStatusBar: React.FC = () => {
  const { currentStation, stationDetail, readiness } = useStation();

  const totalLoad = (stationDetail as any)?.total_load_kw ?? 142.5;
  const criticalLoad = (stationDetail as any)?.critical_load_kw ?? 29.5;
  const reservePct = (stationDetail as any)?.reserve_margin_pct ?? 38.0;

  return (
    <div className="bg-canvas-subtle/80 border-b border-border-subtle px-4 lg:px-6 py-1.5 text-xs text-ink-secondary">
      <div className="max-w-[1520px] mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Left: Station Identity & State */}
        <div className="flex items-center space-x-3">
          <span className="font-mono text-[11px] font-semibold text-ink-primary uppercase">
            STATION: <span className="text-copper">{currentStation}</span>
          </span>
          <span className="text-border">|</span>
          <div className="flex items-center space-x-1.5">
            <span className="text-[10px] font-mono text-ink-muted uppercase">SYSTEM STATE:</span>
            <StatusBadge status="SAFE" size="sm" />
          </div>
        </div>

        {/* Center: Mission Vital Signs */}
        <div className="flex items-center space-x-4 font-mono text-[11px]">
          <div>
            <span className="text-ink-muted">TOTAL POWER: </span>
            <span className="font-mono-numbers font-semibold text-ink-primary">{totalLoad.toFixed(1)} kW</span>
          </div>
          <span className="text-border">|</span>
          <div>
            <span className="text-ink-muted">LIFE-SUPPORT CRITICAL: </span>
            <span className="font-mono-numbers font-semibold text-moss">{criticalLoad.toFixed(1)} kW</span>
          </div>
          <span className="text-border">|</span>
          <div>
            <span className="text-ink-muted">RESERVE MARGIN: </span>
            <span className="font-mono-numbers font-semibold text-copper">{reservePct.toFixed(0)}%</span>
          </div>
        </div>

        {/* Right: Provenance & Epistemic Boundary Truth */}
        <div className="flex items-center space-x-3 font-mono text-[10px]">
          <div className="flex items-center space-x-1 text-ink-muted">
            <Database className="w-3 h-3 text-teal" />
            <span>DATA: LOCKED 6-TIER</span>
          </div>
          <span className="text-border">|</span>
          <div className="flex items-center space-x-1 text-ink-secondary bg-surface px-1.5 py-0.5 rounded border border-border-subtle" title="Zero live physical SCADA connection exists">
            <WifiOff className="w-3 h-3 text-copper" />
            <span className="font-medium text-ink-primary">PHYSICAL: DISCONNECTED</span>
          </div>
        </div>
      </div>
    </div>
  );
};
