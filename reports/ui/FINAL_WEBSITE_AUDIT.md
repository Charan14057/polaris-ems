# POLARIS-EMS — COMPREHENSIVE ALL-PAGE WEBSITE AUDIT
**Prompt ID**: 61853 / Phase 18 Final Launch Quality Gate  
**Scope**: All 12 application routes in `frontend/src/views`

---

## Route 1: Overview (`/overview` — `OverviewView.tsx`)
- **What is this page?**: The executive operational dashboard answering "What is happening at the station right now?"
- **Main Visual**: Primary energy balance donut and real-time generation flow distribution strip with live status badges.
- **Primary User Action**: High-level station situation assessment and one-click navigation to the Energy Digital Twin.
- **Data Shown**: Station health score, total demand (kW), total generation (kW), renewable share (%), battery SOC (%), fuel autonomy (days), active threat count.
- **Where Does It Come From?**: Backend live session snapshot via `GET /api/v1/twin/live/{stationId}`.
- **What Changes When Something Changes?**: When weather or generator state changes, generation mix adjusts immediately; threat ribbons alert to operational risks.
- **What Can the User Inspect?**: Station operational summary, key subsystem metrics, upcoming 6-hour forecast trend.
- **What Belongs on This Page?**: Core situational metrics and primary energy balance.
- **What Was Moved to Secondary Detail?**: Raw solver matrices and equipment breaker logs moved to dedicated Dispatch and Assets views.

---

## Route 2: Energy Digital Twin (`/energy` — `EnergyTwinView.tsx`)
- **What is this page?**: The flagship real-time 3D spatial microgrid digital twin and topological power flow visualizer.
- **Main Visual**: Reference-aligned 3D WebGL spatial model of Bharati / Maitri / Himadri with directional energy flow conduits and particle streams.
- **Primary User Action**: Inspecting physical equipment, tracing power flow, evaluating upstream circuits, simulating manual actions, and testing stress scenarios.
- **Data Shown**: Live kW on each electrical circuit, equipment status (ONLINE / FAULT / STANDBY), battery charge/discharge vectors, bus voltages, fuel levels.
- **Where Does It Come From?**: Server-Sent Events (SSE) live simulation stream (`GET /api/v1/twin/live/{stationId}/stream`).
- **What Changes When Something Changes?**: 3D conduit thicknesses, particle velocities, equipment LEDs, and inspector telemetry respond dynamically to physics updates.
- **What Can the User Inspect?**: Click any building, generator, solar rack, wind turbine, battery bank, or load group to view comprehensive technical details and provenance.
- **What Belongs on This Page?**: Spatial 3D model, circuit power flow, live operating mode controls, asset inspector, and reference comparison.
- **What Was Moved to Secondary Detail?**: Raw JSON payloads and extensive historical calibration logs moved to collapsible inspector sub-drawers.

---

## Route 3: Forecast (`/forecast` — `ForecastView.tsx`)
- **What is this page?**: Predictive meteorological and microgrid load/generation horizon explorer.
- **Main Visual**: Interactive multi-horizon ensemble forecast chart with $P_{10}/P_{50}/P_{90}$ uncertainty confidence bands across 48 hours.
- **Primary User Action**: Adjusting the forecast horizon slider (1h to 48h) and evaluating predicted weather drivers (wind speed, solar irradiance, temperature).
- **Data Shown**: Hourly load forecast (kW), solar PV generation potential (kW), wind turbine potential (kW), ambient temperature trajectory (°C).
- **Where Does It Come From?**: Phase 3 neural & XGBoost ensemble models loaded from `models/registry/`.
- **What Changes When Something Changes?**: Forecast horizon updates dynamically calculate expected reserve margins and predicted fuel burn.
- **What Can the User Inspect?**: Model details drawer with calibration metrics (MAE, RMSE, Pinball Loss) and sensor input weights.
- **What Belongs on This Page?**: Multi-horizon trajectory charts, weather timeline, and confidence interval spreads.
- **What Was Moved to Secondary Detail?**: Deep neural network architecture diagrams and training loss logs moved to expandable Model Details drawer.

---

