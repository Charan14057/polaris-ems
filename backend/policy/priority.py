"""
POLARIS-EMS — Deterministic Conflict Resolution & Generator Physical Safety
SIH26061: Polar Energy Management & Resilience System

Resolves policy conflicts, suppresses incompatible lower-priority directives,
and enforces physical generator availability safety gates.
Strictly adheres to:
- Numerical priority precedence (P1 > P2 > ... > P8).
- Generator override physical safety: NEVER forces a faulted or maintenance unit online.
- Hierarchy: Physical availability -> Twin constraints -> Phase 6 optimizer -> Phase 8 policy.
"""

from typing import Dict, List, Optional, Tuple, Set
from backend.data.station_profiles.loader import StationProfile
from backend.twin.state import TwinState
from backend.policy.schema import (
    PolicyDecision,
    PolicyPriorityEnum,
    PolicyStateEnum,
    PolicyActionEnum,
    PolicyValidationStatusEnum
)


class PolicyPriorityResolver:
    """Resolves policy candidate priorities and filters physical generator constraints."""

    @staticmethod
    def resolve_conflicts(
        candidates: List[PolicyDecision],
        profile: StationProfile,
        initial_state: Optional[TwinState],
        generator_overrides: Optional[Dict[int, str]] = None
    ) -> Tuple[Optional[PolicyDecision], List[PolicyDecision], List[PolicyDecision], List[str]]:
        """
        Sorts candidates by priority, resolves mutual exclusion, applies generator physical safety,
        and partitions into primary, active, and suppressed policies.
        """
        trace_logs: List[str] = []

        if not candidates:
            trace_logs.append("No policy rules triggered; resolving to NO_ACTION")
            return None, [], [], trace_logs

        # 1. Deterministic sort: ascending by priority value, then ESCALATE state first within P1, then by rule_id for total order
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (int(c.priority), 0 if c.policy_state == PolicyStateEnum.ESCALATE else 1, c.rule_id)
        )
        primary = sorted_candidates[0]
        trace_logs.append(f"Primary policy selected: {primary.rule_id} (Priority {primary.priority.name})")

        active: List[PolicyDecision] = []
        suppressed: List[PolicyDecision] = []

        # 2. Conflict suppression rules
        # When an acute emergency policy (P1 or P2) is active, passive monitoring is suppressed
        is_emergency = primary.priority <= PolicyPriorityEnum.P2_CRITICAL_LOAD_PROTECTION

        for cand in sorted_candidates:
            if cand.rule_id == primary.rule_id:
                active.append(cand)
                continue

            # Incompatible: monitoring under acute emergency
            if is_emergency and cand.priority >= PolicyPriorityEnum.P7_NONCRITICAL_OPTIMIZATION:
                cand.is_active = False
                cand.is_suppressed = True
                cand.suppressed_by = primary.rule_id
                suppressed.append(cand)
                trace_logs.append(f"Suppressed {cand.rule_id}: incompatible with primary emergency policy {primary.rule_id}")
            else:
                # Compatible concurrent policy (e.g. Protect Thermal + Preserve Fuel)
                active.append(cand)
                trace_logs.append(f"Active concurrent policy: {cand.rule_id} (Priority {cand.priority.name})")

        # 3. Generator Physical Safety Gate
        # Validate any generator commitment against authoritative physical availability
        PolicyPriorityResolver._enforce_generator_safety(
            active=active,
            profile=profile,
            initial_state=initial_state,
            generator_overrides=generator_overrides,
            trace_logs=trace_logs
        )

        return primary, active, suppressed, trace_logs

    @staticmethod
    def _enforce_generator_safety(
        active: List[PolicyDecision],
        profile: StationProfile,
        initial_state: Optional[TwinState],
        generator_overrides: Optional[Dict[int, str]],
        trace_logs: List[str]
    ) -> None:
        """
        Enforces Guardrail 5:
        A policy may request preparation of a healthy available unit.
        It may NEVER override a faulted or maintenance unit online.
        """
        gen_count = int(profile.electrical.diesel_generator_count)

        # Inspect which generators are physically unavailable
        prohibited_generators: Set[int] = set()
        online_generators: Set[int] = set()

        if initial_state and initial_state.diesel:
            # Check unit-level status from state if available
            gen_status = initial_state.diesel.generator_status
            if gen_status in ("FAULT", "MAINTENANCE", "TRIPPED"):
                # Unit 1 or aggregate primary is faulted
                prohibited_generators.add(1)

        # Ingest external overrides (e.g. from scenarios or maintenance logs)
        if generator_overrides:
            for g_id, status in generator_overrides.items():
                if status in ("FAULT", "MAINTENANCE", "OFFLINE_LOCKED"):
                    prohibited_generators.add(g_id)
                elif status == "ONLINE":
                    online_generators.add(g_id)

        for pol in active:
            if pol.action == PolicyActionEnum.PREPARE_STANDBY_GENERATOR:
                # Find available standby units
                candidate_standby: Optional[int] = None
                for gid in range(1, gen_count + 1):
                    if gid not in prohibited_generators and gid not in online_generators:
                        candidate_standby = gid
                        break

                if candidate_standby is not None:
                    trace_logs.append(
                        f"Generator safety gate: healthy standby unit G{candidate_standby} available for preparation"
                    )
                else:
                    trace_logs.append(
                        f"Generator safety gate WARNING: zero healthy standby units available (fleet size {gen_count}, "
                        f"prohibited: {sorted(list(prohibited_generators))}, online: {sorted(list(online_generators))})"
                    )
                    # Policy cannot proceed because no physical standby units are available
                    pol.reason += " [BLOCKED: No standby units physically available; cannot force faulted units online]"
                    pol.policy_state = PolicyStateEnum.BLOCKED
                    pol.validation_status = PolicyValidationStatusEnum.BLOCKED
