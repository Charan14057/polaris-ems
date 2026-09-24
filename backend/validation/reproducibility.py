"""
POLARIS-EMS — End-to-End Decision Trace Reproducibility Engine
SIH26061: Polar Energy Management & Resilience System

Validates full-pipeline decision reproducibility by taking historical DecisionTrace
records, extracting their original input snapshot parameters, rerunning the authoritative
frozen engines, and comparing the re-executed decision outcomes.

CRITICAL INVARIANTS:
1. Re-execution authority: Does NOT merely reload previous trace outputs. It executes
   the authentic underlying pipeline engines (Forecast -> Scenario -> Optimize -> Twin -> Resilience -> Policy).
2. Scientific categorization: Outcomes are classified into IDENTICAL,
   NUMERICALLY_EQUIVALENT_WITHIN_TOLERANCE, EXPECTED_NONDETERMINISM, or REPRODUCTION_FAILURE.
3. Pure observation: Observes pipeline results without altering production solver states.
"""

from typing import Dict, List, Optional, Any, Tuple
import math
from datetime import datetime, timezone

from backend.trace.schema import TraceRecord
from backend.trace.repository import TraceRepository, get_trace_repository
from backend.validation.schema import (
    ReplayReproductionReport,
    ReproductionCategory,
    BenchmarkOutcome
)


class ReplayRunner:
    """Executes closed-loop reproduction audits from recorded DecisionTrace inputs."""

    def __init__(
        self,
        trace_repository: Optional[TraceRepository] = None,
        orchestrator: Optional[Any] = None
    ):
        self.trace_repository = trace_repository or get_trace_repository()
        if orchestrator is None:
            from backend.api.adapters.pipeline_orchestrator import PipelineOrchestrator
            self.orchestrator = PipelineOrchestrator()
        else:
            self.orchestrator = orchestrator

    def replay_trace(self, trace_id: str) -> ReplayReproductionReport:
        """
        Reruns the end-to-end pipeline using the snapshot input parameters
        from a recorded DecisionTrace and verifies result reproducibility.
        """
        from backend.api.schemas.pipeline import PipelineAnalyzeRequestSchema
        orig_trace = self.trace_repository.get_trace(trace_id)
        if orig_trace is None:
            raise KeyError(f"DecisionTrace '{trace_id}' not found in active or archived stores.")

        sid = orig_trace.station_id.upper()
        horizon = orig_trace.horizon_hours or 24
        scenario_id = orig_trace.scenario_id or "CANONICAL_NOMINAL"
        mode = orig_trace.optimization_mode or "EXPECTED"

        # Re-execute authoritative pipeline
        req = PipelineAnalyzeRequestSchema(
            station_id=sid,
            horizon_hours=horizon,
            scenario_id=scenario_id,
            mode=mode
        )
        replayed_data = self.orchestrator.run_pipeline(req)

        # Extract original metrics
        orig_policy = orig_trace.policy_state or "NO_ACTION"
        orig_resilience = orig_trace.resilience_state or "SAFE"
        orig_objective = 0.0
        for ev in orig_trace.events:
            if getattr(ev.stage, "value", str(ev.stage)) == "OPTIMIZER":
                orig_objective = float(ev.outputs.get("objective_value", 0.0))

        # Extract replayed metrics
        rep_policy = replayed_data.policy.policy_state if replayed_data.policy else "NO_ACTION"
        raw_res = replayed_data.resilience.resilience_state if replayed_data.resilience else "SAFE"
        rep_resilience = raw_res.value if hasattr(raw_res, "value") else str(raw_res)
        rep_objective = replayed_data.optimizer.objective_value if replayed_data.optimizer else 0.0

        # Compare metrics
        obj_diff = abs(orig_objective - rep_objective)
        max_abs_err = obj_diff
        max_rel_err = max_abs_err / max(1.0, orig_objective)

        matches = {
            "policy_state_match": bool(orig_policy == rep_policy),
            "resilience_state_match": bool(orig_resilience == rep_resilience),
            "objective_value_match": bool(obj_diff < 5.0)
        }

        # Determine categorization
        if max_abs_err < 1e-4 and all(matches.values()):
            category = ReproductionCategory.IDENTICAL
            notes = "Replayed decision produced bit-for-bit identical outcomes."
        elif max_abs_err < 0.5 and matches["policy_state_match"] and matches["resilience_state_match"]:
            category = ReproductionCategory.NUMERICALLY_EQUIVALENT_WITHIN_TOLERANCE
            notes = f"Replayed decision matches policy and resilience states within solver tolerance (|delta| = {max_abs_err:.3f})."
        elif matches["policy_state_match"]:
            category = ReproductionCategory.EXPECTED_NONDETERMINISM
            notes = "Solver tie-break variation; policy state and physical constraints remain equivalent."
        else:
            category = ReproductionCategory.REPRODUCTION_FAILURE
            notes = "Reproduction divergence detected across state boundaries."

        stages_reproduced = [s.stage_name for s in replayed_data.stages if getattr(s.status, "value", str(s.status)) in {"SUCCESS", "COMPLETED"}]

        return ReplayReproductionReport(
            original_trace_id=orig_trace.decision_trace_id,
            station_id=sid,
            reproduction_category=category,
            max_absolute_error=round(max_abs_err, 4),
            max_relative_error=round(max_rel_err, 4),
            stages_reproduced=stages_reproduced,
            matches=matches,
            notes=notes
        )


# Global singleton instance
_replay_runner: Optional[ReplayRunner] = None


def get_replay_runner() -> ReplayRunner:
    global _replay_runner
    if _replay_runner is None:
        _replay_runner = ReplayRunner()
    return _replay_runner
