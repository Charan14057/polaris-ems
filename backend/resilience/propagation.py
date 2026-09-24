"""
POLARIS-EMS — Failure Propagation Chain Analyzer
SIH26061: Polar Energy Management & Resilience System

Identifies and traces causal failure cascades directly from observed state transitions:
Environmental Stress → Renewable Shortfall → Storage Discharge → Reserve Erosion → Thermal Vulnerability → Critical Deficit

Enforces Guardrail 15:
- Derives propagation strictly from observed numerical state transitions.
- Zero manufactured or fictional narratives.
"""

from typing import List, Optional
from backend.twin.state import TwinState
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.data.station_profiles.loader import StationProfile
from backend.resilience.schema import FailurePropagationStep, FailureSeverityEnum


class FailurePropagationAnalyzer:
    """Detects and constructs traceable causal failure chains from trajectory transitions."""

    def __init__(self, profile: StationProfile, safety_registry: SafetyThresholdRegistry):
        self.profile = profile
        self.safety_registry = safety_registry

    def trace_propagation(self, states: List[TwinState]) -> List[FailurePropagationStep]:
        """
        Analyzes chronological transitions across subsystems to detect causal failure propagation.
        """
        steps: List[FailurePropagationStep] = []
        if len(states) < 2:
            return steps

        sid = self.profile.station_id.upper()
        min_safe_temp = self.safety_registry.get_value(sid, "indoor_min_safe_temp_c", default=12.0)
        fuel_reserve_l = self.safety_registry.get_value(sid, "fuel_reserve_liters", default=25000.0)

        # State transition flags to prevent redundant chain duplication
        env_flag = False
        renew_flag = False
        bat_flag = False
        res_flag = False
        therm_flag = False
        crit_flag = False

        step_counter = 1

        for idx in range(len(states)):
            curr = states[idx]
            prev = states[idx - 1] if idx > 0 else curr
            ts = curr.timestamp

            # 1. Environmental Stress Trigger
            if not env_flag:
                if curr.environment.ambient_temperature_c <= -30.0 or curr.environment.wind_speed_ms >= 20.0:
                    env_flag = True
                    desc = f"Ambient temp {curr.environment.ambient_temperature_c:.1f} °C, wind {curr.environment.wind_speed_ms:.1f} m/s"
                    steps.append(FailurePropagationStep(
                        step_number=step_counter,
                        timestamp=ts,
                        trigger="Extreme polar environmental stress onset",
                        affected_subsystem="ENVIRONMENT",
                        observed_state_change=desc,
                        severity=FailureSeverityEnum.WARNING,
                        resulting_constraint="Elevated thermal heat loss and windchill hazard",
                        possible_recovery_opportunity="Activate auxiliary shelter insulation and prep trace heating"
                    ))
                    step_counter += 1

            # 2. Renewable Shortfall
            if not renew_flag and env_flag:
                renew_gen = curr.solar.solar_generation_kw + curr.wind.wind_generation_kw
                prev_renew = prev.solar.solar_generation_kw + prev.wind.wind_generation_kw
                if renew_gen < 5.0 and (prev_renew >= 5.0 or curr.solar.solar_status == "NIGHT"):
                    renew_flag = True
                    steps.append(FailurePropagationStep(
                        step_number=step_counter,
                        timestamp=ts,
                        trigger="Renewable generation dropped near zero",
                        affected_subsystem="RENEWABLES",
                        observed_state_change=f"Total renewable output fell to {renew_gen:.1f} kW",
                        severity=FailureSeverityEnum.INFO,
                        resulting_constraint="Station power deficit shifting to storage and thermal generators",
                        possible_recovery_opportunity="Commit standby generator or shift non-critical loads"
                    ))
                    step_counter += 1

            # 3. Storage Discharge & Depletion
            if not bat_flag and (curr.battery.soc_pct <= 0.30 or (curr.battery.discharge_kw > 10.0 and curr.battery.soc_pct < prev.battery.soc_pct)):
                if curr.battery.soc_pct <= 0.25:
                    bat_flag = True
                    steps.append(FailurePropagationStep(
                        step_number=step_counter,
                        timestamp=ts,
                        trigger="Battery storage depleted to warning envelope",
                        affected_subsystem="BATTERY",
                        observed_state_change=f"SOC dropped to {curr.battery.soc_pct * 100:.1f}% (discharging at {curr.battery.discharge_kw:.1f} kW)",
                        severity=FailureSeverityEnum.WARNING,
                        resulting_constraint="Loss of storage discharge capacity and buffer margin",
                        possible_recovery_opportunity="Throttle battery discharge by starting secondary diesel generator"
                    ))
                    step_counter += 1

            # 4. Reserve Margin Erosion
            if not res_flag and curr.resilience and curr.resilience.dependable_reserve_pct < 15.0:
                res_flag = True
                steps.append(FailurePropagationStep(
                    step_number=step_counter,
                    timestamp=ts,
                    trigger="Dependable reserve margin collapsed below high-risk threshold",
                    affected_subsystem="GENERATION",
                    observed_state_change=f"Operating reserve fell to {curr.resilience.dependable_reserve_pct:.1f}% ({curr.resilience.dependable_reserve_kw:.1f} kW)",
                    severity=FailureSeverityEnum.WARNING,
                    resulting_constraint="Single-contingency vulnerability (N-1 deficit)",
                    possible_recovery_opportunity="Immediately start standby diesel generator to restore spinning reserve"
                ))
                step_counter += 1

            # 5. Thermal Vulnerability
            if not therm_flag and (curr.thermal.indoor_temperature_c - min_safe_temp) < 2.0:
                therm_flag = True
                sev = FailureSeverityEnum.CRITICAL if curr.thermal.indoor_temperature_c < min_safe_temp else FailureSeverityEnum.WARNING
                steps.append(FailurePropagationStep(
                    step_number=step_counter,
                    timestamp=ts,
                    trigger="Shelter indoor temperature approaching/breaching safe limit",
                    affected_subsystem="THERMAL",
                    observed_state_change=f"Indoor temperature reached {curr.thermal.indoor_temperature_c:.1f} °C (safe limit {min_safe_temp:.1f} °C)",
                    severity=sev,
                    resulting_constraint="Pipe freeze risk and life-safety habitability hazard",
                    possible_recovery_opportunity="Prioritize electric heating dispatch and protect trace heating coils"
                ))
                step_counter += 1

            # 6. Critical Load Unserved
            if not crit_flag and curr.loads.unserved_critical_kw > 1e-4:
                crit_flag = True
                steps.append(FailurePropagationStep(
                    step_number=step_counter,
                    timestamp=ts,
                    trigger="Critical life-safety load unserved",
                    affected_subsystem="LOADS",
                    observed_state_change=f"{curr.loads.unserved_critical_kw:.2f} kW unserved critical load",
                    severity=FailureSeverityEnum.CRITICAL,
                    resulting_constraint="Mission critical survival constraint breached",
                    possible_recovery_opportunity="Emergency load shed of all non-critical circuits immediately"
                ))
                step_counter += 1

        return steps
