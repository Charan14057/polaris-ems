# POLARIS-EMS — 60-SECOND PRODUCT DEMONSTRATION & PRESENTATION GUIDE
**Prompt ID**: 61853 / Phase 18 Final Launch Quality Gate  
**Presenter Objective**: Demonstrate an operational, connected, and physically believable polar microgrid digital twin in under 60-90 seconds.

---

## The 60-Second Product Narrative

1. **This is the station.** (Bharati Antarctic Research Station, Larsemann Hills).
2. **This is its current energy state.** (Live simulation session streaming in real-time).
3. **These are the sources.** (Solar PV, Katabatic wind turbines, Battery BESS, and Diesel backup).
4. **This is where power is going.** (Topologically flowing through the 400V AC main switchboard into station feeders).
5. **This is what matters most.** (Life Support and Satellite Communications are protected by priority 1 policies).
6. **This is what the weather predicts.** (48-hour neural ensemble forecast warns of approaching blizzard conditions).
7. **This is what happens under stress.** (Applying a Blizzard scenario reduces solar to zero, trips high wind, and drops temperature).
8. **This is what the system recommends.** (Phase 6 MILP optimizer recommends starting DG-1 and pre-charging BESS).
9. **This is what happens when the operator approves.** (Approved setpoints immediately apply to the live simulation session).
10. **This is the resulting system state.** (3D Twin reflects the new diesel generation stream, battery charges, and balance is restored).
11. **This is the trace proving what happened.** (Cryptographic decision trace explains the mathematical rationale and policy authorization).

---

## Step-by-Step Clean Demonstration Script

### STEP 1: Launch & Overview
- Navigate to http://127.0.0.1:3000/.
- Overview loads cleanly. Point out the live telemetry metrics (Total Demand, Generation, BESS SOC, and Fuel Days).
- Highlight that every number originates from the authoritative backend simulation session, not client-side timers.

### STEP 2: Open Energy Twin
- Click **Energy** on the sidebar.
- Observe the recognizable architectural model of Bharati Station:
  - Aerodynamic white hull envelope with orange expedition identification stripe.
  - 24 heavy-duty structural steel stilts with diagonal cross-braces mounted on bedrock.
  - Tilted solar PV racks, rotating wind turbines, bulk fuel storage farm, and shoreline seawater intake pipeline.
  - Natural polar terrain (undulating snow and bedrock knolls with soft polar daylight shadows).

### STEP 3: Verify Live Simulation Session
- Point to the green LIVE SIMULATION badge in the summary strip.
- Show that the simulation timestamp is continuously advancing tick-by-tick based on actual wall-clock execution.
- Show Server-Sent Events (SSE) updates arriving at 1000ms intervals.

### STEP 4: Inspect Key Equipment
- Click the **Solar Array** in the 3D scene: Inspector opens showing current kW generation and SIMULATED provenance.
- Click the **Battery Bank (BESS)**: Observe live SOC percentage and bidirectional charge/discharge power.
- Click **Life Support & HVAC**: Observe nominal power rating and priority rank 1 protection.

### STEP 5: Trace Upstream Power Lineage
- With Life Support selected, click **TRACE POWER**.
- The 3D canvas immediately dims unrelated circuits and illuminates the exact upstream circuit lineage:
  [Solar / Wind / Diesel] -> [Main 400V AC Switchboard] -> [DB-1 Utilities Feeder] -> [Life Support]
- The Inspector displays the exact percentage contribution of each active power source.

### STEP 6: Weather & Expected Mode
- Click the **Weather Influence** card: Distinguish between **CURRENT** environment conditions and **+6H / +12H / +24H** predicted trends.
- Switch viewing mode to **EXPECTED**: Observe predicted renewable potential across the forecast horizon.

### STEP 7: Apply a Polar Stress Scenario
- Switch mode to **IMPACT** or navigate to **Scenarios** and select **BLIZZARD**.
- Click **Execute Scenario**:
  - Solar generation drops to 0.0 kW (dense cloud whiteout).
  - Ambient temperature plunges by 10°C, increasing building thermal loss.
  - The entire system responds: Net generation deficit triggers battery discharge and flags DG-1 auto-start requirement.
  - The 3D Twin reflects the storm: Fault indicators pulse on affected systems.

### STEP 8: Trace Downstream Impact
- In the 3D Twin or Inspector, click **TRACE IMPACT** on the Primary Diesel Generator.
- The system traverses the electrical topology and displays:
  - Downstream affected load kW.
  - Battery capacity remaining to cover the deficit.
  - Policy recommendations to prevent blackout.

### STEP 9: Test Manual Operator Action
- Open the **Manual Control** drawer.
- Select **Simulate Start DG-1** at 60.0 kW.
- Click **Simulate Action**:
  - The request is validated by the backend safety engine.
  - Diesel generation turns on, the generator LED turns emerald green, and an amber diesel power flow conduit appears in 3D.
  - Surplus generation flows into the battery storage bank.

### STEP 10: Test Autonomous Optimization (Auto Mode)
- Switch to **AUTO** mode.
- The system evaluates the Phase 6 MILP optimizer against the active scenario and current state.
- A recommendation card appears with explicit mathematical rationale:
  - Optimal dispatch setpoints for Solar, Wind, Battery, and Diesel.
  - Expected fuel savings and guaranteed spinning reserve margin.
- Click **Approve & Execute Setpoints**:
  - The backend immediately updates simulation setpoints.
  - The 3D Twin and power flow conduits adjust to match the approved schedule.

### STEP 11: Switch Stations (Maitri & Himadri)
- Select **MAITRI** from the top bar:
  - The entire 3D scene transforms to the Schirmacher Oasis rocky permafrost terrain.
  - The iconic central heated spine corridor, modular living blocks, separate powerhouse with exhaust stacks, and Lake Priyadarshini water pump house render cleanly.
  - Telemetry and live session re-sync to Maitri specs.
- Select **HIMADRI** from the top bar:
  - Scene transforms to Ny-Alesund Arctic coastal tundra.
  - The classic two-storey Nordic red timber station with pitched gable roof, tundra boardwalk, and settlement district energy tie-in renders cleanly.

### STEP 12: Reference vs Digital Twin Comparison
- In the 3D toolbar, click **REFERENCE <-> TWIN**.
- The comparison modal opens showing the official NCPOR architectural survey elevation blueprint beside the live 3D reconstruction.
- Drag the **Wipe Slider** across the screen (0% to 100%) to demonstrate architectural fidelity.
- Point out the honest epistemic disclaimer: REFERENCE IMAGE ASSET REQUIRED ensures complete factual transparency.

### STEP 13: Presentation / Demo Mode
- Click the **DEMO MODE** button in the header.
- Secondary technical panels collapse cleanly, presenting an expansive, clutter-free 3D digital twin presentation stage ready for high-level executive demonstrations.
