# POLARIS-EMS — Digital Twin Causal Dependency Map
**SIH26061: Polar Energy Management & Resilience System**  
**Air-Gap Status:** `PHYSICAL_CONNECTIVITY = DISCONNECTED`  
**Authoritative Engine:** Phase 4 `TwinEngine` + Phase 5 `ScenarioEngine` + Phase 6 `OptimizerEngine` + Phase 8 `PolicyEngine`

---

## 1. System Causal Architecture: Full-Circle Closed Loop

Polaris-EMS Digital Twin is strictly causal and computational. Every visible metric, power flow path, 3D element, and decision trace reflects a verified downstream dependency chain:

```
INPUT / PERTURBATION
       │
       ▼
[Environmental Weather / Operational Schedule / Stress Scenario]
       │
       ▼
[Phase 3 ML Forecast / ForecastAdapter (TwinInputStep)]
       │
       ▼
[ThermalEngine & LoadEngine (Heating demand & Device prioritization)]
       │
       ▼
[SolarEngine & WindEngine (Renewable potential & Meteorological limits)]
       │
       ▼
[PowerBalanceEngine (Conservation of Energy: Sources == Sinks + Curtailment)]
       ├──▶ [BatteryEngine (Chemical charging/discharging, SOC, temperature derating)]
       ├──▶ [DieselFuelEngine (Mechanical generation, fuel burn L/h, resupply window)]
       └──▶ [Subload Serving (Critical, Important, Operational, Flexible)]
       │
       ▼
[ResilienceEngine (Reserve margin, Continuity horizon, Threat state)]
       │
       ▼
[PolicyEngine & SafetyThresholdRegistry (Constraint evaluation, Governance)]
       │
       ▼
[OptimizerEngine / Advisory Recommendation / Operator Action Dispatch]
       │
       ▼
[Stateful LiveTwinSession / Live Event Stream (SSE)]
       │
       ▼
[Frontend 3D Spatial Twin & Subsystem Inspectors (Trace Power & Trace Impact)]
```

---

## 2. Definitive Node Catalog & Causal Connections

### Node Definitions

| Node Name | Subsystem / Layer | Technical Owner | Physical Unit | Provenance |
|---|---|---|---|---|
| `Weather` | Boundary Environment | Ambient sensors / Synthetic generator | °C, m/s, W/m² | `SYNTHETIC` / `REAL` |
| `Forecast` | Prediction Engine | Phase 3 ML Models | Multi-horizon time series | `FORECAST` |
| `Solar` | Renewable Generation | Phase 4 `SolarEngine` | kW (DC/AC) | `SIMULATED` |
| `Wind` | Renewable Generation | Phase 4 `WindEngine` | kW (AC) | `SIMULATED` |
| `Diesel` | Backup Generation | Phase 4 `DieselFuelEngine` | kW (AC), L/h | `SIMULATED` |
| `Battery` | Electrochemical Storage | Phase 4 `BatteryEngine` | kWh, % SOC, kW charge/discharge | `SIMULATED` |
| `Fuel` | Logistics & Storage | Phase 4 `DieselFuelEngine` | Liters remaining, Days autonomy | `SIMULATED` |
| `Demand` | Total Electrical Load | Phase 4 `LoadEngine` | kW | `SIMULATED` |
| `Thermal` | Building Enclosure | Phase 4 `ThermalEngine` | °C indoor, kW heating loss | `SIMULATED` |
| `Loads` | Subload Prioritization | Phase 4 `LoadEngine` | kW per priority tier | `SIMULATED` |
| `Main Bus` | Central Switchgear | Topology Config (`415V AC`) | kW throughput | `SIMULATED` |
| `Feeders` | Distribution Branch | Spatial Layout Profile | kW line flow | `SIMULATED` |
| `Panels` | Zone Distribution Boards | Zone Sub-panels (DB-1 to DB-5) | kW zone power | `SIMULATED` |
| `Scenarios` | Stress Perturbation | Phase 5 `ScenarioRegistry` | Mathematical transforms | `CONFIGURED` |
| `Optimizer` | Optimal Dispatch | Phase 6 `OptimizerEngine` | Optimal setpoints | `SIMULATED` |
| `Resilience`| Continuity & Threat | Phase 7 `ResilienceEngine` | Hours continuity, Threat enum | `SIMULATED` |
| `Policy` | Safety Governance | Phase 8 `PolicyEngine` | Status (`ALLOW`, `WARN`, `SHED`) | `CONFIGURED` |
| `Operator` | Human-in-the-Loop | Manual Control Dispatch | Action ID (`dg1_start`, etc.) | `REAL` |
| `Trace` | Decision Audit | Phase 12 `DecisionTraceEngine` | Structured causal JSON | `SIMULATED` |
| `3D Twin` | Spatial Visualization | Three.js / Canvas 3D | Rendered spatial scene | `SIMULATED` |

