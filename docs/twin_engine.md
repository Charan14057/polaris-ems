# POLARIS-EMS — SPATIAL DIGITAL TWIN ENGINE SPECIFICATION
## Phase 18 Architecture, Data Flow, and Epistemic Invariants

---

## 1. Executive Summary & Purpose

The **Spatial Digital Twin Engine** (Phase 18) provides a top-down operational spatial visualization, source-to-load electrical flow animation, 24-hour simulation replay, and interactive equipment inspection platform for polar microgrids at **Bharati**, **Maitri**, and **Himadri** research stations.

### Fundamental Architectural Invariant
The Spatial Digital Twin Engine is **strictly a presentation, spatial mapping, and user interaction layer**.
- **Phase 4 Computational TwinEngine is Authoritative**: All thermal physics, battery equations, diesel/fuel curves, renewable generation estimates, electrical balance invariants, and resilience equations are computed exclusively by backend authorities (`backend/twin/twin_engine.py`, `backend/twin/state.py`).
- **No Duplicated Physics**: The frontend never calculates independent state, modifies physical constraints, or invents energy balances.
- **Strict Epistemic Truth**: The engine explicitly displays `PHYSICAL_CONNECTIVITY = DISCONNECTED`, `PHYSICAL_SCADA_LINK = FALSE`, and `SIMULATION AIR-GAP ENFORCED`. Telemetry is labeled `SIMULATED` (or `CONFIGURED`/`FORECAST`), preventing misleading claims of real-time polar field connectivity.

---

## 2. Architecture & Data Flow

```text
       Authoritative Backend Authorities
       ┌───────────────────────────────┐
       │   backend/twin/twin_engine.py  │  (Thermal, Battery, Diesel, Generation,
       │   backend/twin/state.py        │   Resilience, and Kirchhoff Physics)
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │   TwinAPIAdapter (Phase 18)   │  (Read-only API facade: queries profiles,
       │   backend/api/adapters/twin... │   instantiates TwinState, runs replay)
       └──────────────┬────────────────┘
                      │ GET /api/v1/twin/spatial/{station_id}
                      │ POST /api/v1/twin/trajectory
                      ▼
       ┌───────────────────────────────┐
       │      Frontend API Client      │  (frontend/src/api/endpoints.ts)
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │      buildTwinViewModel       │  (Pure transformation: maps physical TwinState,
       │ (frontend/.../buildTwinVM.ts) │   trajectory steps, and spatial profiles)
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │                  Spatial Digital Twin Canvas                │
       │  ┌───────────────────────┐   ┌───────────────────────────┐  │
       │  │ TwinSummaryStrip      │   │ TwinInspector (2-Layer)   │  │
       │  │ (Plain Language + VM) │   │ (Non-Tech + Specs + Evid) │  │
       │  ├───────────────────────┴───┴───────────────────────────┤  │
       │  │ Master SVG Drafting Canvas                            │  │
       │  │ • TwinZones (Architectural rooms & load badges)       │  │
       │  │ • TwinFlowLayer (Passive wireways + dynamic flows)    │  │
       │  │ • TwinNodes (Sources, 400V Bus, Sub-DBs, Devices)     │  │
       │  │ • TwinJunctions (Conductor vertices & bus splits)     │  │
       │  │ • TwinFaultLayer (Localized soft hazard washes)       │  │
       │  │ • TwinMinimap (Floating viewport locator)             │  │
       │  ├───────────────────────────────────────────────────────┤  │
       │  │ TwinTimeline (24h scrubber, speed 1x-10x, markers)    │  │
       │  └───────────────────────────────────────────────────────┘  │
       └─────────────────────────────────────────────────────────────┘
```

---

## 3. Power Flow Semantics & Non-Renewable Flow Rule

The canvas renders electrical conduits with semantic coloring derived directly from the current Twin trajectory state:

| Flow State | Semantic Color | Palette Token | Physical Meaning |
| :--- | :--- | :--- | :--- |
| **RENEWABLE** | Deep Teal (`#0F766E`) | `teal` | Pure solar or wind power supplying feeders. Zero diesel burned. |
| **BATTERY** | Glacial Ice (`#0284C7`) | `ice` | BESS discharging to the main bus or charging from clean surplus. |
| **NON_RENEWABLE** | Burnished Copper (`#B45309`) | `copper` | Diesel generator active (`P_diesel > 0.05 kW`). Line carries alert status. |
| **DORMANT** | Muted Slate (`#CBD5E1`) | `stone` | De-energized or idle feeder (`P == 0 kW`). |
| **FAULT** | Danger Crimson (`#DC2626`) | `red-600` | Tripped or faulted branch breaker with animated pulse. |

### The Non-Renewable Flow Rule (Prompt Section 12)
Power flow line coloring is never toggled by arbitrary UI switches. If the current trajectory step indicates active diesel generation, all downstream feeder lines carrying generator contribution automatically transition to **Burnished Copper** (`NON_RENEWABLE`). When diesel gensets throttle to zero, lines seamlessly revert to **Deep Teal** (`RENEWABLE`).

---

## 4. Key Interactive Capabilities

1. **"Trace My Power" (Signature Interaction)**:
   - Selecting any station appliance (e.g., Habitat HVAC Life Support) highlights its upstream electrical lineage:
     `Device Node → Branch Edge → Sub-DB Bus → Feeder Edge → Main 400V Bus → Active Sources (Solar/Wind/Diesel/BESS)`
   - Unrelated circuits and equipment are softly dimmed (opacity 15%), providing immediate visual clarity.
2. **"Trace Impact"**:
   - Selecting a generation source or faulted component traces downstream effects through distribution panels to all affected loads and zones.
3. **24-Hour / 48-Hour Replay Controller**:
   - Interactive scrubber, play/pause, single-step forward/backward, and speed multipliers (1x, 2x, 5x, 10x).
   - Powered by smooth `requestAnimationFrame` loops consuming pre-computed trajectory steps from the authoritative engine.
4. **Two-Layer Equipment Inspector**:
   - **Layer 1 (Operational)**: Plain-language operational narrative answering *What this does*, *Current state*, and *Why it matters*.
   - **Layer 2 (Engineering)**: Detailed technical specifications (Circuit ID, 400V 3-Phase, Rated kW, Derived Current, Priority Rank, Evidence Record link).
5. **Station Switching**:
   - Seamlessly transitions between **Bharati**, **Maitri**, and **Himadri**. Each station loads its unique spatial schematic, device inventory, voltage rating, and Twin trajectory with zero stale data leakage and automatic viewport reset.
