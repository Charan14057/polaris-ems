# POLARIS-EMS — PLATFORM ARCHITECTURE & WEBSITE MAP
**Document Version:** 2.0.0 (Production Verified)  
**System Status:** Operational Simulation (Physical Air-Gap Enforced)  
**Hardware Connectivity:** PHYSICAL_CONNECTIVITY = DISCONNECTED • PHYSICAL_SCADA_LINK = FALSE

---

## Navigation Hierarchy

`
GLOBAL SHELL (Locked Shell Architecture)
¦
+-- 1. Overview (Mission Dashboard)
+-- 2. Energy (Operational Spatial Digital Twin)
+-- 3. Forecast (Physics-Informed Conformal Ensembles)
+-- 4. Scenarios (Stress & Disturbance Injection)
+-- 5. Dispatch (MILP Multi-Horizon Cost-Optimal Scheduling)
+-- 6. Resilience (9-Dimensional Polar Stress Horizons)
+-- 7. Assets (Station Electrical Topology & Hierarchy)
+-- 8. Decisions (Verifiable Lineage & Explainability DAG)
¦
+-- Assurance
¦   +-- 9. Validation (Physics & Mathematical Conservation Proofs)
¦
+-- Engineering
    +-- 10. Policy (Hierarchical Governance & Overrides)
    +-- 11. Field / HIL (Hardware-In-The-Loop & Edge Telemetry)
`

---

## Detailed View Specifications

### 1. Overview (/)
- **Purpose:** Consolidated mission control overview displaying real-time simulation health, primary generation/load balance, storage reserve, and active policy directives.
- **Inputs:** Active station selection (BHARATI | MAITRI | HIMADRI), latest simulated microgrid state, horizon selection (24h–168h).
- **Outputs:** Station demand (kW), clean energy share (%), BESS state of charge (%), survival runway (hours), 3-tier feeder flow schematic, active threat flags.
- **Main Controls:** Station selector, Horizon toggle, Quick Orientation Guide, Launch Spatial Digital Twin button, Direct navigation pills.
- **Backend Owner:** backend.core.orchestrator, backend.resilience.engine, backend.policy.engine.
- **Demo Value:** High. Serves as the introductory visual anchor for operators and executive reviewers to grasp holistic station posture in under 15 seconds.
- **Technical Depth:** Low-to-Medium (Topological abstraction with drill-down links to deep telemetry).

---

### 2. Energy (/energy)
- **Purpose:** Spatial operational Digital Twin rendering reference-aligned 3D station geometry, live directional power flow, source contribution, and circuit lineages.
- **Inputs:** Station 3D spatial profile, latest TwinState or simulated TwinTrajectory, selected weather horizon (6h–48h).
- **Outputs:** 3D interactive station model (elevated decks, piles, modules), animated power flow streams with kW-scaled density, aggregated functional load groups (Life Support, Communications, Habitation, Science, Utilities, Workshop), forward weather drivers.
- **Main Controls:** 
  - Master Mode: LIVE (continuous real-time simulation) vs REPLAY (24h/48h historical trajectory scrub).
  - Visualization Layer: ARCH (structural emphasis) | ENERGY (flow lines and particles) | IMPACT (downstream circuit highlighting with 92% dimming of unrelated circuits).
  - Camera Presets: 3D ISO, TOP, ELEVATION.
  - Operational Posture: MANUAL (simulate operator action with impact review) vs AUTO (Phase 6 optimizer advisory with operator approval workflow).
  - Inspector: Trace My Power Route, Trace Disturbance Impact.
- **Backend Owner:** backend.twin.spatial_service, backend.twin.trajectory_engine, backend.twin.physics_engine.
- **Demo Value:** Flagship. Demonstrates spatial microgrid physics without physical risk.
- **Technical Depth:** Very High (Three.js WebGL rendering, Catmull-Rom spline curves, Kirchhoff nodal conservation).

---

### 3. Forecast (/forecast)
- **Purpose:** Multi-horizon predictive modeling for renewable resources (katabatic wind, solar irradiance) and research station electrical load.
- **Inputs:** Weather telemetry, numerical weather prediction (NWP) feeds, historical station load profiles.
- **Outputs:** P10, P50, P90, P95 quantile forecast envelopes across 24h, 48h, and 168h horizons with conformal coverage bounds.
- **Main Controls:** Target variable toggle (Total Load, Wind Power, Solar GHI, Ambient Temperature), Horizon selector, Evidence inspection drawer.
- **Backend Owner:** backend.ml.forecasting, backend.ml.uncertainty.conformal_calibrator.
- **Demo Value:** High. Shows how AI prevents surprises by forecasting katabatic storms and polar night transitions.
- **Technical Depth:** High (Physics-informed XGBoost, conformal prediction calibration, epistemic uncertainty quantification).

---

### 4. Scenarios (/scenarios)
- **Purpose:** What-if simulation and stress testing under severe polar anomalies and equipment failures.
- **Inputs:** Disturbance configurations: Katabatic blizzard (wind cut-out), Solar lull, Generator mechanical trip, Battery cell degradation, Extreme thermal drop (-55°C).
- **Outputs:** Comparative state trajectories, fuel consumption variance, load shedding sequence, battery degradation delta.
- **Main Controls:** Preset scenario selector, custom severity slider, 'Run Simulation' execution button, side-by-side delta comparator.
- **Backend Owner:** backend.scenarios.runner, backend.simulation.engine.
- **Demo Value:** Very High. Demonstrates microgrid resilience when equipment fails.
- **Technical Depth:** High (Dynamic disturbance injection, thermal decay equations).

