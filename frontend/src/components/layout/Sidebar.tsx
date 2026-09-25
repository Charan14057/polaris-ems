import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Zap, 
  TrendingUp, 
  Compass, 
  Cpu, 
  ShieldAlert, 
  Radio, 
  Workflow, 
  CheckCircle, 
  Award, 
  FlaskConical,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Layers,
  Wrench,
  X
} from 'lucide-react';
import { TabType } from './Navbar';

interface SidebarProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  mobileOpen = false,
  onCloseMobile,
  isCollapsed: controlledCollapsed,
  onToggleCollapse: controlledToggle
}) => {
  const [localCollapsed, setLocalCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem('polaris_sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });
  const [assuranceOpen, setAssuranceOpen] = useState<boolean>(true);
  const [engineeringOpen, setEngineeringOpen] = useState<boolean>(true);

  const isCollapsed = controlledCollapsed !== undefined ? controlledCollapsed : localCollapsed;

  const toggleCollapse = () => {
    if (controlledToggle) {
      controlledToggle();
    } else {
      setLocalCollapsed(prev => {
        const next = !prev;
        try {
          localStorage.setItem('polaris_sidebar_collapsed', String(next));
        } catch {}
        return next;
      });
    }
  };

  const handleSelect = (tab: TabType) => {
    onSelectTab(tab);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  const navItemClass = (isActive: boolean) => `
    flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors
    ${isActive 
      ? 'bg-sky-50 text-sky-700 font-semibold' 
      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'}
  `;

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/40 z-40 md:hidden transition-opacity"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside 
        className={`
          fixed top-0 bottom-0 left-0 z-50 bg-white border-r border-slate-200 flex flex-col transition-all duration-200 ease-in-out
          ${mobileOpen ? 'translate-x-0 w-64 shadow-xl' : '-translate-x-full md:translate-x-0'}
          ${isCollapsed ? 'md:w-16' : 'md:w-60'}
        `}
        aria-label="Application navigation"
      >
        {/* Brand / Logo Area */}
        <div className="h-14 border-b border-slate-200 flex items-center justify-between px-3.5 shrink-0">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-md bg-sky-600 flex items-center justify-center text-white shrink-0 shadow-sm">
              <Zap className="w-4 h-4" />
            </div>
            {!isCollapsed && (
              <div className="truncate">
                <span className="font-bold text-slate-900 text-sm tracking-tight">Polaris EMS</span>
                <span className="block text-[10px] text-slate-400 font-mono tracking-wider">UTILITY OPS</span>
              </div>
            )}
          </div>

          {/* Desktop Collapse Toggle */}
          <button
            onClick={toggleCollapse}
            className="hidden md:flex items-center justify-center w-7 h-7 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>

          {/* Mobile Close Button */}
          <button
            onClick={onCloseMobile}
            className="md:hidden flex items-center justify-center w-7 h-7 rounded text-slate-400 hover:text-slate-600"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Content */}
        <nav className="flex-1 overflow-y-auto px-2.5 py-3 space-y-5">
          {/* Group 1: Operations */}
          <div>
            {!isCollapsed && (
              <div className="px-2.5 mb-1.5 text-[10px] font-semibold font-mono uppercase tracking-wider text-slate-400">
                Operations
              </div>
            )}
            <div className="space-y-0.5">
              <button
                onClick={() => handleSelect('overview')}
                className={`w-full ${navItemClass(activeTab === 'overview')} ${isCollapsed ? 'justify-center px-0' : ''}`}
                title="Overview"
              >
                <LayoutDashboard className="w-4 h-4 shrink-0" />
                {!isCollapsed && <span>Overview</span>}
              </button>

              <button
                onClick={() => handleSelect('twin')}
                className={`w-full ${navItemClass(activeTab === 'twin')} ${isCollapsed ? 'justify-center px-0' : ''}`}
                title="Energy"
              >
                <Zap className="w-4 h-4 shrink-0 text-sky-600" />
                {!isCollapsed && <span>Energy</span>}
              </button>

              <button
                onClick={() => handleSelect('forecast')}
                className={`w-full ${navItemClass(activeTab === 'forecast')} ${isCollapsed ? 'justify-center px-0' : ''}`}
                title="Forecast"
              >
                <TrendingUp className="w-4 h-4 shrink-0" />
                {!isCollapsed && <span>Forecast</span>}
              </button>

              <button
                onClick={() => handleSelect('scenarios')}
                className={`w-full ${navItemClass(activeTab === 'scenarios')} ${isCollapsed ? 'justify-center px-0' : ''}`}
                title="Scenarios"
              >
                <Compass className="w-4 h-4 shrink-0" />
                {!isCollapsed && <span>Scenarios</span>}
              </button>

              <button
                onClick={() => handleSelect('optimization')}
                className={`w-full ${navItemClass(activeTab === 'optimization')} ${isCollapsed ? 'justify-center px-0' : ''}`}
                title="Dispatch"
              >
                <Cpu className="w-4 h-4 shrink-0" />
                {!isCollapsed && <span>Dispatch</span>}
              </button>
            </div>
          </div>

          {/* Group 2: Situational */}
          <div>
            {!isCollapsed && (
              <div className="px-2.5 mb-1.5 text-[10px] font-semibold font-mono uppercase tracking-wider text-slate-400">
                Situational
              </div>
            )}
            <div className="space-y-0.5">
              <button
                onClick={() => handleSelect('resilience')}
                className={`w-full ${navItemClass(activeTab === 'resilience')} ${isCollapsed ? 'justify-center px-0' : ''}`}
                title="Resilience"
              >
                <ShieldAlert className="w-4 h-4 shrink-0" />
                {!isCollapsed && <span>Resilience</span>}
              </button>

              <button
                onClick={() => handleSelect('edge')}
                className={`w-full ${navItemClass(activeTab === 'edge')} ${isCollapsed ? 'justify-center px-0' : ''}`}
                title="Assets"
              >
                <Radio className="w-4 h-4 shrink-0" />
                {!isCollapsed && <span>Assets</span>}
              </button>

              <button
                onClick={() => handleSelect('trace')}
                className={`w-full ${navItemClass(activeTab === 'trace')} ${isCollapsed ? 'justify-center px-0' : ''}`}
                title="Decisions"
              >
                <Workflow className="w-4 h-4 shrink-0" />
                {!isCollapsed && <span>Decisions</span>}
              </button>
            </div>
          </div>

          {/* Group 3: Collapsible Assurance & Engineering */}
          <div className="pt-2 border-t border-slate-100">
            {/* Assurance */}
            {!isCollapsed ? (
              <div className="mb-2">
                <button
                  onClick={() => setAssuranceOpen(!assuranceOpen)}
                  className="w-full flex items-center justify-between px-2.5 py-1 text-[10px] font-semibold font-mono uppercase tracking-wider text-slate-400 hover:text-slate-600"
                >
                  <span className="flex items-center gap-1.5">
                    <Layers className="w-3 h-3" />
                    Assurance
                  </span>
                  <ChevronDown className={`w-3 h-3 transition-transform ${assuranceOpen ? '' : '-rotate-90'}`} />
                </button>
                {assuranceOpen && (
                  <div className="mt-1 space-y-0.5">
                    <button
                      onClick={() => handleSelect('validation')}
                      className={`w-full ${navItemClass(activeTab === 'validation')}`}
                    >
                      <CheckCircle className="w-4 h-4 shrink-0 text-emerald-600" />
                      <span>Validation</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => handleSelect('validation')}
                className={`w-full ${navItemClass(activeTab === 'validation')} justify-center px-0 mb-2`}
                title="Validation"
              >
                <CheckCircle className="w-4 h-4 shrink-0 text-emerald-600" />
              </button>
            )}

            {/* Engineering */}
            {!isCollapsed ? (
              <div>
                <button
                  onClick={() => setEngineeringOpen(!engineeringOpen)}
                  className="w-full flex items-center justify-between px-2.5 py-1 text-[10px] font-semibold font-mono uppercase tracking-wider text-slate-400 hover:text-slate-600"
                >
                  <span className="flex items-center gap-1.5">
                    <Wrench className="w-3 h-3" />
                    Engineering
                  </span>
                  <ChevronDown className={`w-3 h-3 transition-transform ${engineeringOpen ? '' : '-rotate-90'}`} />
                </button>
                {engineeringOpen && (
                  <div className="mt-1 space-y-0.5">
                    <button
                      onClick={() => handleSelect('policy')}
                      className={`w-full ${navItemClass(activeTab === 'policy')}`}
                    >
                      <Award className="w-4 h-4 shrink-0" />
                      <span>Policy Rules</span>
                    </button>
                    <button
                      onClick={() => handleSelect('field_hil')}
                      className={`w-full ${navItemClass(activeTab === 'field_hil')}`}
                    >
                      <FlaskConical className="w-4 h-4 shrink-0 text-amber-600" />
                      <span>Field / HIL</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-1">
                <button
                  onClick={() => handleSelect('policy')}
                  className={`w-full ${navItemClass(activeTab === 'policy')} justify-center px-0`}
                  title="Policy"
                >
                  <Award className="w-4 h-4 shrink-0" />
                </button>
                <button
                  onClick={() => handleSelect('field_hil')}
                  className={`w-full ${navItemClass(activeTab === 'field_hil')} justify-center px-0`}
                  title="Field / HIL"
                >
                  <FlaskConical className="w-4 h-4 shrink-0 text-amber-600" />
                </button>
              </div>
            )}
          </div>
        </nav>

        {/* Bottom Environment Status Strip */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/50">
          {!isCollapsed ? (
            <div className="text-[11px] text-slate-500 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                <span>Simulation Safe</span>
              </span>
              <span className="font-mono text-[10px] text-slate-400">v1.8</span>
            </div>
          ) : (
            <div className="flex justify-center" title="Simulation Safe">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
