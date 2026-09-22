# Polaris-EMS: Synthetic Dataset Schema Specification
**SIH Problem Statement**: SIH26061 — AI-Driven Smart Energy Management System for Polar Research Stations  
**Status**: Authoritative Schema Contract (Phase 2 Deliverable)  
**Schema Version**: `v1.0` | **Granularity**: Hourly ($1\text{h}$)  

---

## 1. Column Catalog & Specifications

| Column Name | Data Type | Physical Unit | Valid Range | Provenance Tier | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`timestamp`** | `string` (ISO 8601) | UTC ISO | `2024-01-01` to `2026-12-31` | `SYNTHETIC` | Timezone-aware UTC timestamp (`YYYY-MM-DDTHH:MM:SS+00:00`). |
| **`station_id`** | `string` | Categorical | `BHARATI`, `MAITRI`, `HIMADRI` | `CONFIGURED` | Target Indian Polar Research Station identifier. |
| **`temperature_c`** | `float` | $^\circ\text{C}$ | $[-75.0, 20.0]$ | `SYNTHETIC` | Outside ambient dry-bulb temperature. |
| **`pressure_hpa`** | `float` | $\text{hPa}$ | $[920.0, 1050.0]$ | `SYNTHETIC` | Atmospheric station barometric pressure. |
| **`humidity_pct`** | `float` | $\%$ | $[10.0, 100.0]$ | `SYNTHETIC` | Relative atmospheric humidity. |
| **`wind_speed_ms`** | `float` | $\text{m/s}$ | $[0.0, 70.0]$ | `SYNTHETIC` | 10-meter surface wind speed. |
| **`wind_direction_deg`**| `float` | $\text{degrees}$ | $[0.0, 360.0)$ | `SYNTHETIC` | Wind direction azimuth from true North. |
| **`irradiance_wm2`** | `float` | $\text{W/m}^2$ | $[0.0, 1400.0]$ | `SYNTHETIC` | Surface global horizontal solar irradiance (GHI). |
| **`cloud_fraction`** | `float` | Ratio $[0, 1]$ | $[0.0, 1.0]$ | `SYNTHETIC` | Cloud cover fraction ($0 = \text{clear}, 1 = \text{overcast}$). |
| **`storm_state`** | `string` | Categorical | 10 Regimes | `SYNTHETIC` | Active disturbance state name. |
| **`solar_elevation_deg`**| `float` | $\text{degrees}$ | $[-90.0, 90.0]$ | `SYNTHETIC` | Astronomical solar altitude angle. |
| **`solar_available_kw`** | `float` | $\text{kW}$ | $[0.0, P_{\text{pv,peak}}]$ | `SYNTHETIC` | Potential PV generation before array availability derate. |
| **`solar_generation_kw`**| `float` | $\text{kW}$ | $[0.0, P_{\text{pv,peak}}]$ | `SYNTHETIC` | Actual solar generation delivered to station bus. |
| **`wind_generation_kw`** | `float` | $\text{kW}$ | $[0.0, P_{\text{wind,rated}}]$ | `SYNTHETIC` | Actual wind generation delivered to station bus. |
| **`wind_turbine_status`**| `string` | Categorical | 4 Statuses | `SYNTHETIC` | `BELOW_CUT_IN`, `OPERATING_RAMP`, `OPERATING_RATED`, `STORM_CUT_OUT`, or `TRIPPED_OR_ICED`. |
| **`thermal_load_kw`** | `float` | $\text{kW}$ | $\ge 0.0$ | `SYNTHETIC` | Electrical heating load required to balance building heat loss. |
| **`critical_load_kw`** | `float` | $\text{kW}$ | $> 0.0$ | `SYNTHETIC` | Non-deferrable life support, trace freeze heating, and network comms. |
| **`important_load_kw`**| `float` | $\text{kW}$ | $\ge 0.0$ | `SYNTHETIC` | Science laboratories, data acquisition compute servers, cold food storage. |
| **`operational_load_kw`**| `float`| $\text{kW}$ | $\ge 0.0$ | `SYNTHETIC` | Residential crew quarters, galley cooking surges, waste treatment auxiliary. |
| **`flexible_load_kw`** | `float` | $\text{kW}$ | $\ge 0.0$ | `SYNTHETIC` | Deferrable snow melter tanks and electric skidoo charging. |
| **`maintenance_load_kw`**| `float`| $\text{kW}$ | $\ge 0.0$ | `SYNTHETIC` | Auxiliary workshop testing and generator servicing loads. |
| **`total_load_kw`** | `float` | $\text{kW}$ | $> 0.0$ | `SYNTHETIC` | Total station electrical demand ($\sum \text{subloads}$). |
| **`battery_soc_pct`** | `float` | $\%$ | $[20.0, 95.0]$ | `SYNTHETIC` | Battery state of charge percentage. |
| **`battery_energy_kwh`**| `float` | $\text{kWh}$ | $[0.0, E_{\text{usable}}]$ | `SYNTHETIC` | Usable energy currently stored in battery bank. |
| **`battery_charge_kw`** | `float` | $\text{kW}$ | $[0.0, P_{\text{chg,max}}]$ | `SYNTHETIC` | Power flowing into battery bank from generation surplus. |
| **`battery_discharge_kw`**| `float`| $\text{kW}$ | $[0.0, P_{\text{dis,max}}]$ | `SYNTHETIC` | Power flowing out of battery bank to supply deficit. |
| **`battery_temperature_derating`**| `float`| Ratio | $[0.70, 1.00]$ | `SYNTHETIC` | Cold-temperature capacity derating multiplier. |
| **`generator_status`** | `string` | Categorical | `ONLINE`, `STANDBY` | `SYNTHETIC` | Diesel generator operating state. |
| **`generator_power_kw`**| `float` | $\text{kW}$ | $[0.0, P_{\text{gen,rated}}]$ | `SYNTHETIC` | Electrical power output from diesel generator. |
| **`fuel_consumed_l`** | `float` | $\text{Liters}$ | $\ge 0.0$ | `SYNTHETIC` | Diesel fuel burned during the hourly interval. |
| **`fuel_remaining_l`** | `float` | $\text{Liters}$ | $[0.0, V_{\text{tank}}]$ | `SYNTHETIC` | Remaining fuel volume in bulk storage tanks. |
| **`renewable_generation_kw`**| `float`| $\text{kW}$ | $\ge 0.0$ | `SYNTHETIC` | Combined generation ($\text{solar} + \text{wind}$). |
| **`total_generation_kw`**| `float` | $\text{kW}$ | $\ge 0.0$ | `SYNTHETIC` | Combined generation ($\text{solar} + \text{wind} + \text{diesel}$). |
| **`curtailment_kw`** | `float` | $\text{kW}$ | $\ge 0.0$ | `SYNTHETIC` | Excess renewable generation dumped when storage is full. |
| **`unserved_energy_kw`**| `float` | $\text{kW}$ | $\ge 0.0$ | `SYNTHETIC` | Unmet load if deficit exceeds all generator and battery resources. |
| **`occupancy_state`** | `float` | Factor $[0, 1]$ | $[0.20, 1.00]$ | `SYNTHETIC` | Circadian human activity index. |
| **`maintenance_state`** | `float` | Binary | $0.0 \text{ or } 1.0$ | `SYNTHETIC` | Indicator of scheduled maintenance shift. |
| **`research_activity_state`**| `float`| Factor | $[1.00, 1.45]$ | `SYNTHETIC` | Multiplier for scientific campaign instruments. |
| **`communication_state`**| `float`| Binary | $0.0 \text{ or } 1.0$ | `SYNTHETIC` | Indicator of active satellite tracking pass. |
| **`scenario_id`** | `string` | Categorical | 10 Regimes | `SYNTHETIC` | Disturbance regime identifier. |
| **`disturbance_state`** | `string` | Categorical | 10 Regimes | `SYNTHETIC` | Active environmental disturbance condition. |
| **`provenance`** | `string` | Enum | `SYNTHETIC` | `CONFIGURED` | Strict Phase 1 provenance tag. |
| **`dataset_version`** | `string` | Version | `polaris-synthetic-v1.0` | `CONFIGURED` | Immutable dataset version identifier. |
| **`simulator_version`** | `string` | Version | `polaris-sim-v2.0` | `CONFIGURED` | Simulation code engine version. |
| **`seed`** | `integer` | Seed | $\ge 0$ | `CONFIGURED` | Deterministic seed used to generate realization. |

---

## 2. Invariant Conservation Laws

Every generated row is guaranteed to satisfy:
1. **Load Decomposition**:
   $$\text{total\_load\_kw} = \text{thermal\_load\_kw} + \text{critical\_load\_kw} + \text{important\_load\_kw} + \text{operational\_load\_kw} + \text{flexible\_load\_kw} + \text{maintenance\_load\_kw}$$
2. **Power Balance**:
   $$\text{total\_generation\_kw} + \text{battery\_discharge\_kw} = \text{total\_load\_kw} + \text{battery\_charge\_kw} + \text{curtailment\_kw} - \text{unserved\_energy\_kw}$$
