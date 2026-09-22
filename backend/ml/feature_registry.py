"""
POLARIS-EMS — Machine-Readable Feature Registry
SIH26061: Polar Energy Management & Resilience System

Authoritative schema registry enforcing the Phase 2 Feature Availability Policy
and preventing future data leakage across all ML forecasting models.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class FeatureMetadata:
    feature_name: str
    source: str                 # "ASTRONOMICAL" | "SCHEDULE" | "CALENDAR" | "TELEMETRY" | "WEATHER_FORECAST" | "DERIVED"
    availability_time: str      # "T_PLUS_K" (known ahead) | "ORIGIN_T" (historical/current <= t)
    known_ahead: bool           # True if deterministically known ahead at t+k
    lag_required: int           # Minimum lag required relative to origin t (>= 0)
    future_dependent: bool      # Strictly False for all production features
    allowed_for_model: List[str]# ["LOAD", "SOLAR", "WIND"]
    reason: str


class FeatureRegistry:
    """Central registry of valid, leakage-free features for Polaris-EMS."""

    _FEATURES: Dict[str, FeatureMetadata] = {
        # Calendar & Harmonics (Known Ahead)
        "hour_sin": FeatureMetadata(
            feature_name="hour_sin",
            source="CALENDAR",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD", "SOLAR", "WIND"],
            reason="Diurnal 24h harmonic sin component known ahead"
        ),
        "hour_cos": FeatureMetadata(
            feature_name="hour_cos",
            source="CALENDAR",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD", "SOLAR", "WIND"],
            reason="Diurnal 24h harmonic cos component known ahead"
        ),
        "doy_sin": FeatureMetadata(
            feature_name="doy_sin",
            source="CALENDAR",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD", "SOLAR", "WIND"],
            reason="Annual 365/366d harmonic sin component known ahead"
        ),
        "doy_cos": FeatureMetadata(
            feature_name="doy_cos",
            source="CALENDAR",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD", "SOLAR", "WIND"],
            reason="Annual 365/366d harmonic cos component known ahead"
        ),
        "day_of_week": FeatureMetadata(
            feature_name="day_of_week",
            source="CALENDAR",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD", "SOLAR", "WIND"],
            reason="Deterministic calendar day of week (0-6)"
        ),
        "horizon_k": FeatureMetadata(
            feature_name="horizon_k",
            source="CALENDAR",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD", "SOLAR", "WIND"],
            reason="Forecast lead time in hours (1-168)"
        ),

        # Astronomical Geometry (Known Ahead)
        "solar_elevation_deg": FeatureMetadata(
            feature_name="solar_elevation_deg",
            source="ASTRONOMICAL",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["SOLAR", "LOAD"],
            reason="Astronomical solar elevation at t+k strictly known from orbital mechanics"
        ),
        "is_daylight": FeatureMetadata(
            feature_name="is_daylight",
            source="ASTRONOMICAL",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["SOLAR", "LOAD"],
            reason="Binary flag (solar_elevation_deg > 0) strictly known ahead"
        ),

        # Operational Schedules (Known Ahead)
        "occupancy_state": FeatureMetadata(
            feature_name="occupancy_state",
            source="SCHEDULE",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD"],
            reason="Published circadian station crew shift schedule known ahead"
        ),
        "maintenance_state": FeatureMetadata(
            feature_name="maintenance_state",
            source="SCHEDULE",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD", "WIND"],
            reason="Scheduled maintenance window known in advance"
        ),
        "research_activity_state": FeatureMetadata(
            feature_name="research_activity_state",
            source="SCHEDULE",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD"],
            reason="Published scientific instrument duty cycle known in advance"
        ),
        "communication_state": FeatureMetadata(
            feature_name="communication_state",
            source="SCHEDULE",
            availability_time="T_PLUS_K",
            known_ahead=True,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD"],
            reason="Scheduled satellite dish track passes known in advance"
        ),

        # Causal Weather Forecast Inputs (at t+k, generated from provider)
        "forecast_temperature_c": FeatureMetadata(
            feature_name="forecast_temperature_c",
            source="WEATHER_FORECAST",
            availability_time="T_PLUS_K",
            known_ahead=False,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD", "SOLAR"],
            reason="Causal forecast of ambient temperature at t+k from WeatherForecastProvider"
        ),
        "forecast_wind_speed_ms": FeatureMetadata(
            feature_name="forecast_wind_speed_ms",
            source="WEATHER_FORECAST",
            availability_time="T_PLUS_K",
            known_ahead=False,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["WIND"],
            reason="Causal forecast of wind speed at t+k from WeatherForecastProvider"
        ),
        "forecast_cloud_fraction": FeatureMetadata(
            feature_name="forecast_cloud_fraction",
            source="WEATHER_FORECAST",
            availability_time="T_PLUS_K",
            known_ahead=False,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["SOLAR"],
            reason="Causal forecast of cloud fraction at t+k from WeatherForecastProvider"
        ),
        "forecast_irradiance_wm2": FeatureMetadata(
            feature_name="forecast_irradiance_wm2",
            source="WEATHER_FORECAST",
            availability_time="T_PLUS_K",
            known_ahead=False,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["SOLAR"],
            reason="Causal clear-sky irradiance attenuated by forecast cloud at t+k"
        ),

        # Historical Telemetry at Origin t (<= t)
        "origin_temperature_c": FeatureMetadata(
            feature_name="origin_temperature_c",
            source="TELEMETRY",
            availability_time="ORIGIN_T",
            known_ahead=False,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD", "SOLAR", "WIND"],
            reason="Measured ambient temperature at forecast origin t"
        ),
        "origin_wind_speed_ms": FeatureMetadata(
            feature_name="origin_wind_speed_ms",
            source="TELEMETRY",
            availability_time="ORIGIN_T",
            known_ahead=False,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["WIND", "LOAD"],
            reason="Measured wind speed at forecast origin t"
        ),
        "origin_irradiance_wm2": FeatureMetadata(
            feature_name="origin_irradiance_wm2",
            source="TELEMETRY",
            availability_time="ORIGIN_T",
            known_ahead=False,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["SOLAR"],
            reason="Measured surface solar irradiance at forecast origin t"
        ),
        "origin_pressure_hpa": FeatureMetadata(
            feature_name="origin_pressure_hpa",
            source="TELEMETRY",
            availability_time="ORIGIN_T",
            known_ahead=False,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["WIND", "LOAD"],
            reason="Measured barometric pressure at origin t"
        ),
        "barometric_trend_3h": FeatureMetadata(
            feature_name="barometric_trend_3h",
            source="DERIVED",
            availability_time="ORIGIN_T",
            known_ahead=False,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["WIND", "LOAD"],
            reason="P(t) - P(t-3), rapid drops indicate storm front onset"
        ),
        "thermal_gradient_est": FeatureMetadata(
            feature_name="thermal_gradient_est",
            source="DERIVED",
            availability_time="T_PLUS_K",
            known_ahead=False,
            lag_required=0,
            future_dependent=False,
            allowed_for_model=["LOAD"],
            reason="T_indoor_target - forecast_temperature_c, driving thermal heat loss"
        ),
    }

    @classmethod
    def get(cls, feature_name: str) -> FeatureMetadata:
        if feature_name not in cls._FEATURES:
            raise KeyError(f"Feature '{feature_name}' not registered in FeatureRegistry")
        return cls._FEATURES[feature_name]

    @classmethod
    def list_features_for_model(cls, model_target: str) -> List[str]:
        target = model_target.upper()
        return [
            name for name, meta in cls._FEATURES.items()
            if target in meta.allowed_for_model
        ]

    @classmethod
    def export_json(cls) -> str:
        return json.dumps({k: asdict(v) for k, v in cls._FEATURES.items()}, indent=2)
