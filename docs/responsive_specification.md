# POLARIS-EMS — RESPONSIVE LAYOUT SPECIFICATION

**Document ID:** SPEC-RESPONSIVE-20260925  
**Version:** 1.0.0-MULTI-DEVICE  
**Status:** CANONICAL & IMPLEMENTED  

---

## 1. DESIGN BREAKPOINTS

Polaris-EMS is engineered for mission-critical operation across five distinct device classes:

| Class | Width Range | Target Environment |
| :--- | :--- | :--- |
| **Mobile** | `< 640px` | Handheld field telemetry inspection during exterior station checks |
| **Tablet** | `640px – 1023px` | Portable generator room tablet or bridge clipboard |
| **Laptop** | `1024px – 1439px` | Expedition engineer workstation or field laptop |
| **Desktop** | `1440px – 1919px` | Bharati / Maitri main control room multi-display console |
| **Large Desktop** | `1920px+` | Wall-mounted command center overview display |

---

## 2. ADAPTIVE LAYOUT BEHAVIOR BY DEVICE CLASS

### 2.1 Mobile (`< 640px`)
* **Philosophy:** Triage & immediate operational decision first. Do NOT simply stack desktop cards into an endless vertical scroll.
* **Masthead:** Collapses station selector into an understated dropdown; hides secondary UTC clocks.
* **Global Status Strip:** Retains station name, system condition badge, and net critical load. Hides raw coordinate text.
* **Navigation:** Numbered index transforms into a horizontal scroll rail with active copper underline.
* **Overview:** Displays the Mission Narrative, System Condition, and the 3 Core Metrics. Secondary telemetry and causal graphs collapse behind "Inspect Evidence" drill-downs.
* **Decision Ribbon:** Nodes convert to an interactive horizontal scroll strip.
* **Tables:** Tables collapse to primary identifying column + status badge + drill-down disclosure chevron.

### 2.2 Tablet (`640px – 1023px`)
* **Philosophy:** Field operational workbench.
* **Navigation:** Numbered index fits cleanly across two rows or scrollable rail.
* **Grid:** 6-column effective grid. Primary cards split 2x2.
* **Charts:** Main balance vector and forecast charts scale width to 100% with touch-friendly scrubber nodes.
* **Evidence Drawer:** Slides up from bottom sheet (60% viewport height) rather than right rail.

### 2.3 Laptop (`1024px – 1439px`)
* **Philosophy:** Engineering analysis & schedule review.
* **Grid:** 12-column standard grid. Max canvas width: 1280px.
* **Split Panels:** Two-column asymmetric layouts (7 columns narrative/charts + 5 columns analytical ledger/evidence).
* **Evidence Drawer:** Slides from right edge (440px fixed width) overlaying the canvas without obscuring primary charts.

### 2.4 Desktop (`1440px – 1919px`) — *PRIMARY DESIGN TARGET*
* **Philosophy:** Editorial command center.
* **Grid:** 12-column expanded grid. Max canvas width: 1520px with generous margins.
* **Visual Composition:** Asymmetric editorial sheets, full horizontal Decision Ribbon, simultaneous visibility of Level 1 (narrative), Level 2 (KPI cards), and Level 3 (charts).

### 2.5 Large Desktop (`1920px+`)
* **Philosophy:** Central polar mission room display wall.
* **Grid:** Maximum container width locked to 1680px centered with balanced negative space to prevent excessive eye travel across ultra-wide monitors.
* **Visual Polish:** High-DPI font antialiasing and fine hairlines remain crisp.

---

## 3. TOUCH & POINTER TARGET STANDARDS

* Touch targets on touch devices (mobile/tablet) maintain a minimum active hit area of 44×44px.
* Keyboard navigation provides visible 2px burnished copper focus rings (`outline: 2px solid #B45309; outline-offset: 2px`).
