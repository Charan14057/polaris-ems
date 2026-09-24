# POLARIS-EMS — EXTERNAL DATA INTEGRATION & REALITY BRIDGE GUIDE
**Provider-Agnostic Integration Architecture & Environmental Sanity Validation**

**System:** Polaris-EMS — Polar Energy Management & Resilience System  
**SIH Problem Statement:** SIH26061  
**Architecture Layer:** Phase 14 Workstream C (`backend/integrations/`)  
**Status:** `PHASE_14_READY_TO_FREEZE`

---

## 1. Architectural Philosophy & Reality Bridge

Polaris-EMS is engineered for the world's most remote research stations (Bharati, Maitri, Himadri), where external communications are intermittent, bandwidth-constrained, and subject to severe polar weather disruptions.

The **External Reality Bridge** provides a provider-agnostic ingestion architecture designed around two unbreakable invariants:
1. **The Computational Authority Invariant:** External data feeds must NEVER bypass or replace the frozen ML forecasting models (Phase 3), Digital Twin equations (Phase 4), or microgrid optimizer (Phase 6).
2. **The Epistemic Honesty Invariant:** The existence of an API connection or satcom feed does NOT make data "real". Data must be classified strictly according to what it actually represents. Zero connected physical polar SCADA telemetry exists.

---

## 2. Ingestion & Quality Validation Pipeline

```text
External Provider (API / Satcom Packet / AWS Gateway)
        │
        ▼
Provider Adapter (backend/integrations/adapters/*)
  - Isolates vendor-specific HTTP/JSON/CSV formats
  - Enforces timeouts, circuit breaking & latency tracking
        │
        ▼
Schema Validation (backend/integrations/schemas.py)
  - Normalizes into ExternalWeatherObservation or ExternalTelemetryPayload
        │
        ▼
Physical Boundary & Sanity Filter (backend/integrations/validation.py)
  - Temperature:  -90.0°C <= T <= +30.0°C
  - Wind Speed:     0.0 m/s <= W <= 85.0 m/s
  - Solar Irradiance: 0.0 W/m² <= GHI <= 1400.0 W/m²
  - Rejects NaN / Inf floating-point values
        │
        ▼
Temporal Causality & Freshness Guard
  - Zero future leakage: timestamp <= evaluation_time + 60s tolerance
  - Quality score weighting (1.0 for FRESH, 0.6 for STALE)
        │
        ▼
Provenance Assignment (Strict 6-Tier)
  - REAL | CONFIGURED | ASSUMED | SYNTHETIC | FORECAST | SIMULATED
        │
        ▼
Frozen Interfaces (Phase 3 Forecast / Phase 5 Scenario / Phase 4 Twin)
```

---

## 3. Physical Boundary Filter Specifications

To prevent corrupted satellite feeds, frozen sensors, or malicious payloads from perturbing downstream optimization or digital twin replay, all incoming measurements must satisfy polar physical domain bounds:

| Environmental Metric | Valid Physical Range | Physical / Atmospheric Basis | Failure Action |
| :--- | :--- | :--- | :--- |
| **Ambient Temperature** | `[-90.0°C, +30.0°C]` | Record low is $-89.2^\circ\text{C}$ (Vostok); summer in Svalbard reaches $+20^\circ\text{C}$ | Reject & quarantine |
| **Wind Speed** | `[0.0 m/s, 85.0 m/s]` | Katabatic storm gusts exceed $80\text{ m/s}$ ($288\text{ km/h}$) | Reject & quarantine |
| **Solar Irradiance** | `[0.0 W/m², 1400.0 W/m²]` | Extraterrestrial solar constant is $\approx 1361\text{ W/m}^2$ | Reject & quarantine |
| **Atmospheric Pressure** | `[500.0 hPa, 1100.0 hPa]` | High-altitude polar plateau pressure | Issue warning |
| **Relative Humidity** | `[0.0%, 100.0%]` | Standard psychrometric domain | Issue warning |
| **Finite Number Check** | No `NaN` or `Inf` | Floating-point integrity | Immediate rejection |
| **Temporal Causality** | $t_{\text{obs}} \le t_{\text{ref}} + 60\text{s}$ | Zero future data leakage guard | Rejection (leakage breach) |

---

## 4. Strict 6-Tier Provenance Taxonomy

Polaris-EMS enforces a strict closed taxonomy of exactly six provenance tiers:

