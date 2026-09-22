"""
POLARIS-EMS — Digital Twin Electrical Power Balance Engine
SIH26061: Polar Energy Management & Resilience System

Implements the central conservation of energy equation under BASELINE_SIMULATION_DISPATCH:
P_solar + P_wind + P_diesel + P_bat,dis = P_load,served + P_bat,chg + P_curt
P_load,served + P_unserved = P_load,requested

Strictly non-optimal deterministic simulation rule:
Phase 4 answers: 'What happens if the station follows this baseline dispatch rule?'
Phase 6 (Optimizer) answers: 'What dispatch should Polaris-EMS choose?'
"""

from typing import Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class DispatchResult:
    solar_generation_kw: float
    wind_generation_kw: float
    battery_charge_kw: float
    battery_discharge_kw: float
    diesel_power_kw: float
    curtailment_kw: float
    served_load_kw: float
    unserved_load_kw: float
    served_critical_kw: float
    unserved_critical_kw: float
    balance_error_kw: float
    is_balanced: bool
    policy_name: str = "BASELINE_SIMULATION_DISPATCH"


class PowerBalanceEngine:
    """Solves electrical flow conservation and subload satisfaction at each simulation step."""

    TOLERANCE_KW = 1e-4

    @staticmethod
    def solve_baseline_dispatch(
        requested_load_kw: float,
        critical_load_kw: float,
        solar_available_kw: float,
        wind_available_kw: float,
        max_battery_charge_kw: float,
        max_battery_discharge_kw: float,
        max_diesel_power_kw: float,
        min_diesel_power_kw: float = 0.0
    ) -> DispatchResult:
        """
        Executes BASELINE_SIMULATION_DISPATCH sequence:
        Solar + Wind -> Battery Discharge -> Diesel -> Unserved Energy
        """
        p_load = max(0.0, float(requested_load_kw))
        p_crit = min(p_load, max(0.0, float(critical_load_kw)))
        
        p_solar_avail = max(0.0, float(solar_available_kw))
        p_wind_avail = max(0.0, float(wind_available_kw))
        total_ren_avail = p_solar_avail + p_wind_avail

        net_power = total_ren_avail - p_load

        p_bat_chg = 0.0
        p_bat_dis = 0.0
        p_diesel = 0.0
        p_curt = 0.0
        p_unserved = 0.0
        p_solar_gen = p_solar_avail
        p_wind_gen = p_wind_avail

        if net_power >= 0.0:
            # Surplus renewable scenario
            surplus = net_power
            p_bat_chg = min(max(0.0, max_battery_charge_kw), surplus)
            p_curt = surplus - p_bat_chg
            p_served = p_load
            p_unserved = 0.0

            # If curtailment occurs, apportion curtailment proportionally between solar and wind
            if p_curt > 0.01 and total_ren_avail > 0.01:
                solar_share = p_solar_avail / total_ren_avail
                p_solar_curt = p_curt * solar_share
                p_wind_curt = p_curt * (1.0 - solar_share)
                p_solar_gen = max(0.0, p_solar_avail - p_solar_curt)
                p_wind_gen = max(0.0, p_wind_avail - p_wind_curt)

        else:
            # Deficit scenario: renewables cannot cover full demand
            deficit = -net_power

            # 1. Battery discharge covers deficit up to discharge limits
            p_bat_dis = min(max(0.0, max_battery_discharge_kw), deficit)
            remaining_deficit = deficit - p_bat_dis

            # 2. Diesel generation covers residual deficit up to rated capacity
            if remaining_deficit > 0.01:
                needed_diesel = remaining_deficit
                # Clamp to generator ratings
                p_diesel = min(max_diesel_power_kw, max(min_diesel_power_kw, needed_diesel))
                
                # If diesel produces more than needed due to min_loading, charge battery with surplus
                if p_diesel > remaining_deficit:
                    surplus_diesel = p_diesel - remaining_deficit
                    chg_absorb = min(max_battery_charge_kw, surplus_diesel)
                    p_bat_chg += chg_absorb
                    p_curt += (surplus_diesel - chg_absorb)

                unserved_after_diesel = max(0.0, remaining_deficit - p_diesel)
                p_unserved = unserved_after_diesel
            else:
                p_unserved = 0.0

            p_served = p_load - p_unserved

        # Honest subload allocation: served power covers critical load first
        if p_served >= p_crit:
            served_crit = p_crit
            unserved_crit = 0.0
        else:
            served_crit = p_served
            unserved_crit = p_crit - p_served

        # Power balance conservation verification (Total available sources == Sinks + Curtailment)
        total_sources = p_solar_avail + p_wind_avail + p_diesel + p_bat_dis
        total_sinks = p_served + p_bat_chg + p_curt
        balance_err = abs(total_sources - total_sinks)
        is_balanced = balance_err < PowerBalanceEngine.TOLERANCE_KW

        return DispatchResult(
            solar_generation_kw=round(p_solar_gen, 2),
            wind_generation_kw=round(p_wind_gen, 2),
            battery_charge_kw=round(p_bat_chg, 2),
            battery_discharge_kw=round(p_bat_dis, 2),
            diesel_power_kw=round(p_diesel, 2),
            curtailment_kw=round(p_curt, 2),
            served_load_kw=round(p_served, 2),
            unserved_load_kw=round(p_unserved, 2),
            served_critical_kw=round(served_crit, 2),
            unserved_critical_kw=round(unserved_crit, 2),
            balance_error_kw=round(balance_err, 6),
            is_balanced=is_balanced,
            policy_name="BASELINE_SIMULATION_DISPATCH"
        )