---

### 5. Dispatch (/optimization)
- **Purpose:** Mixed-Integer Linear Programming (MILP) scheduling for multi-source generation and demand flexibility.
- **Inputs:** Forecast quantile envelopes, generator fuel efficiency curves, battery C-rate/degradation limits, non-linear spinning reserve constraints.
- **Outputs:** Timestep-by-timestep generator commitment schedules, battery charge/discharge trajectories, hourly fuel burn rate, reserve margins.
- **Main Controls:** Optimization objective weighting (Minimize Fuel vs Maximize Battery Longevity), spinning reserve threshold slider, Solve execution trigger.
- **Backend Owner:** backend.optimization.milp_solver, backend.optimization.formulation.
- **Demo Value:** High. Shows exact fuel and cost savings (18–25%) achieved through mathematical optimization.
- **Technical Depth:** Very High (Branch-and-bound MILP, lexicographical constraint hierarchy).

---

### 6. Resilience (/resilience)
- **Purpose:** 9-dimensional polar stress evaluation calculating multi-system survival horizons.
- **Inputs:** Current fuel reserves, battery capacity, insulation R-values, external temperature, mission priority rules.
- **Outputs:** Critical load survival horizon (hours), thermal runway to freeze-up, fuel depletion date, multi-attribute radar chart.
- **Main Controls:** Stress test parameter overrides, horizon filter, constraint bottleneck inspector.
- **Backend Owner:** backend.resilience.evaluator, backend.resilience.metrics.
- **Demo Value:** High. Illustrates sovereign life-safety boundaries in extreme isolation.
- **Technical Depth:** High (Differential thermal decay models, bottleneck attribution).

---

### 7. Assets (/assets)
- **Purpose:** Comprehensive registry of all station generation, storage, distribution, and consumption equipment.
- **Inputs:** Authoritative station profile registry.
- **Outputs:** Rated capacity (kW/kWh), nominal bus voltage, circuit ID, location zone, priority rank, physical asset health index.
- **Main Controls:** Search & filter by category (Sources, Storage, Critical Loads, Secondary Loads), asset detail modal.
- **Backend Owner:** backend.assets.registry.
- **Demo Value:** Medium. Shows operational grounding and equipment-level transparency.
- **Technical Depth:** Medium (Relational asset hierarchy, bus line mapping).

---

### 8. Decisions (/decisions)
- **Purpose:** Full auditability and explainability trail for automated advisory recommendations and supervisor approvals.
- **Inputs:** Executed decision runs, policy evaluation logs, optimizer solution metadata.
- **Outputs:** Interactive Directed Acyclic Graph (DAG) of the decision pipeline (Stage 1 Intake ? Stage 7 Policy Enactment), Reason codes, Natural language 'Why?' explainer, Decision Delta comparator, JSON/CSV audit export.
- **Main Controls:** Trace history selector, Stage inspector, 'Compare Decisions' modal, Export Audit Log button.
- **Backend Owner:** backend.decision.tracer, backend.decision.explainer.
- **Demo Value:** Very High. Convinces regulators and mission commanders that the AI is fully deterministic, explainable, and air-gapped.
- **Technical Depth:** High (Causal lineage tracking, DAG dependency traversal, counterfactual diffing).

---

### 9. Validation (/validation)
- **Purpose:** Automated mathematical and physical verification proving conservation laws are never violated.
- **Inputs:** Simulation time series, dispatch schedules, sensor readings.
- **Outputs:** Kirchhoff Current/Voltage Law residuals (|err| < 1e-4 kW), 1st and 2nd Law of Thermodynamics balances, battery mass-charge conservation scores.
- **Main Controls:** Station selector, tolerance slider, run validation suite.
- **Backend Owner:** backend.validation.physics_verifier.
- **Demo Value:** High for engineers and scientists. Proves zero hallucinated telemetry.
- **Technical Depth:** Very High (Conservation proofs, numerical residual matrices).

---

### 10. Policy (/policy)
- **Purpose:** Strict lexicographical priority ruleset governance (P1 Life Safety > P2 Communications ... > P8 Non-Essential).
- **Inputs:** Operational directives, manual supervisor overrides, weather alerts.
- **Outputs:** Active priority ranking, load shed sequence table, rule conflict resolution logs.
- **Main Controls:** Directive selector, emergency override simulation trigger, priority rule reordering preview.
- **Backend Owner:** backend.policy.ruleset_engine.
- **Demo Value:** Medium-High. Shows how life safety is mathematically guaranteed to take precedence over science.
- **Technical Depth:** High (Lexicographical order verification, hysteresis controllers).

---

### 11. Field / HIL (/edge)
- **Purpose:** Hardware-In-The-Loop (HIL) telemetry bridge and edge computing device status.
- **Inputs:** Edge node heartbeats, serial/Modbus simulated bridge packets.
- **Outputs:** Edge processor CPU/RAM utilization, round-trip telemetry latency, air-gap enforcement barrier status (DISCONNECTED).
- **Main Controls:** Edge bridge reconnect test, heartbeat cycle rate selector, packet inspector.
- **Backend Owner:** backend.edge.hil_bridge.
- **Demo Value:** Medium. Confirms operational deployment readiness on ruggedized polar hardware.
- **Technical Depth:** High (Serial protocol frames, edge synchronization buffers).
