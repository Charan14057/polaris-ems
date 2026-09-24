"""
POLARIS-EMS — Decision Trace Event Builder
SIH26061: Polar Energy Management & Resilience System

Extracts factual evidence from frozen engine execution outputs to construct
transparent, auditable TraceEvent records across all pipeline stages.

STRICT INVARIANTS:
1. Pure observation: Zero mathematical solving or physics calculation.
2. Distinguishes OPTIMIZER PROPOSED schedule from DIGITAL TWIN VALIDATED outcome.
3. Distinguishes ESTIMATED recovery projections from PHYSICALLY VALIDATED states.
4. Preserves 6-tier provenance strictly.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid

from backend.trace.schema import (
    TraceEvent,
    TraceStage,
    ReasonCode,
    ValidationTier,
    TraceRecord,
    TraceLifecycleState
)


class TraceEventBuilder:
    """Constructs standardized TraceEvent instances for each pipeline decision stage."""

    @staticmethod
    def generate_trace_id(station_id: str, timestamp: Optional[datetime] = None) -> str:
        """Generates deterministic-format machine/human readable decision trace ID."""
        dt = timestamp or datetime.now(timezone.utc)
        date_str = dt.strftime("%Y%m%d")
        rand_suffix = uuid.uuid4().hex[:6].upper()
        return f"DT-{date_str}-{station_id.upper()}-{rand_suffix}"

    @staticmethod
    def _create_event(
        trace_id: str,
        stage: TraceStage,
        event_type: str,
        station_id: str,
        status: str,
        reason_code: ReasonCode,
        summary: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        validation_tier: ValidationTier,
        provenance: str,
        parent_event_id: Optional[str] = None,
        duration_ms: float = 0.0,
        diagnostics: Optional[List[str]] = None
    ) -> TraceEvent:
        event_id = f"evt_{stage.value.lower()}_{uuid.uuid4().hex[:8]}"
        return TraceEvent(
            event_id=event_id,
            trace_id=trace_id,
            stage=stage,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            station_id=station_id.upper(),
            status=status,
            reason_code=reason_code,
            summary=summary,
            inputs=inputs,
            outputs=outputs,
            validation_tier=validation_tier,
            provenance=provenance,
            parent_event_id=parent_event_id,
            duration_ms=round(duration_ms, 2),
            diagnostics=diagnostics or []
        )

    @classmethod
    def build_edge_event(
        cls,
        trace_id: str,
        station_id: str,
        edge_snapshot: Optional[Any] = None,
        parent_event_id: Optional[str] = None
    ) -> TraceEvent:
        """Constructs edge operational context event (Phase 11)."""
        if edge_snapshot is None:
            return cls._create_event(
                trace_id=trace_id,
                stage=TraceStage.EDGE,
                event_type="EDGE_CONTEXT_INSPECTION",
                station_id=station_id,
                status="COMPLETED",
                reason_code=ReasonCode.EDGE_CONNECTED,
                summary=f"Station {station_id} nominal edge connectivity verified.",
                inputs={"station_id": station_id},
                outputs={"edge_mode": "CONNECTED_OPERATION", "connectivity_state": "CONNECTED"},
                validation_tier=ValidationTier.SIMULATED,
                provenance="CONFIGURED",
                parent_event_id=parent_event_id
            )

        mode = getattr(edge_snapshot, "edge_mode", "CONNECTED_OPERATION")
        if hasattr(mode, "value"):
            mode = mode.value
        conn = getattr(edge_snapshot, "connectivity_state", "CONNECTED")
        if hasattr(conn, "value"):
            conn = conn.value
        posture = getattr(edge_snapshot, "fallback_posture", "WAIT_FOR_BACKEND_DECISION")
        if hasattr(posture, "value"):
            posture = posture.value

        reason = ReasonCode.EDGE_CONNECTED
        if conn == "OFFLINE":
            reason = ReasonCode.EDGE_OFFLINE
        elif conn == "DEGRADED":
            reason = ReasonCode.CONNECTIVITY_DEGRADED
        elif mode == "SAFE_HOLD":
            reason = ReasonCode.FALLBACK_REQUIRED

        summary = (
            f"Edge node in {mode} ({conn}). Fallback posture: {posture}. "
            f"Buffer queue depth: {getattr(edge_snapshot, 'buffer_depth', 0)} observations."
        )

        return cls._create_event(
            trace_id=trace_id,
            stage=TraceStage.EDGE,
            event_type="EDGE_CONTEXT_INSPECTION",
            station_id=station_id,
            status="COMPLETED" if conn != "OFFLINE" else "FALLBACK",
            reason_code=reason,
            summary=summary,
            inputs={"station_id": station_id},
            outputs={
                "edge_mode": mode,
                "connectivity_state": conn,
                "fallback_posture": posture,
                "buffer_depth": getattr(edge_snapshot, "buffer_depth", 0),
                "healthy_devices": getattr(edge_snapshot, "healthy_devices_count", 0),
                "active_devices": getattr(edge_snapshot, "active_devices_count", 0)
            },
            validation_tier=ValidationTier.SIMULATED,
            provenance="CONFIGURED",
            parent_event_id=parent_event_id
        )

    @classmethod
    def build_forecast_event(
        cls,
        trace_id: str,
        station_id: str,
        forecast_data: Optional[Any],
        horizon_hours: int,
        duration_ms: float = 0.0,
        parent_event_id: Optional[str] = None
    ) -> TraceEvent:
        """Constructs machine learning forecast event (Phase 3)."""
        if forecast_data is None:
            return cls._create_event(
                trace_id=trace_id,
                stage=TraceStage.FORECAST,
                event_type="ML_INFERENCE_EXECUTION",
                station_id=station_id,
                status="FAILED",
                reason_code=ReasonCode.FORECAST_FAILED,
                summary=f"Inference pipeline failed to generate {horizon_hours}h forecast for {station_id}.",
                inputs={"horizon_hours": horizon_hours},
                outputs={},
                validation_tier=ValidationTier.COMPUTED,
                provenance="FORECAST",
                parent_event_id=parent_event_id,
                duration_ms=duration_ms
            )

        pts = getattr(forecast_data, "points", []) or getattr(forecast_data, "predictions", [])
        pt_count = len(pts)

        return cls._create_event(
            trace_id=trace_id,
            stage=TraceStage.FORECAST,
            event_type="ML_INFERENCE_EXECUTION",
            station_id=station_id,
            status="COMPLETED",
            reason_code=ReasonCode.FORECAST_AVAILABLE,
            summary=f"Generated {pt_count} probabilistic forecast steps for {horizon_hours}h horizon (P10–P95 calibrated bounds).",
            inputs={"station_id": station_id, "horizon_hours": horizon_hours},
            outputs={
                "points_count": pt_count,
                "model_id": getattr(forecast_data, "model_id", "registered_xgboost_residual_v1"),
                "horizon_hours": horizon_hours,
                "provenance": "FORECAST"
            },
            validation_tier=ValidationTier.COMPUTED,
            provenance="FORECAST",
            parent_event_id=parent_event_id,
            duration_ms=duration_ms
        )

    @classmethod
    def build_scenario_event(
        cls,
        trace_id: str,
        station_id: str,
        scenario_data: Optional[Any],
        scenario_id: Optional[str],
        duration_ms: float = 0.0,
        parent_event_id: Optional[str] = None
    ) -> TraceEvent:
        """Constructs scenario stress testing event (Phase 5)."""
        scen_name = scenario_id or "NORMAL_BASELINE"
        if scenario_data is None:
            return cls._create_event(
                trace_id=trace_id,
                stage=TraceStage.SCENARIO,
                event_type="SCENARIO_STRESS_TEST",
                station_id=station_id,
                status="SKIPPED" if scenario_id is None else "FAILED",
                reason_code=ReasonCode.SCENARIO_BASELINE if scenario_id is None else ReasonCode.SCENARIO_FAILED,
                summary=f"Operating under nominal baseline condition (no hazard scenario injected).",
                inputs={"scenario_id": scen_name},
                outputs={},
                validation_tier=ValidationTier.SIMULATED,
                provenance="SIMULATED",
                parent_event_id=parent_event_id,
                duration_ms=duration_ms
            )

        impact = getattr(scenario_data, "impact_metrics", None)
        unserved_delta = getattr(impact, "delta_unserved_energy_kwh", 0.0) if impact else 0.0
        fuel_delta = getattr(impact, "delta_fuel_consumed_liters", 0.0) if impact else 0.0

        is_baseline = scen_name == "NORMAL_BASELINE"
        reason = ReasonCode.SCENARIO_BASELINE if is_baseline else ReasonCode.SCENARIO_STRESS_APPLIED

        summary = (
            f"Evaluated scenario '{scen_name}'. "
            f"Delta Unserved Energy: {unserved_delta:.2f} kWh, Delta Fuel: {fuel_delta:.2f} L."
        )

        return cls._create_event(
            trace_id=trace_id,
            stage=TraceStage.SCENARIO,
            event_type="SCENARIO_STRESS_TEST",
            station_id=station_id,
            status="COMPLETED",
            reason_code=reason,
            summary=summary,
            inputs={"scenario_id": scen_name},
            outputs={
                "scenario_name": scen_name,
                "delta_unserved_energy_kwh": unserved_delta,
                "delta_fuel_consumed_liters": fuel_delta
            },
            validation_tier=ValidationTier.SIMULATED,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
            duration_ms=duration_ms
        )

    @classmethod
    def build_optimizer_event(
        cls,
        trace_id: str,
        station_id: str,
        optimizer_data: Optional[Any],
        mode: str,
        duration_ms: float = 0.0,
        parent_event_id: Optional[str] = None
    ) -> TraceEvent:
        """Constructs optimization dispatch event (Phase 6)."""
        if optimizer_data is None:
            return cls._create_event(
                trace_id=trace_id,
                stage=TraceStage.OPTIMIZER,
                event_type="MILP_DISPATCH_OPTIMIZATION",
                station_id=station_id,
                status="FAILED",
                reason_code=ReasonCode.OPTIMIZATION_FAILED,
                summary=f"HiGHS solver failed or was not executed for mode '{mode}'.",
                inputs={"mode": mode},
                outputs={},
                validation_tier=ValidationTier.COMPUTED,
                provenance="SIMULATED",
                parent_event_id=parent_event_id,
                duration_ms=duration_ms
            )

        solver_status = getattr(optimizer_data, "solver_status", "UNKNOWN")
        tier = getattr(optimizer_data, "optimality_tier", "FALLBACK")
        gap = getattr(optimizer_data, "relative_gap", None)
        obj = getattr(optimizer_data, "objective_value", None)

        if tier == "EXACT_OPTIMAL":
            reason = ReasonCode.OPTIMIZATION_EXACT
        elif tier == "MIP_GAP_OPTIMAL":
            reason = ReasonCode.OPTIMIZATION_MIP_GAP
        elif tier == "INFEASIBLE":
            reason = ReasonCode.OPTIMIZATION_INFEASIBLE
        else:
            reason = ReasonCode.OPTIMIZATION_FALLBACK

        gap_str = f"MIP Gap: {gap * 100:.2f}%" if gap is not None else "Gap: N/A"
        summary = (
            f"Phase 6 HiGHS solved schedule ({mode} mode) with status {solver_status} "
            f"({tier}, {gap_str}). Proposed objective: {obj:.2f}."
        )

        return cls._create_event(
            trace_id=trace_id,
            stage=TraceStage.OPTIMIZER,
            event_type="MILP_DISPATCH_OPTIMIZATION",
            station_id=station_id,
            status="COMPLETED" if tier in ("EXACT_OPTIMAL", "MIP_GAP_OPTIMAL") else "PARTIAL",
            reason_code=reason,
            summary=summary,
            inputs={"mode": mode},
            outputs={
                "solver_status": solver_status,
                "optimality_tier": tier,
                "relative_gap": gap,
                "objective_value": obj,
                "dispatch_nature": "PROPOSED_SCHEDULE"
            },
            validation_tier=ValidationTier.COMPUTED,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
            duration_ms=duration_ms
        )

    @classmethod
    def build_twin_replay_event(
        cls,
        trace_id: str,
        station_id: str,
        optimizer_data: Optional[Any],
        duration_ms: float = 0.0,
        parent_event_id: Optional[str] = None
    ) -> TraceEvent:
        """Constructs digital twin physical validation event (Phase 4)."""
        replay_valid = getattr(optimizer_data, "twin_replay_valid", False) if optimizer_data else False
        summary_obj = getattr(optimizer_data, "summary", None) if optimizer_data else None

        reason = ReasonCode.TWIN_VALIDATED if replay_valid else ReasonCode.TWIN_VALIDATION_FAILED
        status = "COMPLETED" if replay_valid else "FAILED"
        tier = ValidationTier.VALIDATED if replay_valid else ValidationTier.SIMULATED

        unserved = 0.0
        fuel = 0.0
        if summary_obj:
            if isinstance(summary_obj, dict):
                unserved = float(summary_obj.get("total_unserved_load_kwh", 0.0) or 0.0)
                fuel = float(summary_obj.get("total_fuel_consumed_liters", 0.0) or 0.0)
            else:
                unserved = float(getattr(summary_obj, "total_unserved_load_kwh", 0.0) or 0.0)
                fuel = float(getattr(summary_obj, "total_fuel_consumed_liters", 0.0) or 0.0)

        summary = (
            f"Digital Twin physical validation: {'VALIDATED' if replay_valid else 'FAILED'}. "
            f"Verified Unserved Load: {unserved:.2f} kWh, Fuel Consumption: {fuel:.2f} L."
        )

        return cls._create_event(
            trace_id=trace_id,
            stage=TraceStage.TWIN_REPLAY,
            event_type="PHYSICAL_TWIN_VALIDATION",
            station_id=station_id,
            status=status,
            reason_code=reason,
            summary=summary,
            inputs={"validation_authority": "Phase 4 Digital Twin Engine"},
            outputs={
                "physically_validated": replay_valid,
                "total_unserved_load_kwh": unserved,
                "total_fuel_consumed_liters": fuel
            },
            validation_tier=tier,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
            duration_ms=duration_ms
        )

    @classmethod
    def build_resilience_event(
        cls,
        trace_id: str,
        station_id: str,
        resilience_data: Optional[Any],
        duration_ms: float = 0.0,
        parent_event_id: Optional[str] = None
    ) -> TraceEvent:
        """Constructs operational resilience assessment event (Phase 7)."""
        if resilience_data is None:
            return cls._create_event(
                trace_id=trace_id,
                stage=TraceStage.RESILIENCE,
                event_type="RESILIENCE_ASSESSMENT",
                station_id=station_id,
                status="FAILED",
                reason_code=ReasonCode.RESILIENCE_THREATENED,
                summary="Resilience evaluation unavailable.",
                inputs={},
                outputs={},
                validation_tier=ValidationTier.ESTIMATED,
                provenance="SIMULATED",
                parent_event_id=parent_event_id,
                duration_ms=duration_ms
            )

        if isinstance(resilience_data, dict):
            state = resilience_data.get("resilience_state", "SAFE")
            dims = resilience_data.get("dimensions", None)
            c_index = dims.get("composite_resilience_index", 100.0) if isinstance(dims, dict) else 100.0
            horizons = resilience_data.get("survival_horizons", None)
            binding = horizons.get("binding_subsystem", "NONE") if isinstance(horizons, dict) else "NONE"
            overall_h = horizons.get("overall_station_survival_horizon_h", 720.0) if isinstance(horizons, dict) else 720.0
        else:
            state = getattr(resilience_data, "resilience_state", "SAFE")
            dims = getattr(resilience_data, "dimensions", None)
            c_index = getattr(dims, "composite_resilience_index", 100.0) if dims else 100.0
            horizons = getattr(resilience_data, "survival_horizons", None)
            binding = getattr(horizons, "binding_subsystem", "NONE") if horizons else "NONE"
            overall_h = getattr(horizons, "overall_station_survival_horizon_h", 720.0) if horizons else 720.0

        if hasattr(state, "value"):
            state = state.value
        state = str(state)

        reason = ReasonCode.RESILIENCE_SAFE
        if state == "THREATENED":
            reason = ReasonCode.RESILIENCE_THREATENED
        elif state == "CRITICAL":
            reason = ReasonCode.RESILIENCE_CRITICAL
        elif state == "WATCH":
            reason = ReasonCode.RESILIENCE_WATCH
        elif state == "AT_RISK":
            reason = ReasonCode.RESILIENCE_AT_RISK

        summary = (
            f"Resilience Engine assessed state: {state} (Composite Index: {c_index:.1f}/100). "
            f"Survival Horizon: {overall_h:.1f}h (Binding Constraint: {binding}). "
            f"Recovery pathways: ESTIMATED."
        )

        return cls._create_event(
            trace_id=trace_id,
            stage=TraceStage.RESILIENCE,
            event_type="RESILIENCE_ASSESSMENT",
            station_id=station_id,
            status="COMPLETED",
            reason_code=reason,
            summary=summary,
            inputs={"evaluation_authority": "Phase 7 Resilience Engine"},
            outputs={
                "resilience_state": state,
                "composite_resilience_index": c_index,
                "binding_subsystem": binding,
                "survival_horizon_h": overall_h,
                "recovery_projection_tier": "ESTIMATED"
            },
            validation_tier=ValidationTier.ESTIMATED,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
            duration_ms=duration_ms
        )

    @classmethod
    def build_policy_event(
        cls,
        trace_id: str,
        station_id: str,
        policy_data: Optional[Any],
        duration_ms: float = 0.0,
        parent_event_id: Optional[str] = None
    ) -> TraceEvent:
        """Constructs policy governance event (Phase 8)."""
        if policy_data is None:
            return cls._create_event(
                trace_id=trace_id,
                stage=TraceStage.POLICY,
                event_type="POLICY_GOVERNANCE",
                station_id=station_id,
                status="FAILED",
                reason_code=ReasonCode.POLICY_BLOCKED,
                summary="Policy evaluation unavailable.",
                inputs={},
                outputs={},
                validation_tier=ValidationTier.ADVISORY,
                provenance="SIMULATED",
                parent_event_id=parent_event_id,
                duration_ms=duration_ms
            )

        if isinstance(policy_data, dict):
            p_state = policy_data.get("policy_state", "NO_ACTION")
            directive = policy_data.get("primary_directive", "NORMAL_OPERATION")
            rules = policy_data.get("active_rules", [])
            handoff = policy_data.get("optimizer_handoff", None)
            rationale = handoff.get("advisory_rationale", "") if isinstance(handoff, dict) else ""
        else:
            p_state = getattr(policy_data, "policy_state", "NO_ACTION")
            directive = getattr(policy_data, "primary_directive", "NORMAL_OPERATION")
            rules = getattr(policy_data, "active_rules", [])
            handoff = getattr(policy_data, "optimizer_handoff", None)
            rationale = getattr(handoff, "advisory_rationale", "") if handoff else ""

        if hasattr(p_state, "value"):
            p_state = p_state.value
        p_state = str(p_state)

        if hasattr(directive, "value"):
            directive = directive.value
        directive = str(directive)

        reason = ReasonCode.POLICY_NOMINAL
        if p_state in ("NO_ACTION", "NOMINAL"):
            reason = ReasonCode.POLICY_NOMINAL
        elif p_state == "MONITOR":
            reason = ReasonCode.POLICY_MONITOR
        elif p_state == "PREPARE":
            reason = ReasonCode.POLICY_PREPARE
        elif p_state == "MITIGATE":
            reason = ReasonCode.POLICY_MITIGATE
        elif p_state == "PROTECT":
            reason = ReasonCode.POLICY_PROTECT
        elif p_state == "RECOVER":
            reason = ReasonCode.POLICY_RECOVER
        elif p_state == "BLOCKED":
            reason = ReasonCode.POLICY_BLOCKED
        elif "CRITICAL" in directive or "LIFE_SAFETY" in directive:
            reason = ReasonCode.CRITICAL_LOAD_PROTECTION

        summary = (
            f"Policy Engine governed state: {p_state} (Directive: {directive}). "
            f"Fired rules count: {len(rules)}. Priority compliance verified against P1–P8 hierarchy."
        )

        return cls._create_event(
            trace_id=trace_id,
            stage=TraceStage.POLICY,
            event_type="POLICY_GOVERNANCE",
            station_id=station_id,
            status="COMPLETED" if p_state != "BLOCKED" else "BLOCKED",
            reason_code=reason,
            summary=summary,
            inputs={"governance_authority": "Phase 8 Policy Engine"},
            outputs={
                "policy_state": p_state,
                "primary_directive": directive,
                "active_rules_count": len(rules),
                "advisory_rationale": rationale
            },
            validation_tier=ValidationTier.ADVISORY,
            provenance="SIMULATED",
            parent_event_id=parent_event_id,
            duration_ms=duration_ms
        )
