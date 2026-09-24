# POLARIS-EMS — PHASE 15 REALITY INTEGRATION GUIDE

**Project:** Polaris-EMS — Polar Energy Management & Resilience System
**Document Identity:** Operator & Developer Integration Manual for Real-World Meteorological & Telemetry Feeds
**Status:** `PHASE_15_FROZEN`
**Governance Event:** `PHASE15_EPISTEMIC_RECONCILIATION_COMPLETE`
**Governing Rule:** *"Connect reality to the existing brain. Do not build another brain."*
**Physical Connectivity:** `PHYSICAL_CONNECTIVITY = DISCONNECTED`
**Physical SCADA Link:** `PHYSICAL_SCADA_LINK = FALSE`
**Physical Validation Status:** `PHYSICAL_VALIDATION = NOT_AVAILABLE`

---

## 1. Architectural Overview

Phase 15 connects external reality feeds directly to the frozen Polaris-EMS computational pipeline. The external reality architecture follows this strict sequence:

```text
[EXTERNAL WEATHER SOURCE (e.g. Open-Meteo, NCPOR)]
                     ↓
         [PROVIDER ADAPTER (HTTP/Satcom)]
                     ↓
        [SCHEMA & FINITE VALUE VALIDATION]
                     ↓
    [POLAR PHYSICAL BOUNDS CHECK (-90°C..+30°C)]
                     ↓
         [FRESHNESS SCORING (Staleness)]
                     ↓
        [TEMPORAL CAUSALITY GUARD (Anti-Leak)]
                     ↓
        [PROVENANCE ATTACHMENT (Strict 6 Tiers)]
                     ↓
       [FROZEN POLARIS PIPELINE ORCHESTRATION]
                     ↓
   [MODEL-VS-REFERENCE & TWIN CONSISTENCY CHECK]
                     ↓
        [CONTROLLED CALIBRATION GOVERNANCE]
```

### 1.1 Explicit Operational Data-Lineage Table

| Evaluation | Prediction Source | Reference / Input Source | Epistemic Reality & Provenance | Physical SCADA |
| :--- | :--- | :--- | :---: | :---: |
| **Bharati Electric Load** ($\text{MAE}=1.33\text{ kW}$) | Phase 3 ML Forecast trajectory | Synthetic Benchmark Reference (`obs_load`) | **`SYNTHETIC`** (Deterministic operational validation reference) | `DISCONNECTED` |
| **Open-Meteo Weather Feed** (Hourly multi-horizon) | Open-Meteo NWP Forecast API | Global Numerical Weather Prediction Model | **`FORECAST`** (External numerical atmospheric forecast) | `DISCONNECTED` |
| **Twin Electrical Check** ($\Delta \le 0.05\text{ kW}$) | Phase 4 Digital Twin Simulation | Calibrated Electrical Power Benchmark Step | **`SYNTHETIC`** reference step | `DISCONNECTED` |
| **Twin Thermal Check** (`CALIB-BHA-THE-001`) | Phase 4 Digital Twin Simulation | Synthetic Extreme Cold Reference ($14^\circ\text{C}$ vs $20.5^\circ\text{C}$) | **`SYNTHETIC`** reference perturbation | `DISCONNECTED` |
| **Twin Battery Storage** ($\Delta \le 5.0\%$) | Phase 4 Digital Twin Simulation | Synthetic Battery SOC Benchmark Step | **`SYNTHETIC`** reference step | `DISCONNECTED` |
| **Twin Fuel Rate** ($\Delta \le 1.0\text{ L/h}$) | Phase 4 Digital Twin Simulation | Synthetic Generator Fuel Flow Benchmark Step | **`SYNTHETIC`** reference step | `DISCONNECTED` |
| **Operational Replay** (`REPLAY-BHA-8B1C24`) | Frozen Phase 6 HiGHS + Phase 4 Twin | 48h Open-Meteo NWP Forecast Series | **`SIMULATED`** (Closed-loop digital twin trajectory) | `DISCONNECTED` |

---

## 2. External Provider Configuration

All external integrations are configured via environment variables or `backend/config/settings.py`:

