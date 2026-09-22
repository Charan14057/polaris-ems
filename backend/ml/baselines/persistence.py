"""
POLARIS-EMS — Persistence Baseline Forecaster
SIH26061: Polar Energy Management & Resilience System

Implements the standard persistence benchmark:
ŷ(t+k) = y(t)
"""

from typing import List, Union
import numpy as np
import pandas as pd


class PersistenceForecaster:
    """Predicts future values by holding the most recent observed value constant."""

    def __init__(self, target_name: str = "target"):
        self.target_name = target_name

    def predict(
        self,
        history_series: Union[pd.Series, np.ndarray],
        horizons: List[int]
    ) -> np.ndarray:
        """
        Generates predictions for all horizons k by returning y(t).
        
        Args:
            history_series: Historical target observations up to origin t (length >= 1)
            horizons: List of lead times in hours
            
        Returns:
            np.ndarray of shape (len(horizons),)
        """
        if len(history_series) == 0:
            raise ValueError("history_series cannot be empty")
        y_origin = float(history_series.iloc[-1] if isinstance(history_series, pd.Series) else history_series[-1])
        return np.full(len(horizons), y_origin, dtype=float)
