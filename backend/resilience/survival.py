"""
POLARIS-EMS — Survival Horizon & Time-to-Critical Calculator
SIH26061: Polar Energy Management & Resilience System

Evaluates multi-horizon survivability and earliest threshold breaches:
- Critical-load survival horizon
- Thermal habitability horizon
- Battery endurance horizon
- Fuel endurance horizon
- Dependable-generation horizon
- Resupply-gap survivability
- Overall binding station survival horizon
- Chronological Time-to-Threat tracking with explicit timestamps

Enforces Guardrails 8 & 9:
- Precise thresholds; no extrapolation beyond input trajectory.
- Explicitly distinguishes SURVIVES_FULL_INPUT_HORIZON from infinite claims.
"""

from typing import List, Tuple, Optional, Dict, Any
from backend.twin.state import TwinState
from backend.resilience.schema import SurvivalHorizons, TimeToThreat


class SurvivalCalculator:
    """Calculates chronological failure horizons and earliest threshold crossings."""

    @staticmethod
    def calculate_survival_and_timings(
        states: List[TwinState],
        min_safe_temp: float = 12.0,
        fuel_reserve_liters: float = 25000.0,
        reserve_threat_pct: float = 15.0,
        battery_warning_soc: float = 0.25,
        dt_hours: float = 1.0
    ) -> Tuple[SurvivalHorizons, TimeToThreat]:
        """
        Traverses trajectory chronologically to detect earliest threshold breaches.
        """
        total_steps = len(states)
        total_horizon_h = round(total_steps * dt_hours, 1)

        # Failure horizon tracking (initial None = no failure observed in horizon)
        first_crit_fail_h: Optional[float] = None
        first_crit_fail_ts: Optional[str] = None

        first_therm_fail_h: Optional[float] = None
        first_therm_fail_ts: Optional[str] = None

        first_bat_fail_h: Optional[float] = None
        first_bat_fail_ts: Optional[str] = None

        first_fuel_fail_h: Optional[float] = None
        first_fuel_fail_ts: Optional[str] = None

        first_gen_fail_h: Optional[float] = None
        first_gen_fail_ts: Optional[str] = None

        first_resupply_vuln_h: Optional[float] = None
        first_resupply_vuln_ts: Optional[str] = None

        # Threat timing tracking
        first_reserve_viol_h: Optional[float] = None
        first_reserve_viol_ts: Optional[str] = None

        first_bat_warn_h: Optional[float] = None
        first_bat_warn_ts: Optional[str] = None

        first_overall_crit_h: Optional[float] = None
        first_overall_crit_ts: Optional[str] = None

        for idx, state in enumerate(states):
            h = round((idx + 1) * dt_hours, 2)
            ts = state.timestamp

            # 1. Critical load failure: unserved critical load > 1e-4
            if state.loads.unserved_critical_kw > 1e-4 and first_crit_fail_h is None:
                first_crit_fail_h = h
                first_crit_fail_ts = ts

            # 2. Thermal habitability failure: indoor temp < min_safe_temp
            if state.thermal.indoor_temperature_c < min_safe_temp - 1e-4 and first_therm_fail_h is None:
                first_therm_fail_h = h
                first_therm_fail_ts = ts

            # 3. Battery endurance failure:
            # Battery at/below minimum SOC AND generation cannot pick up the load deficit
            diesel_headroom = 0.0
            if state.diesel.generator_status in ("ONLINE", "STANDBY") and state.fuel.fuel_remaining_l > 0.01:
                diesel_headroom = max(0.0, state.diesel.generator_max_power_kw - state.diesel.generator_power_kw)

            if state.battery.soc_pct <= state.battery.soc_min + 1e-4:
                # If battery is empty and unserved load occurs or diesel cannot cover discharge
                if state.loads.unserved_load_kw > 1e-4 or diesel_headroom < 1e-2:
                    if first_bat_fail_h is None:
                        first_bat_fail_h = h
                        first_bat_fail_ts = ts

            # 4. Fuel endurance failure: remaining fuel <= emergency reserve limit
            if state.fuel.fuel_remaining_l <= fuel_reserve_liters and first_fuel_fail_h is None:
                first_fuel_fail_h = h
                first_fuel_fail_ts = ts

            # 5. Dependable generation failure: dependable reserve < 0
            if state.resilience and state.resilience.dependable_reserve_kw < -1e-4 and first_gen_fail_h is None:
                first_gen_fail_h = h
                first_gen_fail_ts = ts

            # 6. Reserve margin violation: dependable reserve % < reserve_threat_pct
            if state.resilience and state.resilience.dependable_reserve_pct < reserve_threat_pct and first_reserve_viol_h is None:
                first_reserve_viol_h = h
                first_reserve_viol_ts = ts

            # 7. Battery warning threshold: SOC <= battery_warning_soc
            if state.battery.soc_pct <= battery_warning_soc + 1e-4 and first_bat_warn_h is None:
                first_bat_warn_h = h
                first_bat_warn_ts = ts

            # 8. Resupply gap vulnerability:
            # If resupply is scheduled and remaining fuel drops below critical buffer before delivery
            if hasattr(state, "resupply") and state.resupply and state.resupply.resupply_event_active:
                if state.fuel.fuel_remaining_l <= fuel_reserve_liters * 0.5:
                    if first_resupply_vuln_h is None:
                        first_resupply_vuln_h = h
                        first_resupply_vuln_ts = ts

            # 9. Overall critical state:
            # Triggered if critical load fails, thermal fails, fuel hits reserve, or twin threat_state is CRITICAL
            is_critical = (
                (state.loads.unserved_critical_kw > 1e-4) or
                (state.thermal.indoor_temperature_c < min_safe_temp - 1e-4) or
                (state.fuel.fuel_remaining_l <= fuel_reserve_liters) or
                (state.resilience and state.resilience.threat_state == "CRITICAL")
            )
            if is_critical and first_overall_crit_h is None:
                first_overall_crit_h = h
                first_overall_crit_ts = ts

        # Synthesize Subsystem Horizons (bounded by total_horizon_h)
        h_crit = first_crit_fail_h if first_crit_fail_h is not None else total_horizon_h
        h_therm = first_therm_fail_h if first_therm_fail_h is not None else total_horizon_h
        h_bat = first_bat_fail_h if first_bat_fail_h is not None else total_horizon_h
        h_fuel = first_fuel_fail_h if first_fuel_fail_h is not None else total_horizon_h
        h_gen = first_gen_fail_h if first_gen_fail_h is not None else total_horizon_h
        h_resupply = first_resupply_vuln_h if first_resupply_vuln_h is not None else total_horizon_h

        # Find overall binding horizon
        horizon_candidates = [
            (h_crit, "CRITICAL_LOAD"),
            (h_therm, "THERMAL"),
            (h_bat, "BATTERY"),
            (h_fuel, "FUEL"),
            (h_gen, "GENERATION"),
            (h_resupply, "RESUPPLY")
        ]

        # Minimum binding horizon
        min_h, binding_subsystem = min(horizon_candidates, key=lambda x: x[0])
        survives_full = (min_h >= total_horizon_h) and (first_crit_fail_h is None) and (first_therm_fail_h is None)

        if survives_full:
            binding_subsystem = "NONE"

        survival_horizons = SurvivalHorizons(
            critical_load_survival_horizon_h=h_crit,
            thermal_habitability_horizon_h=h_therm,
            battery_endurance_horizon_h=h_bat,
            fuel_endurance_horizon_h=h_fuel,
            dependable_generation_horizon_h=h_gen,
            resupply_gap_survivability_h=h_resupply,
            overall_station_survival_horizon_h=min_h,
            binding_subsystem=binding_subsystem,
            survives_full_horizon=survives_full
        )

        time_to_threat = TimeToThreat(
            time_to_reserve_violation_h=first_reserve_viol_h,
            time_to_reserve_violation_timestamp=first_reserve_viol_ts,
            time_to_battery_terminal_threshold_h=first_bat_warn_h,
            time_to_battery_terminal_threshold_timestamp=first_bat_warn_ts,
            time_to_fuel_threshold_h=first_fuel_fail_h,
            time_to_fuel_threshold_timestamp=first_fuel_fail_ts,
            time_to_thermal_safety_threshold_h=first_therm_fail_h,
            time_to_thermal_safety_threshold_timestamp=first_therm_fail_ts,
            time_to_critical_load_failure_h=first_crit_fail_h,
            time_to_critical_load_failure_timestamp=first_crit_fail_ts,
            time_to_resupply_related_vulnerability_h=first_resupply_vuln_h,
            time_to_resupply_related_vulnerability_timestamp=first_resupply_vuln_ts,
            time_to_overall_critical_state_h=first_overall_crit_h,
            time_to_overall_critical_state_timestamp=first_overall_crit_ts
        )

        return survival_horizons, time_to_threat
