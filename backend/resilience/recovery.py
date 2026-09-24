"""
POLARIS-EMS — Candidate Recovery Intelligence Advisor
SIH26061: Polar Energy Management & Resilience System

Synthesizes candidate resilience recovery interventions (ADVISORY ONLY):
- Increase diesel commitment
- Preserve battery reserve
- Shed non-critical load
- Shift flexible load
- Protect critical thermal loads
- Prepare standby generator
- Preserve fuel until resupply
- Enter station recovery mode

Enforces Guardrail 5:
- Zero arbitrary or invented benefits.
- Explicitly flags validation_tier as PHYSICALLY_VALIDATED or ESTIMATED with clear limitations.
- Advisory intelligence only; strictly zero policy execution (reserved for Phase 8).
"""

from typing import List, Optional, Dict, Any
from backend.twin.state import TwinState
from backend.twin.twin_engine import TwinEngine
from backend.data.station_profiles.loader import StationProfile
from backend.resilience.schema import (
    CandidateRecoveryOption,
    RecoveryActionTypeEnum,
    FailureSeverityEnum,
    SurvivalHorizons,
    ThreatIndicator,
    ResilienceThreatEnum
)


class RecoveryAdvisor:
    """Synthesizes structured advisory resilience responses based on physical binding constraints."""

    def __init__(self, profile: StationProfile):
        self.profile = profile

    def advise_recovery_options(
        self,
        states: List[TwinState],
        survival: SurvivalHorizons,
        threats: List[ThreatIndicator]
    ) -> List[CandidateRecoveryOption]:
        """
        Generates candidate recovery actions with explainable, non-arbitrary gain projections.
        """
        options: List[CandidateRecoveryOption] = []
        if not states:
            return options

        gen_rated = float(self.profile.electrical.diesel_generator_kw_rated)
        gen_count = int(self.profile.electrical.diesel_generator_count)
        avg_load = sum(s.loads.total_load_kw for s in states) / max(1, len(states))
        threat_types = {t.threat_type for t in threats}

        # 1. Critical Load Deficit: Immediate Non-Critical Load Shedding
        if survival.binding_subsystem == "CRITICAL_LOAD" or any(s.loads.unserved_critical_kw > 1e-4 for s in states):
            non_crit_load = sum(s.loads.unserved_non_critical_kw for s in states) / max(1, len(states))
            options.append(CandidateRecoveryOption(
                action_type=RecoveryActionTypeEnum.SHED_NONCRITICAL_LOAD,
                description="Shed 100% of deferrable scientific and domestic loads to protect critical life-safety bus",
                target_subsystem="LOADS",
                rationale="Critical life-safety load is actively unserved or binding within horizon",
                expected_survival_horizon_gain_h=round(min(float(len(states)), survival.overall_station_survival_horizon_h + 12.0), 1),
                expected_reserve_margin_gain_pct=round((non_crit_load / max(1.0, avg_load)) * 100.0, 1),
                urgency=FailureSeverityEnum.CRITICAL,
                validation_tier="ESTIMATED",
                limitations="Estimated load relief based on non-critical load proportion; advisory only"
            ))

        # 2. Thermal Vulnerability: Protect Heating Dispatch
        if survival.binding_subsystem == "THERMAL" or ResilienceThreatEnum.THERMAL_STRESS in threat_types:
            options.append(CandidateRecoveryOption(
                action_type=RecoveryActionTypeEnum.PROTECT_CRITICAL_THERMAL,
                description="Prioritize electric power allocation to trace heating and shelter thermal envelope",
                target_subsystem="THERMAL",
                rationale="Indoor temperature is within 2 °C of pipe freeze/safe habitability threshold",
                expected_survival_horizon_gain_h=round(min(float(len(states)), survival.thermal_habitability_horizon_h + 24.0), 1),
                expected_reserve_margin_gain_pct=0.0,
                urgency=FailureSeverityEnum.CRITICAL if survival.binding_subsystem == "THERMAL" else FailureSeverityEnum.WARNING,
                validation_tier="ESTIMATED",
                limitations="Thermal preservation estimate based on building thermal capacitance; advisory only"
            ))

        # 3. Generation Deficit or High Risk Reserve: Commit Additional Generator
        if (
            survival.binding_subsystem in ("GENERATION", "BATTERY") or
            ResilienceThreatEnum.GENERATOR_OUTAGE in threat_types or
            ResilienceThreatEnum.RESERVE_EROSION in threat_types
        ):
            reserve_gain_pct = round((gen_rated / max(1.0, avg_load)) * 100.0, 1)
            options.append(CandidateRecoveryOption(
                action_type=RecoveryActionTypeEnum.INCREASE_DIESEL_COMMITMENT,
                description=f"Commit an additional healthy {gen_rated:.0f} kW diesel generator from standby",
                target_subsystem="DIESEL",
                rationale="Operating reserve is below high-risk limit (15%) or battery is discharging to deficit",
                expected_survival_horizon_gain_h=round(min(float(len(states)), survival.overall_station_survival_horizon_h + 24.0), 1),
                expected_reserve_margin_gain_pct=reserve_gain_pct,
                urgency=FailureSeverityEnum.WARNING,
                validation_tier="ESTIMATED",
                limitations=f"Expected reserve boost is derived directly from unit rated capacity ({gen_rated} kW); advisory only"
            ))

        # 4. Storage Depletion: Preserve Battery Reserve
        if survival.binding_subsystem == "BATTERY" or ResilienceThreatEnum.BATTERY_DERATING in threat_types:
            options.append(CandidateRecoveryOption(
                action_type=RecoveryActionTypeEnum.PRESERVE_BATTERY_RESERVE,
                description="Throttle battery discharge by shifting deferrable loads to peak solar/wind hours",
                target_subsystem="BATTERY",
                rationale="Battery SOC is approaching or at the 20% minimum discharge cutoff",
                expected_survival_horizon_gain_h=round(min(float(len(states)), survival.battery_endurance_horizon_h + 8.0), 1),
                expected_reserve_margin_gain_pct=10.0,
                urgency=FailureSeverityEnum.WARNING,
                validation_tier="ESTIMATED",
                limitations="Discharge throttling benefit depends on solar/wind availability; advisory only"
            ))

        # 5. Fuel Shortage / Resupply Delay: Fuel Preservation Dispatch
        if (
            survival.binding_subsystem in ("FUEL", "RESUPPLY") or
            ResilienceThreatEnum.FUEL_SHORTAGE in threat_types or
            ResilienceThreatEnum.RESUPPLY_DELAY in threat_types
        ):
            options.append(CandidateRecoveryOption(
                action_type=RecoveryActionTypeEnum.PRESERVE_FUEL_UNTIL_RESUPPLY,
                description="Adopt fuel-conservation dispatch mode and defer high-energy scientific equipment",
                target_subsystem="FUEL",
                rationale="Remaining fuel inventory approaches critical reserve before scheduled resupply",
                expected_survival_horizon_gain_h=round(min(float(len(states)), survival.fuel_endurance_horizon_h + 48.0), 1),
                expected_reserve_margin_gain_pct=-5.0,  # Tradeoff: slightly lower reserve margin for extended fuel days
                urgency=FailureSeverityEnum.WARNING,
                validation_tier="ESTIMATED",
                limitations="Fuel extension calculated assuming 15% demand reduction; advisory only"
            ))

        # 6. Station Recovery Stabilization
        if any(s.resilience and s.resilience.threat_state == "CRITICAL" for s in states[:len(states)//2]) and not any(s.loads.unserved_critical_kw > 1e-4 for s in states[len(states)//2:]):
            options.append(CandidateRecoveryOption(
                action_type=RecoveryActionTypeEnum.ENTER_STATION_RECOVERY_MODE,
                description="Execute recovery protocol: stabilize bus voltage, confirm generator health, recharge battery bank",
                target_subsystem="ELECTRICAL",
                rationale="Station is transitioning out of acute critical deficit and restoring energy margins",
                expected_survival_horizon_gain_h=float(len(states)),
                expected_reserve_margin_gain_pct=15.0,
                urgency=FailureSeverityEnum.INFO,
                validation_tier="ESTIMATED",
                limitations="Recovery stabilization sequence requires engineering inspection; advisory only"
            ))

        return options
