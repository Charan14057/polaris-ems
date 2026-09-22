# Polaris-EMS: Research & Source Registry
**SIH26061**: AI-Driven Smart Energy Management System for Polar Research Stations  
**Status**: Authoritative Documentation (PRD Section 67)

---

## 1. Primary Problem Reference & Official Polar Agencies

| Entity / Portal | URL | Verified Scope / Artifacts | Classification |
| :--- | :--- | :--- | :--- |
| **SIH2026 Portal** | `https://sih2026.vuce.in/ps/SIH26061` | SIH26061 Problem Statement: AI-Driven Smart Energy Management System for Polar Research Stations | Source-supported fact |
| **National Centre for Polar and Ocean Research (NCPOR)** | `https://data.ncpor.res.in/`, `https://npdc.ncpor.res.in/` | Indian Polar Program portal, AWS weather data, expedition archives | Source-supported fact |
| **NCPOR AWS Station Telemetry** | `https://npdc.ncpor.res.in/pdc/Aws/imd/Awsdata.jsp` | In-situ meteorological observations for Maitri and Bharati (Antarctica) | Source-supported fact |
| **NCPOR Research Stations** | `https://npdc.ncpor.res.in/npdc/research-stations.action` | Station infrastructure, geographical coordinates, seasonal operational cycles | Source-supported fact |
| **Copernicus Climate Data Store** | `https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels` | ERA5 single-level hourly atmospheric reanalysis (surface temperature, solar irradiance, wind components) | Source-supported fact |

---

## 2. Competitive Landscape & Technical Benchmarks

| Reference / Project | URL / Documentation | Scope / Observed Features | Polaris-EMS Distinction / Engineering Inference |
| :--- | :--- | :--- | :--- |
| **PolarGrid AI** | `https://github.com/Krish-Rajput/polar_grid` | Public SIH26061 competitor. Uses synthetic polar data, XGBoost/RF forecasting, heuristic battery/diesel dispatch, simulation lab. | Polaris-EMS differentiates via: physics-informed thermal load decomposition, calibrated conformal uncertainty ($P_{10}$ to $P_{95}$), rolling constrained MILP optimizer with resupply survival constraints, and explainable decision traces. |
| **NREL REopt** | `https://www.nrel.gov/reopt/` | Commercial DER optimization & resilience platform. | Polaris-EMS specializes in extreme polar constraints (polar night, sub-zero battery derating, high heating degree hours, annual resupply vessels). |
| **HOMER Pro** | `https://homerenergy.com/homer-pro` | Microgrid techno-economic simulation & sensitivity analysis. | Polaris-EMS integrates real-time predictive ML with operational digital twin and rolling horizon dispatch. |
| **Princess Elisabeth Antarctica** | `https://www.antarcticstation.org/station/smart_grid` | Zero-emission Antarctic polar research station microgrid. | Real-world validation that polar microgrids require strict critical vs flexible load prioritization. |

---

## 3. Data Integrity & Scientific Grounding Rules

1. **Source-Supported Facts**: Physical station coordinates, regional climate bounds, polar night / midnight sun calendars, and NCPOR AWS weather data.
2. **Engineering Inferences**: Diesel generator fuel curves ($0.27 - 0.30 \text{ L/kWh}$), battery roundtrip efficiency ($90-92\%$), and cold derating coefficients ($0.7-1.0\% \text{ per } ^\circ\text{C}$ below $-10^\circ\text{C}$).
3. **Design Decisions**: Rolling constrained MILP optimization with Pyomo + HiGHS, conformal quantile calibration, 3-tier policy model (`MANUAL`, `AUTO`, `EMERGENCY`), representative spatial Energy Twin.
4. **Synthetic Assumptions**: Sub-hourly device loads, synthesized operational noise, proxy building heat loss coefficients ($UA$).
