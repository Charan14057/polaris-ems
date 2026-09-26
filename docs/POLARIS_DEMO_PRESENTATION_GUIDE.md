# POLARIS-EMS — DEMO PRESENTATION & OPERATOR PLAYBOOK
**Document Version:** 2.0.0 (Production Verified)
**Target Timeframes:** 5-Minute Executive Walkthrough • 15-Minute Technical Deep Dive • 30-Minute Architecture Review
**Operational Status:** Software Simulation (PHYSICAL_CONNECTIVITY = DISCONNECTED)

---

## 1. Five-Minute Executive Walkthrough

### 00:00 — Mission Overview (/)
- **What to Click:** Ensure Bharati station is selected. Point to Mission Demand (kW) and Clean Renewable Share (%).
- **What Should Appear:** Overview dashboard with cool neutral workspace, 3-tier system flow architecture, and clean 400V bus status.
- **What It Means:** Polaris-EMS provides instantaneous situational awareness of energy health in isolated polar environments.
- **What to Say:** Welcome to Polaris-EMS, the intelligent energy management and resilience advisory system developed for extreme polar microgrids like India's Bharati, Maitri, and Himadri research stations. In Antarctica, heating failure is an existential threat; this dashboard monitors total generation, battery survival runway, and critical life-support status.
- **What NOT to Claim:** Do not claim this is live physical satellite telemetry. State clearly: This is running in real-time simulation under our physical air-gap protocol.

---

### 00:45 — Operational 3D Spatial Digital Twin (/energy)
- **What to Click:** Click Launch Spatial Digital Twin or select Energy in left navigation sidebar. Keep default mode: LIVE. Toggle between 3D ISO, TOP, and ELEVATION camera presets. Cycle through visualization layers: ARCH -> ENERGY -> IMPACT.
- **What Should Appear:** Reference-aligned 3D station model of Bharati on elevated steel stilts. Directional power flow particles moving from solar array and katabatic wind turbines toward main 400V switchboard and into life-support heating.
- **What It Means:** Real-time Kirchhoff energy conservation translated into an intuitive 3D operational spatial representation.
- **What to Say:** Here is our flagship 3D Operational Digital Twin. Notice that the station is visibly elevated on aerodynamic piles matching Bharati's real-world Larsemann Hills architecture. The colored conduits represent actual computed power flow: gold for solar, blue for katabatic wind, and green for our battery storage bank. In our ENERGY layer, flow density scales directly with computed kilowatts.
- **What NOT to Claim:** Do not claim the 3D model is an exact millimeter BIM survey; state that it is reference-aligned representative geometry.

---

### 02:00 — Forward Weather Drivers & System Effect (/energy)
- **What to Click:** Scroll to Forward Weather Drivers card. Click Next 6h, 12h, and 24h horizon tabs.
- **What Should Appear:** Wind speed (m/s), solar irradiance (W/m2), ambient temperature (-24C), and expected system effects.
- **What It Means:** Demonstrates how the system looks forward in time using machine learning weather models to anticipate operational consequences.
- **What to Say:** Polaris-EMS doesn't just react to current readings; it connects Phase 3 machine learning weather models directly to microgrid physics. Looking ahead to the Next 12h, we see anticipated katabatic wind increases paired with dropping solar irradiance as polar night approaches, predicting a shift toward battery buffer utilization.
- **What NOT to Claim:** Do not claim weather forecasts are 100% infallible; explain that conformal prediction quantiles bound the uncertainty.

---

### 02:45 — Stress Testing & Scenarios (/scenarios)
- **What to Click:** Navigate to Scenarios in left sidebar. Click Katabatic Storm (Wind Cut-Out) preset. Click Run Simulation.
- **What Should Appear:** Simulation trajectory showing high-wind turbine cut-out, BESS discharge surge, and automated advisory recommendation.
- **What It Means:** Validates system resilience under severe polar disturbances without endangering physical equipment.
- **What to Say:** When hurricane-force katabatic winds exceed 25 m/s, wind turbines must feather their blades to prevent structural failure. In this simulated disturbance, Polaris-EMS immediately detects the generation drop, evaluates our survival runway, and initiates automated advisory protection.
- **What NOT to Claim:** Do not claim hardware breakers are physically opened in Antarctica; emphasize the digital twin sandbox.

