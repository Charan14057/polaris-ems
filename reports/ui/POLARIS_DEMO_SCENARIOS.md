# POLARIS-EMS — OPERATIONAL DEMONSTRATION SCENARIOS RUNBOOK
**Version:** 1.0.0-phase18  
**Scope:** 13 Deterministic Operational Demonstrations for Evaluators and Product Owners  
**Safety Mandate:** Zero Fabricated Evidence • Simulation Air-Gap Explicitly Declared  

---

## 1. Overview & Presenter Rules of Engagement

Every demonstration must respect the strict **Epistemic Boundary**:
1. **Always State:** "This simulation demonstrates Polaris-EMS computational optimization, physical energy balancing, and spatial microgrid visualization under validated polar environmental conditions."
2. **Never Claim:** "This is live SCADA telemetry from Antarctica" or "We are remotely turning on physical diesel generators in Antarctica right now."
3. **Hardware Boundary:** Physical telemetry link is air-gapped (`PHYSICAL_CONNECTIVITY = DISCONNECTED`).

---

## 2. The 13 Deterministic Demonstration Scenarios

### DEMO 1: Normal Nominal Operating Station
- **Station:** BHARATI (Larsemann Hills, East Antarctica)
- **Starting State:** Nominal summer conditions, ambient -18°C, wind 11 m/s, GHI 210 W/m², battery SoC 85%.
- **Scenario:** Baseline 24h expected trajectory.
- **User Action:** Navigate to **Energy Twin**, inspect top-level vitals strip, initiate simulation playback at 2x.
- **Expected Visible Change:** Smooth forward animation of simulation time; gentle power flow pulsing from wind turbines and solar array to main 400V bus.
- **Expected Power-Flow Change:** Clean balanced flow from renewable sources feeding critical habitation and science loads. Zero flow on diesel feeders.
- **Expected Source-Mix Change:** Renewable share > 75%, battery floating near neutral balance (-2 kW to +3 kW).
- **Expected Battery/Fuel Effect:** Fuel burn = 0.0 L/h; battery stays healthy between 80% and 85%.
- **Expected Resilience Effect:** Resilience index stays green (88/100 nominal).
- **Expected Policy Result:** P1–P8 fully satisfied with zero active violations.
- **Expected Trace Result:** Routine periodic baseline checkpoint logged in Decision Trace.
- **What Presenter Should Say:** "Under nominal summer conditions at Bharati, renewable generation covers base load, keeping diesel generators in cold standby and preserving scarce arctic fuel."
- **What Must NOT Be Claimed:** Do not claim that solar generation continues through the polar night (June–August at Bharati has negligible sun).

---

### DEMO 2: Diesel Contribution Rising
- **Station:** MAITRI (Schirmacher Oasis, Queen Maud Land)
- **Starting State:** Calm dusk, wind drops from 12 m/s to 3 m/s, solar drops to 0 W/m².
- **Scenario:** Evening renewable deficit surge.
- **User Action:** Scrub timeline to T+18:00 or select 48h horizon.
- **Expected Visible Change:** Diesel generator icon lights up amber; diesel supply bar expands in the Source Mix.
- **Expected Power-Flow Change:** Flow pulses along amber diesel feeder circuit into Main Bus A; battery discharge buffer moderates ramp rate.
- **Expected Source-Mix Change:** Diesel output increases from 0 kW to 38 kW; renewable share drops below 15%.
- **Expected Battery/Fuel Effect:** Fuel consumption rate climbs to 9.8 L/h; battery discharge limited to policy safety floor.
- **Expected Resilience Effect:** Fuel Security dimension in Resilience radar reflects consumption drawdown.
- **Expected Policy Result:** Policy rule P3 (minimum diesel runtime 60 minutes) enforced to prevent thermal cycling.
- **Expected Trace Result:** Immutable trace logs `DISPATCH_COMMITTED` for DG1 with solver confidence 0.98.
- **What Presenter Should Say:** "When wind drops below cut-in speed, the system coordinates diesel start-up without exceeding engine ramp rate constraints."
- **What Must NOT Be Claimed:** Do not claim diesel starts instantaneously without warm-up latency.

---

