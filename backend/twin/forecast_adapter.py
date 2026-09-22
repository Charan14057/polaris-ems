"""
POLARIS-EMS — Digital Twin Forecast Adapter
SIH26061: Polar Energy Management & Resilience System

Ingests Phase 3 ML ForecastResult outputs and weather forecasts, converting them into
aligned driving trajectories for the Digital Twin under specified risk scenarios:
- EXPECTED: P50 load, P50 solar, P50 wind
- CONSERVATIVE (Stress): P90 load, P10 solar, P10 wind
- OPTIMISTIC: P10 load, P90 solar, P90 wind
Maintains strict provenance="FORECAST".
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
import pandas as pd
import numpy as np

from backend.ml.inference import ForecastResult
from backend.ml.weather_provider import WeatherForecastResult


@dataclass
class TwinInputStep:
    """Driving input for a single forward simulation step of the Twin."""
    timestamp: str
    horizon_h: int
    ambient_temp_c: float
    wind_speed_m_per_s: float
    ghi_w_per_m2: float
    load_kw: float
    solar_kw: float
    wind_kw: float
    mode: str
    provenance: str = "FORECAST"


class ForecastAdapter:
    """Adapts Phase 3 multi-horizon quantile forecasts to Digital Twin trajectories."""

    def __init__(self):
        pass

    def build_trajectory(
        self,
        station_id: str,
        load_forecast: ForecastResult,
        weather_forecast: Optional[pd.DataFrame] = None,
        solar_forecast: Optional[ForecastResult] = None,
        wind_forecast: Optional[ForecastResult] = None,
        mode: Literal["EXPECTED", "CONSERVATIVE", "OPTIMISTIC"] = "EXPECTED"
    ) -> List[TwinInputStep]:
        """
        Builds a time-ordered sequence of TwinInputStep items for simulation.

        Args:
            station_id: Station identifier (BHARATI, MAITRI, HIMADRI)
            load_forecast: Phase 3 ML ForecastResult for total load
            weather_forecast: DataFrame containing ambient_temp_c, wind_speed_ms, ghi_wm2
            solar_forecast: Optional Phase 3 ML ForecastResult for solar PV
            wind_forecast: Optional Phase 3 ML ForecastResult for wind turbine
            mode: "EXPECTED" (P50), "CONSERVATIVE" (P90 load / P10 renewables), or "OPTIMISTIC"
        """
        steps: List[TwinInputStep] = []
        n_steps = len(load_forecast.horizons)

        # Weather lookup preparation
        weather_map = {}
        if weather_forecast is not None and not weather_forecast.empty:
            for _, row in weather_forecast.iterrows():
                ts_str = str(row.get("timestamp", ""))
                weather_map[ts_str] = {
                    "temp": float(row.get("temperature_c", row.get("ambient_temp_c", -15.0))),
                    "wind": float(row.get("wind_speed_ms", row.get("wind_speed_m_per_s", 8.0))),
                    "ghi": float(row.get("irradiance_wm2", row.get("ghi_w_per_m2", 0.0)))
                }

        for i in range(n_steps):
            h = load_forecast.horizons[i]
            ts = load_forecast.target_timestamps[i]

            # 1. Select load according to risk mode
            if mode == "CONSERVATIVE":
                p_load = float(load_forecast.p90[i]) if load_forecast.p90 else float(load_forecast.point_predictions[i])
            elif mode == "OPTIMISTIC":
                p_load = float(load_forecast.p10[i]) if load_forecast.p10 else float(load_forecast.point_predictions[i])
            else:  # EXPECTED
                p_load = float(load_forecast.p50[i]) if load_forecast.p50 else float(load_forecast.point_predictions[i])

            p_load = max(0.0, p_load)

            # 2. Select solar power
            p_solar = 0.0
            if solar_forecast is not None and i < len(solar_forecast.horizons):
                if mode == "CONSERVATIVE":
                    p_solar = float(solar_forecast.p10[i]) if solar_forecast.p10 else float(solar_forecast.point_predictions[i])
                elif mode == "OPTIMISTIC":
                    p_solar = float(solar_forecast.p90[i]) if solar_forecast.p90 else float(solar_forecast.point_predictions[i])
                else:
                    p_solar = float(solar_forecast.p50[i]) if solar_forecast.p50 else float(solar_forecast.point_predictions[i])
                p_solar = max(0.0, p_solar)

            # 3. Select wind power
            p_wind = 0.0
            if wind_forecast is not None and i < len(wind_forecast.horizons):
                if mode == "CONSERVATIVE":
                    p_wind = float(wind_forecast.p10[i]) if wind_forecast.p10 else float(wind_forecast.point_predictions[i])
                elif mode == "OPTIMISTIC":
                    p_wind = float(wind_forecast.p90[i]) if wind_forecast.p90 else float(wind_forecast.point_predictions[i])
                else:
                    p_wind = float(wind_forecast.p50[i]) if wind_forecast.p50 else float(wind_forecast.point_predictions[i])
                p_wind = max(0.0, p_wind)

            # 4. Weather extraction (fallback to climatological default if missing)
            w_info = weather_map.get(ts, {"temp": -15.0, "wind": 8.0, "ghi": 0.0})

            steps.append(
                TwinInputStep(
                    timestamp=ts,
                    horizon_h=h,
                    ambient_temp_c=w_info["temp"],
                    wind_speed_m_per_s=w_info["wind"],
                    ghi_w_per_m2=w_info["ghi"],
                    load_kw=round(p_load, 2),
                    solar_kw=round(p_solar, 2),
                    wind_kw=round(p_wind, 2),
                    mode=mode,
                    provenance="FORECAST"
                )
            )

        return steps
