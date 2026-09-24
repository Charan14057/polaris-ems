"""
POLARIS-EMS — Deterministic Device Health Assessment Engine
SIH26061: Polar Energy Management & Resilience System

Evaluates physical and virtual device health deterministically:
- Telemetry freshness and heartbeat monitoring.
- Quality error accumulation and failure rate ratios.
- Configured maintenance and operational flags.

HEALTH STATES:
- HEALTHY: Timely, valid telemetry arriving on all configured channels.
- DEGRADED: Stale readings, intermittent packet loss, or single-channel anomaly.
- UNAVAILABLE: Extended silence exceeding 3x freshness threshold.
- FAULT: Persistent out-of-range readings or reported sensor hardware fault.
- UNKNOWN: Insufficient telemetry history.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import dateutil.parser

from backend.edge.schema import (
    DeviceProfile,
    DeviceHealthState,
    DeviceHealthStatus,
    TelemetryReading,
    DataQualityState
)
from backend.edge.devices import DeviceRegistry, get_device_registry


class DeviceHealthRecord:
    """Internal state tracker for a single device's observations."""
    def __init__(self, device: DeviceProfile):
        self.device = device
        self.last_seen: Optional[datetime] = None
        self.last_valid_seen: Optional[datetime] = None
        self.total_readings: int = 0
        self.valid_readings: int = 0
        self.quality_failures: int = 0
        self.recent_qualities: List[DataQualityState] = []
        self.last_readings_by_channel: Dict[str, TelemetryReading] = {}


class DeviceHealthEngine:
    """Evaluates device health based on deterministic criteria."""

    def __init__(self, device_registry: Optional[DeviceRegistry] = None):
        self.device_registry = device_registry or get_device_registry()
        self._records: Dict[str, DeviceHealthRecord] = {}

    def _get_record(self, station_id: str, device_id: str) -> DeviceHealthRecord:
        key = f"{station_id.upper()}::{device_id}"
        if key not in self._records:
            device = self.device_registry.get_device(station_id, device_id)
            self._records[key] = DeviceHealthRecord(device)
        return self._records[key]

    def record_reading(self, reading: TelemetryReading) -> None:
        """Updates internal health tracking state with a new reading."""
        sid = reading.station_id.upper()
        if not self.device_registry.has_device(sid, reading.device_id):
            return

        rec = self._get_record(sid, reading.device_id)
        rec.total_readings += 1

        try:
            dt = dateutil.parser.parse(reading.received_at)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            dt = datetime.now(timezone.utc)

        rec.last_seen = dt
        rec.recent_qualities.append(reading.quality)
        if len(rec.recent_qualities) > 20:
            rec.recent_qualities.pop(0)

        if reading.quality == DataQualityState.VALID:
            rec.valid_readings += 1
            rec.last_valid_seen = dt
        else:
            rec.quality_failures += 1

        rec.last_readings_by_channel[reading.channel] = reading

    def evaluate_device(
        self,
        station_id: str,
        device_id: str,
        current_time: Optional[datetime] = None
    ) -> DeviceHealthStatus:
        """Determines health state and score for a device."""
        sid = station_id.upper()
        device = self.device_registry.get_device(sid, device_id)
        rec = self._get_record(sid, device_id)

        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        contributing_signals: List[str] = []
        diagnostics: List[str] = []

        if not device.enabled:
            return DeviceHealthStatus(
                device_id=device_id,
                station_id=sid,
                device_type=device.device_type,
                health_state=DeviceHealthState.UNAVAILABLE,
                health_score=0.0,
                contributing_signals=["DEVICE_DISABLED_BY_CONFIG"],
                last_seen=rec.last_seen.isoformat() if rec.last_seen else None,
                last_valid_telemetry=rec.last_valid_seen.isoformat() if rec.last_valid_seen else None,
                provenance="CONFIGURED",
                diagnostics=["Device is marked as disabled in station configuration"]
            )

        # If no telemetry has ever arrived
        if rec.last_seen is None:
            return DeviceHealthStatus(
                device_id=device_id,
                station_id=sid,
                device_type=device.device_type,
                health_state=DeviceHealthState.UNKNOWN,
                health_score=0.5,
                contributing_signals=["NO_TELEMETRY_RECORDED"],
                last_seen=None,
                last_valid_telemetry=None,
                provenance="CONFIGURED",
                diagnostics=["No telemetry envelope has been received since node startup"]
            )

        silence_sec = (now - rec.last_seen).total_seconds()
        valid_silence_sec = (now - rec.last_valid_seen).total_seconds() if rec.last_valid_seen else silence_sec
        threshold = device.freshness_threshold_sec

        # 1. Check for hard FAULT (persistent out-of-range or recent failures)
        recent_window = rec.recent_qualities[-5:] if rec.recent_qualities else []
        out_of_range_count = sum(1 for q in recent_window if q == DataQualityState.OUT_OF_RANGE)
        suspect_count = sum(1 for q in recent_window if q == DataQualityState.SUSPECT)

        if out_of_range_count >= 3:
            state = DeviceHealthState.FAULT
            score = 0.2
            contributing_signals.append(f"{out_of_range_count}_RECENT_OUT_OF_RANGE_READINGS")
            diagnostics.append(f"Device sensor has emitted {out_of_range_count} out-of-range readings in last {len(recent_window)} messages")
        elif valid_silence_sec > threshold * 3.0:
            # 2. Check for UNAVAILABLE (silence > 3x threshold)
            state = DeviceHealthState.UNAVAILABLE
            score = 0.0
            contributing_signals.append(f"EXTENDED_SILENCE_{valid_silence_sec:.1f}S")
            diagnostics.append(f"No valid telemetry received for {valid_silence_sec:.1f}s (exceeds 3x threshold {threshold * 3.0}s)")
        elif valid_silence_sec > threshold:
            # 3. Check for DEGRADED (silence > 1x threshold or moderate quality errors)
            state = DeviceHealthState.DEGRADED
            score = max(0.3, 1.0 - (valid_silence_sec / (threshold * 3.0)))
            contributing_signals.append(f"TELEMETRY_STALE_{valid_silence_sec:.1f}S")
            diagnostics.append(f"Valid telemetry delayed: elapsed {valid_silence_sec:.1f}s exceeds threshold {threshold}s")
        elif suspect_count >= 2:
            state = DeviceHealthState.DEGRADED
            score = 0.65
            contributing_signals.append(f"{suspect_count}_SUSPECT_READINGS")
            diagnostics.append(f"Device has emitted {suspect_count} suspect readings")
        else:
            # 4. HEALTHY
            state = DeviceHealthState.HEALTHY
            score = 1.0
            contributing_signals.append("NOMINAL_REPORTING_INTERVAL")

        return DeviceHealthStatus(
            device_id=device_id,
            station_id=sid,
            device_type=device.device_type,
            health_state=state,
            health_score=round(score, 3),
            contributing_signals=contributing_signals,
            last_seen=rec.last_seen.isoformat() if rec.last_seen else None,
            last_valid_telemetry=rec.last_valid_seen.isoformat() if rec.last_valid_seen else None,
            provenance="CONFIGURED",
            diagnostics=diagnostics
        )

    def evaluate_fleet(self, station_id: str, current_time: Optional[datetime] = None) -> List[DeviceHealthStatus]:
        """Evaluates health for all devices in a station catalog."""
        sid = station_id.upper()
        catalog = self.device_registry.get_catalog(sid)
        return [self.evaluate_device(sid, d.device_id, current_time=current_time) for d in catalog.devices]
