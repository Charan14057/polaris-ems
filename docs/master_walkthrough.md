# Polaris-EMS: Master System Walkthrough & Current Operational Stage

**System Status**: 🟢 **PHASES 1–14 COMPLETE & FROZEN (`PHASE_14_FROZEN`) | ENTERPRISE PRODUCTION HARDENED | DEPLOYMENT & EXTERNAL INTEGRATION OPERATIONAL**  
**Target Fleet**: Bharati Station (69°S, Antarctic), Maitri Station (70°S, Antarctic), Himadri Station (79°N, Arctic)  
**Verification Environment**: Local Integrated Production Runtime (Vite Proxy on `http://127.0.0.1:3000` $\to$ FastAPI on `http://127.0.0.1:8000`)  
**Containerized Deployment**: Multi-Stage Docker (`deployment/Dockerfile`) + Compose (`deployment/docker-compose.yml`) + Nginx Reverse Proxy  
**API Documentation**: Interactive Swagger UI on `http://127.0.0.1:8000/docs`  
**System Readiness**: `GET http://127.0.0.1:8000/ready` (and `/health/ready`)  
**Physical Connectivity**: Disconnected (`GET http://127.0.0.1:8000/health/physical` $\to$ Zero physical SCADA telemetry)  

---

## 1. Exact Stage of the Project

Polaris-EMS has completed Phase 14 engineering, deployment packaging, external data integration architecture, runtime observability, security hardening, frontend productization, disaggregated health modeling, and deterministic demonstration hardening. Following complete empirical validation and final consistency checks, the system is in the **Phases 1–14 Complete & Frozen** stage (**`PHASE_14_FROZEN`**). The overall project status is **`PHASES_1_14_COMPLETE`**.

**Phase 1–13 Frozen Authorities**: All computational forecasting (Phase 3), physical equations (Phase 4), scenarios (Phase 5), Pyomo/HiGHS optimization (Phase 6), resilience state machine (Phase 7), policy governance (Phase 8), edge autonomy (Phase 11), decision trace DAG (Phase 12), and scientific validation benchmarks (Phase 13) remain **permanently frozen and immutable**. Phase 14 acts exclusively as a production packaging, integration, observability, and presentation shell around these frozen authorities.

### Overall Verification Scorecard

| Verification Suite | Tool / Command | Scope | Passing / Total | Pass Rate | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Backend Test Suite** | `pytest tests/` | Phases 1–14 full regression suite | **266 / 266** | **100%** | 🟢 **PASS** |
| **Phase 14 Deployment Suite** | `pytest tests/test_phase14_deployment.py` | Config, providers, bounds, security, health | **20 / 20** | **100%** | 🟢 **PASS** |
| **Frontend Test Suite** | `npm test -- --run` | API client & React UI components | **12 / 12** | **100%** | 🟢 **PASS** |
| **Frontend Production Build** | `npm run build` | `tsc` strict check + Vite production bundle | **0 errors (9.97s)** | **100%** | 🟢 **PASS** |
| **Phase 14 Production Demo** | `python scripts/run_phase14_production_demo.py` | 6-step deterministic end-to-end demo | **6 / 6 steps** | **100%** | 🟢 **PASS** |
| **Production Readiness Gate** | `python scripts/verify_production_readiness.py` | 26 static & architectural checks | **26 / 26** | **100%** | 🟢 **PASS** |
| **Phase 13 Final Consistency Gate** | `python scripts/verify_phase13_consistency.py` | 12 mathematical & taxonomic checks | **12 / 12** | **100%** | 🟢 **PASS** |
| **Phase 10 Runtime Gate** | `python scripts/verify_phase10_runtime.py` | Live UI-to-API proxy & solver pipeline | **13 / 13** | **100%** | 🟢 **PASS** |
| **Phase 11 Edge Gate** | `python scripts/verify_phase11_runtime.py` | Edge fallback, shedding & sync | **10 / 10** | **100%** | 🟢 **PASS** |
| **Phase 12 Trace Gate** | `python scripts/verify_phase12_runtime.py` | DAG lineage, epistemic tiers, exports | **11 / 11** | **100%** | 🟢 **PASS** |
| **Phase 13 Scientific Runtime**| `python scripts/verify_phase13_runtime.py` | 14 validation gates across fleet | **14 / 14** | **100%** | 🟢 **PASS** |
| **Phase 13 Leakage Audit** | `python scripts/verify_phase13_leakage.py` | Temporal causality & feature integrity | **14 / 14** | **100%** | 🟢 **PASS** |
| **End-to-End Demonstration** | `python scripts/run_phase13_demo.py` | 7-step polar emergency scenario | **7 / 7 steps** | **100%** | 🟢 **PASS** |
| **Phase 13 Evidence Reports** | `python scripts/export_phase13_reports.py` | Benchmark, calibration, replay evidence | **15 / 15** | **100%** | 🟢 **PASS** |

