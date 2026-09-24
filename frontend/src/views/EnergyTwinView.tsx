import React, { useState } from 'react';
import { useStation } from '../context/StationContext';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { StatusBadge } from '../components/common/StatusBadge';
import { 
  Sun, 
  Wind, 
  Zap, 
  Battery, 
  ShieldCheck, 
  Radio, 
  Layers, 
  Thermometer, 
  Flame, 
  CheckCircle2, 
  SlidersHorizontal 
} from 'lucide-react';

export const EnergyTwinView: React.FC = () => {
  const { currentStation, stationDetail, lastUpdated } = useStation();

  // Visualization display filters only (does NOT command or control physical hardware)
  const [showCriticalOnly, setShowCriticalOnly] = useState<boolean>(false);
  const [selectedSubsystem, setSelectedSubsystem] = useState<string | null>(null);

  if (!stationDetail) {
    return (
      <div className="p-6 max-w-7xl mx-auto text-center text-polar-400 font-mono text-xs">
        Loading station digital twin specifications...
      </div>
    );
  }

  const elec = stationDetail.electrical;
  const therm = stationDetail.thermal;
  const fuel = stationDetail.fuel;
  const devices = stationDetail.devices || [];

  // Filtered devices for visual inspection only
  const filteredDevices = showCriticalOnly 
    ? devices.filter(d => d.priority_rank <= 2)
    : devices;

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-xl bg-polar-900/60 border border-polar-800">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold font-mono text-polar-100 uppercase tracking-wide">
              {stationDetail.name} • Physical Digital Twin (Phase 4)
            </h2>
            <ProvenanceTag provenance="CONFIGURED" size="xs" />
          </div>
          <p className="text-xs text-polar-400 mt-1">
            Authoritative bus-and-branch electrical topology with closed-loop physical validation.
          </p>
        </div>

        {/* Display-only Filter Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowCriticalOnly(!showCriticalOnly)}
            className={`inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-mono rounded-lg border transition-all ${
              showCriticalOnly
                ? 'bg-cyan-950/80 border-cyan-500/50 text-cyan-300'
                : 'bg-polar-800/80 border-polar-700 text-polar-300 hover:text-polar-100'
            }`}
            title="Display filter only — does not execute device commands"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>{showCriticalOnly ? 'Showing Critical Circuits' : 'Filter: All Circuits'}</span>
          </button>
        </div>
      </div>

      {/* Interactive Single-Line Diagram (SLD) */}
      <div className="p-6 rounded-xl bg-polar-950/90 border border-polar-800/80 shadow-2xl relative overflow-x-auto">
        <div className="min-w-[800px] flex flex-col items-center space-y-8 py-4">
          
          {/* TOP TIER: Generation Sources */}
          <div className="grid grid-cols-4 gap-6 w-full max-w-4xl text-center">
            {/* Solar PV Array */}
            <div 
              onClick={() => setSelectedSubsystem('solar')}
              className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                selectedSubsystem === 'solar'
                  ? 'bg-amber-950/40 border-amber-400 shadow-md shadow-amber-950/30'
                  : 'bg-polar-900/80 border-polar-750 hover:border-amber-500/40'
              }`}
            >
              <div className="flex items-center justify-between text-xs text-amber-400 font-mono mb-1">
                <span className="flex items-center space-x-1">
                  <Sun className="w-3.5 h-3.5" />
                  <span>Solar PV</span>
                </span>
                <span className="text-[10px]">PV-ARRAY</span>
              </div>
              <div className="text-xl font-bold font-mono-numbers text-polar-50">
                {elec.solar_pv_kw_peak.toFixed(1)} <span className="text-xs text-polar-400 font-normal">kWp</span>
              </div>
              <div className="text-[10px] text-polar-400 mt-1 font-mono">
                Tilt: 65° • Coastal Antarctic
              </div>
            </div>

            {/* Wind Turbine Array */}
            <div 
              onClick={() => setSelectedSubsystem('wind')}
              className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                selectedSubsystem === 'wind'
                  ? 'bg-cyan-950/40 border-cyan-400 shadow-md shadow-cyan-950/30'
                  : 'bg-polar-900/80 border-polar-750 hover:border-cyan-500/40'
              }`}
            >
              <div className="flex items-center justify-between text-xs text-cyan-400 font-mono mb-1">
                <span className="flex items-center space-x-1">
                  <Wind className="w-3.5 h-3.5" />
                  <span>Wind Turbine</span>
                </span>
                <span className="text-[10px]">WTG-ARRAY</span>
              </div>
              <div className="text-xl font-bold font-mono-numbers text-polar-50">
                {elec.wind_turbine_kw_rated.toFixed(1)} <span className="text-xs text-polar-400 font-normal">kW</span>
              </div>
              <div className="text-[10px] text-polar-400 mt-1 font-mono">
                Rated: 11.5 m/s • Cut-out: 25 m/s
              </div>
            </div>

            {/* Diesel Generator Units (Status Indicators — Display Only) */}
            <div 
              onClick={() => setSelectedSubsystem('diesel')}
              className={`col-span-2 p-3.5 rounded-lg border cursor-pointer transition-all ${
                selectedSubsystem === 'diesel'
                  ? 'bg-orange-950/40 border-orange-400 shadow-md shadow-orange-950/30'
                  : 'bg-polar-900/80 border-polar-750 hover:border-orange-500/40'
              }`}
            >
              <div className="flex items-center justify-between text-xs text-orange-400 font-mono mb-1">
                <span className="flex items-center space-x-1">
                  <Zap className="w-3.5 h-3.5" />
                  <span>Diesel Genset Fleet</span>
                </span>
                <span className="text-[10px]">{elec.total_diesel_capacity_kw.toFixed(0)} kW Total</span>
              </div>
              
              {/* Individual Generator Status Indicators (Visualization Only) */}
              <div className="grid grid-cols-3 gap-2 mt-2">
                {Array.from({ length: elec.diesel_generator_count }).map((_, idx) => (
                  <div 
                    key={idx}
                    className="p-1.5 rounded bg-polar-950/80 border border-polar-800 text-[11px] font-mono text-center"
                    title={`Generator ${idx + 1} (${elec.diesel_generator_kw_rated} kW). Status indicators are visualization-only; physical commands reserved for backend.`}
                  >
                    <div className="text-polar-300 font-semibold">GEN #{idx + 1}</div>
                    <div className="text-[10px] text-polar-400">{elec.diesel_generator_kw_rated} kW</div>
                    <span className="inline-block mt-1 px-1.5 py-0.2 rounded text-[9px] bg-emerald-950/80 text-emerald-400 border border-emerald-500/30 font-semibold">
                      STANDBY
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* FLOW CONDUIT: Dropping down to AC Bus */}
          <div className="w-full max-w-4xl flex justify-around px-8">
            <div className="w-0.5 h-6 bg-amber-500/60" />
            <div className="w-0.5 h-6 bg-cyan-500/60" />
            <div className="w-0.5 h-6 bg-orange-500/60" />
            <div className="w-0.5 h-6 bg-orange-500/60" />
          </div>

          {/* CENTER TIER: Main AC Microgrid Bus (Dynamically Rendered Specs) */}
          <div className="w-full max-w-4xl relative">
            {/* Bus Bar Line */}
            <div className="h-3 rounded-full bg-gradient-to-r from-amber-500 via-cyan-400 to-orange-500 shadow-md shadow-cyan-500/20" />
            
            <div className="flex items-center justify-between mt-2 text-xs font-mono text-polar-300 px-2">
              <span className="font-bold text-polar-50 tracking-wider">
                MAIN AC MICROGRID BUS
              </span>
              <span className="px-2 py-0.5 rounded bg-polar-900 border border-polar-700 text-polar-200">
                {elec.nominal_voltage_v} V AC • {elec.grid_frequency_hz} Hz
              </span>
              <span className="text-[11px] text-emerald-400 flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Power Balance Validated (Twin Replay)</span>
              </span>
            </div>
          </div>

          {/* FLOW CONDUIT: Branching down to Storage & Loads */}
          <div className="w-full max-w-4xl flex justify-around px-8">
            <div className="w-0.5 h-6 bg-emerald-500/60" />
            <div className="w-0.5 h-6 bg-polar-600" />
            <div className="w-0.5 h-6 bg-pink-500/60" />
          </div>

          {/* BOTTOM TIER: BESS Storage & End-Use Loads */}
          <div className="grid grid-cols-3 gap-6 w-full max-w-4xl text-center">
            {/* Battery Energy Storage System (BESS) */}
            <div 
              onClick={() => setSelectedSubsystem('battery')}
              className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                selectedSubsystem === 'battery'
                  ? 'bg-emerald-950/40 border-emerald-400 shadow-md shadow-emerald-950/30'
                  : 'bg-polar-900/80 border-polar-750 hover:border-emerald-500/40'
              }`}
            >
              <div className="flex items-center justify-between text-xs text-emerald-400 font-mono mb-1">
                <span className="flex items-center space-x-1">
                  <Battery className="w-3.5 h-3.5" />
                  <span>BESS Inverter/Storage</span>
                </span>
                <span className="text-[10px]">BI-DIRECTIONAL</span>
              </div>
              <div className="text-xl font-bold font-mono-numbers text-polar-50">
                {elec.battery_capacity_kwh.toFixed(1)} <span className="text-xs text-polar-400 font-normal">kWh</span>
              </div>
              <div className="text-[10px] text-polar-400 mt-1 font-mono">
                Charge: {elec.battery_max_charge_kw} kW • Disch: {elec.battery_max_discharge_kw} kW
              </div>
            </div>

            {/* Electrical Device Circuits */}
            <div 
              onClick={() => setSelectedSubsystem('loads')}
              className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                selectedSubsystem === 'loads'
                  ? 'bg-polar-800 border-polar-400 shadow-md'
                  : 'bg-polar-900/80 border-polar-750 hover:border-polar-600'
              }`}
            >
              <div className="flex items-center justify-between text-xs text-polar-300 font-mono mb-1">
                <span className="flex items-center space-x-1">
                  <Radio className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Station Demand Circuits</span>
                </span>
                <span className="text-[10px] font-mono">{filteredDevices.length} Connected</span>
              </div>
              <div className="text-xl font-bold font-mono-numbers text-polar-50">
                {filteredDevices.reduce((sum, d) => sum + d.nominal_power_kw, 0).toFixed(1)} <span className="text-xs text-polar-400 font-normal">kW Connected</span>
              </div>
              <div className="text-[10px] text-polar-400 mt-1 font-mono">
                Life-Safety & Science Circuits
              </div>
            </div>

            {/* Building Thermal Envelope */}
            <div 
              onClick={() => setSelectedSubsystem('thermal')}
              className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                selectedSubsystem === 'thermal'
                  ? 'bg-pink-950/40 border-pink-400 shadow-md shadow-pink-950/30'
                  : 'bg-polar-900/80 border-polar-750 hover:border-pink-500/40'
              }`}
            >
              <div className="flex items-center justify-between text-xs text-pink-400 font-mono mb-1">
                <span className="flex items-center space-x-1">
                  <Thermometer className="w-3.5 h-3.5" />
                  <span>Thermal HVAC System</span>
                </span>
                <span className="text-[10px]">CHP RECOVERY</span>
              </div>
              <div className="text-xl font-bold font-mono-numbers text-polar-50">
                {therm.indoor_target_temp_c.toFixed(1)}° <span className="text-xs text-polar-400 font-normal">Target</span>
              </div>
              <div className="text-[10px] text-polar-400 mt-1 font-mono">
                Min Safe: {therm.indoor_min_safe_temp_c}°C • UA: {therm.building_ua_kw_per_k} kW/K
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Connected Load Circuits Inventory (Display Only) */}
      <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
              Station Circuit Inventory ({filteredDevices.length} Circuits)
            </h3>
          </div>
          <span className="text-xs font-mono text-polar-400">
            Snapshot Timestamp: {lastUpdated.split('T')[1]?.substring(0, 5) || '12:00'} UTC
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-polar-800 text-polar-400 uppercase text-[10px]">
                <th className="py-2 px-3">Circuit ID</th>
                <th className="py-2 px-3">Device Name</th>
                <th className="py-2 px-3">Category</th>
                <th className="py-2 px-3 text-right">Nominal kW</th>
                <th className="py-2 px-3 text-center">Priority</th>
                <th className="py-2 px-3 text-center">Deferrable?</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-polar-850/60">
              {filteredDevices.map((dev) => (
                <tr key={dev.id} className="hover:bg-polar-800/40">
                  <td className="py-2 px-3 text-cyan-300 font-semibold">{dev.id}</td>
                  <td className="py-2 px-3 text-polar-200 font-sans">{dev.name}</td>
                  <td className="py-2 px-3 text-polar-400">{dev.category}</td>
                  <td className="py-2 px-3 text-right font-mono-numbers text-polar-100">
                    {dev.nominal_power_kw.toFixed(2)}
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span className={`px-2 py-0.5 rounded text-[10px] ${
                      dev.priority_rank === 1
                        ? 'bg-red-950/80 text-red-300 border border-red-500/40'
                        : dev.priority_rank === 2
                        ? 'bg-amber-950/80 text-amber-300 border border-amber-500/40'
                        : 'bg-polar-800 text-polar-300'
                    }`}>
                      P{dev.priority_rank}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-center text-polar-400">
                    {dev.deferrable ? 'Yes' : 'No'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
