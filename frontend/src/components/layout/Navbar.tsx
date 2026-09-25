import React from 'react';
import { 
  LayoutDashboard, 
  TrendingUp, 
  Boxes, 
  Compass, 
  Cpu, 
  ShieldAlert, 
  Award, 
  Workflow, 
  Radio, 
  CheckCircle,
  FlaskConical,
  Palette
} from 'lucide-react';

export type TabType = 
  | 'overview' 
  | 'forecast' 
  | 'twin' 
  | 'scenarios' 
  | 'optimization' 
  | 'resilience' 
  | 'policy' 
  | 'edge' 
  | 'trace' 
  | 'validation'
  | 'field_hil'
  | 'design_lab';

interface NavbarProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
}

interface NavItem {
  id: TabType;
  index: string;
  label: string;
  icon: React.ReactNode;
  tag?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onSelectTab }) => {
  const navItems: NavItem[] = [
    { id: 'overview', index: '01', label: 'Overview', icon: <LayoutDashboard className="w-3.5 h-3.5" /> },
    { id: 'forecast', index: '02', label: 'Forecast', icon: <TrendingUp className="w-3.5 h-3.5" /> },
    { id: 'twin', index: '03', label: 'Energy Twin', icon: <Boxes className="w-3.5 h-3.5" />, tag: 'PRE-TWIN' },
    { id: 'scenarios', index: '04', label: 'Scenarios', icon: <Compass className="w-3.5 h-3.5" /> },
    { id: 'optimization', index: '05', label: 'Optimizer', icon: <Cpu className="w-3.5 h-3.5" /> },
    { id: 'resilience', index: '06', label: 'Resilience', icon: <ShieldAlert className="w-3.5 h-3.5" /> },
    { id: 'policy', index: '07', label: 'Policy', icon: <Award className="w-3.5 h-3.5" /> },
    { id: 'edge', index: '08', label: 'Devices', icon: <Radio className="w-3.5 h-3.5" /> },
    { id: 'trace', index: '09', label: 'Decision Trace', icon: <Workflow className="w-3.5 h-3.5" /> },
    { id: 'validation', index: '10', label: 'Validation', icon: <CheckCircle className="w-3.5 h-3.5" /> },
    { id: 'field_hil', index: '11', label: 'Field / HIL', icon: <FlaskConical className="w-3.5 h-3.5" /> },
    { id: 'design_lab', index: '12', label: 'Design Lab', icon: <Palette className="w-3.5 h-3.5" />, tag: 'LAB' },
  ];

  return (
    <nav className="bg-canvas-subtle border-b border-border sticky top-[65px] z-30 overflow-x-auto scrollbar-none" aria-label="Main Navigation">
      <div className="max-w-[1520px] mx-auto px-4 lg:px-6">
        <ul className="flex items-center space-x-1 sm:space-x-2 py-1 min-w-max" role="tablist">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <li key={item.id} role="presentation">
                <button
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => onSelectTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 text-xs font-mono transition-all duration-150 rounded-sm relative group ${
                    isActive
                      ? 'text-ink-primary font-semibold bg-surface shadow-xs border-b-2 border-copper'
                      : 'text-ink-muted hover:text-ink-primary hover:bg-surface/60'
                  }`}
                >
                  <span className={`text-[10px] ${isActive ? 'text-copper font-bold' : 'text-ink-subtle'}`}>
                    {item.index}
                  </span>
                  <span className="font-sans font-medium text-xs">{item.label}</span>
                  {item.tag && (
                    <span className="text-[9px] px-1 py-0.2 rounded bg-copper-soft text-copper font-mono font-bold tracking-tight">
                      {item.tag}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
};