---

### 03:30 — AUTO Mode Advisory & Operator Approval (/energy)
- **What to Click:** Return to Energy. Under Operating Mode, observe AUTO mode with advisory card: OPTIMIZER ADVISORY: Cold-soak prevention warm-up. Click Simulate Operator Approval.
- **What Should Appear:** Simulation recalculates state; battery discharge ramps and generator standby posture activates. Real-time status bar updates with new timestamp.
- **What It Means:** Demonstrates that AUTO mode acts as an automated advisory solver through existing Phase 6 MILP authority, strictly maintaining human-in-the-loop governance.
- **What to Say:** Notice that AUTO mode is an advisory optimizer, not an unchecked physical actuator. It presents an optimal dispatch plan and requires supervisory approval. When we simulate approval, the digital twin recalculates all node equations, updating our generation mix in real time.
- **What NOT to Claim:** Never say autonomous physical autopilot; say automated advisory decision-support with human approval.

---

### 04:15 — MANUAL Simulation & Impact Review (/energy)
- **What to Click:** Switch Operating Mode to MANUAL. Select Action: dg1_start (Start Diesel Genset 1 to 40 kW). Review impact card (Reserve +40 kW, Fuel burn +8.4 L/h). Click Simulate Action.
- **What Should Appear:** Diesel generator icon changes to ONLINE, amber power flow stream energizes from powerhouse to main bus, and battery begins charging.
- **What It Means:** Operators can safely test manual decisions inside the physics engine before executing them in the field.
- **What to Say:** In MANUAL mode, station engineers can test operational actions before touching equipment. When we simulate starting Genset 1, the digital twin updates the electrical bus balance, showing surplus generation flowing into battery charging.

---

### 04:45 — Trace Power, Trace Impact & Conclusion (/energy)
- **What to Click:** In 3D canvas, click Life Support & Heat module. In side inspector, click Trace My Power Route. Toggle Trace Disturbance Impact.
- **What Should Appear:** Unrelated circuits dim to 8% opacity. Illuminated path traces directly from Wind Turbine 1 through Main Switchboard SWB-1 to Life Support HVAC heater.
- **What It Means:** Complete spatial circuit explainability.
- **What to Say:** Finally, our Trace Power and Trace Impact tools allow operators to isolate circuit lineages instantly. Here, we see exactly how katabatic wind energy is routed into life-support heating. In summary, Polaris-EMS delivers sovereign, explainable, and resilient energy management for the most extreme environments on Earth.

---

## 2. Fifteen-Minute Technical Walkthrough
1. 00:00 – 03:00: Overview & 3D Spatial Digital Twin architecture (Three.js WebGL rendering, station profiles).
2. 03:00 – 06:00: Physics-Informed Forecasting (/forecast) — Conformal quantiles, P10–P90 uncertainty envelopes.
3. 06:00 – 09:00: MILP Dispatch Optimization (/optimization) — Objective formulation, fuel efficiency curves, battery degradation constraints.
4. 09:00 – 12:00: Decision Traceability & DAG Explainability (/decisions) — 7-stage lineage, counterfactual delta diffing, reason codes.
5. 12:00 – 15:00: Physics Verification & Epistemic Governance (/validation & /policy) — Kirchhoff residual proofs (|err| < 1e-4 kW), lexicographical priority order.

---

## 3. Thirty-Minute Architecture Deep Dive
- Detailed mathematical formulations (Mixed-Integer Linear Programming equations).
- Spatial coordinate systems and Three.js scene graph hierarchies.
- Microgrid air-gap boundary enforcement and serial HIL bridge protocols.
- Conformal prediction mathematical proofs and coverage calibration diagnostics.
- Failure injection analysis across all 12 Phase 5 polar disturbance scenarios.
