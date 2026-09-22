"""
POLARIS-EMS — Tree Baseline Forecaster
SIH26061: Polar Energy Management & Resilience System

Implements a non-boosted Random Forest ensemble baseline
consuming the identical causal feature contracts.
"""

from typing import Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


class TreeBaselineForecaster:
    """Non-boosted ensemble tree baseline for energy time series forecasting."""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 8,
        min_samples_split: int = 5,
        random_state: int = 42,
        n_jobs: int = -1
    ):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=random_state,
            n_jobs=n_jobs
        )
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "TreeBaselineForecaster":
        """Fits the Random Forest model on feature matrix X and target y."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generates predictions for feature matrix X."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict()")
        return np.asarray(self.model.predict(X), dtype=float)
