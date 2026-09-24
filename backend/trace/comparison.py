"""
POLARIS-EMS — Comparative Decision Trace Delta Engine
SIH26061: Polar Energy Management & Resilience System

Compares two compatible DecisionTrace records to extract factual state transitions,
numerical deltas, policy directive adjustments, and operational mode changes.

INVARIANTS:
- Purely factual comparisons; zero subjective or evaluative commentary.
- Compares identical station contexts or explicit counterfactual runs.
"""

from typing import Dict, Tuple, List
from backend.trace.schema import TraceRecord, DecisionDelta


class TraceComparisonEngine:
    """Computes deterministic comparative deltas between two decision traces."""

    @classmethod
    def compare(cls, base_trace: TraceRecord, compare_trace: TraceRecord) -> DecisionDelta:
        """Computes factual diff between base_trace and compare_trace."""
        state_transitions: Dict[str, Tuple[str, str]] = {}
        numerical_deltas: Dict[str, float] = {}

        # 1. State Transitions
        if base_trace.resilience_state != compare_trace.resilience_state:
            state_transitions["resilience_state"] = (
                base_trace.resilience_state or "UNKNOWN",
                compare_trace.resilience_state or "UNKNOWN"
            )

        if base_trace.policy_state != compare_trace.policy_state:
            state_transitions["policy_state"] = (
                base_trace.policy_state or "UNKNOWN",
                compare_trace.policy_state or "UNKNOWN"
            )

        if base_trace.edge_mode != compare_trace.edge_mode:
            state_transitions["edge_mode"] = (
                base_trace.edge_mode or "UNKNOWN",
                compare_trace.edge_mode or "UNKNOWN"
            )

        if base_trace.scenario_id != compare_trace.scenario_id:
            state_transitions["scenario_id"] = (
                base_trace.scenario_id or "NORMAL_BASELINE",
                compare_trace.scenario_id or "NORMAL_BASELINE"
            )

        # 2. Extract numerical values from events
        base_nums = cls._extract_numerical_metrics(base_trace)
        comp_nums = cls._extract_numerical_metrics(compare_trace)

        all_keys = set(base_nums.keys()).union(set(comp_nums.keys()))
        for k in all_keys:
            v_base = base_nums.get(k, 0.0)
            v_comp = comp_nums.get(k, 0.0)
            diff = round(v_comp - v_base, 3)
            if abs(diff) > 1e-4:
                numerical_deltas[k] = diff

        # 3. Policy Directive Change
        dir_changed = base_trace.primary_directive != compare_trace.primary_directive
        edge_changed = base_trace.edge_mode != compare_trace.edge_mode

        # 4. Construct Factual Summary Narrative
        narrative_parts: List[str] = [
            f"Comparison between Trace '{base_trace.decision_trace_id}' and '{compare_trace.decision_trace_id}' for {base_trace.station_id}."
        ]

        for state_name, (s_from, s_to) in state_transitions.items():
            narrative_parts.append(f"{state_name} transitioned from '{s_from}' to '{s_to}'.")

        if dir_changed:
            narrative_parts.append(
                f"Primary directive changed from '{base_trace.primary_directive}' to '{compare_trace.primary_directive}'."
            )

        if "fuel_consumed_liters" in numerical_deltas:
            dfuel = numerical_deltas["fuel_consumed_liters"]
            narrative_parts.append(f"Fuel consumption delta: {dfuel:+.2f} L.")

        if "unserved_load_kwh" in numerical_deltas:
            dunserved = numerical_deltas["unserved_load_kwh"]
            narrative_parts.append(f"Unserved load delta: {dunserved:+.2f} kWh.")

        if "composite_resilience_index" in numerical_deltas:
            dindex = numerical_deltas["composite_resilience_index"]
            narrative_parts.append(f"Resilience index delta: {dindex:+.1f} points.")

        narrative = " ".join(narrative_parts)

        return DecisionDelta(
            base_trace_id=base_trace.decision_trace_id,
            compare_trace_id=compare_trace.decision_trace_id,
            station_id=base_trace.station_id,
            state_transitions=state_transitions,
            numerical_deltas=numerical_deltas,
            policy_directive_changed=dir_changed,
            edge_mode_changed=edge_changed,
            summary_narrative=narrative
        )

    @staticmethod
    def _extract_numerical_metrics(trace: TraceRecord) -> Dict[str, float]:
        metrics: Dict[str, float] = {}
        for ev in trace.events:
            if ev.stage.value == "TWIN_REPLAY":
                metrics["unserved_load_kwh"] = float(ev.outputs.get("total_unserved_load_kwh", 0.0))
                metrics["fuel_consumed_liters"] = float(ev.outputs.get("total_fuel_consumed_liters", 0.0))
            elif ev.stage.value == "RESILIENCE":
                metrics["composite_resilience_index"] = float(ev.outputs.get("composite_resilience_index", 100.0))
                metrics["survival_horizon_h"] = float(ev.outputs.get("survival_horizon_h", 720.0))
            elif ev.stage.value == "OPTIMIZER":
                gap = ev.outputs.get("relative_gap")
                if gap is not None:
                    metrics["relative_gap"] = float(gap)
                obj = ev.outputs.get("objective_value")
                if obj is not None:
                    metrics["objective_value"] = float(obj)
            elif ev.stage.value == "EDGE":
                metrics["buffered_observations"] = float(ev.outputs.get("buffer_depth", 0))
        return metrics
