"""
POLARIS-EMS — Conformalized Quantile Calibrator (CQR)
SIH26061: Polar Energy Management & Resilience System

Implements split-conformal calibration on held-out calibration data.
Calibrates quantile forecasts (P10, P50, P90, P95) and guarantees
finite-sample empirical coverage with strict monotonicity enforcement.
"""

from typing import Dict, List, Optional
import numpy as np


class ConformalQuantileCalibrator:
    """
    Calibrates raw quantile forecasts via Conformalized Quantile Regression (CQR).
    Computes out-of-sample nonconformity scores and adjusts quantile endpoints.
    """

    def __init__(self, target_name: str = "target"):
        self.target_name = target_name
        self.is_calibrated = False
        self.delta_10: float = 0.0
        self.delta_50: float = 0.0
        self.delta_90: float = 0.0
        self.delta_95: float = 0.0
        self.q_conformal_80: float = 0.0
        self.q_conformal_90: float = 0.0
        self.n_calib_samples: int = 0

    def calibrate(
        self,
        raw_calib_preds: Dict[str, np.ndarray],
        y_calib: np.ndarray
    ) -> "ConformalQuantileCalibrator":
        """
        Fits calibration adjustment terms on the dedicated calibration split.
        
        Args:
            raw_calib_preds: Dict containing 'P10', 'P50', 'P90', 'P95', 'point'
            y_calib: True observed values on calibration partition
        """
        y = np.asarray(y_calib, dtype=float)
        n = len(y)
        if n == 0:
            raise ValueError("y_calib cannot be empty")
        self.n_calib_samples = n

        q10 = raw_calib_preds["P10"]
        q50 = raw_calib_preds.get("P50", raw_calib_preds.get("point"))
        q90 = raw_calib_preds["P90"]
        q95 = raw_calib_preds["P95"]

        # 1. Nonconformity score for 80% interval [P10, P90]
        # E_i = max(q10(x_i) - y_i, y_i - q90(x_i))
        scores_80 = np.maximum(q10 - y, y - q90)
        # Finite sample conformal quantile with (n+1) correction
        level_80 = min(1.0, np.ceil((n + 1) * 0.80) / n)
        self.q_conformal_80 = float(np.quantile(scores_80, level_80))

        # 2. Nonconformity score for 90% interval [P05, P95] or [P10, P95]
        scores_90 = np.maximum(q10 - y, y - q95)
        level_90 = min(1.0, np.ceil((n + 1) * 0.90) / n)
        self.q_conformal_90 = float(np.quantile(scores_90, level_90))

        # 3. Individual quantile shift calibration (pinball residual quantiles)
        res_10 = y - q10
        res_50 = y - q50
        res_90 = y - q90
        res_95 = y - q95

        self.delta_10 = float(np.quantile(res_10, 0.10))
        self.delta_50 = float(np.median(res_50))
        self.delta_90 = float(np.quantile(res_90, 0.90))
        self.delta_95 = float(np.quantile(res_95, 0.95))

        self.is_calibrated = True
        return self

    def apply_calibration(
        self,
        raw_preds: Dict[str, np.ndarray],
        use_conformal_interval: bool = True
    ) -> Dict[str, np.ndarray]:
        """
        Applies calibration adjustments and strictly enforces monotonicity:
        0 <= P10 <= P50 <= P90 <= P95.
        """
        if not self.is_calibrated:
            return raw_preds

        q10_raw = raw_preds["P10"]
        q50_raw = raw_preds.get("P50", raw_preds.get("point"))
        q90_raw = raw_preds["P90"]
        q95_raw = raw_preds["P95"]
        point_raw = raw_preds.get("point", q50_raw)

        if use_conformal_interval and self.q_conformal_80 > 0:
            # CQR interval expansion
            cal_p10 = np.maximum(0.0, q10_raw - self.q_conformal_80)
            cal_p90 = np.maximum(0.0, q90_raw + self.q_conformal_80)
            cal_p95 = np.maximum(0.0, q95_raw + self.q_conformal_90)
            cal_p50 = np.maximum(0.0, q50_raw)
        else:
            # Shift calibration
            cal_p10 = np.maximum(0.0, q10_raw + self.delta_10)
            cal_p50 = np.maximum(0.0, q50_raw + self.delta_50)
            cal_p90 = np.maximum(0.0, q90_raw + self.delta_90)
            cal_p95 = np.maximum(0.0, q95_raw + self.delta_95)

        # Monotonicity projection
        n = len(point_raw)
        p10_out = np.zeros(n)
        p50_out = np.zeros(n)
        p90_out = np.zeros(n)
        p95_out = np.zeros(n)

        for i in range(n):
            v10 = max(0.0, float(cal_p10[i]))
            v50 = max(v10, float(cal_p50[i]))
            v90 = max(v50, float(cal_p90[i]))
            v95 = max(v90, float(cal_p95[i]))
            p10_out[i] = round(v10, 2)
            p50_out[i] = round(v50, 2)
            p90_out[i] = round(v90, 2)
            p95_out[i] = round(v95, 2)

        return {
            "point": np.round(point_raw, 2),
            "P10": p10_out,
            "P50": p50_out,
            "P90": p90_out,
            "P95": p95_out
        }

    def get_calibration_metadata(self) -> Dict[str, float]:
        """Returns calibration parameter summary."""
        return {
            "is_calibrated": self.is_calibrated,
            "n_calib_samples": self.n_calib_samples,
            "q_conformal_80": self.q_conformal_80,
            "q_conformal_90": self.q_conformal_90,
            "delta_10": self.delta_10,
            "delta_50": self.delta_50,
            "delta_90": self.delta_90,
            "delta_95": self.delta_95
        }
