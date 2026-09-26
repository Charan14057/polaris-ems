# POLARIS-EMS — PRODUCT OWNER WEBSITE & OPERATOR GUIDE
**Target Audience:** Non-Developer Product Owners, Mission Directors, Reviewers  
**System Classification:** Polar Microgrid Simulation & Advisory Platform  
**Operational Status:** Software Simulation (PHYSICAL_CONNECTIVITY = DISCONNECTED)

---

## Guide Structure
For every page in the application, this guide explains:
1. PAGE NAME
2. WHAT IT IS FOR
3. WHAT I SHOULD LOOK AT
4. WHAT DATA IT USES
5. WHAT I CAN CLICK
6. WHAT HAPPENS WHEN I CLICK IT
7. WHEN I WOULD USE THIS DURING A DEMO
8. WHAT I SHOULD NOT CLAIM

---

### 1. OVERVIEW
- **Purpose:** Provide an instantaneous mission dashboard of the research station's overall energy health.
- **Look at:** 
  - Station Demand (kW) vs Clean Renewable Mix (%).
  - Battery State of Charge (%) and Autonomous Survival Runway (hours).
  - The 3-tier System Flow Architecture (Sources ? 400V Bus ? Priority Feeders).
- **Data used:** Latest simulated station telemetry, Phase 8 operational directive, Phase 7 resilience engine output.
- **Click:** 
  - Station selector (BHARATI / MAITRI / HIMADRI).
  -  Launch Spatial Digital Twin button.
  - Quick Guide (Guide) button.
- **What happens:** 
  - Station selector immediately reconfigures all downstream metrics to that station's profile.
  - Launch Spatial Digital Twin navigates directly to the 3D Energy page.
  - Guide opens the 6-step Plain-English orientation modal.
- **Demo use:** Use in the first 30 seconds of an executive walkthrough to set context on polar challenges and high-level health.
- **Do not claim:** Do not claim this is live satellite SCADA from Antarctica; it is a continuously updated real-time physics simulation.

---

### 2. ENERGY (SPATIAL DIGITAL TWIN)
- **Purpose:** Understand the station's spatial electrical topology, physical equipment layout, and dynamic power flow.
- **Look at:** 
  - 3D Station Model (Elevated stilts for Bharati; twin living blocks and lake manifold for Maitri; 2-storey settlement lab for Himadri).
  - Directional power flow streams (Gold = Solar, Blue = Wind, Amber = Diesel, Green = Battery).
  - Aggregated Functional Load Groups (Life Support, Communications, Habitation, Science, Utilities, Workshop).
  - Forward Weather Drivers (Next 6h, 12h, 24h, 48h).
- **Click:** 
  - LIVE vs REPLAY toggle: Switches between continuous simulation and historical trajectory scrub.
  - Visualization Layer pills (ARCH | ENERGY | IMPACT).
  - 3D Camera Presets (3D ISO, TOP, ELEVATION).
  - Equipment objects in 3D scene (Turbine, Solar PV, Diesel House, Life Support, Panels).
  - Trace My Power Route / Trace Disturbance Impact in side inspector.
  - Operational Mode toggle (AUTO vs MANUAL).
- **What happens:** 
  - In LIVE mode, the real-time simulation status bar updates with exact UTC freshness.
  - In IMPACT mode, unrelated circuits dim to 8% opacity while downstream nodes highlight.
  - Clicking Trace My Power Route isolates the line from generator through switchboard to that exact load.
  - Clicking Simulate Operator Approval in AUTO mode triggers Phase 6 optimizer dispatch execution.
  - Clicking Simulate Action in MANUAL mode recalculates the full Kirchhoff power flow across the station.
- **Demo use:** The core visual centerpiece of any technical demo. Shows where energy comes from and which critical loads are receiving it.
- **Do not claim:** Do not claim exact millimeter BIM survey accuracy; the geometry is reference-aligned and representative. Do not claim autonomous physical actuation; operator approval is required and physical equipment is disconnected.

---

### 3. FORECAST
- **Purpose:** Examine machine learning projections of wind speed, solar radiation, and facility demand.
- **Look at:** 
  - P50 median forecast alongside P10 (conservative) and P90 (optimistic) uncertainty bands.
  - Conformal coverage calibration indicators.
- **Data used:** Historical polar weather archives, numerical weather models, physics-informed XGBoost quantile models.
- **Click:** Horizon buttons (24h, 48h, 168h), Target variable tabs (Total Load, Wind Power, Solar GHI, Temperature).
- **What happens:** Chart updates to show the selected variable's quantile fan chart and expected extreme wind cut-out events.
- **Demo use:** Explain how Polaris-EMS anticipates Antarctic blizzards 12 hours before they strike rather than reacting after power fails.
- **Do not claim:** Do not claim 100% weather certainty; explain that P10/P90 quantile bounds quantify epistemic uncertainty.

---

### 4. SCENARIOS
- **Purpose:** Test how the microgrid handles major physical anomalies and equipment failures without risking hardware.
- **Look at:** 
  - Disturbance presets: Katabatic Storm (wind cut-out), Generator Trip, Deep Thermal Drop (-55°C).
  - Survival time variance and load shedding stages.
- **Data used:** Phase 5 polar disturbance matrix and dynamic stress simulator.
- **Click:** Preset buttons, Run Simulation button.
- **What happens:** The system simulates the failure, reveals if diesel backup starts in time, and shows which scientific loads are shed to protect living quarters.
- **Demo use:** Demonstrate crisis handling and resilience during blizzards.
- **Do not claim:** Do not claim physical equipment is tripped; this is a sandbox simulation.

