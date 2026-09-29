# POLARIS-EMS — COMPLETE SCREEN & COMPONENT INVENTORY
**Release Baseline:** `f425cd4397edd63e99b266c20ab43028be06f286` (origin/main)  
**System Title:** Polar Energy Management & Autonomous Resilience System  
**Classification:** Operational Microgrid Human-Machine Interface (HMI) Specification  
**Audit Date:** September 2026  

---

## 1. Application Shell & Global Layout

The Polaris-EMS operator interface is structured as an air-gapped single-page application (SPA) with an industrial mission-critical layout. Navigation is driven by an internal tab dispatcher (`TabType` in `frontend/src/App.tsx`).

### 1.1 Global Layout Components
1. **Sidebar (`frontend/src/components/layout/Sidebar.tsx`)**:
   - Collapsible desktop navigation bar (collapses from `w-60` to `w-16`).
   - System branding: "POLARIS EMS" with pulsing status orb and active station indicator.
   - Station Badge: Current station identifier (`BHARATI`, `MAITRI`, `HIMADRI`).
   - Primary Navigation Group:
     - **Overview** (`overview`): High-level situational awareness, core metrics, 2D SLD.
     - **Energy Twin** (`twin`): High-fidelity 2D & 3D digital twin, PBR spatial canvas, node inspector.
     - **Forecast** (`forecast`): 48h multi-horizon Load, Solar, and Wind forecasts with CQR intervals.
     - **Scenarios** (`scenarios`): 14 polar stress scenarios + custom exploration matrix.
     - **Optimization** (`optimization`): HiGHS MILP 48h unit commitment and dispatch console.
     - **Resilience** (`resilience`): 10-dimension resilience radar and multi-horizon survival countdowns.
     - **Policy Engine** (`policy`): Autonomous rules, priority tiers, and hysteresis curves.
     - **Decision Trace** (`trace`): Cryptographic sha256 decision ledger and counterfactual replay.
     - **Field & Assets** (`edge`): Asset registry, edge connectivity, telemetry quality metrics.
     - **Validation** (`validation`): Empirical cross-phase benchmarks and validation evidence.
     - **Field HIL** (`field_hil`): Hardware-In-The-Loop emulator, SCADA boundary isolation, and bench testing.
     - **Design Lab** (`design_lab`): Visual style guide, tokens, typography, and atomic component showcase.
   - Operating Mode Indicator: `AUTO` (Emerald badge) vs `MANUAL` (Amber badge).
   - Collapse Toggle Button: Persists state to `localStorage.polaris_sidebar_collapsed`.

2. **Top Application Bar (`frontend/src/components/layout/TopBar.tsx`)**:
   - Mobile Menu Trigger Button (visible on `< md` screens).
   - Station Selector Dropdown / Badges: Real-time switching between Bharati, Maitri, and Himadri.
   - Real-Time Dual Clocks: Local system clock (`HH:mm:ss`) alongside Antarctic UTC operational clock (`HH:mm:ss UTC`).
   - Epistemic Integrity Badge: "COMPUTATIONAL TWIN • PHYSICAL SCADA DISCONNECTED".
   - Threat Warning Bell / Policy Navigation Trigger.
   - "QUICK ORIENTATION" Modal Trigger Button (`openOrientation()`).

3. **Contextual Alert Ribbon (`frontend/src/components/layout/AlertRibbon.tsx`)**:
   - Conditional banner rendered across top of screen whenever active threats or scenario alarms exist.
   - Displays severity tag (`CRITICAL`, `WARNING`), description, and direct link to Policy view.

4. **Industrial Toast Notification (`frontend/src/App.tsx`)**:
   - Floating notification panel in bottom-right corner for operator feedback on actions (dispatch approval, scenario activation, mode toggle).

5. **Evidence Drawer (`frontend/src/components/common/EvidenceDrawer.tsx`)**:
   - Slide-out global inspector showing raw telemetry provenance, model metadata, and mathematical formulations.

6. **Quick Orientation Modal (`frontend/src/components/common/QuickOrientationModal.tsx`)**:
   - Operator onboarding modal detailing the 6 epistemic tiers, keyboard shortcuts, and polar microgrid concepts.

---

## 2. Page 1 — Overview (`OverviewView.tsx`)

