# Polaris-EMS: Polar Energy Management & Resilience System
**SIH Problem Statement**: SIH26061 — AI-Driven Smart Energy Management System for Polar Research Stations  
**Status**: 🟢 `PHASES_1_16_FROZEN` | `PHASE_17_RELEASE_READY` | `POLARIS_EMS_FINAL_RELEASE_READY` | `NEXT_ENGINEERING_STAGE = NONE`  
**Core Philosophy**: Predict → Simulate → Stress Test → Optimize → Protect → Preserve  

[![CI / Pytest Suite](https://img.shields.io/badge/pytest-366%20passed-brightgreen?logo=pytest)](tests)
[![Frontend Vitest](https://img.shields.io/badge/vitest-12%20passed-success?logo=vitest)](frontend)
[![Phase Status](https://img.shields.io/badge/Lifecycle-PHASE__17__RELEASE__READY-blue)](docs/master_walkthrough.md)
[![Zero-Real-Grid-Breach](https://img.shields.io/badge/Air--Gap-100%25%20DISCONNECTED-red)](reports/phase17/PHASE17_EPISTEMIC_BOUNDARY_REPORT.md)
[![Provenance Strict](https://img.shields.io/badge/Provenance-6%20Locked%20Tiers-blueviolet)](backend/core/provenance.py)
[![Docker Multi-Stage](https://img.shields.io/badge/Container-Docker%20Hardened-2496ED?logo=docker)](deployment/Dockerfile)

---

## 📌 Executive Summary

**Polaris-EMS** is an enterprise-grade Polar Energy Management & Resilience System engineered for extreme polar environments down to **-50°C**. Developed in the 2026 project context for **SIH Problem Statement SIH26061**, Polaris-EMS manages electrical, thermal, battery, and fuel systems for **Indian Polar Research Stations**:
- **Bharati Station** (69°S, Larsemann Hills, East Antarctica)
- **Maitri Station** (70°S, Schirmacher Oasis, East Antarctica)
- **Himadri Station** (79°N, Ny-Ålesund, Svalbard, Arctic)

Polar grids face steep operational challenges: severe wind volatility, complete absence of solar generation during months of polar night, high solar irradiance during midnight sun, diesel generator freezing risks, rapid battery capacity degradation in sub-zero temperatures, and prolonged communications blackouts. Polaris-EMS provides an end-to-end, multi-stage resilience architecture designed to protect critical life-support loads and support continuous operation under stressed, black-sky scenarios.

---

## 🏛 System Architecture & Authoritative Phase Ownership

Polaris-EMS adheres to strict contract-first boundaries and single-authority phase ownership:

```text
Predict → Simulate → Stress Test → Optimize → Protect → Preserve
```

| Phase | Subsystem | Domain / Authority Ownership |
|:---:|:---|:---|
| **Phase 1** | Data Foundation | Historical station dataset schemas, physical units, sensor normalization |
| **Phase 2** | Synthetic Environment | Physics-informed synthetic polar energy dataset generation |
| **Phase 3** | **Predict** | ML forecasting: Physics-informed load decomposition + XGBoost residual forecaster, solar PV & wind turbine models, calibrated conformal uncertainty ($P_{10}, P_{50}, P_{90}, P_{95}$) with central interval $P_{10}–P_{90}$ |
| **Phase 4** | **Simulate** | Computational Energy Digital Twin: Physics-based electrical power balance, building thermal dynamics, battery electrochemical state transitions, diesel fuel consumption |
| **Phase 5** | **Stress Test** | Scenario & What-If Engine: 14 canonical polar stress scenarios (Blizzard, Polar Night, Extreme Cold, Generator Outage, Fuel Resupply Delay) |
| **Phase 6** | **Optimize** | Risk-Aware Dispatch Optimizer: Multi-horizon rolling constrained MILP (Pyomo + HiGHS) with resupply-anchored survival constraints and flexible load shifting |
| **Phase 7** | Assess Resilience | Resilience State Machine: 9-dimensional resilience radar, multi-horizon survival horizons, state precedence (Normal, Watch, Threatened, Critical, Recovery) |
| **Phase 8** | Policy / Governance | Operational Governance: 8-level priority hierarchy (Life Safety P1 $\to$ Deferrable Research P8), supervisory override, hysteresis statefulness |
| **Phase 9** | API / Integration | FastAPI gateway, asynchronous telemetry contracts, REST endpoints, CORS, security headers |
| **Phase 10** | Mission Control UI | React 18 + Vite + TypeScript dashboard, Vitest test suite, operators' telemetry views |
| **Phase 11** | Device / Edge Intelligence | Autonomous edge execution cycle, local persistence, offline failover, ring-buffered ingestion |
| **Phase 12** | Decision Trace | Explainable "Why did Polaris-EMS do this?" trace, W3C TraceContext DAG lineage |
| **Phase 13** | Scientific Validation | Conformal calibration audits, Tree SHAP additivity, cold archive lifecycle, fair optimizer benchmarks |
| **Phase 14** | Deployment / Productization | Multi-stage non-root Docker (`polarisuser` UID 10001), Docker Compose, Nginx reverse proxy, Open-Meteo & NCPOR adapters |
| **Phase 15** | Operational Validation | Reality drift monitoring, quarantine circuit breaker, epistemic safeguards, feed completeness tracking |
| **Phase 16** | Field / HIL Validation | Abstracted `DeviceAdapter` hierarchy (`Simulator`, `Emulator`, `HIL`, `Lab`), actuation safety boundary, chaos fault injection |
| **Phase 17** | Final Release & Demonstration | 14-stage automated master demonstration, reproducibility verification, final submission hardening |

---

## 🔒 Epistemic Boundary Declaration

> ### ⚠️ STRICT OPERATIONAL DECLARATION
> - **PHYSICAL_CONNECTIVITY**: `DISCONNECTED`
> - **PHYSICAL_SCADA_LINK**: `FALSE`
> - **PHYSICAL_VALIDATION**: `NOT_AVAILABLE`
>
> All telemetry, sensor feeds, field actuation sequences, and grid interconnects in this repository operate under strictly simulated, emulated, or lab-bench virtual interfaces. No live commercial or military power grid, high-voltage battery bank, or physical diesel switchgear is connected or actuated.
>
> - **Simulation ≠ physical validation**
> - **HIL ≠ field deployment**
> - **Emulator ≠ live telemetry**
> - **Planning ≠ physical actuation**

### Immutable 6-Tier Provenance Contract
Every data point in Polaris-EMS is strictly assigned one of the 6 canonical provenance levels:
1. `REAL`: Direct sensor log playback from historical polar station logs.
2. `CONFIGURED`: Explicit engineering constants defined in configuration specs.
3. `ASSUMED`: Physics-grounded assumptions (e.g. ambient thermal insulation factors).
4. `SYNTHETIC`: Mathematically generated operational scenarios and perturbations.
5. `FORECAST`: Machine learning predictions with probabilistic uncertainty bounds.
6. `SIMULATED`: Dynamic physical models computed during digital twin and edge iterations.

*Any data labeled with unapproved tiers (e.g. `LIVE`, `REAL_TIME`, `API`, `HIL`, `LAB`, `EMULATOR`, `OPTIMIZED`, `DERIVED`) is rejected at the serialization layer. `HIL`, `Emulator`, `Simulator`, and `Lab` are interface environment classifications, not data provenance tiers.*

---

## 📂 Repository Structure

```text
polaris-ems/
├── backend/
│   ├── api/                 # FastAPI REST application, routes, schemas & CORS
│   ├── core/                # Provenance contracts, settings & telemetry schemas
│   ├── data/                # Data connectors, station profiles & synthetic engine
│   ├── edge/                # Edge engine, fault injection, telemetry ingestion & adapters
│   │   ├── adapters/        # DeviceAdapter (Simulator, Emulator, HIL, Lab) & Registry
│   │   ├── actuation.py     # Actuation controller & physical disconnector interlock
│   │   ├── engine.py        # Autonomous edge resilience engine
│   │   ├── fault_injection.py # Chaos engineering fault injection harness
│   │   ├── telemetry_ingestion.py # Ring-buffered telemetry ingestion with provenance
│   │   └── trace_integration.py   # W3C distributed tracing propagator
│   ├── integrations/        # External meteorological & station telemetry adapters
│   ├── ml/                  # ML forecasting pipelines, feature extractors & conformal models
│   ├── optimization/        # Multi-horizon rolling MILP optimizer & degradation models
│   └── tests/               # Backend module-level unit tests
├── configs/                 # Station hardware profiles, asset ratings & operational limits
├── datasets/                # Historical & synthetic polar operational datasets (Bharati, Maitri, Himadri)
├── deployment/              # Dockerfile, docker-compose.yml, nginx.conf
├── docs/                    # Architectural specifications, phase walkthroughs & guides
│   ├── master_walkthrough.md # Master System Walkthrough (Phases 1–17)
│   └── phase16_walkthrough.md# Field & HIL Device Adapter Integration Guide
├── frontend/                # React 18 + TypeScript + Vite + Vitest mission-control UI
│   ├── src/                 # Views, components, hooks, API client
│   │   └── views/FieldHILValidationView.tsx # Field / HIL validation interface
│   └── dist/                # Production static web application bundle
├── models/                  # Serialized ONNX / PyTorch model weights & calibration metadata
├── reports/                 # Formal phase freeze audits, verification benchmarks & traces
│   ├── phase16/             # Phase 16 Field / HIL freeze, implementation & reliability reports
│   ├── phase17/             # Phase 17 Final release audit, reproducibility & demo results
│   └── traces/              # Immutable W3C decision trace JSON archives
├── scripts/                 # CLI tools, data generators, runtime audits & final demonstration
│   ├── final_demo.py        # Phase 17 comprehensive 14-stage demonstration
│   └── phase16_demo.py      # Phase 16 HIL validation lifecycle demonstration
├── tests/                   # Pytest test suite (366 passing tests across Phases 1–16)
│   └── test_phase16_field_validation.py # Phase 16 field test suite (32 tests)
├── .env.example             # Environment configuration template
├── requirements.txt         # Pinned Python root dependencies
└── README.md                # System overview and entry point
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) Docker and Docker Compose

### 2. Setup Environment
```bash
# Clone the repository
git clone https://github.com/Charan14057/polaris-ems.git
cd polaris-ems

# Setup Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Automated Final Master Demonstration
Run the deterministic 14-stage end-to-end system validation:
```bash
python scripts/final_demo.py
```
This executes the full pipeline: station profile resolution, adapter discovery, ML forecasting ($P_{10}..P_{95}$), scenario perturbation, rolling MILP optimization, digital twin replay, resilience radar evaluation, policy governance, edge intelligence, chaos fault injection, state reconciliation, actuation safety boundary enforcement, decision trace DAG emission, and epistemic boundary verification.

### 4. Running Backend & Frontend Locally
```bash
# Terminal 1: Backend API
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend Dashboard
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) to access the Polaris-EMS control center.

---

## 🧪 Verification & Test Suite

The system is rigorously validated by **366 automated Python tests** and **12 frontend Vitest tests**:

```bash
# Run full backend test suite
pytest -q

# Run Phase 16 Field / HIL validation suite specifically
pytest tests/test_phase16_field_validation.py -v

# Run Frontend test suite and production build
cd frontend
npm test
npm run build
```

### Verification Scorecard Matrix
| Phase / Subsystem | Scope | Test Suite | Test Count | Status |
|:---|:---|:---|:---:|:---:|
| **Baseline Core (Phases 1–12)** | Data, ML, Twin, Scenarios, Optimizer, Resilience, Policy, API, Edge, Trace | `tests/test_phase*.py` | 227 | 🟢 **PASS** |
| **Phase 13** | Scientific Validation, Conformal Calibration, Benchmark Audits | `tests/test_phase13_*.py` | 19 | 🟢 **PASS** |
| **Phase 14** | Deployment Hardening, External Integrations & Boundaries | `tests/test_phase14_*.py` | 20 | 🟢 **PASS** |
| **Phase 15** | Operational Validation, Reality Drift & Epistemic Safeguards | `tests/test_phase15_*.py` | 22 | 🟢 **PASS** |
| **Phase 16** | Field / HIL Validation, Device Adapters, Fault Injection | `tests/test_phase16_*.py` | 78 | 🟢 **PASS** |
| **Total Backend** | **Full System Pytest Regression Suite** | | **366** | 🟢 **100% PASS** |
| **Frontend** | **React 18 Components & API Client (Vitest)** | `frontend/src/**/*.test.*` | **12** | 🟢 **100% PASS** |
| **Phase 17 Demo** | **14-Stage Master End-to-End Demonstration** | `scripts/final_demo.py` | **14 stages** | 🟢 **100% PASS** |

---

## 📖 Reproducibility Guide

All key reports, logs, and benchmark proofs are maintained under `reports/`:
- [Phase 16 Field / HIL Freeze Report](reports/phase16/PHASE16_FINAL_FREEZE_REPORT.md)
- [Phase 16 Implementation Report](reports/phase16/PHASE16_IMPLEMENTATION_REPORT.md)
- [Phase 16 Validation Report](reports/phase16/PHASE16_VALIDATION_REPORT.md)
- [Phase 16 Reliability Report](reports/phase16/PHASE16_RELIABILITY_REPORT.md)
- [Phase 17 Release Audit Report](reports/phase17/PHASE17_RELEASE_AUDIT.md)
- [Phase 17 Final Validation Report](reports/phase17/PHASE17_FINAL_VALIDATION_REPORT.md)
- [Phase 17 Epistemic Boundary Report](reports/phase17/PHASE17_EPISTEMIC_BOUNDARY_REPORT.md)
- [Phase 17 Reproducibility Report](reports/phase17/PHASE17_REPRODUCIBILITY_REPORT.md)
- [Phase 17 Final Release Report](reports/phase17/PHASE17_FINAL_RELEASE_REPORT.md)
- [Phase 17 Automated Demo Machine-Readable Log](reports/phase17/demo_result.json)

---

## 📄 Documentation
- [Master System Walkthrough (Phases 1–17)](docs/master_walkthrough.md)
- [Phase 16 Field & Device Adapter Integration Guide](docs/phase16_walkthrough.md)

---
<div align="center">
<b>POLARIS-EMS</b> • Smart India Hackathon (SIH26061) • Hardware & Software Co-Design for High-Reliability Polar Grids
</div>
