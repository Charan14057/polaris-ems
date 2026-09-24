# Phase 11 Architecture: Device Intelligence & Edge-First Field Resilience
**Project:** Polaris-EMS — Polar Energy Management & Resilience System  
**SIH Problem Statement:** SIH26061: AI-Driven Smart Energy Management System for Polar Research Stations  
**Status:** PHASE 11 FROZEN (`PHASE_11_FROZEN`)  
**Parent Baseline:** Phases 1–10 (Frozen)

---

## 1. Architectural Philosophy & Ownership Boundaries

The core Polaris-EMS pipeline operates under strict separation of concerns across 11 frozen phases:

```
[Phase 3: ML]           PREDICT        Load & Renewable Production Forecaster (FORECAST)
      ↓
[Phase 4: Digital Twin] SIMULATE       Physical Authority & Conservation Equations (SIMULATED)
      ↓
[Phase 5: Scenarios]    STRESS TEST    14 Canonical Polar Environmental/Grid Scenarios
      ↓
[Phase 6: Optimizer]    DECIDE         Sole Mathematical Dispatch Optimizer (HiGHS MILP)
      ↓
[Phase 7: Resilience]   ASSESS         9-Dimensional Survival Index & Recovery Intel
      ↓
[Phase 8: Policy]       GOVERN         Rule-Based Safety Hierarchy (P1–P8, Hysteresis)
      ↓
[Phase 9: API]          CONNECT        RESTful Contracts & Integration Boundary
      ↓
[Phase 10: Frontend]    DISPLAY        Operational Visualization (9 Workspaces)
      ↓
[Phase 11: Edge]        RESILIENCE     Device Intelligence, Ingestion Quality, & Field Autonomy
```

### Non-Negotiable Invariants
1. **Phase 6 Remains the Sole Optimizer:** Phase 11 contains **zero** Pyomo or HiGHS solver code, performs no MILP dispatch solving, and does not select generator schedules independently.
2. **Phase 4 Remains Physical Authority:** Phase 11 does not replicate physical power balance, thermal differential, battery degradation, or diesel fuel curve calculations.
3. **Phase 8 Policy Remains Governance:** Phase 11 adheres to the P1–P8 priority hierarchy and uses existing policy pathways.
4. **Strict Six-Tier Provenance Taxonomy:** Only permitted values:
   $$\{\text{REAL}, \text{CONFIGURED}, \text{ASSUMED}, \text{SYNTHETIC}, \text{FORECAST}, \text{SIMULATED}\}$$
   No fabricated 7th tiers (`LIVE`, `REAL_TIME`, `EDGE`, `TELEMETRY`, etc.).
5. **No Direct Hardware Actuation:** All generator, load, and battery cards remain informational. No automatic breaker control or remote start commands are issued without a dedicated future actuation phase.

---

## 2. Edge Subsystem Architecture

```
[FIELD / VIRTUAL DEVICES]
  (Solar, Wind, Gensets, BESS, Thermal, AWS Weather, Power Meter, Fuel, GPS, Satcom)
         │
         ▼
[TELEMETRY NORMALIZATION] ────► [DATA QUALITY ENGINE]
  (Canonical UTC Envelope)        (Bounds, Units, Skew, Duplicates, Freshness)
                                         │
                                         ▼
                                [DEVICE HEALTH ENGINE]
                                  (Freshness, Faults, Silence Scoring)
                                         │
                                         ▼
                               [CONNECTIVITY MACHINE] ◄── [HEARTBEAT / LOSS]
                                 (Connected, Degraded, Offline, Reconnecting)
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
      [CONNECTED OPERATION]                          [OFFLINE / DEGRADED]
               │                                               │
   [API / Policy Pathway]                             [BOUNDED LOCAL BUFFER]
               │                                      (FIFO, Dedup, Max 5000)
       [Phase 6 Optimizer]                                     │
               │                                      [RECOVERY SYNC]
      [Optimal Dispatch]                                       │
                                                      [STATE RECONCILIATION]
                                                      (Newer wins, Audit Log)
```

---