## Route 4: Scenarios (`/scenarios` — `ScenariosView.tsx`)
- **What is this page?**: The polar stress scenario laboratory and contingency simulator.
- **Main Visual**: Scenario workspace cards detailing environmental, compound, and equipment failure stresses with BEFORE vs AFTER delta cards.
- **Primary User Action**: Selecting and injecting stress scenarios (`Blizzard`, `High Wind`, `Extreme Cold`, `Generator Trip`, `Battery Degradation`) into the live engine.
- **Data Shown**: Perturbation parameters, affected subsystems, delta kW in load/generation, reserve margin shift, resilience delta.
- **Where Does It Come From?**: Phase 5 `ScenarioRegistry` and `ScenarioEngine` via `POST /api/v1/twin/scenario/apply`.
- **What Changes When Something Changes?**: Applying a scenario immediately propagates through the live simulation session, updating the 3D twin and triggering alert ribbons.
- **What Can the User Inspect?**: Mathematical transformation rationale, parameter perturbation values, and historical scenario test results.
- **What Belongs on This Page?**: 14-scenario grid, before/after delta comparisons, and reset baseline controls.
- **What Was Moved to Secondary Detail?**: Low-level YAML transform matrices moved to technical documentation.

---

## Route 5: Dispatch (`/optimization` — `OptimizationView.tsx`)
- **What is this page?**: Autonomous MILP microgrid dispatch optimizer and scheduling console.
- **Main Visual**: 24-hour optimal source scheduling timeline showing stacked generation dispatch (Solar, Wind, Battery, Diesel) meeting demand.
- **Primary User Action**: Comparing solver modes (EXPECTED vs CONSERVATIVE vs SCENARIO_ROBUST) and approving autonomous recommendations.
- **Data Shown**: Hourly dispatch setpoints (kW), generator start/stop schedule, battery state-of-charge trajectory, fuel savings percentage.
- **Where Does It Come From?**: Phase 6 MILP mathematical optimization engine via `POST /api/v1/optimizer/solve`.
- **What Changes When Something Changes?**: Solver mode toggles recalculate spinning reserve allocations and diesel run hours.
- **What Can the User Inspect?**: Detailed constraint formulation (energy balance, generator ramp rates, battery C-rates, min downtime).
- **What Belongs on This Page?**: Dispatch horizon chart, source allocation schedule, and operator approval controls.
- **What Was Moved to Secondary Detail?**: Raw solver branch-and-bound iteration logs moved to solver diagnostics drawer.

---

## Route 6: Resilience (`/resilience` — `ResilienceView.tsx`)
- **What is this page?**: Polar station survivability and contingency assessment console.
- **Main Visual**: Composite resilience score card and weakest-link bottleneck visualizer identifying the primary system constraint.
- **Primary User Action**: Inspecting multidimensional stress vectors (Thermal, Fuel, Generation, Storage, Logistics) to identify vulnerabilities.
- **Data Shown**: Autonomous mission survival days, critical load coverage margin, reserve headroom, thermal envelope loss rate.
- **Where Does It Come From?**: Phase 7 `ResilienceEngine` evaluating live simulation telemetry against safety thresholds.
- **What Changes When Something Changes?**: Ambient temperature drops or fuel delays immediately reduce the corresponding resilience sub-metric and flag bottlenecks.
- **What Can the User Inspect?**: 9-dimensional spider/radar breakdown and threshold breach alerts.
- **What Belongs on This Page?**: Resilience health score, weakest link indicator, and survival horizon calculations.
- **What Was Moved to Secondary Detail?**: Raw sensor historical telemetry moved to evidence drawer.

---

## Route 7: Assets (`/edge` — `EdgeView.tsx`)
- **What is this page?**: Comprehensive station asset explorer and equipment health register.
- **Main Visual**: Categorized equipment inventory grid (Generation, Storage, Distribution, Critical Loads) with live power meters and health indicators.
- **Primary User Action**: Filtering by category or importance and clicking equipment cards to focus them in the 3D Digital Twin.
- **Data Shown**: Equipment name, circuit ID, nominal rating (kW), real-time load (kW), health status (HEALTHY / DEGRADED / FAULT), maintenance interval.
- **Where Does It Come From?**: Station profile hardware registry and live simulation device state.
- **What Changes When Something Changes?**: Breaker trips or equipment derating updates health badges and flags affected circuits.
- **What Can the User Inspect?**: Individual device operating history and electrical nameplate ratings.
- **What Belongs on This Page?**: Asset cards, category filters, and quick link to 3D Twin.
- **What Was Moved to Secondary Detail?**: Maintenance schedule forms and spare parts inventory moved to on-demand drawers.

---

## Route 8: Decisions (`/trace` — `DecisionTraceView.tsx`)
- **What is this page?**: The authoritative, tamper-evident audit log explaining "Why did the system take this decision?"
- **Main Visual**: Chronological decision timeline with color-coded pipeline stages (FORECAST $\rightarrow$ SCENARIO $\rightarrow$ OPTIMIZER $\rightarrow$ TWIN $\rightarrow$ POLICY).
- **Primary User Action**: Clicking any trace event to open the comprehensive decision evidence drawer with mathematical proofs and reasoning chains.
- **Data Shown**: Trace ID, timestamp, trigger event, optimizer rationale, policy rule citations, before/after operational state deltas.
- **Where Does It Come From?**: Phase 9 `TraceEngine` and `TraceExplainer` logging every computational event.
- **What Changes When Something Changes?**: Every manual operator action, scenario injection, or autonomous dispatch generates a fresh cryptographic trace entry.
- **What Can the User Inspect?**: Complete input vectors, optimization formulation, policy rule triggers, and human-readable natural language explanations.
- **What Belongs on This Page?**: Decision timeline, filterable event log, and evidence drawer.
- **What Was Moved to Secondary Detail?**: Raw SHA-256 hashes and low-level AST execution trees moved to expandable technical tabs.