- **Route / Tab**: `'overview'`
- **Main Purpose**: Central operational dashboard providing immediate situational awareness of station power balance, renewable penetration, fuel autonomy, and active stress regimes.
- **Key Sections**:
  1. **Industrial Header & Station Banner**: Station identity, geographical coordinates, 400V 3-phase tag, quick station switcher tabs.
  2. **Authentic Real Station Ground Truth Spotlight**: Thumbnail of real station with inspect button triggering `ReferenceComparisonModal`.
  3. **Active Operating Mode Controller**: Direct toggle switch between `AUTO` and `MANUAL` mode.
  4. **Active Scenario Alarm Strip**: Visible only during stress injection; displays scenario name, impact badges, and "CLEAR SCENARIO / RESTORE BASELINE" button.
  5. **Core Telemetry KPI Grid (6 Metric Cards)**:
     - *Total Electrical Load*: Value in kW, served vs unserved, critical vs flexible load breakdown.
     - *Total Generation*: Value in kW, renewable penetration percentage bar.
     - *Solar Photovoltaic*: Value in kW, installed capacity peak, inverter status badge.
     - *Wind Turbine*: Value in kW, installed capacity, cut-in/cut-out status badge.
     - *Battery Storage (BESS)*: State of Charge (SOC %), charge/discharge power (kW), status (`CHARGING`, `DISCHARGING`, `STANDBY`).
     - *Diesel Generators*: Output in kW, reserve capacity, fuel burn rate (L/h), fuel days remaining.
  6. **Single-Line Diagram (SLD) & Power Flow Canvas**:
     - Toggle between `2D_BUS` and `GROUND_TRUTH` topology views.
     - Dynamic flow animated lines connecting Generation (PV, Wind, DG) and Storage (BESS) to 400V AC Bus and Distribution Feeders (Life Support, Science, Auxiliary).
  7. **Multi-Horizon Survivability Strip**:
     - Overall survival horizon (Hours) and binding subsystem tag.
     - Critical load survival, battery endurance, thermal habitability, and fuel endurance countdowns.
  8. **Autonomous Directives & Solver Status**:
     - Active policy directive (e.g., `RENEWABLE_PRIORITY`, `ISLANDED_SURVIVAL`).
     - HiGHS optimizer recommendation text and solve time in milliseconds.
     - "DISPATCH CONSOLE" button navigating to Optimization view.
  9. **Environmental Conditions Bar**:
     - Ambient temperature (°C), wind speed (m/s), solar irradiance (W/m²), cloud fraction, solar elevation angle (°).

---

## 3. Page 2 — Energy Digital Twin (`EnergyTwinView.tsx`)

- **Route / Tab**: `'twin'`
- **Main Purpose**: Real-time 2D schematic and 3D spatial digital twin displaying structural equipment placement, high-fidelity electrical bus topologies, and power flow vectors.
- **Key Sections**:
  1. **Twin Viewport Mode Switcher**:
     - `3D SPATIAL`: Three.js PBR scene rendered with realistic polar lighting, terrain elevation, snowfall particles, and architectural station meshes.
     - `2D TOPOLOGY`: Comprehensive schematic single-line diagram showing electrical bus nodes, breakers, transformers, and distribution junctions.
     - `ACCESSIBLE TABLE`: High-contrast, screen-reader friendly data table of all microgrid nodes and telemetry.
  2. **3D Scene Camera & Environment Controls**:
     - Orbit controls (rotate, pan, zoom).
     - Camera presets: "TOP-DOWN OVERVIEW", "ARRAY FOCUS", "POWERHOUSE FOCUS", "RESIDENTIAL QUARTERS".
     - Weather visualization toggles: Blizzard snowfall, wind drift vectors, generator exhaust plumes.
  3. **Interactive Node Inspector (Drawer / Side Panel)**:
     - Clicking any asset (PV-1, WTG-1, DG-1, DG-2, DG-3, BESS, Main Bus, HVAC) opens a deep telemetry inspector.
     - Displays nominal capacity, active power, voltage, current, temperature, health status, and physical location coordinates.
  4. **Physical Reference Comparison Modal Trigger**:
     - Button opening side-by-side split screen comparing real photographic station assets against 3D mesh representations.
  5. **Timeline Replay Scrub Bar (`TwinTimeline.tsx`)**:
     - Scrub through 48-hour operational history or forecast trajectories.
     - Play, pause, step forward/backward, and playback speed multipliers (1x, 5x, 10x).