## 3. Subsystem Breakdown

### 3.1 Device Fleet Model (`backend/edge/devices.py`)
Dynamic configuration sourced from `configs/device_profiles.json` covering:
- **BHARATI:** 30 kW PV, 25 kW Wind, $3 \times 80\text{ kW}$ Gensets, 120 kWh BESS, CHP Thermal Loop, Polar AWS, 400V Bus Meter, 160,000L Bulk Fuel, NavIC GPS, GSAT Satcom (12 devices).
- **MAITRI:** $2 \times 15\text{ kW}$ Wind, $3 \times 62.5\text{ kW}$ Gensets, 90 kWh BESS, Boiler Thermal Circuit, Oasis AWS, Main Bus Meter, 120,000L Fuel, GPS, Inmarsat Satcom (12 devices).
- **HIMADRI:** 15 kW PV, $2 \times 45\text{ kW}$ Gensets, 60 kWh BESS, Laboratory HVAC, Arctic AWS, Bus Meter, 50,000L Fuel, GPS, Polar Satcom (10 devices).

### 3.2 Telemetry Normalization & Quality Engine (`backend/edge/telemetry.py`, `quality.py`)
Canonical envelope attributes:
- `timestamp`, `station_id`, `device_id`, `channel`, `value`, `unit`, `quality`, `source`, `received_at`, `sequence_number`, `provenance`, `validation_status`, `diagnostics`.
- Deterministic Quality States:
  - `VALID`: Within bounds, correct unit, fresh, monotonic sequence.
  - `STALE`: Observation age exceeds configured freshness threshold ($>60\text{s}$).
  - `OUT_OF_RANGE`: Exceeds physical configured limits for device channel.
  - `DUPLICATE`: Identical timestamp received on active channel.
  - `OUT_OF_ORDER`: Regressed sequence number compared to latest received.
  - `SUSPECT`: Future timestamp skew ($>60\text{s}$), unit mismatch, or unregistered device.

### 3.3 Device Health Engine (`backend/edge/health.py`)
- Evaluates telemetry freshness, silence thresholds ($>3\times$ freshness $\to$ `UNAVAILABLE`), and repeated fault accumulation ($\ge 3$ out-of-range $\to$ `FAULT`).
- Computes deterministic health scores $[0.0, 1.0]$ with transparent contributing signal lineage.

### 3.4 Connectivity State Machine (`backend/edge/connectivity.py`)
- Tracks consecutive failures, packet loss percentage, heartbeat age, and local buffer depth.
- Transitions:
  - Nominal: `CONNECTED`
  - 1–2 drops or packet loss: `DEGRADED`
  - $\ge 3$ consecutive dropouts or timeout: `OFFLINE`
  - Reconnect initiation: `RECONNECTING`

### 3.5 Bounded Local Buffer & State Reconciliation (`backend/edge/buffer.py`, `reconciliation.py`)
- Bounded capacity (5,000 readings) with FIFO eviction of oldest buffered items upon overflow.
- Three-state lifecycle: `BUFFERED` $\to$ `IN_FLIGHT` $\to$ `CONFIRMED`.
- Deterministic reconciliation rules:
  1. Newer buffered readings update live state.
  2. Older buffered readings are accepted into historical logs without overwriting newer live state.
  3. Duplicates are identified and safely dropped.
  4. Missing telemetry intervals ($>120\text{s}$) are explicitly flagged.
  5. Produces an auditable `ReconciliationReport`.

### 3.6 Edge Fallback Postures (`backend/edge/state.py`, `adapters.py`)
When disconnected from central backend:
- `HOLD_LAST_VALIDATED_STATE`: Maintains previous verified operational settings.
- `SAFE_HOLD`: Enforces minimal life-safety loads and suspends noncritical discretionary tasks.
- `PROTECT_CRITICAL_SYSTEMS`: Protects life support and water line heating during severe fleet faults.
- `BUFFER_AND_FORWARD`: Caches telemetry locally during reconnection.
- **Critical Boundary:** Never runs an independent mathematical optimizer or MILP solver at the edge node.
