# POLARIS-EMS — FINAL NUMERICAL VALUE & TELEMETRY AUDIT
**Prompt ID**: 61853 / Phase 18 Final Launch Quality Gate  
**Requirement**: "Every displayed operational value must originate from one of: REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED according to the canonical provenance system. Zero arbitrary, hardcoded numbers for appearance."

---

## 1. Authoritative Value Registry & Provenance Mapping

| UI Field / Metric | Source Object | Canonical Provenance | Physical Unit | Real-Time Update Mechanism | Backend Calculation Owner | Scenario Sensitive? | Audit Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Total Generation** | `viewModel.powerSummary.totalGenerationKw` | `SIMULATED` | kW | 1000ms SSE Stream (`/twin/live/{id}/stream`) | `TwinEngine` / `PowerBalanceEngine` | Yes — shifts on renewable curtailment or generator trip | **VERIFIED** |
| **Solar PV Output** | `viewModel.powerSummary.solarGenerationKw` | `SIMULATED` | kW | 1000ms SSE Stream | `SolarEngine` (Irradiance $\times$ Area $\times \eta$) | Yes — attenuates under cloud/blizzard | **VERIFIED** |
| **Wind Turbine Output** | `viewModel.powerSummary.windGenerationKw` | `SIMULATED` | kW | 1000ms SSE Stream | `WindEngine` (Power curve vs $V_{\text{wind}}$) | Yes — cuts out at 25 m/s storm wind | **VERIFIED** |
| **Diesel Generation** | `viewModel.powerSummary.dieselGenerationKw` | `SIMULATED` | kW | 1000ms SSE Stream | `PowerBalanceEngine` (Dispatched base load) | Yes — replaces lost renewables or trips | **VERIFIED** |
| **Battery Power** | `viewModel.powerSummary.batteryPowerKw` | `SIMULATED` | kW | 1000ms SSE Stream | `BatteryEngine` (Net surplus charge / deficit discharge) | Yes — reverses flow during load surges | **VERIFIED** |
| **Battery State of Charge (SOC)** | `viewModel.powerSummary.batterySocPercent` | `SIMULATED` | % | 1000ms SSE Stream | `BatteryEngine` (Coulomb counting with efficiency) | Yes — discharges under prolonged storm | **VERIFIED** |
| **Battery Usable Capacity** | `state.battery.capacity_kwh` | `SIMULATED` | kWh | 1000ms SSE Stream | `BatteryEngine` (Degraded capacity vs temperature) | Yes — drops under `BATTERY_DEGRADATION` | **VERIFIED** |
| **Total Station Demand** | `viewModel.powerSummary.totalDemandKw` | `SIMULATED` | kW | 1000ms SSE Stream | Device sum + `ThermalEngine` heating load | Yes — surges under cold snap / blizzard | **VERIFIED** |
| **Life Support Demand** | `viewModel.loadGroups.criticalKw` | `CONFIGURED` / `SIMULATED` | kW | 1000ms SSE Stream | Device profile nominal rating + HVAC loop | Yes — guarded with priority 1 protection | **VERIFIED** |
| **Ambient Temperature** | `viewModel.environment.ambientTemperatureC` | `FORECAST` / `SIMULATED` | °C | 1000ms SSE Stream | Station diurnal model / Weather dataset | Yes — drops by 10–20°C in cold scenarios | **VERIFIED** |
| **Wind Speed** | `viewModel.environment.windSpeedMs` | `FORECAST` / `SIMULATED` | m/s | 1000ms SSE Stream | Weather dataset / Katabatic surge model | Yes — surges up to 30 m/s in blizzard | **VERIFIED** |
| **Solar GHI Irradiance** | `viewModel.environment.irradianceWm2` | `FORECAST` / `SIMULATED` | W/m² | 1000ms SSE Stream | Astronomical solar elevation + cloud factor | Yes — zeroed in night and whiteout | **VERIFIED** |
| **Fuel Tank Autonomy** | `viewModel.fuel.daysRemaining` | `SIMULATED` | Days | 1000ms SSE Stream | `FuelEngine` (Stock / dynamic burn rate) | Yes — drops faster under diesel surge | **VERIFIED** |
| **Composite Resilience Score**| `viewModel.resilience.score` | `SIMULATED` | % (0–100) | 1000ms SSE Stream | `ResilienceEngine` (9-dimensional metric) | Yes — decreases under compound stress | **VERIFIED** |
| **Spinning Reserve Margin** | `viewModel.resilience.spinningReserveKw`| `SIMULATED` | kW | 1000ms SSE Stream | Available online headroom above load | Yes — drops to zero if generators trip | **VERIFIED** |
| **Rated Solar Capacity** | `stationProfile.electrical.solar_pv_kw_peak` | `CONFIGURED` | kWp | Station Switcher / Profile load | Station hardware specification file | No — hardware constant | **VERIFIED** |
| **Rated Wind Capacity** | `stationProfile.electrical.wind_turbines[].rated_kw` | `CONFIGURED` | kW | Station Switcher / Profile load | Station hardware specification file | No — hardware constant | **VERIFIED** |
| **Rated Generator Capacity** | `stationProfile.electrical.diesel_generator_kw_rated` | `CONFIGURED` | kW | Station Switcher / Profile load | Station hardware specification file | No — hardware constant | **VERIFIED** |
| **Rated BESS Capacity** | `stationProfile.electrical.battery_capacity_kwh_rated` | `CONFIGURED` | kWh | Station Switcher / Profile load | Station hardware specification file | No — hardware constant | **VERIFIED** |

---

## 2. Eradication of Legacy Mock Fallbacks
The following static legacy constants were audited and eliminated from all frontend components:
- `142.5` (arbitrary demand): Replaced by `viewModel.powerSummary.totalDemandKw || '—'`
- `29.5` (arbitrary temperature): Replaced by `viewModel.environment.ambientTemperatureC || '—'`
- `38 kW` (arbitrary diesel): Replaced by authoritative `viewModel.powerSummary.dieselGenerationKw`
- `9.8 L/h` (arbitrary fuel burn): Replaced by dynamic `fuelEngine.get_consumption_rate_lph()`
- Hardcoded sine wave animations: Replaced by Three.js state interpolation driven directly by incoming SSE snapshot telemetry.

---

## 3. Epistemic Provenance Compliance Audit
1. Every numeric display in the application explicitly indicates its provenance tag on hover or in the inspector drawer.
2. In the event of a severed network connection or backend outage, metrics display `—` or `UNAVAILABLE` rather than defaulting to fabricated placeholder readings.
3. Total generation and total load strictly satisfy the power balance invariant:
   $$P_{\text{gen}} + P_{\text{battery,dis}} = P_{\text{load}} + P_{\text{battery,chg}} + P_{\text{losses}} + P_{\text{unserved}}$$
   reconciling across the UI cards, the 3D conduit flow thicknesses, and the decision trace.
