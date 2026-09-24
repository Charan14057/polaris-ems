"""
POLARIS-EMS — Deterministic Field Device & Connectivity Simulation Harness
SIH26061: Polar Energy Management & Resilience System

Provides a controlled, deterministic simulation harness for polar field conditions:
- Generates realistic synthetic telemetry for all configured device classes.
- Simulates communication degradation, blackouts, packet loss, and buffer growth.
- Injects edge edge-cases: staleness, out-of-range sensor spikes, duplicates, out-of-order sequences.

INVARIANTS:
- All generated telemetry is explicitly labeled provenance="SYNTHETIC".
- Never claims actual physical Antarctic/Arctic field connection.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import random

from backend.edge.schema import (
    TelemetryReading,
    DataQualityState,
    DeviceType
)
from backend.edge.devices import DeviceRegistry, get_device_registry
from backend.edge.telemetry import TelemetryNormalizer


class EdgeSimulationHarness:
    """Deterministic simulation harness for polar edge telemetry."""

    def __init__(self, device_registry: Optional[DeviceRegistry] = None):
        self.device_registry = device_registry or get_device_registry()
        self._seq_counters: Dict[str, int] = {}

    def _next_seq(self, device_id: str) -> int:
        self._seq_counters[device_id] = self._seq_counters.get(device_id, 0) + 1
        return self._seq_counters[device_id]

    def generate_nominal_reading(
        self,
        station_id: str,
        device_id: str,
        channel_name: str,
        timestamp: Optional[datetime] = None
    ) -> TelemetryReading:
        """Generates a nominal, valid telemetry reading within configured ranges."""
        sid = station_id.upper()
        device = self.device_registry.get_device(sid, device_id)

        target_ch = None
        for ch in device.telemetry_channels:
            if ch.channel == channel_name:
                target_ch = ch
                break

        if target_ch is None:
            raise KeyError(f"Channel '{channel_name}' not configured for device '{device_id}'")

        # Generate a mid-range value
        mid = (target_ch.min_val + target_ch.max_val) / 2.0
        spread = (target_ch.max_val - target_ch.min_val) * 0.2
        val = round(mid + (spread * 0.1), 2)

        ts = timestamp or datetime.now(timezone.utc)
        seq = self._next_seq(device_id)

        return TelemetryNormalizer.create_envelope(
            station_id=sid,
            device_id=device_id,
            channel=channel_name,
            value=val,
            unit=target_ch.unit,
            timestamp=ts,
            source="simulated_field_sensor",
            sequence_number=seq,
            provenance="SYNTHETIC",
            quality=DataQualityState.VALID
        )

    def generate_station_snapshot(
        self,
        station_id: str,
        timestamp: Optional[datetime] = None
    ) -> List[TelemetryReading]:
        """Generates a full sweep of nominal readings across all devices in a station."""
        sid = station_id.upper()
        catalog = self.device_registry.get_catalog(sid)
        readings: List[TelemetryReading] = []
        ts = timestamp or datetime.now(timezone.utc)

        for dev in catalog.devices:
            if not dev.enabled:
                continue
            for ch in dev.telemetry_channels:
                r = self.generate_nominal_reading(sid, dev.device_id, ch.channel, timestamp=ts)
                readings.append(r)

        return readings

    def generate_scenario_telemetry(
        self,
        station_id: str,
        scenario_name: str,
        timestamp: Optional[datetime] = None
    ) -> List[TelemetryReading]:
        """
        Generates telemetry tailored to specific test conditions:
        - NORMAL
        - DEVICE_STALE
        - DEVICE_FAILURE
        - DUPLICATE_TELEMETRY
        - OUT_OF_ORDER_TELEMETRY
        - OUT_OF_RANGE
        """
        sid = station_id.upper()
        ts = timestamp or datetime.now(timezone.utc)
        readings = self.generate_station_snapshot(sid, timestamp=ts)

        if scenario_name == "NORMAL":
            return readings

        elif scenario_name == "DEVICE_STALE":
            # Artificially age the timestamp of the first device by 150 seconds
            stale_ts = ts - timedelta(seconds=150)
            target_dev = readings[0].device_id
            for r in readings:
                if r.device_id == target_dev:
                    r.timestamp = stale_ts.isoformat()

        elif scenario_name == "DEVICE_FAILURE":
            # Force severe out-of-range on primary generator
            for r in readings:
                if "gen" in r.device_id and "coolant_temp" in r.channel:
                    r.value = 150.0  # Above 120.0 max

        elif scenario_name == "OUT_OF_RANGE":
            # Set a bus voltage to 500V (max 460V)
            for r in readings:
                if "bus_voltage" in r.channel:
                    r.value = 520.0

        elif scenario_name == "DUPLICATE_TELEMETRY":
            # Duplicate the first reading
            dup = readings[0].model_copy(deep=True)
            readings.append(dup)

        elif scenario_name == "OUT_OF_ORDER_TELEMETRY":
            # Reverse sequence numbers on the first two readings
            if len(readings) >= 2:
                readings[1].sequence_number = 1
                readings[0].sequence_number = 5

        return readings
