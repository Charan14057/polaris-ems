"""
POLARIS-EMS — Deterministic Telemetry Quality Validation Engine
SIH26061: Polar Energy Management & Resilience System

Performs rigorous deterministic validation on ingested field telemetry:
- Timestamp formatting, future clock skew, and historical retention limits.
- Station identity and device registration consistency.
- Channel registration and unit conformance.
- Range bounds against configured safety/operational envelopes.
- Freshness against configured freshness thresholds.
- Sequence ordering and duplicate detection.

INVARIANTS:
- Deterministic validation only.
- Never silently drops invalid or suspect data.
- Returns explicit reasons for every non-VALID state.
"""

from typing import Dict, Tuple, Optional
from datetime import datetime, timezone
import dateutil.parser

from backend.edge.schema import (
    TelemetryReading,
    DataQualityState,
    QualityValidationResult
)
from backend.edge.devices import DeviceRegistry, get_device_registry


class TelemetryQualityEngine:
    """Deterministic validation engine for field device telemetry streams."""

    def __init__(
        self,
        device_registry: Optional[DeviceRegistry] = None,
        max_future_skew_sec: float = 60.0,
        max_retention_age_sec: float = 86400.0 * 7.0  # 7 days
    ):
        self.device_registry = device_registry or get_device_registry()
        self.max_future_skew_sec = max_future_skew_sec
        self.max_retention_age_sec = max_retention_age_sec

        # State tracking for sequence & duplicate detection:
        # key: (station_id, device_id, channel) -> (last_timestamp_iso, last_sequence_number)
        self._last_observations: Dict[Tuple[str, str, str], Tuple[str, Optional[int]]] = {}

    def reset_state(self) -> None:
        """Clears sequence and duplicate tracking caches."""
        self._last_observations.clear()

    def validate(
        self,
        reading: TelemetryReading,
        current_time: Optional[datetime] = None
    ) -> QualityValidationResult:
        """
        Runs comprehensive deterministic checks against a TelemetryReading.
        Updates reading.quality, reading.validation_status, and reading.diagnostics in-place.
        """
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # 1. Parse and validate observation timestamp
        try:
            obs_dt = dateutil.parser.parse(reading.timestamp)
            if obs_dt.tzinfo is None:
                obs_dt = obs_dt.replace(tzinfo=timezone.utc)
        except Exception as e:
            reason = f"Malformed observation timestamp '{reading.timestamp}': {e}"
            return self._fail(reading, DataQualityState.SUSPECT, reason, "INVALID_TIMESTAMP")

        age_sec = (now - obs_dt).total_seconds()

        # Future clock skew check
        if age_sec < -self.max_future_skew_sec:
            reason = f"Timestamp is in the future by {-age_sec:.1f}s (max allowed skew: {self.max_future_skew_sec}s)"
            return self._fail(reading, DataQualityState.SUSPECT, reason, "FUTURE_TIMESTAMP")

        # Ancient retention age check
        if age_sec > self.max_retention_age_sec:
            reason = f"Timestamp is too old ({age_sec / 86400.0:.1f} days, max retention: {self.max_retention_age_sec / 86400.0} days)"
            return self._fail(reading, DataQualityState.STALE, reason, "EXPIRED_RETENTION")

        # 2. Check station and device registration
        sid = reading.station_id.upper()
        if not self.device_registry.has_device(sid, reading.device_id):
            reason = f"Device '{reading.device_id}' is not registered under station '{sid}'"
            return self._fail(reading, DataQualityState.SUSPECT, reason, "DEVICE_NOT_REGISTERED")

        device = self.device_registry.get_device(sid, reading.device_id)

        # Check if device is enabled
        if not device.enabled:
            reason = f"Device '{reading.device_id}' is marked as DISABLED in configuration"
            return self._fail(reading, DataQualityState.SUSPECT, reason, "DEVICE_DISABLED")

        # 3. Check channel configuration
        channel_cfg = None
        for ch in device.telemetry_channels:
            if ch.channel == reading.channel:
                channel_cfg = ch
                break

        if channel_cfg is None:
            reason = f"Channel '{reading.channel}' is not configured for device '{reading.device_id}'"
            return self._fail(reading, DataQualityState.MISSING, reason, "UNKNOWN_CHANNEL")

        # 4. Unit consistency check
        if reading.unit.strip().lower() != channel_cfg.unit.strip().lower():
            reason = f"Unit mismatch on channel '{reading.channel}': received '{reading.unit}', expected '{channel_cfg.unit}'"
            return self._fail(reading, DataQualityState.SUSPECT, reason, "UNIT_MISMATCH")

        # 5. Range bounds check for numeric values
        expected_range = [channel_cfg.min_val, channel_cfg.max_val]
        if isinstance(reading.value, (int, float)):
            val = float(reading.value)
            if val < channel_cfg.min_val or val > channel_cfg.max_val:
                reason = (
                    f"Value {val} on channel '{reading.channel}' is outside configured range "
                    f"[{channel_cfg.min_val}, {channel_cfg.max_val}] {channel_cfg.unit}"
                )
                return self._fail(reading, DataQualityState.OUT_OF_RANGE, reason, "VALUE_OUT_OF_RANGE", expected_range=expected_range)

        # 6. Duplicate and Sequence check
        key = (sid, reading.device_id, reading.channel)
        last_obs = self._last_observations.get(key)
        if last_obs is not None:
            last_ts, last_seq = last_obs
            # Duplicate check
            if reading.timestamp == last_ts:
                reason = f"Duplicate telemetry timestamp detected: '{reading.timestamp}' on channel '{reading.channel}'"
                return self._fail(reading, DataQualityState.DUPLICATE, reason, "DUPLICATE_READING")

            # Sequence check
            if reading.sequence_number is not None and last_seq is not None:
                if reading.sequence_number < last_seq:
                    reason = f"Out of order sequence: received seq={reading.sequence_number}, previous seq={last_seq}"
                    return self._fail(reading, DataQualityState.OUT_OF_ORDER, reason, "OUT_OF_ORDER_SEQUENCE")

        # 7. Freshness check
        freshness_limit = channel_cfg.freshness_limit_seconds or device.freshness_threshold_sec
        if age_sec > freshness_limit:
            reason = f"Telemetry is stale: observed age {age_sec:.1f}s exceeds freshness threshold of {freshness_limit}s"
            # Stale data is quarantined rather than rejected
            return self._fail(reading, DataQualityState.STALE, reason, "STALE_DATA", is_valid=False)

        # All checks passed: Record observation state and accept reading
        self._last_observations[key] = (reading.timestamp, reading.sequence_number)
        reading.quality = DataQualityState.VALID
        reading.validation_status = "ACCEPTED"

        return QualityValidationResult(
            is_valid=True,
            quality=DataQualityState.VALID,
            reason=None,
            rejection_code=None,
            checked_channel=reading.channel,
            observed_value=reading.value,
            expected_range=expected_range,
            latency_sec=max(0.0, age_sec)
        )

    def _fail(
        self,
        reading: TelemetryReading,
        quality: DataQualityState,
        reason: str,
        rejection_code: str,
        expected_range: Optional[list] = None,
        is_valid: bool = False
    ) -> QualityValidationResult:
        """Helper to mark reading invalid and construct result envelope."""
        reading.quality = quality
        reading.validation_status = "QUARANTINED" if quality == DataQualityState.STALE else "REJECTED"
        reading.diagnostics.append(f"[{rejection_code}] {reason}")

        return QualityValidationResult(
            is_valid=is_valid,
            quality=quality,
            reason=reason,
            rejection_code=rejection_code,
            checked_channel=reading.channel,
            observed_value=reading.value,
            expected_range=expected_range,
            latency_sec=0.0
        )
