# POLARIS-EMS DESIGN SYSTEM SPECIFICATION

**Canonical Reference Version:** 2.0.0-MISSION-CONTROL  
**Aesthetic Baseline:** Editorial Control Room (Copper × Ice)  
**Environmental Posture:** Light-First Polar Mission Operations  

---

## 1. DESIGN PHILOSOPHY & CORE AESTHETIC

Polaris-EMS rejects standard SaaS templates, neon cyber aesthetics, dark SCADA clones, and decorative AI dashboards. The design system is founded on five interlocking principles:

```text
EDITORIAL CLARITY
+
INDUSTRIAL PRECISION
+
INDIAN MATERIAL SENSIBILITY
+
POLAR CALM
+
MISSION-CRITICAL INFORMATION HIERARCHY
```

### Expression of Cultural Identity
Indian material identity is expressed through genuine material textures, confident technical typography, restrained warmth, architectural balance, and mineral pigments (burnished copper, terracotta warmth, lapis lazuli/indigo depth, and mineral charcoal). It strictly avoids decorative nationalism, flags, mandala motifs, or superficial ornamentation.

### Expression of Polar Identity
The polar environment demands high-contrast legibility, calming warm light surfaces that reduce eye fatigue during 24-hour polar night shifts, and crystal-clear operational boundaries.

---

## 2. COLOR TOKEN ARCHITECTURE

All colors are systematically organized into semantic tokens. The interface is light-first, eliminating black navigation shells and dark glass walls.

### 2.1 Surface & Ink Tokens

| Semantic Token | Hex Value | Role / Usage |
| :--- | :--- | :--- |
| `--color-canvas` | `#FBF9F5` | Base background: Warm Ivory / Chalk |
| `--color-canvas-subtle` | `#F6F3EC` | Secondary background: Parchment sheet |
| `--color-surface` | `#FFFFFF` | Primary card / container surface: Chalk White |
| `--color-surface-raised` | `#FFFFFF` | Elevated dialogs, tooltips, dropdowns |
| `--color-border` | `#DDD6C6` | Neutral divider / bounding rules |
| `--color-border-subtle` | `#EDE8DF` | Secondary hairline division rules |
| `--color-ink-primary` | `#1C1917` | High-contrast mineral charcoal typography |
| `--color-ink-secondary` | `#57534E` | Body text, captions, contextual annotations |
| `--color-ink-muted` | `#78716C` | Metadata, timestamps, inactive labels |
| `--color-ink-inverse` | `#FFFFFF` | Text on saturated badges or buttons |

### 2.2 Accent & Environmental Tokens

| Semantic Token | Hex Value | Role / Usage |
| :--- | :--- | :--- |
| `--color-copper` | `#B45309` | Primary action, focus anchors, weather alerts |
| `--color-copper-soft` | `#FEF3C7` | Soft copper background tint |
| `--color-ice` | `#0284C7` | Glacial Ice: wind generation, secondary telemetry |
| `--color-ice-soft` | `#E0F2FE` | Soft ice background tint |
| `--color-teal` | `#0F766E` | Digital Twin physics replay, balance vector |
| `--color-teal-soft` | `#CCFBF1` | Soft teal background tint |
| `--color-moss` | `#166534` | Life safety load protection, verified states |
| `--color-moss-soft` | `#EBF7F0` | Soft moss background tint |

### 2.3 Operational State Markers

State communication never relies on color alone; every state incorporates textual indicators, accessible contrast (WCAG 2.1 AA), and explicit iconography:

* **SAFE:** `#166534` on `#EBF7F0` with ShieldCheck icon.
* **WATCH:** `#B45309` on `#FEF3C7` with AlertCircle icon.
* **AT_RISK:** `#C2410C` on `#FFEDD5` with AlertTriangle icon.
* **THREATENED:** `#DC2626` on `#FEE2E2` with AlertTriangle icon.
* **CRITICAL:** `#991B1B` on `#FEE2E2` with Flame icon.
* **RECOVERY:** `#0284C7` on `#E0F2FE` with RefreshCw icon.

---

## 3. TYPOGRAPHY SYSTEM

Typography uses a two-layer structure: editorial display serif combined with clean technical sans-serif and tabular monospace numerals.

