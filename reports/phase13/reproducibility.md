# Polaris-EMS: Phase 13 End-to-End Reproducibility Audit Report

**Audit Timestamp**: 2026-09-24T13:57:51.821431+00:00  
**Replay Harness**: `ReplayRunner` (Reruns Forecast $\to$ Scenario $\to$ Optimizer $\to$ Twin Replay $\to$ Resilience $\to$ Policy)  
**Replay Scope**: 5 recorded decision traces re-executed from original snapshot inputs.  

---

## 1. Replay Reproducibility Table

| Decision Trace ID | Station | Classification | Max Abs Δ | Max Rel Δ | Policy Match | Resilience Match | Objective Match |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `DT-20260924-MAITRI-F9A8C4` | MAITRI | `ReproductionCategory.IDENTICAL` | 0.0000 | 0.0000 | PASS | PASS | PASS |
| `DT-20260924-MAITRI-3C26C7` | MAITRI | `ReproductionCategory.IDENTICAL` | 0.0000 | 0.0000 | PASS | PASS | PASS |
| `DT-20260924-MAITRI-36C2DE` | MAITRI | `ReproductionCategory.IDENTICAL` | 0.0000 | 0.0000 | PASS | PASS | PASS |
| `DT-20260924-MAITRI-2C8124` | MAITRI | `ReproductionCategory.IDENTICAL` | 0.0000 | 0.0000 | PASS | PASS | PASS |
| `DT-20260924-HIMADRI-E39672` | HIMADRI | `ReproductionCategory.IDENTICAL` | 0.0000 | 0.0000 | PASS | PASS | PASS |

---

## 2. Classification Criteria
- **IDENTICAL**: Bit-for-bit identical objective values and matching categorical states ($|\Delta| < 10^{-4}$).
- **NUMERICALLY_EQUIVALENT_WITHIN_TOLERANCE**: State classifications match; continuous objective values match within solver tolerance ($|\Delta| < 0.5$).
- **EXPECTED_NONDETERMINISM**: Minor MIP branch-and-cut solver path differences due to degenerate solution polyhedra, but operational policy and physical constraints remain equivalent.
- **REPRODUCTION_FAILURE**: Policy or resilience state divergence.
