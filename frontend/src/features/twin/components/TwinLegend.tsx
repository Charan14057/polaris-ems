/**
 * POLARIS-EMS — Digital Twin Map Legend Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Provides clear, accessible visual guidance on flow colors, line thicknesses,
 * and device priority rings conforming to the Copper x Ice design system.
 */

import React, { useState } from 'react';
import { HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

export const TwinLegend: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="absolute top-4 right-4 z-20 select-none">
      <div className="rounded bg-surface/95 border border-border shadow-md backdrop-blur-xs text-xs font-sans">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="px-3 py-1.5 flex items-center space-x-2 text-ink-primary hover:text-copper transition-colors"
          aria-expanded={isOpen}
        >
          <HelpCircle className="w-3.5 h-3.5 text-copper" />
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider">MAP LEGEND</span>
          {isOpen ? <ChevronUp className="w-3 h-3 text-ink-muted" /> : <ChevronDown className="w-3 h-3 text-ink-muted" />}
        </button>

        {isOpen && (
          <div className="p-3 border-t border-border-subtle space-y-3 w-64 animate-in fade-in duration-150">
            {/* Electrical Flows */}
            <div className="space-y-1.5 font-mono text-[10px]">
              <span className="text-[9px] uppercase tracking-wider text-ink-muted block font-bold">
                ELECTRICAL POWER FLOWS
              </span>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-4 h-1 bg-[#0F766E] rounded-full"></span>
                  <span className="text-ink-secondary">Renewable Pure</span>
                </div>
                <span className="text-ink-muted text-[9px]">Solar/Wind</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-4 h-1 bg-[#0284C7] rounded-full"></span>
                  <span className="text-ink-secondary">Battery Storage</span>
                </div>
                <span className="text-ink-muted text-[9px]">BESS</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-4 h-1 bg-[#B45309] rounded-full"></span>
                  <span className="text-ink-secondary">Diesel Contribution</span>
                </div>
                <span className="text-ink-muted text-[9px]">Genset</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-4 h-1 bg-[#CBD5E1] rounded-full"></span>
                  <span className="text-ink-secondary">Dormant / Off</span>
                </div>
                <span className="text-ink-muted text-[9px]">0 kW</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-4 h-1 border-t border-dashed border-red-500"></span>
                  <span className="text-red-600 font-semibold">Circuit Fault</span>
                </div>
                <span className="text-red-500 text-[9px]">Tripped</span>
              </div>
            </div>

            {/* Device Priorities */}
            <div className="space-y-1.5 font-mono text-[10px] pt-2 border-t border-border-subtle">
              <span className="text-[9px] uppercase tracking-wider text-ink-muted block font-bold">
                SYSTEM CRITICALITY
              </span>
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded-full border-2 border-moss bg-moss/20"></span>
                <span className="text-ink-secondary">P1 Critical Life Support</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded-full border border-sky-600 bg-sky-100"></span>
                <span className="text-ink-secondary">P2 Important Science</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded-full border border-zinc-400 bg-zinc-100"></span>
                <span className="text-ink-secondary">P3 Operational Aux</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
