# POLARIS-EMS — DEMO EXECUTION RUNBOOK & SCRIPT
**Release Baseline:** `f425cd4397edd63e99b266c20ab43028be06f286` (origin/main)  
**System Title:** Polar Energy Management & Autonomous Resilience System  
**Presentation Class:** Live Demonstration & Video Walkthrough Guide  
**Target Duration:** 3 to 5 Minutes  
**Audit Date:** September 2026  

---

## 1. Live Demonstration & Video Architecture

This runbook provides the exact, click-by-click operational choreography for presenting Polaris-EMS to evaluators, technical judges, and video audiences. The recommended primary demonstration journey follows the **BLIZZARD** storm compound stress scenario on the **BHARATI** research station.

---

## 2. Pre-Demo Checklist (T-Minus 5 Minutes)

1. **Verify Local Environment**:
   - Backend running on `http://127.0.0.1:8000` (FastAPI daemon verified).
   - Frontend running on `http://localhost:5173` (Vite dev server verified) or production port.
2. **Initial Reset**:
   - Navigate to `Overview` tab.
   - Ensure Station is set to `BHARATI`.
   - Ensure Operating Mode is set to `AUTO`.
   - Ensure Active Scenario is `NORMAL_BASELINE` (no red alarm ribbon visible).
3. **Display Configuration**:
   - Resolution: 1920x1080 (1080p Full HD) or 2560x1440 (2K).
   - Browser Zoom: 100%.
   - Fullscreen Mode (`F11`).

---

## 3. Master 3–5 Minute Demonstration Script

### Scene 1: Baseline Overview & Station Situational Awareness (0:00 - 0:45)
- **Starting Screen**: `Overview` tab (`/` or tab `overview`).
- **Presenter Action**:
  1. Point to Top Application Bar showing dual clocks (`Local` and `Antarctic UTC`) and station title: "Bharati Research Station (69°S • Larsemann Hills)".
  2. Point to the Ground Truth Photographic Card showing the authentic Indian Antarctic station on elevated stilts.
  3. Review Core KPI Grid:
     - Load: `34.8 kW` (all served, zero unserved load).
     - Generation: `42.7 kW` (100% renewable penetration: `14.2 kW` Solar + `28.5 kW` Wind).
     - Battery: `68.0% SOC`, charging at `7.9 kW`.
     - Diesel Generators: `0.0 kW` output, all units on cold standby (`STANDBY`), `18,500 L` fuel remaining (`64 days` autonomy).
  4. Point to the Single-Line Diagram (SLD): Highlight the green animated power flows from Solar and Wind feeding the 400V AC Bus, while surplus flows into BESS storage.
  5. Point to the Survivability Panel: `Overall Survival: 168.0 h`, Composite Resilience `0.91 (SAFE)`.
- **What Presenter Says**:
  > "Welcome to Polaris-EMS, the autonomous microgrid energy management and resilience system engineered for extreme polar environments. We are currently looking at the live operational overview of India's Bharati Station in East Antarctica. Under this baseline summer regime, the station operates at 100% renewable penetration—28.5 kW from wind and 14.2 kW from solar PV—completely supplying the 34.8 kW station demand while charging our battery bank at 7.9 kW. The diesel generators are on cold standby, with zero fuel burn."

---

### Scene 2: 3D Digital Twin & Spatial Inspection (0:45 - 1:20)
- **Navigation**: Click `Energy Twin` in sidebar (or shortcut tab `twin`).
- **Presenter Action**:
  1. Show the Three.js 3D PBR viewport rendering Bharati Station's elevated container architecture, wind turbines, solar array, and snowy Larsemann Hills terrain.
  2. Perform gentle orbit/pan around the station using mouse drag.
  3. Click on the Wind Turbine mesh: The Twin Inspector drawer opens on the right, showing `25 kW rated`, active power `28.5 kW`, aerodynamic wind speed `8.5 m/s`.
  4. Click "COMPARE FIELD REFERENCE" button: Shows side-by-side photographic validation of the real Bharati station vs the computational 3D twin.
  5. Close modal, point to the 2D Topology switcher tab: Show the electrical bus distribution hierarchy.
