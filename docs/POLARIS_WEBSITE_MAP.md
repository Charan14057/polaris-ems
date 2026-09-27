# POLARIS-EMS — COMPLETE WEBSITE MAP & NAVIGATION STRUCTURE
**Prompt ID**: 61853 / Phase 18 Final Launch Quality Gate  
**Product**: Polaris EMS — Autonomous Polar Microgrid Optimization & Digital Twin Engine

---

## 1. Global Navigation Hierarchy

`
POLARIS EMS
|
+-- TOP APPLICATION BAR
|   +-- Station Switcher (BHARATI [Default] | MAITRI | HIMADRI)
|   +-- Global Threat Alert Ribbon (Conditional: triggers on active operational threats)
|   +-- Provenance Verification Badge (6 Tiers: REAL / CONFIGURED / ASSUMED / SYNTHETIC / FORECAST / SIMULATED)
|   +-- Epistemic Boundary Notice ('Simulated Environment • No Physical SCADA')
|
+-- OPERATIONS (Primary Operator Workflow)
|   +-- /overview        -> OverviewView: Executive situational awareness & energy balance
|   +-- /energy          -> EnergyTwinView: Flagship 3D Spatial Digital Twin & Power Flow
|   +-- /forecast        -> ForecastView: 48h multi-horizon renewable & load predictions
|   +-- /scenarios       -> ScenariosView: 14 polar stress contingency experiments
|   +-- /optimization    -> OptimizationView: 24h MILP optimal source dispatch schedule
|
+-- SITUATIONAL (Condition & Diagnostics)
|   +-- /resilience      -> ResilienceView: Multi-dimensional survivability & bottleneck analysis
|   +-- /edge            -> EdgeView: Station asset explorer & equipment health register
|   +-- /trace           -> DecisionTraceView: Cryptographic tamper-evident decision audit log
|
+-- ASSURANCE (Verification & Governance)
|   +-- /validation      -> ValidationView: Model benchmarks, accuracy & energy conservation
|
+-- ENGINEERING (Deep System Operations)
    +-- /policy          -> PolicyView: Operational safety rules & priority shedding matrix
    +-- /field_hil       -> FieldHILValidationView: Hardware-in-the-Loop interface topology
    +-- /design_lab      -> DesignLabView: Component design system & UI tokens
`

---

## 2. Interactive Modal & Drawer Sub-Surfaces

1. **Reference <-> Twin Comparison Modal** (ReferenceComparisonModal.tsx)
   - Trigger: REFERENCE <-> TWIN button in 3D Canvas toolbar
   - Layouts: 50/50 Split View, Draggable Wipe Slider, Alpha Opacity Crossfade
   - Content: Authoritative NCPOR architectural survey elevation vs live 3D digital reconstruction snapshot
   - Epistemic Badge: REFERENCE IMAGE ASSET REQUIRED / CONFIGURED / REPRESENTATIVE

2. **Asset Technical Inspector Drawer** (TwinInspector.tsx)
   - Trigger: Raycasting click on any 3D station equipment mesh or circuit node
   - Telemetry: Equipment name, nominal rating, real-time power (kW), operating status, load importance
   - Actions: TRACE POWER (upstream circuit lineage) and TRACE IMPACT (downstream outage consequence)
   - Value Provenance: Canonical provenance tier and calculation owner

3. **Decision Evidence Drawer** (EvidenceDrawer.tsx)
   - Trigger: Clicking any row in the Decision Trace event timeline
   - Telemetry: Trace UUID, timestamp, pipeline stage, triggering inputs, optimizer setpoints, policy rule citations
   - Mathematical Rationale: Natural language explanation and before/after state delta proof

4. **Quick Orientation Guide** (QuickOrientationModal.tsx)
   - Trigger: TopBar orientation/help icon button
   - Content: Explains the polar microgrid digital twin, real-time live simulation session, and air-gap safety boundary
