"""
POLARIS-EMS — Walk-Forward Rolling Evaluation
SIH26061: Polar Energy Management & Resilience System

Implements chronological walk-forward expanding window cross-validation.
Enforces zero temporal leakage and measures model generalization across seasons.
"""

from typing import Dict, List, Tuple, Callable, Any
import numpy as np
import pandas as pd

from backend.ml.evaluation.metrics import ForecastMetrics


class WalkForwardValidator:
    """Evaluates time-series models using chronological expanding windows."""

    def __init__(
        self,
        initial_train_hours: int = 8760,  # 1 year
        val_step_hours: int = 720,        # 30 days
        purge_gap_hours: int = 24         # 24h gap between train and val
    ):
        self.initial_train_hours = initial_train_hours
        self.val_step_hours = val_step_hours
        self.purge_gap_hours = purge_gap_hours

    def get_folds(
        self,
        df: pd.DataFrame
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Generates chronological (train_df, val_df) fold pairs.
        """
        n_total = len(df)
        folds = []
        train_end = self.initial_train_hours

        while train_end + self.purge_gap_hours + self.val_step_hours <= n_total:
            train_df = df.iloc[:train_end].copy()
            val_start = train_end + self.purge_gap_hours
            val_end = val_start + self.val_step_hours
            val_df = df.iloc[val_start:val_end].copy()

            folds.append((train_df, val_df))
            train_end += self.val_step_hours

        return folds

    def evaluate_model(
        self,
        model_factory: Callable[[], Any],
        df: pd.DataFrame,
        target_name: str,
        horizons: List[int],
        feature_builder: Callable[[pd.DataFrame, List[int]], Tuple[pd.DataFrame, pd.DataFrame]],
        capacity_kw: float = None
    ) -> Dict[str, Any]:
        """
        Runs walk-forward cross-validation for a candidate model.
        """
        folds = self.get_folds(df)
        if not folds:
            raise ValueError("Dataset length is too short for walk-forward validation with specified parameters")

        fold_metrics = []

        for fold_idx, (train_df, val_df) in enumerate(folds):
            model = model_factory()
            X_train, y_train = feature_builder(train_df, horizons)
            X_val, y_val = feature_builder(val_df, horizons)

            model.fit(X_train, y_train["target"])
            preds = model.predict(X_val)
            point_pred = preds["point"] if isinstance(preds, dict) else preds

            m = ForecastMetrics.compute_all(
                y_true=y_val["target"].values,
                y_pred=point_pred,
                capacity_kw=capacity_kw
            )
            m["fold"] = fold_idx + 1
            m["train_size"] = len(train_df)
            m["val_size"] = len(val_df)
            fold_metrics.append(m)

        # Compute summary statistics across folds
        summary = {
            "n_folds": len(fold_metrics),
            "mae_mean": round(float(np.mean([f["mae"] for f in fold_metrics])), 3),
            "mae_std": round(float(np.std([f["mae"] for f in fold_metrics])), 3),
            "rmse_mean": round(float(np.mean([f["rmse"] for f in fold_metrics])), 3),
            "rmse_std": round(float(np.std([f["rmse"] for f in fold_metrics])), 3),
            "smape_mean": round(float(np.mean([f["smape"] for f in fold_metrics])), 2),
            "r2_mean": round(float(np.mean([f["r2"] for f in fold_metrics])), 4),
            "folds": fold_metrics
        }
        return summary
