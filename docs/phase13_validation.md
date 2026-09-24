# Polaris-EMS: Phase 13 Scientific Validation Specification & Protocol

**System**: Polaris-EMS — Polar Energy Management & Resilience System  
**Problem Statement**: SIH26061 — AI-Driven Smart Energy Management System for Polar Research Stations  
**Phase**: Phase 13 (Validation, Benchmarking, Explainability & Reproducibility Protocol)  

---

## 1. Validation Methodology & Standards

Phase 13 establishes the rigorous evaluation protocols used to substantiate all technical claims across the Polaris-EMS platform. Every metric reported is derived from automated, reproducible scripts executed directly against trained models and validated physical digital twins.

---

## 2. Machine Learning Forecast Evaluation Protocols

### A. Point Forecast Accuracy Metrics
For an actual time series $y_t$ and forecast prediction $\hat{y}_t$ over horizon steps $t = 1, \dots, N$:

1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N} \sum_{t=1}^N |y_t - \hat{y}_t|$$
2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{t=1}^N (y_t - \hat{y}_t)^2}$$
3. **Symmetric Mean Absolute Percentage Error (sMAPE)**:
   $$\text{sMAPE} = \frac{100\%}{N} \sum_{t=1}^N \frac{|y_t - \hat{y}_t|}{(|y_t| + |\hat{y}_t|)/2}$$
4. **Coefficient of Determination ($R^2$)**:
   $$R^2 = 1 - \frac{\sum (y_t - \hat{y}_t)^2}{\sum (y_t - \bar{y})^2}$$
5. **Capacity-Normalized MAE / RMSE**:
   $$\text{NMAE} = \frac{\text{MAE}}{P_{\text{capacity}}} \times 100\%, \quad \text{NRMSE} = \frac{\text{RMSE}}{P_{\text{capacity}}} \times 100\%$$

### B. Standard Baseline Comparisons
All production Physics-Informed XGBoost models are benchmarked directly against four standard baselines:
- **Persistence**: $\hat{y}_{t+k} = y_t$
- **Seasonal Naive (24h)**: $\hat{y}_{t+k} = y_{t+k-24}$
- **Ridge Regression**: L2-regularized linear model trained on identical normalized feature vectors
- **Random Forest**: Uncalibrated 100-tree regression ensemble

### C. Conformal Uncertainty Calibration Protocol
Conformal prediction intervals are constructed via non-conformity scores computed on the dedicated calibration split:
- **Empirical Coverage**:
  $$\text{Coverage}(1 - \alpha) = \frac{1}{N} \sum_{t=1}^N \mathbb{I}\left( y_t \in [\hat{q}_{\alpha/2}, \hat{q}_{1 - \alpha/2}] \right)$$
- **Interval Sharpness**:
  $$\text{Sharpness} = \frac{1}{N} \sum_{t=1}^N (\hat{q}_{1 - \alpha/2, t} - \hat{q}_{\alpha/2, t})$$
- **Quantile Crossing Invariant**:
  $$\sum_{t=1}^N \mathbb{I}(\hat{q}_{10, t} > \hat{q}_{50, t} \lor \hat{q}_{50, t} > \hat{q}_{90, t} \lor \hat{q}_{90, t} > \hat{q}_{95, t}) = 0$$

---

## 3. Formal Data Leakage & Causality Audit Protocol

The automated leakage auditor (`scripts/verify_phase13_leakage.py`) enforces:
1. **Chronological Splitting**:
   $$\max(\text{Train Timestamps}) < \min(\text{Calibration Timestamps}) < \min(\text{Test Timestamps})$$
2. **Causal Lag Construction**:
   $$\text{Feature } x_j(t) = y(t - k) \quad \text{for } k \ge 0$$
   Zero forward-looking offsets ($k < 0$) or centered rolling filters.
3. **Weather Information Horizon**:
   Numerical weather forecast features represent predictions available at origin timestamp $t_0$, preventing future ground-truth contamination.

---

## 4. Native Tree SHAP Explainability Protocol

- **Algorithm**: Exact Tree SHAP polynomial-time algorithm executed via XGBoost native booster API (`booster.predict(dmat, pred_contribs=True)`).
- **Exact Additivity Verification**:
  $$\left| \sum_{i=1}^M \phi_i(x) + \phi_0 - f(x) \right| < 10^{-2}$$
- **Disciplinary Labeling**: All generated reports label feature attributions as:
  `MODEL CONTRIBUTION ONLY — NOT PHYSICAL CAUSATION`

---

## 5. Microgrid Optimizer Benchmarking Protocol

- **Fairness Criterion**: Candidate optimization schedules (`EXPECTED`, `CONSERVATIVE`, `SCENARIO_ROBUST`) and `BASELINE_SIMULATION_DISPATCH` are evaluated from **identical initial physical state** ($S_0$, battery SOC, fuel day-tank level, indoor temperature) and identical exogenous scenario disturbance trajectories.
- **Physical Twin Validation**: Every proposed optimizer schedule is replayed through Phase 4 Computational Digital Twin. A schedule is marked valid if and only if physical continuity, electrical power balance, and thermal safety boundaries are respected throughout the horizon.
- **Optimality Classification**:
  - `EXACT_OPTIMAL`: Relative MIP gap $< 10^{-4}$
  - `MIP_GAP_OPTIMAL`: Relative MIP gap $< 0.05$ (typically $< 1.5\%$)
  - `FEASIBLE`: Sub-optimal admissible solution meeting emergency dispatch criteria

---

## 6. Resilience Stress Progression & Property Invariants

Five formal property invariants are verified to enforce resilience engine integrity:
1. **Capacity Bound**: Generator outage never increases aggregate available generation capacity.
2. **Demand Monotonicity**: Load increase never reduces net required generation.
3. **Irradiance Bound**: Zero irradiance never yields positive solar power.
4. **Degradation Bound**: Cell capacity loss strictly derates usable energy storage.
5. **Logistics Delay**: Resupply delay never produces an earlier fuel replenishment event.

---

## 7. Edge Offline Safety Protocol

Under communication disruption:
1. Central solver invocation is formally blocked (`central_solver_invoked = False`).
2. Edge state transitions deterministically to `SAFE_HOLD` or `PROTECT_CRITICAL_SYSTEMS`.
3. High-frequency telemetry is queued locally in FIFO buffer with bounded memory usage.
4. On reconnection, state reconciliation occurs deterministically without telemetry duplication.

---

## 8. Closed-Loop Decision Trace Reproducibility Protocol

- **Harness**: `ReplayRunner` extracts immutable recorded snapshot inputs from `TraceRecord` and re-executes all 6 computational engines.
- **Classification Categories**:
  - `IDENTICAL`: $|\Delta \text{Objective}| < 10^{-4}$ and matching categorical states.
  - `NUMERICALLY_EQUIVALENT_WITHIN_TOLERANCE`: $|\Delta \text{Objective}| < 0.5$ and matching policy/resilience states.
  - `EXPECTED_NONDETERMINISM`: Minor branch-and-cut solver path differences due to degenerate solution polyhedra; constraints and policy directives remain equivalent.
  - `REPRODUCTION_FAILURE`: Divergent states or constraint violations.