### DEMO 3: Battery Reserve Depletion & Low SoC Defense
- **Station:** HIMADRI (Ny-Ålesund, Svalbard, Arctic)
- **Starting State:** High scientific heating demand, battery discharging steadily.
- **Scenario:** Battery State of Charge approaches 30% safety floor.
- **User Action:** Advance timeline to battery depletion point; observe inspector drawer on Battery Asset.
- **Expected Visible Change:** Battery SoC bar transitions from emerald to warning amber; alert badge appears.
- **Expected Power-Flow Change:** Battery discharge flow throttles back; grid/external supply increases to balance bus.
- **Expected Source-Mix Change:** Battery contribution drops from 12 kW to 0 kW; primary source takes over load.
- **Expected Battery/Fuel Effect:** Battery SoC is halted precisely at the 25% deep-discharge protection floor.
- **Expected Resilience Effect:** Autonomy dimension drops, triggering cold-reserve advisory.
- **Expected Policy Result:** Policy rule P2 (`BATTERY_MIN_SOC_25`) actively prevents further discharge.
- **Expected Trace Result:** `POLICY_INTERVENTION` event registered in Decision Trace.
- **What Presenter Should Say:** "Polaris-EMS enforces hard mathematical boundaries. The battery will never be allowed to drain into deep degradation, preserving cell life in sub-zero ambient."
- **What Must NOT Be Claimed:** Do not claim the battery can charge faster than chemical C-rate limits in cold environments.

---

### DEMO 4: Low Solar & Overcast Blizzard Cloud Cover
- **Station:** BHARATI
- **Starting State:** Midday 12:00 UTC, expected solar peak 35 kW.
- **Scenario:** Injected dense cloud bank and blowing snow (GHI drops by 85%).
- **User Action:** Select "Low Solar" forecast condition or toggle weather disturbance in timeline.
- **Expected Visible Change:** Solar generation card drops from 35 kW to 4.2 kW.
- **Expected Power-Flow Change:** Solar flow line thins; battery discharge automatically compensates without grid voltage sag.
- **Expected Source-Mix Change:** Solar contribution shrinks; battery and wind expand to fill the generation gap.
- **Expected Battery/Fuel Effect:** Battery discharges at 18 kW; fuel burn remains zero if wind is sufficient.
- **Expected Resilience Effect:** Reserve margin contracts moderately.
- **Expected Policy Result:** Renewable priority policy holds.
- **Expected Trace Result:** Dispatch re-optimization logged within 42ms.
- **What Presenter Should Say:** "Our physics-informed solar model accounts for albedo and blizzard attenuation, instantly re-dispatching battery storage."
- **What Must NOT Be Claimed:** Do not claim solar can generate power covered in 2 meters of hard snow drifts.

---

### DEMO 5: High Wind Storm & Aerodynamic Cut-Out
- **Station:** MAITRI
- **Starting State:** Blizzard gale winds ramping from 15 m/s to 28 m/s.
- **Scenario:** Severe katabatic storm surpassing turbine cut-out threshold (25 m/s).
- **User Action:** Trigger blizzard scenario or fast-forward to storm peak.
- **Expected Visible Change:** Wind turbine status changes from ONLINE to CUT_OUT (feathered blades); wind bar collapses.
- **Expected Power-Flow Change:** Wind feeder flow abruptly ceases; diesel generator rapidly picks up base load.
- **Expected Source-Mix Change:** Wind 45 kW -> 0 kW; Diesel 0 kW -> 52 kW.
- **Expected Battery/Fuel Effect:** Battery absorbs transient shock during the 90-second diesel spin-up.
- **Expected Resilience Effect:** Asset Redundancy and Recovery Time dimensions flagged in resilience radar.
- **Expected Policy Result:** Aerodynamic safety lockout strictly honored.
- **Expected Trace Result:** `ASSET_PROTECTION_EVENT` logged with turbine aerodynamic telemetry.
- **What Presenter Should Say:** "To prevent catastrophic mechanical rotor failure in polar katabatic gales, Polaris-EMS safely shuts down turbines at 25 m/s while smoothly transitioning to thermal generators."
- **What Must NOT Be Claimed:** Do not claim wind turbines generate unlimited power at 40 m/s gale forces.

---

