# Polaris-EMS: Synthetic Energy Environment Architecture
**SIH Problem Statement**: SIH26061 — AI-Driven Smart Energy Management System for Polar Research Stations  
**Status**: Authoritative Technical Documentation (Phase 2 Deliverable)  
**Simulator Version**: `polaris-sim-v2.0` | **Dataset Version**: `polaris-synthetic-v1.0`  

---

## 1. Physical Modeling Principles

The Phase 2 synthetic environment is built to serve as the rigorous training ground for Phase 3 ML forecasting, Digital Twin simulation, and rolling MILP optimization. It explicitly enforces the causal chain:

$$\text{Weather} \longrightarrow \text{Physical Environment} \longrightarrow \text{Renewable Generation} \longrightarrow \text{Thermal Dynamics} \longrightarrow \text{Operational Load} \longrightarrow \text{Power Balance} \longrightarrow \text{Battery / Fuel State}$$

### Core Scientific Rules:
1. **Zero Fake Telemetry**: All generated values are classified as `SYNTHETIC` per the immutable Phase 1 Data Provenance Contract.
2. **Deterministic Seed Hierarchy**: Every simulation is fully reproducible via structured seeds:
   - `global_seed`: Base environment seed (default: 42).
   - `station_seed`: Station-specific offset (Bharati: +100, Maitri: +200, Himadri: +300).
   - `weather_seed`, `operational_seed`, `disturbance_seed`: Orthogonal sub-generators.
3. **Leap-Year Explicit Calendar**: Exact UTC timestamps from `2024-01-01 00:00:00Z` to `2026-12-31 23:00:00Z` (26,304 hours per station). Leap day (Feb 29, 2024) is fully modeled.

---

## 2. Environmental & Weather Engine

### A. Temperature Dynamics
Model combines seasonal solar phase, diurnal oscillation, and autoregressive weather noise:
$$T_{\text{ambient}}(t) = 0.94 \cdot T_{\text{ambient}}(t-1) + 0.06 \cdot (\bar{T}_{\text{seasonal}} + T_{\text{diurnal}}) + \epsilon_{\text{temp}} + \Delta T_{\text{disturbance}}$$
- **Seasonal Phase**: Cosine modulation anchored to regional summer solstice (Jan 15 for Antarctica, July 15 for Svalbard).
- **Diurnal Amplitude**: $2.5^\circ\text{C}$ in summer; dampened to $0.8^\circ\text{C}$ during polar night darkness.
- **Extreme Limits**: Strictly bounded to station profile limits (e.g. $-45^\circ\text{C}$ Bharati, $-52^\circ\text{C}$ Maitri, $-38^\circ\text{C}$ Himadri).

### B. Solar Geometry & Irradiance
- **Solar Declination** ($\delta$): Approximated by Cooper's astronomical formula:
  $$\delta = 23.45^\circ \cdot \sin\left(\frac{360^\circ}{365.25} \cdot (d_{\text{oy}} - 81)\right)$$
- **Solar Hour Angle** ($h$): Corrected for station longitude ($\lambda$) from UTC:
  $$t_{\text{solar}} = \left(t_{\text{UTC}} + \frac{\lambda}{15^\circ}\right) \pmod{24}$$
  $$h = (t_{\text{solar}} - 12) \cdot 15^\circ$$
- **Elevation Angle** ($\alpha$):
  $$\sin\alpha = \sin\phi \cdot \sin\delta + \cos\phi \cdot \cos\delta \cdot \cos h$$
- **Clear-Sky Global Horizontal Irradiance** ($G_{\text{clear}}$):
  $$G_{\text{clear}} = 1361.0 \cdot \sin\alpha \cdot (0.72)^{1 / \max(0.08, \sin\alpha)}$$
- **Cloud Attenuation**:
  $$G_{\text{effective}} = G_{\text{clear}} \cdot (1 - 0.78 \cdot C_{\text{fraction}}^2)$$

