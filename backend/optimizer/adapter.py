"""
POLARIS-EMS — Optimizer Data Adapter
SIH26061: Polar Energy Management & Resilience System

Converts Phase 3 ML ForecastResult, Phase 4 TwinState, Phase 5 ScenarioDefinition,
and authoritative station configurations into sanitized, strongly typed model inputs for Pyomo.
Features:
- Effective resupply schedule synthesis (accounting for base schedule + scenario delays)
- Per-generator availability matrices (handling maintenance, trip, and fault states)
- Multi-tier subload decomposition (critical, non-critical, flexible, thermal)
- Cold-derated battery capacity trajectories
- Terminal state targets for storage, fuel, and reserve
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
import json
import numpy as np

from backend.data.station_profiles.loader import StationProfile
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.optimizer.schema import EffectiveResupplyEvent, OptimizationMode
from backend.scenarios.schema import ScenarioDefinition


@dataclass
class OptimizerModelInputs:
    """Sanitized parameter pack ready for Pyomo ConcreteModel formulation."""
    horizon_hours: int
    timestamps: List[str]
    ambient_temp_c: List[float]
    wind_speed_ms: List[float]
    ghi_wm2: List[float]
    p_load_req: List[float]
    p_crit_req: List[float]
    p_noncrit_req: List[float]
    p_flex_req: List[float]
    p_solar_avail: List[float]
    p_wind_avail: List[float]
    
    # Generator specs
    generator_count: int
    generator_rated_kw: float
    generator_min_loading_pct: float
    generator_fuel_curve_l_per_kwh: float
    generator_idle_fuel_l_per_h: float
    generator_availability: Dict[int, List[bool]]
    initial_generator_online: Dict[int, bool]

    # Battery specs
    initial_battery_soc: float
    battery_capacity_nominal_kwh: float
    battery_usable_capacity_kwh: List[float]
    battery_min_soc: float
    battery_max_soc: float
    battery_max_charge_kw: float
    battery_max_discharge_kw: float
    battery_charge_efficiency: float
    battery_discharge_efficiency: float

    # Fuel & Resupply specs
    initial_fuel_liters: float
    critical_fuel_reserve_liters: float
    effective_resupplies: List[EffectiveResupplyEvent]
    resupply_inflow_liters: List[float]
    pre_resupply_timesteps: List[int]

    # Thermal specs
    initial_indoor_temp_c: float
    target_indoor_temp_c: float
    min_safe_indoor_temp_c: float
    building_ua_kw_per_k: float
    thermal_capacitance_kwh_per_k: float
    ventilation_loss_coeff: float
    internal_heat_gain_kw: float

    # Reserve & Terminal Targets
    reserve_margin_pct: float
    terminal_soc_target: float
    terminal_required_fuel: float
    weights: Dict[str, float]


class OptimizerDataAdapter:
    """Translates state and trajectory data into mathematical model parameters."""

    def __init__(
        self,
        weights_path: Optional[Path] = None,
        safety_registry: Optional[SafetyThresholdRegistry] = None
    ):
        if weights_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            weights_path = base_dir / "configs" / "optimizer_weights.json"
        self.weights_path = Path(weights_path)
        self.safety_registry = safety_registry or SafetyThresholdRegistry()
        self._weights: Dict[str, float] = {}
        self._terminal_cfg: Dict[str, Any] = {}
        self.load_weights()

    def load_weights(self) -> None:
        if not self.weights_path.exists():
            raise FileNotFoundError(f"Optimizer weights config not found at {self.weights_path}")
        with open(self.weights_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_w = data.get("weights", {})
        self._weights = {
            "w_crit": float(raw_w.get("critical_unserved_penalty_per_kwh", {}).get("value", 100000.0)),
            "w_thermal": float(raw_w.get("thermal_violation_penalty_per_deg_c", {}).get("value", 10000.0)),
            "w_noncrit": float(raw_w.get("noncritical_unserved_penalty_per_kwh", {}).get("value", 500.0)),
            "w_reserve": float(raw_w.get("reserve_deficit_penalty_per_kw", {}).get("value", 50.0)),
            "w_fuel": float(raw_w.get("fuel_cost_per_liter", {}).get("value", 1.0)),
            "w_start": float(raw_w.get("generator_startup_penalty", {}).get("value", 5.0)),
            "w_bat_wear": float(raw_w.get("battery_wear_penalty_per_kwh", {}).get("value", 0.05)),
            "w_curt": float(raw_w.get("renewable_curtailment_penalty_per_kwh", {}).get("value", 0.01)),
        }
        self._terminal_cfg = data.get("terminal_protection", {})

    def build_effective_resupply_schedule(
        self,
        profile: StationProfile,
        horizon_hours: int,
        scenario: Optional[ScenarioDefinition] = None
    ) -> List[EffectiveResupplyEvent]:
        """
        Synthesizes the effective resupply events within the planning horizon,
        incorporating any scenario-induced resupply delays (Correction 4).
        """
        events: List[EffectiveResupplyEvent] = []
        
        # Baseline arrival step: within horizon if interval fits, otherwise day 3 (72h)
        baseline_step = min(72, int(getattr(profile, "resupply_interval_days", 180) * 24))
        fuel_delivery = float(profile.fuel.storage_capacity_liters * 0.40)  # standard ~40% tank restock

        delay_hours = 0
        if scenario:
            for pt in getattr(scenario, "transforms", []):
                if pt.parameter == "resupply_delay_hours":
                    delay_hours = int(pt.value)
                elif pt.parameter == "resupply_active" and pt.value is False:
                    delay_hours = 999999  # effectively cancelled

        effective_step = baseline_step + delay_hours
        if 0 <= effective_step < horizon_hours:
            events.append(EffectiveResupplyEvent(
                step_index=effective_step,
                timestamp=f"T+{effective_step}",
                fuel_delivered_liters=fuel_delivery,
                is_delayed=(delay_hours > 0),
                delay_hours=delay_hours,
                provenance="CONFIGURED"
            ))

        return events

    def adapt(
        self,
        profile: StationProfile,
        initial_state: TwinState,
        trajectory: List[TwinInputStep],
        scenario: Optional[ScenarioDefinition] = None,
        mode: OptimizationMode = OptimizationMode.EXPECTED,
        generator_overrides: Optional[Dict[int, str]] = None  # {gen_id: "AVAILABLE" | "FAULT" | "MAINTENANCE"}
    ) -> OptimizerModelInputs:
        """Constructs the comprehensive OptimizerModelInputs parameter pack."""
        sid = profile.station_id.upper()
        T = len(trajectory)

        # 1. Weather and Potentials
        timestamps = [step.timestamp for step in trajectory]
        amb_temps = [step.ambient_temp_c for step in trajectory]
        wind_speeds = [step.wind_speed_m_per_s for step in trajectory]
        ghis = [step.ghi_w_per_m2 for step in trajectory]
        solar_cap = float(profile.electrical.solar_pv_kw_peak)
        wind_cap = float(profile.electrical.wind_turbine_kw_rated)
        p_solars = [min(solar_cap, max(0.0, step.solar_kw)) for step in trajectory]
        p_winds = [min(wind_cap, max(0.0, step.wind_kw)) for step in trajectory]

        # 2. Subload Breakdown
        # Critical load: typically 35-40% of base load (freeze protection, satcom, medical)
        # Flexible load: 15% of non-critical load (water pumping, snow melter, laundry)
        p_loads = [step.load_kw for step in trajectory]
        p_crits: List[float] = []
        p_noncrits: List[float] = []
        p_flexs: List[float] = []

        for p_l in p_loads:
            crit = round(p_l * 0.38, 2)
            rem = max(0.0, p_l - crit)
            flex = round(rem * 0.18, 2)
            noncrit = round(rem - flex, 2)
            p_crits.append(crit)
            p_flexs.append(flex)
            p_noncrits.append(noncrit)

        # 3. Generator Parameters & Availability Matrix
        gen_count = int(profile.electrical.diesel_generator_count)
        gen_rated = float(profile.electrical.diesel_generator_kw_rated)
        gen_min_pct = float(profile.electrical.diesel_min_loading_pct)
        gen_fuel_curve = float(profile.electrical.diesel_fuel_curve_l_per_kwh)
        gen_idle_fuel = float(profile.electrical.diesel_idle_fuel_l_per_h)

        gen_avail: Dict[int, List[bool]] = {g: [True] * T for g in range(1, gen_count + 1)}
        init_online: Dict[int, bool] = {g: False for g in range(1, gen_count + 1)}
        if initial_state.diesel.generator_status == "ONLINE":
            init_online[1] = True

        # Apply generator scenario/manual overrides
        if generator_overrides:
            for g, status in generator_overrides.items():
                if 1 <= g <= gen_count:
                    if status in ("FAULT", "MAINTENANCE"):
                        gen_avail[g] = [False] * T
                        init_online[g] = False

        if scenario:
            for pt in getattr(scenario, "transforms", []):
                if pt.parameter == "diesel_generator_available" and pt.value is False:
                    # Trip unit 2 by default if multiple
                    target_g = 2 if gen_count >= 2 else 1
                    gen_avail[target_g] = [False] * T
                elif pt.parameter == "diesel_capacity_kw" and pt.operator == "SET":
                    gen_rated = float(pt.value)

        # 4. Battery Parameters & Cold Derating
        nom_bat_cap = float(profile.electrical.battery_capacity_kwh)
        bat_min_soc = float(profile.electrical.battery_min_soc)
        bat_max_soc = float(profile.electrical.battery_max_soc)
        max_chg = float(profile.electrical.battery_max_charge_kw)
        max_dis = float(profile.electrical.battery_max_discharge_kw)
        rt_eff = float(profile.electrical.battery_roundtrip_efficiency)
        chg_eff = float(round(np.sqrt(rt_eff), 4))
        dis_eff = float(round(np.sqrt(rt_eff), 4))
        cold_coeff = float(profile.electrical.battery_cold_derate_coeff)

        # Check scenario battery degradation (Correction 3 applies proper terminology)
        deg_factor = 1.0
        if scenario:
            for pt in getattr(scenario, "transforms", []):
                if pt.parameter == "battery_capacity_derate":
                    deg_factor = float(pt.value)

        usable_caps: List[float] = []
        for t_amb in amb_temps:
            if t_amb < -10.0:
                derate = max(0.70, 1.0 - cold_coeff * (-10.0 - t_amb))
            else:
                derate = 1.0
            usable_caps.append(round(nom_bat_cap * derate * deg_factor, 2))

        # 5. Effective Resupply Schedule & Pre-Resupply Constraints (Correction 4)
        effective_resupplies = self.build_effective_resupply_schedule(profile, T, scenario)
        resupply_inflow = [0.0] * T
        pre_resupply_steps: List[int] = []
        for ev in effective_resupplies:
            if 0 <= ev.step_index < T:
                resupply_inflow[ev.step_index] = ev.fuel_delivered_liters
                if ev.step_index > 0:
                    pre_resupply_steps.append(ev.step_index - 1)

        # 6. Thermal Profile
        init_indoor = float(initial_state.thermal.indoor_temp_c)
        target_indoor = float(profile.thermal.indoor_target_temp_c)
        min_safe_indoor = float(self.safety_registry.get_value(
            sid, "indoor_temp_safe_min", profile.thermal.indoor_min_safe_temp_c
        ))
        building_ua = float(profile.thermal.building_ua_kw_per_k)
        th_cap = float(profile.thermal.thermal_capacitance_kwh_per_k)
        vent_loss = float(profile.thermal.ventilation_loss_coeff)
        int_gain = float(profile.thermal.internal_heat_gain_kw)

        # 7. Reserve & Terminal Targets (Correction 1)
        res_margin_pct = 0.40 if mode == OptimizationMode.CONSERVATIVE else 0.30
        terminal_soc = float(self._terminal_cfg.get("default_terminal_soc_target", 0.50))
        # Fuel terminal: ensure at least critical fuel reserve is preserved
        crit_fuel_res = float(profile.fuel.critical_fuel_reserve_liters)
        terminal_fuel = crit_fuel_res

        return OptimizerModelInputs(
            horizon_hours=T,
            timestamps=timestamps,
            ambient_temp_c=amb_temps,
            wind_speed_ms=wind_speeds,
            ghi_wm2=ghis,
            p_load_req=p_loads,
            p_crit_req=p_crits,
            p_noncrit_req=p_noncrits,
            p_flex_req=p_flexs,
            p_solar_avail=p_solars,
            p_wind_avail=p_winds,
            generator_count=gen_count,
            generator_rated_kw=gen_rated,
            generator_min_loading_pct=gen_min_pct,
            generator_fuel_curve_l_per_kwh=gen_fuel_curve,
            generator_idle_fuel_l_per_h=gen_idle_fuel,
            generator_availability=gen_avail,
            initial_generator_online=init_online,
            initial_battery_soc=float(initial_state.battery.soc_pct),
            battery_capacity_nominal_kwh=nom_bat_cap,
            battery_usable_capacity_kwh=usable_caps,
            battery_min_soc=bat_min_soc,
            battery_max_soc=bat_max_soc,
            battery_max_charge_kw=max_chg,
            battery_max_discharge_kw=max_dis,
            battery_charge_efficiency=chg_eff,
            battery_discharge_efficiency=dis_eff,
            initial_fuel_liters=float(initial_state.fuel.fuel_remaining_l),
            critical_fuel_reserve_liters=crit_fuel_res,
            effective_resupplies=effective_resupplies,
            resupply_inflow_liters=resupply_inflow,
            pre_resupply_timesteps=pre_resupply_steps,
            initial_indoor_temp_c=init_indoor,
            target_indoor_temp_c=target_indoor,
            min_safe_indoor_temp_c=min_safe_indoor,
            building_ua_kw_per_k=building_ua,
            thermal_capacitance_kwh_per_k=th_cap,
            ventilation_loss_coeff=vent_loss,
            internal_heat_gain_kw=int_gain,
            reserve_margin_pct=res_margin_pct,
            terminal_soc_target=terminal_soc,
            terminal_required_fuel=terminal_fuel,
            weights=self._weights
        )
