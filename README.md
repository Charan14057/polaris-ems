# Polaris-EMS: Polar Energy Management & Resilience System
**AI-Driven Smart Energy Management System for Polar Research Stations**  
**Status**: LOCKED FOR PRODUCTION  
**Core Philosophy**: Predict → Simulate → Optimize → Protect → Preserve  

---

## 1. System Overview
Polaris-EMS is a mission-critical energy management and resilience system engineered for extreme polar environments. It manages electrical, thermal, battery, and fuel systems for **Indian Polar Research Stations**:
- **Bharati Station** (Larsemann Hills, East Antarctica)
- **Maitri Station** (Schirmacher Oasis, East Antarctica)
- **Himadri Station** (Ny-Ålesund, Svalbard, Arctic)

## 2. Computational Engines
1. **Engine 1 — Prediction Engine (ML)**: Physics-informed load decomposition + XGBoost residual operational forecaster, solar PV & wind turbine models, calibrated conformal uncertainty ($P_{10}, P_{50}, P_{80}, P_{90}, P_{95}$).
2. **Engine 2 — Energy Digital Twin (Computational Simulation)**: Physics-based electrical power balance, building thermal dynamics, battery electrochemical state transitions, diesel fuel consumption, and device continuity horizons.
3. **Engine 3 — Decision / Optimization Engine (MILP)**: Rolling constrained MILP optimization (Pyomo + HiGHS) with resupply-anchored survival constraints and mission-aware flexible load scheduling.

## 3. Data Provenance Contract
Every variable is explicitly classified to ensure total scientific credibility:
- `REAL`: Verified public weather stations (NCPOR AWS / NPDC).
- `CONFIGURED`: Station assets, ratings, device parameters, operational schedules.
- `ASSUMED`: Stated engineering approximations (e.g. building heat loss coefficients).
- `SYNTHETIC`: Physics-informed synthetic load, solar, wind, and battery states.
- `FORECAST`: Machine learning predictions with probabilistic uncertainty bounds.
- `SIMULATED`: Future digital twin trajectories and counterfactual optimizer schedules.

## 4. Repository Structure
```
polaris-ems/
├── backend/
│   ├── app/             # FastAPI REST endpoints & schemas
│   ├── data/            # Connectors, provenance, station profiles, synthetic engine
│   ├── ml/              # Load, solar, wind forecasting & conformal calibration
│   ├── twin/            # Electrical, thermal, battery, fuel, device twin
│   ├── scenarios/       # 13 presets + custom stress transforms
│   ├── optimizer/       # Pyomo/HiGHS rolling MILP optimizer
│   ├── resilience/      # Survival horizon, reserve margin, resilience envelope
│   ├── policy/          # Manual, Auto, Emergency operational policies
│   ├── alerts/          # Threat detection & advisory system
│   └── decision_trace/  # Explainable "Why did Polaris-EMS do this?" trace
├── configs/             # Verified station profiles & asset limits
├── datasets/            # Training, calibration, test datasets
├── models/              # Model artifacts, metadata & calibration curves
├── scripts/             # Data generation & training CLI scripts
├── tests/               # Automated test suite
└── docs/                # Architecture docs & research registry
```

## 5. Production Documentation & Walkthroughs
Detailed operational walkthroughs and audit verification reports:
- [Master System Walkthrough & Current Operational Stage](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/docs/master_walkthrough.md)
- [Phase 12 Decision Trace & Explainability Walkthrough](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/docs/phase12_walkthrough.md)
- [Phase 12 Decision Trace Architecture Specification](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/docs/phase12_architecture.md)
- [Phase 11 Field Resilience & Device Intelligence Walkthrough](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/docs/phase11_walkthrough.md)
- [Phase 11 Field Architecture Specification](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/docs/phase11_architecture.md)
- [Phase 10 Production Integration Walkthrough](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/docs/phase10_walkthrough.md)
- [Phase 12 Runtime Audit Script](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/scripts/verify_phase12_runtime.py)
- [Phase 11 Runtime Audit Script](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/scripts/verify_phase11_runtime.py)
- [Phase 10 Runtime Freeze Audit Script](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/scripts/verify_phase10_runtime.py)

## 6. Execution & Verification Setup
```bash
# 1. Start FastAPI Backend (Port 8000)
.venv\Scripts\activate
python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000

# 2. Start Mission Control Frontend (Port 3000)
cd frontend
npm run dev

# 3. Run Automated Test Suites
pytest tests/ -v                           # Full backend regression suite (227/227 passed)
pytest tests/test_phase12_trace.py -v      # Phase 12 Decision Trace suite (10/10 passed)
pytest tests/test_phase11_edge.py -v       # Phase 11 Edge Resilience suite (11/11 passed)
cd frontend && npm test                    # Frontend Vitest suite (12/12 passed)
cd frontend && npm run build               # Frontend production bundle (0 errors)

# 4. Run Runtime Audits via Reverse Proxy
python scripts/verify_phase12_runtime.py   # Phase 12 trace audit (11/11 gates passed)
python scripts/verify_phase11_runtime.py   # Phase 11 edge audit (10/10 gates passed)
python scripts/verify_phase10_runtime.py   # Phase 10 runtime audit (13/13 gates passed)
```