- **What Presenter Says**:
  > "Polaris-EMS features a dual-mode Digital Twin. The 3D spatial twin renders station architecture, equipment placement, and physics-driven environmental conditions using physically-based materials. When we select any asset—such as this wind turbine—the inspector displays its real-time electrical state, operating limits, and aerodynamic inflow. Notice that every visual element is strictly tied to our underlying physical models, avoiding cosmetic randomization."

---

### Scene 3: Blizzard Scenario Activation (1:20 - 2:00)
- **Navigation**: Click `Scenarios` in sidebar.
- **Presenter Action**:
  1. Scroll to the `BLIZZARD` scenario card (Polar Blizzard Storm, Compound Disaster).
  2. Show the mathematical perturbations declared on the card:
     - Ambient Temperature: $-10.0\text{°C}$ drop (wind-chill plunge to $-28.5\text{°C}$).
     - Wind Speed: $2.0\times$ multiplier (katabatic gale surging to $17.0\text{ m/s}$).
     - Cloud Fraction: $1.0$ (complete whiteout storm).
     - Solar Irradiance: Forced to $0.0\text{ W/m}^2$ (dense blowing snow blackout).
  3. Click the red button: **"ACTIVATE SCENARIO"**.
  4. High-visibility Toast Notification fires: "SCENARIO ACTIVATED: BLIZZARD".
  5. Top Alert Ribbon turns RED: "ACTIVE THREAT: POLAR BLIZZARD STORM • ELEVATED HEATING DEMAND".
- **What Presenter Says**:
  > "Now, let's inject a severe compound polar stress event: the Polar Blizzard Storm. In Antarctica, a blizzard is not just snow; it couples a severe temperature plunge with gale-force winds and a complete solar whiteout. When I activate this scenario, watch how the perturbation deterministically propagates through our forecast, optimizer, and physical twin."

---

### Scene 4: Observing Cascading System Impact (2:00 - 2:45)
- **Navigation**: Click `Overview` tab.
- **Presenter Action**:
  1. Point to the Red Scenario Alarm Banner at the top of Overview: "SCENARIO ACTIVE: BLIZZARD".
  2. Point to the KPI changes:
     - Solar generation collapsed to `0.0 kW` (Solar status: `ZERO_IRRADIANCE`).
     - Ambient temperature plunged to `-28.5°C`.
     - Total heating load surged due to building thermal envelope losses ($U \cdot A \cdot \Delta T$).
     - High wind pushed turbine output, but autonomous safety monitoring prevents overspeed trip.
     - HiGHS Optimizer automatically commanded DG-1 to start (`ONLINE`), providing baseline firm power.
     - Battery shifted seamlessly from `CHARGING` to `DISCHARGING` buffer mode.
  3. Point to the Resilience Strip: Composite score dropped from `0.91` to `WATCH / AT_RISK`, with thermal habitability horizon tightening.
- **What Presenter Says**:
  > "Back on the Overview screen, the system response is instantaneous. Solar generation has dropped to zero due to whiteout conditions. Building heat loss surged as temperatures dropped to -28.5°C, increasing electrical heating demand. To protect battery state-of-charge and prevent unserved critical load, the autonomous policy engine and optimizer committed Diesel Generator 1, while modulating BESS discharging to stabilize bus frequency."

---

### Scene 5: Forecast Studio & Conformal Prediction (2:45 - 3:20)
- **Navigation**: Click `Forecast` tab.
- **Presenter Action**:
  1. Show the 48-hour forecast chart for `SOLAR`: Irradiance collapsed to zero across the storm window.
  2. Select `LOAD`: Show the forecast load surge reflecting building thermodynamics.
  3. Highlight the Shaded Uncertainty Bands ($P_{10} - P_{90}$):
     - Explain Conformalized Quantile Regression (CQR).
     - Show the calibration card: 81.23% empirical coverage on out-of-sample Antarctic test data, 0 quantile crossings.
- **What Presenter Says**:
  > "In the Forecast Studio, our multi-horizon models reflect the storm dynamics. Because polar weather is notoriously volatile, Polaris-EMS does not rely on naive point predictions. We implement Conformalized Quantile Regression—CQR—which guarantees mathematically calibrated uncertainty intervals. The 80% prediction interval achieves an empirical coverage of 81.23% with zero quantile crossings, providing our optimizer with dependable bounds."