---

### 5. DISPATCH (OPTIMIZATION)
- **Purpose:** Review the hour-by-hour cost-optimal dispatch schedule for all generators, batteries, and flexible loads.
- **Look at:** 
  - Generator unit commitment bar chart (when diesel engines start/stop).
  - Battery charge/discharge cycling curves.
  - Projected fuel burn (L/h) and spinning reserve margin (>= 35%).
- **Data used:** Phase 6 Mixed-Integer Linear Programming (MILP) solver outputs.
- **Click:** Optimization objective selector (Minimize Diesel vs Preserve Battery), Re-solve Schedule.
- **What happens:** Recalculates the optimal schedule and updates the fuel savings projection.
- **Demo use:** Show government sponsors how the system reduces shipped-in diesel logistics by 18–25%.
- **Do not claim:** Do not claim real generators are physically dispatched in real time without human authorization.

---

### 6. RESILIENCE
- **Purpose:** Monitor the station's sovereign survival envelope under severe polar isolation.
- **Look at:** 
  - Critical Load Survival Horizon (e.g. 84 hours).
  - Thermal freeze-up runway (hours before building interior hits 0°C if heating fails).
  - 9-dimensional polar stress radar chart.
- **Data used:** Thermal loss coefficients, insulation R-values, fuel tank capacity, ambient air temperatures.
- **Click:** Stress test parameter sliders, horizon toggle.
- **What happens:** Recalculates the bottleneck constraint (e.g. fuel vs battery capacity) governing station survivability.
- **Demo use:** Show the life-safety assurance framework to safety officers and station leaders.
- **Do not claim:** Do not claim guaranteed life safety under impossible physical conditions (e.g. empty fuel tanks + zero wind).

---

### 7. ASSETS
- **Purpose:** Inspect technical nameplate ratings, bus connections, and health scores for every piece of electrical gear.
- **Look at:** 
  - Rated capacity (kW), bus voltage, circuit ID, location zone, priority tier.
- **Data used:** Authoritative station equipment registry.
- **Click:** Category filter tabs (Sources, Storage, Critical Loads, Secondary Loads), Individual asset cards.
- **What happens:** Opens detailed asset specs, including nominal amperage, voltage, and maintenance logs.
- **Demo use:** Answer technical engineering questions about specific equipment ratings.
- **Do not claim:** Do not claim live vibration or oil-analysis telemetry is physically connected.

---

### 8. DECISIONS
- **Purpose:** Provide complete, auditable explainability for every automated advisory recommendation.
- **Look at:** 
  - 7-Stage Decision Lineage DAG (Intake ? Weather ? State ? Scenarios ? MILP ? Resilience ? Policy).
  - Reason codes and plain-English 'Why?' explainer.
  - Decision Delta tab comparing baseline vs alternate runs.
- **Data used:** Phase 10 causal audit logs, optimizer solution metadata, policy evaluations.
- **Click:** Trace history selector, individual pipeline stages, 'Compare Decisions' modal, Export CSV/JSON.
- **What happens:** Highlights upstream dependencies in the DAG, displays exact mathematical inputs and outputs, and exports cryptographic audit logs.
- **Demo use:** Show regulatory auditors and mission commanders that the AI is fully transparent and explainable.
- **Do not claim:** Do not claim the system operates as an unreviewable black-box; every decision is deterministically auditable.

---

### 9. VALIDATION
- **Purpose:** Prove that all simulation outputs obey physical conservation laws and contain zero hallucinated figures.
- **Look at:** 
  - Kirchhoff Current and Voltage Law residuals (|err| < 1e-4 kW).
  - 1st & 2nd Law of Thermodynamics balances.
  - Battery mass-charge conservation verification.
- **Data used:** Mathematical residual matrices from simulation replay runs.
- **Click:** Station selector, residual tolerance filter, 'Run Full Physics Verification'.
- **What happens:** Verifies all node conservation balances across the active dataset in real time.
- **Demo use:** Prove to technical and scientific reviewers that the system is scientifically grounded.
- **Do not claim:** Do not claim empirical verification on physical hardware until physical sensors are connected.

---

### 10. POLICY
- **Purpose:** Govern the strict priority hierarchy that determines which systems receive power during emergencies.
- **Look at:** 
  - Lexicographical priority ordering ( \text{ Life Safety} \succ P_2 \text{ Satcom} \dots \succ P_8 \text{ Non-Essential}$).
  - Automatic load shedding ladder.
- **Data used:** Phase 8 operational governance ruleset.
- **Click:** Directive selector (Renewable Priority, Storm Protect, Minimum Fuel), Override simulation button.
- **What happens:** Demonstrates how secondary scientific experiments are deferred to protect habitat heat.
- **Demo use:** Demonstrate how organizational rules and human safety principles govern AI recommendations.
- **Do not claim:** Do not claim policies can override the fundamental laws of physics.

---

### 11. FIELD / HIL
- **Purpose:** Monitor the edge computing hardware, communication latency, and Hardware-In-The-Loop integration status.
- **Look at:** 
  - Edge node CPU/RAM load, round-trip packet latency, Physical Air-Gap status (DISCONNECTED).
- **Data used:** Simulated edge heartbeats and serial Modbus bridge packets.
- **Click:** 'Ping Edge Node', 'Cycle Heartbeat', packet trace inspector.
- **What happens:** Tests edge connectivity and proves that commands remain strictly advisory.
- **Demo use:** Show hardware and systems integration engineers how Polaris-EMS runs on ruggedized edge units.
- **Do not claim:** Do not claim live connection to physical station switchgear while air-gap barrier is active.
