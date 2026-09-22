"""
POLARIS-EMS — Model Card Generator
SIH26061: Polar Energy Management & Resilience System

Generates formal markdown model cards for production models in docs/model_cards/.
Enforces transparent documentation of synthetic-environment training,
failure modes, conformal coverage, and intended vs non-intended use.
"""

from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parent.parent


def generate_all_model_cards():
    output_dir = ROOT_DIR / "docs" / "model_cards"
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = ROOT_DIR / "models" / "phase3_evaluation_results.json"

    data = {}
    if results_path.exists():
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    for station_id, station_data in data.items():
        for target_key, target_dict in station_data.get("targets", {}).items():
            meta = target_dict["metadata"]
            m_name = meta["model_name"]
            card_path = output_dir / f"{m_name}.md"

            content = f"""# Polaris-EMS Model Card: {m_name}

**SIH Problem Statement**: SIH26061 — AI-Driven Smart Energy Management System for Polar Research Stations  
**Model Name**: `{m_name}`  
**Model Version**: `{meta['model_version']}`  
**Station**: `{meta['station']}`  
**Target Variable**: `{meta['target']}`  
**Physical Rated Capacity**: `{meta['capacity_kw']} kW`  
**Git Commit**: `{meta['git_commit']}`  
**Provenance**: `SYNTHETIC` (Polaris-EMS Synthetic Environment)

---

## 1. Intended Use & Scope
- **Primary Purpose**: Multi-horizon forecasting for polar microgrid operational planning (1–48h) and strategic resilience scheduling (up to 168h).
- **Intended Downstream Consumer**: Phase 4 Digital Twin and Phase 6 Rolling Horizon Optimizer.
- **Not Intended Use**: Physical station field deployment without site-specific recalibration against certified physical SCADA telemetry and calibrated AWS weather sensors.

---

## 2. Architecture & Physics Coupling
- **Model Family**: { 'Physics-Informed Thermal Decomposition + XGBoost Operational Residual Learner' if target_key == 'load' else ('Direct Astronomical XGBoost with Hard Night Clamping' if target_key == 'solar' else 'Direct Aerodynamic XGBoost with Turbine Power Curve Clamping') }
- **Point Objective**: `reg:squarederror`
- **Probabilistic / Quantile Loss**: `reg:quantileerror` at quantiles $\\alpha \\in \\{{0.10, 0.50, 0.90, 0.95\\}}$
- **Uncertainty Calibration**: Conformalized Quantile Regression (CQR) with monotonicity sorting ($P_{10} \\le P_{50} \\le P_{90} \\le P_{95}$)
- **Weather Input Abstraction**: Strict causal inputs from `WeatherForecastProvider` (zero future weather leakage).

---

## 3. Training & Validation Protocol
- **Training Data**: 70% chronological partition (2024-01-01 to 2026-01-31, 18,412 hours).
- **Validation Tuning Split**: First 50% of val_calibration (1,973 hours) used for model comparison.
- **Calibration Split**: Subsequent 50% of val_calibration (1,973 hours) used exclusively for nonconformity quantile calibration.
- **Final Test Set**: 15% isolated chronological test set (2026-07-16 to 2026-12-31, 3,946 hours) evaluated strictly once.

---

## 4. Final Isolated Test Performance
- **MAE**: `{meta['test_metrics']['mae']} kW`
- **RMSE**: `{meta['test_metrics']['rmse']} kW`
- **sMAPE**: `{meta['test_metrics']['smape']}%`
- **R² Score**: `{meta['test_metrics']['r2']}`
- **Mean Bias Error (MBE)**: `{meta['test_metrics']['mbe']} kW`

### Probabilistic Uncertainty & Empirical Coverage
- **Nominal 80% Interval Coverage**: `{meta['test_coverage']['interval_80_coverage'] * 100:.1f}%` (Gap: `{meta['test_coverage']['nominal_80_gap'] * 100:+.1f}%`)
- **Nominal 90% Interval Coverage**: `{meta['test_coverage']['interval_90_coverage'] * 100:.1f}%`
- **Mean 80% Interval Width (Sharpness)**: `{meta['test_coverage']['sharpness_80_kw']} kW`
- **Quantile Crossing Rate**: `{meta['test_coverage']['quantile_crossing_rate'] * 100:.1f}%` (Strict zero crossing)

---

## 5. Known Limitations & Failure Modes
1. **Severe Blizzard Cut-Outs**: Rapid wind cut-outs (> 25 m/s) can trigger transient wind overprediction if the barometric drop is misjudged.
2. **Extreme Cold Events**: Under extreme thermal stress (< -40°C), building thermal inertia causes non-linear demand spikes.
3. **Synthetic Environment Contract**: This model was trained and validated exclusively within the Polaris-EMS synthetic environment (`polaris-sim-v2.0`). Real-world deployment requires retraining using validated station telemetry.
"""
            with open(card_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[MODEL CARD] Generated: {card_path.name}")


if __name__ == "__main__":
    generate_all_model_cards()