### C. Wind Power Curve & Cut-Out
The wind turbine power curve obeys piecewise physics:
$$P_{\text{wind}}(v) = \begin{cases} 0 & v < v_{\text{cut-in}} \\ P_{\text{rated}} \cdot \frac{v^3 - v_{\text{cut-in}}^3}{v_{\text{rated}}^3 - v_{\text{cut-in}}^3} & v_{\text{cut-in}} \le v < v_{\text{rated}} \\ P_{\text{rated}} & v_{\text{rated}} \le v < v_{\text{cut-out}} \\ 0 & v \ge v_{\text{cut-out}} \quad (\text{storm protection shutoff}) \end{cases}$$

---

## 3. Polar Disturbance Engine

Ten explicit regimes simulate adverse polar stressors:

| Disturbance Regime | Duration | Physical & Operational Transformation |
| :--- | :--- | :--- |
| `NORMAL` | 12–72 h | Baseline weather and normal operations. |
| `CLOUD_SURGE` | 6–36 h | Cloud cover jumps to 0.85–1.0; diffuse radiation attenuation. |
| `BLIZZARD` | 12–48 h | Wind speed surges $\times 1.8 - 2.5$ ($> 25\text{ m/s}$ cut-out), clouds 1.0, temperature drops $4-10^\circ\text{C}$, solar availability 0.05, infiltration heating $+35\%$. |
| `EXTREME_COLD` | 24–96 h | Radiative clear-sky drop of $10-18^\circ\text{C}$ below normal; heating demand surges $+45\%$; battery capacity derates. |
| `HIGH_WIND` | 8–36 h | Wind surges to $16-22\text{ m/s}$ (maximum turbine capacity). |
| `LOW_WIND` | 12–48 h | Stagnant polar high pressure ($< 2.5\text{ m/s}$), dropping wind generation to zero. |
| `SOLAR_REDUCTION`| 12–72 h | Snow/rime accumulation on panels, reducing PV yield by $60-80\%$. |
| `SOLAR_FAILURE` | 8–48 h | Inverter trip or complete panel snow burial ($0.0\text{ kW}$ solar). |
| `WIND_FAILURE` | 12–48 h | Mechanical failure or blade icing lock ($0.0\text{ kW}$ wind). |
| `COMBINED_POLAR_STRESS` | 24–72 h | Severe blizzard + extreme cold + low solar simultaneously. Tests emergency station survivability. |

---

## 4. Building Thermal Capacitance Model

Building thermal dynamics are modeled with thermal capacitance persistence:
$$T_{\text{indoor}}(t+1) = T_{\text{indoor}}(t) + \frac{\Delta t}{C_{\text{th}}} \cdot \left[ Q_{\text{heating}} + Q_{\text{internal}} - Q_{\text{loss}} \right]$$
- $Q_{\text{loss}} = UA \cdot (T_{\text{indoor}} - T_{\text{ambient}}) \cdot (1 + c_{\text{vent}})$
- $C_{\text{th}}$: Thermal inertia capacitance ($22\text{ kWh/K}$ for Bharati, $18\text{ kWh/K}$ for Maitri, $12\text{ kWh/K}$ for Himadri).
- Prevents artificial discontinuous jumping of indoor temperatures.

---

## 5. Human Activity & Operational Schedules

1. **Circadian Rhythm**:
   - Sleeping hours (23:00–06:00 UTC): Low residential lighting, base HVAC ventilation.
   - Wakeup & Galley Surge (06:00–08:30 UTC): Breakfast cooking ($4.5\text{ kW}$ galley surge).
   - Core Science Shifts (08:30–12:00, 13:30–18:00 UTC): Laboratory spectrometers and compute servers active.
   - Lunch / Dinner Dining Surges: $4.8 - 5.2\text{ kW}$ spikes.
2. **Science Campaign Bursts**: Atmospheric lidar and radar soundings scheduled every 2 days during peak observation hours ($1.45\times$ base science load).
3. **Satellite Pass Windows**: Low-earth orbit tracking antenna runs for 30 minutes every 4–5 hours ($2.2\text{ kW}$ surge).
4. **Resupply Restocking**: Fuel replenishment occurs explicitly on scheduled dates (Jan 20 for Antarctica; May 10 & Oct 10 for Arctic).
