# Polaris-EMS Model Card: polaris-wind-xgb-himadri-v1.0

**SIH Problem Statement**: SIH26061 — AI-Driven Smart Energy Management System for Polar Research Stations  
**Model Name**: `polaris-wind-xgb-himadri-v1.0`  
**Model Version**: `v1.0`  
**Station**: `HIMADRI`  
**Target Variable**: `wind_generation_kw`  
**Physical Rated Capacity**: `10.0 kW`  
**Git Commit**: `f81f4a3`  
**Provenance**: `SYNTHETIC` (Polaris-EMS Synthetic Environment)

---

## 1. Intended Use & Scope
- **Primary Purpose**: Multi-horizon forecasting for polar microgrid operational planning (1–48h) and strategic resilience scheduling (up to 168h).
- **Intended Downstream Consumer**: Phase 4 Digital Twin and Phase 6 Rolling Horizon Optimizer.
- **Not Intended Use**: Physical station field deployment without site-specific recalibration against certified physical SCADA telemetry and calibrated AWS weather sensors.

---

## 2. Architecture & Physics Coupling
- **Model Family**: Direct Aerodynamic XGBoost with Turbine Power Curve Clamping
- **Point Objective**: `reg:squarederror`
- **Probabilistic / Quantile Loss**: `reg:quantileerror` at quantiles $\alpha \in \{0.10, 0.50, 0.90, 0.95\}$
- **Uncertainty Calibration**: Conformalized Quantile Regression (CQR) with monotonicity sorting ($P_10 \le P_50 \le P_90 \le P_95$)
- **Weather Input Abstraction**: Strict causal inputs from `WeatherForecastProvider` (zero future weather leakage).

---

## 3. Training & Validation Protocol
- **Training Data**: 70% chronological partition (2024-01-01 to 2026-01-31, 18,412 hours).
- **Validation Tuning Split**: First 50% of val_calibration (1,973 hours) used for model comparison.
- **Calibration Split**: Subsequent 50% of val_calibration (1,973 hours) used exclusively for nonconformity quantile calibration.
- **Final Test Set**: 15% isolated chronological test set (2026-07-16 to 2026-12-31, 3,946 hours) evaluated strictly once.

---

## 4. Final Isolated Test Performance
- **MAE**: `1.852 kW`
- **RMSE**: `2.488 kW`
- **sMAPE**: `57.72%`
- **R² Score**: `0.2808`
- **Mean Bias Error (MBE)**: `-0.315 kW`

### Probabilistic Uncertainty & Empirical Coverage
- **Nominal 80% Interval Coverage**: `80.0%` (Gap: `+0.0%`)
- **Nominal 90% Interval Coverage**: `88.4%`
- **Mean 80% Interval Width (Sharpness)**: `5.52 kW`
- **Quantile Crossing Rate**: `0.0%` (Strict zero crossing)

---

## 5. Known Limitations & Failure Modes
1. **Severe Blizzard Cut-Outs**: Rapid wind cut-outs (> 25 m/s) can trigger transient wind overprediction if the barometric drop is misjudged.
2. **Extreme Cold Events**: Under extreme thermal stress (< -40°C), building thermal inertia causes non-linear demand spikes.
3. **Synthetic Environment Contract**: This model was trained and validated exclusively within the Polaris-EMS synthetic environment (`polaris-sim-v2.0`). Real-world deployment requires retraining using validated station telemetry.
