# POLARIS-EMS — STATION CONFIGURATION RECONCILIATION
**Release Milestone:** v1.0.0 Production  
**Authority:** `configs/station_profiles.json`  
**Date of Audit:** 2026-09-28  
**Status:** RECONCILED & CANONICALLY ENFORCED  

---

## 1. Authoritative Configuration Source of Truth

The authoritative specifications for all three Indian polar research facilities reside in:
`configs/station_profiles.json` (ingested by `backend/data/station_profiles/loader.py:StationProfileRegistry`).

Any documentation, report text, or UI label claiming conflicting figures (e.g. 60 kW PV or 3 × 64 kW DG for Bharati) is superseded and corrected to the authoritative values below.

---

## 2. Complete Station Specification Reconciliation Table

| Station | Parameter | Erroneous / Draft Value | Authoritative Profile Value (`configs/station_profiles.json`) | Physical Context & Engineering Rationale | Status |
|---|---|---|---|---|---|
| **BHARATI** | **Solar PV Peak** | $60.0\text{ kW}$ | **$30.0\text{ kW}$** | Bifacial elevated rooftop & perimeter test string ($65^\circ$ tilt, $18\%$ efficiency). | **RECONCILED** |
| **BHARATI** | **Wind Turbine Rated** | $25.0\text{ kW}$ | **$25.0\text{ kW}$** | High-latitude polar turbine ($3.0\text{ m/s}$ cut-in, $11.5\text{ m/s}$ rated, $25.0\text{ m/s}$ storm cut-out). | **VERIFIED** |
| **BHARATI** | **Diesel Generator Count** | 3 Gensets | **3 Gensets** | Primary Caterpillar 3406 / Kirloskar polar-rated gensets in insulated lower deck. | **VERIFIED** |
| **BHARATI** | **Diesel Unit Rating** | $64.0\text{ kW}$ each | **$80.0\text{ kW}$ each ($3 \times 80\text{ kW}$)** | Continuous prime polar rating at $30\%$ min loading ($24.0\text{ kW}$ spinning floor). | **RECONCILED** |
| **BHARATI** | **BESS Capacity** | $120.0\text{ kWh}$ | **$120.0\text{ kWh}$** | Containerized Lithium Iron Phosphate (LFP) ($35\text{ kW}$ charge, $40\text{ kW}$ discharge, $92\%$ roundtrip). | **VERIFIED** |
| **BHARATI** | **Fuel Storage Capacity**| $160,000\text{ L}$ | **$160,000\text{ L}$** | Double-walled insulated bulk polar diesel fuel farm ($25,000\text{ L}$ critical reserve). | **VERIFIED** |
| **BHARATI** | **Resupply Window** | 45 days | **45 days** | Annual sea voyage delivery window (Nov–Jan expedition season). | **VERIFIED** |
| **MAITRI** | **Solar PV Peak** | $30.0\text{ kW}$ | **$18.0\text{ kW}$** | Ground-mounted test array on rocky Schirmacher Oasis terrain ($70^\circ$ tilt, $17\%$ efficiency). | **RECONCILED** |
| **MAITRI** | **Wind Turbine Rated** | $15.0\text{ kW}$ | **$15.0\text{ kW}$** | Katabatic wind generator on bedrock ridge ($3.5\text{ m/s}$ cut-in, $12.0\text{ m/s}$ rated). | **VERIFIED** |
| **MAITRI** | **Diesel Generator Count** | 3 Gensets | **3 Gensets** | Kirloskar-Cummins engines in dedicated central power house. | **VERIFIED** |
| **MAITRI** | **Diesel Unit Rating** | $50.0\text{ kW}$ | **$62.5\text{ kW}$ each ($3 \times 62.5\text{ kW}$)** | Continuous polar rating at $35\%$ min loading ($21.88\text{ kW}$ spinning floor). | **RECONCILED** |
| **MAITRI** | **BESS Capacity** | $80.0\text{ kWh}$ | **$90.0\text{ kWh}$** | Temperature-regulated indoor battery bank ($25\text{ kW}$ charge, $30\text{ kW}$ discharge, $90\%$ roundtrip). | **RECONCILED** |
| **MAITRI** | **Fuel Storage Capacity**| $140,000\text{ L}$ | **$140,000\text{ L}$** | Bulk Aviation Kerosene / Polar Diesel storage tanks ($22,000\text{ L}$ critical reserve). | **VERIFIED** |
| **MAITRI** | **Resupply Window** | 30 days | **30 days** | Annual convoy and helicopter resupply window across coastal shelf. | **VERIFIED** |
| **HIMADRI** | **Solar PV Peak** | $10.0\text{ kW}$ / $15.0\text{ kW}$ | **$12.0\text{ kW}$** | High Arctic summer rooftop array taking advantage of 24h polar daylight ($75^\circ$ tilt). | **RECONCILED** |
| **HIMADRI** | **Wind Turbine Rated** | $0.0\text{ kW}$ | **$10.0\text{ kW}$** | Compact micro-turbine for Arctic fjord coastal winds ($3.0\text{ m/s}$ cut-in, $11.0\text{ m/s}$ rated). | **RECONCILED** |
| **HIMADRI** | **Diesel Generator Count** | 1 Genset | **2 Gensets** | Backup diesel gensets backing up clean Ny-Ålesund district microgrid interconnection. | **RECONCILED** |
| **HIMADRI** | **Diesel Unit Rating** | $40.0\text{ kW}$ | **$45.0\text{ kW}$ each ($2 \times 45\text{ kW}$)** | Continuous rating at $30\%$ min loading ($13.5\text{ kW}$ spinning floor). | **RECONCILED** |
| **HIMADRI** | **BESS Capacity** | $60.0\text{ kWh}$ | **$50.0\text{ kWh}$** | Indoor clean power conditioning battery buffer ($18\text{ kW}$ charge, $20\text{ kW}$ discharge, $92\%$ roundtrip). | **RECONCILED** |
| **HIMADRI** | **Fuel Storage Capacity**| $50,000\text{ L}$ | **$60,000\text{ L}$** | Arctic low-pour diesel reserve tank ($10,000\text{ L}$ critical reserve). | **RECONCILED** |
| **HIMADRI** | **Resupply Window** | 21 days | **21 days** | Semi-annual Svalbard maritime shipping resupply schedule (180-day cycle). | **VERIFIED** |

