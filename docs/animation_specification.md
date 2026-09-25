# POLARIS-EMS — MOTION & ANIMATION SPECIFICATION

**Document ID:** SPEC-ANIMATION-20260925  
**Version:** 1.0.0-MISSION-MOTION  
**Status:** CANONICAL & IMPLEMENTED  

---

## 1. MOTION PHILOSOPHY

Motion in Polaris-EMS is strictly functional, understated, and state-communicative. It exists solely to:
1. Preserve spatial orientation when expanding or drilling into evidence.
2. Confirm user intent and dispatch actions with tactile responsiveness.
3. Signal background synchronization without drawing distracting attention.

### Anti-Patterns Strictly Prohibited:
* No bouncing cards or elastic spring overshoots.
* No constant ambient pulsing or glowing neon loops.
* No decorative parallax scrolling effects.
* No auto-spinning widgets unless actively performing asynchronous network I/O.

---

## 2. CENTRALIZED MOTION TOKENS

All durations and timing curves are centralized in `frontend/src/design/tokens.ts` and `frontend/src/index.css`:

```typescript
export const motionTokens = {
  duration: {
    instant: '0ms',
    micro: '120ms',    // Button clicks, badge active states
    hover: '180ms',    // Interactive element hovers, border color shifts
    panel: '240ms',    // Accordion disclosures, table row expansions
    drawer: '320ms',   // Slide-out Evidence Drawer
    page: '350ms',     // View navigation transitions
    emphasis: '500ms', // Critical alarm state transition
  },
  easing: {
    standard: 'cubic-bezier(0.2, 0.0, 0.0, 1.0)', // Natural decel curve
    accelerate: 'cubic-bezier(0.3, 0.0, 1.0, 1.0)', // Exit curve
    decelerate: 'cubic-bezier(0.0, 0.0, 0.2, 1.0)', // Entry curve
    drawer: 'cubic-bezier(0.16, 1.0, 0.3, 1.0)',    // High-precision sliding
  }
};
```

---

## 3. COMPONENT MOTION SPECIFICATIONS

### 3.1 Evidence Drawer
* **Transition:** Slides horizontally from the right edge on desktop; slides up from bottom on mobile.
* **Duration:** `320ms`.
* **Easing:** `cubic-bezier(0.16, 1.0, 0.3, 1.0)` (crisp deceleration with no bounce).
* **Backdrop:** Fades from `rgba(0, 0, 0, 0)` to `rgba(28, 25, 23, 0.25)` over `240ms`.

### 3.2 Decision Ribbon Nodes
* **Hover:** Border shifts from `#DDD6C6` to `#B45309` over `180ms` ease-in-out; scale remains strictly 1.0 (no card zooming).
* **Active Node:** Slight background tint shift to soft copper (`#FEF3C7`) with 1px active underline rule.

### 3.3 Progressive Disclosure (Why This Matters)
* **Expansion:** Smooth vertical height expansion over `240ms` standard deceleration.
* **Chevron:** 180-degree rotation over `180ms`.

---

## 4. PREFERS-REDUCED-MOTION SUPPORT

Polaris-EMS guarantees complete accessibility for users with vestibular sensitivities or high-latency remote rendering terminals:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

When reduced motion is enabled:
* The Evidence Drawer opens instantly without sliding.
* Accordions expand instantly without vertical translation.
* Loading spinners collapse to static "Loading..." text with ARIA status roles.
