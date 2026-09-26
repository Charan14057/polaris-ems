# POLARIS-EMS — CURRENT UI SHELL FREEZE SPECIFICATION
**Version:** 1.0.0-phase18-freeze  
**Status:** `CURRENT_UI_SHELL = FROZEN`  
**Date:** 2026-09-26  
**Target Environment:** Polar Microgrid Energy Operations Platform  

---

## 1. Architectural Mandate & Non-Regression Gate

The current frontend shell design, information architecture, navigation topology, and Quiet Industrial aesthetic are formally **LOCKED AND FROZEN**. 

No further redesigns of the application shell, layout structure, color schemes, or typography may take place. Future developments (including Digital Twin enhancements, 3D spatial engines, and scenario expansions) must execute strictly within the bounds of this approved product shell.

```text
================================================================================
SHELL FREEZE VERIFICATION GATE:
CURRENT_UI_SHELL = FROZEN
SIDEBAR_TOPOLOGY = LOCKED
TOPBAR_TOPOLOGY = LOCKED
RESPONSIVE_BREAKPOINTS = LOCKED
AESTHETIC_SYSTEM = QUIET INDUSTRIAL / ARCTIC UTILITY (LOCKED)
================================================================================
```

---

## 2. Accepted Shell Structure

The accepted shell consists of four structural cornerstones:

1. **Collapsible Industrial Navigation Rail (`Sidebar.tsx`)**:
   - Fixed left-aligned navigation drawer.
   - Width: `w-60` (240px) expanded, `w-16` (64px) collapsed.
   - Smooth desktop transition (`transition-all duration-200 ease-in-out`).
   - Grouped visual hierarchy:
     - **Operations**: Overview, Energy (Spatial Twin), Forecast, Scenarios, Dispatch, Resilience.
     - **Decisions**: Decision Engine & Trace Log.
     - **Assurance**: Multi-Domain Validation & Statistical Conformance.
     - **Engineering**: Policy Rules (P1–P8), Field / HIL Integration.
   - Persistent user collapse preference saved via `localStorage` (`polaris_sidebar_collapsed`).

2. **Compact Industrial Top Application Bar (`TopBar.tsx`)**:
   - Fixed height: `h-14` (56px), border-b `border-slate-200`, bg `bg-white/95 backdrop-blur-xs`.
   - Left-aligned mobile hamburger menu trigger (`md:hidden`).
   - Left-aligned station identifier & station switcher dropdown (`BHARATI`, `MAITRI`, `HIMADRI`).
   - Center/Right-aligned global simulation horizon controls (`6h`, `12h`, `24h`, `48h`, `168h`).
   - Connection & physical air-gap status indicator (`AIR-GAP SIMULATION`).
   - Station operational condition badge (`NOMINAL`, `STRESSED`, `DEFICIT`).

3. **Mobile Navigation Suite (`MobileNav.tsx`)**:
   - Fixed bottom tab bar (`h-14`, `z-40`, `md:hidden`) for thumb-friendly navigation across primary operational views (Overview, Energy Twin, Scenarios, Dispatch).
   - Off-canvas overlay drawer on mobile viewports with modal backdrop (`bg-slate-900/40 z-40`).

4. **Unified Root Application Frame (`App.tsx`)**:
   - Provider injection wrapper: `StationProvider` -> `EvidenceProvider` -> `ComprehensionProvider`.
   - Main content viewport with calculated margin offset (`md:ml-60` or `md:ml-16`).
   - Global air-gap disclaimer banner at top of view.
   - Maximum content constraint: `max-w-[1520px] mx-auto`.

---

## 3. Approved Page Dimensions & Responsive Breakpoints