### DEMO 6: Primary Diesel Generator Sudden Trip
- **Station:** HIMADRI
- **Starting State:** Operating on DG1 base load (40 kW).
- **Scenario:** Sudden mechanical trip / fuel injector failure on DG1.
- **User Action:** Click DG1 node on canvas -> click "Simulate Trip" in inspector.
- **Expected Visible Change:** DG1 node turns red with FAULT badge; sound/visual fault pulse along feeder.
- **Expected Power-Flow Change:** Instantaneous flow transfer: Battery inverts from standby to emergency discharge (40 kW) in < 16ms.
- **Expected Source-Mix Change:** Battery covers 100% of critical load while backup DG2 is signaled to start.
- **Expected Battery/Fuel Effect:** Battery SoC drops rapidly; DG2 begins cold-start cranking sequence.
- **Expected Resilience Effect:** Deficit Tolerance dimension drops from 95 to 60.
- **Expected Policy Result:** P1 (`LIFE_SUPPORT_ZERO_SHED`) strictly maintained—no habitat blackout.
- **Expected Trace Result:** `CRITICAL_FAULT_MITIGATION` trace committed to immutable ledger.
- **What Presenter Should Say:** "When a primary generator trips at -40°C, human survival depends on automated response. Polaris-EMS uses battery storage as an instantaneous bridging asset."
- **What Must NOT Be Claimed:** Do not claim physical backup generators start in zero seconds without pre-heating.

---

### DEMO 7: Extreme Arctic Deep Freeze (-48°C)
- **Station:** BHARATI
- **Starting State:** Ambient temperature plunges from -22°C to -48°C during polar storm.
- **Scenario:** Massive spike in habitat life-support and pipe trace-heating electrical demand.
- **User Action:** Select 48h horizon under winter polar night scenario.
- **Expected Visible Change:** Total demand climbs from 42 kW to 68 kW; Life Support group expands in load breakdown.
- **Expected Power-Flow Change:** Thickened flow conduits to Habitation and Life Support modules.
- **Expected Source-Mix Change:** Dual generator operation committed by HiGHS MILP solver.
- **Expected Battery/Fuel Effect:** Fuel consumption increases; battery capacity de-rated by thermal temperature coefficient.
- **Expected Resilience Effect:** Thermal Buffer dimension highlighted with active vigilance.
- **Expected Policy Result:** Non-critical science labs (LIDAR, clean lab) flagged as deferrable candidates.
- **Expected Trace Result:** Optimization solves with augmented thermal load constraints.
- **What Presenter Should Say:** "Sub-zero cold does not just increase heating load—it also de-rates battery electrochemical capacity. Our twin couples thermal dynamics directly to electrical dispatch."
- **What Must NOT Be Claimed:** Do not claim batteries operate at full nominal capacity in unheated outdoor enclosures.

---

### DEMO 8: Multi-Shock Combined Stress Test
- **Station:** MAITRI
- **Starting State:** Mid-winter polar night, -35°C ambient.
- **Scenario:** Katabatic storm + DG1 lockout + Battery capacity constrained to 40%.
- **User Action:** Run Scenario SCEN-08 ("Combined Extreme Shocks") from the Scenarios view.
- **Expected Visible Change:** Station condition badge updates to `STRESSED`; multi-colored warnings across canvas.
- **Expected Power-Flow Change:** Controlled load shedding: workshop and auxiliary science circuits dim to zero flow.
- **Expected Source-Mix Change:** All available generation directed solely to P1 Critical Life Support circuits.
- **Expected Battery/Fuel Effect:** Fuel preserved for life-support boiler pumps; zero unserved critical energy.
- **Expected Resilience Effect:** Composite Resilience Index drops to 48/100 (`VULNERABLE`).
- **Expected Policy Result:** Policy priority hierarchy P1 > P2 > P3 > P4 strictly observed.
- **Expected Trace Result:** Full multi-asset constraint satisfaction proof recorded.
- **What Presenter Should Say:** "Under multiple compounding failures, Polaris-EMS gracefully sheds non-essential research equipment to ensure habitat survival."
- **What Must NOT Be Claimed:** Do not claim the station can operate indefinitely with zero fuel and no generation.

---