### Test Count Reconciliation

$$\text{Total Discovered Tests} = \text{Baseline (Phases 1–12)} + \text{Phase 13 Validation} + \text{Phase 14 Deployment} = 227 + 19 + 20 = \mathbf{266}$$

- **Baseline Core Engine (227 tests)**: Foundation (11), Synthetic Environment (10), ML Forecasting (9), Digital Twin (11), Scenario Engine (17), Final Audit (45), Optimizer Core (23), Resilience Engine (34), Policy Engine (25), REST API (21), Edge Intelligence (11), Decision Trace (10).
- **Phase 13 Scientific Validation Suite (19 tests)**: Out-of-sample pinball loss, horizon evaluations, conformal calibration, baseline benchmarks, causality audit, Tree SHAP additivity, optimizer fair comparisons, 5/5 resilience invariants, offline safety proof, closed-loop reproducibility replay, cold archive lifecycle, latency profile, evidence table, boundary invariants, quantile taxonomy integrity, resilience vocabulary lock, twin physical tolerances, sample denominator proofs.
- **Phase 14 Deployment & Integration Suite (20 tests)**: Hierarchical settings resolution, sensitive credential masking, Open-Meteo adapter ingest, NCPOR format transformation, polar physical domain bounds enforcement ($-90^\circ\text{C}$ to $+30^\circ\text{C}$, wind $\le 85\text{ m/s}$, solar $\le 1400\text{ W/m}^2$, non-finite rejection), temporal causality checks, strict 6-tier provenance lock (rejection of `LIVE`, `API`, `REAL-TIME`), provider failure graceful fallback, data freshness degradation, disaggregated health endpoints (`/health`, `/ready`, `/health/providers`, `/health/physical`, `/health/engines`), security headers injection (HSTS, CSP, nosniff, X-Frame-Options), payload limit protection (HTTP 413 on $>10\text{MB}$), operator approval boundary enforcement.

---

## 2. End-to-End Architectural Pipeline & Authority Ownership

Every stage of Polaris-EMS adheres to strict single-authority ownership. No downstream module usurps or duplicates upstream logic:

```mermaid
flowchart TD
    EXT["EXTERNAL REALITY BRIDGE (Phase 14)<br/>Provider Adapters & Polar Physical Bounds Validation"] -.-> D
    D["1. SENSORS & TELEMETRY<br/>NCPOR Telemetry & Station Profiles"] --> F["2. PREDICT (Phase 3 ML)<br/>XGBoost Quantiles (P10, P50, P90, P95)"]
    F --> S["3. STRESS TEST (Phase 5 Scenario Engine)<br/>14 Polar Extreme Presets"]
    S --> O["4. DECIDE (Phase 6 Microgrid Optimizer)<br/>Sole Optimization Authority: Pyomo + HiGHS MILP"]
    O --> T["5. SIMULATE (Phase 4 Digital Twin)<br/>Sole Physical Authority: Electrical, Thermal, Battery, Fuel"]
    T --> R["6. ASSESS RESILIENCE (Phase 7 Resilience Engine)<br/>9 Quantitative Dimensions & Survival Horizons"]
    R --> P["7. GOVERN (Phase 8 Policy Engine)<br/>8 Priority Tiers, Hard Invariants & Hysteresis"]
    P --> E["8. OPERATE AT THE EDGE (Phase 11 Edge Engine)<br/>Telemetry Ingest, Load Shedding, Fallback Posture"]
    E --> DT["9. AUDIT & EXPLAIN (Phase 12 Decision Trace)<br/>Deterministic Lineage DAG & 'Why?' Explainer"]
    DT --> V["10. VALIDATE (Phase 13 Benchmark)<br/>Calibration, Tree SHAP, Replay Reproduction"]
    V --> PROD["11. PRODUCT & DEPLOY (Phase 14 Packaging)<br/>Operator Boundary, Disaggregated Health, Observability"]
```

