"""
POLARIS-EMS — Causal Seasonal-Naive Baseline Forecaster
SIH26061: Polar Energy Management & Resilience System

Implements 24-hour diurnal and 168-hour weekly seasonal-naive baselines.
Enforces the strict causal seasonal lag contract:
reference_timestamp <= forecast_origin
eliminating future observation leakage for all horizons k >= 1.
"""

import math
from typing import List, Union
import numpy as np
import pandas as pd


def get_causal_seasonal_reference_index(
    origin_idx: int,
    horizon_k: int,
    season_period: int
) -> int:
    """
    Finds the latest historical index that shares the exact same seasonal phase
    as target step (origin_idx + horizon_k), strictly satisfying ref_idx <= origin_idx.
    
    Proof of causality:
    Let cycles = ceil(k / season_period) >= 1.
    ref_idx = origin_idx + k - (cycles * season_period).
    Since cycles * season_period >= k, (k - cycles * season_period) <= 0.
    Therefore, ref_idx <= origin_idx is strictly guaranteed.
    """
    cycles = math.ceil(horizon_k / season_period)
    ref_idx = origin_idx + horizon_k - (cycles * season_period)
    return max(0, ref_idx)


class SeasonalNaiveForecaster:
    """Predicts future values using the nearest valid historical seasonal match."""

    def __init__(self, season_period: int = 24, target_name: str = "target"):
        """
        Args:
            season_period: 24 for diurnal cycle, 168 for weekly cycle
            target_name: Name of target variable
        """
        self.season_period = season_period
        self.target_name = target_name

    def predict(
        self,
        history_series: Union[pd.Series, np.ndarray],
        horizons: List[int]
    ) -> np.ndarray:
        """
        Generates predictions for all horizons k using historical seasonal match.
        
        Args:
            history_series: Full history up to origin t (length >= 1)
            horizons: List of lead times in hours
            
        Returns:
            np.ndarray of shape (len(horizons),)
        """
        arr = history_series.values if isinstance(history_series, pd.Series) else np.asarray(history_series)
        origin_idx = len(arr) - 1
        if origin_idx < 0:
            raise ValueError("history_series cannot be empty")

        preds = []
        for k in horizons:
            ref_idx = get_causal_seasonal_reference_index(origin_idx, k, self.season_period)
            preds.append(float(arr[ref_idx]))
        return np.array(preds, dtype=float)