### DEMO 9: Manual Operator Simulation Override
- **Station:** BHARATI
- **Starting State:** Automatic dispatch running.
- **Scenario:** Operator manually requests early battery charging ahead of forecasted storm.
- **User Action:** Toggle **Operating Mode** to `MANUAL` -> select Battery -> click "Force Charge (15 kW)" -> click "Simulate Action".
- **Expected Visible Change:** Confirmation drawer displays exact impacts: "Fuel burn +3.2 L/h, Reserve +18% at T+4h" -> visual flow redirects to battery.
- **Expected Power-Flow Change:** Flow from diesel increases to feed both station loads and battery charger bus.
- **Expected Source-Mix Change:** Generation exceeds load by exactly 15 kW (charging power).
- **Expected Battery/Fuel Effect:** Battery SoC slope increases positively; diesel runtime extended.
- **Expected Resilience Effect:** Autonomy metric improves for future storm horizon.
- **Expected Policy Result:** Policy check approves action with `OPERATOR_OVERRIDE` flag.
- **Expected Trace Result:** Trace records user ID, action timestamp, and expected vs actual trajectory delta.
- **What Presenter Should Say:** "Operators retain full agency. When manual simulation mode is selected, every intended action is pre-checked for safety and fuel impact before confirmation."
- **What Must NOT Be Claimed:** Do not claim the simulation action flipped a physical switch in Antarctica.

---

### DEMO 10: AUTO Mode Autonomous Recommendation
- **Station:** HIMADRI
- **Starting State:** Operating with inefficient diesel spinning reserve.
- **Scenario:** Automatic optimization identifies 18% fuel saving opportunity.
- **User Action:** Toggle **Operating Mode** to `AUTO` -> observe "Recommended Action" banner.
- **Expected Visible Change:** Banner displays: "RECOMMENDED ACTION: Shut down DG2 and shift 8 kW to Battery Buffer".
- **Expected Power-Flow Change:** Projected flow diagram previews cleaner single-generator + battery flow.
- **Expected Source-Mix Change:** Projected fuel savings: 4.1 L/h; generator loading optimized to 82% sweet spot.
- **Expected Battery/Fuel Effect:** Estimated 98 L fuel saved over 24h horizon.
- **Expected Resilience Effect:** Resilience score maintained within 1.5% of baseline.
- **Expected Policy Result:** All safety margins (minimum reserve, thermal constraints) verified by policy engine.
- **Expected Trace Result:** Recommendation trace hashed and staged awaiting operator approval.
- **What Presenter Should Say:** "In AUTO mode, Polaris-EMS continuously explores the MILP solution space, surfacing high-confidence, safety-verified recommendations to the operator."
- **What Must NOT Be Claimed:** Do not claim the system physically executed the shutdown without operator authorization.

---

### DEMO 11: Weather Forecast Shift Drives Forward Dispatch
- **Station:** BHARATI
- **Starting State:** Current weather calm, but 12-hour forecast detects incoming front.
- **Scenario:** Forecast updates wind speed from 5 m/s to 18 m/s at T+08:00.
- **User Action:** Click "Next 12 Hours" weather panel in Energy Twin; scrub timeline forward to T+08:00.
- **Expected Visible Change:** Generation forecast chart updates with higher wind potential; Twin shows wind turbine pre-spinning.
- **Expected Power-Flow Change:** Projected flow shifts from diesel reliance to planned wind capture.
- **Expected Source-Mix Change:** Expected renewable share increases from 25% to 85% at T+08:00.
- **Expected Battery/Fuel Effect:** System schedules battery pre-discharge now to create headroom for incoming wind power.
- **Expected Resilience Effect:** Autonomy expands over the 24h horizon.
- **Expected Policy Result:** Avoidable diesel start scheduled for T+06:00 is automatically cancelled.
- **Expected Trace Result:** Causal forecast inference trace linked to optimizer schedule update.
- **What Presenter Should Say:** "Polaris-EMS does not just react to current weather. Our Phase 3 conformal forecast feeds directly into the Phase 6 MILP solver, anticipating renewable surges hours in advance."
- **What Must NOT Be Claimed:** Do not claim the weather forecast has 100% zero-error certainty (conformal bands show P10–P90 spread).

---