### Frozen Authority Boundaries

- **Phase 3 (Forecasting Authority)**: Sole ML predictive model. Employs conformal quantile regression on load, solar, and wind predicting quantiles $\{P_{10}, P_{50}, P_{90}, P_{95}\}$ with nominal 80% central prediction interval $[P_{10}, P_{90}]$.
- **Phase 4 (Physical Authority)**: Sole digital twin simulator. Governs electrical power balance (deviation tolerance $\le 10^{-4}\text{ kW} = 0.1\text{ W}$), building envelope thermodynamics ($T_{\text{indoor}} \ge 12.0^\circ\text{C}$), electrochemical battery degradation, and diesel consumption curves.
- **Phase 5 (Stress Testing Authority)**: Sole what-if scenario perturbation engine. 14 locked polar storm scenarios in `ScenarioRegistry`.
- **Phase 6 (Optimization Authority)**: **Sole mathematical optimizer** (`Pyomo` + `HiGHS`). Zero optimization logic permitted in API or UI. Strictly enforces 30%–40% spinning reserve margin. Distinguishes `EXACT_OPTIMAL` from `MIP_GAP_OPTIMAL`.
- **Phase 7 (Resilience Authority)**: Sole resilience evaluator. Computes 9-dimensional resilience scores (0–100 scale) and subsystem survival horizons ($h$). Strict vocabulary: `SAFE`, `WATCH`, `AT_RISK`, `THREATENED`, `CRITICAL`, `RECOVERY`.
- **Phase 8 (Governance Authority)**: Sole policy authority. Enforces life-safety priority (P1–P8) and hysteresis deadbands.
- **Phase 9 (Integration Authority)**: FastAPI backend service with structured error contracts and request correlation tracking (`X-Request-ID`).
- **Phase 10 (Presentation Authority)**: Mission Control frontend with zero physics equations and strict provenance rendering.
- **Phase 11 (Edge Authority)**: Autonomous field device intelligence, priority load shedding, and store-and-forward buffer synchronization.
- **Phase 12 (Auditability Authority)**: Immutable decision traces, lineage DAG generation, and deterministic explainability.
- **Phase 13 (Scientific Benchmark Authority)**: Statistical validation, Tree SHAP explainability, and closed-loop reproducibility replay.
- **Phase 14 (Deployment & Integration Authority)**: Sole deployment, external reality adapter, and runtime observability wrapper. Wraps the frozen pipeline without duplicating or altering any upstream decision-making. Enforces provider fallbacks, polar bounds validation, disaggregated health, and operator supervisory review boundaries.

---

## 3. The 10 Operational Mission-Control Workspaces

The Polaris-EMS frontend provides 10 dedicated operational workspaces:

### 1. Fleet & Station Overview ([OverviewView.tsx](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/views/OverviewView.tsx))
- **Dynamic Fleet Telemetry**: Live station switching between **Bharati** (240 kW aggregate diesel, 3 gensets), **Maitri** (187.5 kW, 3 gensets), and **Himadri** (90 kW, 2 gensets) with zero hardcoded specs.
- **System Health & Resilience Matrix**: Immediate visibility of composite resilience score, operational policy directives, and active threat warnings.
- **Subsystem Telemetry Badges**: High-contrast, WCAG-compliant status badges with explicit state text (`SAFE`, `WATCH`, `THREATENED`, `CRITICAL`).

### 2. Probabilistic Forecast Explorer ([ForecastView.tsx](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/views/ForecastView.tsx))
- **Multi-Target Forecasting**: On-demand conformal quantile predictions ($P_{10}, P_{50}, P_{90}, P_{95}$) with nominal 80% central interval $[P_{10}, P_{90}]$ for electrical load, solar PV generation, and wind turbine generation.
- **Horizon Switching**: Instant toggle between **48h tactical operational horizon** and **168h strategic weekly horizon**.
- **Physics-Informed Bounds**: Load decomposition separating baseline thermal losses from human-driven scientific loads.

