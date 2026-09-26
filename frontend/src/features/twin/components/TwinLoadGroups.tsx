/**
 * POLARIS-EMS — Digital Twin Aggregated Load Groups & Importance
 * Phase 18: Operational 3D Digital Twin Engine (Workstream 10 & 11)
 * 
 * Aggregates all station connected devices into 5 clean functional groups:
 * LIFE SUPPORT, SCIENCE, HABITATION, COMMUNICATIONS, WORKSHOP.
 * Classified by P1–P4 importance hierarchy. Clicking opens the detail drawer.
 */

import React from 'react';
import { 
  Activity, 
  Microscope, 
  Home, 
  Radio, 
  Wrench, 
  ShieldAlert, 
  ChevronRight,
  Zap
} from 'lucide-react';
import { TwinViewModel, VisualDeviceState } from '../model/twinTypes';

interface TwinLoadGroupsProps {
  viewModel: TwinViewModel;
  onSelectGroup?: (groupName: string) => void;
  onSelectDevice?: (deviceId: string) => void;
}

export const TwinLoadGroups: React.FC<TwinLoadGroupsProps> = ({
  viewModel,
  onSelectGroup,
  onSelectDevice
}) => {
  const devices = Object.values(viewModel.devices);

  // Group calculations
  const groups = [
    {
      id: 'LIFE_SUPPORT',
      name: 'LIFE SUPPORT',
      importance: 'CRITICAL (P1)',
      icon: Activity,
      color: 'rose',
      devices: devices.filter(d => d.id.includes('life') || d.id.includes('water') || d.id.includes('heat') || d.id.includes('boiler')),
      description: 'Habitat climate pressurization, freeze protection, potable water supply'
    },
    {
      id: 'COMMUNICATIONS',
      name: 'COMMUNICATIONS',
      importance: 'CRITICAL (P1/P2)',
      icon: Radio,
      color: 'rose',
      devices: devices.filter(d => d.id.includes('comms') || d.id.includes('satcom') || d.id.includes('telemetry') || d.id.includes('nav')),
      description: 'Satellite uplink bridge, emergency HF/VHF radio, mission data gateway'
    },
    {
      id: 'HABITATION',
      name: 'HABITATION',
      importance: 'IMPORTANT (P2)',
      icon: Home,
      color: 'emerald',
      devices: devices.filter(d => d.id.includes('residential') || d.id.includes('galley') || d.id.includes('living') || d.id.includes('berth')),
      description: 'Crew berths, kitchen refrigeration, galley cooking, domestic power'
    },
    {
      id: 'SCIENCE',
      name: 'SCIENCE',
      importance: 'OPERATIONAL (P3)',
      icon: Microscope,
      color: 'violet',
      devices: devices.filter(d => d.id.includes('sci') || d.id.includes('lab') || d.id.includes('brewer') || d.id.includes('geomag') || d.id.includes('incubator') || d.id.includes('lidar')),
      description: 'Spectrophotometers, air monitoring arrays, cryo sample bio-freezers'
    },
    {
      id: 'WORKSHOP',
      name: 'WORKSHOP',
      importance: 'FLEXIBLE (P4)',
      icon: Wrench,
      color: 'amber',
      devices: devices.filter(d => d.id.includes('work') || d.id.includes('ev') || d.id.includes('charge') || d.id.includes('tool')),
      description: 'Equipment repair tools, skidoo block heating, battery charging docks'
    }
  ];

  return (
    <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-xs space-y-3 font-sans select-none">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <div className="flex items-center space-x-2">
          <Zap className="w-3.5 h-3.5 text-sky-600" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
            AGGREGATED LOAD GROUPS & POLICY IMPORTANCE
          </span>
        </div>
        <span className="text-[10px] font-mono text-slate-400">
          Total Demand: {viewModel.powerSummary.totalLoadKw.toFixed(1)} kW
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
        {groups.map(grp => {
          const Icon = grp.icon;
          const groupPower = grp.devices.reduce((acc, d) => acc + (d.currentPowerKw || 0), 0);
          const hasDevices = grp.devices.length > 0;

          return (
            <div
              key={grp.id}
              onClick={() => {
                if (hasDevices && onSelectDevice) {
                  onSelectDevice(grp.devices[0].id);
                }
              }}
              className="bg-slate-50 hover:bg-slate-100/80 rounded-lg p-3 border border-slate-200 cursor-pointer transition-all hover:border-slate-300 shadow-2xs group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1.5">
                    <Icon className="w-3.5 h-3.5 text-slate-600 group-hover:text-sky-600 transition-colors" />
                    <span className="text-xs font-bold text-slate-900 truncate">{grp.name}</span>
                  </div>
                  <ChevronRight className="w-3 h-3 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                </div>
                <span className={`inline-block text-[9px] font-mono font-bold mt-1 px-1.5 py-0.2 rounded ${
                  grp.color === 'rose' ? 'bg-rose-50 text-rose-700' :
                  grp.color === 'emerald' ? 'bg-emerald-50 text-emerald-700' :
                  grp.color === 'violet' ? 'bg-purple-50 text-purple-700' :
                  'bg-amber-50 text-amber-700'
                }`}>
                  {grp.importance}
                </span>
                <p className="text-[10px] text-slate-500 mt-1 line-clamp-2 leading-tight">
                  {grp.description}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-200/60 flex items-baseline justify-between font-mono">
                <span className="text-[10px] text-slate-400 uppercase">ACTIVE DRAW</span>
                <div className="text-base font-bold text-slate-900">
                  {groupPower.toFixed(1)} <span className="text-[10px] font-normal text-slate-400">kW</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
