"""
POLARIS-EMS — Forecast Evaluation Metrics
SIH26061: Polar Energy Management & Resilience System

Computes MAE, RMSE, sMAPE, R2, nMAE, nRMSE, MBE, capacity-normalized error,
and daylight-period solar metrics. Handles zero-target boundaries cleanly.
"""

from typing import Dict, Optional
import numpy as np


class ForecastMetrics:
    """Calculates standardized point-forecast evaluation metrics."""

    @staticmethod
    def compute_all(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        capacity_kw: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Computes the complete suite of forecast performance metrics.
        """
        y = np.asarray(y_true, dtype=float)
        y_hat = np.asarray(y_pred, dtype=float)
        n = len(y)
        if n == 0:
            return {}

        errors = y_hat - y
        abs_errors = np.abs(errors)
        sq_errors = errors ** 2

        # 1. Standard Metrics
        mae = float(np.mean(abs_errors))
        rmse = float(np.sqrt(np.mean(sq_errors)))
        mbe = float(np.mean(errors))  # Mean Bias Error

        # 2. sMAPE: symmetric MAPE, safe for zero-values
        denom = np.abs(y) + np.abs(y_hat)
        # Add epsilon where both are 0 to avoid 0/0
        zero_mask = denom < 1e-6
        smape_elements = np.zeros(n)
        smape_elements[~zero_mask] = 200.0 * abs_errors[~zero_mask] / denom[~zero_mask]
        smape = float(np.mean(smape_elements))

        # 3. R2 Score
        y_mean = float(np.mean(y))
        ss_tot = float(np.sum((y - y_mean) ** 2))
        ss_res = float(np.sum(sq_errors))
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-6 else 0.0

        # 4. Normalized Metrics
        norm_ref = capacity_kw if capacity_kw is not None and capacity_kw > 0 else (y_mean if y_mean > 0 else 1.0)
        nmae = float(mae / norm_ref)
        nrmse = float(rmse / norm_ref)

        metrics = {
            "n_samples": n,
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "smape": round(smape, 2),
            "r2": round(r2, 4),
            "mbe": round(mbe, 3),
            "nmae": round(nmae, 4),
            "nrmse": round(nrmse, 4),
        }
        if capacity_kw is not None:
            metrics["capacity_kw"] = capacity_kw
            metrics["capacity_norm_mae_pct"] = round(nmae * 100.0, 2)
            metrics["capacity_norm_rmse_pct"] = round(nrmse * 100.0, 2)

        return metrics

    @staticmethod
    def compute_daylight_solar(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        solar_elevation: np.ndarray,
        capacity_kw: float
    ) -> Dict[str, float]:
        """
        Computes solar metrics specifically during daylight hours (elevation > 0).
        Prevents polar night zeros from artificially inflating R2 or masking errors.
        """
        mask = np.asarray(solar_elevation) > 0.0
        if not np.any(mask):
            return {
                "daylight_samples": 0,
                "daylight_mae": 0.0,
                "daylight_rmse": 0.0,
                "daylight_r2": 0.0
            }
        
        daylight_y = y_true[mask]
        daylight_pred = y_pred[mask]
        m = ForecastMetrics.compute_all(daylight_y, daylight_pred, capacity_kw=capacity_kw)
        return {
            "daylight_samples": int(np.sum(mask)),
            "daylight_mae": m["mae"],
            "daylight_rmse": m["rmse"],
            "daylight_r2": m["r2"],
            "daylight_smape": m["smape"],
            "daylight_norm_mae_pct": m.get("capacity_norm_mae_pct", 0.0)
        }
