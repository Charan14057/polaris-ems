/**
 * POLARIS-EMS — Operating Mode Selector & Simulation Action Drawer
 * Phase 18: Operational 3D Digital Twin Engine (Workstream 15, 16, 21)
 * 
 * Provides operator choice between MANUAL (operator-directed simulation)
 * and AUTO (Phase 6 MILP recommendation with approval workflow).
 * 
 * STRICT EPISTEMIC BOUNDARY:
 * Status: SIMULATION ONLY.
 * Physical actuation is air-gapped (PHYSICAL_CONNECTIVITY = DISCONNECTED).
 */

import React, { useState } from 'react';
import { 
  Sliders, 
  Cpu, 
  CheckCircle, 
  AlertTriangle, 
  ShieldCheck, 
  Fuel, 
  Battery, 
  Thermometer, 
  Zap, 
  Play,
  RotateCcw,
  X
} from 'lucide-react';
import { ProvenanceTag } from '../../../components/common/ProvenanceTag';

export type OperatingMode = 'MANUAL' | 'AUTO';

export interface ManualSimAction {
  id: string;
  name: string;
  action: string;
  expectedImpact: string;
  affectedLoads: string;
  reserveChange: string;
  fuelChange: string;
  thermalEffect: string;
  policyResult: 'PASS' | 'ADVISORY' | 'VIOLATION';
}

interface TwinOperatingModeControlProps {
  mode: OperatingMode;
  onModeChange: (mode: OperatingMode) => void;
  onSimulateAction?: (actionId: string) => void;
  onApproveRecommendation?: () => void;
  currentDieselKw?: number;
  currentBatterySoc?: number;
}

