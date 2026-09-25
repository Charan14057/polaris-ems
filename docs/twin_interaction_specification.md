# POLARIS-EMS — TWIN INTERACTION SPECIFICATION
## Phase 18 Interactions, Gestures, Accessibility, and Visual Behaviors

---

## 1. Viewport Navigation (Zoom, Pan, Fit-to-View)

### Pointer-Centered Zoom
Zooming via mouse scroll wheel or trackpad pinch scales around the exact pointer coordinates:
$$\text{nextPanX} = \text{pointerX} - (\text{pointerX} - \text{panX}) \times \frac{\text{nextZoom}}{\text{currentZoom}}$$
$$\text{nextPanY} = \text{pointerY} - (\text{pointerY} - \text{panY}) \times \frac{\text{nextZoom}}{\text{currentZoom}}$$

- **Zoom Range**: Clamped smoothly between $0.6\times$ (overview) and $2.8\times$ (component detail).
- **Drag Pan**: Left-click and drag across the canvas background with active grab cursor indicators (`cursor-grab` to `cursor-grabbing`).
- **Fit to View**: Instantly recalculates bounding dimensions to center and scale the station floorplan to fit the active browser viewport with 40px margins.
- **Reset**: Restores baseline zoom ($1.0\times$) and center translation ($0, 0$).

---

## 2. Selection & Inspection Architecture

### Selection Precedence
1. **Device Selection**: Clicking any device node opens the **TwinInspector** side panel, highlights the circuit, and activates the *Trace My Power Route* action.
2. **Zone Selection**: Clicking room floor regions selects the architectural zone, showing aggregate kW demand, critical load portion, connected device counts, and active fault indicators.
3. **Bus/Source Selection**: Clicking main buses or generators activates downstream *Trace Impact* mode.
4. **Canvas Background Click**: Clears active selections and restores full opacity across all circuits.

### Two-Layer Non-Technical Information Architecture
- **Layer 1 (Human Operational)**:
  - *What This Does*: Explains equipment role in plain English without acronyms (e.g., "Maintains habitable indoor temperatures, air circulation, and life-support atmosphere").
  - *Current State*: Dynamic operational reading (e.g., "Drawing 18.5 kW of 18.5 kW capacity").
  - *Why It Matters*: Operational risk context (e.g., "In polar winter (-40°C), temperature drops to freezing within hours if heating is lost").
- **Layer 2 (Expandable Technical View)**:
  - Accordion trigger: *"View Engineering Specs →"*
  - Circuit ID, 400V 3-Phase Voltage, Rated kW, Derived Operating Current ($I = \frac{P}{\sqrt{3} \times V \times \text{pf}}$), Priority Rank, Thermal Consequence, and Provenance Tag.
  - Link directly to the authoritative **EvidenceDrawer** via `inspectEvidence`.

---

## 3. "Trace My Power" & "Trace Impact"

### "Trace My Power"
- Triggered by clicking *Trace My Power Route* in the inspector or pressing keyboard shortcut `T`.
- Resolves upstream graph path:
  `Selected Device → Branch Conduit → Sub-DB Panel → Main Feeder → 400V AC Bus → Online Sources (Solar / Wind / Diesel / BESS)`
- **Visual Presentation**:
  - Traced upstream conduit paths and nodes remain 100% opaque with thickened strokes (3.5px) and glowing borders.
  - Unrelated circuits, panels, and loads are softly dimmed to 15% opacity.
  - The inspector displays an upstream power contribution summary.

### "Trace Impact"
- Triggered when a generator trips, fuel shortage occurs, or a user inspects a source/breaker.
- Highlights downstream paths from the source/breaker through distribution feeder conduits to every connected device and affected architectural zone.

---

## 4. Accessibility & Performance Controls

1. **Reduced Motion (`prefers-reduced-motion`)**:
   ```css
   @media (prefers-reduced-motion: reduce) {
     .twin-flow-path {
       animation: none !important;
       stroke-dasharray: none !important;
     }
   }
   ```
   When reduced motion is requested, animated dash flows are replaced with static directional arrows and high-contrast text indicators (`Flow: ACTIVE • Direction: FORWARD`).
2. **Non-Color Status Cues**:
   - Every status badge couples color with an explicit icon (Clock, ShieldCheck, AlertTriangle) and textual label (e.g., `ONLINE`, `STANDBY`, `DEFERRED`, `FAULT`).
3. **Keyboard Navigation**:
   - `Space`: Toggle 24-hour simulation replay.
   - `Left Arrow` / `Right Arrow`: Step 1 hour backward / forward along the timeline.
   - `+` / `-`: Zoom in / zoom out.
   - `Escape`: Clear active device inspection and reset tracing.
