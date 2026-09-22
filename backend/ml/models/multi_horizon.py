"""
POLARIS-EMS — Multi-Horizon Forecaster Manager
SIH26061: Polar Energy Management & Resilience System

Manages continuous multi-horizon forecasting:
- Direct benchmark models for specific audit horizons: k in {1, 2, 6, 12, 24, 48, 168}
- Continuous horizon-conditioned forecaster supporting every continuous hour 1h to 48h
  for operational dispatch and 1h to 168h for strategic load planning.
"""

from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd

from backend.ml.models.physics_load_model import PhysicsInformedLoadForecaster
from backend.ml.models.solar_forecaster import SolarForecaster
from backend.ml.models.wind_forecaster import WindForecaster
from backend.ml.station_config import StationConfigAdapter


class MultiHorizonForecaster:
    """Orchestrates multi-horizon operational (1-48h) and strategic (1-168h) forecasting."""

    BENCHMARK_HORIZONS = [1, 2, 6, 12, 24, 48, 168]

    def __init__(
        self,
        station_id: str,
        target_name: str,
        station_config: Optional[StationConfigAdapter] = None,
        quantiles: tuple = (0.10, 0.50, 0.90, 0.95),
        random_state: int = 42
    ):
        self.station_id = station_id.upper()
        self.target_name = target_name
        self.station_config = station_config or StationConfigAdapter()
        self.quantiles = quantiles
        self.random_state = random_state

        # Initialize underlying engine based on target
        if "load" in target_name.lower():
            self.model_type = "PHYSICS_XGB"
            self.model = PhysicsInformedLoadForecaster(
                station_id=self.station_id,
                station_config=self.station_config,
                quantiles=self.quantiles,
                random_state=self.random_state
            )
        elif "solar" in target_name.lower():
            self.model_type = "SOLAR_XGB"
            self.model = SolarForecaster(
                station_id=self.station_id,
                station_config=self.station_config,
                quantiles=self.quantiles,
                random_state=self.random_state
            )
        elif "wind" in target_name.lower():
            self.model_type = "WIND_XGB"
            self.model = WindForecaster(
                station_id=self.station_id,
                station_config=self.station_config,
                quantiles=self.quantiles,
                random_state=self.random_state
            )
        else:
            raise ValueError(f"Unsupported target_name: {target_name}")

        self.is_fitted = False

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[List] = None
    ) -> "MultiHorizonForecaster":
        """Fits the underlying horizon-conditioned forecaster."""
        self.model.fit(X, y, eval_set=eval_set)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Generates predictions containing point forecast and P10, P50, P90, P95 quantiles."""
        if not self.is_fitted:
            raise RuntimeError("MultiHorizonForecaster must be fitted before predict()")
        return self.model.predict(X)