```bash
# Enable/Disable External Provider Ingestion
POLARIS_PROVIDERS__ENABLED=true

# Request Timeout (Satcom links may require higher tolerance)
POLARIS_PROVIDERS__REQUEST_TIMEOUT_SEC=10.0

# Freshness Horizon (Observations older than 3600s are scored as degraded)
POLARIS_PROVIDERS__MAX_FRESHNESS_SEC=3600.0

# Open-Meteo Endpoint
POLARIS_PROVIDERS__OPENMETEO_ENDPOINT=https://api.open-meteo.com/v1/forecast

# NCPOR Polar Telemetry Gateway (Optional)
POLARIS_PROVIDERS__NCPOR_GATEWAY_URL=
```

---

## 3. Data Quality & Bounds Validation Contract

Every external weather record ingested must satisfy the following physical constraints:

| Variable | Physical Bounds | Units | Rejection Consequence |
| :--- | :--- | :---: | :--- |
| **Ambient Temperature** | $[-90.0, +30.0]$ | $^\circ\text{C}$ | `is_valid = False`, observation quarantined |
| **Wind Speed** | $[0.0, 85.0]$ | $\text{m/s}$ | `is_valid = False`, observation quarantined |
| **Solar Irradiance** | $[0.0, 1400.0]$ | $\text{W/m}^2$ | `is_valid = False`, observation quarantined |
| **Surface Pressure** | $[850.0, 1050.0]$ | $\text{hPa}$ | `is_valid = False`, observation quarantined |
| **Relative Humidity** | $[0.0, 100.0]$ | $\%$ | `is_valid = False`, observation quarantined |
| **Timestamp Causality** | $\le \text{reference\_time} + 60\text{s}$ | ISO-8601 | `is_valid = False`, leakage guard triggered |

### Circuit Breaker & Quarantine Policy
- If an external provider generates **5 consecutive invalid payloads**, the provider is transitioned to `QUARANTINED`.
- During quarantine, the system engages autonomous fallback to synthetic physics artifacts.
- Operators can inspect and unquarantine a provider using:
  ```python
  bridge = get_reality_bridge()
  bridge.unquarantine_provider("OpenMeteo-Polar")
  ```

---

## 4. Provenance Taxonomy Rules

Polaris-EMS enforces a closed 6-tier provenance taxonomy. Developers and operators must never introduce alternative labels:

1. `REAL`: Actual telemetry received from authenticated, physically wired instrumentation. *(Note: Currently disabled since zero physical SCADA hardware is connected).*
2. `CONFIGURED`: Static system specifications from engineering nameplates (e.g. diesel tank capacities, solar tilt).
3. `ASSUMED`: Default operating assumptions where direct measurements are physically unavailable.
4. `SYNTHETIC`: Deterministic climatological baselines generated by physics models.
5. `FORECAST`: Predictions generated by Phase 3 ML models or external meteorological feeds (e.g. Open-Meteo).
6. `SIMULATED`: Microgrid dynamic trajectories computed by the Phase 4 Digital Twin.

**PROHIBITED LABELS:** `LIVE`, `REAL_TIME`, `API`, `OPTIMIZED`, `DERIVED`, `REAL_EXTERNAL`, `FIELD_REAL`, `OBSERVED_REAL`, `PRODUCTION_REAL`.

---

## 5. Controlled Model Calibration Protocol

Discrepancies identified during operational comparisons are **never** used to silently retrain or update frozen production models. The following human-gated workflow is mandatory:

1. **Detection:** Digital Twin consistency checks detect systematic error ($\Delta > \text{tolerance}$).
2. **Registration:** A `CalibrationCandidate` is logged with an immutable unique ID (e.g. `CALIB-BHA-THE-001`).
3. **Status:** The candidate is tagged with `governance_status = "PENDING_CONTROLLED_REVIEW"`.
4. **Preservation:** The frozen baseline model remains the sole authority (`immutable_baseline_preserved = True`).
5. **Review Gate:** Polar station engineers evaluate candidate parameters against seasonal maintenance logs and sensor recalibration certificates before issuing formal approval.

---

## 6. Physical SCADA Hardware Reality Disclaimer

The system's operational status is governed by an absolute truth boundary:

```text
PHYSICAL_CONNECTIVITY = DISCONNECTED
PHYSICAL_SCADA_LINK = FALSE
PHYSICAL_VALIDATION = NOT_AVAILABLE
```

Under no circumstances should API connectivity or simulation accuracy be misrepresented as a physical connection to Antarctic microgrid breakers or generator governors. All dispatch setpoints operate in **Advisory Mode**.
