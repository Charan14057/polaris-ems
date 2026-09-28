import React, { useState } from 'react';
import { StationProvider, useStation, useOperationalSnapshot } from './context/StationContext';
import { EvidenceProvider } from './context/EvidenceContext';
import { ComprehensionProvider, useComprehension } from './context/ComprehensionContext';
import { QuickOrientationModal } from './components/common/QuickOrientationModal';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import { MobileNav } from './components/layout/MobileNav';
import { TabType } from './components/layout/Navbar';
import { AlertRibbon } from './components/layout/AlertRibbon';
import { EvidenceDrawer } from './components/common/EvidenceDrawer';
import { OverviewView } from './views/OverviewView';
import { EnergyTwinView } from './views/EnergyTwinView';
import { ForecastView } from './views/ForecastView';
import { ScenariosView } from './views/ScenariosView';
import { OptimizationView } from './views/OptimizationView';
import { ResilienceView } from './views/ResilienceView';
import { PolicyView } from './views/PolicyView';
import { DecisionTraceView } from './views/DecisionTraceView';
import { EdgeView } from './views/EdgeView';
import { ValidationView } from './views/ValidationView';
import { FieldHILValidationView } from './views/FieldHILValidationView';
import { DesignLabView } from './views/DesignLabView';
import { ShieldCheck, WifiOff } from 'lucide-react';

const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem('polaris_sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });

  const { activeThreats } = useStation();
  const { isOrientationOpen, closeOrientation } = useComprehension();
  const { toast, dismissToast } = useOperationalSnapshot();

  const handleToggleCollapse = () => {
    setIsSidebarCollapsed(prev => {
      const next = !prev;
      try {
        localStorage.setItem('polaris_sidebar_collapsed', String(next));
      } catch {}
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex font-sans antialiased selection:bg-sky-100 selection:text-sky-900">
      {/* 1. Desktop & Mobile Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        onSelectTab={setActiveTab}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={handleToggleCollapse}
      />

      {/* 2. Main Content Container */}
      <div 
        className={`flex-1 flex flex-col min-w-0 transition-all duration-200 ${
          isSidebarCollapsed ? 'md:pl-16' : 'md:pl-60'
        }`}
      >
        {/* Top Application Bar */}
        <TopBar 
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
          onNavigateToPolicy={() => setActiveTab('policy')}
        />

        {/* Contextual Alert Ribbon (rendered only when active threats exist) */}
        {activeThreats && activeThreats.length > 0 && (
          <AlertRibbon 
            threats={activeThreats} 
            onNavigateToPolicy={() => setActiveTab('policy')} 
          />
        )}

        {/* Primary Operational Stage */}
        <main className="flex-1 w-full p-4 sm:p-6 lg:p-8 pb-20 md:pb-8">
          {activeTab === 'overview' && <OverviewView onNavigate={(tab) => setActiveTab(tab as TabType)} />}
          {activeTab === 'twin' && <EnergyTwinView />}
          {activeTab === 'forecast' && <ForecastView />}
          {activeTab === 'scenarios' && <ScenariosView onNavigate={(tab) => setActiveTab(tab as TabType)} />}
          {activeTab === 'optimization' && <OptimizationView />}
          {activeTab === 'resilience' && <ResilienceView />}
          {activeTab === 'policy' && <PolicyView />}
          {activeTab === 'trace' && <DecisionTraceView />}
          {activeTab === 'edge' && <EdgeView />}
          {activeTab === 'validation' && <ValidationView />}
          {activeTab === 'field_hil' && <FieldHILValidationView />}
          {activeTab === 'design_lab' && <DesignLabView />}
        </main>

        {/* Minimal Unobtrusive Status Footer */}
        <footer className="border-t border-slate-200 bg-white text-slate-500 text-xs py-3 px-4 sm:px-8 mt-auto hidden md:block">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] font-mono">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
              <span className="text-slate-800 font-medium">POLARIS EMS</span>
              <span className="text-slate-300">|</span>
              <span className="text-slate-500">Autonomous Polar Microgrid Optimization</span>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1 text-slate-600">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>6 Provenance Tiers Enforced</span>
              </div>
              <span className="text-slate-200">|</span>
              <div className="flex items-center space-x-1 text-slate-500">
                <WifiOff className="w-3.5 h-3.5 text-slate-400" />
                <span>Computational Twin • Physical SCADA Disconnected</span>
              </div>
            </div>
          </div>
        </footer>

        {/* Mobile Bottom Navigation */}
        <MobileNav activeTab={activeTab} onSelectTab={setActiveTab} />
      </div>

      {/* Global Drawers & Modals */}
      <EvidenceDrawer />
      <QuickOrientationModal isOpen={isOrientationOpen} onClose={closeOrientation} />

      {/* Floating Industrial Toast Notification */}
      {toast && (
        <div
          role="alert"
          aria-live="assertive"
          className={`fixed bottom-6 right-6 z-50 max-w-sm w-full shadow-2xl rounded-xl border overflow-hidden transition-all duration-300 ${
            toast.type === 'success'
              ? 'bg-emerald-950 border-emerald-600/50 text-emerald-50'
              : toast.type === 'warning'
              ? 'bg-amber-950 border-amber-600/50 text-amber-50'
              : 'bg-slate-900 border-slate-700 text-slate-100'
          }`}
        >
          <div className="px-4 py-3 flex items-start gap-3">
            <div className={`mt-0.5 w-2 h-2 rounded-full shrink-0 ${
              toast.type === 'success' ? 'bg-emerald-400' : toast.type === 'warning' ? 'bg-amber-400' : 'bg-sky-400'
            }`} />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-mono font-bold uppercase tracking-wide">{toast.title}</p>
              <p className="text-xs mt-0.5 opacity-80 leading-relaxed">{toast.message}</p>
            </div>
            <button
              onClick={dismissToast}
              className="shrink-0 text-current opacity-50 hover:opacity-100 text-lg leading-none"
              aria-label="Dismiss notification"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <StationProvider>
      <EvidenceProvider>
        <ComprehensionProvider>
          <AppContent />
        </ComprehensionProvider>
      </EvidenceProvider>
    </StationProvider>
  );
};

export default App;
