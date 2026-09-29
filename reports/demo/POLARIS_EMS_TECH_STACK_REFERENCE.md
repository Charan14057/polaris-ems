# POLARIS-EMS — TECHNICAL STACK MASTER INVENTORY
**Release Baseline:** `f425cd4397edd63e99b266c20ab43028be06f286` (origin/main)  
**System Title:** Polar Energy Management & Autonomous Resilience System  
**Classification:** Mission-Critical Polar Microgrid Energy Management System (EMS)  
**Audit Date:** September 2026  

---

## 1. Executive Summary of Tech Stack

Polaris-EMS is built as a decoupled, air-gapped, mission-critical autonomous energy management system engineered for extreme polar environments (Antarctica & High Arctic). The architecture combines a reactive, single-page operator dashboard (React 18 / TypeScript 5 / Three.js PBR 3D / Tailwind CSS) with a high-performance Python 3.13 scientific computing and mathematical optimization backend (FastAPI, Pyomo MILP, HiGHS solver, XGBoost, Scipy, Pandas).

---

## 2. Frontend Technology Stack

| Layer | Technology | Exact Version | Repository Evidence | Purpose & Role |
| :--- | :--- | :--- | :--- | :--- |
| **Framework** | React | `18.3.1` | `frontend/package.json` | Component lifecycle, virtual DOM, context state management. |
| **Runtime / Core** | React DOM | `18.3.1` | `frontend/package.json` | Web DOM rendering and event tree management. |
| **Language** | TypeScript | `5.7.3` | `frontend/package.json` | Strict static typing, discriminated unions, schema enforcement across all UI layers. |
| **Build Tool / Dev Server** | Vite | `6.1.0` | `frontend/package.json` | Lightning-fast HMR dev server, Rollup-based tree-shaken production bundler. |
| **Compiler Plugin** | `@vitejs/plugin-react` | `4.3.4` | `frontend/package.json` | Fast Refresh and JSX AST transformation. |
| **CSS Engine** | Tailwind CSS | `3.4.17` | `frontend/package.json` | Utility-first CSS, custom polar color palette, high-contrast dark industrial surfaces. |
| **CSS Preprocessor** | PostCSS | `8.5.2` | `frontend/package.json` | CSS transformation pipeline, autoprefixer integration. |
| **Vendor Prefixer** | Autoprefixer | `10.4.20` | `frontend/package.json` | Browser engine compatibility rules. |
| **CSS Class Utilities** | `clsx` / `tailwind-merge`| `2.1.1` / `2.6.0` | `frontend/package.json` | Dynamic conditional class merging with conflict resolution. |
| **3D Graphics Engine** | Three.js | `0.186.1` | `frontend/package.json` | Physically-Based Rendering (PBR) 3D Digital Twin, custom shaders, procedural textures. |
| **3D Typings** | `@types/three` | `0.186.0` | `frontend/package.json` | Full TypeScript typings for Three.js scene graph, geometries, materials. |
| **Iconography** | Lucide React | `0.475.0` | `frontend/package.json` | Unified industrial and scientific icon system across all views. |
| **Unit Testing** | Vitest | `3.0.5` | `frontend/package.json` | Native Vite unit testing framework for components and utilities. |
| **DOM Test Harness** | JSDOM | `26.0.0` | `frontend/package.json` | Headless browser DOM environment for Node.js test execution. |
| **Component Testing** | `@testing-library/react` | `16.2.0` | `frontend/package.json` | React component integration tests, user event assertions. |
| **DOM Matchers** | `@testing-library/jest-dom` | `6.6.3` | `frontend/package.json` | Custom jest DOM matchers for Vitest. |
| **Routing Architecture** | Internal Tab Dispatcher | Custom | `frontend/src/App.tsx` | Instantaneous tab state dispatcher (`TabType`), no browser reload, persistent air-gapped state. |

---

## 3. Backend Technology Stack

