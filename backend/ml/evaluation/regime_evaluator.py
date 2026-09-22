"""
POLARIS-EMS — Regime-Wise Model Evaluator
SIH26061: Polar Energy Management & Resilience System

Evaluates model performance stratified across all 10 polar disturbance regimes,
daylight seasonal states (Polar Day, Polar Night, Transition), and extreme weather conditions.
Prevents strong normal scores from hiding extreme regime vulnerabilities.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from backend.ml.evaluation.metrics import ForecastMetrics


class RegimeEvaluator:
    """Stratifies forecast accuracy across polar operational and disturbance regimes."""

    ALL_DISTURBANCE_REGIMES = [
        "NORMAL",
        "CLOUD_SURGE",
        "BLIZZARD",
        "EXTREME_COLD",
        "HIGH_WIND",
        "LOW_WIND",
        "SOLAR_REDUCTION",
        "SOLAR_FAILURE",
        "WIND_FAILURE",
        "COMBINED_POLAR_STRESS",
    ]

    @staticmethod
    def evaluate_disturbances(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        disturbance_series: pd.Series,
        capacity_kw: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Evaluates metrics per disturbance regime.
        """
        df = pd.DataFrame({
            "y": y_true,
            "y_hat": y_pred,
            "regime": disturbance_series.values
        })

        records = []
        for regime in RegimeEvaluator.ALL_DISTURBANCE_REGIMES:
            sub_df = df[df["regime"] == regime]
            if sub_df.empty:
                records.append({
                    "regime": regime,
                    "samples": 0,
                    "mae": 0.0,
                    "rmse": 0.0,
                    "smape": 0.0,
                    "r2": 0.0,
                    "mbe": 0.0
                })
                continue

            m = ForecastMetrics.compute_all(
                y_true=sub_df["y"].values,
                y_pred=sub_df["y_hat"].values,
                capacity_kw=capacity_kw
            )
            records.append({
                "regime": regime,
                "samples": len(sub_df),
                "mae": m["mae"],
                "rmse": m["rmse"],
                "smape": m["smape"],
                "r2": m["r2"],
                "mbe": m["mbe"]
            })

        return pd.DataFrame.from_records(records)

    @staticmethod
    def evaluate_seasons(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        timestamps: pd.Series,
        station_id: str,
        capacity_kw: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Evaluates metrics across Polar Day, Polar Night, and Transition seasons.
        """
        ts = pd.to_datetime(timestamps, utc=True)
        # Bharati/Maitri (Antarctica):
        # Polar Day: Nov-Jan; Polar Night: May-Jul; Transition: Feb-Apr, Aug-Oct
        # Himadri (Arctic):
        # Polar Day: Apr-Aug; Polar Night: Oct-Feb; Transition: Mar, Sep
        is_antarctic = "HIMADRI" not in station_id.upper()
        
        def classify_season(dt) -> str:
            m = dt.month
            if is_antarctic:
                if m in [11, 12, 1]:
                    return "POLAR_DAY"
                elif m in [5, 6, 7]:
                    return "POLAR_NIGHT"
                else:
                    return "TRANSITION"
            else:
                if m in [5, 6, 7]:
                    return "POLAR_DAY"
                elif m in [11, 12, 1]:
                    return "POLAR_NIGHT"
                else:
                    return "TRANSITION"

        seasons = ts.apply(classify_season)
        df = pd.DataFrame({"y": y_true, "y_hat": y_pred, "season": seasons})

        records = []
        for season_name in ["POLAR_DAY", "POLAR_NIGHT", "TRANSITION"]:
            sub_df = df[df["season"] == season_name]
            if sub_df.empty:
                continue
            m = ForecastMetrics.compute_all(
                y_true=sub_df["y"].values,
                y_pred=sub_df["y_hat"].values,
                capacity_kw=capacity_kw
            )
            records.append({
                "season": season_name,
                "samples": len(sub_df),
                "mae": m["mae"],
                "rmse": m["rmse"],
                "smape": m["smape"],
                "r2": m["r2"],
                "mbe": m["mbe"]
            })

        return pd.DataFrame.from_records(records)
