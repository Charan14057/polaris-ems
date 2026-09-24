"""
POLARIS-EMS — Phase 12 Decision Trace & Explainability Test Suite
SIH26061: Polar Energy Management & Resilience System

Validates:
1. Trace Schema & Invariants: unique ID, lifecycle states, locked 6-tier provenance.
2. Lineage Graph: DAG adjacency, parent-child links, terminal event identification.
3. Stage Event Builder: forecast, scenario, optimizer, twin replay, resilience, policy, edge.
4. Proposed vs Validated Distinction: optimizer proposed dispatch vs twin physically validated.
5. Estimated vs Validated Distinction: resilience recovery estimated vs twin validated.
6. Deterministic Explainer: factual "Why this state/policy/schedule?", zero LLM hallucination.
7. Decision Delta Comparison: two-trace state transitions, numerical differentials, directive diffs.
8. Persistence Repository: local file save, memory cache, list filters, bounded retention, JSON/CSV export.
9. API Endpoints: GET /traces, /traces/{id}, /events, /summary, /explanation, /compare, /export.
10. Architectural Boundary: zero Pyomo, zero HiGHS, zero physical equations, zero solver invocations.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.trace.schema import (
    TraceLifecycleState,
    TraceStage,
    ValidationTier,
    ReasonCode,
    TraceEvent,
    TraceRecord,
    LOCKED_PROVENANCE_TIERS,
    validate_provenance_tier
)
from backend.trace.builder import TraceEventBuilder
from backend.trace.lineage import LineageGraphBuilder
from backend.trace.explainer import DeterministicExplainer
from backend.trace.comparison import TraceComparisonEngine
from backend.trace.repository import TraceRepository
from backend.trace.engine import TraceService
from backend.api.app import create_app


# =========================================================================
# 1. Schema & Provenance Invariants
# =========================================================================

def test_trace_schema_and_provenance():
    # Valid locked 6-tier provenance
    assert validate_provenance_tier("SIMULATED") == "SIMULATED"
    assert validate_provenance_tier("FORECAST") == "FORECAST"
    assert validate_provenance_tier("CONFIGURED") == "CONFIGURED"

    # 7th tier violation raises ValueError
    with pytest.raises(ValueError):
        validate_provenance_tier("LIVE")

    with pytest.raises(ValueError):
        validate_provenance_tier("REAL_TIME")

    with pytest.raises(ValueError):
        validate_provenance_tier("EDGE")

    trace_id = TraceEventBuilder.generate_trace_id("BHARATI")
    assert trace_id.startswith("DT-")
    assert "BHARATI" in trace_id


# =========================================================================
# 2. Stage Event Builder & Epistemic Distinctions
# =========================================================================

def test_event_builder_and_distinctions():
    trace_id = "DT-20260924-BHARATI-TEST01"

    # 1. Optimizer Proposed Dispatch
    opt_data = type("OptResult", (), {
        "solver_status": "OPTIMAL",
        "optimality_tier": "MIP_GAP_OPTIMAL",
        "relative_gap": 0.0299,
        "objective_value": 1420.5,
        "twin_replay_valid": True,
        "summary": type("OptSummary", (), {
            "total_unserved_load_kwh": 0.0,
            "total_fuel_consumed_liters": 195.4
        })()
    })()

    opt_ev = TraceEventBuilder.build_optimizer_event(trace_id, "BHARATI", opt_data, mode="EXPECTED")
    assert opt_ev.stage == TraceStage.OPTIMIZER
    assert opt_ev.reason_code == ReasonCode.OPTIMIZATION_MIP_GAP
    assert opt_ev.outputs["dispatch_nature"] == "PROPOSED_SCHEDULE"
    assert opt_ev.validation_tier == ValidationTier.COMPUTED

    # 2. Digital Twin Replay (PHYSICALLY VALIDATED)
    tw_ev = TraceEventBuilder.build_twin_replay_event(trace_id, "BHARATI", opt_data)
    assert tw_ev.stage == TraceStage.TWIN_REPLAY
    assert tw_ev.reason_code == ReasonCode.TWIN_VALIDATED
    assert tw_ev.validation_tier == ValidationTier.VALIDATED
    assert tw_ev.outputs["physically_validated"] is True

    # 3. Resilience Assessment (ESTIMATED recovery)
    res_data = type("ResResult", (), {
        "resilience_state": "THREATENED",
        "dimensions": type("Dims", (), {"composite_resilience_index": 82.5})(),
        "survival_horizons": type("Horiz", (), {
            "binding_subsystem": "FUEL",
            "overall_station_survival_horizon_h": 144.0
        })()
    })()

    res_ev = TraceEventBuilder.build_resilience_event(trace_id, "BHARATI", res_data)
    assert res_ev.stage == TraceStage.RESILIENCE
    assert res_ev.reason_code == ReasonCode.RESILIENCE_THREATENED
    assert res_ev.validation_tier == ValidationTier.ESTIMATED
    assert res_ev.outputs["recovery_projection_tier"] == "ESTIMATED"

    # 4. Policy Governance (ADVISORY Directive)
    pol_data = type("PolResult", (), {
        "policy_state": "MITIGATE",
        "primary_directive": "BLOCK_DISCRETIONARY_LOADS",
        "active_rules": ["RULE_P2_LOAD_SHED"],
        "optimizer_handoff": type("Handoff", (), {"advisory_rationale": "Mitigate load"})()
    })()

    pol_ev = TraceEventBuilder.build_policy_event(trace_id, "BHARATI", pol_data)
    assert pol_ev.stage == TraceStage.POLICY
    assert pol_ev.reason_code == ReasonCode.POLICY_MITIGATE
    assert pol_ev.validation_tier == ValidationTier.ADVISORY
    assert pol_ev.outputs["primary_directive"] == "BLOCK_DISCRETIONARY_LOADS"


# =========================================================================
# 3. Lineage Graph & Execution Paths
# =========================================================================

def test_lineage_graph_assembly():
    trace_id = "DT-20260924-BHARATI-LIN001"
    events = [
        TraceEvent(
            event_id="evt_edge_1",
            trace_id=trace_id,
            stage=TraceStage.EDGE,
            event_type="EDGE_CONTEXT",
            station_id="BHARATI",
            status="COMPLETED",
            reason_code=ReasonCode.EDGE_CONNECTED,
            summary="Edge connected",
            validation_tier=ValidationTier.SIMULATED,
            provenance="CONFIGURED"
        ),
        TraceEvent(
            event_id="evt_forecast_1",
            trace_id=trace_id,
            stage=TraceStage.FORECAST,
            event_type="FORECAST",
            station_id="BHARATI",
            status="COMPLETED",
            reason_code=ReasonCode.FORECAST_AVAILABLE,
            summary="Forecast ready",
            validation_tier=ValidationTier.COMPUTED,
            provenance="FORECAST",
            parent_event_id="evt_edge_1"
        ),
        TraceEvent(
            event_id="evt_scenario_1",
            trace_id=trace_id,
            stage=TraceStage.SCENARIO,
            event_type="SCENARIO",
            station_id="BHARATI",
            status="COMPLETED",
            reason_code=ReasonCode.SCENARIO_STRESS_APPLIED,
            summary="Blizzard scenario",
            validation_tier=ValidationTier.SIMULATED,
            provenance="SIMULATED",
            parent_event_id="evt_forecast_1"
        )
    ]

    adj = LineageGraphBuilder.build_adjacency(events)
    assert adj["__root__"] == ["evt_edge_1"]
    assert adj["evt_edge_1"] == ["evt_forecast_1"]
    assert adj["evt_forecast_1"] == ["evt_scenario_1"]

    path = LineageGraphBuilder.extract_execution_path(events)
    assert len(path) == 3
    assert path[0] == "EDGE (COMPLETED)"
    assert path[1] == "FORECAST (COMPLETED)"
    assert path[2] == "SCENARIO (COMPLETED)"

    rec = LineageGraphBuilder.assemble_trace_record(trace_id, "BHARATI", events)
    assert rec.execution_status == TraceLifecycleState.PARTIAL  # Only 3 stages executed


# =========================================================================
# 4. Deterministic Explainer Tests
# =========================================================================

def test_deterministic_explainer():
    trace_id = "DT-20260924-BHARATI-EXP01"
    events = [
        TraceEvent(
            event_id="e1",
            trace_id=trace_id,
            stage=TraceStage.RESILIENCE,
            event_type="RES",
            station_id="BHARATI",
            status="COMPLETED",
            reason_code=ReasonCode.RESILIENCE_THREATENED,
            summary="Resilience event",
            outputs={
                "resilience_state": "THREATENED",
                "composite_resilience_index": 78.4,
                "binding_subsystem": "FUEL",
                "survival_horizon_h": 120.0
            },
            validation_tier=ValidationTier.ESTIMATED,
            provenance="SIMULATED"
        ),
        TraceEvent(
            event_id="e2",
            trace_id=trace_id,
            stage=TraceStage.POLICY,
            event_type="POL",
            station_id="BHARATI",
            status="COMPLETED",
            reason_code=ReasonCode.POLICY_MITIGATE,
            summary="Policy event",
            outputs={
                "policy_state": "MITIGATE",
                "primary_directive": "BLOCK_DISCRETIONARY_LOADS",
                "active_rules_count": 2,
                "advisory_rationale": "Conserve fuel"
            },
            validation_tier=ValidationTier.ADVISORY,
            provenance="SIMULATED"
        )
    ]

    rec = LineageGraphBuilder.assemble_trace_record(trace_id, "BHARATI", events)
    exp = DeterministicExplainer.explain(rec)

    assert "THREATENED" in exp.why_this_state
    assert "78.4" in exp.why_this_state
    assert "FUEL" in exp.why_this_state
    assert "BLOCK_DISCRETIONARY_LOADS" in exp.why_this_policy
    assert "MITIGATE" in exp.why_this_policy
    assert len(exp.what_remains_estimated) > 0
    assert ReasonCode.RESILIENCE_THREATENED in exp.reason_codes


# =========================================================================
# 5. Comparative Delta Engine Tests
# =========================================================================

def test_trace_comparison_engine():
    trace1 = TraceRecord(
        decision_trace_id="DT-01",
        station_id="BHARATI",
        resilience_state="SAFE",
        policy_state="NO_ACTION",
        primary_directive="NORMAL_OPERATION",
        edge_mode="CONNECTED_OPERATION",
        events=[
            TraceEvent(
                event_id="e1",
                trace_id="DT-01",
                stage=TraceStage.TWIN_REPLAY,
                event_type="TWIN",
                station_id="BHARATI",
                status="COMPLETED",
                reason_code=ReasonCode.TWIN_VALIDATED,
                summary="Twin replay",
                outputs={"total_fuel_consumed_liters": 100.0, "total_unserved_load_kwh": 0.0},
                validation_tier=ValidationTier.VALIDATED,
                provenance="SIMULATED"
            )
        ]
    )

    trace2 = TraceRecord(
        decision_trace_id="DT-02",
        station_id="BHARATI",
        resilience_state="THREATENED",
        policy_state="MITIGATE",
        primary_directive="BLOCK_DISCRETIONARY_LOADS",
        edge_mode="CONNECTED_OPERATION",
        events=[
            TraceEvent(
                event_id="e2",
                trace_id="DT-02",
                stage=TraceStage.TWIN_REPLAY,
                event_type="TWIN",
                station_id="BHARATI",
                status="COMPLETED",
                reason_code=ReasonCode.TWIN_VALIDATED,
                summary="Twin replay",
                outputs={"total_fuel_consumed_liters": 150.0, "total_unserved_load_kwh": 5.0},
                validation_tier=ValidationTier.VALIDATED,
                provenance="SIMULATED"
            )
        ]
    )

    delta = TraceComparisonEngine.compare(trace1, trace2)
    assert delta.state_transitions["resilience_state"] == ("SAFE", "THREATENED")
    assert delta.state_transitions["policy_state"] == ("NO_ACTION", "MITIGATE")
    assert delta.policy_directive_changed is True
    assert delta.numerical_deltas["fuel_consumed_liters"] == 50.0
    assert delta.numerical_deltas["unserved_load_kwh"] == 5.0
    assert "Comparison between Trace" in delta.summary_narrative


# =========================================================================
# 6. Persistence Repository Tests
# =========================================================================

def test_trace_repository_lifecycle(tmp_path):
    repo = TraceRepository(storage_dir=str(tmp_path), max_retention_traces=5)

    rec = TraceRecord(
        decision_trace_id="DT-SAVE-01",
        station_id="BHARATI",
        resilience_state="SAFE",
        policy_state="NO_ACTION",
        primary_directive="NORMAL_OPERATION",
        events=[]
    )

    # Save and retrieve
    repo.save_trace(rec)
    loaded = repo.get_trace("DT-SAVE-01")
    assert loaded is not None
    assert loaded.decision_trace_id == "DT-SAVE-01"
    assert loaded.explanation is not None

    # List with filters
    summaries = repo.list_traces(station_id="BHARATI")
    assert len(summaries) == 1
    assert summaries[0].decision_trace_id == "DT-SAVE-01"

    # Export JSON
    json_out = repo.export_trace_json("DT-SAVE-01")
    assert "DT-SAVE-01" in json_out

    # Export CSV
    csv_out = repo.export_trace_csv("DT-SAVE-01")
    assert "Trace ID,Station,Stage" in csv_out


# =========================================================================
# 7. Architecture Boundary Tests (Strict Invariants)
# =========================================================================

def test_architecture_boundary_invariants():
    import backend.trace.schema as ts
    import backend.trace.builder as tb
    import backend.trace.explainer as te
    import backend.trace.engine as teng

    for mod in [ts, tb, te, teng]:
        source = open(mod.__file__, "r", encoding="utf-8").read()
        assert "import pyomo" not in source
        assert "from pyomo" not in source
        assert "appsi_highs" not in source.lower()
        assert "solverfactory" not in source.lower()
        assert "solve(" not in source

    # Provenance taxonomy check
    assert len(LOCKED_PROVENANCE_TIERS) == 6
    assert "LIVE" not in LOCKED_PROVENANCE_TIERS
    assert "REAL_TIME" not in LOCKED_PROVENANCE_TIERS
    assert "EDGE" not in LOCKED_PROVENANCE_TIERS


# =========================================================================
# 8. API Integration Tests (FastAPI TestClient)
# =========================================================================

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_api_trace_endpoints(client):
    # 1. Run pipeline analysis to generate a live trace
    pipe_payload = {
        "station_id": "BHARATI",
        "horizon_hours": 48,
        "scenario_id": "NORMAL_BASELINE",
        "mode": "EXPECTED"
    }
    pipe_resp = client.post("/api/v1/pipeline/analyze", json=pipe_payload)
    assert pipe_resp.status_code == 200
    pipe_data = pipe_resp.json()["data"]
    trace_id = pipe_data.get("decision_trace_id")
    assert trace_id is not None
    assert trace_id.startswith("DT-")

    # 2. GET /api/v1/traces
    resp_list = client.get("/api/v1/traces?station_id=BHARATI")
    assert resp_list.status_code == 200
    traces = resp_list.json()["data"]
    assert len(traces) >= 1
    assert any(t["decision_trace_id"] == trace_id for t in traces)

    # 3. GET /api/v1/traces/{trace_id}
    resp_detail = client.get(f"/api/v1/traces/{trace_id}")
    assert resp_detail.status_code == 200
    detail = resp_detail.json()["data"]
    assert detail["decision_trace_id"] == trace_id
    assert len(detail["events"]) >= 5
    assert "lineage_graph" in detail

    # 4. GET /api/v1/traces/{trace_id}/events
    resp_events = client.get(f"/api/v1/traces/{trace_id}/events")
    assert resp_events.status_code == 200
    evs = resp_events.json()["data"]
    assert len(evs) >= 5

    # 5. GET /api/v1/traces/{trace_id}/summary
    resp_sum = client.get(f"/api/v1/traces/{trace_id}/summary")
    assert resp_sum.status_code == 200
    assert resp_sum.json()["data"]["decision_trace_id"] == trace_id

    # 6. GET /api/v1/traces/{trace_id}/explanation
    resp_exp = client.get(f"/api/v1/traces/{trace_id}/explanation")
    assert resp_exp.status_code == 200
    exp = resp_exp.json()["data"]
    assert "why_this_state" in exp
    assert "why_this_policy" in exp

    # 7. GET /api/v1/traces/{trace_id}/export?format=json
    resp_exp_json = client.get(f"/api/v1/traces/{trace_id}/export?format=json")
    assert resp_exp_json.status_code == 200
    assert "application/json" in resp_exp_json.headers["content-type"]

    # 8. GET /api/v1/traces/{trace_id}/export?format=csv
    resp_exp_csv = client.get(f"/api/v1/traces/{trace_id}/export?format=csv")
    assert resp_exp_csv.status_code == 200
    assert "text/csv" in resp_exp_csv.headers["content-type"]

    # 9. GET /api/v1/traces/{trace_id}/compare/{other_trace_id}
    resp_cmp = client.get(f"/api/v1/traces/{trace_id}/compare/{trace_id}")
    assert resp_cmp.status_code == 200
    cmp_data = resp_cmp.json()["data"]
    assert cmp_data["base_trace_id"] == trace_id
    assert cmp_data["compare_trace_id"] == trace_id

    # 10. 404 for unknown trace
    resp_404 = client.get("/api/v1/traces/DT-NONEXISTENT")
    assert resp_404.status_code == 404


def test_blocked_and_partial_pipeline_lineage():
    """Verify that a blocked or failed pipeline stops at the exact failure stage."""
    trace_id = "DT-20260924-BHARATI-BLOCKED01"
    ev1 = TraceEvent(
        event_id="evt_edge_1",
        trace_id=trace_id,
        stage=TraceStage.EDGE,
        event_type="EDGE_CONTEXT",
        station_id="BHARATI",
        status="COMPLETED",
        reason_code=ReasonCode.EDGE_CONNECTED,
        summary="Edge nominal",
        validation_tier=ValidationTier.SIMULATED,
        provenance="CONFIGURED"
    )
    ev2 = TraceEvent(
        event_id="evt_forecast_1",
        trace_id=trace_id,
        stage=TraceStage.FORECAST,
        event_type="FORECAST",
        station_id="BHARATI",
        status="COMPLETED",
        reason_code=ReasonCode.FORECAST_AVAILABLE,
        summary="Forecast nominal",
        validation_tier=ValidationTier.COMPUTED,
        provenance="FORECAST",
        parent_event_id="evt_edge_1"
    )
    ev3 = TraceEvent(
        event_id="evt_policy_blocked",
        trace_id=trace_id,
        stage=TraceStage.POLICY,
        event_type="POLICY_GOVERNANCE",
        station_id="BHARATI",
        status="BLOCKED",
        reason_code=ReasonCode.POLICY_BLOCKED,
        summary="Safety violation: Dispatch blocked by policy P1 life safety",
        validation_tier=ValidationTier.ADVISORY,
        provenance="SIMULATED",
        parent_event_id="evt_forecast_1"
    )

    rec = LineageGraphBuilder.assemble_trace_record(
        decision_trace_id=trace_id,
        station_id="BHARATI",
        events=[ev1, ev2, ev3]
    )

    assert rec.execution_status == TraceLifecycleState.BLOCKED
    term = LineageGraphBuilder.identify_terminal_event(rec.events)
    assert term is not None
    assert term.event_id == "evt_policy_blocked"
    assert len(rec.events) == 3
    # Ensure downstream stages were NOT artificially fabricated
    assert not any(e.stage == TraceStage.TWIN_REPLAY for e in rec.events)


def test_trace_security_and_sanitization(client):
    """Verify traces do not leak credentials or private infrastructure secrets."""
    resp = client.get("/api/v1/traces")
    assert resp.status_code == 200
    text_data = resp.text.lower()
    assert "password" not in text_data
    assert "secret" not in text_data
    assert "private_key" not in text_data
    assert "authorization" not in text_data