| Layer | Technology | Exact Version | Repository Evidence | Purpose & Role |
| :--- | :--- | :--- | :--- | :--- |
| **Language Runtime** | Python | `3.13.x` | `requirements.txt`, runtime | High-performance modern asynchronous Python execution environment. |
| **Web API Framework** | FastAPI | `0.141.1` | `pip list`, `backend/api/app.py` | Asynchronous REST API, OpenAPI v3 spec generator, dependency injection. |
| **ASGI Web Server** | Uvicorn | `0.53.0` | `pip list`, `backend/api/app.py` | Production asynchronous event loop and HTTP/1.1 protocol server. |
| **Schema Validation** | Pydantic | `2.13.5` | `pip list`, `backend/api/schemas.py` | High-speed C-extension data validation, serialization, strict type casting. |
| **Configuration** | Pydantic Settings | `2.15.0` | `pip list`, `backend/api/config.py` | Multi-tiered hierarchical settings from JSON profiles and environment variables. |
| **Linear / MILP Modeling**| Pyomo | `6.10.1` | `pip list`, `backend/optimizer/model.py`| Mathematical algebraic modeling language for unit commitment and dispatch. |
| **Mathematical Solver** | HiGHS (`highspy`) | `1.15.1` | `pip list`, `backend/optimizer/solver.py`| State-of-the-art C++ Mixed Integer Linear Programming (MILP) Branch-and-Cut solver. |
| **Scientific Computing** | SciPy | `1.18.1` | `pip list`, `backend/twin/power_balance.py` | Scientific algorithms, numerical integration, statistical distribution functions. |
| **Numerical Computing** | NumPy | `2.5.3` | `pip list`, `backend/ml/uncertainty/` | Multi-dimensional array manipulations, conformal score quantiles, vector math. |
| **Data Analysis** | Pandas | `3.0.6` | `pip list`, `backend/data/` | Time-series indexing, CSV baseline parsing, tabular evidence generation. |
| **Machine Learning Core** | Scikit-Learn | `1.9.1` | `pip list`, `backend/ml/baselines/` | Ridge regression baselines, cross-validation splitters, preprocessing pipelines. |
| **Gradient Boosting ML** | XGBoost | `3.4.1` | `pip list`, `models/registry/` | Quantile regression models (P10, P50, P90, P95) for Load, Solar, and Wind. |
| **Model Persistence** | Joblib | `1.6.0` | `pip list`, `backend/ml/models/` | Serialized model artifact compression and rapid out-of-core loading. |
| **HTTP Client** | HTTPX | `0.28.1` | `pip list`, `backend/api/` | Asynchronous HTTP client for test fixtures and microgrid edge sync. |
| **Legacy Requests** | Requests | `2.34.2` | `pip list`, `backend/edge/` | Synchronous HTTP communication fallback for edge telemetry probes. |
| **Testing Framework** | Pytest | `9.1.1` | `pip list`, `tests/` | Comprehensive test runner executing 436 unit, integration, and physics tests. |

---

## 4. Machine Learning & Forecasting Technology

### 4.1 Architecture & Pipeline
1. **Data Ingestion**: Historical Automatic Weather Station (AWS) records from NCPOR (National Centre for Polar and Ocean Research) for Bharati, Maitri, and Himadri.
2. **Feature Engineering** (`backend/ml/features.py`):
   - **Solar Radiation Geometry**: Solar elevation, azimuth, extraterrestrial solar irradiance, air mass, clear-sky index.
   - **Thermal Lags**: Ambient temperature moving averages (1h, 3h, 6h, 24h), thermal delta rates ($\Delta T / \Delta t$).
   - **Wind Dynamics**: Cube of wind speed ($v^3$ power proxy), wind gust ratios, aerodynamic shear estimates.
   - **Temporal Trigonometrics**: Cyclical sin/cos encodings of hour-of-day, day-of-year, solar polar day/night indicators.
3. **Forecasting Models**:
   - **Load Forecaster**: Multi-horizon XGBoost quantile regressor predicting total station power demand with indoor thermal habitability feedback.
   - **Solar Forecaster**: Hybrid physics-ML model mapping GHI and panel temperature to DC/AC power injection through station-specific PV arrays.
   - **Wind Forecaster**: Aerodynamic power curve modeling with cut-in, rated, and emergency blizzard cut-out (25 m/s) physical thresholds.
4. **Uncertainty Quantification (CQR)** (`backend/ml/uncertainty/conformal_calibrator.py`):
   - **Conformalized Quantile Regression**: Computes non-conformity scores on held-out calibration partitions.
   - **Guaranteed Coverage**: Enforces finite-sample coverage guarantees ($1 - \alpha = 80\%$ and $90\%$).
   - **Monotonicity**: Post-processing guarantees $0 \le P_{10} \le P_{50} \le P_{90} \le P_{95}$ without quantile crossing.

