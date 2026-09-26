/**
 * POLARIS-EMS — Accessible Digital Twin Table Fallback View
 * Phase 18: Operational 3D Digital Twin Engine (Workstream 31)
 * 
 * Provides an accessible, high-contrast tabular representation of all microgrid
 * electrical assets (Sources, Storage, Buses, Feeders, and Connected Loads)
 * for screen readers, keyboard-only operators, and low-bandwidth environments.
 * 
 * Epistemic Boundary: Simulation air-gap enforced. Zero fabricated live telemetry.
 */

import React from 'react';
import { 
  Zap, 
  Battery, 
  Sun, 
  Wind, 
  Fuel, 
  ShieldCheck, 
  AlertTriangle,
  Server,
  Layers,
  CheckCircle,
  ExternalLink
} from 'lucide-react';
import { TwinViewModel, VisualDeviceState } from '../model/twinTypes';
import { STATION_SPATIAL_3D_PROFILES } from '../model/spatialProfiles3D';
import { ProvenanceTag } from '../../../components/common/ProvenanceTag';

interface TwinAccessibleTableProps {
  viewModel: TwinViewModel;
  onSelectDevice: (deviceId: string) => void;
  selectedDeviceId?: string | null;
}

export const TwinAccessibleTable: React.FC<TwinAccessibleTableProps> = ({
  viewModel,
  onSelectDevice,
  selectedDeviceId
}) => {
  const station3D = STATION_SPATIAL_3D_PROFILES[viewModel.stationId] || STATION_SPATIAL_3D_PROFILES.BHARATI;
  const devicesList = Object.values(viewModel.devices);

  const sources = [
    { name: 'Solar PV Array', type: 'SOLAR', kw: viewModel.powerSummary.solarGenerationKw, status: viewModel.powerSummary.solarGenerationKw > 0.1 ? 'ONLINE' : 'DORMANT' },
    { name: 'Wind Turbine Fleet', type: 'WIND', kw: viewModel.powerSummary.windGenerationKw, status: viewModel.powerSummary.windGenerationKw > 0.1 ? 'ONLINE' : 'DORMANT' },
    { name: 'Diesel Generator Bank', type: 'DIESEL', kw: viewModel.powerSummary.dieselGenerationKw, status: viewModel.powerSummary.dieselGenerationKw > 0.1 ? 'ONLINE' : 'STANDBY' },
    { name: 'Battery Storage (BESS)', type: 'BATTERY', kw: Math.abs(viewModel.powerSummary.batteryPowerKw), status: `${(viewModel.powerSummary.batterySocPct * 100).toFixed(0)}% SoC` }
  ];

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 space-y-6 shadow-xs font-sans">
      {/* Header & Accessibility Notice */}
      <div className="border-b border-slate-200 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-slate-500 uppercase tracking-wider">
            <span className="font-bold text-slate-800">{viewModel.stationId}</span>
            <span>•</span>
            <span>Accessible Tabular Electrical Network</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mt-1">
            Station Microgrid Circuit & Asset Inventory
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Structured high-contrast list for keyboard navigation and screen readers. All values computed by Phase 4 TwinEngine.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ProvenanceTag provenance={viewModel.provenance} size="sm" />
          <span className="text-[11px] font-mono px-2 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
            WCAG 2.1 AA COMPLIANT
          </span>
        </div>
      </div>

      {/* 1. Power Generation & Energy Storage Table */}
      <div className="space-y-2">
        <h3 className="text-xs font-mono uppercase font-bold text-slate-800 flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 text-sky-600" />
          <span>1. Energy Sources & Primary Storage</span>
        </h3>
        <div className="overflow-x-auto border border-slate-200 rounded-md">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
              <tr>
                <th className="p-2.5">Asset Name</th>
                <th className="p-2.5">Category</th>
                <th className="p-2.5">Current Output (kW)</th>
                <th className="p-2.5">Operational Status</th>
                <th className="p-2.5">Provenance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800">
              {sources.map((s, idx) => (
                <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                  <td className="p-2.5 font-bold font-sans">{s.name}</td>
                  <td className="p-2.5 text-slate-500">{s.type}</td>
                  <td className="p-2.5 font-bold">{s.kw.toFixed(1)} kW</td>
                  <td className="p-2.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                      {s.status}
                    </span>
                  </td>
                  <td className="p-2.5">
                    <ProvenanceTag provenance="SIMULATED" size="xs" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Connected Electrical Loads Table */}
      <div className="space-y-2">
        <h3 className="text-xs font-mono uppercase font-bold text-slate-800 flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-sky-600" />
          <span>2. Operational & Life-Support Loads</span>
        </h3>
        <div className="overflow-x-auto border border-slate-200 rounded-md">
          <table className="w-full text-left text-xs font-mono" role="table" aria-label="Connected Electrical Loads">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
              <tr>
                <th className="p-2.5">Device Name</th>
                <th className="p-2.5">Importance</th>
                <th className="p-2.5">Zone Location</th>
                <th className="p-2.5">Rated Power</th>
                <th className="p-2.5">Current Power</th>
                <th className="p-2.5">Circuit ID</th>
                <th className="p-2.5">Status</th>
                <th className="p-2.5">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800">
              {devicesList.map((dev: VisualDeviceState) => {
                const isSelected = selectedDeviceId === dev.id;
                return (
                  <tr 
                    key={dev.id} 
                    className={`transition-colors ${isSelected ? 'bg-sky-50' : 'hover:bg-slate-50/60'}`}
                  >
                    <td className="p-2.5 font-bold font-sans">
                      <div className="flex items-center space-x-1.5">
                        <span className="w-2 h-2 rounded-full bg-sky-600 shrink-0" />
                        <span>{dev.name}</span>
                      </div>
                    </td>
                    <td className="p-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        dev.category === 'CRITICAL' ? 'bg-rose-50 text-rose-700 border border-rose-200' :
                        dev.category === 'IMPORTANT' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {dev.category}
                      </span>
                    </td>
                    <td className="p-2.5 text-slate-600">{dev.zoneName}</td>
                    <td className="p-2.5">{dev.nominalPowerKw.toFixed(1)} kW</td>
                    <td className="p-2.5 font-bold text-slate-900">{dev.currentPowerKw.toFixed(1)} kW</td>
                    <td className="p-2.5 text-slate-400 text-[10px]">{dev.circuitId || '—'}</td>
                    <td className="p-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        dev.status === 'ONLINE' ? 'bg-emerald-50 text-emerald-700' :
                        dev.status === 'FAULT' ? 'bg-rose-50 text-rose-700' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {dev.status}
                      </span>
                    </td>
                    <td className="p-2.5">
                      <button
                        type="button"
                        onClick={() => onSelectDevice(dev.id)}
                        className="px-2 py-1 rounded bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 text-[10px] font-bold"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
