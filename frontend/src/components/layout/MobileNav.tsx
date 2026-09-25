import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  Zap, 
  TrendingUp, 
  Compass, 
  MoreHorizontal,
  Cpu,
  ShieldAlert,
  Radio,
  Workflow,
  CheckCircle,
  Award,
  FlaskConical,
  X
} from 'lucide-react';
import { TabType } from './Navbar';

interface MobileNavProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
}

export const MobileNav: React.FC<MobileNavProps> = ({ activeTab, onSelectTab }) => {
  const [moreOpen, setMoreOpen] = useState<boolean>(false);

  const primaryItems = [
    { id: 'overview' as TabType, label: 'Overview', icon: LayoutDashboard },
    { id: 'twin' as TabType, label: 'Energy', icon: Zap },
    { id: 'forecast' as TabType, label: 'Forecast', icon: TrendingUp },
    { id: 'scenarios' as TabType, label: 'Scenarios', icon: Compass },
  ];

  const secondaryItems = [
    { id: 'optimization' as TabType, label: 'Dispatch Optimization', icon: Cpu, section: 'Operations' },
    { id: 'resilience' as TabType, label: 'Resilience Analysis', icon: ShieldAlert, section: 'Situational' },
    { id: 'edge' as TabType, label: 'Asset Telemetry', icon: Radio, section: 'Situational' },
    { id: 'trace' as TabType, label: 'Decision Trace', icon: Workflow, section: 'Situational' },
    { id: 'validation' as TabType, label: 'Software Validation', icon: CheckCircle, section: 'Assurance' },
    { id: 'policy' as TabType, label: 'Policy Rules', icon: Award, section: 'Engineering' },
    { id: 'field_hil' as TabType, label: 'Field / HIL Emulation', icon: FlaskConical, section: 'Engineering' },
  ];

  const isMoreActive = secondaryItems.some(item => item.id === activeTab);

  return (
    <>
      {/* Fixed Bottom Navigation Bar on Mobile */}
      <nav 
        className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 px-2 py-1.5 flex items-center justify-around shadow-lg"
        aria-label="Mobile navigation"
      >
        {primaryItems.map(item => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`flex flex-col items-center justify-center py-1 px-2.5 rounded-md text-[11px] font-medium transition-colors ${
                isActive ? 'text-sky-600 font-semibold' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              <Icon className={`w-5 h-5 mb-0.5 ${isActive ? 'text-sky-600' : 'text-slate-500'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}

        {/* More Trigger */}
        <button
          onClick={() => setMoreOpen(true)}
          className={`flex flex-col items-center justify-center py-1 px-2.5 rounded-md text-[11px] font-medium transition-colors ${
            isMoreActive ? 'text-sky-600 font-semibold' : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          <MoreHorizontal className={`w-5 h-5 mb-0.5 ${isMoreActive ? 'text-sky-600' : 'text-slate-500'}`} />
          <span>More</span>
        </button>
      </nav>

      {/* Secondary Destinations Slide-over Drawer */}
      {moreOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex flex-col justify-end">
          <div 
            className="fixed inset-0 bg-slate-900/40"
            onClick={() => setMoreOpen(false)}
            aria-hidden="true"
          />
          <div className="relative bg-white rounded-t-xl border-t border-slate-200 p-4 max-h-[75vh] overflow-y-auto space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="font-semibold text-slate-900 text-sm">Additional Destinations</span>
              <button
                onClick={() => setMoreOpen(false)}
                className="p-1 rounded-md text-slate-400 hover:text-slate-600"
                aria-label="Close menu"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 gap-1">
              {secondaryItems.map(item => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onSelectTab(item.id);
                      setMoreOpen(false);
                    }}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors text-left ${
                      isActive ? 'bg-sky-50 text-sky-700 font-semibold' : 'text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <Icon className="w-4 h-4 shrink-0 text-slate-500" />
                    <div className="flex-1">
                      <div className="font-medium text-xs text-slate-900">{item.label}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{item.section}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
