# Polaris-EMS: Phase 17 Reproducibility & Evaluator Guide

**System Name:** Polaris-EMS — Polar Energy Management & Resilience System  
**SIH Problem Statement:** SIH26061 — AI-Driven Smart Energy Management System for Polar Research Stations  
**Phase Identity:** Phase 17 — Final Release, Demonstration & Submission Hardening  
**Target Audience:** Independent Evaluators, Jurors, Technical Reviewers  
**Status:** 🟢 **`REPRODUCIBILITY_VERIFIED`**  

---

## 1. Prerequisites & Environment Matrix

Polaris-EMS has been verified on both Windows (PowerShell) and Linux (Ubuntu 22.04 LTS / Debian 12):

| Component | Minimum Version | Tested Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11+ | 3.13.7 / 3.12.3 | Backend API, optimization engines, digital twin, ML |
| **Node.js** | 18.0+ | 20.18.0 | React Mission Control UI build and test execution |
| **npm** | 9.0+ | 10.8.2 | Frontend package manager |
| **Docker** *(Optional)* | 24.0+ | 27.1.1 | Containerized deployment via Docker Compose |

---

## 2. Step-by-Step Clean Reproduction

### Step 1: Clone Repository
```bash
git clone https://github.com/Charan14057/polaris-ems.git
cd polaris-ems
```

### Step 2: Python Environment & Dependencies
```bash
# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# Install backend dependencies (all pinned in requirements.txt)
pip install -r requirements.txt
```

### Step 3: Run Full Backend Test Suite (366 Tests)
```bash
pytest tests/ -v
```
*Expected Outcome: 366 passed in ~5 minutes with 0 errors.*

### Step 4: Run Authoritative Master Demonstration
```bash
python scripts/final_demo.py
```
*Expected Outcome: 14 stages pass in ~2 seconds; machine-readable artifact saved to `reports/phase17/demo_result.json`.*

### Step 5: Frontend Build & Test Verification
```bash
cd frontend
npm install
npm test -- --run
npm run build
```
*Expected Outcome: 12 tests passed; production bundle built cleanly into `frontend/dist` with 0 errors.*

### Step 6: Start Full System Runtime
```bash
# Terminal 1: Start FastAPI Backend
python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000

# Terminal 2: Start Mission Control Frontend
cd frontend
npm run dev
```
Open your browser to:
- **Mission Control UI:** `http://127.0.0.1:3000`
- **FastAPI OpenAPI Docs:** `http://127.0.0.1:8000/docs`
- **Readiness Probe:** `http://127.0.0.1:8000/ready`
- **Physical Boundary Truth:** `http://127.0.0.1:8000/health/physical` (returns `physical_scada_connected: false`)

---

## 3. Deterministic Seed Guarantees

All synthetic environment generators, scenario perturbations, fault injectors, and LightGBM model evaluations utilize fixed deterministic random seeds:
- Synthetic physics seed: `seed=42`
- Fault injector seed: `seed=42`
- LightGBM model inference: deterministic inference graphs
- Solver optimality: exact deterministic simplex/interior point via HiGHS
