"""
POLARIS-EMS — Physics-Informed Load Forecaster
SIH26061: Polar Energy Management & Resilience System

Couples deterministic thermodynamic heat-loss physics + base operational demand
with an XGBoost operational residual learner for both point and quantile forecasting.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import xgboost as xgb

from backend.ml.station_config import StationConfigAdapter


class PhysicsInformedLoadForecaster:
    """
    Decomposes total load into:
    y(t+k) = P_physics_base(t+k) + r(t+k)
    where:
    P_physics_base = max(0, UA * (T_target - T_amb_est(t+k))) + P_crit + occ * P_delta
    r(t+k) is learned by XGBoost (point and quantile regressors).
    """

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

        # Fetch physical parameters from station configuration
        therm = self.station_config.get_thermal_parameters(self.station_id)
        prof = self.station_config.get_profile(self.station_id)
        
        self.ua = float(therm["building_ua_kw_per_k"])
        self.t_target = float(therm["indoor_target_temp_c"])
        
        # Estimate base critical load from critical devices
        crit_kw = sum(
            d.min_required_power_kw for d in prof.devices
            if d.category == "CRITICAL"
        )
        self.base_critical_kw = max(15.0, crit_kw)
        self.occupancy_delta_kw = 12.0  # Circadian crew activity swing

        # Starter XGBoost parameters
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

        # Regressors
        self.point_model = xgb.XGBRegressor(
            objective="reg:squarederror",
            **self.xgb_params
        )
        self.quantile_models: Dict[float, xgb.XGBRegressor] = {}
        for q in self.quantiles:
            q_params = dict(self.xgb_params)
            # XGBoost quantile loss configuration
            q_params["objective"] = "reg:quantileerror"
            q_params["quantile_alpha"] = q
            self.quantile_models[q] = xgb.XGBRegressor(**q_params)

        self.is_fitted = False
        self.feature_names: List[str] = []

    def compute_physics_baseline(self, X: pd.DataFrame) -> np.ndarray:
        """
        Computes the deterministic physics baseline:
        P_physics = max(0, UA * (T_target - T_amb_est)) + base_critical + occ * delta
        """
        if "forecast_temperature_c" in X.columns:
            t_amb = X["forecast_temperature_c"].values
        elif "origin_temperature_c" in X.columns:
            t_amb = X["origin_temperature_c"].values
        else:
            t_amb = np.full(len(X), -15.0)

        if "occupancy_state" in X.columns:
            occ = X["occupancy_state"].values
        else:
            occ = np.full(len(X), 0.5)

        # Thermal building envelope heat loss
        delta_t = np.maximum(0.0, self.t_target - t_amb)
        p_thermal = self.ua * delta_t

        # Physics base total
        p_base = p_thermal + self.base_critical_kw + (occ * self.occupancy_delta_kw)
        return np.maximum(0.0, p_base)

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[List[Tuple[pd.DataFrame, pd.Series]]] = None,
        early_stopping_rounds: Optional[int] = 30
    ) -> "PhysicsInformedLoadForecaster":
        """Fits the point model and quantile models on operational residuals."""
        self.feature_names = list(X.columns)
        p_base_train = self.compute_physics_baseline(X)
        r_train = y.values - p_base_train

        # Point model fitting
        if eval_set:
            X_val, y_val = eval_set[0]
            p_base_val = self.compute_physics_baseline(X_val)
            r_val = y_val.values - p_base_val
            self.point_model.fit(
                X, r_train,
                eval_set=[(X_val, r_val)],
                verbose=False
            )
        else:
            self.point_model.fit(X, r_train, verbose=False)

        # Quantile models fitting
        for q, model in self.quantile_models.items():
            model.fit(X, r_train, verbose=False)

        self.is_fitted = True
        return self

    def predict_point(self, X: pd.DataFrame) -> np.ndarray:
        """Generates point predictions = P_physics_base + predicted_residual."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_point()")
        p_base = self.compute_physics_baseline(X)
        r_pred = self.point_model.predict(X[self.feature_names])
        return np.maximum(0.0, p_base + r_pred)

    def predict_quantiles(self, X: pd.DataFrame) -> Dict[float, np.ndarray]:
        """
        Generates quantile predictions P_alpha = max(0, P_physics_base + predicted_q_residual).
        Enforces quantile monotonicity (P10 <= P50 <= P90 <= P95).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_quantiles()")
        p_base = self.compute_physics_baseline(X)
        raw_quantiles = {}
        for q, model in self.quantile_models.items():
            r_q = model.predict(X[self.feature_names])
            raw_quantiles[q] = np.maximum(0.0, p_base + r_q)

        # Monotonicity sorting / isotonic projection
        sorted_qs = sorted(self.quantiles)
        n_samples = len(X)
        calibrated_qs = {q: np.zeros(n_samples) for q in sorted_qs}

        for i in range(n_samples):
            vals = [raw_quantiles[q][i] for q in sorted_qs]
            # Ensure non-decreasing ordering
            for j in range(1, len(vals)):
                if vals[j] < vals[j - 1]:
                    vals[j] = vals[j - 1]
            for j, q in enumerate(sorted_qs):
                calibrated_qs[q][i] = vals[j]

        return calibrated_qs

    def predict(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Returns point and all quantiles in a unified dictionary."""
        point = self.predict_point(X)
        quantiles = self.predict_quantiles(X)
        out = {"point": point}
        for q, arr in quantiles.items():
            p_label = f"P{int(q * 100):02d}"
            out[p_label] = arr
        return out