### 3.1 Type Families
* **Display / Editorial:** *Cormorant Garamond* (or *Instrument Serif*) — used for station headers, mission narratives, and primary operational statements.
* **Interface / Body:** *IBM Plex Sans* (or *Inter*) — used for controls, labels, and analytical prose.
* **Data / Telemetry:** *JetBrains Mono* / *IBM Plex Mono* — tabular numerals (`font-variant-numeric: tabular-nums`) for exact alignment of electrical readings.

### 3.2 Responsive Type Scale

```css
Display XL: clamp(2.5rem, 4vw + 1rem, 3.75rem)
Display L:  clamp(2.0rem, 3vw + 0.8rem, 2.75rem)
Display M:  clamp(1.5rem, 2vw + 0.5rem, 2.0rem)
Heading L:  1.25rem (20px), Semi-bold
Heading M:  1.0rem (16px), Semi-bold
Heading S:  0.875rem (14px), Semi-bold
Body:       0.875rem (14px), Regular, 1.5 line-height
Body Small: 0.75rem (12px), Regular, 1.4 line-height
Caption:    0.6875rem (11px), Monospace
Metric:     clamp(1.25rem, 2vw + 0.5rem, 1.875rem), Tabular numbers
```

---

## 4. LAYOUT & GRID ARCHITECTURE

* **Base Unit:** 8px spacing base (`--spacing-1` = 4px, `--spacing-2` = 8px, `--spacing-4` = 16px, `--spacing-6` = 24px, `--spacing-8` = 32px).
* **Grid:** 12-column desktop grid with a maximum canvas width of 1520px.
* **Surface Treatment:** Thin rules (`1px solid #DDD6C6`), subtle hairline dividers (`#EDE8DF`), tactile paper texture, zero glassmorphism, zero neon glow, restrained box-shadows (`shadow-sm`, `shadow-raised`).

---

## 5. NAVIGATION & STATUS STRIP

### 5.1 Global Status Strip
A single calm top ribbon maintaining situational orientation across all views:
1. Active station selector (`BHARATI` / `MAITRI` / `HIMADRI`).
2. Current system state (`SAFE` / `WATCH` / `CRITICAL`).
3. Total microgrid power demand (kW).
4. Life-support critical load (kW).
5. Spinning reserve margin (%).
6. Epistemic data contract (`LOCKED 6-TIER PROVENANCE`).
7. Physical connection state: `PHYSICAL_CONNECTIVITY = DISCONNECTED`.

### 5.2 Editorial Index Navigation
Organized as a numbered mission index:
* `01 OVERVIEW` — Energy Mission Control & Causal Decision Ribbon.
* `02 FORECAST` — P10/P50/P90/P95 Conformal Quantile Horizon.
* `03 TWIN` — Pre-Twin Spatial Architecture Shell (Implementation Deferred).
* `04 SCENARIOS` — Controlled Disturbance & Perturbation Studio.
* `05 OPTIMIZER` — HiGHS MILP Asymmetric Dispatch & Physics Replay.
* `06 RESILIENCE` — Survival Horizons & Multi-Dimension Envelope.
* `07 POLICY` — P1–P8 Priority Cascade & Anti-Oscillation Hysteresis.
* `08 DEVICES` — Edge Intelligence & Field Telemetry Fleet.
* `09 TRACE` — End-to-End Decision Trace & Lineage DAG.
* `10 VALIDATION` — Empirical Benchmark Suite & Shapley Attributions.
* `11 FIELD / HIL` — Testbed Device Fleet & SCADA Boundary Validation.
* `12 DESIGN LAB` — Design Directions & Aesthetic Evaluation Matrix.

---

## 6. MOTION & ACCESSIBILITY TOKENS

### 6.1 Motion Durations
* Micro feedback: `120ms` ease-out.
* Hover transition: `180ms` ease-in-out.
* Panel disclosure: `240ms` ease-out.
* Drawer transition: `300ms` cubic-bezier(0.16, 1, 0.3, 1).
* Page transition: `350ms` ease-out.

### 6.2 Accessibility Standards (WCAG 2.1 AA)
* Minimum contrast ratio of 4.5:1 for body text and 3:1 for large display headers against warm ivory surfaces.
* Full keyboard tab navigation with visible focus rings (`2px solid #B45309`).
* Strict support for `prefers-reduced-motion`: all transforms and transitions collapse to zero duration when reduced motion is requested.
* Screen reader announcements on all status changes and drawer actions.
