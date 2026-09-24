import React from 'react';
import { 
  LayoutDashboard, 
  Cpu, 
  TrendingUp, 
  AlertTriangle, 
  Zap, 
  ShieldAlert, 
  Scale, 
  GitCommit,
  Radio
} from 'lucide-react';

export type TabType = 
  | 'overview' 
  | 'twin' 
  | 'forecast' 
  | 'scenarios' 
  | 'optimization' 
  | 'resilience' 
  | 'policy' 
  | 'trace'
  | 'edge';

export type ActiveTab = TabType;

interface NavbarProps {
  activeTab: TabType;
  setActiveTab?: (tab: TabType) => void;
  onSelectTab?: (tab: TabType) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, onSelectTab }) => {
  const handleSelect = (tab: TabType) => {
    if (setActiveTab) setActiveTab(tab);
    if (onSelectTab) onSelectTab(tab);
  };

  const tabs: { id: TabType; label: string; icon: React.ReactNode; phase: string }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="w-4 h-4" />, phase: 'Snapshot' },
    { id: 'twin', label: 'Energy Twin', icon: <Cpu className="w-4 h-4" />, phase: 'Phase 4' },
    { id: 'forecast', label: 'Forecast', icon: <TrendingUp className="w-4 h-4" />, phase: 'Phase 3' },
    { id: 'scenarios', label: 'Scenarios', icon: <AlertTriangle className="w-4 h-4" />, phase: 'Phase 5' },
    { id: 'optimization', label: 'Optimizer', icon: <Zap className="w-4 h-4" />, phase: 'Phase 6' },
    { id: 'resilience', label: 'Resilience', icon: <ShieldAlert className="w-4 h-4" />, phase: 'Phase 7' },
    { id: 'policy', label: 'Policy', icon: <Scale className="w-4 h-4" />, phase: 'Phase 8' },
    { id: 'trace', label: 'Decision Trace', icon: <GitCommit className="w-4 h-4" />, phase: 'Pipeline' },
    { id: 'edge', label: 'Edge & Devices', icon: <Radio className="w-4 h-4" />, phase: 'Phase 11' },
  ];

  return (
    <nav className="bg-polar-950/80 border-b border-polar-800 px-4 lg:px-6 overflow-x-auto no-scrollbar" aria-label="Main Navigation">
      <div className="flex space-x-1 min-w-max py-1.5">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleSelect(tab.id)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-polar-800 text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-950/20'
                  : 'text-polar-400 hover:text-polar-200 hover:bg-polar-900/60'
              }`}
            >
              <span className={isActive ? 'text-cyan-400' : 'text-polar-500'}>
                {tab.icon}
              </span>
              <span>{tab.label}</span>
              <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-polar-900/80 text-polar-500 border border-polar-800">
                {tab.phase}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
