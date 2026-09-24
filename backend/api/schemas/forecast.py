"""
POLARIS-EMS — Forecast API Schemas
SIH26061: Polar Energy Management & Resilience System

Typed schemas for Phase 3 ML forecasting endpoint.
Preserves calibrated quantile intervals (P10, P50, P90, P95) and provenance="FORECAST".
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ForecastRequestSchema(BaseModel):
    """Input payload for multi-horizon probabilistic forecast."""
    station_id: str = Field(..., description="BHARATI | MAITRI | HIMADRI")
    target: str = Field("total_load_kw", description="total_load_kw | solar_generation_kw | wind_generation_kw")
    horizon_hours: int = Field(48, ge=1, le=168, description="Forecast lead time in hours (1 to 168)")
    forecast_origin: Optional[str] = Field(None, description="ISO-8601 timestamp of forecast origin t")
    historical_records: Optional[List[Dict[str, Any]]] = Field(
        None, description="Optional custom telemetry records at or before origin"
    )

    @field_validator("station_id")
    @classmethod
    def validate_station(cls, v: str) -> str:
        s = v.upper()
        if s not in {"BHARATI", "MAITRI", "HIMADRI"}:
            raise ValueError(f"Station '{v}' is invalid. Supported stations: BHARATI, MAITRI, HIMADRI")
        return s

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        valid_targets = {"total_load_kw", "solar_generation_kw", "wind_generation_kw"}
        if v.lower() not in valid_targets:
            raise ValueError(f"Target '{v}' must be one of {valid_targets}")
        return v.lower()


class QuantilePointSchema(BaseModel):
    """Calibrated quantile point for a single forecast step."""
    horizon_h: int
    timestamp: str
    point: float
    p10: float
    p50: float
    p90: float
    p95: float


class ForecastResponseData(BaseModel):
    """Structured forecast output preserving calibrated intervals and model metadata."""
    station_id: str
    forecast_origin: str
    target: str
    horizon_hours: int
    quantiles: List[QuantilePointSchema]
    mean_forecast_kw: float
    min_p10_kw: float
    max_p90_kw: float
    model_version: str
    feature_schema_version: str
    provenance: str = "FORECAST"
