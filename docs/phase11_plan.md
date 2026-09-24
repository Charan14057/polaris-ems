# Phase 11 Implementation Plan: Device Intelligence & Edge-First Field Resilience
**Project:** Polaris-EMS (SIH Problem Statement: SIH26061)  
**Status:** In Progress (Frozen Baseline: Phases 1–10)

---

## 1. Executive Objective
Extend Polaris-EMS with an **Edge-First / Hybrid / Connectivity-Degraded Field Resilience Architecture** for polar research stations (Bharati, Maitri, Himadri). Phase 11 enables the system to represent physical and virtual field devices, ingest and normalize heterogeneous telemetry, validate data quality deterministically, monitor device health and connectivity state, maintain a local bounded telemetry buffer, enforce safe fallback postures during network dropouts, and reconcile state upon reconnection—**without violating any frozen decision engine boundaries**.

---

## 2. Frozen Architectural Invariants & Ownership Boundaries
The Phase 1–10 pipeline remains strictly frozen and authoritative:
- **Phase 3 ML:** Sole authority for load, solar, and wind PREDICTION (`FORECAST`).
- **Phase 4 Digital Twin:** Sole authority for physical SIMULATION and electrical/thermal conservation equations (`SIMULATED`).
- **Phase 5 Scenario Engine:** Sole authority for environmental and hazard STRESS TESTING.
- **Phase 6 Optimizer:** Sole authority for mathematical DISPATCH OPTIMIZATION (MILP/MINLP via HiGHS). Phase 11 contains **zero** Pyomo/HiGHS code and does **not** choose generator schedules independently.
- **Phase 7 Resilience Engine:** Sole authority for operational RESILIENCE ASSESSMENT and recovery options.
- **Phase 8 Policy Engine:** Sole authority for rule-based GOVERNANCE (P1–P8 hierarchy).
- **Phase 9 API:** Sole authority for RESTful CONTRACTS and HTTP boundary integration.
- **Phase 10 Frontend:** Sole authority for OPERATIONAL VISUALIZATION.
- **Provenance:** Strictly limited to the locked 6-tier taxonomy:
  $$\{\text{REAL}, \text{CONFIGURED}, \text{ASSUMED}, \text{SYNTHETIC}, \text{FORECAST}, \text{SIMULATED}\}$$
  Quality states (`VALID`, `STALE`, etc.) and Edge modes (`CONNECTED_OPERATION`, `OFFLINE_EDGE`, etc.) are operational states, **never** provenance tiers.

---

## 3. Directory Layout & Module Specifications

```
backend/
└── edge/
    ├── __init__.py           # Package exports
    ├── schema.py             # Enums, Pydantic/dataclass schemas for devices, telemetry, quality, health, connectivity, state
    ├── devices.py            # Device profile registry & model
    ├── telemetry.py          # Telemetry normalization and envelope
    ├── quality.py            # Deterministic data quality validation engine
    ├── health.py             # Deterministic device health assessment engine
    ├── connectivity.py       # Edge-to-backend connectivity state machine
    ├── state.py              # Canonical edge state model & fallback postures
    ├── buffer.py             # Bounded local telemetry persistence and queue
    ├── reconciliation.py     # Deterministic state reconciliation upon reconnect
    ├── simulation.py         # Deterministic offline/degraded field simulation harness
    ├── adapters.py           # Adapters bridging edge state to Twin/Policy/Optimizer
    └── engine.py             # Edge orchestration coordinator
configs/
└── device_profiles.json      # Station-aware device configuration for BHARATI, MAITRI, HIMADRI
backend/api/
├── schemas/edge.py           # API request/response models for edge routes
├── adapters/edge_adapter.py  # API response mapping for edge domain
└── routes/edge.py            # REST endpoints under /api/v1/edge
frontend/src/
├── views/EdgeView.tsx        # 9th Operational Workspace: Edge & Device Intelligence
├── api/client.ts             # Edge API client methods
└── components/layout/Navbar.tsx # Navigation integration for Edge workspace
tests/
└── test_phase11_edge.py      # Comprehensive unit & integration test suite
```

