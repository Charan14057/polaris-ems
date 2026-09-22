"""
POLARIS-EMS — Causal Weather Forecast Provider
SIH26061: Polar Energy Management & Resilience System

Provides strictly causal weather predictions using only telemetry observed
at or before forecast origin t. Completely eliminates future weather leakage.
Includes optional diagnostic ORACLE mode strictly for ablation analysis.
"""

from typing import List, Dict, Optional, Literal
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class WeatherForecastResult:
    station_id: str
    forecast_origin: pd.Timestamp
    horizons: List[int]
    df: pd.DataFrame  # Columns: horizon, timestamp, temperature_c, wind_speed_ms, cloud_fraction, irradiance_wm2, provenance
    mode: str         # "CAUSAL" | "ORACLE"
    provenance: str   # "FORECAST" | "DIAGNOSTIC_ORACLE"


class WeatherForecastProvider:
    """Generates causal forward weather estimates for ML forecasting engines."""

    # Seasonal temperature and wind climatological baselines per station
    CLIMATOLOGY: Dict[str, Dict[str, float]] = {
        "BHARATI": {"temp_mean": -12.0, "wind_mean": 9.5, "cloud_mean": 0.45},
        "MAITRI": {"temp_mean": -15.0, "wind_mean": 10.0, "cloud_mean": 0.40},
        "HIMADRI": {"temp_mean": -6.0, "wind_mean": 7.0, "cloud_mean": 0.65},
    }

    def __init__(self):
        pass

    def predict(
        self,
        station_id: str,
        forecast_origin: pd.Timestamp,
        horizons: List[int],
        historical_weather_df: pd.DataFrame,
        mode: Literal["CAUSAL", "ORACLE"] = "CAUSAL",
        oracle_future_df: Optional[pd.DataFrame] = None,
    ) -> WeatherForecastResult:
        """
        Generates forward weather predictions for target horizons k in horizons.
        
        Args:
            station_id: BHARATI | MAITRI | HIMADRI
            forecast_origin: Origin timestamp t
            horizons: List of lead times in hours (e.g. [1, 2, ..., 48])
            historical_weather_df: Historical telemetry strictly <= t
            mode: "CAUSAL" (production path) or "ORACLE" (diagnostic ablation only)
            oracle_future_df: Target dataset future rows, required only if mode == "ORACLE"
        """
        sid = station_id.upper()
        if sid not in self.CLIMATOLOGY:
            sid = "BHARATI"
        clima = self.CLIMATOLOGY[sid]

        if mode == "ORACLE":
            if oracle_future_df is None:
                raise ValueError("oracle_future_df must be provided when mode == 'ORACLE'")
            records = []
            for k in horizons:
                target_time = forecast_origin + pd.Timedelta(hours=k)
                future_row = oracle_future_df[oracle_future_df["timestamp"] == target_time]
                if not future_row.empty:
                    row = future_row.iloc[0]
                    records.append({
                        "horizon": k,
                        "timestamp": target_time,
                        "temperature_c": float(row["temperature_c"]),
                        "wind_speed_ms": float(row["wind_speed_ms"]),
                        "cloud_fraction": float(row["cloud_fraction"]),
                        "irradiance_wm2": float(row["irradiance_wm2"]),
                        "solar_elevation_deg": float(row["solar_elevation_deg"]),
                        "provenance": "DIAGNOSTIC_ORACLE"
                    })
                else:
                    # Fallback to causal if row missing in oracle dataset
                    records.append(self._predict_causal_step(sid, forecast_origin, k, historical_weather_df, clima))
            res_df = pd.DataFrame.from_records(records)
            return WeatherForecastResult(
                station_id=sid,
                forecast_origin=forecast_origin,
                horizons=horizons,
                df=res_df,
                mode="ORACLE",
                provenance="DIAGNOSTIC_ORACLE"
            )

        # Strictly CAUSAL production path:
        # Enforce that historical_weather_df does NOT contain any rows > forecast_origin
        history = historical_weather_df[historical_weather_df["timestamp"] <= forecast_origin]
        if history.empty:
            raise ValueError(f"No historical telemetry found at or before {forecast_origin}")

        records = [
            self._predict_causal_step(sid, forecast_origin, k, history, clima)
            for k in horizons
        ]
        res_df = pd.DataFrame.from_records(records)
        return WeatherForecastResult(
            station_id=sid,
            forecast_origin=forecast_origin,
            horizons=horizons,
            df=res_df,
            mode="CAUSAL",
            provenance="FORECAST"
        )

    def _predict_causal_step(
        self,
        station_id: str,
        forecast_origin: pd.Timestamp,
        k: int,
        history: pd.DataFrame,
        clima: Dict[str, float]
    ) -> Dict:
        """Computes causal weather projection for a single horizon k."""
        target_time = forecast_origin + pd.Timedelta(hours=k)
        
        # Origin state (latest observation <= t)
        last_row = history.iloc[-1]
        t_origin = float(last_row.get("temperature_c", clima["temp_mean"]))
        w_origin = float(last_row.get("wind_speed_ms", clima["wind_mean"]))
        c_origin = float(last_row.get("cloud_fraction", clima["cloud_mean"]))
        p_origin = float(last_row.get("pressure_hpa", 985.0))
        
        # Calculate 3-hour barometric trend if available
        if len(history) >= 4:
            p_3h_ago = float(history.iloc[-4].get("pressure_hpa", p_origin))
            delta_p_3h = p_origin - p_3h_ago
        else:
            delta_p_3h = 0.0

        # Astronomical solar elevation at target time t+k is deterministically known ahead
        # If solar_elevation_deg is provided in history or target, or compute approximate
        target_hour = target_time.hour
        target_doy = target_time.dayofyear
        
        # 1. Temperature projection:
        # Exponential memory decay (half-life 24h) toward seasonal mean + diurnal harmonic
        alpha_t = np.exp(-k / 24.0)
        diurnal_t = 2.5 * np.sin(2.0 * np.pi * (target_hour - 9) / 24.0)
        temp_pred = alpha_t * t_origin + (1.0 - alpha_t) * clima["temp_mean"] + diurnal_t

        # 2. Wind speed projection:
        # Autoregressive persistence + storm front acceleration from barometric drop
        alpha_w = np.exp(-k / 18.0)
        storm_boost = max(0.0, -delta_p_3h * 1.5) * np.exp(-k / 12.0)
        wind_pred = alpha_w * w_origin + (1.0 - alpha_w) * clima["wind_mean"] + storm_boost
        wind_pred = max(0.0, wind_pred)

        # 3. Cloud fraction projection:
        # Persistence decaying toward station average cloud cover
        alpha_c = np.exp(-k / 12.0)
        cloud_pred = alpha_c * c_origin + (1.0 - alpha_c) * clima["cloud_mean"]
        cloud_pred = float(np.clip(cloud_pred, 0.0, 1.0))

        # 4. Solar elevation calculation for target step:
        # Approximate solar elevation based on latitude and day of year
        lat_rad = np.radians(-69.4 if "BHARATI" in station_id else (-70.7 if "MAITRI" in station_id else 78.9))
        declination = np.radians(-23.44 * np.cos(np.radians(360.0 / 365.0 * (target_doy + 10))))
        hour_angle = np.radians(15.0 * (target_hour - 12))
        sin_elev = np.sin(lat_rad) * np.sin(declination) + np.cos(lat_rad) * np.cos(declination) * np.cos(hour_angle)
        solar_elev_deg = float(np.degrees(np.arcsin(np.clip(sin_elev, -1.0, 1.0))))

        # 5. Clear-sky surface irradiance estimate:
        if solar_elev_deg > 0.0:
            air_mass = 1.0 / max(0.05, np.sin(np.radians(solar_elev_deg)))
            i_clear = max(0.0, 1361.0 * np.sin(np.radians(solar_elev_deg)) * (0.7 ** (air_mass ** 0.678)))
            # Attenuate by forecast cloud fraction
            irr_pred = float(max(0.0, i_clear * (1.0 - 0.75 * (cloud_pred ** 1.5))))
        else:
            irr_pred = 0.0

        return {
            "horizon": k,
            "timestamp": target_time,
            "temperature_c": round(float(temp_pred), 2),
            "wind_speed_ms": round(float(wind_pred), 2),
            "cloud_fraction": round(float(cloud_pred), 3),
            "irradiance_wm2": round(float(irr_pred), 2),
            "solar_elevation_deg": round(solar_elev_deg, 2),
            "provenance": "FORECAST"
        }
