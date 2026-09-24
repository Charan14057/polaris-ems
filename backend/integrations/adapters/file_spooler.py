"""
POLARIS-EMS — Offline Staging & File Spooler Reality Adapter
SIH26061: Polar Energy Management & Resilience System

Workstream C: Air-Gapped Polar Satcom File Spooler
Reads queued observation JSON/CSV dumps dropped from sporadic satellite links.
Safely ingests external data without requiring active continuous internet connectivity.
"""

import os
import json
import logging
from typing import Optional, List
from datetime import datetime, timezone

from backend.integrations.base import AbstractBaseProviderAdapter
from backend.integrations.schemas import ExternalWeatherObservation

logger = logging.getLogger("polaris.integrations.spooler")


class OfflineFileSpoolerAdapter(AbstractBaseProviderAdapter):
    """Adapter for offline staged satellite packet files in polar air-gapped mode."""

    def __init__(
        self,
        spool_dir: str = "datasets/incoming_spool",
        enabled: bool = True
    ):
        super().__init__(name="Offline-Satcom-Spooler", enabled=enabled)
        self.spool_dir = spool_dir

    def fetch_latest_weather(self, station_id: str) -> Optional[ExternalWeatherObservation]:
        """Reads latest staged observation for the given station from the spool directory."""
        if not self.enabled or not os.path.isdir(self.spool_dir):
            return None

        station_key = station_id.upper()
        station_spool_dir = os.path.join(self.spool_dir, station_key)
        if not os.path.isdir(station_spool_dir):
            return None

        try:
            files = sorted(
                [f for f in os.listdir(station_spool_dir) if f.endswith(".json")],
                reverse=True
            )
            if not files:
                return None

            latest_file = os.path.join(station_spool_dir, files[0])
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            ts_str = data.get("timestamp")
            if ts_str:
                ts = datetime.fromisoformat(ts_str)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = datetime.now(timezone.utc)

            obs = ExternalWeatherObservation(
                station_id=station_key,
                timestamp=ts,
                ambient_temperature_c=float(data.get("ambient_temperature_c", -15.0)),
                wind_speed_ms=float(data.get("wind_speed_ms", 12.0)),
                solar_irradiance_wm2=float(data.get("solar_irradiance_wm2", 0.0)),
                surface_pressure_hpa=data.get("surface_pressure_hpa"),
                relative_humidity_pct=data.get("relative_humidity_pct"),
                source_provider=self.name,
                provenance=data.get("provenance", "SYNTHETIC"),
                metadata={"spool_file": latest_file}
            )
            self.record_success(0.5)
            return obs

        except Exception as e:
            self.record_failure(f"Error reading spool file: {e}")
            logger.error(f"[{self.name}] Failed to read spool: {e}")
            return None

    def test_connectivity(self) -> bool:
        """Verifies if the spool directory exists."""
        return os.path.isdir(self.spool_dir)