### 3. Computational Energy Digital Twin ([EnergyTwinView.tsx](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/views/EnergyTwinView.tsx))
- **Coupled 4-Domain Physics**:
  - **Electrical**: Power balance ($\le 0.1\text{ W}$ tolerance), bus voltage stability, and unserved energy accounting.
  - **Thermal**: First-principles building heat loss and indoor temperature envelope ($T_{\text{indoor}} \ge 12.0^\circ\text{C}$).
  - **Battery**: Electrochemical state-of-charge (SOC), cold-temperature capacity derating, and anti-churn rules.
  - **Diesel Fuel**: Non-linear generator fuel curves and day-tank depletion tracking.

### 4. Stress Scenario & What-If Studio ([ScenariosView.tsx](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/views/ScenariosView.tsx))
- **14 Authoritative Locked Polar Scenarios**:
  `NORMAL_BASELINE`, `CLOUDY_CONDITIONS`, `HEAVY_CLOUD_LOW_IRRADIANCE`, `HIGH_WIND`, `BLIZZARD`, `EXTREME_COLD`, `LOW_DAYLIGHT`, `POLAR_NIGHT`, `SOLAR_GENERATION_FAILURE`, `WIND_GENERATION_FAILURE`, `BATTERY_DEGRADATION`, `FUEL_RESUPPLY_DELAY`, `COMBINED_POLAR_STRESS`, and `CUSTOM`.
- **Comparative Impact Matrix**: Immediate delta computations against baseline for unserved energy ($\Delta \text{kWh}$), excess diesel consumed ($\Delta \text{L}$), and minimum battery SOC reached.

### 5. Microgrid Optimizer Dispatch ([OptimizationView.tsx](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/views/OptimizationView.tsx))
- **HiGHS Rolling MILP**: Rigorous mixed-integer linear programming dispatch with verified solver optimality tiers (`EXACT_OPTIMAL` or `MIP_GAP_OPTIMAL`).
- **3 Optimization Modes**: `EXPECTED` (median cost optimal), `CONSERVATIVE` (hedged against load spikes), `SCENARIO_ROBUST` (multi-scenario contingency robust).
- **Closed-Loop Twin Replay**: Every optimizer schedule is re-simulated in the Digital Twin to verify physical feasibility before dispatch approval.

### 6. Resilience & Survival Horizon Assessment ([ResilienceView.tsx](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/views/ResilienceView.tsx))
- **9 Quantitative Dimensions**: Radar breakdown spanning Energy Adequacy, Critical Load Resilience, Thermal Resilience, Generation Headroom, Storage Health, Fuel Endurance, Logistics Buffer, Renewable Penetration, and Recovery Potential.
- **Subsystem Survival Horizons**: Independent calculation of hours until failure: Battery ($h$), Thermal ($h$), Fuel ($h$), and Critical Life Safety ($h$).
- **Advisory Recovery Pathways**: Prioritized, actionable operator recovery interventions with zero frontend re-ranking.

### 7. Operational Policy & Governance ([PolicyView.tsx](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/views/PolicyView.tsx))
- **8-Level Priority Hierarchy**:
  - **P1**: Critical Life Safety (Habitation & life-support power)
  - **P2**: Critical Load Protection (Freeze-protection heat tracing, satcoms)
  - **P3**: Generation Reserve Protection (Standby genset spin reserve)
  - **P4**: Thermal Safety (Building envelope heating prioritization)
  - **P5**: Fuel / Resupply Protection (Strategic stock rationing)
  - **P6**: Storage Protection (Battery SOC reserve & cold derating defense)
  - **P7**: Noncritical Curtailment / Recovery Stabilization
  - **P8**: Monitoring & Supervisory Observation
- **Hysteresis Deadbands**: Stateful prevention of rapid cycling on generator start/stop and load shedding triggers.

### 8. Device Intelligence & Field Resilience ([EdgeView.tsx](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/views/EdgeView.tsx))
- **Fleet Device Inventory**: Comprehensive catalog of generators, inverters, batteries, and heat tracing circuits across all stations.
- **Autonomous Load Shedding**: Real-time shedding plan calculation based on priority classes during generation deficits.
- **Store-and-Forward Buffer**: Resilient telemetry caching during satcom blackouts with automatic reconciliation on reconnect.
- **Fallback Postures**: Autonomous operational modes (`WAIT_FOR_BACKEND_DECISION`, `LOCAL_EDGE_FALLBACK`, `ISOLATED_EMERGENCY`).