---

### Scene 6: Optimization & Dispatch Proof (3:20 - 4:00)
- **Navigation**: Click `Optimization` tab.
- **Presenter Action**:
  1. Point to the HiGHS Solver Banner: `OPTIMAL` in `14.2 ms`, MIP Gap `3.0%`.
  2. Review the 48-Hour Stacked Area Dispatch Chart:
     - Show DG-1 operating within its high-efficiency loading window ($> 30\%$).
     - Show flexible load (snow melters and EV skidoo chargers) deferred to later hours.
     - Critical life support load remains 100% served.
  3. Point to the Operating Mode Controller: Explain that the operator can switch to `MANUAL` to inspect or override dispatch decisions, or leave in `AUTO` for autonomous execution.
- **What Presenter Says**:
  > "The Optimization console showcases our core dispatch engine. Formulated as a Mixed-Integer Linear Program in Pyomo and solved via the state-of-the-art HiGHS branch-and-cut solver in just 14 milliseconds, the dispatch schedule guarantees exact physical power balance. It enforces generator minimum loading limits, prevents battery over-discharge, and defers non-critical snow melting to conserve fuel while keeping life support fully energized."

---

### Scene 7: Cryptographic Decision Ledger & Baseline Restoration (4:00 - 4:45)
- **Navigation**: Click `Decision Trace` tab.
- **Presenter Action**:
  1. Point to the top row of the ledger: The latest entry timestamped with the Blizzard optimization event.
  2. Expand the trace details:
     - Show the SHA-256 lineage hash verifying cryptographic audit integrity.
     - Show natural language explainability: "DG-1 online commitment triggered by zero solar and surge in building heat loss".
  3. Return to `Overview` tab and click **"CLEAR SCENARIO / RESTORE BASELINE"**.
  4. Toast confirms restoration; system returns to unperturbed renewable baseline.
- **What Presenter Says**:
  > "Every single autonomous decision is recorded in our tamper-evident Decision Trace ledger, complete with an explanation and cryptographic SHA-256 hash for post-mission auditing. Finally, when the blizzard subsides, the operator or automated clearing resets the system, immediately ramping back to our high-efficiency renewable baseline. Polaris-EMS delivers complete, verifiable polar microgrid resilience."

---

## 4. Alternative Mini-Demo Paths

### Path B: Solar Generation Failure (Inverter Trip)
1. Navigate to `Scenarios` -> Select `SOLAR_GENERATION_FAILURE`.
2. Activate scenario -> Solar drops to 0 kW immediately, Wind and BESS compensate.
3. Highlight: Demonstrates sudden electrical trip without weather changes.

### Path C: Wind Generation Failure (Mechanical Trip)
1. Navigate to `Scenarios` -> Select `WIND_GENERATION_FAILURE`.
2. Activate scenario -> Wind turbine trips to 0 kW.
3. Highlight: DG-1 automatically starts up within seconds; BESS handles transient frequency sag.

### Path D: Battery Degradation
1. Navigate to `Scenarios` -> Select `BATTERY_DEGRADATION`.
2. Activate scenario -> BESS usable capacity drops to 65%.
3. Highlight: Resilience radar storage dimension contracts; optimizer restricts charging rate.

---

## 5. Potential Failure Points & Recovery Protocols

| Potential Issue | Symptom | Immediate Recovery Action |
| :--- | :--- | :--- |
| **Backend Unreachable** | Red network toast "API Connection Failed" | Verify terminal daemon on port 8000. Restart: `.\.venv\Scripts\python.exe -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000`. |
| **Scenario Won't Clear** | Red alarm banner remains after click | Click "CLEAR SCENARIO" on Overview; if stuck, navigate to Scenarios tab and click "NORMAL_BASELINE" -> "ACTIVATE". |
| **3D Canvas Blank** | WebGL context lost or black canvas | Click "2D TOPOLOGY" tab and switch back to "3D SPATIAL", or refresh browser tab (`F5`). |
| **Operating Mode Glitch** | Toggle doesn't update | Click mode switch on Overview; state is tracked in `StationContext.operatingModeRef`. |
