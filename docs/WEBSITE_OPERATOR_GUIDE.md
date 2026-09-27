# POLARIS-EMS — WEBSITE OPERATOR GUIDE
**Product**: Polaris Polar Microgrid Energy Management System & Operational Digital Twin  
**Audience**: Station Microgrid Operators, Research Facility Engineers, and Mission Directors  
**System Status**: Computational Simulation • Air-Gap Safety Active (PHYSICAL SCADA = DISCONNECTED)

---

## 1. Introduction: What is Polaris EMS?

Polaris EMS is an autonomous energy management system and digital twin engine built for extreme polar environments (Antarctica and the High Arctic). It operates at three primary polar research facilities:
1. **Bharati Station** (Larsemann Hills, East Antarctica)
2. **Maitri Station** (Schirmacher Oasis, Queen Maud Land, Antarctica)
3. **Himadri Station** (Ny-Alesund, Svalbard, High Arctic)

In polar research stations, energy is literally life support. If power fails during a winter blizzard, indoor temperatures plunge to fatal sub-zero levels within hours. Polaris EMS continuously solves the mathematical puzzle of balancing intermittent renewables (solar and wind), battery storage (BESS), and diesel generators to guarantee that critical life support and communications never lose power, while minimizing expensive fuel burn.

---

## 2. Navigating the Product Section by Section

### Section 1: Top Application Bar
At the top of every screen, you will find:
- **Station Switcher**: Switch between Bharati, Maitri, and Himadri. Switching stations immediately reconfigures the entire physical model, 3D architecture, circuit topology, and weather profile.
- **Active Threat Alert**: If an equipment failure or severe storm threatens power balance, an amber or red alert banner appears, telling you what is happening and what action to take.
- **Provenance Badges**: Polaris strictly labels where every number comes from (SIMULATED, CONFIGURED, FORECAST). We never invent numbers for decoration.

---

### Section 2: Overview Page (/overview)
The Overview gives you an instant snapshot of station status:
- **Total Station Demand**: How much power the station is using right now (in kilowatts).
- **Total Generation & Source Mix**: Where the power is coming from (Solar, Wind, Battery, or Diesel).
- **Battery State of Charge (SOC)**: How full the battery storage bank is.
- **Fuel Stock Autonomy**: How many days of diesel fuel remain at the current burn rate.

---

### Section 3: Energy Digital Twin Page (/energy)
This is the flagship operational heart of Polaris EMS.
- **Realistic 3D Station Model**: You see an authentic 3D spatial reconstruction of the station:
  - **Bharati**: Elevated aerodynamic building on 24 heavy steel stilts with upper science observation deck, fuel farm, and seawater intake.
  - **Maitri**: Modular living blocks connected by the iconic central heated corridor spine, detached powerhouse, and Lake Priyadarshini water pump house.
  - **Himadri**: Two-storey Nordic timber research station with pitched gable roof and Arctic settlement district energy tie-in.
- **Live 3D Power Flow**: Colored energy conduits show power flowing from sources through the main switchboard into feeders and load blocks.
  - Solar flows in gold.
  - Wind flows in blue.
  - Diesel flows in amber.
  - Battery flows in emerald green. When charging, energy particles flow *into* the battery; when discharging, they flow *out* onto the AC bus.
- **Viewing Modes**:
  - **ARCH**: Focuses on the architectural building envelope and physical structure.
  - **ENERGY**: Turns the building semi-transparent so you can look inside and inspect electrical switchboards, panels, and live energy flow.
  - **IMPACT**: Highlights tripped breakers and shed loads in bold red or amber.
- **Reference <-> Twin Comparison**:
  - Click the **REFERENCE <-> TWIN** button to open the side-by-side comparison. You can view the authoritative architectural survey blueprint beside the live 3D digital model, with a draggable wipe slider or opacity fader.
- **Asset Inspection & Tracing**:
  - Click any equipment in the 3D scene to open the Inspector drawer.
  - Click **TRACE POWER** to see the exact circuit path delivering power to that device.
  - Click **TRACE IMPACT** to see what downstream equipment would lose power if that device failed.
- **Manual vs Auto Operation**:
  - **MANUAL**: Test starting/stopping diesel generators or forcing battery charging. All actions are validated by the backend before executing.
  - **AUTO**: Evaluates the Phase 6 MILP mathematical optimizer. Review the recommended dispatch setpoints and click **Approve** to execute them.

---

### Section 4: Forecast Page (/forecast)
Polar weather changes rapidly. The Forecast page shows 48-hour forward predictions:
- **Load Forecast**: Expected electrical demand for the next two days.
- **Solar & Wind Potential**: Predicted renewable energy available from sunlight and katabatic winds.
- **Uncertainty Bands**: Shaded areas show conservative (P10) to optimistic (P90) confidence intervals so you know how much spinning reserve is needed.

---

### Section 5: Scenarios Page (/scenarios)
Test how the station handles emergencies before they occur:
- Select from 14 stress scenarios such as **Blizzard**, **High Wind**, **Extreme Cold**, **Generator Trip**, or **Battery Degradation**.
- When you execute a scenario, the backend perturbs the physics, recalculates power balance, and pushes live updates to the 3D Twin.
- You can immediately review the **BEFORE vs AFTER** delta cards showing how load, renewables, battery, and fuel burn responded.

---

### Section 6: Dispatch Page (/optimization)
Shows the cost-optimal 24-hour dispatch schedule calculated by the Phase 6 mathematical solver:
- Tells you hour-by-hour which generators to run, when to charge or discharge the battery, and how much fuel will be saved.
- You can choose between **EXPECTED**, **CONSERVATIVE**, and **SCENARIO_ROBUST** solver strategies.

---

### Section 7: Resilience Page (/resilience)
Evaluates polar station survivability across multiple stress dimensions:
- Computes your **Composite Resilience Health Score** (0-100%).
- Identifies the **Weakest-Link Bottleneck** (e.g., fuel reserve horizon, thermal building heat loss, or storage capacity) so you can fix vulnerabilities before winter.

---

### Section 8: Assets Page (/edge)
A comprehensive equipment directory:
- Lists all generators, inverters, battery banks, pumps, and science instruments with live kW ratings and health status (HEALTHY, DEGRADED, FAULT).
- Clicking any equipment lets you instantly focus on it in the 3D Digital Twin.

---

### Section 9: Decisions Page (/trace)
Every automated action taken by Polaris EMS is permanently recorded in a cryptographic audit log:
- Explains **What** happened, **Why** the system made that decision, and **Which** policy rule authorized it.
- Click any entry to inspect the mathematical formulation and evidence.

---

### Section 10: Validation, Policy & Field/HIL Pages
- **Validation**: Scientific proofs verifying energy conservation ($\Delta < 0.01\%$) and model accuracy.
- **Policy**: The safety rulebook defining priorities (Life Support always comes first; non-critical science sheds first during a shortage).
- **Field / HIL**: Displays communication interface topology and confirms the physical safety air-gap (PHYSICAL SCADA = DISCONNECTED).
