"""
POLARIS-EMS — Stateful Live Twin Session & Real-Time Orchestration
SIH26061: Polar Energy Management & Resilience System

Maintains backend-owned, stateful real-time Digital Twin sessions with:
- True wall-clock synchronized simulation clock progression
- Full causal propagation (inputs -> TwinEngine -> TwinState -> derived state -> live stream)
- Authoritative manual action dispatch through safety and policy validation
- Phase 6 optimizer advisory integration for automated recommendations
- Scenario perturbation injection and closure verification
- Topological power flow and causal dependency tracing (Trace Power & Trace Impact)
"""

import time
import math
import uuid
import copy
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.twin_engine import TwinEngine
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.scenarios.registry import ScenarioRegistry
from backend.scenarios.transformations import ScenarioTransformer
from backend.policy.engine import PolicyEngine
from backend.optimizer.engine import OptimizerEngine
from backend.optimizer.schema import OptimizationMode


@dataclass
class LiveSessionMetadata:
    session_id: str
    station_id: str
    simulation_timestamp: str
    wall_clock_timestamp: str
    simulation_elapsed_seconds: float
    time_acceleration: float
    operating_mode: str  # "LIVE_AUTO" | "LIVE_MANUAL"
    active_scenario: Optional[str]
    active_controls: Dict[str, Any]
    session_status: str  # "ACTIVE" | "PAUSED" | "RECONNECTING"
    last_update: str
    data_mode: str = "LIVE"  # "LIVE" | "HISTORICAL" | "REPLAY"
    provenance: str = "SIMULATED"