| Tier | Definition | Allowed Use in Reality Bridge |
| :--- | :--- | :--- |
| `REAL` | Directly measured from verified physical SCADA sensors. | Permitted ONLY when authenticated hardware telemetry is connected. Currently 0 sensors. |
| `CONFIGURED` | Read from immutable station profile specifications or frozen registry configs. | System specifications, adapter configuration metadata, station ratings. |
| `ASSUMED` | Documented engineering estimates or conservative physical constants. | Fuel density, battery nominal temperatures, resupply margins. |
| `SYNTHETIC` | Physics-calibrated synthetic baselines (e.g. ERA5-calibrated polar environments). | Simulated station baselines, incoming test packets, benchmark datasets. |
| `FORECAST` | Machine learning model predictions from Phase 3 conformal quantile models. | Quantile predictions ($P_{10}, P_{50}, P_{90}, P_{95}$). |
| `SIMULATED` | Deterministic outputs of the Phase 4 Digital Twin, Phase 6 MILP, or Phase 7 resilience engine. | Power trajectories, battery SOC profiles, thermal habitability curves. |

> [!CAUTION]
> **Prohibited Provenance Tiers:**  
> The following terms are **strictly forbidden** anywhere in Polaris-EMS schemas, API routes, or adapters:
> `LIVE`, `REAL_TIME`, `OPTIMIZED`, `API`, `DERIVED`, `PRODUCTION`.  
> Attempting to emit any forbidden tier triggers immediate validation exceptions (`ValueError`).

---

## 5. External Provider Fallback Invariant

External reality feeds are strictly optional. When an external feed is disconnected, stale, or malformed:

```text
Provider Failure / Stale Observation
               │
               ▼
Validation Rejection (Quarantined)
               │
               ▼
Preserve Existing Safe Pipeline (Calibrated Synthetic Twin Baseline)
               │
               ▼
Emit Degraded Health Status (GET /health/providers)
               │
               ▼
NEVER Manufacture Fake "Live" Telemetry
```

---

## 6. Built-in Provider Adapters

### 1. Open-Meteo Polar Adapter (`OpenMeteoPolarAdapter`)
- Queries Open-Meteo REST API for polar coordinates:
  - *Bharati:* $69.4^\circ\text{S}, 76.18^\circ\text{E}$
  - *Maitri:* $70.77^\circ\text{S}, 11.73^\circ\text{E}$
  - *Himadri:* $78.92^\circ\text{N}, 11.93^\circ\text{E}$
- Normalizes solar GHI, 2-meter air temperature, and 10-meter wind speed into `ExternalWeatherObservation`.

### 2. NCPOR Format Adapter (`NCPORFormatAdapter`)
- Adheres to National Centre for Polar and Ocean Research (NCPOR) automated weather station (AWS) packet format.
- Parses specialized fields (snow drift factor, surface barometric pressure, battery voltage).

### 3. Offline Satcom File Spooler (`OfflineFileSpoolerAdapter`)
- Ingests air-gapped packet dumps dropped from satellite communication links into `datasets/incoming_spool/<STATION>/`.
- Enables remote station deployment without continuous internet connectivity.

---

## 7. How to Implement a Custom Adapter

To integrate a new station telemetry provider or scientific satellite feed:

```python
from typing import Optional
from backend.integrations.base import AbstractBaseProviderAdapter
from backend.integrations.schemas import ExternalWeatherObservation
from datetime import datetime, timezone

class CustomPolarSatcomAdapter(AbstractBaseProviderAdapter):
    """Custom adapter for Polar Research Station satcom packets."""
    
    def __init__(self, endpoint_url: str, enabled: bool = True):
        super().__init__(name="Custom-Satcom-Adapter", enabled=enabled)
        self.endpoint_url = endpoint_url

    def fetch_latest_weather(self, station_id: str) -> Optional[ExternalWeatherObservation]:
        if not self.enabled:
            return None
            
        try:
            # 1. Fetch raw payload from vendor endpoint with timeout
            # 2. Extract metrics (temperature, wind, solar)
            # 3. Construct and return normalized observation
            obs = ExternalWeatherObservation(
                station_id=station_id.upper(),
                timestamp=datetime.now(timezone.utc),
                ambient_temperature_c=-22.5,
                wind_speed_ms=16.0,
                solar_irradiance_wm2=0.0,
                source_provider=self.name,
                provenance="SYNTHETIC"  # Or "REAL" only if physical sensor verified
            )
            self.record_success(latency_ms=120.0)
            return obs
            
        except Exception as e:
            self.record_failure(str(e))
            return None

    def test_connectivity(self) -> bool:
        return True
```

Register the adapter in `ExternalRealityBridge`:
```python
bridge = get_reality_bridge()
bridge.register_adapter(CustomPolarSatcomAdapter(endpoint_url="https://..."))
```
All validation, physical boundary checking, freshness rating, and safe fallback handling are applied automatically by the orchestrator.