---

## 4. Page 3 — Forecast Studio (`ForecastView.tsx`)

- **Route / Tab**: `'forecast'`
- **Main Purpose**: Multi-horizon probabilistic forecasting console for Station Load, Solar Generation, and Wind Generation across a 48-hour planning horizon.
- **Key Sections**:
  1. **Forecast Target Selector**:
     - Tabs for `LOAD` (kW), `SOLAR` (kW), `WIND` (kW), and `NET DEMAND` (kW).
  2. **Horizon & Resolution Controls**:
     - Horizon selection: 1h, 6h, 12h, 24h, 48h, 168h (7 days).
  3. **Interactive Forecast Chart**:
     - Point forecast line ($P_{50}$ median).
     - 80% Conformal Prediction Band ($P_{10} - P_{90}$ shaded interval).
     - 90% Conformal Prediction Band ($P_{05} - P_{95}$ outer band).
     - Historical observed telemetry overlay.
  4. **Model Performance & Calibration Card**:
     - Active model artifact name (e.g., `polaris-load-xgb-bharati-v1.0`).
     - Validation metrics: MAE, RMSE, SMAPE, $R^2$, Capacity-Normalized MAE (%).
     - Conformal coverage check: Empirical 80% coverage vs nominal target (e.g., 81.23% observed).
     - Pinball loss and quantile sharpness values.
  5. **Meteorological Drivers Panel**:
     - Correlated weather forecasts: Temperature plunge curves, katabatic wind surges, cloud fraction attenuation.

---

## 5. Page 4 — Scenario Engine (`ScenariosView.tsx`)

- **Route / Tab**: `'scenarios'`
- **Main Purpose**: Catalog, evaluation, and stress-testing workbench for polar weather extremes, equipment trips, and logistics delays.
- **Key Sections**:
  1. **Scenario Filter & Category Tabs**:
     - `ALL`, `ENVIRONMENTAL` (Blizzard, Extreme Cold, Cloudy), `ASSET FAILURE` (Solar Trip, Wind Trip, Battery Degradation), `LOGISTICS` (Resupply Delay), `COMPOUND` (Combined Polar Stress, Unforeseen Weather).
  2. **14 Pre-Configured Scenario Cards Grid**:
     - Card displaying Scenario Name, Category Badge, Severity Rating (`CRITICAL`, `HIGH`, `ELEVATED`, `NORMAL`).
     - Transformation summary (e.g., Blizzard: Ambient $-10\text{°C}$, Wind $2.0\times$, Solar $= 0\text{ W/m}^2$, Cloud $= 1.0$).
     - Engineering rationale badge.
     - "ACTIVATE SCENARIO" button.
     - Active indicator with pulsing red badge when running.
  3. **Custom Scenario Parameter Sandbox**:
     - Sliders for Temperature Offset ($-30\text{°C}$ to $+10\text{°C}$), Wind Multiplier ($0\times$ to $3\times$), Solar Irradiance Scaling ($0\%$ to $150\%$), Battery Degradation ($20\%$ to $100\%$), Fuel Delay Days ($0$ to $30\text{ days}$).
     - "RUN CUSTOM SIMULATION" button.
  4. **Scenario Delta Comparison Panel**:
     - Side-by-side delta visualization showing baseline vs perturbed trajectory for load, generation, fuel burn, and resilience index.

---

## 6. Page 5 — Optimization & Dispatch Console (`OptimizationView.tsx`)

- **Route / Tab**: `'optimization'`
- **Main Purpose**: HiGHS MILP 48-hour unit commitment and dispatch console showing generation schedules, fuel consumption, battery state, and operator approval controls.
- **Key Sections**:
  1. **Solver Status Banner**:
     - Solver status badge (`OPTIMAL`, `FEASIBLE`, `TIME_LIMIT`).
     - Solve execution duration (e.g., `14.2 ms`).
     - MIP Gap metric (`3.0%`).
     - Total estimated 48-hour fuel burn in Liters.
  2. **48-Hour Dispatch Stack Chart**:
     - Stacked area chart showing power balance hour-by-hour: Solar (Amber), Wind (Sky Blue), BESS Discharge (Emerald), Diesel Generator 1/2/3 (Slate), Load Demand Line (Red dashed).
  3. **Unit Commitment Matrix (DG-1, DG-2, DG-3)**:
     - Heatmap / timeline showing hourly binary commitment state ($u_{g,t}$) and kW loading for each generator.
  4. **Battery Energy Storage Trajectory**:
     - Dual-axis chart showing SOC % curve alongside charge/discharge power blocks.
  5. **Operator Approval & Actuation Bar**:
     - In `MANUAL` mode: "APPROVE DISPATCH SCHEDULE", "RE-SOLVE WITH CONSERVATIVE BIAS", "REJECT / HOLD STANDBY" buttons.
     - In `AUTO` mode: "AUTONOMOUS ACTUATION ENGAGED — CONTINUOUS ROLLING UPDATE" status indicator.

