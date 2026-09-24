"""
POLARIS-EMS — Forecast API Adapter
SIH26061: Polar Energy Management & Resilience System

Translates API forecast requests into causal calls to Phase 3 InferenceEngine.
Resolves historical telemetry from MLDataLoader or caller payload without inventing data.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from backend.ml.inference import InferenceEngine, ForecastResult
from backend.ml.data_loader import MLDataLoader
from backend.api.schemas.forecast import ForecastRequestSchema, ForecastResponseData, QuantilePointSchema
from backend.api.errors import InvalidRequestException


class ForecastAPIAdapter:
    """Bridges FastAPI requests to the Phase 3 ML Inference Engine."""

    def __init__(self, inference_engine: Optional[InferenceEngine] = None, data_loader: Optional[MLDataLoader] = None):
        self.inference = inference_engine or InferenceEngine()
        self.data_loader = data_loader or MLDataLoader()

    def execute_forecast(self, req: ForecastRequestSchema) -> ForecastResponseData:
        """Executes causal multi-horizon probabilistic forecast."""
        sid = req.station_id.upper()
        target = req.target.lower()
        horizon_hours = req.horizon_hours

        # 1. Resolve Historical Telemetry
        if req.historical_records and len(req.historical_records) > 0:
            history_df = pd.DataFrame(req.historical_records)
            if "timestamp" not in history_df.columns:
                raise InvalidRequestException("historical_records must include 'timestamp' field", field="historical_records")
            history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], utc=True)
            history_df = history_df.sort_values("timestamp").reset_index(drop=True)
        else:
            try:
                # Load verified station telemetry from partition
                history_df = self.data_loader.load_train_data(sid)
            except Exception as e:
                raise InvalidRequestException(
                    f"Unable to load historical telemetry for station '{sid}': {str(e)}",
                    field="station_id"
                )

        # 2. Resolve Forecast Origin
        if req.forecast_origin:
            try:
                origin_ts = pd.to_datetime(req.forecast_origin, utc=True)
            except Exception:
                raise InvalidRequestException(f"Invalid forecast_origin timestamp: {req.forecast_origin}", field="forecast_origin")
        else:
            # Default to the most recent observation in history
            origin_ts = history_df["timestamp"].iloc[-1]

        # Verify historical observations exist at or before origin
        history_at_origin = history_df[history_df["timestamp"] <= origin_ts]
        if history_at_origin.empty:
            raise InvalidRequestException(
                f"No historical telemetry found at or before requested forecast_origin '{origin_ts.isoformat()}'",
                field="forecast_origin"
            )

        horizons = list(range(1, horizon_hours + 1))

        # 3. Call Phase 3 Inference Engine
        try:
            result: ForecastResult = self.inference.forecast(
                station_id=sid,
                target_name=target,
                forecast_origin=origin_ts,
                horizons=horizons,
                historical_df=history_at_origin
            )
        except Exception as e:
            raise InvalidRequestException(f"ML Forecasting failed: {str(e)}")

        # 4. Map to API Response Schema
        quantiles = [
            QuantilePointSchema(
                horizon_h=h,
                timestamp=ts,
                point=round(pt, 3),
                p10=round(p10_val, 3),
                p50=round(p50_val, 3),
                p90=round(p90_val, 3),
                p95=round(p95_val, 3)
            )
            for h, ts, pt, p10_val, p50_val, p90_val, p95_val in zip(
                result.horizons,
                result.target_timestamps,
                result.point_predictions,
                result.p10,
                result.p50,
                result.p90,
                result.p95
            )
        ]

        mean_pt = float(np.mean(result.point_predictions)) if result.point_predictions else 0.0
        min_p10 = float(np.min(result.p10)) if result.p10 else 0.0
        max_p90 = float(np.max(result.p90)) if result.p90 else 0.0

        return ForecastResponseData(
            station_id=sid,
            forecast_origin=origin_ts.isoformat(),
            target=target,
            horizon_hours=horizon_hours,
            quantiles=quantiles,
            mean_forecast_kw=round(mean_pt, 2),
            min_p10_kw=round(min_p10, 2),
            max_p90_kw=round(max_p90, 2),
            model_version=result.model_version,
            feature_schema_version=result.feature_schema_version,
            provenance="FORECAST"
        )