---

## 4. Implementation Steps & Verification Gates

### Step 1: Interface & Boundary Inspection
- Verify all frozen dependencies (`backend/twin/`, `backend/policy/`, `backend/optimizer/`, `backend/api/`).
- Confirm zero solver imports in `backend/edge/`.

### Step 2: Configuration (`configs/device_profiles.json`)
- Define device profiles for `BHARATI`, `MAITRI`, `HIMADRI`.
- Device classes: `SOLAR`, `WIND`, `DIESEL_GENERATOR`, `BATTERY`, `THERMAL`, `WEATHER`, `POWER_METER`, `FUEL`, `GPS`, `COMMUNICATIONS`.
- Specify telemetry channels, units, valid ranges, and freshness thresholds.

### Step 3: Core Schemas (`backend/edge/schema.py`)
- `DeviceType`, `DataQualityState`, `DeviceHealthState`, `ConnectivityState`, `EdgeMode`, `FallbackPosture`.
- Data envelopes and state models with locked 6-tier provenance validation.

### Step 4: Device Registry (`backend/edge/devices.py`)
- Station-aware device profile loader and querying interface.

### Step 5: Telemetry Normalization & Quality Engine (`backend/edge/telemetry.py`, `quality.py`)
- Canonical telemetry envelope with deterministic quality checks (range, freshness, units, duplicates, sequence).

### Step 6: Device Health & Connectivity Engines (`backend/edge/health.py`, `connectivity.py`)
- Deterministic health scoring based on telemetry freshness, quality faults, and heartbeat.
- Finite state machine for edge connectivity (`CONNECTED`, `DEGRADED`, `OFFLINE`, `RECONNECTING`, `UNKNOWN`).

### Step 7: Bounded Local Buffer & State Model (`backend/edge/buffer.py`, `state.py`)
- FIFO bounded buffer with deduplication and state tracking (`BUFFERED`, `IN_FLIGHT`, `CONFIRMED`).
- Edge operational state with fallback postures (`HOLD_LAST_VALIDATED_STATE`, `SAFE_HOLD`, `SUSPEND_NONCRITICAL_REQUESTS`, etc.).

### Step 8: Reconnection & State Reconciliation (`backend/edge/reconciliation.py`)
- Chronological replay, deduplication, conflict resolution, and auditable reconciliation logs.

### Step 9: Edge Orchestrator & Adapters (`backend/edge/engine.py`, `adapters.py`)
- Full edge workflow coordination.
- Thin adapters dispatching to frozen Policy and Optimizer engines when connected.
- Fallback enforcement when offline/degraded.

### Step 10: Deterministic Simulation Harness (`backend/edge/simulation.py`)
- Configurable scenarios: `NORMAL`, `DEVICE_STALE`, `DEVICE_FAILURE`, `CONNECTIVITY_DEGRADED`, `CONNECTIVITY_OFFLINE`, `BUFFER_GROWTH`, `RECONNECT`, `REPLAY_DELAYED_TELEMETRY`.

### Step 11: API Routes & Schemas (`backend/api/routes/edge.py`, `schemas/edge.py`)
- Mount `/api/v1/edge/{station_id}/...` endpoints.

### Step 12: Frontend Workspace (`frontend/src/views/EdgeView.tsx`)
- Informational, API-driven Edge & Device Intelligence workspace.

### Step 13: Test Suite & Verification Matrix
- Dedicated Phase 11 unit and integration tests (`tests/test_phase11_edge.py`).
- Full backend regression (206+ tests).
- Frontend tests (12+ tests) & production build (`npm run build`).
- Phase 10 runtime verification script (`verify_phase10_runtime.py`).
- Architecture boundary audit (zero solvers, zero physical equations in edge layer).

---

## 5. Execution Strategy
1. Create `configs/device_profiles.json`.
2. Implement backend edge domain modules.
3. Wire API schemas, adapters, and routes.
4. Add frontend client types and view.
5. Execute full test suite and verify zero regression across frozen phases.
