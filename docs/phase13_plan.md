# Polaris-EMS: Phase 13 Implementation Plan
## Validation, Benchmarking, Model Explainability & Reproducibility

**SIH Problem Statement**: SIH26061 — AI-Driven Smart Energy Management System for Polar Research Stations  
**Phase**: Phase 13 (Validation, Benchmarking, Explainability & Reproducibility)  
**Baseline**: Phases 1–12 Complete & Frozen (227 backend tests passed, 12 frontend tests passed)  
**Core Purpose**: Prove, measure, explain, and benchmark the existing system without modifying any decision authority.

---

## 1. Non-Negotiable Invariants
1. **Zero New Solvers / Optimizers**: 0 Pyomo models, 0 HiGHS calls. Phase 6 remains the sole optimizer.
2. **Zero New Physics Equations**: Phase 4 Digital Twin remains the sole physical authority.
3. **Zero New Forecasting Models**: Use existing Phase 3 models.
4. **Zero New Policy Logic**: Phase 8 Policy Engine remains the governance authority.
5. **Zero New Resilience Scores**: Phase 7 Resilience Engine remains the resilience authority.
6. **Strict Six-Tier Provenance**: `REAL`, `CONFIGURED`, `ASSUMED`, `SYNTHETIC`, `FORECAST`, `SIMULATED`.
7. **Scientific Objectivity**: No gaming benchmarks, no cherry-picking data, explicit distinction between REAL, SYNTHETIC, SIMULATED, and FORECAST evidence.
8. **Explainability Safety**: Model feature contributions are strictly labelled "MODEL CONTRIBUTION", never "CAUSE". Zero LLM hallucinated explanations.

---

## 2. Work Breakdown Structure

### Step 1: Benchmark Registry & Architecture Setup
- Create `configs/benchmark_registry.json` registering standard benchmark fixtures.
- Define typed schemas in `backend/validation/schema.py`.

### Step 2: ML Forecast Validation & Baselines (Layer A)
- Implement `backend/validation/forecast_validator.py`:
  - Metrics calculation: MAE, RMSE, sMAPE, R2 across 1h, 6h, 12h, 24h, 48h, 168h horizons for all 3 stations.
  - Baselines: Persistence, Seasonal Naive, Ridge, Random Forest vs Production XGBoost.
  - Conformal prediction coverage: P10, P50, P90, P95 (nominal 80% central interval [P10, P90]), interval sharpness, quantile crossings.
  - Regime evaluation: Normal, low solar, high wind, extreme cold, blizzard, polar night.
  - Data leakage audit: chronological split, causal feature availability check.
  - Longitudinal stability analysis.

### Step 3: Model Explainability (Addressing Limitation A)
- Implement `backend/validation/explainability.py`:
  - Native XGBoost Tree SHAP (`booster.predict(dmat, pred_contribs=True)`).
  - Exact Shapley value additivity ($\sum \phi_i + \phi_0 = \hat{y}$).
  - Safe labelling as "MODEL CONTRIBUTION", zero causal overreach.
  - Deterministic and reproducible across executions.

### Step 4: Optimization Benchmarking & Twin Validation (Layer B)
- Implement `backend/validation/optimizer_benchmark.py`:
  - Fair comparison between Baseline Simulation Dispatch and Phase 6 Optimizer (EXPECTED, CONSERVATIVE, SCENARIO_ROBUST).
  - Metrics: Fuel, unserved load, reserve margin, battery terminal SOC, thermal safety, solve time, optimality tier.
  - Validation through Phase 4 Digital Twin replay.

### Step 5: Resilience & Edge Degradation Validation (Layer C)
- Implement `backend/validation/resilience_validator.py` and `backend/validation/edge_validator.py`:
  - Monotonicity & property-based physical invariant tests.
  - Edge degradation modes: device stale, device failure, degraded link, offline edge, buffer growth, sync.
  - Offline safety proof: zero central optimizer invocation during offline hold.

### Step 6: End-to-End Reproducibility (Layer D)
- Implement `backend/validation/reproducibility.py`:
  - `ReplayRunner`: Takes a recorded `decision_trace_id`, pulls recorded input state, reruns pipeline engines, and categorizes reproduction: `IDENTICAL`, `NUMERICALLY_EQUIVALENT_WITHIN_TOLERANCE`, `EXPECTED_NONDETERMINISM`, `REPRODUCTION_FAILURE`.

### Step 7: Trace Archival Store (Addressing Limitation B)
- Implement `backend/trace/archive.py`:
  - Pluggable `TraceArchive` interface (`save_active`, `archive`, `retrieve_archived`, `list_archived`, `status`).
  - `LocalFileTraceArchive` with compressed JSON (`.json.gz`) rotation preventing disk exhaustion while preserving history.

### Step 8: Scientific Validation Reports & Evidence Package
- Generate `reports/phase13/`:
  - `forecast_benchmark.json`, `forecast_benchmark.csv`
  - `optimizer_benchmark.json`, `optimizer_benchmark.csv`
  - `resilience_validation.json`
  - `edge_validation.json`
  - `replay_validation.json`
  - `explainability_report.json`
  - `performance_benchmark.json`
  - `phase13_summary.md`
  - `SIH_TECHNICAL_EVIDENCE.md`

### Step 9: REST API Additions
- Mount `backend/api/routes/validation.py` at `/api/v1/validation`.

### Step 10: Mission Control Frontend Addition
- Implement `frontend/src/views/ValidationView.tsx` and link in Navbar.
- Types in `frontend/src/api/types.ts` and client methods in `frontend/src/api/endpoints.ts`.

### Step 11: Automated Test Suite & Runtime Audits
- Write `tests/test_phase13_validation.py`.
- Write `scripts/verify_phase13_runtime.py` and `scripts/run_phase13_demo.py`.
- Run full regression suites: backend, frontend, Phase 10/11/12/13 runtime gates.

### Step 12: Final Documentation & Freeze
- Write `docs/phase13_architecture.md`, `docs/phase13_validation.md`, `docs/phase13_walkthrough.md`.
- Update `README.md`.
- Issue final report and mark `PHASE_13_FROZEN`.
