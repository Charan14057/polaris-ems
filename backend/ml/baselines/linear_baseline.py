"""
POLARIS-EMS — Regularized Linear / Ridge Baseline Forecaster
SIH26061: Polar Energy Management & Resilience System

Implements a regularized L2 linear regression baseline with standard scaling
consuming the identical causal feature contracts.
"""

from typing import Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


class RidgeBaselineForecaster:
    """Regularized linear regression baseline for energy time series forecasting."""

    def __init__(self, alpha: float = 1.0, random_state: int = 42):
        self.alpha = alpha
        self.random_state = random_state
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=self.alpha, random_state=self.random_state))
        ])
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RidgeBaselineForecaster":
        """Fits the scaled Ridge model on feature matrix X and target y."""
        self.pipeline.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generates predictions for feature matrix X."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict()")
        return np.asarray(self.pipeline.predict(X), dtype=float)