### 9. End-to-End Decision Trace & Explainability ([DecisionTraceView.tsx](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/views/DecisionTraceView.tsx))
- **Machine-Readable Trace ID**: Format `DT-YYYYMMDD-<STATION>-<HEX6>` uniquely tracking each pipeline execution.
- **Lineage DAG**: Interactive visual graph displaying execution path across all 7 pipeline stages.
- **Epistemic Tier Distinctions**:
  - `COMPUTED`: Optimizer mathematical solutions
  - `VALIDATED`: Digital twin physical simulation checks
  - `ESTIMATED`: Conformal ML forecasts & resilience indices
  - `ADVISORY`: Operational policy recommendations
- **Deterministic Explainer**: Factual "Why did Polaris-EMS decide this?" narrative generated without LLM hallucination.
- **Comparative Decision Delta**: Side-by-side delta between any two trace runs.
- **Canonical Export**: One-click download of full trace in JSON or CSV summary format.

### 10. Scientific Validation & Model Benchmarking ([ValidationView.tsx](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/views/ValidationView.tsx))
- **Forecast Model Validation**: Pinball loss, CRPS calibration, and baseline comparison tables (XGBoost vs Persistence vs Climatology).
- **Leakage & Temporal Audit**: Verification of strict chronological train/test splitting and zero target leakage.
- **Tree SHAP Explainability**: Feature importance attributions for temperature, wind speed, solar irradiance, and hour of day. Labeled strictly as `MODEL CONTRIBUTION ONLY — NOT PHYSICAL CAUSATION`.
- **Reproducibility Replay**: Re-execution of recorded decision traces with closed-loop numerical comparison against original results (`IDENTICAL`, $\Delta=0.0000$).
- **Component Latency Profiling**: Empirical runtime latency distributions across inference, optimization, twin simulation, and trace persistence.

---

## 4. Strict 6-Tier Provenance Taxonomy

Every single metric, card, table, and chart in the user interface renders an explicit provenance tag to prevent misinterpreting synthetic or simulated values for physical sensor readings:

```
[REAL]        -> Verified NCPOR AWS / NPDC polar research station telemetry
[CONFIGURED]  -> Manufacturer nameplate ratings, fuel tank sizes, generator ratings
[ASSUMED]     -> Stated engineering approximations (building heat transfer U-values)
[SYNTHETIC]   -> Physics-informed base environment generation
[FORECAST]    -> Calibrated ML model quantiles (P10, P50, P90, P95)
[SIMULATED]   -> Digital Twin continuous simulation & optimizer dispatch trajectories
```

> [!IMPORTANT]
> The codebase enforces an architectural boundary prohibiting fabricated 7th tiers (`LIVE`, `REAL-TIME`, `OPTIMIZED`, `API`). Any such tag triggers lint, test, and validation failure.
> Furthermore, Polaris-EMS explicitly documents that the current deployment has **zero connected physical polar SCADA telemetry**; all evaluated benchmarks represent synthetic environment generation and physical digital twin simulations.

---

## 5. Independent Empirical Validation & Reconciliation Findings

Polaris-EMS underwent an exhaustive pre-freeze reconciliation audit against raw machine artifacts:

1. **Quantile Topology Verified**: Phase 3 models strictly produce $\{P_{10}, P_{50}, P_{90}, P_{95}\}$. The nominal 80% central prediction interval is $[P_{10}, P_{90}]$. References to individual $P_{05}$ and $P_{80}$ quantiles have been excised across all documentation, APIs, and reports.
2. **Authoritative Forecast Metrics**: Out-of-sample test split MAEs ($N=4,214$): **Bharati 24h load = 7.579 kW**, **Maitri = 9.547 kW**, **Himadri = 3.332 kW**. These are distinguished from validation split scores ($N=1,911$, Bharati = 2.042 kW).
3. **Exact Sample Count Proof**: 57 evaluated points across 3 stations $\times$ (7 load horizons + 6 solar + 6 wind) = $19 \times 3 = 57$ tuples. Fleet average MAE is **3.55 kW**.
4. **Disturbance Regime Counts**: Scenario Registry contains **14 locked scenarios**; the Phase 13 regime benchmark evaluated **8 disturbance regimes** across 3 stations $\times$ 3 targets = **72 evaluations**.
5. **Conformal Uncertainty Calibration**: 84.3% empirical coverage for the nominal 80% central interval with zero quantile crossing violations.
6. **Digital Twin Feasibility**: Closed-loop physical validation achieved **83.3% pass rate** ($5/6$ compliant schedules; $1$ caught low-temperature battery derating under severe blizzard conditions).
7. **Reserve-Constrained Optimizer Trade-Off**: The optimizer uses more diesel than naive baselines (e.g., 322.4 L vs 113.7 L) to strictly enforce the **30%–40% spinning reserve margin** and maintain indoor thermal comfort ($T_{\text{indoor}} \ge 12.0^\circ\text{C}$), whereas unconstrained baselines violated safety reserves.
8. **Resilience Vocabulary Integrity**: All states strictly match `ResilienceStateEnum` (`SAFE`, `WATCH`, `AT_RISK`, `THREATENED`, `CRITICAL`, `RECOVERY`). Non-existent state `SECURE` has been prohibited repository-wide.
9. **Performance Terminology**: Replaced overstated labels with evidence-based terminology ("low-latency operational responsiveness", "interactive response"). Prohibited "hard real-time control" in the absence of hardware deadline guarantees.

