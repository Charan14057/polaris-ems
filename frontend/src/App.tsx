import React, { useState } from 'react';
import { StationProvider, useStation } from './context/StationContext';
import { Header } from './components/layout/Header';
import { Navbar, TabType } from './components/layout/Navbar';
import { AlertRibbon } from './components/layout/AlertRibbon';
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
import { OperatorApprovalBanner } from './components/common/OperatorApprovalBanner';
import { ShieldAlert, Server, Info } from 'lucide-react';

const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const { stationId, stationDetail, activeThreats } = useStation();

  return (
    <div className="min-h-screen bg-polar-950 text-polar-100 flex flex-col font-sans selection:bg-cyan-500/20 selection:text-cyan-300">
      {/* Global Header */}
      <Header />

      {/* Primary Navigation */}
      <Navbar activeTab={activeTab} onSelectTab={setActiveTab} />

      {/* Active Threat / Policy Ribbon */}
      <AlertRibbon threats={activeThreats} onNavigateToPolicy={() => setActiveTab('policy')} />

      {/* Operator Dispatch Approval Boundary (Workstream G) */}
      <OperatorApprovalBanner
        onNavigateToOptimization={() => setActiveTab('optimization')}
        onNavigateToTwin={() => setActiveTab('twin')}
      />

      {/* Main Operational Stage */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6">
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
      </main>

      {/* Polar Station Telemetry & Compliance Footer */}
      <footer className="border-t border-polar-800 bg-polar-900/60 backdrop-blur text-polar-500 text-xs py-5 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
            </span>
            <span className="font-mono text-polar-400 font-semibold tracking-wider">
              POLARIS-EMS // POLAR MISSION CONTROL
            </span>
            <span className="text-polar-700">|</span>
            <span>Station ID: <strong className="text-polar-300">{stationId}</strong></span>
            {stationDetail && (
              <>
                <span className="text-polar-700">|</span>
                <span>Type: <strong className="text-polar-300">{stationDetail.classification}</strong></span>
                <span className="text-polar-700">|</span>
                <span>Bus: <strong className="text-polar-300 font-mono">{stationDetail.electrical.nominal_voltage_v}V @ {stationDetail.electrical.grid_frequency_hz}Hz</strong></span>
              </>
            )}
          </div>

          <div className="flex items-center space-x-4 text-polar-400">
            <div className="flex items-center space-x-1" title="Phase 9 FastAPI Boundary">
              <Server className="w-3.5 h-3.5 text-cyan-400" />
              <span>FastAPI Gateway: <span className="font-mono text-cyan-300">:8000</span></span>
            </div>
            <span className="text-polar-700">|</span>
            <div className="flex items-center space-x-1" title="Read-only Twin Protocol">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              <span>Advisory Telemetry Only</span>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-2.5 pt-2 border-t border-polar-800/40 text-[11px] text-polar-600 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <Info className="w-3 h-3 text-polar-500" />
            <span>
              All power values, forecasts, optimization dispatches, and policy directives are snapshot-evaluated by frozen server-side physical and mathematical engines.
            </span>
          </div>
          <div className="font-mono tracking-tight text-polar-400">
            DATA CLASSIFICATION: SNAPSHOT TELEMETRY • STATION SPEC • PHYSICAL DIGITAL TWIN
          </div>
        </div>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <StationProvider>
      <AppContent />
    </StationProvider>
  );
};

export default App;