---

### Comprehensive Edge Connection Matrix

| Source Node | Target Node | Trigger Event | Data Transferred | Calculation Owner | Visible Effect in Digital Twin |
|---|---|---|---|---|---|
| `Weather` | `Forecast` | Real-time sensor / wall-clock time tick | Temperature, Wind Speed, GHI | Phase 3 ML Model | Weather card updates; forecast trajectory curves recompute |
| `Forecast` | `Thermal` | Hourly horizon step | Ambient Temp ($T_{amb}$) | `ThermalEngine` | Heat loss rate changes; indoor temp responds; thermal demand curves adjust |
| `Thermal` | `Loads` | Thermal demand calculation | Heating required (kW) | `LoadEngine` | Total demand ($P_{load}$) increases or decreases; heating subload reflects delta |
| `Weather` | `Solar` | Irradiance & temp step | GHI (W/m²), $T_{amb}$ | `SolarEngine` | PV available power adjusts; solar array in 3D reflects active/curtailed state |
| `Weather` | `Wind` | Wind velocity step | $V_{wind}$ (m/s) | `WindEngine` | Cut-in, ramp, rated, or storm cut-out enforced; turbine rotor speed scales |
| `Solar` / `Wind` | `Main Bus` | Renewable availability | $P_{solar}$, $P_{wind}$ (kW) | `PowerBalanceEngine` | Green power flow particle beams travel into Main Bus; generation mix shifts |
| `Demand` | `Main Bus` | Load requirement | $P_{load}$ (kW) | `PowerBalanceEngine` | Bus total throughput equals served load; bus loading indicator updates |
| `Main Bus` | `Battery` | Net surplus or deficit | $P_{chg}$ or $P_{dis}$ (kW) | `PowerBalanceEngine` | Flow particle direction: INTO battery (charging) or OUT OF battery (discharging) |
| `Main Bus` | `Diesel` | Unmet deficit after battery | $P_{diesel}$ (kW) | `PowerBalanceEngine` | Diesel generator online count, kW output, and exhaust vibration indicator in 3D |
| `Diesel` | `Fuel` | Generator dispatched | Fuel burn rate (L/h) | `DieselFuelEngine` | Fuel gauge drops proportionally; days of fuel autonomy recalculates |
| `Main Bus` | `Feeders` | Power distribution | Feeder branch kW | Topological profile | Feeder beam widths and particle velocities reflect branch kW |
| `Feeders` | `Panels` | Zone distribution | Sub-panel kW | Spatial layout | Zone cards highlight active loading; panel status reflects energized state |
| `Panels` | `Loads` | Device circuit feed | Subload kW | `LoadEngine` | Device status: `ONLINE`, `DERATED`, or `SHED` |
| `Scenarios` | `Weather` / `Assets` | Operator scenario selection | Transform operators (SET, MULTIPLY) | `ScenarioTransformer` | Immediate visual perturbation across driving conditions and asset health |
| `Battery` / `Diesel` | `Resilience` | State change | Reserve kW, SOC, Fuel L | `ResilienceEngine` | Threat level shifts (`SAFE` -> `AT_RISK` -> `THREATENED`); continuity hours update |
| `Resilience` | `Policy` | Threat level transition | Threat enum, reserve margin | `PolicyEngine` | Safety rules trigger; advisory warnings or load-shed policies become active |
| `Policy` | `Optimizer` | Constraint boundaries | Hard reserve limits, priority rank | Phase 6 MILP Solver | Optimal dispatch recommendation formulated (`WHAT`, `WHY`, `EXPECTED RESULT`) |
| `Optimizer` | `Operator` | Advisory generation | Recommendation card | Advisory UI | Operator reviews proposed dispatch and approval requirement |
| `Operator` | `LiveTwinSession` | Manual action / Approval | Action dispatch payload | `LiveTwinSession` | Live session applies override; backend advances clock; delta computed |
| `LiveTwinSession` | `3D Twin` | SSE event stream | Complete `TwinState` snapshot | Three.js Spatial Renderer | 3D models change state; power flow particles re-route; colors update |
| `LiveTwinSession` | `Trace` | Any state transition | Event record, delta, causation | `DecisionTraceEngine` | Audit log appends verified decision node; causal explanation accessible |

