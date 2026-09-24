import React, { useState, useEffect, useCallback } from 'react';
import { useStation } from '../context/StationContext';
import { api } from '../api/endpoints';
import { 
  ResilienceEvaluateResponseData, 
  PolicyEvaluateResponseData 
} from '../api/types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { MetricCard } from '../components/common/MetricCard';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorCard } from '../components/common/ErrorCard';
import { 
  ShieldCheck, 
  ShieldAlert, 
  Zap, 
  BatteryCharging, 
  Fuel, 
  Thermometer, 
  Activity, 
  Clock, 
  Compass, 
  AlertTriangle,
  ArrowRight
} from 'lucide-react';

interface OverviewViewProps {
  onNavigate?: (tab: any) => void;
  onNavigateTab?: (tab: any) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate, onNavigateTab }) => {
  const navigate = onNavigate || onNavigateTab || (() => {});
  const { currentStation, horizonHours, stationDetail } = useStation();

  const [resilience, setResilience] = useState<ResilienceEvaluateResponseData | null>(null);
  const [policy, setPolicy] = useState<PolicyEvaluateResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [resRes, polRes] = await Promise.all([
        api.evaluateResilience({
          station_id: currentStation,
          horizon_hours: horizonHours,
        }),
        api.evaluatePolicy({
          station_id: currentStation,
          horizon_hours: horizonHours,
          include_suppressed: true,
        }),
      ]);

      if (resRes.data) setResilience(resRes.data);
      if (polRes.data) setPolicy(polRes.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch operational overview data.');
    } finally {
      setLoading(false);
    }
  }, [currentStation, horizonHours]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        <LoadingSkeleton height="h-44" rows={1} />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <LoadingSkeleton height="h-32" rows={4} />
        </div>
      </div>
    );
  }

  if (error || !resilience || !stationDetail) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <ErrorCard 
          title="Operational Overview Error" 
          message={error || 'Station telemetry snapshot unavailable'} 
          onRetry={loadData} 
        />
      </div>
    );
  }

  const surv = resilience.survival_horizons;
  const dims = resilience.dimensions;
  const isEmergency = resilience.resilience_state === 'CRITICAL' || resilience.resilience_state === 'THREATENED';

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">
      {/* 1. Hero Operational State Banner */}
      <div className={`p-6 rounded-xl border relative overflow-hidden transition-all ${
        isEmergency 
          ? 'bg-gradient-to-r from-red-950/40 via-polar-900/90 to-polar-950/80 border-red-500/40 shadow-xl shadow-red-950/20' 
          : 'bg-gradient-to-r from-polar-900/90 via-polar-900/80 to-polar-950/80 border-polar-750/70 shadow-lg'
      }`}>
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs uppercase tracking-wider text-polar-400">
                {stationDetail.classification}
              </span>
              <span className="text-polar-600">•</span>
              <span className="font-mono text-xs text-polar-300">
                {stationDetail.location} ({stationDetail.latitude.toFixed(2)}°, {stationDetail.longitude.toFixed(2)}°)
              </span>
              <ProvenanceTag provenance={stationDetail.provenance} size="xs" />
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-3xl font-extrabold text-polar-50 tracking-tight font-mono">
                {stationDetail.name}
              </h2>
              <StatusBadge status={resilience.resilience_state} size="lg" />
              {policy && (
                <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-polar-800/80 border border-polar-700 text-xs font-mono">
                  <span className="text-polar-400">Policy:</span>
                  <span className="text-cyan-300 font-semibold">{policy.primary_directive}</span>
                </div>
              )}
            </div>

            <p className="text-sm text-polar-300 max-w-2xl leading-relaxed">
              Operational resilience evaluated across a <strong className="text-polar-100 font-mono">{horizonHours}h</strong> horizon.
              {surv.survives_full_horizon ? (
                <span className="text-emerald-400 ml-1.5 font-medium">Station survives the entire evaluated horizon without shortfall.</span>
              ) : (
                <span className="text-amber-400 ml-1.5 font-medium">Critical deficit projected at {surv.overall_station_survival_horizon_h}h bound by {surv.binding_subsystem}.</span>
              )}
            </p>
          </div>

          {/* Quick Survival Gauge Tile */}
          <div className="flex items-center gap-4 bg-polar-950/70 border border-polar-800 p-4 rounded-xl shrink-0">
            <div className="text-center px-2">
              <div className="text-[10px] font-mono text-polar-400 uppercase tracking-wider">
                Overall Survival
              </div>
              <div className="text-3xl font-extrabold font-mono-numbers text-polar-50 mt-1">
                {surv.overall_station_survival_horizon_h.toFixed(1)}
                <span className="text-sm font-normal text-polar-400 ml-1">h</span>
              </div>
              <div className="mt-1">
                <StatusBadge 
                  status={surv.survives_full_horizon ? 'SAFE' : 'THREATENED'} 
                  size="sm" 
                  showIcon={false} 
                />
              </div>
            </div>

            <div className="h-12 w-px bg-polar-800" />

            <div className="space-y-1 text-xs font-mono">
              <div className="text-polar-400">Binding Subsystem:</div>
              <div className="font-semibold text-cyan-300 uppercase tracking-wide">
                {surv.binding_subsystem}
              </div>
              <div className="text-[10px] text-polar-500 pt-1">
                Snapshot: {resilience.assessment_timestamp?.split('T')[1]?.substring(0, 5) || '12:00'} UTC
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Subsystem Telemetry KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Diesel / Generation Capacity */}
        <MetricCard
          title="Diesel Fleet"
          value={stationDetail.electrical.total_diesel_capacity_kw}
          unit="kW Rated"
          subtitle={`${stationDetail.electrical.diesel_generator_count} × ${stationDetail.electrical.diesel_generator_kw_rated} kW units`}
          icon={<Zap className="w-4 h-4 text-orange-400" />}
          provenance="CONFIGURED"
          statusBadge={<StatusBadge status="SAFE" size="sm" />}
        />

        {/* Battery Storage */}
        <MetricCard
          title="BESS Storage"
          value={stationDetail.electrical.battery_capacity_kwh}
          unit="kWh Nameplate"
          subtitle={`Usable SOC: ${(stationDetail.electrical.battery_min_soc * 100).toFixed(0)}% – ${(stationDetail.electrical.battery_max_soc * 100).toFixed(0)}%`}
          icon={<BatteryCharging className="w-4 h-4 text-emerald-400" />}
          provenance="CONFIGURED"
          statusBadge={<StatusBadge status="SAFE" size="sm" />}
        />

        {/* Fuel Inventory */}
        <MetricCard
          title="Fuel Inventory"
          value={stationDetail.fuel.initial_fuel_liters.toLocaleString()}
          unit="Liters"
          subtitle={`Critical reserve: ${stationDetail.fuel.critical_fuel_reserve_liters.toLocaleString()} L`}
          icon={<Fuel className="w-4 h-4 text-slate-400" />}
          provenance="CONFIGURED"
          statusBadge={<StatusBadge status="SAFE" size="sm" />}
        />

        {/* Thermal Habitability */}
        <MetricCard
          title="Indoor Thermal Safe"
          value={stationDetail.thermal.indoor_min_safe_temp_c}
          unit="°C Safe Min"
          subtitle={`Target: ${stationDetail.thermal.indoor_target_temp_c}°C`}
          icon={<Thermometer className="w-4 h-4 text-pink-400" />}
          provenance="CONFIGURED"
          statusBadge={<StatusBadge status="SAFE" size="sm" />}
        />
      </div>

      {/* 3. Operational Resilience & Dimensions Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: 9-Dimension Health Overview */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
                Station Resilience Health Index
              </h3>
            </div>
            <div className="flex items-center space-x-2">
              <ProvenanceTag provenance={resilience.provenance} size="xs" />
              <button
                onClick={() => navigate('resilience')}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center space-x-1"
              >
                <span>Full Audit</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {dims ? (
            <div className="space-y-4">
              <div className="flex items-baseline justify-between p-3 bg-polar-950/60 rounded-lg border border-polar-800">
                <span className="text-xs text-polar-300">Composite Engineering Index:</span>
                <div className="flex items-baseline space-x-2">
                  <span className="text-2xl font-bold font-mono-numbers text-cyan-400">
                    {dims.composite_resilience_index.toFixed(1)}
                  </span>
                  <span className="text-xs font-mono text-polar-400">/ 100</span>
                </div>
              </div>

              {/* Subsystem Survival Horizons Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                <div className="p-2.5 rounded bg-polar-950/40 border border-polar-800/80">
                  <div className="text-[10px] text-polar-400 uppercase">Critical Load</div>
                  <div className="text-base font-bold font-mono-numbers text-polar-100 mt-1">
                    {surv.critical_load_survival_horizon_h.toFixed(1)}h
                  </div>
                </div>
                <div className="p-2.5 rounded bg-polar-950/40 border border-polar-800/80">
                  <div className="text-[10px] text-polar-400 uppercase">Thermal Margin</div>
                  <div className="text-base font-bold font-mono-numbers text-polar-100 mt-1">
                    {surv.thermal_habitability_horizon_h.toFixed(1)}h
                  </div>
                </div>
                <div className="p-2.5 rounded bg-polar-950/40 border border-polar-800/80">
                  <div className="text-[10px] text-polar-400 uppercase">Battery Reserve</div>
                  <div className="text-base font-bold font-mono-numbers text-polar-100 mt-1">
                    {surv.battery_endurance_horizon_h.toFixed(1)}h
                  </div>
                </div>
                <div className="p-2.5 rounded bg-polar-950/40 border border-polar-800/80">
                  <div className="text-[10px] text-polar-400 uppercase">Fuel Endurance</div>
                  <div className="text-base font-bold font-mono-numbers text-polar-100 mt-1">
                    {surv.fuel_endurance_horizon_h.toFixed(1)}h
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-polar-400">Resilience dimensions unassessed.</p>
          )}
        </div>

        {/* Right Column: Active Threats & Alerts */}
        <div className="p-5 rounded-xl bg-polar-900/60 border border-polar-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-polar-200">
                Threat Breakdown
              </h3>
            </div>
            <span className="text-xs font-mono text-polar-400">
              {resilience.threat_decomposition.length} Active
            </span>
          </div>

          <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
            {resilience.threat_decomposition.length === 0 ? (
              <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-center text-xs text-emerald-300">
                ✓ No critical operational threats detected. Station operates within nominal margins.
              </div>
            ) : (
              resilience.threat_decomposition.map((threat, idx) => (
                <div 
                  key={idx} 
                  className="p-3 rounded-lg bg-polar-950/80 border border-polar-800 text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-polar-200 uppercase font-mono">
                      {threat.threat_type.replace(/_/g, ' ')}
                    </span>
                    <StatusBadge status={threat.severity} size="sm" showIcon={false} />
                  </div>
                  <p className="text-polar-300 text-[11px] leading-relaxed">
                    {threat.trigger_condition}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