---

## 6. Enterprise Hardening & Boundary Invariants

1. **Security & Secrets**:
   - Zero hardcoded secrets, API tokens, or credentials in source code.
   - [`.env.example`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/.env.example) documented with all environment variables.
   - Zero committed `.env` files in git repository.
2. **Architectural Isolation**:
   - `Pyomo` and `highspy` imports are restricted strictly to [`backend/optimizer/`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/backend/optimizer/).
   - Microgrid physics equations are restricted strictly to [`backend/twin/`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/backend/twin/).
   - Zero physics equations exist in the React frontend.
3. **Observability & Error Handling**:
   - Request correlation middleware injects unique `X-Request-ID` and timing header `X-Process-Time` on every HTTP request.
   - Structured JSON error responses (`ErrorResponse`) with machine-readable error codes (`STATION_NOT_FOUND`, `VALIDATION_ERROR`, `OPTIMIZER_ERROR`).
   - Zero raw python traceback leakage in 500 error responses.
4. **Configuration Centralization**:
   - All station specs, device fleets, policy thresholds, and optimizer weights live in centralized JSON schemas under [`configs/`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/configs/).

---

## 7. Phase 14: Deployment, External Integration & Productization Architecture

Phase 14 establishes a hardened production wrapper around the frozen computational authorities, ensuring Polaris-EMS is deployable, externally integrable, observable, and demonstration-ready:

### Workstream A: Containerized Deployment & Packaging
- **Multi-Stage Container**: [`deployment/Dockerfile`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/deployment/Dockerfile) compiles the React frontend (`node:20-alpine`), copies production assets into a hardened Python 3.12 slim runtime, and executes under an unprivileged user (`polarisuser:polarisgroup`).
- **Orchestration**: [`deployment/docker-compose.yml`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/deployment/docker-compose.yml) configures memory limits (2GB), CPU allocations (2 cores), health checks (`/health/ready`), and an Nginx reverse proxy (`deployment/nginx.conf`) routing `/api` and `/health` requests with SSL termination readiness.
- **Graceful Lifecycle**: FastAPI `@asynccontextmanager` lifespan handler manages safe startup and clean shutdown of file handles and cache directories with zero deprecation warnings.

### Workstream B: Hierarchical Configuration
- **Structured Pydantic Model**: [`backend/config/settings.py`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/backend/config/settings.py) implements `PolarisSettings` with nested sub-models: `ApplicationSettings`, `SecuritySettings`, `ExternalProviderSettings`, `DeploymentSettings`, and `ProductSettings`.
- **Credential Masking**: Sensitive tokens (API keys, secret keys) are redacted in representations and audits (`mask_sensitive()`), ensuring zero leakage in logs or client-facing responses.
- **Environment Reference**: [`.env.example`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/.env.example) documents 28 typed environment variables across all subsystems.

### Workstream C: External Reality Bridge
- **Provider-Agnostic Adapter Pattern**: [`backend/integrations/`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/backend/integrations/) introduces `AbstractBaseProviderAdapter` implemented by:
  - `OpenMeteoAdapter`: Global polar numerical weather prediction ingestion.
  - `NcporFormatAdapter`: Standardized Indian Antarctic/Arctic CSV and JSON telemetry import.
  - `FileSpoolerAdapter`: Air-gapped offline file drop integration.
