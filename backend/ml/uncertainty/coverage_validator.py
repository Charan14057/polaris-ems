"""
POLARIS-EMS — Coverage & Sharpness Validator
SIH26061: Polar Energy Management & Resilience System

Validates empirical coverage and sharpness (interval width) of probabilistic forecasts.
Computes P10, P90, P95 coverage, interval coverage (P10-P90, P10-P95), quantile crossing checks,
and breakdowns across horizons, stations, and disturbance regimes.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd


class CoverageValidator:
    """Evaluates finite-sample validity and sharpness of uncertainty intervals."""

    @staticmethod
    def evaluate_overall(
        y_true: np.ndarray,
        preds: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """
        Computes overall empirical coverage and sharpness metrics.
        """
        y = np.asarray(y_true, dtype=float)
        n = len(y)
        if n == 0:
            return {}

        p10 = preds["P10"]
        p50 = preds.get("P50", preds.get("point"))
        p90 = preds["P90"]
        p95 = preds["P95"]

        # Empirical quantile coverage (cumulative probabilities)
        cov_p10 = float(np.mean(y <= p10))
        cov_p90 = float(np.mean(y <= p90))
        cov_p95 = float(np.mean(y <= p95))

        # Interval coverage
        cov_p10_p90 = float(np.mean((y >= p10) & (y <= p90)))
        cov_p10_p95 = float(np.mean((y >= p10) & (y <= p95)))

        # Sharpness (interval width in physical units, kW)
        width_80 = float(np.mean(p90 - p10))
        width_90 = float(np.mean(p95 - p10))

        # Quantile crossing check (must be 0.0)
        crossings = int(np.sum((p10 > p50) | (p50 > p90) | (p90 > p95)))
        crossing_rate = float(crossings / n)

        return {
            "n_samples": n,
            "cov_p10": round(cov_p10, 4),
            "cov_p90": round(cov_p90, 4),
            "cov_p95": round(cov_p95, 4),
            "interval_80_coverage": round(cov_p10_p90, 4),
            "interval_90_coverage": round(cov_p10_p95, 4),
            "nominal_80_gap": round(cov_p10_p90 - 0.80, 4),
            "sharpness_80_kw": round(width_80, 2),
            "sharpness_90_kw": round(width_90, 2),
            "quantile_crossing_count": crossings,
            "quantile_crossing_rate": round(crossing_rate, 4),
        }

    @staticmethod
    def evaluate_by_group(
        y_true: np.ndarray,
        preds: Dict[str, np.ndarray],
        group_series: pd.Series
    ) -> pd.DataFrame:
        """
        Computes coverage and sharpness grouped by horizon, regime, or season.
        """
        df = pd.DataFrame({
            "y": y_true,
            "p10": preds["P10"],
            "p50": preds.get("P50", preds.get("point")),
            "p90": preds["P90"],
            "p95": preds["P95"],
            "group": group_series.values
        })

        records = []
        for grp_val, grp_df in df.groupby("group"):
            y_g = grp_df["y"].values
            p_dict = {
                "P10": grp_df["p10"].values,
                "P50": grp_df["p50"].values,
                "P90": grp_df["p90"].values,
                "P95": grp_df["p95"].values
            }
            metrics = CoverageValidator.evaluate_overall(y_g, p_dict)
            metrics["group"] = grp_val
            records.append(metrics)

        res_df = pd.DataFrame.from_records(records)
        if not res_df.empty:
            cols = ["group"] + [c for c in res_df.columns if c != "group"]
            res_df = res_df[cols]
        return res_df