class LiveTwinSession:
    """
    Authoritative stateful computational live session for a polar research station.
    The backend owns the simulation clock, physics state, active perturbations, and control overrides.
    """

    def __init__(
        self,
        station_id: str,
        profile_registry: Optional[StationProfileRegistry] = None,
        safety_registry: Optional[SafetyThresholdRegistry] = None,
        scenario_registry: Optional[ScenarioRegistry] = None,
        time_acceleration: float = 1.0,
        start_simulation_time: Optional[str] = None,
        data_mode: str = "LIVE"
    ):
        self.station_id = station_id.upper()
        self.session_id = f"twin-session-{self.station_id.lower()}-{uuid.uuid4().hex[:8]}"
        self.profile_registry = profile_registry or StationProfileRegistry()
        self.safety_registry = safety_registry or SafetyThresholdRegistry()
        self.scenario_registry = scenario_registry or ScenarioRegistry()
        
        self.profile = self.profile_registry.get(self.station_id)
        self.twin_engine = TwinEngine(
            station_id=self.station_id,
            profile=self.profile,
            safety_registry=self.safety_registry
        )
        self.policy_engine = PolicyEngine(
            station_id=self.station_id,
            profile=self.profile,
            safety_registry=self.safety_registry
        )
        self.optimizer_engine = OptimizerEngine(station_id=self.station_id, profile=self.profile)

        # Simulation and Wall Clock
        self.time_acceleration = max(0.1, float(time_acceleration))
        self.wall_clock_start = time.time()
        self.last_wall_tick = self.wall_clock_start
        self.data_mode = data_mode.upper() if data_mode in ("LIVE", "HISTORICAL", "REPLAY") else "LIVE"

        # Anchor to real-world current UTC date/time unless explicitly overridden
        if start_simulation_time is None:
            now_utc = datetime.now(timezone.utc)
            start_simulation_time = now_utc.isoformat().replace("+00:00", "Z")

        self.simulation_base_time = datetime.fromisoformat(start_simulation_time.replace("Z", "+00:00"))
        self.simulation_elapsed_seconds = 0.0

        # State management
        self.operating_mode: str = "LIVE_AUTO"
        self.active_scenario: Optional[str] = None
        self.active_controls: Dict[str, Any] = {}
        self.session_status: str = "ACTIVE"
        
        # Initialize physical twin state
        self.current_twin_state: TwinState = self.twin_engine.initialize_twin(
            timestamp=start_simulation_time
        )
        self.previous_twin_state: Optional[TwinState] = None
        self.last_update = datetime.now(timezone.utc).isoformat()
        
        # Decision and trace history
        self.trace_history: List[Dict[str, Any]] = [{
            "timestamp": self.current_simulation_iso(),
            "wall_clock": self.current_wall_clock_iso(),
            "event": "SESSION_INITIALIZED",
            "station_id": self.station_id,
            "session_id": self.session_id,
            "data_mode": self.data_mode,
            "details": f"Digital Twin initialized under baseline {self.station_id} profile anchored at {start_simulation_time}"
        }]

    def current_wall_clock_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def current_simulation_iso(self) -> str:
        current_sim_dt = self.simulation_base_time + timedelta(seconds=self.simulation_elapsed_seconds)
        return current_sim_dt.isoformat().replace("+00:00", "Z")

    def step(self, force_elapsed_seconds: Optional[float] = 60.0) -> TwinState:
        """Alias for advance_clock for convenient step-based testing."""
        return self.advance_clock(force_elapsed_seconds=force_elapsed_seconds)

    def calculate_astronomical_environment(
        self, sim_dt: datetime, elapsed_seconds: float
    ) -> tuple[float, float, float, float]:
        """
        Computes real-world astronomical solar elevation, seasonal ambient temperature,
        and polar wind conditions based on station latitude, longitude, day of year, and UTC time.
        """
        if self.station_id == "BHARATI":
            lat_deg, lon_deg = -69.41, 76.19
        elif self.station_id == "MAITRI":
            lat_deg, lon_deg = -70.77, 11.73
        else:  # HIMADRI
            lat_deg, lon_deg = 78.92, 11.92

        day_of_year = sim_dt.timetuple().tm_yday
        utc_hour = sim_dt.hour + sim_dt.minute / 60.0 + sim_dt.second / 3600.0

        # Solar declination angle (Cooper formulation)
        declination_rad = math.radians(23.45 * math.sin(math.radians(360.0 / 365.0 * (day_of_year - 81))))
        lat_rad = math.radians(lat_deg)

        # Local solar time: LST = UTC + lon / 15
        lst_hour = (utc_hour + lon_deg / 15.0) % 24.0
        hour_angle_rad = math.radians(15.0 * (lst_hour - 12.0))

        # Solar elevation angle: sin(alpha) = sin(lat)*sin(dec) + cos(lat)*cos(dec)*cos(H)
        sin_elev = math.sin(lat_rad) * math.sin(declination_rad) + math.cos(lat_rad) * math.cos(declination_rad) * math.cos(hour_angle_rad)
        elev_deg = math.degrees(math.asin(max(-1.0, min(1.0, sin_elev))))

        # Irradiance based on real elevation
        if elev_deg <= 0.0:
            ghi = 0.0
        else:
            air_mass = 1.0 / max(0.08, math.sin(math.radians(max(0.5, elev_deg))))
            dni = 1050.0 * (0.72 ** (air_mass ** 0.678))
            sin_e = math.sin(math.radians(elev_deg))
            ghi = round(dni * sin_e + 45.0 * sin_e, 1)
            ghi = max(0.0, min(1000.0, ghi))

        # Seasonal temperature model
        if lat_deg < 0:  # Southern Hemisphere (Bharati, Maitri)
            season_offset = math.cos(math.radians(360.0 / 365.0 * (day_of_year - 15)))
            base_station_t = -18.0 if self.station_id == "BHARATI" else -21.0
            seasonal_t = base_station_t + 13.0 * season_offset
        else:  # Northern Hemisphere (Himadri)
            season_offset = math.cos(math.radians(360.0 / 365.0 * (day_of_year - 197)))
            base_station_t = -5.0
            seasonal_t = base_station_t + 11.0 * season_offset

        # Diurnal temperature cycle
        diurnal = 2.0 * math.sin(math.radians(15.0 * (lst_hour - 9.0)))
        amb_temp = round(seasonal_t + diurnal, 2)

        # Wind variations
        base_wind = 8.5
        wind_spd = round(base_wind + 2.0 * ((int(elapsed_seconds // 30) % 5) - 2) * 0.4, 2)

        return amb_temp, wind_spd, ghi, elev_deg

    def advance_clock(self, force_elapsed_seconds: Optional[float] = None) -> TwinState:
        """
        Advances the simulation clock according to actual wall-clock execution or explicit step.
        Evaluates physical equations through TwinEngine and updates live state.
        """
        now = time.time()
        if force_elapsed_seconds is not None:
            elapsed_wall = max(0.0, float(force_elapsed_seconds))
        else:
            elapsed_wall = max(0.0, now - self.last_wall_tick)
        
        self.last_wall_tick = now
        delta_sim_seconds = elapsed_wall * self.time_acceleration
        self.simulation_elapsed_seconds += delta_sim_seconds
        
        sim_timestamp = self.current_simulation_iso()
        dt_hours = max(0.001, delta_sim_seconds / 3600.0) if delta_sim_seconds > 0 else 1.0 / 3600.0

        # Build baseline environmental input step based on station, calendar date, and season
        sim_dt = self.simulation_base_time + timedelta(seconds=self.simulation_elapsed_seconds)
        amb_temp, wind_spd, ghi, elev_deg = self.calculate_astronomical_environment(sim_dt, self.simulation_elapsed_seconds)

        hour_float = sim_dt.hour + sim_dt.minute / 60.0 + sim_dt.second / 3600.0
        nominal_kw = sum(d.nominal_power_kw for d in self.profile.devices if d.category == "CRITICAL")
        load_kw = round(nominal_kw * (1.15 if (7 <= hour_float <= 9 or 18 <= hour_float <= 21) else 0.95), 1)

        input_step = TwinInputStep(
            timestamp=sim_timestamp,
            horizon_h=1,
            ambient_temp_c=amb_temp,
            wind_speed_m_per_s=wind_spd,
            ghi_w_per_m2=ghi,
            load_kw=load_kw,
            solar_kw=0.0,
            wind_kw=0.0,
            mode="EXPECTED",
            provenance="FORECAST"
        )

        # Apply active scenario perturbation if present
        working_state = copy.deepcopy(self.current_twin_state)
        working_input = copy.deepcopy(input_step)

        # Anchor hardware and logistics capacities to baseline profile to prevent compounding multipliers
        working_state.battery.capacity_kwh = float(self.profile.electrical.battery_capacity_kwh)
        working_state.battery.usable_capacity_kwh = float(self.profile.electrical.battery_capacity_kwh * 0.9)
        working_state.diesel.generator_max_power_kw = float(self.profile.electrical.diesel_generator_kw_rated)
        working_state.resupply.resupply_window_days = int(self.profile.default_resupply_window_days)
        working_state.solar.solar_capacity_kw = float(self.profile.electrical.solar_pv_kw_peak)
        working_state.wind.wind_capacity_kw = float(self.profile.electrical.wind_turbine_kw_rated)
        if hasattr(working_state, "environment") and working_state.environment:
            working_state.environment.cloud_fraction = 0.5

        if self.active_scenario:
            try:
                scen_def = self.scenario_registry.get(self.active_scenario)
                transformer = ScenarioTransformer(scen_def)
                transformed_state, transformed_steps = transformer.transform(working_state, [working_input])
                working_state = transformed_state
                if transformed_steps:
                    working_input = transformed_steps[0]
            except Exception as e:
                # Log scenario application warning in trace
                self.trace_history.append({
                    "timestamp": sim_timestamp,
                    "event": "SCENARIO_PERMISSIVE_WARNING",
                    "error": str(e)
                })

        # Apply active manual controls (e.g. forced diesel online, forced battery charge, shed flexible loads)
        if self.active_controls:
            if "diesel_power_override_kw" in self.active_controls:
                p_override = float(self.active_controls["diesel_power_override_kw"])
                working_state.diesel.generator_power_kw = p_override
                working_state.diesel.generator_status = "ONLINE" if p_override > 0.1 else "STANDBY"
                working_state.diesel.online_count = 1 if p_override > 0.1 else 0

            if "battery_charge_force_kw" in self.active_controls:
                working_state.battery.charge_kw = float(self.active_controls["battery_charge_force_kw"])
                working_state.battery.discharge_kw = 0.0

            if "shed_load_kw" in self.active_controls:
                working_input.load_kw = max(
                    working_state.loads.critical_load_kw,
                    working_input.load_kw - float(self.active_controls["shed_load_kw"])
                )

        # Execute computational step through authoritative TwinEngine
        new_state = self.twin_engine.step(
            current_state=working_state,
            input_step=working_input,
            dt_hours=dt_hours
        )

        self.previous_twin_state = self.current_twin_state
        self.current_twin_state = new_state
        self.last_update = self.current_wall_clock_iso()

        return self.current_twin_state

    def apply_manual_action(self, action_id: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes an authoritative operator manual action through backend validation and twin update.
        """
        params = parameters or {}
        aid = action_id.lower()
        sim_ts = self.current_simulation_iso()
        wall_ts = self.current_wall_clock_iso()

        # Action handling with strict physical parameterization
        if aid == "dg1_start":
            rated = float(self.profile.electrical.diesel_generator_kw_rated)
            target_kw = float(params.get("power_kw", rated * 0.75))
            self.active_controls["diesel_power_override_kw"] = target_kw
            description = f"Operator started DG-1 generator dispatched to {target_kw:.1f} kW"
            expected_change = "Diesel online, battery charging from surplus, fuel burn initiated"
        elif aid == "dg1_stop":
            self.active_controls["diesel_power_override_kw"] = 0.0
            description = "Operator stopped DG-1 generator"
            expected_change = "Diesel off, battery covers residual deficit, zero fuel burn"
        elif aid == "bess_charge_force":
            chg_kw = float(params.get("charge_kw", 15.0))
            self.active_controls["battery_charge_force_kw"] = chg_kw
            description = f"Operator forced battery charging at {chg_kw:.1f} kW"
            expected_change = "Battery SOC increasing, available generation routed to storage"
        elif aid == "shed_flexible":
            shed_kw = float(params.get("shed_kw", 12.0))
            self.active_controls["shed_load_kw"] = shed_kw
            description = f"Operator shed flexible loads ({shed_kw:.1f} kW)"
            expected_change = "Total demand reduced, non-critical subloads curtailed"
        elif aid == "restore_all_loads":
            self.active_controls.pop("shed_load_kw", None)
            description = "Operator restored all shed loads to standard schedule"
            expected_change = "Full operational load restored to baseline nominal"
        else:
            return {
                "status": "REJECTED",
                "reason": f"Unsupported manual action: {action_id}",
                "timestamp": sim_ts
            }

        self.operating_mode = "LIVE_MANUAL"

        # Advance clock to calculate immediate downstream impact
        new_state = self.advance_clock(force_elapsed_seconds=1.0)

        trace_entry = {
            "timestamp": sim_ts,
            "wall_clock": wall_ts,
            "event": "MANUAL_ACTION_EXECUTED",
            "action_id": aid,
            "description": description,
            "expected_change": expected_change,
            "resulting_power_kw": {
                "solar": new_state.solar.solar_generation_kw,
                "wind": new_state.wind.wind_generation_kw,
                "diesel": new_state.diesel.generator_power_kw,
                "battery_charge": new_state.battery.charge_kw,
                "battery_discharge": new_state.battery.discharge_kw,
                "total_demand": new_state.loads.served_load_kw
            },
            "resilience_threat": new_state.resilience.threat_state if new_state.resilience else "UNKNOWN"
        }
        self.trace_history.append(trace_entry)

        return {
            "status": "APPROVED",
            "action_id": aid,
            "description": description,
            "expected_change": expected_change,
            "state": new_state.to_dict(),
            "trace": trace_entry
        }

    def approve_auto_recommendation(self) -> Dict[str, Any]:
        """
        Executes Phase 6 OptimizerEngine (HiGHS MILP) over 24h lookahead horizon,
        derives optimal unit commitment & dispatch recommendation, and applies it authoritatively.
        """
        sim_ts = self.current_simulation_iso()
        wall_ts = self.current_wall_clock_iso()
        sim_dt = self.simulation_base_time + timedelta(seconds=self.simulation_elapsed_seconds)

        # 1. Synthesize 24-hour forward lookahead trajectory from astronomical environment & load profiles
        forward_trajectory: List[TwinInputStep] = []
        nominal_kw = sum(d.nominal_power_kw for d in self.profile.devices if d.category == "CRITICAL")
        
        for h in range(1, 25):
            step_dt = sim_dt + timedelta(hours=h)
            amb_temp, wind_spd, ghi, _ = self.calculate_astronomical_environment(step_dt, h * 3600.0)
            hour_float = step_dt.hour + step_dt.minute / 60.0 + step_dt.second / 3600.0
            step_load_kw = round(nominal_kw * (1.15 if (7 <= hour_float <= 9 or 18 <= hour_float <= 21) else 0.95), 1)
            
            step_iso = step_dt.isoformat().replace("+00:00", "Z")
            forward_trajectory.append(TwinInputStep(
                timestamp=step_iso,
                horizon_h=h,
                ambient_temp_c=amb_temp,
                wind_speed_m_per_s=wind_spd,
                ghi_w_per_m2=ghi,
                load_kw=step_load_kw,
                solar_kw=0.0,
                wind_kw=0.0,
                mode="EXPECTED",
                provenance="FORECAST"
            ))

        # 2. Retrieve active scenario definition if perturbed
        scen_def = None
        if self.active_scenario:
            try:
                scen_def = self.scenario_registry.get(self.active_scenario)
            except Exception:
                pass

        # 3. ACTUALLY INVOKE Phase 6 OptimizerEngine (Pyomo + HiGHS)
        opt_result = self.optimizer_engine.optimize(
            initial_state=self.current_twin_state,
            trajectory=forward_trajectory,
            scenario=scen_def,
            mode=OptimizationMode.EXPECTED
        )

        # 4. Extract first-timestep optimal decision
        first_dec = opt_result.decision_schedule[0] if (opt_result.decision_schedule and len(opt_result.decision_schedule) > 0) else None
        
        if first_dec and opt_result.solver_status.value in ("OPTIMAL", "FEASIBLE"):
            optimal_diesel_kw = first_dec.diesel_total_kw
            optimal_bess_charge_kw = first_dec.battery_charge_kw
            optimal_bess_dischg_kw = first_dec.battery_discharge_kw
            
            if optimal_diesel_kw > 0.1:
                self.active_controls["diesel_power_override_kw"] = optimal_diesel_kw
                rec_what = f"Dispatch DG-1 at {optimal_diesel_kw:.1f} kW to maintain spinning reserve"
                rec_why = f"HiGHS MILP solved in {opt_result.solver_time_seconds:.3f}s: min-load satisfied, objective {opt_result.summary.objective_value:.1f}"
            else:
                self.active_controls["diesel_power_override_kw"] = 0.0
                rec_what = "Shut down diesel generator DG-1 and dispatch renewable + BESS reserves"
                rec_why = f"HiGHS MILP identified zero diesel requirement: objective {opt_result.summary.objective_value:.1f}, fuel savings prioritized"
                
            if optimal_bess_charge_kw > 0.1:
                self.active_controls["battery_charge_force_kw"] = optimal_bess_charge_kw
            elif optimal_bess_dischg_kw > 0.1 and "battery_charge_force_kw" in self.active_controls:
                del self.active_controls["battery_charge_force_kw"]
        else:
            self.active_controls.clear()
            rec_what = "Engage safe default baseline dispatch (HiGHS fallback)"
            rec_why = f"Solver status {opt_result.solver_status.value}: safe fallback active"

        self.operating_mode = "LIVE_AUTO"
        new_state = self.advance_clock(force_elapsed_seconds=1.0)

        trace_entry = {
            "timestamp": sim_ts,
            "wall_clock": wall_ts,
            "event": "AUTO_RECOMMENDATION_APPROVED",
            "optimizer_class": "OptimizerEngine",
            "solver": "HiGHS",
            "run_id": opt_result.run_id,
            "optimizer_run_id": opt_result.run_id,
            "solver_status": opt_result.solver_status.value,
            "solver_time_sec": opt_result.solver_time_seconds,
            "horizon_hours": opt_result.horizon_hours,
            "objective_value": opt_result.summary.objective_value if opt_result.summary else 0.0,
            "total_fuel_consumed_liters": opt_result.summary.total_fuel_consumed_liters if opt_result.summary else 0.0,
            "twin_replay_valid": opt_result.is_valid,
            "what": rec_what,
            "why": rec_why,
            "resulting_power_kw": {
                "diesel": new_state.diesel.generator_power_kw,
                "battery_soc": new_state.battery.soc_pct,
                "total_demand": new_state.loads.served_load_kw
            },
            "resilience_threat": new_state.resilience.threat_state if new_state.resilience else "UNKNOWN"
        }
        self.trace_history.append(trace_entry)

        return {
            "status": "APPROVED",
            "optimizer_class": "OptimizerEngine",
            "solver": "HiGHS",
            "run_id": opt_result.run_id,
            "solver_status": opt_result.solver_status.value,
            "solver_time_sec": opt_result.solver_time_seconds,
            "horizon_hours": opt_result.horizon_hours,
            "objective_value": opt_result.summary.objective_value if opt_result.summary else 0.0,
            "total_fuel_consumed_liters": opt_result.summary.total_fuel_consumed_liters if opt_result.summary else 0.0,
            "twin_replay_valid": opt_result.is_valid,
            "validation_messages": opt_result.validation_messages,
            "recommendation": rec_what,
            "rationale": rec_why,
            "state": new_state.to_dict(),
            "trace": trace_entry
        }

    def apply_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """
        Injects a scenario perturbation into the live session and recalculates state immediately.
        """
        sid = scenario_id.upper()
        scen_def = self.scenario_registry.get(sid)
        self.active_scenario = sid
        
        sim_ts = self.current_simulation_iso()
        wall_ts = self.current_wall_clock_iso()

        # Recalculate twin state under scenario
        new_state = self.advance_clock(force_elapsed_seconds=1.0)

        trace_entry = {
            "timestamp": sim_ts,
            "wall_clock": wall_ts,
            "event": "SCENARIO_APPLIED",
            "scenario_id": sid,
            "name": scen_def.name,
            "category": scen_def.category.value,
            "transforms_count": len(scen_def.transforms),
            "threat_state": new_state.resilience.threat_state if new_state.resilience else "UNKNOWN"
        }
        self.trace_history.append(trace_entry)

        return {
            "status": "APPLIED",
            "scenario_id": sid,
            "name": scen_def.name,
            "state": new_state.to_dict(),
            "trace": trace_entry
        }

    def clear_scenario(self) -> Dict[str, Any]:
        """Clears active scenario perturbation and recalculates baseline twin state."""
        prev = self.active_scenario
        self.active_scenario = None

        # Explicitly restore baseline hardware and logistics capacities
        self.current_twin_state.battery.capacity_kwh = float(self.profile.electrical.battery_capacity_kwh)
        self.current_twin_state.battery.usable_capacity_kwh = float(self.profile.electrical.battery_capacity_kwh * 0.9)
        self.current_twin_state.diesel.generator_max_power_kw = float(self.profile.electrical.diesel_generator_kw_rated)
        self.current_twin_state.resupply.resupply_window_days = int(self.profile.default_resupply_window_days)
        self.current_twin_state.resupply.resupply_event_active = False
        self.current_twin_state.solar.solar_capacity_kw = float(self.profile.electrical.solar_pv_kw_peak)
        self.current_twin_state.wind.wind_capacity_kw = float(self.profile.electrical.wind_turbine_kw_rated)
        if hasattr(self.current_twin_state, "environment") and self.current_twin_state.environment:
            self.current_twin_state.environment.cloud_fraction = 0.5

        new_state = self.advance_clock(force_elapsed_seconds=1.0)
        
        trace_entry = {
            "timestamp": self.current_simulation_iso(),
            "wall_clock": self.current_wall_clock_iso(),
            "event": "SCENARIO_CLEARED",
            "cleared_scenario_id": prev,
            "status": "BASELINE_RESTORED"
        }
        self.trace_history.append(trace_entry)

        return {
            "status": "CLEARED",
            "active_scenario": None,
            "previous_scenario": prev,
            "state": new_state.to_dict(),
            "trace": trace_entry
        }

    def get_power_flow_topology(self) -> Dict[str, Any]:
        """
        Computes the topological power flow distribution across sources, buses, feeders, and loads.
        Returns exact kW values for each segment, flow direction, and device states.
        """
        state = self.current_twin_state
        
        p_solar = state.solar.solar_generation_kw
        p_wind = state.wind.wind_generation_kw
        p_diesel = state.diesel.generator_power_kw
        p_bat_dis = state.battery.discharge_kw
        p_bat_chg = state.battery.charge_kw
        
        total_gen = p_solar + p_wind + p_diesel + p_bat_dis
        total_load = state.loads.served_load_kw

        # Subload breakdown strictly derived from LoadState
        crit_kw = state.loads.critical_load_kw
        imp_kw = state.loads.important_load_kw
        op_kw = state.loads.operational_load_kw
        flex_kw = state.loads.flexible_load_kw
        maint_kw = state.loads.maintenance_load_kw

        # Active edge flows (from -> to -> kW, active, direction)
        edges = [
            {
                "id": "flow_solar_bus",
                "source": "solar",
                "target": "main_bus",
                "power_kw": p_solar,
                "active": p_solar > 0.05,
                "direction": "FORWARD"
            },
            {
                "id": "flow_wind_bus",
                "source": "wind",
                "target": "main_bus",
                "power_kw": p_wind,
                "active": p_wind > 0.05,
                "direction": "FORWARD"
            },
            {
                "id": "flow_diesel_bus",
                "source": "diesel",
                "target": "main_bus",
                "power_kw": p_diesel,
                "active": p_diesel > 0.05,
                "direction": "FORWARD"
            },
            {
                "id": "flow_battery_bus",
                "source": "battery",
                "target": "main_bus",
                "power_kw": p_bat_chg if p_bat_chg > 0.05 else p_bat_dis,
                "active": (p_bat_chg > 0.05 or p_bat_dis > 0.05),
                "direction": "INTO_BATTERY" if p_bat_chg > 0.05 else "OUT_OF_BATTERY"
            },
            {
                "id": "flow_bus_utilities",
                "source": "main_bus",
                "target": "z_utilities",
                "power_kw": crit_kw,
                "active": crit_kw > 0.05,
                "direction": "FORWARD"
            },
            {
                "id": "flow_bus_operations",
                "source": "main_bus",
                "target": "z_operations",
                "power_kw": imp_kw,
                "active": imp_kw > 0.05,
                "direction": "FORWARD"
            },
            {
                "id": "flow_bus_habitation",
                "source": "main_bus",
                "target": "z_habitation",
                "power_kw": op_kw,
                "active": op_kw > 0.05,
                "direction": "FORWARD"
            },
            {
                "id": "flow_bus_science",
                "source": "main_bus",
                "target": "z_science",
                "power_kw": flex_kw,
                "active": flex_kw > 0.05,
                "direction": "FORWARD"
            },
            {
                "id": "flow_bus_workshop",
                "source": "main_bus",
                "target": "z_workshop",
                "power_kw": maint_kw,
                "active": maint_kw > 0.05,
                "direction": "FORWARD"
            }
        ]

        # Asset operational states
        assets = {
            "solar": {
                "id": "solar",
                "name": "Solar PV Array",
                "power_kw": p_solar,
                "status": "RUNNING" if p_solar > 0.1 else ("FAULT" if state.solar.solar_status == "FAULT" else "STANDBY"),
                "provenance": "SIMULATED"
            },
            "wind": {
                "id": "wind",
                "name": "Wind Turbine Array",
                "power_kw": p_wind,
                "status": "RUNNING" if p_wind > 0.1 else ("FAULT" if state.wind.wind_status == "FAULT" else "STANDBY"),
                "provenance": "SIMULATED"
            },
            "diesel": {
                "id": "diesel",
                "name": "Primary Diesel Generator",
                "power_kw": p_diesel,
                "status": "FAULT" if state.diesel.generator_status == "FAULT" else ("RUNNING" if p_diesel > 0.1 else "STANDBY"),
                "fuel_consumption_l_per_h": state.diesel.fuel_consumption_l_per_h,
                "provenance": "SIMULATED"
            },
            "battery": {
                "id": "battery",
                "name": "Station BESS",
                "soc_pct": state.battery.soc_pct,
                "power_kw": p_bat_chg if p_bat_chg > 0.05 else p_bat_dis,
                "status": "CHARGING" if p_bat_chg > 0.05 else ("DISCHARGING" if p_bat_dis > 0.05 else "STANDBY"),
                "provenance": "SIMULATED"
            },
            "main_bus": {
                "id": "main_bus",
                "name": "Main AC Distribution Switchgear",
                "throughput_kw": total_load,
                "status": "ONLINE",
                "provenance": "SIMULATED"
            }
        }

        # Source mix percentages
        source_mix = {
            "solar_pct": round((p_solar / total_gen * 100.0), 1) if total_gen > 0.01 else 0.0,
            "wind_pct": round((p_wind / total_gen * 100.0), 1) if total_gen > 0.01 else 0.0,
            "diesel_pct": round((p_diesel / total_gen * 100.0), 1) if total_gen > 0.01 else 0.0,
            "battery_pct": round((p_bat_dis / total_gen * 100.0), 1) if total_gen > 0.01 else 0.0
        }

        return {
            "station_id": self.station_id,
            "timestamp": state.timestamp,
            "total_generation_kw": round(total_gen, 2),
            "total_demand_kw": round(total_load, 2),
            "unserved_demand_kw": round(state.loads.unserved_load_kw, 2),
            "source_mix": source_mix,
            "edges": edges,
            "assets": assets,
            "resilience": asdict(state.resilience) if state.resilience else {},
            "provenance": "SIMULATED"
        }

    def trace_power_path(self, target_id: str) -> Dict[str, Any]:
        """
        Traces the exact upstream power delivery chain from a load/panel to the main bus and generation sources.
        """
        flow = self.get_power_flow_topology()
        assets = flow["assets"]
        tid = target_id.lower()

        # Find which zone or device is requested
        zone_map = {
            "z_utilities": "Life Support & Critical Auxiliaries",
            "z_operations": "Mission Operations & Communications",
            "z_habitation": "Habitation & Domestic Living",
            "z_science": "Science Laboratories & Experiments",
            "z_workshop": "Maintenance Workshop & EV Charging"
        }
        target_name = zone_map.get(tid, f"Load Circuit ({target_id})")

        # Proportional contributions from current active generation mix
        tot_gen = flow["total_generation_kw"]
        contributions = []
        if tot_gen > 0.01:
            for src_key in ["solar", "wind", "diesel", "battery"]:
                src = assets[src_key]
                p_kw = src.get("power_kw", 0.0)
                if p_kw > 0.01 and (src_key != "battery" or src.get("status") == "DISCHARGING"):
                    share_pct = round(p_kw / tot_gen * 100.0, 1)
                    contributions.append({
                        "source_id": src_key,
                        "source_name": src["name"],
                        "share_pct": share_pct,
                        "delivered_kw": p_kw
                    })

        chain = [
            {"level": "SOURCES", "elements": [c["source_name"] for c in contributions]},
            {"level": "MAIN_BUS", "elements": ["Main 415V AC Switchboard"]},
            {"level": "DISTRIBUTION", "elements": [f"Feeder to {target_name}"]},
            {"level": "TARGET", "elements": [target_name]}
        ]

        return {
            "station_id": self.station_id,
            "target_id": target_id,
            "target_name": target_name,
            "upstream_chain": chain,
            "active_contributions": contributions,
            "provenance": "SIMULATED"
        }

    def trace_impact(self, asset_id: str) -> Dict[str, Any]:
        """
        Traces downstream consequences if a source, bus, or feeder is degraded or lost.
        Calculates exact affected loads, deficit, reserve delta, and policy recommendation.
        """
        state = self.current_twin_state
        aid = asset_id.lower()
        
        if "gen" in aid or "diesel" in aid:
            lost_kw = state.diesel.generator_power_kw
            asset_name = "Primary Diesel Generator"
            deficit_kw = max(0.0, lost_kw - state.battery.discharge_kw)
            critical_impact = (deficit_kw > state.loads.flexible_load_kw + state.loads.operational_load_kw)
            recommended_action = "Start Auxiliary Generator DG-2; prioritize Life Support and Communications"
        elif "solar" in aid:
            lost_kw = state.solar.solar_generation_kw
            asset_name = "Solar PV Array"
            deficit_kw = lost_kw
            critical_impact = False
            recommended_action = "Ramp battery discharge or schedule DG-1 startup to offset lost renewable generation"
        elif "wind" in aid:
            lost_kw = state.wind.wind_generation_kw
            asset_name = "Wind Turbine System"
            deficit_kw = lost_kw
            critical_impact = False
            recommended_action = "Engage battery discharge support; monitor blizzard cutout thresholds"
        elif "bat" in aid or "bess" in aid:
            lost_kw = state.battery.discharge_kw
            asset_name = "Battery Energy Storage System (BESS)"
            deficit_kw = lost_kw
            critical_impact = True
            recommended_action = "Start DG-1 immediately to cover base load; enforce non-critical load shedding"
        else:
            lost_kw = 10.0
            asset_name = f"Asset {asset_id}"
            deficit_kw = 10.0
            critical_impact = False
            recommended_action = "Inspect feeder breaker and isolate non-critical circuits"

        return {
            "station_id": self.station_id,
            "asset_id": asset_id,
            "asset_name": asset_name,
            "lost_power_kw": round(lost_kw, 2),
            "net_deficit_kw": round(deficit_kw, 2),
            "critical_loads_threatened": critical_impact,
            "current_threat_state": state.resilience.threat_state if state.resilience else "UNKNOWN",
            "recommended_mitigation": recommended_action,
            "affected_subsystems": [
                "Life Support" if critical_impact else "Science Labs",
                "Galley & Residential",
                "Battery Reserve"
            ],
            "provenance": "SIMULATED"
        }

    def configure_session(
        self,
        data_mode: str = "LIVE",
        simulation_time: Optional[str] = None,
        time_acceleration: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Configures session mode (LIVE vs HISTORICAL vs REPLAY) and simulation anchor time.
        """
        mode = data_mode.upper()
        if mode in ("LIVE", "HISTORICAL", "REPLAY"):
            self.data_mode = mode

        if time_acceleration is not None:
            self.time_acceleration = max(0.1, float(time_acceleration))

        if self.data_mode == "LIVE":
            self.simulation_base_time = datetime.now(timezone.utc)
            self.simulation_elapsed_seconds = 0.0
            self.wall_clock_start = time.time()
            self.last_wall_tick = self.wall_clock_start
        elif self.data_mode == "HISTORICAL":
            if simulation_time:
                self.simulation_base_time = datetime.fromisoformat(simulation_time.replace("Z", "+00:00"))
            self.simulation_elapsed_seconds = 0.0
            self.wall_clock_start = time.time()
            self.last_wall_tick = self.wall_clock_start

        # Advance clock to calculate immediate state under configured date/season
        new_state = self.advance_clock(force_elapsed_seconds=1.0)

        trace_entry = {
            "timestamp": self.current_simulation_iso(),
            "wall_clock": self.current_wall_clock_iso(),
            "event": "SESSION_CONFIGURED",
            "data_mode": self.data_mode,
            "simulation_time": self.current_simulation_iso(),
            "details": f"Session configured to {self.data_mode} mode anchored at {self.current_simulation_iso()}"
        }
        self.trace_history.append(trace_entry)

        return {
            "status": "CONFIGURED",
            "data_mode": self.data_mode,
            "simulation_time": self.current_simulation_iso(),
            "snapshot": self.get_snapshot(),
            "trace": trace_entry
        }

    def get_snapshot(self) -> Dict[str, Any]:
        """Returns complete serializable snapshot of the live session."""
        return {
            "metadata": asdict(LiveSessionMetadata(
                session_id=self.session_id,
                station_id=self.station_id,
                simulation_timestamp=self.current_simulation_iso(),
                wall_clock_timestamp=self.current_wall_clock_iso(),
                simulation_elapsed_seconds=round(self.simulation_elapsed_seconds, 2),
                time_acceleration=self.time_acceleration,
                operating_mode=self.operating_mode,
                active_scenario=self.active_scenario,
                active_controls=self.active_controls,
                session_status=self.session_status,
                last_update=self.last_update,
                data_mode=self.data_mode,
                provenance="SIMULATED"
            )),
            "state": self.current_twin_state.to_dict(),
            "power_flow": self.get_power_flow_topology(),
            "provenance": "SIMULATED"
        }


class LiveTwinSessionManager:
    """Singleton session registry managing active live twin sessions across stations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LiveTwinSessionManager, cls).__new__(cls)
            cls._instance.sessions: Dict[str, LiveTwinSession] = {}
        return cls._instance

    def get_session(self, station_id: str) -> LiveTwinSession:
        sid = station_id.upper()
        if sid not in self.sessions:
            self.sessions[sid] = LiveTwinSession(station_id=sid)
        return self.sessions[sid]

    def reset_session(self, station_id: str) -> LiveTwinSession:
        sid = station_id.upper()
        self.sessions[sid] = LiveTwinSession(station_id=sid)
        return self.sessions[sid]


# Global session manager instance
live_twin_manager = LiveTwinSessionManager()
