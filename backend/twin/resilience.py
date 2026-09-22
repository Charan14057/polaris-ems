"""
POLARIS-EMS — Digital Twin Resilience & Threat Engine
SIH26061: Polar Energy Management & Resilience System

Evaluates station survivability, operating reserve margins, and threat states:
- Dependable reserve margin: distinguishes nameplate vs dependable vs fuel-constrained reserves
- Critical load survival: strict boolean and status tracking (fails if unserved critical > 0 or temp < safe)
- Continuity horizon: minimum time to fuel, battery, or thermal safe limit breach
- Threat state classification: SAFE, AT_RISK, THREATENED, CRITICAL with clear triggering conditions
"""

from typing import Dict, Any, List, Literal, Tuple
import math

from backend.twin.state import TwinState, ResilienceState
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.data.station_profiles.loader import StationProfile


class ResilienceEngine:
    """Computes reserve margins, survival horizons, and polar threat states."""

    def __init__(
        self,
        profile: StationProfile,
        safety_registry: SafetyThresholdRegistry
    ):
        self.profile = profile
        self.safety_registry = safety_registry

    def evaluate_resilience(
        self,
        state: TwinState,
        dt_hours: float = 1.0,
        temp_rate_c_per_h: float = 0.0
    ) -> ResilienceState:
        """
        Calculates all reserve metrics, continuity horizons, and threat classifications.
        """
        sid = state.station_id.upper()
        p_load = max(0.01, state.loads.total_load_kw)

        # 1. Nameplate Reserve
        # Total installed generator capacity + nameplate battery discharge - current load
        p_diesel_rated = float(self.profile.electrical.diesel_generator_kw_rated)
        p_bat_rated_dis = float(self.profile.electrical.battery_max_discharge_kw)
        nameplate_reserve_kw = round((p_diesel_rated + p_bat_rated_dis) - p_load, 2)

        # 2. Dependable Reserve
        # Available online/standby generator headroom + usable battery discharge power - unserved load
        diesel_headroom = 0.0
        if state.diesel.generator_status in ("ONLINE", "STANDBY"):
            diesel_headroom = max(0.0, state.diesel.generator_max_power_kw - state.diesel.generator_power_kw)

        # Usable battery power constrained by SOC > SOC_min and cold derating
        usable_bat_dis_kw = 0.0
        if state.battery.soc_pct > state.battery.soc_min:
            # Energy available above minimum cutoff
            soc_headroom = state.battery.soc_pct - state.battery.soc_min
            usable_energy_kwh = soc_headroom * state.battery.usable_capacity_kwh
            # Maximum instantaneous deliverable discharge over 1 hour
            max_dis_rate = usable_energy_kwh * state.battery.discharge_efficiency / max(0.01, dt_hours)
            deliverable_dis_kw = min(state.battery.max_discharge_kw, max_dis_rate)
            usable_bat_dis_kw = max(0.0, deliverable_dis_kw - state.battery.discharge_power_kw)

        if state.loads.unserved_total_kw > 1e-4:
            # Under active deficit, dependable reserve is negative by the unserved deficit
            dependable_reserve_kw = -round(state.loads.unserved_total_kw, 2)
        else:
            dependable_reserve_kw = round(diesel_headroom + usable_bat_dis_kw, 2)

        dependable_reserve_pct = round((dependable_reserve_kw / p_load) * 100.0, 1)

        # 3. Fuel-Constrained Reserve
        # If remaining fuel is zero, diesel headroom is zero.
        # If remaining fuel is at or below emergency reserve, diesel reserve is penalised
        fuel_reserve_l = self.safety_registry.get_value(sid, "fuel_reserve_liters", default=25000.0)
        fuel_rem = state.fuel.fuel_remaining_l

        if fuel_rem <= 0.01:
            fuel_constrained_reserve_kw = round(usable_bat_dis_kw - state.loads.unserved_total_kw, 2)
        elif fuel_rem < fuel_reserve_l:
            fraction = max(0.0, fuel_rem / max(1.0, fuel_reserve_l))
            fuel_constrained_reserve_kw = round(
                (diesel_headroom * fraction) + usable_bat_dis_kw - state.loads.unserved_total_kw,
                2
            )
        else:
            fuel_constrained_reserve_kw = dependable_reserve_kw

        # 4. Critical Load Survival Status
        # Must be SURVIVED only if unserved critical energy is 0 AND indoor temp > min safe limit
        min_safe_temp = self.safety_registry.get_value(sid, "indoor_min_safe_temp_c", default=12.0)
        indoor_temp = state.thermal.indoor_temp_c
        critical_unserved = state.loads.unserved_critical_kw

        if critical_unserved > 1e-4 or indoor_temp < min_safe_temp:
            survival_status: Literal["SURVIVED", "FAILED"] = "FAILED"
        else:
            survival_status = "SURVIVED"

        # 5. Continuity Horizon
        continuity_hours, binding_constraint = self._calculate_continuity_horizon(
            state, min_safe_temp, temp_rate_c_per_h
        )

        # 6. Threat State Classification
        threat_state = self._classify_threat_state(
            state=state,
            survival_status=survival_status,
            dependable_reserve_pct=dependable_reserve_pct,
            fuel_rem=fuel_rem,
            fuel_reserve_l=fuel_reserve_l,
            continuity_hours=continuity_hours,
            min_safe_temp=min_safe_temp
        )

        return ResilienceState(
            nameplate_reserve_kw=nameplate_reserve_kw,
            dependable_reserve_kw=dependable_reserve_kw,
            dependable_reserve_pct=dependable_reserve_pct,
            fuel_constrained_reserve_kw=fuel_constrained_reserve_kw,
            critical_load_survival_status=survival_status,
            continuity_horizon_hours=continuity_hours,
            threat_state=threat_state,
            provenance="SIMULATED"
        )

    def _calculate_continuity_horizon(
        self,
        state: TwinState,
        min_safe_temp: float,
        temp_rate_c_per_h: float
    ) -> Tuple[float, str]:
        """Calculates time until fuel exhaustion, battery exhaustion, or thermal limit breach."""
        horizons = []

        # A. Fuel continuity
        burn_rate = state.diesel.fuel_consumption_l_per_h
        if burn_rate > 0.01:
            fuel_hours = state.fuel.fuel_remaining_l / burn_rate
        else:
            # If generator is standby, estimate baseline 12 L/h standby/emergency burn
            fuel_hours = state.fuel.fuel_remaining_l / 12.0
        horizons.append((fuel_hours, "FUEL"))

        # B. Battery continuity
        # Battery exhaustion is a binding station failure only if diesel cannot pick up the load
        # (e.g. generator faulted, fuel exhausted, or load exceeds total generator rating).
        diesel_headroom = 0.0
        if state.diesel.generator_status in ("ONLINE", "STANDBY") and state.fuel.fuel_remaining_l > 0.01:
            diesel_headroom = max(0.0, state.diesel.generator_max_power_kw - state.diesel.generator_power_kw)

        if state.battery.discharge_power_kw > 0.01:
            usable_energy = max(0.0, (state.battery.soc_pct - state.battery.soc_min) * state.battery.usable_capacity_kwh)
            dis_rate = state.battery.discharge_power_kw / max(0.01, state.battery.discharge_efficiency)
            bat_hours = usable_energy / max(0.01, dis_rate)
            if diesel_headroom < (state.battery.discharge_power_kw - 0.01):
                # Diesel cannot cover the battery deficit when battery exhausts -> binding blackout horizon!
                horizons.append((bat_hours, "BATTERY"))
            else:
                # Diesel has sufficient headroom to take over when battery reaches SOC_min
                horizons.append((999.0, "BATTERY"))
        elif state.loads.unserved_total_kw > 1e-4 and state.battery.soc_pct <= state.battery.soc_min + 1e-4:
            horizons.append((0.0, "BATTERY"))
        else:
            horizons.append((999.0, "BATTERY"))

        # C. Thermal continuity
        indoor_temp = state.thermal.indoor_temp_c
        if indoor_temp <= min_safe_temp:
            horizons.append((0.0, "THERMAL"))
        elif temp_rate_c_per_h < -0.01:
            # Indoor temperature is dropping
            dt_to_breach = (indoor_temp - min_safe_temp) / abs(temp_rate_c_per_h)
            horizons.append((dt_to_breach, "THERMAL"))
        else:
            horizons.append((999.0, "THERMAL"))

        # Find minimum horizon
        min_h, binding = min(horizons, key=lambda x: x[0])
        min_h_clamped = round(max(0.0, min(999.0, min_h)), 1)
        return min_h_clamped, binding

    def _classify_threat_state(
        self,
        state: TwinState,
        survival_status: str,
        dependable_reserve_pct: float,
        fuel_rem: float,
        fuel_reserve_l: float,
        continuity_hours: float,
        min_safe_temp: float
    ) -> Literal["SAFE", "AT_RISK", "THREATENED", "CRITICAL"]:
        """
        Classifies current station status into SAFE, AT_RISK, THREATENED, or CRITICAL.
        """
        sid = state.station_id.upper()
        reserve_threat_pct = self.safety_registry.get_value(sid, "reserve_margin_threatened_pct", default=15.0)
        reserve_warn_pct = self.safety_registry.get_value(sid, "reserve_margin_warning_pct", default=30.0)
        cont_crit_hours = self.safety_registry.get_value(sid, "continuity_critical_hours", default=24.0)
        cont_warn_hours = self.safety_registry.get_value(sid, "continuity_warning_hours", default=72.0)
        bat_warn_soc = self.safety_registry.get_value(sid, "battery_warning_soc", default=0.25)

        # 1. CRITICAL
        if (
            survival_status == "FAILED"
            or state.loads.unserved_critical_kw > 1e-4
            or state.thermal.indoor_temp_c < min_safe_temp
            or fuel_rem <= fuel_reserve_l
            or continuity_hours <= cont_crit_hours
            or state.diesel.generator_status == "FAULT"
        ):
            return "CRITICAL"

        # 2. THREATENED
        if (
            dependable_reserve_pct < reserve_threat_pct
            or state.battery.soc_pct <= bat_warn_soc
            or continuity_hours <= cont_warn_hours
            or state.loads.unserved_non_critical_kw > 1e-4
            or (state.thermal.indoor_temp_c - min_safe_temp) < 2.0
            or state.environment.wind_speed_ms >= 28.0
        ):
            return "THREATENED"

        # 3. AT_RISK
        if (
            dependable_reserve_pct < reserve_warn_pct
            or state.fuel.days_of_fuel_remaining < 30.0
            or state.environment.temperature_c <= -35.0
            or state.diesel.generator_power_kw >= 0.85 * state.diesel.generator_max_power_kw
        ):
            return "AT_RISK"

        # 4. SAFE
        return "SAFE"

    def get_threat_diagnostics(
        self,
        state: TwinState,
        resilience: ResilienceState
    ) -> Dict[str, Any]:
        """Provides operator justifications and SOP actions for the active threat state."""
        actions = []
        triggers = []

        if resilience.threat_state == "CRITICAL":
            triggers.append("Active deficit or critical survival constraint breach.")
            actions.extend([
                "IMMEDIATE: Shed all deferrable and non-critical station loads.",
                "Verify and force-start secondary diesel generator.",
                "Inspect trace heating and shelter thermal envelope integrity.",
                "Issue station emergency alert to expedition leader."
            ])
        elif resilience.threat_state == "THREATENED":
            triggers.append("Operating reserve below high-risk limit or approaching weather/storage cutoff.")
            actions.extend([
                "Curtail scheduled flexible scientific experiments and EV charging.",
                "Prepare standby diesel generator for immediate hot-start.",
                "Verify battery heating circuits to prevent sub-zero capacity loss."
            ])
        elif resilience.threat_state == "AT_RISK":
            triggers.append("Reserve margins tight or severe environmental cold front detected.")
            actions.extend([
                "Advise science teams of potential power restrictions.",
                "Monitor fuel burn curves against resupply calendar.",
                "Pre-heat backup generator blocks."
            ])
        else:
            triggers.append("All physical, electrical, and thermal parameters nominal.")
            actions.append("Continue routine baseline monitoring.")

        return {
            "station_id": state.station_id,
            "threat_state": resilience.threat_state,
            "critical_load_survival": resilience.critical_load_survival_status,
            "continuity_horizon_hours": resilience.continuity_horizon_hours,
            "dependable_reserve_pct": resilience.dependable_reserve_pct,
            "triggers": triggers,
            "recommended_actions": actions
        }
