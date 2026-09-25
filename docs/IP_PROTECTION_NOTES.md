# POLARIS-EMS — INTELLECTUAL PROPERTY & TRADE-SECRET PROTECTION GUIDELINES

**Document ID:** IP-MEMO-20260925  
**Classification:** ARCHITECTURAL GOVERNANCE & LEGAL AUDIT  
**Status:** CANONICAL REFERENCE  

---

## 1. PURPOSE & ARCHITECTURAL BOUNDARY

This document establishes the formal intellectual property (IP), trade-secret, and confidentiality boundary for the Polaris-EMS platform. It identifies proprietary algorithms and formulations that must remain server-side and concealed from public client-side browser bundles, while clarifying what remains presentational and open.

> [!IMPORTANT]
> **Legal Disclaimer:** This document provides technical categorization and architectural boundaries from an engineering perspective. For formal patent filing, trade-secret registry, or statutory copyright decisions, professional intellectual property legal counsel must review this material prior to external release or deployment.

---

## 2. IP CLASSIFICATION TAXONOMY

Polaris-EMS enforces a strict bifurcation between **Client Presentational Interfaces** and **Core Server-Side Computational Engines**:

```text
┌────────────────────────────────────────────────────────┐
│             TIER A: OPEN / PRESENTATIONAL              │
│  (Frontend UI, CSS Tokens, Layouts, Visual Contracts)  │
└───────────────────────────┬────────────────────────────┘
                            │  Restricted Typed JSON API
┌───────────────────────────▼────────────────────────────┐
│      TIER B: PROPRIETARY SERVER-SIDE INTELLIGENCE       │
│ (MILP Formulations, Physics Derivations, Conformal ML) │
└────────────────────────────────────────────────────────┘
```

---

## 3. PROPRIETARY SERVER-SIDE IMPLEMENTATIONS (CORE IP)

The following components represent high-value computational trade secrets and must NEVER be ported, exposed, or leaked into client-side JavaScript bundles:

### 3.1 Mathematical Dispatch Optimization (Phase 6 / backend)
* **Asymmetric Piecewise-Linear Engine Fuel Formulation:** Specific slope-intercept MILP constraints modeling sub-zero diesel generator fuel efficiency curves while preventing wet-stacking.
* **Cold-Weather Battery Degradation Bounds:** Non-linear electrochemical derating constraints integrated into linear inequality solvers.
* **Solver Tuning & Branch-and-Cut Heuristics:** Custom branch-priority orderings and presolve cuts optimized specifically for small-scale polar microgrid topologies.

### 3.2 Predictive Machine Learning & Uncertainty Calibration (Phases 2 & 3 / backend)
* **Temporal Feature Engineering Pipeline:** Proprietary lagged rolling-window transformations ($t-k$ weather features, diurnal solar angle vectors) trained on polar meteorological anomalies.
* **Finite-Sample Conformal Prediction Coverage Algorithms:** Exact non-crossing monotonic quantile calibration routines ensuring $P_{10} \le P_{50} \le P_{90} \le P_{95}$ without empirical quantile inversion.
* **Tree SHAP Additivity Proof Engines:** Server-side Tree SHAP explainer configurations and background reference datasets.

### 3.3 Dynamic Resilience & Survival Horizon Engine (Phase 7 / backend)
* **Multi-Dimensional Survivability Bottleneck Formulation:** Closed-form analytical equations computing exact time-to-breach across electrical, thermal, fuel, and battery storage dimensions.
* **Disturbance Escalation Propagation Models:** Non-linear cascading failure graph models tracing secondary equipment trips.

### 3.4 Future Digital Twin Engine Physics (Phases 4 & 18 / backend)
* **Spatial Circuit Graph & Thermal Flow Mechanics:** Thermodynamic indoor heat-loss models ($UA \Delta T$) paired with hydraulic district-heating fluid dynamics.
* **Device-at-Location Adjacency Algorithms:** Network graph algorithms calculating line losses, voltage sag, and harmonic distortion across harsh sub-zero transmission runs.

---

## 4. PRESENTATIONAL & CLIENT-SIDE BOUNDARY (TIER A)

The frontend codebase (`frontend/`) contains only presentational logic, design tokens, UI components, and visualization containers. It operates exclusively over serialized typed JSON responses:

* **Design Tokens & System:** Color palettes, typography configurations, grid systems, and motion easings are open and unencumbered.
* **Visual Components:** Reusable widgets (Decision Ribbon, Evidence Drawer, Resilience Envelope, Scenario Delta Canvas) render telemetry received from the API and contain no proprietary mathematical solvers.
* **No Client-Side ML:** No machine learning models, weights, training pipelines, or Pyomo optimization formulations are bundled or evaluated in the browser.

---

## 5. AUDIT & RELEASE CHECKLIST

Prior to public repository publishing, demonstrations, or external audits:
1. Verify `frontend/dist/` contains zero embedded `.py` scripts, model weight files (`.pkl`, `.onnx`, `.pt`), or proprietary constant matrices.
2. Confirm all telemetry endpoints communicate via sanitized response schemas defined in `backend/api/schemas/`.
3. Verify that environment variables containing operational API keys or internal server URIs are excluded via `.gitignore`.
4. Ensure no confidential polar station electrical blueprints or classified payload telemetry are stored in unencrypted repository commits.
