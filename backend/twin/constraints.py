"""
POLARIS-EMS — Digital Twin Constraint Evaluation Engine
SIH26061: Polar Energy Management & Resilience System

Evaluates physical boundaries, generator ratings, electrochemical limits,
and monitored service constraints (critical load satisfaction and thermal habitability).
Never silently repairs violations; reports full physical status honestly.
"""

from typing import List, Dict, Any, Optional
from backend.twin.state import TwinState, ConstraintEvaluation
from backend.twin.safety_thresholds import SafetyThresholdRegistry


class ConstraintEvaluator:
    """Evaluates the complete set of physical, electrical, and service constraints on TwinState."""

    def __init__(self, safety_registry: Optional[SafetyThresholdRegistry] = None):
        self.safety_registry = safety_registry or SafetyThresholdRegistry()

    def evaluate_all(self, state: TwinState) -> List[ConstraintEvaluation]:
        """
        Evaluates 10 distinct constraints on the station twin state.
        """
        evaluations: List[ConstraintEvaluation] = []
        sid = state.station_id

        # 1. Diesel generator maximum capacity
        p_diesel = state.diesel.generator_power_kw
        p_d_max = state.diesel.generator_max_power_kw
        v_d_max = max(0.0, p_diesel - p_d_max)
        evaluations.append(ConstraintEvaluation(
            constraint_name="diesel_generator_max_capacity",
            value=p_diesel,
            limit=p_d_max,
            status="VIOLATED" if v_d_max > 0.01 else "SATISFIED",
            violation_magnitude=round(v_d_max, 2),
            unit="kW",
            provenance="CONFIGURED"
        ))

        # 2. Diesel generator minimum loading
        p_d_min = state.diesel.generator_min_power_kw
        if state.diesel.generator_status == "ONLINE" and p_diesel > 0.01:
            v_d_min = max(0.0, p_d_min - p_diesel)
            status_d_min = "VIOLATED" if v_d_min > 0.01 else "SATISFIED"
        else:
            v_d_min = 0.0
            status_d_min = "SATISFIED"
        evaluations.append(ConstraintEvaluation(
            constraint_name="diesel_generator_min_loading",
            value=p_diesel,
            limit=p_d_min,
            status=status_d_min,
            violation_magnitude=round(v_d_min, 2),
            unit="kW",
            provenance="CONFIGURED"
        ))

        # 3. Battery SOC minimum
        soc = state.battery.soc_pct
        soc_min = state.battery.soc_min
        v_soc_min = max(0.0, soc_min - soc)
        warn_soc = self.safety_registry.get_value(sid, "battery_warning_soc", soc_min + 0.05)
        status_soc = "VIOLATED" if v_soc_min > 0.001 else ("WARNING" if soc <= warn_soc else "SATISFIED")
        evaluations.append(ConstraintEvaluation(
            constraint_name="battery_soc_minimum",
            value=round(soc, 4),
            limit=round(soc_min, 4),
            status=status_soc,
            violation_magnitude=round(v_soc_min, 4),
            unit="fraction",
            provenance="CONFIGURED"
        ))

        # 4. Battery SOC maximum
        soc_max = state.battery.soc_max
        v_soc_max = max(0.0, soc - soc_max)
        evaluations.append(ConstraintEvaluation(
            constraint_name="battery_soc_maximum",
            value=round(soc, 4),
            limit=round(soc_max, 4),
            status="VIOLATED" if v_soc_max > 0.001 else "SATISFIED",
            violation_magnitude=round(v_soc_max, 4),
            unit="fraction",
            provenance="CONFIGURED"
        ))

        # 5. Battery Charge Inverter Rate Limit
        p_chg = state.battery.charge_kw
        p_chg_max = state.battery.max_charge_kw
        v_chg = max(0.0, p_chg - p_chg_max)
        evaluations.append(ConstraintEvaluation(
            constraint_name="battery_charge_rate_limit",
            value=round(p_chg, 2),
            limit=round(p_chg_max, 2),
            status="VIOLATED" if v_chg > 0.01 else "SATISFIED",
            violation_magnitude=round(v_chg, 2),
            unit="kW",
            provenance="CONFIGURED"
        ))

        # 6. Battery Discharge Inverter Rate Limit
        p_dis = state.battery.discharge_kw
        p_dis_max = state.battery.max_discharge_kw
        v_dis = max(0.0, p_dis - p_dis_max)
        evaluations.append(ConstraintEvaluation(
            constraint_name="battery_discharge_rate_limit",
            value=round(p_dis, 2),
            limit=round(p_dis_max, 2),
            status="VIOLATED" if v_dis > 0.01 else "SATISFIED",
            violation_magnitude=round(v_dis, 2),
            unit="kW",
            provenance="CONFIGURED"
        ))

        # 5. Fuel critical reserve
        fuel = state.fuel.fuel_remaining_l
        fuel_res = state.fuel.fuel_reserve_l
        v_fuel = max(0.0, fuel_res - fuel)
        evaluations.append(ConstraintEvaluation(
            constraint_name="fuel_critical_reserve",
            value=round(fuel, 1),
            limit=round(fuel_res, 1),
            status="VIOLATED" if v_fuel > 0.1 else ("WARNING" if fuel <= fuel_res * 1.15 else "SATISFIED"),
            violation_magnitude=round(v_fuel, 1),
            unit="liters",
            provenance="CONFIGURED"
        ))

        # 6. Monitored Critical Load Protection
        unserved_crit = state.loads.unserved_critical_kw
        evaluations.append(ConstraintEvaluation(
            constraint_name="critical_load_protection",
            value=round(unserved_crit, 2),
            limit=0.0,
            status="VIOLATED" if unserved_crit > 0.01 else "SATISFIED",
            violation_magnitude=round(unserved_crit, 2),
            unit="kW",
            provenance="CONFIGURED"
        ))

        # 7. Indoor thermal safe minimum
        t_in = state.thermal.indoor_temperature_c
        t_min_safe = state.thermal.indoor_min_safe_temp_c
        v_temp = max(0.0, t_min_safe - t_in)
        evaluations.append(ConstraintEvaluation(
            constraint_name="indoor_thermal_safe_minimum",
            value=round(t_in, 2),
            limit=round(t_min_safe, 2),
            status="VIOLATED" if v_temp > 0.01 else ("WARNING" if t_in <= t_min_safe + 1.5 else "SATISFIED"),
            violation_magnitude=round(v_temp, 2),
            unit="deg_C",
            provenance="CONFIGURED"
        ))

        # 8. Electrical Power Balance Conservation
        p_sources = (
            state.solar.solar_generation_kw
            + state.wind.wind_generation_kw
            + state.diesel.generator_power_kw
            + state.battery.discharge_kw
        )
        p_sinks = (
            state.loads.served_load_kw
            + state.battery.charge_kw
            + state.solar.solar_curtailed_kw
            + state.wind.wind_curtailed_kw
        )
        balance_err = abs(p_sources - p_sinks)
        evaluations.append(ConstraintEvaluation(
            constraint_name="electrical_power_balance",
            value=round(balance_err, 5),
            limit=1e-4,
            status="VIOLATED" if balance_err > 1e-4 else "SATISFIED",
            violation_magnitude=round(max(0.0, balance_err - 1e-4), 5),
            unit="kW",
            provenance="CONFIGURED"
        ))

        return evaluations
