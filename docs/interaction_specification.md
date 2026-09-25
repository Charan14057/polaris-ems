# POLARIS-EMS — INTERACTION SPECIFICATION

**Document ID:** SPEC-INTERACTION-20260925  
**Version:** 1.0.0-DEFENSIBLE-PATTERNS  
**Status:** CANONICAL & IMPLEMENTED  

---

## 1. OVERVIEW

Polaris-EMS introduces five signature, defensible interaction patterns specifically designed for polar microgrid mission control. Unlike generic dashboard charts, these patterns reflect physical causality, epistemic provenance, and supervisory control boundaries.

---

## 2. THE FIVE SIGNATURE POLARIS-EMS INTERACTION PATTERNS

### 2.1 Decision Ribbon (Causal Operational Chain)

* **Architecture:** A persistent horizontal directed causal pipeline:
  ```text
  WEATHER / TELEMETRY
         ↓
      FORECAST
         ↓
      SCENARIO
         ↓
     OPTIMIZER
         ↓
    TWIN REPLAY
         ↓
    RESILIENCE
         ↓
      POLICY
  ```
* **Behavior:**
  * Displays real-time operational status, execution duration (ms), and governing reason code at each node.
  * Clicking any node highlights that stage's causal contribution to the current dispatch directive.
  * Preserves the strict separation between mathematical optimizer proposals and downstream physical twin replay.
* **Defensibility & Technical Distinction:** Most dashboard systems show isolated stage metrics. The Decision Ribbon renders the complete end-to-end multi-phase dependency DAG in real time, preventing operators from confusing mathematical proposals with physically verified consequences.

---

### 2.2 Evidence Drawer (Epistemic Provenance Inspection)

* **Architecture:** Universal slide-out drawer accessible from any metric, chart node, or schedule cell across the entire application via `EvidenceContext`.
* **Telemetry Fields Displayed:**
  1. *Factual Value & Unit*
  2. *Data Source Subsystem / Transducer*
  3. *Locked 6-Tier Provenance Classification* (`REAL`, `CONFIGURED`, `ASSUMED`, `SYNTHETIC`, `FORECAST`, `SIMULATED`)
  4. *Observation / Execution Timestamp*
  5. *Station ID*
  6. *Underlying Predictive Model / Physical Law*
  7. *Uncertainty Interval* ($P_{10}–P_{90}$)
  8. *Validation State* (`VALIDATED`, `COMPUTED`, `ESTIMATED`, `ADVISORY`)
  9. *Governing Invariant Rule*
* **Defensibility & Technical Distinction:** Eliminates "black box" dashboard metrics. Every numerical representation is cryptographically and epistemically bound to its computational origin, preventing unverified or hallucinated operational claims.

---

### 2.3 Resilience Envelope (Binding Resource Bottleneck Model)

* **Architecture:** Operational resource envelope replacing unreadable radar charts with an intuitive bottleneck visualization.
* **Visual Components:**
  * Center Hero: Overall Station Survival Horizon (hours) and categorical resilience state (`SAFE`, `WATCH`, `AT_RISK`, `CRITICAL`).
  * Binding Resource Callout: Pinpoints the exact subsystem currently constraining station survivability (e.g. *Fuel Endurance*, *Thermal Habitability*, or *Battery Depletion*).
  * 4 Subsystem Capacity Channels: Parallel bars displaying current margin, time to breach, and safety threshold.
* **Defensibility & Technical Distinction:** Unlike conventional geometric radar charts that distort multi-dimensional metrics, the Resilience Envelope enforces physical conservation laws and highlights the first-to-fail dimension under escalating polar stress.

---

### 2.4 Scenario Delta Canvas (Causal Impact Chain)

* **Architecture:** A 4-step horizontal delta canvas connecting baseline state to perturbed scenario outcomes:
  ```text
  [01 DISTURBANCE] → [02 GENERATION DELTA] → [03 OPTIMIZER ACTION] → [04 RESILIENCE OUTCOME]
  ```
* **Behavior:**
  * Replaces static "before vs after" tables with a narrative of physical perturbation.
  * Step 1 shows the injected environmental stress (e.g., wind cut-out storm at 28 m/s).
  * Step 2 shows the resulting power loss (e.g., -65 kW wind).
  * Step 3 shows the automatic dispatch compensation (e.g., +55 kW diesel + BESS discharge).
  * Step 4 shows the net impact on station survival hours (e.g., 142h → 84h).
* **Defensibility & Technical Distinction:** Connects cause, physical reaction, and operational impact in a single glance without cognitive fragmentation.

---

### 2.5 Mission Narrative (Plain-Language Progressive Disclosure)

* **Architecture:** Every major technical page begins with an 8th-grade-readable operational statement before exposing analytical charts and technical models:
  * *Overview:* "Renewables are currently supplying 61% of station demand. Wind is projected to drop below cut-in threshold over the next 12 hours, requiring G1 diesel startup."
  * *Forecast:* "Load forecast is stable with tight P10–P90 bounds; wind uncertainty expands significantly after +18h due to approaching low-pressure front."
  * *Resilience:* "Station is in SAFE posture with 142.0 hours of autonomous endurance; fuel storage is the governing binding constraint."
* **Progressive Disclosure Levels:**
  * *Level 1:* Plain-Language Narrative Summary.
  * *Level 2:* High-level KPI Badges.
  * *Level 3:* Time-series charts & dispatch ledgers.
  * *Level 4:* Mathematical constraints & solver metrics.
  * *Level 5:* Immutable audit trace & provenance hashes.
* **Defensibility & Technical Distinction:** Ensures non-expert expedition leaders and senior engineers can share the exact same screen and understand immediate operational risk without wading through complex algebraic equations.
