"""
POLARIS-EMS — Weather Ingestion Adapters
SIH26061: Polar Energy Management & Resilience System

Ingests, validates, standardizes, and quality-checks real meteorological data from:
1. NCPOR / National Polar Data Center (NPDC) Automatic Weather Station (AWS) datasets.
2. Copernicus ERA5 single-level hourly atmospheric reanalysis.

Strictly labels data provenance as REAL (for in-situ station observations)
or REAL (REANALYSIS) for ERA5. Enforces physical unit conversions to standard SI:
- Temperature: Celsius (°C)
- Wind speed: meters per second (m/s)
- Solar irradiance: Watts per square meter (W/m²)
- Pressure: Hectopascals (hPa)
- Relative humidity: Percentage (%)
"""

import math
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from backend.data.provenance.metadata import ProvenanceTier, ProvenanceRecord


class WeatherStandardSchema:
    """Canonical columns and units for all weather data inside Polaris-EMS."""
    REQUIRED_COLUMNS = [
        "timestamp",
        "station_id",
        "ambient_temperature_c",
        "wind_speed_ms",
        "wind_direction_deg",
        "solar_irradiance_wm2",
        "provenance_tier",
    ]
    OPTIONAL_COLUMNS = [
        "relative_humidity_pct",
        "atmospheric_pressure_hpa",
        "cloud_cover_fraction",
    ]