| Breakpoint | Window Width | Sidebar Mode | TopBar Mode | Twin Inspector Mode | Bottom Bar |
|---|---|---|---|---|---|
| **Mobile (`xs`/`sm`)** | `< 768px` | Hidden (Drawer toggleable) | Compact (Hamburger active) | Bottom drawer / Modal overlay | Visible (`h-14`) |
| **Tablet (`md`)** | `768px - 1023px` | Collapsed Rail (`64px`) | Standard (`56px`) | Stacked below canvas | Hidden |
| **Desktop (`lg`/`xl`)** | `>= 1024px` | Expandable (`240px` / `64px`) | Standard (`56px`) | Right-side column (`320px` width) | Hidden |
| **Ultra-Wide (`2xl`)** | `>= 1536px` | Expandable (`240px` / `64px`) | Standard (`56px`) | Right-side column (`320px` width) | Hidden |

---

## 4. Approved Interaction Locations & Control Placements

1. **Station & Context Selection**:
   - Strictly positioned inside `TopBar.tsx`. Never duplicate station selector inside child view canvases.
2. **Global Horizon Controls**:
   - Centrally anchored in `TopBar.tsx` for multi-screen coherence.
3. **Spatial Twin Controls**:
   - **Spatial Canvas (`TwinCanvas.tsx`)**:
     - Viewport zoom, pan, reset controls placed on top-right floating toolbar.
     - View mode toggle (`ARCHITECTURAL` vs `SCHEMATIC` vs `3D SPATIAL`) anchored on top-left toolbar.
     - Device classification filter pills anchored below canvas header.
     - Canvas minimap docked on bottom-right corner.
   - **Twin Replay Rail (`TwinTimeline.tsx`)**:
     - Anchored immediately beneath the spatial canvas.
     - Time display shows simulation clock (`T+hh:00`) alongside UTC timestamp.
     - Play, pause, step-forward, step-backward, reset, and speed multiplier (1x, 2x, 5x, 10x).
     - Discrete event markers for generator transitions, battery thresholds, and weather events.
   - **Device & Asset Inspection (`TwinInspector.tsx`)**:
     - Docked to right side (`w-80`) on desktop viewports.
     - Houses tabbed detail views: Overview, Technical Specs, Circuit Lineage, Trace Power, and Epistemic Provenance.
     - Single-click close affordance (`X`) and keyboard `Escape` handler.

---

## 5. Visual Palette System

- **Base Canvas**: Neutral Cool White / Slate (`bg-slate-50`, `#f8fafc`).
- **Surface Cards & Panels**: Pure White (`bg-white`, `#ffffff`) with subtle hairline border (`border-slate-200`, `#e2e8f0`).
- **Brand & Operational Primary**: Deep Sky / Cobalt (`text-sky-700`, `bg-sky-600`, `#0284c7`).
- **Healthy / Renewable / Sustained**: Muted Emerald (`text-emerald-700`, `bg-emerald-600`, `#059669`).
- **Advisory / Warning / Diesel Active**: Burnished Amber (`text-amber-700`, `bg-amber-600`, `#d97706`).
- **Critical / Fault / Emergency**: Pure Alert Red (`text-rose-700`, `bg-rose-600`, `#e11d48`).
- **Strict Prohibition**: Neon greens, purple glows, pure black SCADA backgrounds, and cyber-aesthetic decorations are forbidden.

---

## 6. Epistemic Provenance Display Mandate

Every operational value rendered within the shell MUST declare its provenance using the canonical 6-tier tag (`<ProvenanceTag />`):
1. `REAL`
2. `CONFIGURED`
3. `ASSUMED`
4. `SYNTHETIC`
5. `FORECAST`
6. `SIMULATED`

Forbidden terms for provenance tiering: `LIVE`, `REAL_TIME`, `HIL`, `LAB`, `EMULATOR`.
Simulation state indicators must strictly read `SIMULATION` or `REAL-TIME SIMULATION`, never claiming live SCADA links.

**APPROVED & CERTIFIED:**
```text
CURRENT_UI_SHELL = FROZEN
POLARIS_SYSTEM_VERSION = 1.0.0
TIMESTAMP = 2026-09-26T21:32:00Z
```