---

## Route 9: Validation (`/validation` — `ValidationView.tsx`)
- **What is this page?**: Empirical scientific and engineering validation benchmark dashboard.
- **Main Visual**: System-wide model validation scorecard covering forecast accuracy, uncertainty calibration, optimization quality, and twin reproducibility.
- **Primary User Action**: Reviewing validation metrics against target thresholds (MAE, pinball loss, energy conservation invariant).
- **Data Shown**: 3-year historical dataset validation metrics, benchmark comparisons, energy conservation error ($\Delta < 0.01\%$).
- **Where Does It Come From?**: Phase 10 validation benchmarks and automated pytest test suites.
- **What Changes When Something Changes?**: Station switching loads station-specific validation scores for Bharati, Maitri, and Himadri.
- **What Can the User Inspect?**: Deep calibration plots and statistical error distribution histograms.
- **What Belongs on This Page?**: High-level validation scorecards and scientific verification summaries.
- **What Was Moved to Secondary Detail?**: Raw CSV metric dumps and test logs moved to on-demand technical drawers.

---

## Route 10: Policy Rules (`/policy` — `PolicyView.tsx`)
- **What is this page?**: Authoritative operational policy and safety governance console.
- **Main Visual**: Active policy status banner with tiered priority hierarchy (Life Support > Comms > Habitation > Science > Workshop).
- **Primary User Action**: Inspecting active operating rules, load shedding thresholds, and safety envelopes.
- **Data Shown**: Active rule count, critical safety constraints, diesel minimum runtime rules, cold soak prevention triggers.
- **Where Does It Come From?**: Phase 8 `PolicyEngine` and `SafetyThresholdRegistry`.
- **What Changes When Something Changes?**: Operational disturbances trigger automated safety policies, visibly highlighting active rules in amber/red.
- **What Can the User Inspect?**: Rule mathematical definitions, trigger conditions, action setpoints, and priority overrides.
- **What Belongs on This Page?**: Safety hierarchy, active policy rules, and operational constraint definitions.
- **What Was Moved to Secondary Detail?**: Advanced rule configuration editor moved to authorized engineering drawers.

---

## Route 11: Field / HIL (`/field_hil` — `FieldHILValidationView.tsx`)
- **What is this page?**: Hardware-in-the-Loop and real-time simulator interface topology console.
- **Main Visual**: Architectural field communication topology diagram clearly displaying the physical air-gap boundary (`PHYSICAL SCADA = DISCONNECTED`).
- **Primary User Action**: Evaluating simulated HIL device loopback interfaces and communication health.
- **Data Shown**: Protocol status (Modbus TCP / DNP3 / IEC 61850 simulated links), telemetry packet rate, loopback latency.
- **Where Does It Come From?**: Phase 11 HIL adapter and edge communication simulator.
- **What Changes When Something Changes?**: Communication stress tests show simulated packet loss and interface degradations.
- **What Can the User Inspect?**: Protocol message framing, simulated register maps, and boundary declarations.
- **What Belongs on This Page?**: Interface topology, communication status, and epistemic boundary notices.
- **What Was Moved to Secondary Detail?**: Raw hex packet dumps moved to technical debug drawer.

---

## Route 12: Design Lab (`/design_lab` — `DesignLabView.tsx`)
- **What is this page?**: Architectural component and design system reference sandbox.
- **Main Visual**: Polaris visual token and UI component catalog showcasing typography, color scales, gauges, buttons, and alert ribbons.
- **Primary User Action**: Verifying global visual consistency and design token harmonization across the product.
- **Data Shown**: Active color palette, font scales, icon library, elevation shadows, state badges.
- **Where Does It Come From?**: Polaris Design System tokens in `tailwind.config.js` and `index.css`.
- **What Changes When Something Changes?**: Interactive component toggles demonstrate hover, active, disabled, and error states.
- **What Can the User Inspect?**: CSS class definitions and component accessibility attributes.
- **What Belongs on This Page?**: Design tokens, UI atoms, molecules, and layout specifications.
- **What Was Moved to Secondary Detail?**: Internal developer notes kept in documentation.