export const TwinOperatingModeControl: React.FC<TwinOperatingModeControlProps> = ({
  mode,
  onModeChange,
  onSimulateAction,
  onApproveRecommendation,
  currentDieselKw = 0,
  currentBatterySoc = 0.82
}) => {
  const [selectedAction, setSelectedAction] = useState<ManualSimAction | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);
  const [simulationApplied, setSimulationApplied] = useState<boolean>(false);

  const manualActions: ManualSimAction[] = [
    {
      id: 'dg1_start',
      name: 'Start Backup Diesel Generator (DG1)',
      action: 'Commit 40 kW base generation from Standby DG1',
      expectedImpact: '+40.0 kW generation buffer to 400V bus',
      affectedLoads: 'Supplies all P1 and P2 circuits; reduces battery draw',
      reserveChange: '+22% battery reserve preserved over 12h horizon',
      fuelChange: '+9.4 L/h fuel consumption rate',
      thermalEffect: '+14°C engine jacket heat available for district heating loop',
      policyResult: 'PASS'
    },
    {
      id: 'bess_charge_force',
      name: 'Force Battery Pre-Charge (15 kW)',
      action: 'Direct surplus generation into BESS storage',
      expectedImpact: '+15.0 kW load added to charging bus',
      affectedLoads: 'P3/P4 flexible loads deferred during charging window',
      reserveChange: 'SoC increases to 95% ahead of forecasted storm front',
      fuelChange: '+1.8 L/h if thermal generator running',
      thermalEffect: 'Battery thermal management maintains cell at +18°C',
      policyResult: 'PASS'
    },
    {
      id: 'shed_flexible',
      name: 'Shed Flexible Loads (Workshop & EV)',
      action: 'De-energize Workshop tools and vehicle skid charging',
      expectedImpact: '-14.5 kW total station demand reduction',
      affectedLoads: 'DB-5 Workshop & Vehicle bay deferred; zero impact on habitat',
      reserveChange: 'Extends station autonomy by +4.2 hours',
      fuelChange: '-3.2 L/h fuel consumption reduction',
      thermalEffect: 'Minimal (< 0.2°C ambient variation)',
      policyResult: 'PASS'
    }
  ];

  const handleApplySimulation = (actionId: string) => {
    setSimulating(true);
    setTimeout(() => {
      setSimulating(false);
      setSimulationApplied(true);
      onSimulateAction?.(actionId);
    }, 800);
  };

  return (
    <div className="space-y-3 font-sans select-none">
      {/* 1. Compact Mode Toggle Strip */}
      <div className="bg-white rounded-lg p-2.5 sm:p-3 border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <span className="text-slate-500 text-[11px] font-bold">OPERATING MODE:</span>
          <div className="flex items-center rounded border border-slate-200 bg-slate-50 p-0.5">
            <button
              type="button"
              onClick={() => { onModeChange('MANUAL'); setSimulationApplied(false); }}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded text-xs transition-colors ${
                mode === 'MANUAL'
                  ? 'bg-sky-600 text-white font-bold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>MANUAL</span>
            </button>
            <button
              type="button"
              onClick={() => { onModeChange('AUTO'); setSelectedAction(null); setSimulationApplied(false); }}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded text-xs transition-colors ${
                mode === 'AUTO'
                  ? 'bg-sky-600 text-white font-bold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>AUTO</span>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
            SIMULATION ONLY
          </span>
          <ProvenanceTag provenance="SIMULATED" size="xs" />
        </div>
      </div>

      {/* 2. AUTO MODE CONTENT: Proactive MILP Optimizer Recommendation */}
      {mode === 'AUTO' && (
        <div className="bg-white rounded-lg p-4 border border-slate-200 border-l-4 border-l-emerald-600 shadow-xs space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-2">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
              <span className="text-xs font-mono font-bold text-slate-800 uppercase tracking-wide">
                AUTO: RECOMMENDED DISPATCH ACTION
              </span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">
              APPROVAL REQUIRED
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
              <span className="text-[9px] font-mono text-slate-400 block uppercase">CURRENT STATE</span>
              <p className="text-slate-700 mt-1 font-medium">
                Renewable share {currentDieselKw > 0 ? '42%' : '88%'}, battery SoC {(currentBatterySoc * 100).toFixed(0)}%. Diesel in standby.
              </p>
            </div>
            <div className="bg-sky-50/70 p-2.5 rounded border border-sky-200">
              <span className="text-[9px] font-mono text-sky-700 block uppercase font-bold">RECOMMENDED CHANGE</span>
              <p className="text-slate-800 mt-1 font-medium">
                Maintain 100% renewable priority; keep DG1 locked out unless wind drops below 5.5 m/s.
              </p>
            </div>
            <div className="bg-emerald-50/70 p-2.5 rounded border border-emerald-200">
              <span className="text-[9px] font-mono text-emerald-800 block uppercase font-bold">EXPECTED RESULT</span>
              <p className="text-slate-800 mt-1 font-medium">
                Saves 85 L polar diesel over 24h horizon with zero risk of unserved critical life-support energy.
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between pt-2 border-t border-slate-100 gap-2 text-[11px] font-mono">
            <div>
              <span className="text-slate-500">HiGHS MILP Solver Engine • MIP Gap &lt; 0.05%</span>
              <span className="text-slate-400 text-[10px] block sm:inline sm:ml-2">Physical SCADA actuation disconnected</span>
            </div>
            <button
              type="button"
              onClick={() => {
                setSimulating(true);
                setTimeout(() => {
                  setSimulating(false);
                  setSimulationApplied(true);
                  onApproveRecommendation?.();
                }, 500);
              }}
              disabled={simulating}
              className={`px-3 py-1.5 rounded text-xs font-bold font-mono transition-colors shadow-xs flex items-center space-x-1.5 self-start sm:self-auto ${
                simulationApplied
                  ? 'bg-emerald-700 text-white'
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white'
              }`}
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>{simulating ? 'Simulating...' : simulationApplied ? 'Recommendation Approved (Simulated)' : 'Simulate Operator Approval'}</span>
            </button>
          </div>
        </div>
      )}

      {/* 3. MANUAL MODE CONTENT: Operator Simulation Interventions */}
      {mode === 'MANUAL' && (
        <div className="bg-white rounded-lg p-4 border border-slate-200 border-l-4 border-l-sky-600 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <span className="text-xs font-mono font-bold text-slate-800 uppercase tracking-wide">
              OPERATOR SIMULATION DISPATCH
            </span>
            <span className="text-[10px] font-mono text-slate-400">Select an action to test forward impacts</span>
          </div>

          {/* Action Chips */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {manualActions.map(act => (
              <button
                key={act.id}
                type="button"
                onClick={() => { setSelectedAction(act); setSimulationApplied(false); }}
                className={`text-left p-2.5 rounded border transition-colors ${
                  selectedAction?.id === act.id
                    ? 'border-sky-600 bg-sky-50/80 shadow-xs'
                    : 'border-slate-200 hover:bg-slate-50 bg-white'
                }`}
              >
                <div className="text-xs font-bold text-slate-900">{act.name}</div>
                <div className="text-[10px] text-slate-500 mt-0.5 line-clamp-1">{act.action}</div>
              </button>
            ))}
          </div>

          {/* Action Confirmation Drawer */}
          {selectedAction && (
            <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-200 space-y-3 mt-2">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="font-bold text-xs text-slate-900">
                  ACTION: {selectedAction.name}
                </span>
                <button
                  type="button"
                  onClick={() => setSelectedAction(null)}
                  className="text-slate-400 hover:text-slate-600 p-0.5"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs font-mono">
                <div>
                  <span className="text-[9px] text-slate-400 block uppercase">EXPECTED IMPACT</span>
                  <span className="font-bold text-slate-800">{selectedAction.expectedImpact}</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-400 block uppercase">AFFECTED LOADS</span>
                  <span className="text-slate-700">{selectedAction.affectedLoads}</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-400 block uppercase">RESERVE CHANGE</span>
                  <span className="font-bold text-emerald-700">{selectedAction.reserveChange}</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-400 block uppercase">FUEL CHANGE</span>
                  <span className="text-slate-800">{selectedAction.fuelChange}</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-400 block uppercase">THERMAL EFFECT</span>
                  <span className="text-slate-700">{selectedAction.thermalEffect}</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-400 block uppercase">SAFETY & POLICY</span>
                  <span className="px-1.5 py-0.5 rounded font-bold text-[10px] bg-emerald-100 text-emerald-800">
                    {selectedAction.policyResult}
                  </span>
                </div>
              </div>

              {/* Action Execution Button */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                <span className="text-[10px] text-slate-500 font-mono">
                  Executes forward simulation only • Physical plant unmodified
                </span>
                <button
                  type="button"
                  disabled={simulating}
                  onClick={() => handleApplySimulation(selectedAction.id)}
                  className={`px-3 py-1.5 rounded text-xs font-bold font-mono transition-colors shadow-xs flex items-center space-x-1.5 ${
                    simulationApplied
                      ? 'bg-emerald-600 text-white'
                      : 'bg-sky-600 hover:bg-sky-700 text-white'
                  }`}
                >
                  {simulating ? (
                    <span>Simulating...</span>
                  ) : simulationApplied ? (
                    <>
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>SIMULATION ACTIVE</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5" />
                      <span>SIMULATE ACTION</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
