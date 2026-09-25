import React, { useState, useEffect, useRef } from 'react';
import { useStation } from '../../context/StationContext';
import { StationId } from '../../api/types';
import { useComprehension } from '../../context/ComprehensionContext';
import { 
  Menu, 
  RotateCw, 
  Clock, 
  HelpCircle, 
  ShieldCheck, 
  AlertTriangle,
  ChevronDown,
  Info,
  Radio,
  Sliders
} from 'lucide-react';

interface TopBarProps {
  onOpenMobileMenu: () => void;
  onNavigateToPolicy?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onOpenMobileMenu, onNavigateToPolicy }) => {
  const { 
    currentStation, 
    setStation, 
    horizonHours, 
    setHorizonHours, 
    loading, 
    refreshStationData,
    activeThreats
  } = useStation();

  const { openOrientation } = useComprehension();

  const [utcTime, setUtcTime] = useState<string>('');
  const [showEnvInfo, setShowEnvInfo] = useState<boolean>(false);
  const [showAlertsMenu, setShowAlertsMenu] = useState<boolean>(false);
  const envInfoRef = useRef<HTMLDivElement>(null);
  const alertsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const hours = String(now.getUTCHours()).padStart(2, '0');
      const mins = String(now.getUTCMinutes()).padStart(2, '0');
      setUtcTime(`${hours}:${mins} UTC`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Close popovers on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (envInfoRef.current && !envInfoRef.current.contains(e.target as Node)) {
        setShowEnvInfo(false);
      }
      if (alertsRef.current && !alertsRef.current.contains(e.target as Node)) {
        setShowAlertsMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const stations: { id: StationId; label: string; location: string }[] = [
    { id: 'BHARATI', label: 'Bharati', location: '69°S Antarctica' },
    { id: 'MAITRI', label: 'Maitri', location: '70°S Antarctica' },
    { id: 'HIMADRI', label: 'Himadri', location: '79°N Svalbard' },
  ];

  const hasCritical = activeThreats.some(t => t.severity === 'CRITICAL');
  const alertCount = activeThreats.length;

  return (
    <header className="h-14 bg-white border-b border-slate-200 sticky top-0 z-30 px-3 sm:px-6 flex items-center justify-between gap-3 shadow-xs">
      {/* Left: Mobile hamburger & Station branding */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileMenu}
          className="md:hidden flex items-center justify-center w-8 h-8 rounded-md text-slate-600 hover:bg-slate-100"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2">
          <span className="font-semibold text-slate-900 text-sm tracking-tight">Polaris EMS</span>
          <span className="text-slate-300">/</span>
          <span className="text-xs text-slate-500 font-normal">Polar Energy Management</span>
        </div>
      </div>

      {/* Center & Right: Controls and Status */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Station Selector Dropdown */}
        <div className="relative">
          <label htmlFor="station-select" className="sr-only">Select Station</label>
          <select
            id="station-select"
            value={currentStation}
            onChange={(e) => setStation(e.target.value as StationId)}
            className="text-xs font-medium text-slate-800 bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 hover:bg-slate-100 focus:ring-1 focus:ring-sky-500 focus:outline-none transition-colors cursor-pointer"
          >
            {stations.map(st => (
              <option key={st.id} value={st.id}>
                {st.label} ({st.location})
              </option>
            ))}
          </select>
        </div>

        {/* Horizon Selector */}
        <div className="hidden lg:flex items-center bg-slate-50 border border-slate-200 rounded-md p-0.5 text-xs">
          <button
            onClick={() => setHorizonHours(48)}
            className={`px-2 py-1 rounded font-medium transition-colors ${horizonHours === 48 ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-500 hover:text-slate-900'}`}
          >
            48h
          </button>
          <button
            onClick={() => setHorizonHours(168)}
            className={`px-2 py-1 rounded font-medium transition-colors ${horizonHours === 168 ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-500 hover:text-slate-900'}`}
          >
            168h
          </button>
        </div>

        {/* Environment Status Pill with Popover */}
        <div className="relative" ref={envInfoRef}>
          <button
            onClick={() => setShowEnvInfo(!showEnvInfo)}
            className="flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-mono font-medium bg-slate-100 hover:bg-slate-200/80 text-slate-700 border border-slate-200 transition-colors"
            title="Environment & Physical Boundary Status"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-sky-500" />
            <span className="hidden sm:inline">SIMULATION</span>
            <Info className="w-3 h-3 text-slate-400" />
          </button>

          {showEnvInfo && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-lg shadow-lg p-3.5 z-50 text-xs text-slate-600 space-y-2">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <span className="font-semibold text-slate-900 text-xs flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  Operational Boundary
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                  Air-Gapped
                </span>
              </div>
              <p className="leading-relaxed">
                Operating in simulation mode. Software models forward station physics and optimizes dispatch plans.
              </p>
              <div className="p-2 bg-slate-50 rounded border border-slate-100 text-[11px] font-mono text-slate-500 space-y-1">
                <div>SCADA Link: <span className="text-slate-700 font-semibold">Disconnected</span></div>
                <div>Actuation: <span className="text-slate-700 font-semibold">Operator Auth Required</span></div>
                <div>Provenance: <span className="text-slate-700 font-semibold">6 Locked Tiers</span></div>
              </div>
            </div>
          )}
        </div>

        {/* System Condition / Alerts Pill */}
        <div className="relative" ref={alertsRef}>
          <button
            onClick={() => setShowAlertsMenu(!showAlertsMenu)}
            className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium border transition-colors ${
              hasCritical 
                ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100' 
                : alertCount > 0 
                  ? 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
            }`}
          >
            {alertCount > 0 ? (
              <>
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>{alertCount} {alertCount === 1 ? 'Alert' : 'Alerts'}</span>
              </>
            ) : (
              <>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span className="hidden md:inline">Normal</span>
              </>
            )}
          </button>

          {showAlertsMenu && alertCount > 0 && (
            <div className="absolute right-0 mt-2 w-84 bg-white border border-slate-200 rounded-lg shadow-lg p-3 z-50 text-xs">
              <div className="font-semibold text-slate-900 pb-2 border-b border-slate-100 flex items-center justify-between">
                <span>Active System Conditions</span>
                <span className="text-[10px] font-mono text-slate-400">{alertCount} flagged</span>
              </div>
              <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto mt-1">
                {activeThreats.map((threat, idx) => (
                  <div key={idx} className="py-2 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-900 text-xs">{threat.threat_type.replace(/_/g, ' ')}</span>
                      <span className={`text-[9px] font-mono px-1 rounded ${threat.severity === 'CRITICAL' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}`}>
                        {threat.severity}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500">{threat.trigger_condition}</p>
                  </div>
                ))}
              </div>
              {onNavigateToPolicy && (
                <button
                  onClick={() => {
                    setShowAlertsMenu(false);
                    onNavigateToPolicy();
                  }}
                  className="w-full mt-2 text-center text-[11px] text-sky-600 hover:text-sky-800 font-medium pt-2 border-t border-slate-100"
                >
                  View Policy Dispatch Rules →
                </button>
              )}
            </div>
          )}
        </div>

        {/* UTC Clock */}
        <div className="hidden xl:flex items-center gap-1.5 text-xs font-mono text-slate-500 px-2 py-1 bg-slate-50 rounded border border-slate-200">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{utcTime}</span>
        </div>

        {/* Refresh Action */}
        <button
          onClick={refreshStationData}
          disabled={loading}
          className="p-1.5 rounded-md text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          title="Refresh Station Telemetry"
          aria-label="Refresh Station Telemetry"
        >
          <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-600' : ''}`} />
        </button>

        {/* Quick Orientation / Help Button */}
        <button
          onClick={openOrientation}
          className="p-1.5 rounded-md text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          title="System Overview & Orientation"
          aria-label="System Overview & Orientation"
        >
          <HelpCircle className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