- **Polar Physical Bounds Validation**: [`backend/integrations/validation.py`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/backend/integrations/validation.py) validates inputs against polar physical domains:
  - Temperature: $[-90.0^\circ\text{C}, +30.0^\circ\text{C}]$
  - Wind Speed: $[0.0\text{ m/s}, 85.0\text{ m/s}]$
  - Solar Irradiance: $[0.0\text{ W/m}^2, 1400.0\text{ W/m}^2]$
  - Rejects non-finite values (NaN, Inf) and enforces strict temporal causality ($t_{\text{observation}} \le t_{\text{current}} + \Delta_{\text{tol}}$).
- **Safe Fallback & Quarantine**: Invalid or failing external feeds are automatically quarantined without crashing the pipeline, falling back to the verified synthetic/configured data baseline while alerting operators of degraded integration status.

### Workstream D & E: Observability & Security Hardening
- **Security Headers Middleware**: Injects `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, and `X-Frame-Options: DENY` on every HTTP response.
- **Payload Limiting**: `PayloadLimitMiddleware` enforces a strict 10MB maximum request size, returning structured HTTP 413 responses for oversized payloads.
- **Structured Observability**: `/api/observability/metrics` provides runtime inference and optimizer latencies; `/api/observability/audit` reports deployment security posture and masked configuration status.

### Workstream F & G: Frontend Productization & Operator Approval Boundary
- **Operator Review Banner**: [`frontend/src/components/common/OperatorApprovalBanner.tsx`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/components/common/OperatorApprovalBanner.tsx) makes explicit that optimizer dispatches are advisory and require human supervisory authorization before field execution.
- **Epistemic Disclaimers**: [`frontend/src/components/layout/Header.tsx`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/frontend/src/components/layout/Header.tsx) renders production branding, environment indicators (`PRODUCTION_SIMULATION`), and explicit disclaimers: `SCADA: SIMULATION ONLY (ZERO PHYSICAL TELEMETRY)`.
- **Strict Provenance Display**: Guarantees all operational surfaces render only the authoritative 6 provenance tags (`REAL`, `CONFIGURED`, `ASSUMED`, `SYNTHETIC`, `FORECAST`, `SIMULATED`).

### Workstream H & I: Disaggregated Deployment Health Model
Polaris-EMS strictly separates 5 independent operational concepts:
1. **Application Health** (`/health`): Is the FastAPI HTTP worker responsive?
2. **Readiness** (`/ready` or `/health/ready`): Can the ML, solver, and twin pipeline execute?
3. **Provider Health** (`/health/providers`): Are external feeds connected and fresh?
4. **Physical Connectivity** (`/health/physical`): Truthfully reports `DISCONNECTED` (zero physical SCADA connection).
5. **Computational Engines** (`/health/engines`): Status of HiGHS solver, XGBoost inference, and Digital Twin.

### Workstream J: Deterministic Demonstration Hardening
- [`scripts/run_phase14_production_demo.py`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/scripts/run_phase14_production_demo.py) executes a 6-step end-to-end demonstration verifying disaggregated health, reality bridge validation, ML forecasting, HiGHS optimization, closed-loop twin validation, and operator approval lifecycle.

---

## 8. How to Run, Test, and Verify Locally

### 1. Launch Services (Local Development)
```powershell
# Start Backend FastAPI Server
.venv\Scripts\python.exe -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000

# Start Frontend Mission Control
cd frontend
npm run dev
# Dashboard opens at http://127.0.0.1:3000
```

### 2. Containerized Deployment (Production)
```bash
# Build and run complete stack via Docker Compose
docker compose -f deployment/docker-compose.yml up -d --build

# Verify health status
curl -i http://localhost/health/ready
```

### 3. Run Test Suites
```powershell
# Full Backend Regression Suite (266 tests: 227 baseline + 19 Phase 13 + 20 Phase 14)
.venv\Scripts\python.exe -m pytest tests/

# Phase 14 Deployment & External Integrations Suite (20 tests)
.venv\Scripts\python.exe -m pytest tests/test_phase14_deployment.py

# Frontend Vitest Suite (12 tests)
cd frontend
npm test -- --run

# Frontend TypeScript & Bundle Verification (0 errors)
cd frontend
npm run build
```

### 4. Run Automated Runtime Quality & Consistency Gates
```powershell
# Phase 14 Production & Deployment Demonstration (6 steps)
.venv\Scripts\python.exe scripts/run_phase14_production_demo.py

