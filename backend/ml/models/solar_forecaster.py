"""
POLARIS-EMS — Solar Generation Forecaster
SIH26061: Polar Energy Management & Resilience System

Forecasts solar PV generation across operational horizons (1-48h).
Enforces strict physical constraints:
- Zero generation during astronomical night and polar night (solar_elevation <= 0)
- Clamped above by station-specific PV peak capacity from StationProfileRegistry
- Calibrated quantiles (P10, P50, P90, P95) via quantile loss
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import xgboost as xgb

from backend.ml.station_config import StationConfigAdapter


class SolarForecaster:
    """XGBoost solar forecaster with hard astronomical and capacity physical constraints."""

    def __init__(
        self,
        station_id: str,
        station_config: Optional[StationConfigAdapter] = None,
        xgb_params: Optional[Dict] = None,
        quantiles: Tuple[float, ...] = (0.10, 0.50, 0.90, 0.95),
        random_state: int = 42
    ):
        self.station_id = station_id.upper()
        self.station_config = station_config or StationConfigAdapter()
        self.quantiles = quantiles
        self.random_state = random_state

        limits = self.station_config.get_solar_limits(self.station_id)
        self.pv_peak_kw = float(limits["solar_pv_kw_peak"])

        self.xgb_params = {
            "n_estimators": 300,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 3,
            "reg_alpha": 0.0,
            "reg_lambda": 1.0,
            "random_state": self.random_state,
            "n_jobs": -1
        }
        if xgb_params:
            self.xgb_params.update(xgb_params)

        self.point_model = xgb.XGBRegressor(
            objective="reg:squarederror",
            **self.xgb_params
        )
        self.quantile_models: Dict[float, xgb.XGBRegressor] = {}
        for q in self.quantiles:
            q_params = dict(self.xgb_params)
            q_params["objective"] = "reg:quantileerror"
            q_params["quantile_alpha"] = q
            self.quantile_models[q] = xgb.XGBRegressor(**q_params)

        self.is_fitted = False
        self.feature_names: List[str] = []

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[List[Tuple[pd.DataFrame, pd.Series]]] = None
    ) -> "SolarForecaster":
        """Fits solar point and quantile models."""
        self.feature_names = list(X.columns)

        if eval_set:
            self.point_model.fit(
                X, y,
                eval_set=eval_set,
                verbose=False
            )
        else:
            self.point_model.fit(X, y, verbose=False)

        for q, model in self.quantile_models.items():
            model.fit(X, y, verbose=False)

        self.is_fitted = True
        return self

    def _apply_physical_bounds(
        self,
        raw_pred: np.ndarray,
        X: pd.DataFrame
    ) -> np.ndarray:
        """Enforces solar night zeros and peak inverter capacity clamps."""
        pred = np.clip(raw_pred, 0.0, self.pv_peak_kw)
        
        # Zero out if sun is below horizon
        if "solar_elevation_deg" in X.columns:
            night_mask = X["solar_elevation_deg"].values <= 0.0
            pred[night_mask] = 0.0
        elif "is_daylight" in X.columns:
            night_mask = X["is_daylight"].values <= 0.0
            pred[night_mask] = 0.0

        return np.round(pred, 2)

    def predict_point(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_point()")
        raw = self.point_model.predict(X[self.feature_names])
        return self._apply_physical_bounds(raw, X)

    def predict_quantiles(self, X: pd.DataFrame) -> Dict[float, np.ndarray]:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_quantiles()")
        
        raw_quantiles = {}
        for q, model in self.quantile_models.items():
            raw = model.predict(X[self.feature_names])
            raw_quantiles[q] = self._apply_physical_bounds(raw, X)

        # Enforce monotonicity
        sorted_qs = sorted(self.quantiles)
        n_samples = len(X)
        calibrated_qs = {q: np.zeros(n_samples) for q in sorted_qs}

        for i in range(n_samples):
            vals = [raw_quantiles[q][i] for q in sorted_qs]
            for j in range(1, len(vals)):
                if vals[j] < vals[j - 1]:
                    vals[j] = vals[j - 1]
            for j, q in enumerate(sorted_qs):
                calibrated_qs[q][i] = vals[j]

        return calibrated_qs

    def predict(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        point = self.predict_point(X)
        quantiles = self.predict_quantiles(X)
        out = {"point": point}
        for q, arr in quantiles.items():
            p_label = f"P{int(q * 100):02d}"
            out[p_label] = arr
        return out
