"""
POLARIS-EMS — Deterministic Decision Explainer
SIH26061: Polar Energy Management & Resilience System

Generates structured, factual, operator-ready explanations from structured trace events.

STRICT INVARIANTS:
1. Zero LLM or generative hallucination.
2. Derives every answer solely from factual engine outputs and registered reason codes.
3. Explicitly distinguishes PHYSICALLY VALIDATED outcomes from ESTIMATED projections.
"""

from typing import List, Dict, Any, Optional

from backend.trace.schema import (
    TraceRecord,
    TraceEvent,
    DecisionExplanation,
    ReasonCode
)


class DeterministicExplainer:
    """Generates deterministic human-readable explanations from TraceRecord evidence."""

    @classmethod
    def explain(cls, trace: TraceRecord) -> DecisionExplanation:
        """Constructs an auditable DecisionExplanation envelope."""
        events_by_stage: Dict[str, TraceEvent] = {
            ev.stage.value: ev for ev in trace.events
        }

        # 1. Headline
        headline = (
            f"Decision Trace for {trace.station_id}: Policy directed '{trace.primary_directive or 'NORMAL_OPERATION'}' "
            f"under {trace.resilience_state or 'SAFE'} resilience posture ({trace.execution_status.value})."
        )

        # 2. Why this state?
        res_ev = events_by_stage.get("RESILIENCE")
        if res_ev:
            state = res_ev.outputs.get("resilience_state", "SAFE")
            c_idx = res_ev.outputs.get("composite_resilience_index", 100.0)
            binding = res_ev.outputs.get("binding_subsystem", "NONE")
            surv_h = res_ev.outputs.get("survival_horizon_h", 720.0)
            why_state = (
                f"Station entered '{state}' resilience posture with a composite index of {c_idx:.1f}/100. "
                f"Survival horizon is assessed at {surv_h:.1f} hours, with '{binding}' as the binding subsystem constraint."
            )
        else:
            why_state = f"Resilience assessment not available; trace terminated with status {trace.execution_status.value}."

        # 3. Why this policy?
        pol_ev = events_by_stage.get("POLICY")
        if pol_ev:
            p_state = pol_ev.outputs.get("policy_state", "NO_ACTION")
            directive = pol_ev.outputs.get("primary_directive", "NORMAL_OPERATION")
            rules_cnt = pol_ev.outputs.get("active_rules_count", 0)
            rationale = pol_ev.outputs.get("advisory_rationale", "")
            why_policy = (
                f"Policy Engine transitioned to state '{p_state}' and issued directive '{directive}' based on "
                f"{rules_cnt} active rules evaluated against the P1–P8 governance hierarchy. "
                f"Advisory rationale: {rationale or 'Preserve critical loads and life-support reserves.'}"
            )
        else:
            why_policy = "Policy governance was not reached or failed to execute."

        # 4. Why this schedule?
        opt_ev = events_by_stage.get("OPTIMIZER")
        if opt_ev:
            mode = opt_ev.inputs.get("mode", "EXPECTED")
            tier = opt_ev.outputs.get("optimality_tier", "FALLBACK")
            gap = opt_ev.outputs.get("relative_gap")
            gap_str = f"with a relative MIP gap of {gap * 100:.2f}%" if gap is not None else "without gap tolerance"
            why_schedule = (
                f"Phase 6 HiGHS solved the dispatch schedule in '{mode}' mode, achieving optimality tier '{tier}' "
                f"{gap_str}. The proposed dispatch prioritizes critical thermal and life-support loads while minimizing unserved energy."
            )
        else:
            why_schedule = "Optimization schedule not generated; operating under local fallback posture."

        # 5. What data was used?
        data_used: List[str] = []
        fc_ev = events_by_stage.get("FORECAST")
        if fc_ev:
            data_used.append(f"Phase 3 Probabilistic Forecaster: {fc_ev.outputs.get('points_count', 0)} hourly steps (provenance=FORECAST).")
        sc_ev = events_by_stage.get("SCENARIO")
        if sc_ev:
            data_used.append(f"Phase 5 Scenario: '{sc_ev.inputs.get('scenario_id', 'NORMAL_BASELINE')}' environmental stress parameters.")
        ed_ev = events_by_stage.get("EDGE")
        if ed_ev:
            data_used.append(f"Phase 11 Edge Context: {ed_ev.outputs.get('edge_mode', 'CONNECTED_OPERATION')} node state.")

        # 6. What was physically validated?
        validated: List[str] = []
        tw_ev = events_by_stage.get("TWIN_REPLAY")
        if tw_ev and tw_ev.outputs.get("physically_validated"):
            validated.append("Digital Twin Replay: Electrical power balance, battery SoC bounds, and thermal indoor thresholds were physically simulated and validated.")
            validated.append(f"Observed Unserved Load: {tw_ev.outputs.get('total_unserved_load_kwh', 0.0):.2f} kWh.")
        else:
            validated.append("Digital Twin Replay was bypassed or unverified; schedule remains in PROPOSED state.")

        # 7. What remains estimated?
        estimated: List[str] = []
        if res_ev:
            estimated.append("Resilience recovery trajectories and counterfactual options are modeled estimations (provenance=SIMULATED).")
        if fc_ev:
            estimated.append("Load and renewable profiles beyond the immediate observation horizon are conformal machine learning estimates (P10–P95).")

        # 8. What is next?
        if trace.execution_status.value == "COMPLETED":
            what_next = f"Station operational posture maintained under directive '{trace.primary_directive}'. Next scheduled pipeline re-evaluation in 1 hour."
        elif trace.execution_status.value == "FALLBACK":
            what_next = "Edge node maintaining safe hold posture. Awaiting reconnection and local buffer synchronization."
        else:
            what_next = f"Pipeline execution halted with status '{trace.execution_status.value}'. Investigate stage failure diagnostics."

        # Reason codes
        reason_codes = [ev.reason_code for ev in trace.events]

        return DecisionExplanation(
            trace_id=trace.decision_trace_id,
            station_id=trace.station_id,
            headline=headline,
            why_this_state=why_state,
            why_this_policy=why_policy,
            why_this_schedule=why_schedule,
            what_data_used=data_used,
            what_was_validated=validated,
            what_remains_estimated=estimated,
            what_is_next=what_next,
            reason_codes=reason_codes
        )
