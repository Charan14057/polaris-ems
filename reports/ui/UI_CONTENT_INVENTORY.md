# POLARIS-EMS — FRONTEND UI CONTENT INVENTORY & AUDIT
**Version:** 1.0.0-phase18  
**Scope:** Exhaustive Component, Screen, Data Source & Necessity Audit  
**System Status:** `CURRENT_UI_SHELL = FROZEN`  

---

## 1. Global Shell & Persistent Navigation

| Element | Type | Purpose | Data Shown | Data Source | User Actions | Necessity |
|---|---|---|---|---|---|---|
| **`Sidebar.tsx`** | Navigation Rail | Primary multi-domain view routing | Operations, Decisions, Assurance, Engineering menu items | Static route configuration | Click view to switch, collapse/expand toggle | **CORE** |
| **`TopBar.tsx`** | Application Bar | Station switcher, horizon selector, connection badge | Selected station (Bharati/Maitri/Himadri), horizon (6h..168h), air-gap badge | `StationContext` | Select station, select horizon, mobile hamburger toggle | **CORE** |
| **`MobileNav.tsx`** | Tab Bar | Mobile navigation for small viewports | Overview, Energy, Scenarios, Dispatch quick tabs | Static route configuration | Tap tab to navigate | **CORE** |
| **Air-Gap Banner** | Notice Banner | Transparent physical boundary disclaimer | "SIMULATION AIR-GAP ENFORCED: PHYSICAL_CONNECTIVITY = DISCONNECTED" | Static configuration | Dismiss or read context | **CORE** |
| **`GlobalStatusBar.tsx`** | Global Telemetry Strip | High-level system KPI overview | Total Generation, Total Load, Storage SoC, Station Status | `StationContext` / API | Inspect quick metrics | **CORE** |

---

## 2. Screen-by-Screen Content Inventory

### 2.1 Overview Screen (`OverviewView.tsx`)
- **Purpose:** Primary operational situational awareness dashboard for station operators and non-technical visitors.
- **Visible Components:**
  1. *Executive Status Hero*: Plain language headline ("STATION POWER SECURED", "COLD SURGE ACTIVE"), operating mode badge, 6-tier provenance indicator.
  2. *Operational Vitals Grid*: Generation vs Demand balance card, Battery Storage SoC, Fuel Reserve Days Remaining, Microgrid Resiliency Index (0..100).
  3. *Generation Source Breakdown*: Visual energy distribution bar showing Solar, Wind, Battery, and Diesel contribution.
  4. *Active Stress Disturbances*: Table/cards of active weather and physical faults (e.g. Blizzard alert, High wind cut-out).
  5. *Decision Audit Summary*: Last recommended dispatch action, approval state, and confidence score.
- **Data Sources:** `/api/v1/stations/{id}`, `/api/v1/resilience/evaluate`, `/api/v1/policy/evaluate`, `/api/v1/twin/state/{id}`.
- **User Actions:** Station selection, horizon shift, jump to Twin or Dispatch view.
- **Necessity:** **CORE** (Essential executive situational awareness).

---

### 2.2 Energy & Spatial Digital Twin Screen (`EnergyTwinView.tsx`)
- **Purpose:** Spatial operational twin displaying floor-plan microgrid layout, 3D station geometry, thermal zones, and directional electrical flow.
- **Visible Components:**
  1. *Twin Header*: Station name, model status (`REPRESENTATIVE`), provenance tag (`SIMULATED`), epistemic boundary badge.
  2. *Twin Summary Strip (`TwinSummaryStrip.tsx`)*: Plain language "WHAT IS HAPPENING?", "WHY THIS MATTERS", and 6 vitals cards (Demand, Renewable Share, Battery State, Diesel Status, Fuel Burn, Thermal Reserve).
  3. *Source Mix Bar (`TwinSourceMix.tsx`)*: Proportional energy supply bar with kW values for Solar, Wind, Diesel, Battery.
  4. *Spatial Canvas (`TwinCanvas.tsx`)*: 3D / 2D interactive canvas showing station zones, equipment nodes, electrical buses, feeders, and dynamic flow edges.
  5. *Replay & Simulation Rail (`TwinTimeline.tsx`)*: Play/Pause, Step Forward/Back, Reset, 1x/2x/5x/10x speed, event markers, simulation time vs UTC clock.
  6. *Side Inspector Drawer (`TwinInspector.tsx`)*: Device name, status, rated kW, circuit ID, upstream lineage, Trace Power button, technical evidence.
  7. *Explain This Drawer (`ExplainThis.tsx`)*: Non-technical primer on Kirchhoff conservation and polar storm resilience.
