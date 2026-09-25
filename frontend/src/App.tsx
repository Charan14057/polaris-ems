import React, { useState } from 'react';
import { StationProvider, useStation } from './context/StationContext';
import { EvidenceProvider } from './context/EvidenceContext';
import { ComprehensionProvider, useComprehension } from './context/ComprehensionContext';
import { QuickOrientationModal } from './components/common/QuickOrientationModal';
import { Header } from './components/layout/Header';
import { GlobalStatusBar } from './components/layout/GlobalStatusBar';
import { Navbar, TabType } from './components/layout/Navbar';
import { AlertRibbon } from './components/layout/AlertRibbon';
import { OperatorApprovalBanner } from './components/common/OperatorApprovalBanner';
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
import { ShieldCheck, WifiOff, FileCheck } from 'lucide-react';

const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const { activeThreats } = useStation();
  const { isOrientationOpen, closeOrientation } = useComprehension();

  return (
    <div className="min-h-screen bg-canvas text-ink-primary flex flex-col font-sans selection:bg-copper-soft selection:text-copper-dark">
      {/* 1. Global Header & Masthead */}
      <Header />

      {/* 2. Calm Global Status Orientation Strip */}
      <GlobalStatusBar />

      {/* 3. Primary Mission-Control Navigation Index */}
      <Navbar activeTab={activeTab} onSelectTab={setActiveTab} />

      {/* 4. Active Threat / Policy Alert Ribbon */}
      <AlertRibbon threats={activeThreats} onNavigateToPolicy={() => setActiveTab('policy')} />

      {/* 5. Operator Supervisory Boundary Banner */}
      <OperatorApprovalBanner
        onNavigateToOptimization={() => setActiveTab('optimization')}
        onNavigateToTwin={() => setActiveTab('twin')}
      />

      {/* 6. Scientific Evidence & Provenance Inspection Drawer */}
      <EvidenceDrawer />

      {/* 6.1 Non-Technical Visitor 60-Second Orientation Modal */}
      <QuickOrientationModal isOpen={isOrientationOpen} onClose={closeOrientation} />

      {/* 7. Main Operational Stage */}
      <main className="flex-1 max-w-[1520px] mx-auto w-full px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && <OverviewView onNavigate={setActiveTab} />}
        {activeTab === 'twin' && <EnergyTwinView />}
        {activeTab === 'forecast' && <ForecastView />}
        {activeTab === 'scenarios' && <ScenariosView />}
        {activeTab === 'optimization' && <OptimizationView />}
        {activeTab === 'resilience' && <ResilienceView />}
        {activeTab === 'policy' && <PolicyView />}
        {activeTab === 'trace' && <DecisionTraceView />}
        {activeTab === 'edge' && <EdgeView />}
        {activeTab === 'validation' && <ValidationView />}
        {activeTab === 'field_hil' && <FieldHILValidationView />}
        {activeTab === 'design_lab' && <DesignLabView />}
      </main>

      {/* 8. Mission Control & Epistemic Boundary Footer */}
      <footer className="border-t border-border bg-canvas-subtle text-ink-muted text-xs py-5 mt-auto">
        <div className="max-w-[1520px] mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono">
          <div className="flex items-center space-x-3">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-copper opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-copper"></span>
            </span>
            <span className="text-ink-secondary font-medium">
              POLARIS-EMS • MISSION CONTROL CORE
            </span>
            <span className="text-border">|</span>
            <span className="text-ink-muted">SIH26061</span>
          </div>

          <div className="flex items-center space-x-4 text-[11px]">
            <div className="flex items-center space-x-1 text-teal">
              <FileCheck className="w-3.5 h-3.5" />
              <span>PROVENANCE: 6 LOCKED TIERS</span>
            </div>
            <span className="text-border">|</span>
            <div className="flex items-center space-x-1 text-copper font-medium">
              <WifiOff className="w-3.5 h-3.5" />
              <span>SCADA: SIMULATION ONLY (ZERO PHYSICAL TELEMETRY)</span>
            </div>
          </div>
        </div>
      </footer>
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
