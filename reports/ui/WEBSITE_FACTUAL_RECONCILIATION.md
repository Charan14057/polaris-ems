# POLARIS-EMS — WEBSITE FACTUAL & TECHNICAL RECONCILIATION
**Audit Date:** 2026-09-27  
**Auditor:** Polaris Core Engineering Team  
**Compliance Standard:** ISO / Polar Engineering Epistemic Verification  
**Enforced Canonical Provenance Tiers:** REAL | CONFIGURED | ASSUMED | SYNTHETIC | FORECAST | SIMULATED

---

## Provenance Grounding Priority
1. Actual Backend Implementation
2. Actual Frontend Implementation
3. Authoritative Station Configuration
4. Current Test Suite Results (374 backend tests, 36 frontend tests passing)
5. Historical Reports / Documentation

---

## Visible Claims Reconciliation Matrix

| UI TEXT / CLAIM | SOURCE FILE | BACKEND SOURCE | ACTUAL VALUE / BEHAVIOR | PROVENANCE | VERIFIED? | ACTION TAKEN |
|:---|:---|:---|:---|:---|:---|:---|
| **" Autopilot for polar microgrids\** | QuickOrientationModal.tsx | N/A | Advisory decision-support system, not autonomous physical actuator | CONFIGURED | VERIFIED | **CHANGED:** Replaced with \intelligent advisory mission control / automated advisory system\. |
| **\Guaranteed continuous life-support heating\** | QuickOrientationModal.tsx | ackend/policy/ruleset_engine.py | Strictly prioritizes P1 Life Safety in mathematical solver; cannot physically guarantee if fuel/energy depleted | CONFIGURED | VERIFIED | **CHANGED:** Replaced with \prioritizes continuous life-support heating\. |
| **\Life support circuit guaranteed dispatch override\** | DecisionRibbon.tsx | ackend/policy/ruleset_engine.py | Lexicographical policy directive \succ P_2$ overrides secondary loads | CONFIGURED | VERIFIED | **CHANGED:** Replaced with \priority dispatch override\. |
| **\Conformal coverage 80% guaranteed\** | ForecastView.tsx | ackend/ml/uncertainty/coverage_validator.py | Conformal prediction calibrates non-conformity scores targeting 80% empirical validity | FORECAST | VERIFIED | **CHANGED:** Replaced with \80% empirical validity target\. |
| **\Live Station Telemetry\ / \Live SCADA\** | Legacy UI references | ackend/api/routes.py | Hardware air-gap enforced: PHYSICAL_CONNECTIVITY = DISCONNECTED | SIMULATED | VERIFIED | **CHANGED:** Replaced with \LIVE SIMULATION ACTIVE\ with explicit air-gap indicator. |
| **Bharati 3D Geometry** | TwinCanvas3D.tsx, spatialProfiles3D.ts | Authoritative station architectural layouts | Elevated multi-deck structure on steel stilts, aerodynamic profile, fuel farm & water context | CONFIGURED | VERIFIED | **KEEP & REFINED:** Labeled \CONFIGURED / REPRESENTATIVE\. Never claimed exact BIM. |
| **Maitri 3D Geometry** | TwinCanvas3D.tsx, spatialProfiles3D.ts | Authoritative station architectural layouts | Living Blocks A & B, central heated pipeline spine, Priyadarshini Lake water pumping station | CONFIGURED | VERIFIED | **KEEP & REFINED:** Distinct oasis bedrock layout. Labeled \CONFIGURED / REPRESENTATIVE\. |
| **Himadri 3D Geometry** | TwinCanvas3D.tsx, spatialProfiles3D.ts | Ny-Ålesund research station layout | Two-storey lab & living quarters connected to settlement microgrid & district heating | CONFIGURED | VERIFIED | **KEEP & REFINED:** Avoids false standalone diesel representation. |
| **Power Flow Line Width / Direction** | TwinCanvas3D.tsx | TwinViewModel.powerSummary | Derived from actual computed kW values (line thickness) and generation/battery states | SIMULATED | VERIFIED | **VERIFIED:** Zero Math.sin() fake generation. Kirchhoff conserved. |
| **AUTO Mode Action** | TwinOperatingModeControl.tsx | ackend/optimization/milp_solver.py | Computes Phase 6 MILP advisory; requires simulated operator approval before twin state changes | SIMULATED | VERIFIED | **VERIFIED:** Replaced autonomous execution claims with \Approval Required\. |
| **MANUAL Mode Action** | TwinOperatingModeControl.tsx | ackend/twin/physics_engine.py | Simulates generator posture or load shed request and recalculates TwinState | SIMULATED | VERIFIED | **VERIFIED:** Functional simulation with verified Kirchhoff state update. |
| **Decision Trace Lineage DAG** | DecisionTraceView.tsx | allbackTraces.ts & backend API | 7-stage deterministic DAG with reason codes and delta calculation | CONFIGURED / SIMULATED | VERIFIED | **VERIFIED:** Fixed infinite render loop; verified offline and live trace loads. |
| **Kirchhoff Node Conservation** | TwinSummaryStrip.tsx, EnergyTwinView.tsx | ackend/twin/physics_engine.py | Residual \|err\| < 1e-4 kW across 400V 3-phase bus | SIMULATED | VERIFIED | **VERIFIED:** Exact energy balance verified in tests. |

---

## Summary of Changes
1. **Eliminated all unsupported terminology:** Removed \autopilot\, \guaranteed power\, \exact BIM\, \autonomous physical control\, and \live SCADA\.
2. **Standardized on verified canonical provenance:** Every telemetry value, forecast band, and policy directive explicitly displays its true tier (REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, or SIMULATED).
3. **Confirmed Physical Air-Gap:** All views explicitly state PHYSICAL_CONNECTIVITY = DISCONNECTED to prevent misleading operational stakeholders.