# Phase 13 Final Consistency & Freeze Gate (12 checks)
.venv\Scripts\python.exe scripts/verify_phase13_consistency.py

# Production Readiness & Static Hardening Audit (26 checks)
.venv\Scripts\python.exe scripts/verify_production_readiness.py

# Phase 10 Runtime & Fleet Audit (13 gates)
.venv\Scripts\python.exe scripts/verify_phase10_runtime.py

# Phase 11 Edge & Device Intelligence Audit (10 gates)
.venv\Scripts\python.exe scripts/verify_phase11_runtime.py

# Phase 12 Decision Trace & Explainability Audit (11 gates)
.venv\Scripts\python.exe scripts/verify_phase12_runtime.py

# Phase 13 Scientific Validation & Benchmarking Audit (14 gates)
.venv\Scripts\python.exe scripts/verify_phase13_runtime.py

# Phase 13 Temporal Causality & Data Leakage Audit (14 gates)
.venv\Scripts\python.exe scripts/verify_phase13_leakage.py

# Phase 13 Master End-to-End Fleet Demonstration (7 steps)
.venv\Scripts\python.exe scripts/run_phase13_demo.py

# Export Phase 13 Scientific Benchmark & Evidence Reports (15 reports)
.venv\Scripts\python.exe scripts/export_phase13_reports.py
```

---

## 9. Final Freeze Governance & Next Authorized Stage

- **Phases 1–13 Operational Baseline**: Permanently Complete & Frozen (`PHASE_13_FROZEN`).
- **Phase 14 Freeze Status**: 🟢 **`PHASE_14_FROZEN`** (Deployment, External Data Integration, Productization & Demonstration Hardening)
- **Project Canonical Status**: 🟢 **`PHASES_1_14_COMPLETE`**
- **Canonical Freeze Timestamp**: `2026-09-24T22:28:00+05:30` (UTC `2026-09-24T16:58:00Z`)
- **Freeze Commit / Hash**: `227c44e47a03c3521a45dca685e8dd4897c9b45e` *(Canonical freeze commit; post-freeze documentation synchronization at HEAD `1ef85297fe336b1830f965fde70e4abd1609b116`; audited in [PHASE14_METADATA_RECONCILIATION.md](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/PHASE14_METADATA_RECONCILIATION.md))*
- **Phase 14 Test Verification**: **20/20 Phase 14 tests PASS** | **266/266 Total Pytest tests PASS (100%)** | **12/12 Frontend tests PASS** | **Production build clean (0 errors)** | **All 7 runtime audits PASS** | **Phase 14 Demo 6/6 PASS**
- **Deployment Container Smoke Test**: `CONTAINER_SMOKE_TEST = NOT_EXECUTED` *(Docker engine/CLI not installed in current host environment; Dockerfile, docker-compose.yml, and Nginx reverse proxy verified structurally and syntactically)*
- **Python Runtime Compatibility**: Development runtime verified as **Python 3.13.7**; production container targets **Python 3.12-slim** (`deployment/Dockerfile`).
- **Remaining Documented Limitations (Preserved Truthfully)**:
  1. **Zero Connected Physical Polar SCADA Telemetry**: The system operates with physics-calibrated synthetic weather/load inputs and simulated digital twin responses; no live hardware connection to Bharati, Maitri, or Himadri is established. The physical health status truthfully returns `DISCONNECTED`.
  2. **Advisory / Supervised Physical Actuation**: Downstream physical actuator dispatch requires human supervisor review or local edge policy approval. The product enforces an explicit operator approval boundary.
  3. **External Data Feeds are Optional & Resilient**: When external reality providers (Open-Meteo, NCPOR) are unavailable, rate-limited, or stale, Polaris-EMS safely quarantines them and falls back to configured baselines without interruption.
  4. **Local Compressed Trace Archival**: Decision traces are archived in local gzip-compressed storage with SHA-256 integrity checks; enterprise cloud object storage is pluggable but unconfigured.
  5. **Solver Latency Envelope**: 48h Pyomo/HiGHS MILP optimization solves within $1.8\text{--}2.5\text{ seconds}$, designed for operational dispatch cycles rather than sub-millisecond inverter pulse control.
- **Next Authorized Stage**: 🛑 **`PHASE_15_NOT_STARTED`** (Halted at the freeze boundary. No Phase 15 work permitted without explicit authorization).