---

## 3. Causal Propagation Walkthroughs

### Walkthrough A: Severe Cold Wave & Blizzard Cut-Out
1. **Trigger:** `BLIZZARD` or `COMBINED_POLAR_STRESS` scenario activated.
2. **Weather Impact:** Wind speed rises to 30.0 m/s; ambient temperature drops by -15°C; solar GHI drops to 0.
3. **Physical Response:**
   - Wind speed exceeds turbine storm cut-out threshold (25.0 m/s) $\to$ Wind turbines automatically trip to protected standby ($P_{wind} = 0$).
   - Thermal losses surge due to extreme building UA heat transfer $\to$ Heating demand increases.
   - Solar arrays produce 0 kW.
4. **Power Balance Response:** Total station demand must be covered by storage and generators.
5. **Storage & Diesel Response:** Battery discharges at maximum discharge rating; diesel generator DG-1 ramps to 40+ kW; fuel burn increases to ~11 L/h.
6. **Resilience & Policy:** Dependable reserve drops; continuity horizon shortens; threat state shifts from `SAFE` $\to$ `THREATENED`.
7. **Trace & 3D Update:**
   - 3D wind turbine blades feather/stop.
   - Solar flow turns dormant.
   - Diesel generator pulses online with orange operational flow.
   - Decision trace records blizzard cut-out and governor response.

### Walkthrough B: Operator Manual DG-1 Start
1. **Trigger:** Operator clicks `Start DG-1 (Dispatched to 30 kW)` in Manual Control panel.
2. **Dispatch:** Frontend dispatches `POST /api/v1/twin/control/manual` with `action_id: "dg1_start"`.
3. **Backend Validation:** Policy engine validates that starting the generator does not violate safety interlocks.
4. **Physical Calculation:** `TwinEngine` dispatches generator to 30 kW. Surplus generation above station demand flows into the battery storage at up to 24.0 kW charge rate.
5. **Downstream Effects:** Fuel consumption begins; battery SOC begins rising; reserve margin increases; threat state stays `SAFE`.
6. **Live Stream:** SSE stream delivers updated state to frontend. 3D Twin renders active diesel flow and battery charging beams.

---

## 4. Architectural Guarantees
- **Zero Frontend Telemetry Math:** All power balance, thermal, and storage calculations are performed strictly by backend Python engines.
- **Topological Integrity:** Flow paths connect actual topological nodes (Sources $\to$ Main Bus $\to$ Feeders $\to$ Panels $\to$ Loads).
- **Epistemic Air-Gap:** Boundary explicitly locked to `PHYSICAL_CONNECTIVITY = DISCONNECTED`.