### DEMO 12: Trace Power Circuit Lineage
- **Station:** BHARATI
- **Starting State:** Energy Twin canvas open.
- **Scenario:** Operator wants to verify which generators are currently keeping the Life Support system warm.
- **User Action:** Click "Life Support HVAC" node -> click "Trace Power" button.
- **Expected Visible Change:** Unrelated circuits, science labs, and lighting dim by 75%; complete power lineage highlights in brilliant high-contrast sky blue.
- **Expected Power-Flow Change:** Visual path illuminates: Source (Wind Turbine + Battery) -> Main 400V Switchboard -> Feeder F1 -> Sub-DB Habitation -> HVAC Node.
- **Expected Source-Mix Change:** Inspector displays exact source contribution: "Wind: 68%, Battery: 32%, Diesel: 0%".
- **Expected Battery/Fuel Effect:** Readout shows exact kW draw (14.2 kW).
- **Expected Resilience Effect:** Confirms redundancy on primary life-support bus.
- **Expected Policy Result:** P1 circuit protection verified.
- **Expected Trace Result:** Circuit connectivity graph queried from station spatial topology.
- **What Presenter Should Say:** "Trace Power provides instant spatial transparency. An operator can point at any critical room and immediately trace the electrical conduit back to the exact supplying generators."
- **What Must NOT Be Claimed:** Do not claim this requires invasive physical wire tracing sensors (it is derived from validated topological circuit schematics).

---

### DEMO 13: Trace Impact Disturbance Propagation
- **Station:** MAITRI
- **Starting State:** Energy Twin canvas open.
- **Scenario:** Operator wants to evaluate what happens if Main Feeder 2 trips.
- **User Action:** Select Feeder F2 -> click "Trace Impact" button.
- **Expected Visible Change:** Feeder flashes amber; all downstream connected equipment and rooms highlight with projected impact badges.
- **Expected Power-Flow Change:** Downstream flow lines to Workshop and Snowmelt plant drop to zero.
- **Expected Source-Mix Change:** Load reduction of 18.5 kW immediately reflected in total generation requirement.
- **Expected Battery/Fuel Effect:** Diesel throttle rolls back to avoid over-frequency.
- **Expected Resilience Effect:** Life Support remains unaffected on isolated Feeder F1 (zero life-support vulnerability).
- **Expected Policy Result:** Deferrable load shedding policy validated.
- **Expected Trace Result:** Impact assessment matrix generated in < 15ms.
- **What Presenter Should Say:** "Trace Impact lets operators ask 'What happens if this switch trips?' before touching a physical circuit breaker, protecting mission-critical life support."
- **What Must NOT Be Claimed:** Do not claim this is an irreversible physical breaker trip.

---

### DEMO 14: Real-Time Live Twin Session & Wall-Clock Progression
- **Station:** BHARATI
- **Starting State:** Default Energy Twin view in LIVE mode.
- **Scenario:** Stateful live simulation session running continuously in the backend.
- **User Action:** Observe the live timestamp advancing synchronous with wall-clock execution; toggle between LIVE and REPLAY.
- **Expected Visible Change:** Simulation clock advances in real-time; SSE event stream delivers fresh computational state deltas every 1.5 seconds.
- **Expected Power-Flow Change:** Flow beams pulse with dynamic kW loading; battery floats between charge and discharge.
- **Expected Source-Mix Change:** Reconciled continuously with actual `TwinState` conservation invariants.
- **Expected Policy Result:** Evaluated continuously under active baseline dispatch.
- **What Presenter Should Say:** "LIVE mode is not a precomputed trajectory playback or frontend timer. The backend owns a stateful LiveTwinSession whose simulation clock synchronizes with actual wall-clock execution."
- **What Must NOT Be Claimed:** Do not claim this is live satellite SCADA from Antarctica.

---

### DEMO 15: Real Architectural Reference Comparison & Executive Demo Mode
- **Station:** BHARATI / MAITRI / HIMADRI
- **Starting State:** 3D Spatial Digital Twin view open.
- **Scenario:** Executive presentation comparing physical base architectural references with the 3D computational model.
- **User Action:** Click "REFERENCE ↔ TWIN" in the 3D toolbar; click "DEMO MODE" in the top banner.
- **Expected Visible Change:** 
  1. The Reference comparison drawer opens displaying the verified station structural specifications (Bharati 24 stilts, Maitri central corridor, Himadri 2-storey Nordic frame) side-by-side with the 3D model.
  2. In Demo Mode, secondary configuration toolbars collapse, presenting an executive view focused on the 3D twin, directional energy flow, clean source mix, and automated advisory recommendation.
- **What Presenter Should Say:** "Here is our approved architectural reference alongside the 3D digital reconstruction. The computational state from our TwinEngine is projected directly onto the topological energy layer."
- **What Must NOT Be Claimed:** Do not claim the 3D geometry is an exact millimeter-surveyed BIM scan (it is explicitly classified as CONFIGURED / REPRESENTATIVE).

