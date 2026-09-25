import React from 'react';
import { useEvidence } from '../../context/EvidenceContext';
import { Shield, AlertTriangle, BatteryCharging, Flame, Thermometer, Clock, Info } from 'lucide-react';

export interface ResilienceDimension {
  id: string;
  name: string;
  horizonHours: number;
  score: number; // 0.0 to 1.0
  isBinding: boolean;
  status: 'SAFE' | 'WATCH' | 'AT_RISK' | 'CRITICAL';
  description: string;
}

interface ResilienceEnvelopeProps {
  stationId?: string;
  overallState?: string;
  overallHorizonHours?: number;
  className?: string;
}

export const ResilienceEnvelope: React.FC<ResilienceEnvelopeProps> = ({
  stationId = 'BHARATI',
  overallState = 'WATCH',
  overallHorizonHours = 84.0,
  className = '',
}) => {
  const { inspectEvidence } = useEvidence();

  const dimensions: ResilienceDimension[] = [
    {
      id: 'critical_load',
      name: 'Life-Support Critical Load',
      horizonHours: 120.0,
      score: 0.92,
      isBinding: false,
      status: 'SAFE',
      description: 'Habitation heating, atmospheric scrubbers, and satellite coms load (29.5 kW) priority dispatch sustained.',
    },
    {
      id: 'fuel',
      name: 'Diesel Fuel Reserve',
      horizonHours: 84.0,
      score: 0.72,
      isBinding: true,
      status: 'WATCH',
      description: 'Tank capacity remaining: 3,420 liters. At current dual-generator run profile, fuel will bind in 84 hours.',
    },
    {
      id: 'thermal',
      name: 'Thermal Building Envelope',
      horizonHours: 96.0,
      score: 0.81,
      isBinding: false,
      status: 'SAFE',
      description: 'Habitation core interior sustained at +19.5°C; safe minimum threshold is +15.0°C.',
    },
    {
      id: 'battery',
      name: 'BESS Electrochemical Reserve',
      horizonHours: 9.5,
      score: 0.65,
      isBinding: false,
      status: 'WATCH',
      description: 'Battery bank SOC at 68.4%. Provides 9.5 hours of emergency black-sky bridging without generator support.',
    },
  ];

  return (
    <div className={`editorial-sheet rounded p-5 sm:p-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-5 border-b border-border-subtle gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded bg-copper-soft text-copper flex items-center justify-center shrink-0">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted block">
              OPERATIONAL ENVELOPE
            </span>
            <h3 className="text-base font-serif font-bold text-ink-primary">
              Station Survival Envelope & Binding Constraints
            </h3>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-right">
            <span className="text-[10px] font-mono uppercase text-ink-muted block">Overall Survival Horizon</span>
            <span className="text-xl font-mono-numbers font-bold text-copper">
              {overallHorizonHours.toFixed(1)} <span className="text-xs font-normal text-ink-muted">hours</span>
            </span>
          </div>
        </div>
      </div>

      {/* Binding Bottleneck Callout */}
      <div className="p-3.5 rounded bg-copper-subtle border border-copper/30 mb-6 flex items-start justify-between gap-3">
        <div className="flex items-start space-x-2.5">
          <AlertTriangle className="w-4 h-4 text-copper shrink-0 mt-0.5" />
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-copper font-bold block">
              PRIMARY BINDING CONSTRAINT: DIESEL FUEL RUNWAY
            </span>
            <p className="text-xs text-ink-secondary mt-0.5 leading-relaxed">
              Resilience is currently limited to 84.0 hours by remaining fuel tank capacity. Battery and thermal buffers have adequate safety margins.
            </p>
          </div>
        </div>
        <button
          onClick={() =>
            inspectEvidence({
              title: 'Resilience Binding Constraint',
              value: '84.0 hours (Fuel Bound)',
              source: 'Polaris Resilience State Machine (Phase 7)',
              provenance: 'SIMULATED',
              station: stationId,
              modelOrSubsystem: 'Multi-Horizon Survival Calculus',
              mathematicalBasis: '$T_{\\text{surv}} = \\min(T_{\\text{fuel}}, T_{\\text{battery}}, T_{\\text{thermal}}, T_{\\text{critical}})$',
              validationState: 'Verified via Digital Twin 168h Replay',
            })
          }
          className="text-xs font-mono text-copper hover:text-copper-dark shrink-0 p-1"
          aria-label="Inspect evidence for binding constraint"
        >
          <Info className="w-4 h-4" />
        </button>
      </div>

      {/* Dimensional Breakdown Bars */}
      <div className="space-y-4">
        {dimensions.map((dim) => (
          <div key={dim.id} className="p-3 rounded bg-canvas-subtle border border-border-subtle">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <div className="flex items-center space-x-2">
                {dim.id === 'fuel' && <Flame className="w-3.5 h-3.5 text-copper" />}
                {dim.id === 'battery' && <BatteryCharging className="w-3.5 h-3.5 text-moss" />}
                {dim.id === 'thermal' && <Thermometer className="w-3.5 h-3.5 text-ice" />}
                {dim.id === 'critical_load' && <Shield className="w-3.5 h-3.5 text-teal" />}
                <span className="font-medium text-ink-primary font-sans">{dim.name}</span>
                {dim.isBinding && (
                  <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-copper text-ink-inverse font-bold">
                    BINDING
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <span className="font-mono-numbers text-ink-primary font-semibold">
                  {dim.horizonHours} h
                </span>
                <span className="text-[10px] font-mono text-ink-muted">
                  ({Math.round(dim.score * 100)}% margin)
                </span>
              </div>
            </div>

            {/* Visual Margin Bar */}
            <div className="w-full h-1.5 bg-canvas rounded-full overflow-hidden border border-border-subtle">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  dim.isBinding ? 'bg-copper' : 'bg-teal'
                }`}
                style={{ width: `${Math.min(100, Math.max(10, dim.score * 100))}%` }}
              />
            </div>
            <p className="text-[11px] text-ink-muted mt-2 leading-relaxed font-sans">
              {dim.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
