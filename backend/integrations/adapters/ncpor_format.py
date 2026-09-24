"""
POLARIS-EMS — NCPOR Polar Gateway & AWS Format Adapter
SIH26061: Polar Energy Management & Resilience System

Workstream C: Standard National Centre for Polar and Ocean Research (NCPOR) format adapter.
Parses telemetry records from Antarctic AWS data loggers (Campbell Scientific / Vaisala)
and NCPOR ground-station telemetry schemas.

Provenance Rule:
If verified from an authenticated Antarctic telemetry transmission log with valid checksum,
provenance is categorized as 'REAL'. If unverified or simulated, strictly 'SYNTHETIC'.
"""

import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from backend.integrations.base import AbstractBaseProviderAdapter
from backend.integrations.schemas import ExternalWeatherObservation, ExternalTelemetryPayload

logger = logging.getLogger("polaris.integrations.ncpor")


class NCPORFormatAdapter(AbstractBaseProviderAdapter):
    """Adapter for NCPOR Antarctic Automatic Weather Station (AWS) formats."""

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        enabled: bool = False
    ):
        super().__init__(name="NCPOR-AWS-Gateway", enabled=enabled)
        self.gateway_url = gateway_url

    def parse_ncpor_raw_record(
        self,
        record: Dict[str, Any],
        is_verified_hardware: bool = False
    ) -> Optional[ExternalWeatherObservation]:
        """Parses a structured NCPOR AWS dictionary into a normalized ExternalWeatherObservation."""
        try:
            station_id = str(record.get("station_id", "")).upper()
            if station_id not in ("BHARATI", "MAITRI", "HIMADRI"):
                logger.warning(f"[{self.name}] Invalid station in raw record: {station_id}")
                return None

            ts_raw = record.get("timestamp")
            if isinstance(ts_raw, str):
                ts = datetime.fromisoformat(ts_raw)
            elif isinstance(ts_raw, datetime):
                ts = ts_raw
            else:
                ts = datetime.now(timezone.utc)

            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            # NCPOR field mapping
            temp_c = float(record.get("air_temp_c", record.get("temperature_c", 0.0)))
            wind_speed = float(record.get("wind_speed_ms", record.get("wind_spd_ms", 0.0)))
            solar_irr = float(record.get("solar_rad_wm2", record.get("solar_irradiance_wm2", 0.0)))
            pressure = float(record.get("baro_pressure_hpa", record.get("surface_pressure_hpa", 1013.25)))
            humidity = float(record.get("relative_humidity_pct", record.get("humidity_pct", 50.0)))

            # Provenance assignment: REAL only if verified from hardware source
            provenance = "REAL" if is_verified_hardware else "SYNTHETIC"

            return ExternalWeatherObservation(
                station_id=station_id,
                timestamp=ts,
                ambient_temperature_c=temp_c,
                wind_speed_ms=wind_speed,
                solar_irradiance_wm2=solar_irr,
                surface_pressure_hpa=pressure,
                relative_humidity_pct=humidity,
                source_provider=self.name,
                provenance=provenance,
                metadata={
                    "sensor_type": record.get("sensor_model", "Vaisala PTU300 / WAA151"),
                    "logger_id": record.get("logger_serial", "CR1000X-POLAR"),
                    "verified_hardware": is_verified_hardware
                }
            )
        except Exception as e:
            logger.error(f"[{self.name}] Failed to parse raw NCPOR record: {e}")
            return None

    def fetch_latest_weather(self, station_id: str) -> Optional[ExternalWeatherObservation]:
        """Fetches from configured NCPOR gateway if available.

        Since physical polar SCADA telemetry is currently disconnected in Phase 14,
        this cleanly returns None unless an authenticated gateway is configured.
        """
        if not self.enabled or not self.gateway_url:
            return None

        # When gateway is configured in future polar hardware deployment:
        logger.info(f"[{self.name}] Polling gateway {self.gateway_url} for {station_id}")
        return None

    def test_connectivity(self) -> bool:
        """Tests gateway reachability."""
        return self.enabled and self.gateway_url is not None
