"""
POLARIS-EMS — Phase 16 Telemetry Ingestion Validation (Workstream C)
SIH26061: Polar Energy Management & Resilience System

Extends the existing telemetry pipeline with robust field-condition handling
for adapter-originated telemetry. Integrates:
  Adapter → Telemetry Validation → Edge State → Local Buffer → Reconciliation

Does NOT create a second telemetry pipeline. Reuses:
  TelemetryReading, DeviceChannelConfig, TelemetryQualityEngine,
  EdgeEngine.ingest_telemetry

INVARIANTS:
  - Locked 6-tier provenance: {REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED}
  - Never fabricates field telemetry
  - All generated data carries provenance=SIMULATED or SYNTHETIC
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from backend.edge.schema import (
    TelemetryReading,
    DataQualityState,
    QualityValidationResult,
    validate_provenance,
)
from backend.edge.telemetry import TelemetryNormalizer
from backend.edge.quality import TelemetryQualityEngine


class TelemetryCondition:
    """Named constants for integration test conditions."""
    VALID = "VALID"
    STALE = "STALE"
    MISSING = "MISSING"
    DUPLICATE = "DUPLICATE"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    SUSPECT = "SUSPECT"
    DELAYED = "DELAYED"
    MALFORMED = "MALFORMED"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    INVALID_UNIT = "INVALID_UNIT"
    UNSUPPORTED_CHANNEL = "UNSUPPORTED_CHANNEL"
    DEVICE_UNAVAILABLE = "DEVICE_UNAVAILABLE"
    RECONNECT_BURST = "RECONNECT_BURST"


class AdapterTelemetryIngestor:
    """Bridges adapter-produced telemetry into the existing EdgeEngine pipeline.

    This class adds field-condition awareness on top of the existing
    TelemetryNormalizer and TelemetryQualityEngine.
    """

    def __init__(self, quality_engine: Optional[TelemetryQualityEngine] = None):
        self.quality_engine = quality_engine

    def validate_and_classify(
        self,
        reading: TelemetryReading,
        current_time: Optional[datetime] = None,
    ) -> Tuple[TelemetryReading, str]:
        """Run quality validation and return (reading, condition_name).

        The condition_name is one of the TelemetryCondition constants.
        """
        if self.quality_engine is None:
            return reading, TelemetryCondition.VALID

        result = self.quality_engine.validate(reading, current_time=current_time)
        condition = self._quality_to_condition(result)
        return reading, condition

    @staticmethod
    def _quality_to_condition(result: QualityValidationResult) -> str:
        """Map a quality validation result to a TelemetryCondition constant."""
        if result.is_valid:
            return TelemetryCondition.VALID
        mapping = {
            DataQualityState.STALE: TelemetryCondition.STALE,
            DataQualityState.MISSING: TelemetryCondition.MISSING,
            DataQualityState.DUPLICATE: TelemetryCondition.DUPLICATE,
            DataQualityState.OUT_OF_RANGE: TelemetryCondition.OUT_OF_RANGE,
            DataQualityState.OUT_OF_ORDER: TelemetryCondition.OUT_OF_ORDER,
            DataQualityState.SUSPECT: TelemetryCondition.SUSPECT,
        }
        return mapping.get(result.quality, TelemetryCondition.SUSPECT)

    @staticmethod
    def create_adapter_reading(
        station_id: str,
        device_id: str,
        channel: str,
        value: Any,
        unit: str,
        timestamp: Optional[datetime] = None,
        provenance: str = "SIMULATED",
        source: str = "adapter",
        environment: str = "SIMULATOR",
        sequence_number: Optional[int] = None,
    ) -> TelemetryReading:
        """Create a TelemetryReading from adapter-supplied data.

        Uses TelemetryNormalizer to ensure a canonical envelope.
        """
        return TelemetryNormalizer.create_envelope(
            station_id=station_id,
            device_id=device_id,
            channel=channel,
            value=value,
            unit=unit,
            timestamp=timestamp or datetime.now(timezone.utc),
            source=source,
            sequence_number=sequence_number,
            provenance=validate_provenance(provenance),
            quality=DataQualityState.VALID,
        )

    @staticmethod
    def generate_reconnect_burst(
        station_id: str,
        device_id: str,
        channel: str,
        unit: str,
        burst_size: int = 10,
        start_time: Optional[datetime] = None,
        interval_sec: float = 10.0,
        base_value: float = 50.0,
    ) -> List[TelemetryReading]:
        """Generate a burst of telemetry readings simulating reconnect replay.

        The readings have sequential timestamps and sequence numbers.
        """
        t0 = start_time or datetime.now(timezone.utc) - timedelta(seconds=burst_size * interval_sec)
        readings: List[TelemetryReading] = []
        for i in range(burst_size):
            ts = t0 + timedelta(seconds=i * interval_sec)
            reading = TelemetryNormalizer.create_envelope(
                station_id=station_id,
                device_id=device_id,
                channel=channel,
                value=round(base_value + i * 0.1, 2),
                unit=unit,
                timestamp=ts,
                source="reconnect_replay",
                sequence_number=i + 1,
                provenance="SIMULATED",
                quality=DataQualityState.VALID,
            )
            readings.append(reading)
        return readings