---

## 3. Subsystem Alignment Verification

1. **Backend Profile Ingestion (`backend/data/station_profiles/loader.py`):**
   - Ingests `configs/station_profiles.json` dynamically into Pydantic model `StationProfile`.
   - Verified that `StationProfileRegistry().get("BHARATI").electrical.solar_pv_kw_peak == 30.0`.
   - Verified that `StationProfileRegistry().get("BHARATI").electrical.diesel_generator_kw_rated == 80.0`.
2. **Frontend 3D Spatial Profiles (`frontend/src/features/twin/model/spatialProfiles3D.ts`):**
   - Verified that Bharati 3D objects declare `Photovoltaic Array (30 kWp)` with `nominalPowerKw: 30.0`.
   - Verified that Bharati 3D objects declare `Primary Diesel Gensets (3x80 kW)` with `nominalPowerKw: 80.0`.
   - Verified that Maitri 3D objects declare `Photovoltaic Array (18 kWp)` and `3x62.5 kW Cummins`.
   - Verified that Himadri 3D objects declare `Solar PV Array (12 kWp)`, `10 kW wind turbine`, and `2x45 kW backup diesel`.
3. **Full-Circle Simulation Lifecycle (`tests/test_scenario_full_circle.py`):**
   - Anchors baseline state to `profile.electrical.solar_pv_kw_peak` ($30.0\text{ kW}$) and `profile.electrical.diesel_generator_kw_rated` ($80.0\text{ kW}$).
   - Restores cleanly on `clear_scenario()` without compounding or rating drift.