class WeatherIngestionAdapter:
    """Ingests and standardizes polar weather datasets with quality control checks."""

    @staticmethod
    def validate_and_clean(df: pd.DataFrame, station_id: str) -> pd.DataFrame:
        """
        Validates timestamps, sorts chronologically, removes duplicates,
        and enforces polar physical plausibility bounds.
        """
        df = df.copy()
        if "timestamp" not in df.columns:
            raise ValueError("Dataframe must contain a 'timestamp' column.")

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        df["station_id"] = station_id.upper()

        # Physical limit checks
        # Polar temperature bounds: -75°C to +25°C
        if "ambient_temperature_c" in df.columns:
            df["ambient_temperature_c"] = df["ambient_temperature_c"].clip(lower=-75.0, upper=25.0)

        # Wind speed >= 0, maximum realistic gust 70 m/s
        if "wind_speed_ms" in df.columns:
            df["wind_speed_ms"] = df["wind_speed_ms"].clip(lower=0.0, upper=70.0)

        # Wind direction in [0, 360)
        if "wind_direction_deg" in df.columns:
            df["wind_direction_deg"] = df["wind_direction_deg"] % 360.0

        # Solar irradiance >= 0, top of atmosphere max solar constant ~1361 W/m2
        if "solar_irradiance_wm2" in df.columns:
            df["solar_irradiance_wm2"] = df["solar_irradiance_wm2"].clip(lower=0.0, upper=1400.0)

        # Cloud cover in [0.0, 1.0]
        if "cloud_cover_fraction" in df.columns:
            df["cloud_cover_fraction"] = df["cloud_cover_fraction"].clip(lower=0.0, upper=1.0)

        return df

    @classmethod
    def ingest_ncpor_aws_csv(cls, file_path: Path, station_id: str) -> pd.DataFrame:
        """
        Ingests NCPOR / NPDC Automatic Weather Station CSV records.
        Maps variable column naming variations (e.g. 'Air_Temp', 'Ta', 'Wind_Spd') to canonical fields.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"NCPOR weather file not found at: {file_path}")

        raw = pd.read_csv(file_path)
        col_map = {col.strip().lower(): col for col in raw.columns}

        # Identify timestamp column
        ts_col = None
        for candidate in ["datetime", "date_time", "timestamp", "date"]:
            if candidate in col_map:
                ts_col = col_map[candidate]
                break

        if ts_col is None:
            raise ValueError(f"Could not locate timestamp column in NCPOR dataset: {list(raw.columns)}")

        out = pd.DataFrame()
        out["timestamp"] = pd.to_datetime(raw[ts_col])

        # Temperature
        temp_col = next((col_map[c] for c in ["temp_air", "air_temp", "temperature", "ta", "temp"] if c in col_map), None)
        out["ambient_temperature_c"] = raw[temp_col].astype(float) if temp_col else np.nan

        # Wind speed
        wind_col = next((col_map[c] for c in ["wind_speed", "wind_spd", "ws", "ff"] if c in col_map), None)
        out["wind_speed_ms"] = raw[wind_col].astype(float) if wind_col else np.nan

        # Wind direction
        wdir_col = next((col_map[c] for c in ["wind_dir", "wind_direction", "wd", "dd"] if c in col_map), None)
        out["wind_direction_deg"] = raw[wdir_col].astype(float) if wdir_col else 0.0

        # Solar radiation
        rad_col = next((col_map[c] for c in ["solar_rad", "solar_irradiance", "rad", "sw_down", "ghi"] if c in col_map), None)
        out["solar_irradiance_wm2"] = raw[rad_col].astype(float) if rad_col else 0.0

        # Relative humidity
        rh_col = next((col_map[c] for c in ["rel_hum", "humidity", "rh"] if c in col_map), None)
        if rh_col:
            out["relative_humidity_pct"] = raw[rh_col].astype(float)

        # Pressure
        press_col = next((col_map[c] for c in ["pressure", "press_station", "p_air", "hpa"] if c in col_map), None)
        if press_col:
            out["atmospheric_pressure_hpa"] = raw[press_col].astype(float)

        out["provenance_tier"] = ProvenanceTier.REAL.value
        return cls.validate_and_clean(out, station_id)

    @classmethod
    def ingest_era5_reanalysis_csv(cls, file_path: Path, station_id: str) -> pd.DataFrame:
        """
        Ingests Copernicus ERA5 hourly reanalysis data.
        Converts:
        - 2m Temperature: Kelvin -> Celsius (K - 273.15)
        - 10m Wind components (u, v): sqrt(u^2 + v^2) -> wind speed (m/s)
        - Wind direction: (atan2(-u, -v) * 180 / pi) % 360
        - Solar radiation: Joules/m2 per hour -> W/m2 (div by 3600s)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"ERA5 file not found at: {file_path}")

        raw = pd.read_csv(file_path)
        col_map = {col.strip().lower(): col for col in raw.columns}

        ts_col = next((col_map[c] for c in ["valid_time", "time", "date", "timestamp"] if c in col_map), None)
        if not ts_col:
            raise ValueError(f"No timestamp found in ERA5 dataset: {list(raw.columns)}")

        out = pd.DataFrame()
        out["timestamp"] = pd.to_datetime(raw[ts_col])

        # Temperature (2m_temperature in Kelvin)
        t2m_col = next((col_map[c] for c in ["t2m", "2m_temperature", "temperature"] if c in col_map), None)
        if t2m_col:
            vals = raw[t2m_col].astype(float)
            # If values > 150, assume Kelvin
            out["ambient_temperature_c"] = vals - 273.15 if (vals > 150).all() else vals

        # Wind components (u10, v10)
        u_col = next((col_map[c] for c in ["u10", "10m_u_component_of_wind"] if c in col_map), None)
        v_col = next((col_map[c] for c in ["v10", "10m_v_component_of_wind"] if c in col_map), None)
        if u_col and v_col:
            u = raw[u_col].astype(float)
            v = raw[v_col].astype(float)
            out["wind_speed_ms"] = np.sqrt(u**2 + v**2)
            out["wind_direction_deg"] = (np.degrees(np.arctan2(-u, -v)) + 360.0) % 360.0

        # Solar radiation (ssrd: Surface Solar Radiation Downwards in J/m2)
        ssrd_col = next((col_map[c] for c in ["ssrd", "surface_solar_radiation_downwards"] if c in col_map), None)
        if ssrd_col:
            # ERA5 ssrd is hourly accumulated Joules/m2. 1 Watt = 1 Joule/sec.
            # 1 hour = 3600 seconds -> SSRD (J/m2) / 3600 = Mean Watts/m2
            out["solar_irradiance_wm2"] = raw[ssrd_col].astype(float) / 3600.0

        # Total cloud cover (tcc) in fraction [0, 1]
        tcc_col = next((col_map[c] for c in ["tcc", "total_cloud_cover"] if c in col_map), None)
        if tcc_col:
            out["cloud_cover_fraction"] = raw[tcc_col].astype(float)

        out["provenance_tier"] = ProvenanceTier.REAL.value
        return cls.validate_and_clean(out, station_id)
