# Phase 12 Implementation Plan: Decision Trace, Explainability & End-to-End Auditability
**Project:** Polaris-EMS — Polar Energy Management & Resilience System (SIH26061)  
**Status:** In Progress (Frozen Baseline: Phases 1–11)

---

## 1. Executive Objective
Engineer an **observational, auditable, and deterministic decision trace layer** for Polaris-EMS. Phase 12 enables human operators and automated audits to answer:
- *What did the system decide?*
- *Why did it reach that state?*
- *What data, forecast, and scenario were evaluated?*
- *What did the optimizer solve, and what was the MIP gap?*
- *What did the Digital Twin validate versus what was merely proposed?*
- *What did the Resilience Engine conclude, and what was physically validated versus estimated?*
- *Which policy rule dictated the primary directive?*
- *Was the station connected or operating in a degraded/offline fallback posture?*
- *What changed from the previous decision?*

**Critical Invariant:** Phase 12 is an **audit and explainability layer**, NOT another decision engine. It observes, structures, persists, compares, and explains the outputs of existing frozen engines (Phases 3–11) with **zero** new solvers, **zero** duplicated physics equations, and **zero** modified policy rules.

---

## 2. Frozen Architectural Ownership & Invariants
- **Phase 3 ML:** Sole authority for load & renewable forecasts (`FORECAST`).
- **Phase 4 Digital Twin:** Sole authority for physical simulation & conservation equations (`SIMULATED`).
- **Phase 5 Scenario Engine:** Sole authority for hazard & environmental stress testing.
- **Phase 6 Optimizer:** Sole authority for dispatch optimization (Pyomo + HiGHS). Phase 12 contains **0** Pyomo/HiGHS code.
- **Phase 7 Resilience Engine:** Sole authority for survival horizon calculation and recovery options.
- **Phase 8 Policy Engine:** Sole authority for governance rules, priority tiers ($P_1\text{–}P_8$), and hysteresis.
- **Phase 9 API:** RESTful integration contract boundary.
- **Phase 10 Frontend:** Operational presentation boundary.
- **Phase 11 Edge:** Device intelligence, telemetry quality, connectivity state, and local buffer authority.
- **Strict 6-Tier Provenance Taxonomy:**
  $$\{\text{REAL}, \text{CONFIGURED}, \text{ASSUMED}, \text{SYNTHETIC}, \text{FORECAST}, \text{SIMULATED}\}$$
  No 7th tier (`LIVE`, `REAL_TIME`, `EDGE`, `TELEMETRY`, etc.) permitted.

---

## 3. Subsystem Architecture & Module Organization

```
backend/
└── trace/
    ├── __init__.py           # Package exports
    ├── schema.py             # Enums, TraceRecord, TraceEvent, ReasonCode, TraceSummary
    ├── builder.py            # Event extraction and trace builder across stages
    ├── lineage.py            # Parent-child lineage graph construction & execution paths
    ├── explainer.py          # Deterministic human-readable explanation generator (NO LLM)
    ├── comparison.py         # Two-trace comparative delta engine (before vs after)
    ├── repository.py         # File/In-memory persistent repository with retention & indexing
    └── engine.py             # Trace service coordinator
backend/api/
├── schemas/trace.py          # REST request/response schemas for /api/v1/traces
├── adapters/trace_adapter.py # Domain to API response translation
└── routes/traces.py          # REST endpoints under /api/v1/traces
frontend/src/
├── api/client.ts             # Typed trace API client methods
├── api/types.ts              # Synchronized TypeScript interfaces for trace domain
└── views/DecisionTraceView.tsx # Expanded Decision Trace Workspace with timeline, graph, why panel, diff
tests/
└── test_phase12_trace.py     # Comprehensive automated test suite
```

---

## 4. Key Milestones

1. **Schema Design (`backend/trace/schema.py`):**
   - Unique `decision_trace_id` (`DT-YYYYMMDD-STATION-XXXXXX`).
   - Lifecycle states: `CREATED`, `RUNNING`, `COMPLETED`, `PARTIAL`, `BLOCKED`, `INFEASIBLE`, `FALLBACK`, `FAILED`.
   - Canonical `TraceEvent` with stage (`FORECAST`, `SCENARIO`, `OPTIMIZER`, `TWIN_REPLAY`, `RESILIENCE`, `POLICY`, `EDGE`, `RECONCILIATION`), inputs, outputs, validation status, provenance.
   - Machine-readable `ReasonCode` taxonomy.
2. **Trace Event Builder & Stage Adapters (`backend/trace/builder.py`, `lineage.py`):**
   - Extracts factual evidence from Phase 3 forecast results, Phase 5 scenario outcomes, Phase 6 optimizer results, Phase 4 twin replay validations, Phase 7 resilience assessments, Phase 8 policy traces, and Phase 11 edge snapshots.
   - Maintains explicit distinction between `OPTIMIZER_PROPOSED` and `TWIN_VALIDATED`, and between `ESTIMATED` and `PHYSICALLY_VALIDATED`.
3. **Deterministic Explainer (`backend/trace/explainer.py`):**
   - Generates structured, deterministic text answers to "Why this state?", "Why this policy?", "What data was used?", "What was validated?", "What remains estimated?", "What changed?".
   - Zero hallucinated rationale; derived solely from factual engine outputs.
4. **Comparative Delta Engine (`backend/trace/comparison.py`):**
   - Evaluates factual state transitions, numerical deltas, fuel differentials, and unserved energy differences between any two compatible traces.
5. **Persistence Repository (`backend/trace/repository.py`):**
   - Deterministic local repository saving traces to `reports/traces/` with in-memory caching, indexing by station and timestamp, bounded retention, and export utilities.
6. **API Integration (`backend/api/routes/traces.py`):**
   - Endpoints: `GET /traces`, `GET /traces/{id}`, `GET /traces/{id}/events`, `GET /traces/{id}/summary`, `GET /traces/{id}/explanation`, `GET /traces/{id}/compare/{other_id}`, `GET /traces/{id}/export`.
   - Backward-compatible linkage in `POST /api/v1/pipeline/analyze`.
7. **Frontend Workspace Expansion (`frontend/src/views/DecisionTraceView.tsx`):**
   - Stage timeline, lineage DAG, "Why?" explanation panel, trace diff inspector, evidence panel, provenance badges, and JSON/CSV export buttons.
8. **Verification & Regression:**
   - 100% pass on new Phase 12 test suite.
   - 100% pass on 217 existing backend tests.
   - 100% pass on frontend tests & build.
   - 100% pass on Phase 10 (13/13) and Phase 11 (10/10) runtime audit scripts.
