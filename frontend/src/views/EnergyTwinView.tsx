import React from 'react';
import { useStation } from '../context/StationContext';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { 
  Boxes, 
  Layers, 
  Compass, 
  MapPin, 
  ShieldCheck, 
  Sliders, 
  Maximize2, 
  Grid,
  Info
} from 'lucide-react';

export const EnergyTwinView: React.FC = () => {
  const { currentStation, stationDetail } = useStation();

  return (
    <div className="space-y-6 max-w-[1520px] mx-auto pb-12">
      {/* Editorial Header */}
      <div className="border-b border-border pb-6 flex flex-col sm:flex-row sm:items-baseline justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-copper font-bold mb-2">
            <Boxes className="w-4 h-4" />
            <span>03 TWIN ENGINE PLATFORM</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-serif font-bold text-ink-primary tracking-tight">
            Spatial Energy Digital Twin
          </h2>
          <p className="text-sm text-ink-secondary mt-1 font-sans">
            Top-down spatial microgrid floor-plan, thermal zone layout, and physical power flow platform.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <ProvenanceTag provenance="SIMULATED" size="sm" />
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-canvas-subtle border border-border text-ink-muted">
            TARGET: {currentStation}
          </span>
        </div>
      </div>

      {/* Main Architectural Drafting Canvas Shell (Reserved for Phase 18 Twin Engine) */}
      <div className="editorial-sheet rounded-lg p-6 sm:p-10 border border-border relative overflow-hidden texture-subtle-grid min-h-[520px] flex flex-col justify-between">
        {/* Top Control Bar of the Spatial Canvas */}
        <div className="flex items-center justify-between pb-4 border-b border-border-subtle z-10">
          <div className="flex items-center space-x-3 text-xs font-mono">
            <span className="font-semibold text-ink-primary flex items-center space-x-1.5">
              <MapPin className="w-3.5 h-3.5 text-copper" />
              <span>STATION GEOMETRY CANVAS: {stationDetail?.name || currentStation}</span>
            </span>
            <span className="text-border">|</span>
            <span className="text-ink-muted">COORDINATES: {stationDetail ? `${stationDetail.latitude.toFixed(2)}°S, ${stationDetail.longitude.toFixed(2)}°E` : '69°24\'S, 76°11\'E'}</span>
          </div>

          <div className="flex items-center space-x-2 font-mono text-xs">
            <span className="text-[11px] text-ink-muted px-2 py-1 rounded bg-canvas border border-border-subtle">
              SCALE: 1:250
            </span>
            <span className="text-[11px] text-copper px-2 py-1 rounded bg-copper-soft font-medium">
              PRE-TWIN UI SHELL READY
            </span>
          </div>
        </div>

        {/* Center Blueprint Notice & Architectural Framing */}
        <div className="my-auto py-12 flex flex-col items-center justify-center text-center z-10 max-w-xl mx-auto">
          <div className="w-16 h-16 rounded-full bg-copper-soft border border-copper/30 flex items-center justify-center text-copper mb-4 shadow-sm">
            <Compass className="w-8 h-8 animate-pulse" />
          </div>

          <span className="text-xs font-mono uppercase tracking-widest text-copper font-bold mb-1">
            PRE-TWIN DESIGN SYSTEM SLOT
          </span>
          <h3 className="text-2xl font-serif font-bold text-ink-primary mb-2">
            Spatial Energy Digital Twin Reserved Slot
          </h3>
          <p className="text-sm text-ink-secondary leading-relaxed mb-6 font-sans">
            The spatial building architecture, zone-by-zone power flow animation, circuit graph topology, and interactive room thermal models are formally reserved for the Twin Engine implementation stage.
          </p>

          {/* Architecture Readiness Card */}
          <div className="w-full text-left p-4 rounded bg-surface border border-border text-xs space-y-2.5 font-mono shadow-xs">
            <div className="flex items-center justify-between text-ink-muted border-b border-border-subtle pb-2">
              <span className="text-ink-primary font-semibold">TWIN ENGINE INTEGRATION READINESS</span>
              <span className="text-moss font-semibold">100% CONTRACT READY</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-ink-muted block">Electrical Bus Schema:</span>
                <span className="text-ink-secondary font-medium">IEEE 14-Bus Node Topology</span>
              </div>
              <div>
                <span className="text-ink-muted block">Thermal Building Model:</span>
                <span className="text-ink-secondary font-medium">3-Zone Dynamic Lumped Capacitance</span>
              </div>
              <div>
                <span className="text-ink-muted block">Device Registry Binding:</span>
                <span className="text-ink-secondary font-medium">{stationDetail?.devices?.length || 8} Discoverable Endpoints</span>
              </div>
              <div>
                <span className="text-ink-muted block">Actuation Guardrail:</span>
                <span className="text-copper font-medium">Simulation Air-Gap Enforced</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Status Ribbon */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pt-4 border-t border-border-subtle text-xs text-ink-muted font-mono z-10 gap-2">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-3.5 h-3.5 text-moss" />
            <span>Multi-Physics Thermodynamic Conservation Invariants Verified</span>
          </div>
          <span className="text-[11px]">
            SLOT: <code className="text-ink-primary">views/EnergyTwinView.tsx</code>
          </span>
        </div>
      </div>
    </div>
  );
};
