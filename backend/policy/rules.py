"""
POLARIS-EMS — Explicit Deterministic Policy Rules Evaluator
SIH26061: Polar Energy Management & Resilience System

Evaluates explicit, auditable policy rules across all 8 policy families.
Strictly adheres to:
- Measurable physical conditions directly from Phase 7 and Phase 4.
- Station-specific thresholds dynamically loaded from registry (Bharati, Maitri, Himadri).
- Explicit hysteresis state tracking via HysteresisController.
- Zero opaque AI models or hidden logic.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json

from backend.data.station_profiles.loader import StationProfile
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.resilience.schema import ResilienceStateEnum, ResilienceThreatEnum
from backend.policy.schema import (
    PolicyDecision,
    PolicyCondition,
    PolicyStateEnum,
    PolicyCategoryEnum,
    PolicyPriorityEnum,
    PolicyActionEnum,
    PolicyValidationStatusEnum,
    HysteresisState
)
from backend.policy.adapter import ValidatedPolicyInputs
from backend.policy.hysteresis import HysteresisController


class PolicyRuleEvaluator:
    """Evaluates explicit policy rules against validated upstream inputs."""

    def __init__(
        self,
        profile: StationProfile,
        safety_registry: SafetyThresholdRegistry,
        config_path: Optional[Path] = None
    ):
        self.profile = profile
        self.safety_registry = safety_registry
        self.station_id = profile.station_id.upper()

        if config_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            config_path = base_dir / "configs" / "policy_rules.json"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f).get("rules", {})

    def evaluate_rules(
        self,
        inputs: ValidatedPolicyInputs,
        previous_hysteresis: Optional[HysteresisState] = None
    ) -> Tuple[List[PolicyDecision], HysteresisState]:
        """
        Evaluates all policy rules deterministically.
        Returns triggered candidate policies and updated hysteresis state.
        """
        candidates: List[PolicyDecision] = []
        hyst_state = previous_hysteresis or HysteresisState()

        # Dynamic station thresholds from registry
        sid = self.station_id
        min_safe_temp = float(self.safety_registry.get_value(sid, "indoor_min_safe_temp_c", default=12.0))
        fuel_reserve_l = float(self.safety_registry.get_value(sid, "fuel_reserve_liters", default=25000.0))
        reserve_threat_pct = float(self.safety_registry.get_value(sid, "reserve_margin_threatened_pct", default=15.0))
        reserve_warning_pct = float(self.safety_registry.get_value(sid, "reserve_margin_warning_pct", default=30.0))

        state = inputs.initial_state
        survival = inputs.survival
        cur_ts = inputs.timestamp

        # ----------------------------------------------------------------------
        # Rule 1: Critical Load Protection (P1_CRITICAL_LIFE_SAFETY)
        # ----------------------------------------------------------------------
        unserved_crit = state.loads.unserved_critical_kw if state and state.loads else 0.0
        crit_horizon = survival.critical_load_survival_horizon_h if survival else float(inputs.horizon_hours)

        crit_load_triggered = (unserved_crit > 1e-4) or (crit_horizon < inputs.horizon_hours - 1e-4)
        if crit_load_triggered:
            conds = [
                PolicyCondition(
                    condition_name="Unserved Critical Load",
                    threshold_field="unserved_critical_kw",
                    operator=">",
                    threshold_value=1e-4,
                    observed_value=round(unserved_crit, 3),
                    satisfied=(unserved_crit > 1e-4)
                ),
                PolicyCondition(
                    condition_name="Critical Load Survival Horizon",
                    threshold_field="critical_load_survival_horizon_h",
                    operator="<",
                    threshold_value=inputs.horizon_hours,
                    observed_value=round(crit_horizon, 1),
                    satisfied=(crit_horizon < inputs.horizon_hours)
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R1_CRITICAL_LOAD_PRESERVATION",
                policy_category=PolicyCategoryEnum.CRITICAL_LOAD_PROTECTION,
                policy_state=PolicyStateEnum.PROTECT,
                priority=PolicyPriorityEnum.P1_CRITICAL_LIFE_SAFETY,
                action=PolicyActionEnum.PRESERVE_CRITICAL_LOADS,
                reason=f"Life-safety critical load deficit detected (unserved={unserved_crit:.1f} kW, horizon={crit_horizon:.1f} h)",
                conditions_met=conds,
                expected_effect="Mandatory shedding of discretionary and non-critical loads to preserve life-safety bus",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 2: Thermal Safety Critical (P1_CRITICAL_LIFE_SAFETY)
        # ----------------------------------------------------------------------
        indoor_temp = state.thermal.indoor_temperature_c if state and state.thermal else min_safe_temp
        therm_horizon = survival.thermal_habitability_horizon_h if survival else float(inputs.horizon_hours)

        therm_crit_triggered = (indoor_temp < min_safe_temp - 1e-4) or (therm_horizon < inputs.horizon_hours - 1e-4)
        if therm_crit_triggered:
            conds = [
                PolicyCondition(
                    condition_name="Indoor Temperature Safe Minimum Breach",
                    threshold_field="indoor_temperature_c",
                    operator="<",
                    threshold_value=min_safe_temp,
                    observed_value=round(indoor_temp, 2),
                    satisfied=(indoor_temp < min_safe_temp)
                ),
                PolicyCondition(
                    condition_name="Thermal Habitability Horizon",
                    threshold_field="thermal_habitability_horizon_h",
                    operator="<",
                    threshold_value=inputs.horizon_hours,
                    observed_value=round(therm_horizon, 1),
                    satisfied=(therm_horizon < inputs.horizon_hours)
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R2_THERMAL_SAFETY_CRITICAL",
                policy_category=PolicyCategoryEnum.THERMAL_PROTECTION,
                policy_state=PolicyStateEnum.PROTECT,
                priority=PolicyPriorityEnum.P1_CRITICAL_LIFE_SAFETY,
                action=PolicyActionEnum.PROTECT_INDOOR_TEMPERATURE,
                reason=f"Indoor temperature ({indoor_temp:.1f} °C) below safe limit ({min_safe_temp:.1f} °C)",
                conditions_met=conds,
                expected_effect="Prioritize electric power allocation to heating circuits and prevent envelope freeze",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 3: Thermal Safety Preparedness (P3_THERMAL_SAFETY with Hysteresis)
        # ----------------------------------------------------------------------
        therm_buffer = 2.0  # Activate within 2.0 °C of safe minimum
        therm_hyst = 1.5    # Deactivate when margin >= 3.5 °C
        therm_margin = indoor_temp - min_safe_temp

        is_therm_warn, hyst_state = HysteresisController.evaluate_deadband(
            parameter_key="thermal_margin_c",
            current_value=therm_margin,
            activation_threshold=therm_buffer,
            deactivation_threshold=therm_buffer + therm_hyst,
            is_less_than_trigger=True,
            previous_state=hyst_state,
            current_timestamp=cur_ts
        )

        if is_therm_warn and not therm_crit_triggered:
            conds = [
                PolicyCondition(
                    condition_name="Thermal Safety Warning Buffer",
                    threshold_field="thermal_margin_c",
                    operator="<=",
                    threshold_value=therm_buffer,
                    observed_value=round(therm_margin, 2),
                    satisfied=True
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R3_THERMAL_SAFETY_WARNING",
                policy_category=PolicyCategoryEnum.THERMAL_PROTECTION,
                policy_state=PolicyStateEnum.PREPARE,
                priority=PolicyPriorityEnum.P4_THERMAL_SAFETY,
                action=PolicyActionEnum.PREPARE_THERMAL_ENVELOPE,
                reason=f"Indoor temperature ({indoor_temp:.1f} °C) within warning buffer ({therm_buffer} °C) of safe limit",
                conditions_met=conds,
                expected_effect="Preheat quarters and inspect insulation flaps before severe freeze sets in",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 4: Dependable Reserve Erosion Emergency (P3 with Hysteresis)
        # ----------------------------------------------------------------------
        res_pct = state.resilience.dependable_reserve_pct if state and state.resilience else 50.0
        res_hyst = 5.0  # 5% deadband: activate at <= 15%, deactivate at >= 20%

        is_res_crit, hyst_state = HysteresisController.evaluate_deadband(
            parameter_key="dependable_reserve_critical",
            current_value=res_pct,
            activation_threshold=reserve_threat_pct,
            deactivation_threshold=reserve_threat_pct + res_hyst,
            is_less_than_trigger=True,
            previous_state=hyst_state,
            current_timestamp=cur_ts
        )

        if is_res_crit:
            conds = [
                PolicyCondition(
                    condition_name="Emergency Reserve Margin Limit",
                    threshold_field="dependable_reserve_pct",
                    operator="<=",
                    threshold_value=reserve_threat_pct,
                    observed_value=round(res_pct, 1),
                    satisfied=True
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R4_RESERVE_EROSION_CRITICAL",
                policy_category=PolicyCategoryEnum.PREPAREDNESS,
                policy_state=PolicyStateEnum.PROTECT,
                priority=PolicyPriorityEnum.P3_GENERATION_RESERVE_PROTECTION,
                action=PolicyActionEnum.PREPARE_STANDBY_GENERATOR,
                reason=f"Operating dependable reserve ({res_pct:.1f}%) below emergency limit ({reserve_threat_pct}%)",
                conditions_met=conds,
                expected_effect="Unmask and prepare standby generator to restore required generation reserve margin",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 5: Dependable Reserve Erosion Warning (P3 with Hysteresis)
        # ----------------------------------------------------------------------
        is_res_warn, hyst_state = HysteresisController.evaluate_deadband(
            parameter_key="dependable_reserve_warning",
            current_value=res_pct,
            activation_threshold=reserve_warning_pct,
            deactivation_threshold=reserve_warning_pct + res_hyst,
            is_less_than_trigger=True,
            previous_state=hyst_state,
            current_timestamp=cur_ts
        )

        if is_res_warn and not is_res_crit:
            conds = [
                PolicyCondition(
                    condition_name="Warning Reserve Margin Limit",
                    threshold_field="dependable_reserve_pct",
                    operator="<=",
                    threshold_value=reserve_warning_pct,
                    observed_value=round(res_pct, 1),
                    satisfied=True
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R5_RESERVE_EROSION_WARNING",
                policy_category=PolicyCategoryEnum.MONITORING,
                policy_state=PolicyStateEnum.MONITOR,
                priority=PolicyPriorityEnum.P3_GENERATION_RESERVE_PROTECTION,
                action=PolicyActionEnum.MONITOR_RESERVES,
                reason=f"Operating dependable reserve ({res_pct:.1f}%) within warning zone ({reserve_warning_pct}%)",
                conditions_met=conds,
                expected_effect="Elevate tracking frequency of generator headrooms and intermittent loads",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 6: Fuel Emergency Preservation (P5_FUEL_RESUPPLY_PROTECTION)
        # ----------------------------------------------------------------------
        rem_fuel = state.fuel.fuel_remaining_l if state and state.fuel else 99999.0
        fuel_horizon = survival.fuel_endurance_horizon_h if survival else float(inputs.horizon_hours)

        fuel_crit_triggered = (rem_fuel <= fuel_reserve_l) or (fuel_horizon < inputs.horizon_hours - 1e-4)
        if fuel_crit_triggered:
            conds = [
                PolicyCondition(
                    condition_name="Station Emergency Fuel Reserve Limit",
                    threshold_field="fuel_remaining_l",
                    operator="<=",
                    threshold_value=fuel_reserve_l,
                    observed_value=round(rem_fuel, 0),
                    satisfied=(rem_fuel <= fuel_reserve_l)
                ),
                PolicyCondition(
                    condition_name="Fuel Endurance Horizon",
                    threshold_field="fuel_endurance_horizon_h",
                    operator="<",
                    threshold_value=inputs.horizon_hours,
                    observed_value=round(fuel_horizon, 1),
                    satisfied=(fuel_horizon < inputs.horizon_hours)
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R6_FUEL_EMERGENCY_PRESERVATION",
                policy_category=PolicyCategoryEnum.FUEL_PRESERVATION,
                policy_state=PolicyStateEnum.PROTECT,
                priority=PolicyPriorityEnum.P5_FUEL_RESUPPLY_PROTECTION,
                action=PolicyActionEnum.PRESERVE_EMERGENCY_FUEL,
                reason=f"Fuel inventory ({rem_fuel:.0f} L) at or below emergency limit ({fuel_reserve_l:.0f} L)",
                conditions_met=conds,
                expected_effect="Adopt fuel-conservation dispatch and restrict diesel generation strictly to critical needs",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 7: Resupply Gap Logistics Vulnerability (P5)
        # ----------------------------------------------------------------------
        resupply_gap_h = survival.resupply_gap_survivability_h if survival else float(inputs.horizon_hours)
        binding_sub = survival.binding_subsystem if survival else "NONE"

        resupply_gap_triggered = (resupply_gap_h < inputs.horizon_hours - 1e-4) or (binding_sub == "RESUPPLY")
        if resupply_gap_triggered and not fuel_crit_triggered:
            conds = [
                PolicyCondition(
                    condition_name="Resupply Gap Survivability Duration",
                    threshold_field="resupply_gap_survivability_h",
                    operator="<",
                    threshold_value=inputs.horizon_hours,
                    observed_value=round(resupply_gap_h, 1),
                    satisfied=(resupply_gap_h < inputs.horizon_hours)
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R7_RESUPPLY_GAP_VULNERABILITY",
                policy_category=PolicyCategoryEnum.RESUPPLY_PROTECTION,
                policy_state=PolicyStateEnum.PROTECT,
                priority=PolicyPriorityEnum.P5_FUEL_RESUPPLY_PROTECTION,
                action=PolicyActionEnum.CONSERVE_FUEL_UNTIL_RESUPPLY,
                reason=f"Projected fuel endurance cannot bridge the resupply gap ({resupply_gap_h:.1f} h < {inputs.horizon_hours} h)",
                conditions_met=conds,
                expected_effect="Enforce strict conservation posture to guarantee fuel integrity through convoy delivery",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 8: Storage Depletion Warning (P6 with Hysteresis)
        # ----------------------------------------------------------------------
        soc_pct = state.battery.soc_pct if state and state.battery else 0.8
        soc_thresh = 0.25
        soc_hyst = 0.10  # Activate at <= 25%, deactivate at >= 35%

        is_bat_warn, hyst_state = HysteresisController.evaluate_deadband(
            parameter_key="battery_soc_depletion",
            current_value=soc_pct,
            activation_threshold=soc_thresh,
            deactivation_threshold=soc_thresh + soc_hyst,
            is_less_than_trigger=True,
            previous_state=hyst_state,
            current_timestamp=cur_ts
        )

        if is_bat_warn:
            conds = [
                PolicyCondition(
                    condition_name="Battery State of Charge Low Limit",
                    threshold_field="battery_soc_pct",
                    operator="<=",
                    threshold_value=soc_thresh,
                    observed_value=round(soc_pct, 3),
                    satisfied=True
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R8_STORAGE_DEPLETION_WARNING",
                policy_category=PolicyCategoryEnum.STORAGE_PROTECTION,
                policy_state=PolicyStateEnum.PREPARE,
                priority=PolicyPriorityEnum.P6_STORAGE_PROTECTION,
                action=PolicyActionEnum.PRESERVE_MINIMUM_BATTERY_SOC,
                reason=f"Battery SOC ({soc_pct * 100:.1f}%) approaching minimum discharge cutoff (20%)",
                conditions_met=conds,
                expected_effect="Throttle battery discharge by shifting deferrable loads to peak renewable hours",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 9: Station Recovery Protocol (P7_NONCRITICAL_OPTIMIZATION)
        # ----------------------------------------------------------------------
        if inputs.resilience_state == ResilienceStateEnum.RECOVERY:
            conds = [
                PolicyCondition(
                    condition_name="Resilience State is RECOVERY",
                    threshold_field="resilience_state",
                    operator="==",
                    threshold_value="RECOVERY",
                    observed_value="RECOVERY",
                    satisfied=True
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R9_STATION_RECOVERY_PROTOCOL",
                policy_category=PolicyCategoryEnum.RECOVERY,
                policy_state=PolicyStateEnum.RECOVER,
                priority=PolicyPriorityEnum.P7_NONCRITICAL_OPTIMIZATION,
                action=PolicyActionEnum.ADOPT_STATION_RECOVERY_POSTURE,
                reason="Station is transitioning out of acute critical deficit and restoring energy margins",
                conditions_met=conds,
                expected_effect="Execute recovery protocol: stabilize bus voltage, confirm generator health, recharge battery",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 10: Nominal Baseline Monitoring (P8_MONITORING)
        # ----------------------------------------------------------------------
        # If no protective or recovery candidates were triggered, evaluate nominal monitoring
        protective_candidates = [
            c for c in candidates if c.priority <= PolicyPriorityEnum.P6_STORAGE_PROTECTION
        ]
        if not protective_candidates and inputs.resilience_state in (ResilienceStateEnum.SAFE, ResilienceStateEnum.WATCH):
            conds = [
                PolicyCondition(
                    condition_name="Operational Posture Nominal",
                    threshold_field="resilience_state",
                    operator="in",
                    threshold_value=["SAFE", "WATCH"],
                    observed_value=inputs.resilience_state.value,
                    satisfied=True
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R10_NOMINAL_MONITORING",
                policy_category=PolicyCategoryEnum.MONITORING,
                policy_state=PolicyStateEnum.MONITOR if inputs.resilience_state == ResilienceStateEnum.WATCH else PolicyStateEnum.NO_ACTION,
                priority=PolicyPriorityEnum.P8_MONITORING,
                action=PolicyActionEnum.MONITOR_RESERVES,
                reason="All physical and life-safety margins nominal; passive monitoring active",
                conditions_met=conds,
                expected_effect="Continue standard telemetry ingestion and microgrid dispatch observation",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 11: Discretionary Load Mitigation (P2 - MITIGATE)
        # ----------------------------------------------------------------------
        renewable_or_storage_threat = any(
            t.threat_type in (
                ResilienceThreatEnum.SOLAR_FAILURE,
                ResilienceThreatEnum.WIND_FAILURE,
                ResilienceThreatEnum.RENEWABLE_SHORTFALL,
                ResilienceThreatEnum.BATTERY_DERATING
            )
            for t in inputs.threats
        ) or (
            inputs.scenario is not None and any(
                term in inputs.scenario.scenario_id for term in ("FAILURE", "DEGRADATION", "BLIZZARD")
            )
        )
        if inputs.resilience_state in (ResilienceStateEnum.AT_RISK, ResilienceStateEnum.THREATENED) and renewable_or_storage_threat:
            conds = [
                PolicyCondition(
                    condition_name="Elevated Threat with Generation/Storage Disruption",
                    threshold_field="resilience_state",
                    operator="in",
                    threshold_value=["AT_RISK", "THREATENED"],
                    observed_value=inputs.resilience_state.value,
                    satisfied=True
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R11_DISCRETIONARY_LOAD_MITIGATION",
                policy_category=PolicyCategoryEnum.CRITICAL_LOAD_PROTECTION,
                policy_state=PolicyStateEnum.MITIGATE,
                priority=PolicyPriorityEnum.P2_CRITICAL_LOAD_PROTECTION,
                action=PolicyActionEnum.BLOCK_DISCRETIONARY_LOADS,
                reason=f"Station under {inputs.resilience_state.value} with renewable/storage disruption; blocking discretionary loads",
                conditions_met=conds,
                expected_effect="Suspend discretionary loads to mitigate power deficit before critical loads are threatened",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        # ----------------------------------------------------------------------
        # Rule 12: Station Governance Escalation (P1 - ESCALATE)
        # ----------------------------------------------------------------------
        overall_horizon = survival.overall_station_survival_horizon_h if survival else float(inputs.horizon_hours)
        is_compound_crit = (
            unserved_crit > 1e-4
            and rem_fuel <= fuel_reserve_l
            and inputs.resilience_state == ResilienceStateEnum.CRITICAL
        )

        if is_compound_crit:
            conds = [
                PolicyCondition(
                    condition_name="Compound Emergency: Critical Load Deficit & Fuel Depletion",
                    threshold_field="unserved_critical_kw_and_fuel",
                    operator="<=",
                    threshold_value=fuel_reserve_l,
                    observed_value=round(rem_fuel, 0),
                    satisfied=True
                )
            ]
            candidates.append(PolicyDecision(
                rule_id="R12_GOVERNANCE_ESCALATION",
                policy_category=PolicyCategoryEnum.CRITICAL_LOAD_PROTECTION,
                policy_state=PolicyStateEnum.ESCALATE,
                priority=PolicyPriorityEnum.P1_CRITICAL_LIFE_SAFETY,
                action=PolicyActionEnum.PRESERVE_CRITICAL_LOADS,
                reason=f"Compound critical crisis: unserved load ({unserved_crit:.1f} kW) with fuel depletion ({rem_fuel:.0f} L); mandatory governance escalation",
                conditions_met=conds,
                expected_effect="Trigger immediate emergency governance escalation to station commander and polar operations HQ",
                validation_status=PolicyValidationStatusEnum.APPROVED,
                provenance="SIMULATED",
                rule_source="policy_rules.json"
            ))

        return candidates, hyst_state
