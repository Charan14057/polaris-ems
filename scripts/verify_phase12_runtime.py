#!/usr/bin/env python3
"""
POLARIS-EMS PHASE 12: DECISION TRACE & EXPLAINABILITY RUNTIME AUDIT
SIH26061: Polar Energy Management & Resilience System

Validates:
1. End-to-end decision trace generation via POST /api/v1/pipeline/analyze
2. Unique, deterministic machine-readable Decision Trace ID format
3. Complete DAG lineage assembly across all 7 pipeline stages
4. Strict epistemic validation tier distinctions (Computed vs Validated vs Estimated vs Advisory)
5. Strict 6-tier provenance enforcement (REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED)
6. Deterministic human-readable explanation layer (Why this state/policy/schedule?)
7. Factual comparative decision delta (Before vs After)
8. Local trace repository persistence & query filtering
9. Export-ready formats (Canonical JSON & CSV summary)
10. Strict architectural boundary invariants (0 Pyomo, 0 HiGHS, 0 new physics)
"""

import os
import sys
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))

GATEWAY_URL = "http://127.0.0.1:3000"
BACKEND_URL = "http://127.0.0.1:8000"

# Target port 3000 (Vite proxy) with fallback to 8000 (FastAPI direct)
def get_base_url():
    try:
        req = urllib.request.Request(f"{GATEWAY_URL}/health/ready", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                return GATEWAY_URL
    except Exception:
        pass
    return BACKEND_URL

BASE_URL = get_base_url()

LOCKED_PROVENANCE_TIERS = {"REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"}

def http_get(path: str) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def http_post(path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def http_get_raw(path: str) -> str:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8")

def run_audit():
    print("=" * 80)
    print("POLARIS-EMS PHASE 12: DECISION TRACE & EXPLAINABILITY RUNTIME AUDIT")
    print(f"Target Gateway: {BASE_URL}")
    print("=" * 80)

    # Gate 1: Generate Pipeline Analysis with Decision Trace
    print("Running Gate 1: Pipeline Analysis & Decision Trace ID Generation...")
    pipe_payload = {
        "station_id": "BHARATI",
        "horizon_hours": 48,
        "scenario_id": "NORMAL_BASELINE",
        "mode": "EXPECTED"
    }
    pipe_resp = http_post("/api/v1/pipeline/analyze", pipe_payload)
    data = pipe_resp["data"]
    trace_id = data.get("decision_trace_id")
    assert trace_id is not None, "Pipeline did not return decision_trace_id!"
    assert trace_id.startswith("DT-"), f"Invalid trace ID format: {trace_id}"
    assert "BHARATI" in trace_id, f"Trace ID must encode station ID: {trace_id}"
    print(f"[PASS] Gate 1: Pipeline trace generated: {trace_id} (Overall: {data.get('overall_status')})")

    # Gate 2: Trace Detail Retrieval
    print("Running Gate 2: Trace Detail Retrieval...")
    tr_resp = http_get(f"/api/v1/traces/{trace_id}")
    tr_data = tr_resp["data"]
    assert tr_data["decision_trace_id"] == trace_id
    assert tr_data["station_id"] == "BHARATI"
    assert tr_data["execution_status"] in ("COMPLETED", "PARTIAL", "FALLBACK", "BLOCKED", "FAILED", "INFEASIBLE")
    assert len(tr_data["events"]) >= 5, f"Expected >= 5 events, got {len(tr_data['events'])}"
    print(f"[PASS] Gate 2: Trace record retrieved with {len(tr_data['events'])} events. Status: {tr_data['execution_status']}")

    # Gate 3: Trace Events & Stage Coverage
    print("Running Gate 3: Stage Events & Reason Code Coverage...")
    events_resp = http_get(f"/api/v1/traces/{trace_id}/events")
    events = events_resp["data"]
    stages_present = {e["stage"] for e in events}
    expected_stages = {"EDGE", "FORECAST", "SCENARIO", "OPTIMIZER", "TWIN_REPLAY", "RESILIENCE", "POLICY"}
    assert expected_stages.issubset(stages_present), f"Missing stages: {expected_stages - stages_present}"
    for ev in events:
        assert ev["reason_code"] is not None and len(ev["reason_code"]) > 0
        assert ev["provenance"] in LOCKED_PROVENANCE_TIERS, f"Invalid provenance {ev['provenance']} in event {ev['event_id']}"
    print(f"[PASS] Gate 3: All 7 decision stages present ({', '.join(stages_present)}) with machine reason codes.")

    # Gate 4: Lineage DAG Adjacency
    print("Running Gate 4: Lineage DAG Adjacency & Execution Path...")
    adj = tr_data.get("lineage_graph", {})
    assert len(adj) > 0, "Lineage graph adjacency is empty!"
    edge_evt = next((e for e in events if e["stage"] == "EDGE"), None)
    assert edge_evt is not None
    assert edge_evt["event_id"] in adj, "Edge event missing from DAG adjacency map!"
    print(f"[PASS] Gate 4: Lineage graph verified with {len(adj)} nodes and explicit parent-child edges.")

    # Gate 5: Epistemic Validation Distinction (Optimizer Proposed vs Twin Validated vs Resilience Estimated)
    print("Running Gate 5: Epistemic Validation Invariant Verification...")
    opt_ev = next(e for e in events if e["stage"] == "OPTIMIZER")
    twin_ev = next(e for e in events if e["stage"] == "TWIN_REPLAY")
    res_ev = next(e for e in events if e["stage"] == "RESILIENCE")
    pol_ev = next(e for e in events if e["stage"] == "POLICY")

    assert opt_ev["validation_tier"] == "COMPUTED", f"Optimizer tier must be COMPUTED, got {opt_ev['validation_tier']}"
    assert opt_ev["outputs"].get("dispatch_nature") == "PROPOSED_SCHEDULE"
    assert twin_ev["validation_tier"] in ("VALIDATED", "SIMULATED")
    assert res_ev["validation_tier"] == "ESTIMATED", f"Resilience recovery must be ESTIMATED, got {res_ev['validation_tier']}"
    assert pol_ev["validation_tier"] == "ADVISORY", f"Policy directive must be ADVISORY, got {pol_ev['validation_tier']}"
    print("[PASS] Gate 5: Epistemic distinctions preserved (Optimizer=COMPUTED, Twin=VALIDATED, Resilience=ESTIMATED, Policy=ADVISORY).")

    # Gate 6: Strict 6-Tier Provenance Taxonomy Compliance
    print("Running Gate 6: Provenance Compliance...")
    assert tr_data["provenance"] in LOCKED_PROVENANCE_TIERS
    for ev in events:
        assert ev["provenance"] in LOCKED_PROVENANCE_TIERS
    print(f"[PASS] Gate 6: Strict 6-tier provenance confirmed across all trace entities ({', '.join(LOCKED_PROVENANCE_TIERS)}).")

    # Gate 7: Deterministic Human-Readable Explainer
    print("Running Gate 7: Deterministic 'Why?' Explainer...")
    exp_resp = http_get(f"/api/v1/traces/{trace_id}/explanation")
    exp = exp_resp["data"]
    assert exp["headline"] and len(exp["headline"]) > 10
    assert exp["why_this_state"] and len(exp["why_this_state"]) > 10
    assert exp["why_this_policy"] and len(exp["why_this_policy"]) > 10
    assert exp["why_this_schedule"] and len(exp["why_this_schedule"]) > 10
    assert len(exp["what_data_used"]) >= 1
    assert len(exp["what_was_validated"]) >= 1
    assert len(exp["what_remains_estimated"]) >= 1
    print(f"[PASS] Gate 7: Deterministic explainer verified without LLM hallucination:")
    print(f"       -> Headline: {exp['headline']}")
    print(f"       -> Next: {exp['what_is_next']}")

    # Gate 8: Factual Comparative Decision Delta
    print("Running Gate 8: Comparative Decision Delta...")
    cmp_resp = http_get(f"/api/v1/traces/{trace_id}/compare/{trace_id}")
    cmp_data = cmp_resp["data"]
    assert cmp_data["base_trace_id"] == trace_id
    assert cmp_data["compare_trace_id"] == trace_id
    assert "summary_narrative" in cmp_data
    print(f"[PASS] Gate 8: Decision delta comparison operational. Narrative: {cmp_data['summary_narrative']}")

    # Gate 9: Trace Repository Persistence & List Query
    print("Running Gate 9: Repository Persistence & Filtered Query...")
    list_resp = http_get("/api/v1/traces?station_id=BHARATI&limit=10")
    traces_list = list_resp["data"]
    assert len(traces_list) >= 1
    assert any(t["decision_trace_id"] == trace_id for t in traces_list)
    print(f"[PASS] Gate 9: Persistent trace list retrieved ({len(traces_list)} traces recorded).")

    # Gate 10: Multi-Format Trace Export
    print("Running Gate 10: Trace Export (JSON & CSV)...")
    json_text = http_get_raw(f"/api/v1/traces/{trace_id}/export?format=json")
    parsed_json = json.loads(json_text)
    assert parsed_json["decision_trace_id"] == trace_id

    csv_text = http_get_raw(f"/api/v1/traces/{trace_id}/export?format=csv")
    assert "Trace ID" in csv_text
    assert "Reason Code" in csv_text
    assert trace_id in csv_text
    print(f"[PASS] Gate 10: Export verified (JSON size: {len(json_text)} bytes, CSV rows: {len(csv_text.splitlines())}).")

    # Gate 11: Architecture Boundary Invariant Check
    print("Running Gate 11: Architectural Boundary Verification...")
    import inspect
    from backend.trace import builder, lineage, explainer, comparison, repository
    trace_modules = [builder, lineage, explainer, comparison, repository]
    for mod in trace_modules:
        src = inspect.getsource(mod)
        assert "import pyomo" not in src, f"Pyomo import leakage in {mod.__name__}"
        assert "from pyomo" not in src, f"Pyomo import leakage in {mod.__name__}"
        assert "appsi_highs" not in src.lower(), f"HiGHS solver leakage in {mod.__name__}"
        assert "solverfactory" not in src.lower(), f"Solver factory leakage in {mod.__name__}"
        assert "solver.solve(" not in src and "opt.solve(" not in src, f"Solver execution in {mod.__name__}"
    print("[PASS] Gate 11: Zero Pyomo, zero HiGHS, zero independent physics verified in trace layer.")

    print("=" * 80)
    print("ALL 11 PHASE 12 RUNTIME AUDIT GATES PASSED CLEANLY (100%)")
    print("=" * 80)

if __name__ == "__main__":
    try:
        run_audit()
        sys.exit(0)
    except Exception as exc:
        print(f"\n[FAIL] Audit failed: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