- **Data Sources:** `/api/v1/twin/spatial/{id}`, `/api/v1/twin/state/{id}`, `/api/v1/twin/trajectory`.
- **User Actions:** Pan/zoom canvas, switch 3D/2D view mode, filter device categories, click device/zone/node, trace power/impact, play/pause trajectory, scrub timeline.
- **Necessity:** **CORE** (Flagship operational product interface).

---

### 2.3 Forecast Screen (`ForecastView.tsx`)
- **Purpose:** Probabilistic load, solar PV, and wind turbine generation forecasting with conformal prediction intervals (P10, P50, P90).
- **Visible Components:**
  1. *Multi-Horizon Chart*: Multi-quantile ribbon chart showing forecasted load against historical ground truth.
  2. *Weather Driver Strip*: Wind speed, solar irradiance (GHI), ambient temperature forecast.
  3. *Uncertainty Bounds Card*: P10/P90 spread analysis and coverage guarantee percentage.
  4. *Model Metadata*: Architecture details (Transformer/LSTM/XGBoost ensemble), conformal calibration score.
- **Data Sources:** `/api/v1/forecasts/generate`.
- **User Actions:** Horizon toggle (6h, 12h, 24h, 48h, 168h), target selector (Load, Solar, Wind), confidence band toggle.
- **Necessity:** **CORE** (Underpins all proactive microgrid dispatch decisions).

---

### 2.4 Multi-Horizon Scenarios Screen (`ScenariosView.tsx`)
- **Purpose:** Stress-testing the station against 14 locked polar stress scenarios (blizzards, generator dropouts, fuel line freezing, polar night).
- **Visible Components:**
  1. *Scenario Catalog*: Grid of 14 deterministic scenario cards with severity badges (LOW, MEDIUM, HIGH, CATASTROPHIC).
  2. *Perturbation Parameters*: Injected physical faults (e.g. DG1 lockout, wind turbine icing).
  3. *Comparative Horizon Curves*: Baseline vs Perturbed trajectory curves for fuel burn, battery reserve, and unserved energy.
  4. *Deficit Accounting Ledger*: Explicit tracking of deficit kWh and duration of critical load shedding.
- **Data Sources:** `/api/v1/scenarios/run`, `/api/v1/scenarios/catalog`.
- **User Actions:** Select scenario, execute simulation, compare trajectories.
- **Necessity:** **CORE** (Proves microgrid survivability under extreme arctic shocks).

---

### 2.5 Dispatch Optimization Screen (`OptimizationView.tsx`)
- **Purpose:** HiGHS Mixed-Integer Linear Program (MILP) dispatch optimizer with honest fuel vs battery trade-offs.
- **Visible Components:**
  1. *Dispatch Schedule Table*: Hourly asset commitments (Diesel Gen 1..N, Battery Charge/Discharge, Renewable curtailment).
  2. *Solver Status Badge*: Optimal, Feasible, or Infeasible status with solve time (ms) and MIP gap (< 0.1%).
  3. *Objective Breakdown*: Fuel cost, cycling degradation penalty, and emissions penalty.
  4. *Operator Review & Approval Action*: "Approve Dispatch Schedule" button with explicit human-in-the-loop review modal.
- **Data Sources:** `/api/v1/optimizer/solve`, `/api/v1/optimizer/schedule`.
- **User Actions:** Select horizon, trigger solve, inspect constraints, approve/reject schedule.
- **Necessity:** **CORE** (Primary computational dispatch authority).

---

