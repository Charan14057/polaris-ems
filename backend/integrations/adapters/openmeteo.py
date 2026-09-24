"""
POLARIS-EMS — Open-Meteo Polar Meteorological Adapter
SIH26061: Polar Energy Management & Resilience System

Workstream C: External Meteorological Reality Bridge
Connects to Open-Meteo polar weather forecast & reanalysis API.
Coordinates:
- BHARATI: -69.4069°S, 76.1878°E (Larsemann Hills)
- MAITRI:  -70.7667°S, 11.7333°E (Schirmacher Oasis)
- HIMADRI:  78.9244°N, 11.9286°E (Ny-Ålesund, Svalbard)

Provenance Rule:
External meteorological model forecasts are strictly categorized as 'SYNTHETIC' or 'ASSUMED',
NEVER mislabeled as 'REAL' physical polar station telemetry.
"""

import time
import json
import urllib.request
import urllib.error
import logging
from typing import Optional, Dict
from datetime import datetime, timezone

from backend.integrations.base import AbstractBaseProviderAdapter
from backend.integrations.schemas import ExternalWeatherObservation

logger = logging.getLogger("polaris.integrations.openmeteo")

POLAR_COORDINATES = {
    "BHARATI": {"latitude": -69.4069, "longitude": 76.1878},
    "MAITRI":  {"latitude": -70.7667, "longitude": 11.7333},
    "HIMADRI": {"latitude":  78.9244, "longitude": 11.9286},
}


class OpenMeteoPolarAdapter(AbstractBaseProviderAdapter):
    """Adapter for Open-Meteo polar numerical weather predictions."""

    def __init__(
        self,
        endpoint: str = "https://api.open-meteo.com/v1/forecast",
        timeout_sec: float = 10.0,
        enabled: bool = False
    ):
        super().__init__(name="OpenMeteo-Polar", enabled=enabled)
        self.endpoint = endpoint
        self.timeout_sec = timeout_sec

    def fetch_latest_weather(self, station_id: str) -> Optional[ExternalWeatherObservation]:
        """Fetches current observation/prediction for the specified station."""
        if not self.enabled:
            return None

        station_key = station_id.upper()
        if station_key not in POLAR_COORDINATES:
            logger.warning(f"[{self.name}] Unsupported station for Open-Meteo: {station_id}")
            return None

        coords = POLAR_COORDINATES[station_key]
        params = (
            f"latitude={coords['latitude']}&longitude={coords['longitude']}"
            f"&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,direct_normal_irradiance"
            f"&timezone=UTC"
        )
        url = f"{self.endpoint}?{params}"
        start_time = time.perf_counter()

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Polaris-EMS-PolarMicrogrid/1.0", "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency_ms = (time.perf_counter() - start_time) * 1000.0

            current = data.get("current", {})
            obs_time_str = current.get("time")
            if obs_time_str:
                obs_timestamp = datetime.fromisoformat(obs_time_str).replace(tzinfo=timezone.utc)
            else:
                obs_timestamp = datetime.now(timezone.utc)

            # Wind speed comes in km/h by default from Open-Meteo if not specified -> convert to m/s
            wind_kmh = float(current.get("wind_speed_10m", 0.0))
            wind_ms = round(wind_kmh / 3.6, 2)
            temp_c = float(current.get("temperature_2m", 0.0))
            dni = float(current.get("direct_normal_irradiance", 0.0))
            pressure = float(current.get("surface_pressure", 1013.25))
            humidity = float(current.get("relative_humidity_2m", 50.0))

            obs = ExternalWeatherObservation(
                station_id=station_key,
                timestamp=obs_timestamp,
                ambient_temperature_c=temp_c,
                wind_speed_ms=wind_ms,
                solar_irradiance_wm2=dni,
                direct_normal_irradiance_wm2=dni,
                surface_pressure_hpa=pressure,
                relative_humidity_pct=humidity,
                source_provider=self.name,
                provenance="SYNTHETIC",  # Strictly SYNTHETIC / reanalysis
                metadata={
                    "latitude": coords["latitude"],
                    "longitude": coords["longitude"],
                    "elevation_m": data.get("elevation", 0),
                    "model": "Open-Meteo Numerical Prediction"
                }
            )

            self.record_success(latency_ms)
            logger.info(f"[{self.name}] Successfully fetched {station_key}: T={temp_c}°C, Wind={wind_ms}m/s, Latency={latency_ms:.1f}ms")
            return obs

        except urllib.error.HTTPError as e:
            self.record_failure(f"HTTP Error {e.code}: {e.reason}")
            logger.warning(f"[{self.name}] HTTP Error fetching {station_key}: {e.code} {e.reason}")
            return None
        except urllib.error.URLError as e:
            self.record_failure(f"Network Unreachable: {e.reason}")
            logger.warning(f"[{self.name}] Network error fetching {station_key}: {e.reason}")
            return None
        except Exception as e:
            self.record_failure(f"Unexpected error: {str(e)}")
            logger.error(f"[{self.name}] Failed to parse response: {e}")
            return None

    def test_connectivity(self) -> bool:
        """Tests if Open-Meteo endpoint is reachable."""
        try:
            req = urllib.request.Request(
                f"{self.endpoint}?latitude=-69.4&longitude=76.2&current=temperature_2m",
                headers={"User-Agent": "Polaris-EMS-PolarMicrogrid/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                return resp.status == 200
        except Exception:
            return False
