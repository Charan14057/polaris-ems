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
  FlaskConical
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
  label: string;
  icon: React.ReactNode;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onSelectTab }) => {
  const navItems: NavItem[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="w-3.5 h-3.5" /> },
    { id: 'twin', label: 'Energy Twin', icon: <Boxes className="w-3.5 h-3.5" /> },
    { id: 'forecast', label: 'Forecast', icon: <TrendingUp className="w-3.5 h-3.5" /> },
    { id: 'scenarios', label: 'Scenarios', icon: <Compass className="w-3.5 h-3.5" /> },
    { id: 'optimization', label: 'Optimizer', icon: <Cpu className="w-3.5 h-3.5" /> },
    { id: 'resilience', label: 'Resilience', icon: <ShieldAlert className="w-3.5 h-3.5" /> },
    { id: 'policy', label: 'Policy', icon: <Award className="w-3.5 h-3.5" /> },
    { id: 'edge', label: 'Devices', icon: <Radio className="w-3.5 h-3.5" /> },
    { id: 'trace', label: 'Decision Trace', icon: <Workflow className="w-3.5 h-3.5" /> },
    { id: 'validation', label: 'Validation', icon: <CheckCircle className="w-3.5 h-3.5" /> },
    { id: 'field_hil', label: 'Field / HIL', icon: <FlaskConical className="w-3.5 h-3.5" /> },
  ];

  return (
    <nav className="bg-white border-b border-slate-200 overflow-x-auto scrollbar-none" aria-label="Main Navigation">
      <div className="max-w-[1520px] mx-auto px-4 lg:px-6">
        <ul className="flex items-center space-x-1 py-1 min-w-max" role="tablist">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <li key={item.id} role="presentation">
                <button
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => onSelectTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-1.5 text-xs font-medium transition-colors rounded-md ${
                    isActive
                      ? 'text-sky-700 font-semibold bg-sky-50 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
};