### 2.6 Resilience Engine Screen (`ResilienceView.tsx`)
- **Purpose:** 9-dimensional polar resilience radar and survivability metrics.
- **Visible Components:**
  1. *9-Dimension Polar Radar Chart*: Autonomy, Thermal Buffer, Reserve Margin, Cold Start, Fuel Security, Asset Redundancy, Recovery Time, Cyber Resilience, Deficit Tolerance.
  2. *Composite Resilience Index*: 0..100 aggregate resilience score with status class (RESILIENT, DEGRADED, VULNERABLE, CRITICAL).
  3. *Vulnerability Breakdown*: Specific dimensions under threshold with suggested mitigations.
- **Data Sources:** `/api/v1/resilience/evaluate`.
- **User Actions:** Toggle benchmark comparisons, filter dimensions, inspect mitigation actions.
- **Necessity:** **SECONDARY** (Vital for deep engineering resilience audits; summarized in Overview).

---

### 2.7 Decision Trace Screen (`TracesView.tsx`)
- **Purpose:** Cryptographically hashed immutable audit trail of every autonomous recommendation and operator override.
- **Visible Components:**
  1. *Decision Log Table*: Timestamp, Action Type, Model Confidence, SHA-256 State Hash, Operator Decision.
  2. *Lineage Explorer*: JSON trace tree showing input features, solver parameters, and resulting policy checks.
- **Data Sources:** `/api/v1/traces/log`, `/api/v1/traces/{id}`.
- **User Actions:** Search traces, filter by date/status, export audit report.
- **Necessity:** **SECONDARY** (Mandatory for compliance and post-incident investigation).

---

### 2.8 Policy Governance Screen (`PolicyView.tsx`)
- **Purpose:** Explicit P1–P8 polar safety and microgrid policy constraints enforcement.
- **Visible Components:**
  1. *Policy Matrix*: P1 (Life Support Non-Curtailment), P2 (Battery Deep Discharge Floor), P3 (Diesel Minimum Runtime), etc.
  2. *Violation Counter*: Zero-tolerance violation alerts.
- **Data Sources:** `/api/v1/policy/rules`, `/api/v1/policy/evaluate`.
- **User Actions:** Inspect rule parameters, simulate policy check.
- **Necessity:** **ENGINEERING** (Specialist microgrid compliance rule engine).

---

### 2.9 Field & HIL Integration Screen (`FieldHilView.tsx`)
- **Purpose:** Hardware-in-the-loop and external SCADA protocol bridge testing.
- **Visible Components:**
  1. *Protocol Adapters*: Modbus TCP, DNP3, IEC 61850 protocol connection states (all currently `DISCONNECTED / VIRTUALIZED`).
  2. *Roundtrip Latency & Packet Statistics*.
- **Data Sources:** `/api/v1/integrations/status`.
- **User Actions:** Test protocol handshake, view simulated packet stream.
- **Necessity:** **ENGINEERING** (Hardware integration boundary; clearly displays simulated air-gap).

---

### 2.10 Multi-Domain Validation Screen (`ValidationView.tsx`)
- **Purpose:** Statistical performance and drift monitoring across all 15 project phases.
- **Visible Components:**
  1. *Phase Validation Badges*: Verification checkmarks across Phase 1 through 18.
  2. *Statistical Drift Charts*: Kolmogorov-Smirnov test statistics and pinball loss metrics.
- **Data Sources:** `/api/v1/validation/summary`.
- **User Actions:** Inspect test execution reports.
- **Necessity:** **ENGINEERING** (Verification gate evidence).

---

## 3. Redundancy & Simplification Recommendations

1. **Remove Duplicate Hardcoded Numbers in Visual Wrappers**:
   - Ensure all sub-panels in `OverviewView` and `EnergyTwinView` derive strictly from API responses or null-safe defaults (`—`).
2. **Harmonize Replay Terminology**:
   - Replay timeline must consistently be titled `SIMULATION REPLAY` or `REAL-TIME SIMULATION`, never "Video Stream" or "Live Feed".
3. **Consolidate Secondary Technical Fields**:
   - Move raw electrical impedance and node coordinates to the right-side `TwinInspector` technical drawer, keeping the main 3D canvas clean and uncluttered.
