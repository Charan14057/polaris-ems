"""
POLARIS-EMS — Policy to Optimizer Handoff Translator
SIH26061: Polar Energy Management & Resilience System

Translates active policy decisions into explicit Phase 6 optimizer requirements.
Enforces Guardrail 1 & Final Handoff Clarification:
- Strictly adheres to the frozen OptimizerEngine.optimize() interface.
- Classifies every field into:
  * DIRECTLY_SUPPORTED
  * DERIVED_FROM_SUPPORTED_INPUT
  * DECLARATIVE_ONLY
  * REQUIRES_OPTIMIZATION
- Preserves explicit distinction between:
  1. Requested policy constraint
  2. Optimizer-enforced constraint
  3. Post-replay validated outcome
- Never falsely claims un-enforced declarative fields are satisfied by the solver.
"""

from typing import Dict, List, Optional, Any, Set
from backend.data.station_profiles.loader import StationProfile
from backend.twin.state import TwinState
from backend.optimizer.schema import OptimizationMode
from backend.policy.schema import (
    PolicyDecision,
    PolicyPriorityEnum,
    PolicyActionEnum,
    PolicyValidationStatusEnum,
    HandoffEnforcementTierEnum,
    OptimizerHandoffRequirements
)


class PolicyOptimizerHandoffTranslator:
    """Formulates structured optimizer requirements without modifying Phase 6."""

    @staticmethod
    def build_handoff_requirements(
        active_policies: List[PolicyDecision],
        profile: StationProfile,
        initial_state: Optional[TwinState],
        generator_overrides: Optional[Dict[int, str]] = None
    ) -> OptimizerHandoffRequirements:
        """
        Synthesizes structured handoff requirements from active policies.
        """
        requested_constraints: Dict[str, Any] = {}
        optimizer_enforced_constraints: Dict[str, Any] = {}
        enforcement_tiers: Dict[str, str] = {}

        # 1. Mode determination
        # If acute life safety, critical load, thermal, or reserve emergency is active -> CONSERVATIVE mode
        needs_conservative = any(
            p.priority <= PolicyPriorityEnum.P3_GENERATION_RESERVE_PROTECTION
            for p in active_policies
        )
        rec_mode = OptimizationMode.CONSERVATIVE if needs_conservative else OptimizationMode.EXPECTED

        enforcement_tiers["recommended_mode"] = HandoffEnforcementTierEnum.DIRECTLY_SUPPORTED.value
        optimizer_enforced_constraints["mode"] = rec_mode.value

        # 2. Generator overrides determination
        overrides: Dict[int, str] = dict(generator_overrides) if generator_overrides else {}
        wants_standby = any(
            p.action == PolicyActionEnum.PREPARE_STANDBY_GENERATOR for p in active_policies
        )

        if wants_standby:
            requested_constraints["request_standby_generator"] = True
            gen_count = int(profile.electrical.diesel_generator_count)
            online_cnt = initial_state.diesel.online_count if (initial_state and initial_state.diesel) else 1

            # Find first healthy standby unit not already online or prohibited
            for gid in range(1, gen_count + 1):
                cur_status = overrides.get(gid)
                is_currently_online = (gid <= online_cnt) or (cur_status == "ONLINE")
                if is_currently_online or cur_status in ("FAULT", "MAINTENANCE", "OFFLINE_LOCKED"):
                    continue
                # Eligible healthy standby unit
                overrides[gid] = "ONLINE"
                requested_constraints["prepared_unit_id"] = gid
                break

        if overrides:
            enforcement_tiers["generator_overrides"] = HandoffEnforcementTierEnum.DIRECTLY_SUPPORTED.value
            optimizer_enforced_constraints["generator_overrides"] = dict(overrides)

        # 3. Reserve requirements
        min_reserve_req = None
        if any(p.priority <= PolicyPriorityEnum.P3_GENERATION_RESERVE_PROTECTION for p in active_policies):
            min_reserve_req = 30.0 if rec_mode == OptimizationMode.CONSERVATIVE else 15.0
            requested_constraints["min_operating_reserve_pct"] = min_reserve_req
            # In Phase 6, CONSERVATIVE mode elevates the reserve margin target internally
            enforcement_tiers["min_operating_reserve_pct"] = (
                HandoffEnforcementTierEnum.DERIVED_FROM_SUPPORTED_INPUT.value
                if rec_mode == OptimizationMode.CONSERVATIVE
                else HandoffEnforcementTierEnum.DECLARATIVE_ONLY.value
            )
            optimizer_enforced_constraints["derived_reserve_margin_elevation"] = (
                rec_mode == OptimizationMode.CONSERVATIVE
            )

        # 4. Storage preservation requirements
        min_terminal_soc = None
        if any(p.action == PolicyActionEnum.PRESERVE_MINIMUM_BATTERY_SOC for p in active_policies):
            min_terminal_soc = 0.50
            requested_constraints["min_terminal_soc_pct"] = min_terminal_soc
            # Declarative only: Phase 6 enforces nominal terminal SOC from profile, not arbitrary runtime policy target
            enforcement_tiers["min_terminal_soc_pct"] = HandoffEnforcementTierEnum.DECLARATIVE_ONLY.value

        # 5. Fuel preservation requirements
        min_terminal_fuel = None
        if any(p.action in (PolicyActionEnum.PRESERVE_EMERGENCY_FUEL, PolicyActionEnum.CONSERVE_FUEL_UNTIL_RESUPPLY) for p in active_policies):
            min_terminal_fuel = float(profile.fuel.critical_fuel_reserve_liters)
            requested_constraints["min_terminal_fuel_liters"] = min_terminal_fuel
            # Requires microgrid dispatch re-optimization through Phase 6 before it can be mathematically enforced
            enforcement_tiers["min_terminal_fuel_liters"] = HandoffEnforcementTierEnum.REQUIRES_OPTIMIZATION.value

        # 6. Load shedding allowance
        shed_allowed = any(p.action == PolicyActionEnum.PRESERVE_CRITICAL_LOADS for p in active_policies)
        if shed_allowed:
            requested_constraints["shed_noncritical_load_allowed"] = True
            # Declarative only: in Phase 6, non-critical shedding is governed by penalty weights, not binary toggle
            enforcement_tiers["shed_noncritical_load_allowed"] = HandoffEnforcementTierEnum.DECLARATIVE_ONLY.value

        # 7. Thermal protection requirement
        protect_thermal = any(p.action in (PolicyActionEnum.PROTECT_INDOOR_TEMPERATURE, PolicyActionEnum.PREPARE_THERMAL_ENVELOPE) for p in active_policies)
        if protect_thermal:
            requested_constraints["protect_heating_demand"] = True
            # Declarative only: Phase 6 includes thermal heat in continuous balance equation
            enforcement_tiers["protect_heating_demand"] = HandoffEnforcementTierEnum.DECLARATIVE_ONLY.value

        # Determine overall handoff status
        has_requires_opt = any(
            tier == HandoffEnforcementTierEnum.REQUIRES_OPTIMIZATION.value
            for tier in enforcement_tiers.values()
        )
        has_declarative = any(
            tier == HandoffEnforcementTierEnum.DECLARATIVE_ONLY.value
            for tier in enforcement_tiers.values()
        )

        if has_requires_opt:
            handoff_status = PolicyValidationStatusEnum.REQUIRES_OPTIMIZATION
        elif has_declarative:
            handoff_status = PolicyValidationStatusEnum.ADVISORY
        else:
            handoff_status = PolicyValidationStatusEnum.APPROVED

        requires_opt_count = len([t for t in enforcement_tiers.values() if t == HandoffEnforcementTierEnum.REQUIRES_OPTIMIZATION.value])
        declarative_count = len([t for t in enforcement_tiers.values() if t == HandoffEnforcementTierEnum.DECLARATIVE_ONLY.value])

        reasons = []
        if requires_opt_count > 0:
            reasons.append(
                f"{requires_opt_count} constraint(s) classified as REQUIRES_OPTIMIZATION: "
                f"Frozen Phase 6 OptimizerEngine.optimize() interface accepts mode and generator overrides, but does not accept terminal fuel bounds directly; "
                f"re-optimization is required."
            )
        if declarative_count > 0:
            reasons.append(
                f"{declarative_count} declarative target(s) tracked for post-replay validation."
            )

        rationale = (
            f"Policy dispatched in mode={rec_mode.value} with "
            f"{len(overrides)} generator overrides. "
            + " ".join(reasons)
        )

        return OptimizerHandoffRequirements(
            recommended_mode=rec_mode,
            generator_overrides=overrides if overrides else None,
            target_scenario_id=None,
            min_operating_reserve_pct=min_reserve_req,
            min_terminal_soc_pct=min_terminal_soc,
            min_terminal_fuel_liters=min_terminal_fuel,
            shed_noncritical_load_allowed=shed_allowed,
            protect_heating_demand=protect_thermal,
            enforcement_tiers=enforcement_tiers,
            requested_constraints=requested_constraints,
            optimizer_enforced_constraints=optimizer_enforced_constraints,
            post_replay_validated_outcomes={},
            handoff_status=handoff_status,
            advisory_rationale=rationale
        )