---

## 5. Mathematical Optimization & Dispatch Technology

### 5.1 Formulation
- **Mathematical Class**: Mixed-Integer Linear Programming (MILP) with Unit Commitment (UC) and Economic Dispatch (ED).
- **Modeling Language**: Pyomo 6.10.1 (`backend/optimizer/model.py`).
- **Underlying Solver**: HiGHS 1.15.1 (`appsi_highs` / `highspy`).
- **Optimization Horizon**: 48 hours rolling horizon at 1-hour resolution ($T = 48$).
- **Solver Performance**: Relative MIP Gap = 3% (`mip_gap = 0.03`), Time Limit = 120s (typical solve time 12–45 ms).

### 5.2 Objective Function Terms
$$\min \sum_{t=0}^{T-1} \Big( w_{\text{fuel}} F_t + w_{\text{crit}} P^{\text{unserved}}_{\text{crit},t} + w_{\text{noncrit}} P^{\text{unserved}}_{\text{noncrit},t} + w_{\text{thermal}} s^{\text{temp}}_t + w_{\text{reserve}} s^{\text{res}}_t + w_{\text{bat}} (P^{\text{chg}}_t + P^{\text{dis}}_t) + w_{\text{curt}} P^{\text{curt}}_t + w_{\text{start}} \sum_g v_{g,t} \Big)$$

---

## 6. Digital Twin Physics & Spatial 3D Engine

### 6.1 Spatial 3D Engine
- **Engine**: Three.js v0.186.1 with Physically-Based Rendering (PBR).
- **Materials**: `MeshStandardMaterial` with custom procedural roughness, metalness, and normal maps (`pbrMaterialFactory.ts`).
- **Polar Environment**: Dynamic sky dome with Rayleigh scattering, volumetric blizzard snowfall particle systems, katabatic wind drift, and diesel generator exhaust heat plumes (`polarEnvironment3D.ts`).
- **Station Meshes**: Procedurally constructed architectural models accurately matching Bharati (containerized elevated stilts), Maitri (inland oasis steel trusses), and Himadri (Svalbard Arctic pitched timber building) (`stationMeshBuilders.ts`).

### 6.2 Physics Engines
- **Power Balance**: Non-linear Kirchhoff Current Law balance ($\sum P_{\text{sources}} = \sum P_{\text{sinks}} + P_{\text{losses}}$) with strict conservation check ($\Delta P < 10^{-4}\text{ kW}$).
- **Thermal Habitability Engine**: Lumped capacitance building thermal model:
  $$C_{\text{th}} \frac{dT_{\text{in}}}{dt} = P_{\text{heat}} + Q_{\text{internal}} - UA_{\text{eff}} (T_{\text{in}} - T_{\text{amb}})$$
- **Battery Electrochemical Model**: State of Charge (SOC) tracking with temperature-dependent capacity derating ($0.008/\text{°C}$ below freezing) and asymmetric Coulombic charge/discharge efficiencies ($\eta_{\text{chg}} = 0.96, \eta_{\text{dis}} = 0.96 \implies \eta_{\text{roundtrip}} \approx 0.92$).
- **Diesel Fuel Dynamics**: Piecewise-linear fuel consumption model with idle fuel consumption and specific loading curve ($0.27 - 0.30\text{ L/kWh}$).

---

## 7. Build, Deployment & Runtime Configurations

- **Frontend Production Bundler**: Vite 6.1.0 producing a single-page application bundle (`frontend/dist`) of 358 kB gzipped.
- **Web Server & SPA Rewrites**:
  - `frontend/public/_redirects`: Cloudflare Pages / Netlify SPA rewrite rule (`/* /index.html 200`).
  - `frontend/vercel.json`: Vercel routing configuration with immutable asset cache-control headers (`max-age=31536000, immutable`).
- **Python ASGI Deployment**: Uvicorn running `backend.api.app:app` on port 8000 with lifespan management and graceful shutdown.
- **Unified Single-Port Deployment**: FastAPI optionally serves `frontend/dist` static assets directly when `SERVE_FRONTEND=True`.