---

## 7. Page 6 — Resilience Radar & Survivability (`ResilienceView.tsx`)

- **Route / Tab**: `'resilience'`
- **Main Purpose**: Multidimensional microgrid resilience assessment across 10 mission-critical indices and survival horizon countdowns.
- **Key Sections**:
  1. **Composite Resilience Index Gauge**:
     - Master score ($0.0 - 1.0$) with status badge (`SAFE`, `WATCH`, `AT_RISK`, `CRITICAL`).
  2. **10-Dimension Resilience Radar Chart**:
     - 1. Energy Adequacy
     - 2. Critical Load Survival
     - 3. Thermal Resilience
     - 4. Generation Adequacy
     - 5. Storage Autonomy
     - 6. Fuel Reserves
     - 7. Logistics Endurance
     - 8. Renewable Fraction
     - 9. System Recovery Speed
     - 10. Composite Survivability
  3. **Multi-Horizon Survival Timers Grid**:
     - *Overall Survival Horizon*: Binding countdown in hours before mission compromise.
     - *Critical Load Survival*: Hours of continuous power guaranteed for life support.
     - *Thermal Habitability Horizon*: Hours until indoor temperature drops below $12\text{°C}$ ($10\text{°C}$ Maitri, $14\text{°C}$ Himadri).
     - *Fuel Stock Endurance*: Total days of diesel fuel remaining under projected dispatch.
  4. **Vulnerability & Bottleneck Inspector**:
     - Identifies binding subsystem (e.g., "BINDING: BATTERY STORAGE DEPLETION AT T+18.5H").

---

## 8. Page 7 — Policy Engine (`PolicyView.tsx`)

- **Route / Tab**: `'policy'`
- **Main Purpose**: Rule-based safety governor and prioritized load shedding controller enforcing thermal envelopes and generator protection.
- **Key Sections**:
  1. **Active Policy Regime Banner**:
     - Displays active policy state: `RENEWABLE_PRIORITY`, `CONSERVATION_STAGE_1`, `CONSERVATION_STAGE_2`, `ISLANDED_SURVIVAL`, `BLACK_START_PREP`.
  2. **Load Priority Shedding Hierarchy (Tiers 1–10)**:
     - Tier 1: Life Support HVAC (Non-deferrable, Critical)
     - Tier 2: Water Line Freeze Protection (Non-deferrable, Extreme consequence)
     - Tier 3: Emergency Comms & Satellite Telemetry (Non-deferrable)
     - Tier 4: Science Laboratory Instruments (Important)
     - Tier 5: Compute Servers & Storage (Important)
     - Tier 6: Galley & Cold Storage (Important)
     - Tier 7: Living Quarters Lighting (Operational, Deferrable)
     - Tier 8: Waste Treatment Auxiliary (Operational, Deferrable)
     - Tier 9: Snow Melter Bulk Heating (Flexible, Deferrable)
     - Tier 10: Vehicle & Skidoo EV Charging (Flexible, Deferrable)
  3. **Hysteresis & Safety Thresholds Panel**:
     - Battery minimum SOC cut-off ($20\%$).
     - Diesel minimum loading limit ($30\%$).
     - Minimum indoor safe temperature ($12\text{°C}$).
  4. **Policy Decision Log**:
     - Real-time audit trail of policy evaluations, shedding decisions, and constraint overrides.

---

## 9. Page 8 — Decision Trace Ledger (`DecisionTraceView.tsx`)

