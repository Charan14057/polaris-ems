"""
POLARIS-EMS — Deployable Machine Learning Inference Engine
SIH26061: Polar Energy Management & Resilience System

Provides a clean, typed inference pipeline for online station forecasting.
Produces point predictions and calibrated P10, P50, P90, P95 intervals.
Strictly outputs provenance="FORECAST".
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

from backend.ml.station_config import StationConfigAdapter
from backend.ml.weather_provider import WeatherForecastProvider
from backend.ml.features import FeaturePipeline
from backend.ml.registry import ModelRegistry


@dataclass
class ForecastResult:
    """Structured output schema for Polaris-EMS forecasting engines."""
    station_id: str
    forecast_origin: str
    target: str
    horizons: List[int]
    target_timestamps: List[str]
    point_predictions: List[float]
    p10: List[float]
    p50: List[float]
    p90: List[float]
    p95: List[float]
    model_version: str
    feature_schema_version: str
    provenance: str = "FORECAST"

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame({
            "station_id": self.station_id,
            "forecast_origin": self.forecast_origin,
            "target": self.target,
            "horizon_k": self.horizons,
            "timestamp": self.target_timestamps,
            "point": self.point_predictions,
            "P10": self.p10,
            "P50": self.p50,
            "P90": self.p90,
            "P95": self.p95,
            "provenance": self.provenance
        })


class InferenceEngine:
    """Production inference interface loading models from registry and executing forecasts."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        station_config: Optional[StationConfigAdapter] = None
    ):
        self.registry = registry or ModelRegistry()
        self.station_config = station_config or StationConfigAdapter()
        self.feature_pipeline = FeaturePipeline(self.station_config)
        self.weather_provider = WeatherForecastProvider()
        self._loaded_models: Dict[str, tuple] = {}

    def get_model(self, model_name: str) -> tuple:
        if model_name not in self._loaded_models:
            self._loaded_models[model_name] = self.registry.load_model(model_name)
        return self._loaded_models[model_name]

    def forecast(
        self,
        station_id: str,
        target_name: str,
        forecast_origin: pd.Timestamp,
        horizons: List[int],
        historical_df: pd.DataFrame,
        known_ahead_df: Optional[pd.DataFrame] = None,
        model_name: Optional[str] = None
    ) -> ForecastResult:
        """
        Executes end-to-end forecasting for requested horizons from origin t.
        
        Args:
            station_id: BHARATI | MAITRI | HIMADRI
            target_name: total_load_kw | solar_generation_kw | wind_generation_kw
            forecast_origin: Timestamp of current observation t
            horizons: List of horizons in hours (e.g. range(1, 49) for 48h)
            historical_df: Telemetry strictly at or before forecast_origin
            known_ahead_df: Future schedule DataFrame (t+1 to t+max_h)
            model_name: Specific model name to load from registry (or auto-resolved)
        """
        sid = station_id.upper()
        
        # Auto-resolve model name if not provided
        if model_name is None:
            prefix = "load" if "load" in target_name.lower() else ("solar" if "solar" in target_name.lower() else "wind")
            model_name = f"polaris-{prefix}-xgb-{sid.lower()}-v1.0"

        model, calibrator, metadata = self.get_model(model_name)

        # 1. Enforce historical cut-off
        history = historical_df[historical_df["timestamp"] <= forecast_origin].copy()
        if history.empty:
            raise ValueError(f"Historical dataframe contains no observations at or before {forecast_origin}")

        # 2. Generate causal weather forecast
        weather_res = self.weather_provider.predict(
            station_id=sid,
            forecast_origin=forecast_origin,
            horizons=horizons,
            historical_weather_df=history,
            mode="CAUSAL"
        )
        weather_by_h = {row["horizon"]: row for _, row in weather_res.df.iterrows()}

        # 3. Extract feature matrix
        feature_rows = []
        target_timestamps = []
        for k in horizons:
            target_time = forecast_origin + pd.Timedelta(hours=k)
            target_timestamps.append(target_time.isoformat())
            known_row = None
            if known_ahead_df is not None:
                match = known_ahead_df[known_ahead_df["timestamp"] == target_time]
                if not match.empty:
                    known_row = match.iloc[0]

            feat = self.feature_pipeline.extract_features_step(
                station_id=sid,
                target_name=target_name,
                forecast_origin=forecast_origin,
                horizon_k=k,
                history_df=history,
                known_ahead_row=known_row,
                weather_step=weather_by_h.get(k)
            )
            feature_rows.append(feat)

        X = pd.DataFrame.from_records(feature_rows)

        # 4. Model Prediction
        raw_preds = model.predict(X)

        # 5. Conformal Calibration
        if calibrator is not None:
            cal_preds = calibrator.apply_calibration(raw_preds)
        else:
            cal_preds = raw_preds

        # 6. Format into ForecastResult
        return ForecastResult(
            station_id=sid,
            forecast_origin=forecast_origin.isoformat(),
            target=target_name,
            horizons=list(horizons),
            target_timestamps=target_timestamps,
            point_predictions=[float(x) for x in cal_preds["point"]],
            p10=[float(x) for x in cal_preds["P10"]],
            p50=[float(x) for x in cal_preds.get("P50", cal_preds["point"])],
            p90=[float(x) for x in cal_preds["P90"]],
            p95=[float(x) for x in cal_preds["P95"]],
            model_version=metadata.get("model_version", "v1.0"),
            feature_schema_version=metadata.get("feature_schema_version", "v1.0"),
            provenance="FORECAST"
        )
