"""
POLARIS-EMS — Threat Decomposition & Deterministic Resilience State Machine
SIH26061: Polar Energy Management & Resilience System

Implements:
- Threat Decomposition across all canonical environmental & operational hazards
- Deterministic State Machine with explicit severity precedence:
    CRITICAL > THREATENED > AT_RISK > WATCH > RECOVERY > SAFE
- History-Aware RECOVERY State Transition Logic (Guardrail 4)
- Multi-threat trigger preservation (Guardrail 6: all fired triggers exposed)
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from backend.twin.state import TwinState
from backend.data.station_profiles.loader import StationProfile
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.scenarios.schema import ScenarioDefinition
from backend.resilience.schema import (
    ResilienceStateEnum,
    ResilienceThreatEnum,
    FailureSeverityEnum,
    ThreatIndicator,
    SurvivalHorizons
)


class ThreatAndStateMachine:
    """Evaluates physical threat drivers and executes deterministic state transitions."""

    def __init__(
        self,
        profile: StationProfile,
        safety_registry: SafetyThresholdRegistry
    ):
        self.profile = profile
        self.safety_registry = safety_registry

    def decompose_threats(
        self,
        states: List[TwinState],
        scenario: Optional[ScenarioDefinition] = None
    ) -> List[ThreatIndicator]:
        """
        Scans trajectory states to detect all active threat indicators with provenance.
        """
        threats: List[ThreatIndicator] = []
        seen_threats: Set[ResilienceThreatEnum] = set()

        sid = self.profile.station_id.upper()
        min_safe_temp = self.safety_registry.get_value(sid, "indoor_min_safe_temp_c", default=12.0)
        fuel_reserve_l = self.safety_registry.get_value(sid, "fuel_reserve_liters", default=25000.0)

        for idx, s in enumerate(states):
            h = idx + 1
            ts = s.timestamp

            # 1. Extreme Cold
            if s.environment.ambient_temperature_c <= -35.0 and ResilienceThreatEnum.EXTREME_COLD not in seen_threats:
                threats.append(ThreatIndicator(
                    threat_type=ResilienceThreatEnum.EXTREME_COLD,
                    severity=FailureSeverityEnum.CRITICAL if s.environment.ambient_temperature_c <= -45.0 else FailureSeverityEnum.WARNING,
                    trigger_condition=f"Ambient temperature {s.environment.ambient_temperature_c:.1f} °C <= -35.0 °C",
                    affected_subsystems=["THERMAL", "LOADS", "BATTERY"],
                    first_observed_timestep=ts,
                    first_observed_hour=float(h)
                ))
                seen_threats.add(ResilienceThreatEnum.EXTREME_COLD)

            # 2. Polar Night / Low Daylight
            if s.environment.solar_elevation_deg < 0.0 and s.environment.irradiance_wm2 <= 0.1 and ResilienceThreatEnum.POLAR_NIGHT not in seen_threats:
                threats.append(ThreatIndicator(
                    threat_type=ResilienceThreatEnum.POLAR_NIGHT,
                    severity=FailureSeverityEnum.INFO,
                    trigger_condition="Sub-horizon solar elevation (Continuous Polar Night)",
                    affected_subsystems=["SOLAR", "ELECTRICAL"],
                    first_observed_timestep=ts,
                    first_observed_hour=float(h)
                ))
                seen_threats.add(ResilienceThreatEnum.POLAR_NIGHT)

            # 3. Generator Outage (Fault)
            if s.diesel.generator_status == "FAULT" and ResilienceThreatEnum.GENERATOR_OUTAGE not in seen_threats:
                threats.append(ThreatIndicator(
                    threat_type=ResilienceThreatEnum.GENERATOR_OUTAGE,
                    severity=FailureSeverityEnum.CRITICAL,
                    trigger_condition="Primary diesel generator trip/fault detected",
                    affected_subsystems=["DIESEL", "GENERATION", "ELECTRICAL"],
                    first_observed_timestep=ts,
                    first_observed_hour=float(h)
                ))
                seen_threats.add(ResilienceThreatEnum.GENERATOR_OUTAGE)

            # 4. Maintenance Loss
            if s.diesel.generator_status == "MAINTENANCE" and ResilienceThreatEnum.MAINTENANCE_AVAILABILITY_LOSS not in seen_threats:
                threats.append(ThreatIndicator(
                    threat_type=ResilienceThreatEnum.MAINTENANCE_AVAILABILITY_LOSS,
                    severity=FailureSeverityEnum.WARNING,
                    trigger_condition="Generator scheduled maintenance active (unit unavailable)",
                    affected_subsystems=["DIESEL", "GENERATION"],
                    first_observed_timestep=ts,
                    first_observed_hour=float(h)
                ))
                seen_threats.add(ResilienceThreatEnum.MAINTENANCE_AVAILABILITY_LOSS)

            # 5. Solar Generation Failure (Zero solar with high GHI)
            if s.solar.solar_status == "FAULT" or (s.environment.irradiance_wm2 > 100.0 and s.solar.solar_generation_kw <= 0.01):
                if ResilienceThreatEnum.SOLAR_FAILURE not in seen_threats:
                    threats.append(ThreatIndicator(
                        threat_type=ResilienceThreatEnum.SOLAR_FAILURE,
                        severity=FailureSeverityEnum.WARNING,
                        trigger_condition="Solar PV array failure (zero power under positive irradiance)",
                        affected_subsystems=["SOLAR", "RENEWABLES"],
                        first_observed_timestep=ts,
                        first_observed_hour=float(h)
                    ))
                    seen_threats.add(ResilienceThreatEnum.SOLAR_FAILURE)

            # 6. Wind Generation Failure (Zero wind power with operating wind speed 4-25 m/s)
            if s.wind.wind_status == "FAULT" or (4.0 <= s.environment.wind_speed_ms <= 25.0 and s.wind.wind_generation_kw <= 0.01):
                if ResilienceThreatEnum.WIND_FAILURE not in seen_threats:
                    threats.append(ThreatIndicator(
                        threat_type=ResilienceThreatEnum.WIND_FAILURE,
                        severity=FailureSeverityEnum.WARNING,
                        trigger_condition="Wind turbine cut-out/mechanical fault (zero generation under 4-25 m/s wind)",
                        affected_subsystems=["WIND", "RENEWABLES"],
                        first_observed_timestep=ts,
                        first_observed_hour=float(h)
                    ))
                    seen_threats.add(ResilienceThreatEnum.WIND_FAILURE)

            # 7. Battery Derating / Depletion
            if s.battery.soc_pct <= 0.25 and ResilienceThreatEnum.BATTERY_DERATING not in seen_threats:
                threats.append(ThreatIndicator(
                    threat_type=ResilienceThreatEnum.BATTERY_DERATING,
                    severity=FailureSeverityEnum.CRITICAL if s.battery.soc_pct <= 0.20 else FailureSeverityEnum.WARNING,
                    trigger_condition=f"Battery SOC ({s.battery.soc_pct * 100:.1f}%) <= 25% warning threshold",
                    affected_subsystems=["BATTERY", "STORAGE"],
                    first_observed_timestep=ts,
                    first_observed_hour=float(h)
                ))
                seen_threats.add(ResilienceThreatEnum.BATTERY_DERATING)

            # 8. Fuel Shortage
            if s.fuel.fuel_remaining_l <= fuel_reserve_l and ResilienceThreatEnum.FUEL_SHORTAGE not in seen_threats:
                threats.append(ThreatIndicator(
                    threat_type=ResilienceThreatEnum.FUEL_SHORTAGE,
                    severity=FailureSeverityEnum.CRITICAL,
                    trigger_condition=f"Fuel remaining ({s.fuel.fuel_remaining_l:.0f} L) <= {fuel_reserve_l:.0f} L emergency reserve",
                    affected_subsystems=["FUEL", "LOGISTICS"],
                    first_observed_timestep=ts,
                    first_observed_hour=float(h)
                ))
                seen_threats.add(ResilienceThreatEnum.FUEL_SHORTAGE)

            # 9. Reserve Erosion
            if s.resilience and s.resilience.dependable_reserve_pct < 15.0 and ResilienceThreatEnum.RESERVE_EROSION not in seen_threats:
                threats.append(ThreatIndicator(
                    threat_type=ResilienceThreatEnum.RESERVE_EROSION,
                    severity=FailureSeverityEnum.CRITICAL if s.resilience.dependable_reserve_pct < 0.0 else FailureSeverityEnum.WARNING,
                    trigger_condition=f"Dependable reserve ({s.resilience.dependable_reserve_pct:.1f}%) < 15% high-risk threshold",
                    affected_subsystems=["GENERATION", "BATTERY", "ELECTRICAL"],
                    first_observed_timestep=ts,
                    first_observed_hour=float(h)
                ))
                seen_threats.add(ResilienceThreatEnum.RESERVE_EROSION)

            # 10. Thermal Stress
            if (s.thermal.indoor_temperature_c - min_safe_temp) < 2.0 and ResilienceThreatEnum.THERMAL_STRESS not in seen_threats:
                threats.append(ThreatIndicator(
                    threat_type=ResilienceThreatEnum.THERMAL_STRESS,
                    severity=FailureSeverityEnum.CRITICAL if s.thermal.indoor_temperature_c < min_safe_temp else FailureSeverityEnum.WARNING,
                    trigger_condition=f"Indoor temperature ({s.thermal.indoor_temperature_c:.1f} °C) within 2.0 °C of safe limit ({min_safe_temp:.1f} °C)",
                    affected_subsystems=["THERMAL", "HEATING"],
                    first_observed_timestep=ts,
                    first_observed_hour=float(h)
                ))
                seen_threats.add(ResilienceThreatEnum.THERMAL_STRESS)

            # 11. Combined Polar Stress (Extreme cold + high wind + high load)
            if (s.environment.ambient_temperature_c <= -30.0 and s.environment.wind_speed_ms >= 20.0):
                if ResilienceThreatEnum.COMBINED_POLAR_STRESS not in seen_threats:
                    threats.append(ThreatIndicator(
                        threat_type=ResilienceThreatEnum.COMBINED_POLAR_STRESS,
                        severity=FailureSeverityEnum.CRITICAL,
                        trigger_condition="Compound blizzard & extreme windchill stress (Temp <= -30 °C, Wind >= 20 m/s)",
                        affected_subsystems=["ENVIRONMENT", "THERMAL", "ELECTRICAL", "WIND"],
                        first_observed_timestep=ts,
                        first_observed_hour=float(h)
                    ))
                    seen_threats.add(ResilienceThreatEnum.COMBINED_POLAR_STRESS)

        # Check scenario definition lineage for logistical threats
        if scenario:
            for pt in getattr(scenario, "transforms", []):
                if pt.parameter == "resupply_delay_hours" and int(pt.value) > 0 and ResilienceThreatEnum.RESUPPLY_DELAY not in seen_threats:
                    threats.append(ThreatIndicator(
                        threat_type=ResilienceThreatEnum.RESUPPLY_DELAY,
                        severity=FailureSeverityEnum.WARNING,
                        trigger_condition=f"Convoy delivery delayed by {pt.value} hours",
                        affected_subsystems=["LOGISTICS", "FUEL"],
                        provenance="CONFIGURED"
                    ))
                    seen_threats.add(ResilienceThreatEnum.RESUPPLY_DELAY)

        return threats

    def classify_state(
        self,
        states: List[TwinState],
        survival: SurvivalHorizons,
        threats: List[ThreatIndicator],
        previous_state: Optional[ResilienceStateEnum] = None
    ) -> Tuple[ResilienceStateEnum, List[ResilienceStateEnum], Optional[str]]:
        """
        Executes the deterministic state machine.
        Severity Precedence:
            CRITICAL > THREATENED > AT_RISK > WATCH > RECOVERY > SAFE
        
        Returns:
            (selected_state, all_active_states, recovery_direction)
        """
        sid = self.profile.station_id.upper()
        min_safe_temp = self.safety_registry.get_value(sid, "indoor_min_safe_temp_c", default=12.0)
        fuel_reserve_l = self.safety_registry.get_value(sid, "fuel_reserve_liters", default=25000.0)

        active_states: List[ResilienceStateEnum] = []

        # 1. Evaluate CRITICAL triggers
        has_critical = (
            survival.critical_load_survival_horizon_h < len(states) or
            survival.thermal_habitability_horizon_h < len(states) or
            any(s.loads.unserved_critical_kw > 1e-4 for s in states) or
            any(s.thermal.indoor_temperature_c < min_safe_temp for s in states) or
            any(s.fuel.fuel_remaining_l <= fuel_reserve_l for s in states) or
            (not survival.survives_full_horizon and survival.overall_station_survival_horizon_h <= 24.0) or
            any(s.diesel.generator_status == "FAULT" for s in states)
        )
        if has_critical:
            active_states.append(ResilienceStateEnum.CRITICAL)

        # 2. Evaluate THREATENED triggers
        has_threatened = (
            any(s.resilience and s.resilience.dependable_reserve_pct < 15.0 for s in states) or
            any(s.battery.soc_pct <= 0.25 for s in states) or
            (not survival.survives_full_horizon and survival.overall_station_survival_horizon_h <= 72.0) or
            any(s.loads.unserved_non_critical_kw > 1e-4 for s in states) or
            any((s.thermal.indoor_temperature_c - min_safe_temp) < 2.0 for s in states) or
            any(s.environment.wind_speed_ms >= 28.0 for s in states)
        )
        if has_threatened:
            active_states.append(ResilienceStateEnum.THREATENED)

        # 3. Evaluate AT_RISK triggers
        has_at_risk = (
            any(s.resilience and s.resilience.dependable_reserve_pct < 30.0 for s in states) or
            any(s.fuel.days_of_fuel_remaining < 30.0 for s in states) or
            any(s.environment.ambient_temperature_c <= -35.0 for s in states) or
            any(s.diesel.generator_power_kw >= 0.85 * s.diesel.generator_max_power_kw for s in states) or
            any(t.threat_type in (ResilienceThreatEnum.SOLAR_FAILURE, ResilienceThreatEnum.WIND_FAILURE) for t in threats)
        )
        if has_at_risk:
            active_states.append(ResilienceStateEnum.AT_RISK)

        # 4. Evaluate WATCH triggers
        has_watch = (
            any(s.environment.ambient_temperature_c <= -25.0 for s in states) or
            any(s.environment.wind_speed_ms >= 20.0 for s in states) or
            any(s.diesel.generator_status == "MAINTENANCE" for s in states) or
            any(t.threat_type == ResilienceThreatEnum.RESUPPLY_DELAY for t in threats)
        )
        if has_watch:
            active_states.append(ResilienceStateEnum.WATCH)

        # 5. Evaluate History-Aware RECOVERY triggers (Guardrail 4)
        recovery_direction: Optional[str] = None
        has_recovery = False
        if previous_state in (ResilienceStateEnum.CRITICAL, ResilienceStateEnum.THREATENED):
            # Must no longer meet CRITICAL or THREATENED triggering conditions
            if not has_critical and not has_threatened:
                # Check measurable restoration
                initial_s = states[0]
                final_s = states[-1]

                delta_soc = final_s.battery.soc_pct - initial_s.battery.soc_pct
                delta_temp = final_s.thermal.indoor_temperature_c - initial_s.thermal.indoor_temperature_c
                init_res = initial_s.resilience.dependable_reserve_pct if initial_s.resilience else 0.0
                final_res = final_s.resilience.dependable_reserve_pct if final_s.resilience else 0.0
                delta_res = final_res - init_res

                if delta_res > 5.0:
                    has_recovery = True
                    recovery_direction = f"RESERVES_RESTORING (+{delta_res:.1f}%)"
                elif delta_soc > 0.05:
                    has_recovery = True
                    recovery_direction = f"STORAGE_RECHARGING (+{delta_soc * 100:.1f}%)"
                elif delta_temp > 1.0:
                    has_recovery = True
                    recovery_direction = f"THERMAL_WARMING (+{delta_temp:.1f} °C)"
                else:
                    has_recovery = True
                    recovery_direction = "DEFICIT_RESOLVED_STABILIZING"

                if has_recovery:
                    active_states.append(ResilienceStateEnum.RECOVERY)

        # 6. Evaluate SAFE triggers
        if not has_critical and not has_threatened and not has_at_risk and not has_watch and not has_recovery:
            active_states.append(ResilienceStateEnum.SAFE)

        # Apply deterministic severity precedence:
        # CRITICAL > THREATENED > AT_RISK > WATCH > RECOVERY > SAFE
        precedence = [
            ResilienceStateEnum.CRITICAL,
            ResilienceStateEnum.THREATENED,
            ResilienceStateEnum.AT_RISK,
            ResilienceStateEnum.WATCH,
            ResilienceStateEnum.RECOVERY,
            ResilienceStateEnum.SAFE
        ]

        selected_state = ResilienceStateEnum.SAFE
        for p_state in precedence:
            if p_state in active_states:
                selected_state = p_state
                break

        return selected_state, active_states, recovery_direction