- **Route / Tab**: `'trace'`
- **Main Purpose**: Cryptographically verifiable decision ledger recording every optimizer execution, scenario activation, and operator action with explainability reports.
- **Key Sections**:
  1. **Trace Ledger Table**:
     - Columns: Trace ID, Timestamp (UTC), Station, Trigger Event, Decision Category, Primary Directives, Solved Status, Verification Hash.
  2. **Trace Filter & Search Bar**:
     - Filter by Station (`BHARATI`, `MAITRI`, `HIMADRI`), Trigger (`OPTIMIZER`, `SCENARIO`, `MANUAL_OVERRIDE`, `POLICY_TRIP`).
  3. **Detailed Decision Inspector**:
     - Selecting a trace opens full decision detail:
       - Mathematical Objective breakdown.
       - Generation dispatch vector.
       - Natural language explainability summary ("Why DG-1 was started: Solar dropped to 0 kW and BESS reached minimum discharge limit").
       - SHA-256 cryptographic lineage hash.
  4. **Counterfactual Trace Comparison**:
     - Side-by-side comparison of actual decision vs counterfactual baseline (e.g., "Without optimizer: 420 L additional fuel burned").

---

## 10. Page 9 — Field & Assets Management (`EdgeView.tsx`)

- **Route / Tab**: `'edge'`
- **Main Purpose**: Physical microgrid asset inventory, edge node connectivity monitoring, and telemetry data quality auditing.
- **Key Sections**:
  1. **Asset Inventory Cards**:
     - PV Inverters, Wind Turbines, Diesel Generators, BESS PCS, Building HVAC, Main 400V Switchgear.
     - Real-time telemetry: Voltage, Current, Temperature, Vibration, Operating Hours, Service Due countdown.
  2. **Edge Node Telemetry & Sync Status**:
     - Edge Gateway connection status: `AIR-GAPPED LOCAL RUNTIME` (Active, Latency $< 2\text{ ms}$).
     - Ingestion buffer health: FIFO buffer queue depth, dropped packet rate ($0.0\%$).
  3. **Data Quality Audit**:
     - Telemetry completeness ($100\%$), out-of-range sensor alerts ($0$), timestamp jitter check.

---

## 11. Page 10 — Validation & Benchmark Archive (`ValidationView.tsx`)

- **Route / Tab**: `'validation'`
- **Main Purpose**: Comprehensive verification matrix containing offline benchmarks, mathematical proofs, energy conservation audits, and cross-phase test results.
- **Key Sections**:
  1. **Energy Conservation Validation**:
     - Continuous Kirchhoff balance check: $\sum P_{\text{gen}} - \sum P_{\text{load}} - P_{\text{loss}} = 0.000\text{ kW}$ (Tolerance $< 10^{-4}\text{ kW}$).
  2. **Forecast Model Benchmark Suite**:
     - Test split evaluation metrics across all 9 models vs Persistence, Seasonal Naive, and Ridge baselines.
  3. **Optimizer Rigor Audit**:
     - Branch-and-cut optimality proofs, constraint satisfaction checks, zero unphysical generation proof.
  4. **Empirical Technical Evidence Table**:
     - Comprehensive tabular audit across all project development phases.

---

## 12. Page 11 — Field HIL & SCADA Boundary (`FieldHILValidationView.tsx`)

- **Route / Tab**: `'field_hil'`
- **Main Purpose**: Hardware-In-The-Loop simulation control, SCADA boundary isolation auditing, and physical bench test harness.
- **Key Sections**:
  1. **SCADA Air-Gap & Isolation Status**:
     - Prominent status indicator: `PHYSICAL SCADA LINK: DISCONNECTED (AIR-GAPPED)`.
     - Computational twin isolation protocol verified.
  2. **HIL Emulator Controls**:
     - Modbus / DNP3 emulator bridge control.
     - Simulated PLC hardware clock frequency.
  3. **Fault Injection Bench**:
     - Inject simulated breaker trips, sensor drift, and communication packet drops to test edge autonomous response.

---

## 13. Page 12 — Design Lab & Component Showcase (`DesignLabView.tsx`)

- **Route / Tab**: `'design_lab'`
- **Main Purpose**: Visual design system reference displaying UI tokens, typography, colors, badges, and interactive component states.
- **Key Sections**:
  1. Color Palette Swatches (Polar Ice Sky, Deep Oceanic Navy, Arctic White, Emerald Safe, Amber Watch, Rose Critical).
  2. Typography Scale (Inter / Mono data formats).
  3. Status Badges and Provenance Tags.
  4. Button Hierarchies (Primary, Secondary, Danger, Ghost).
