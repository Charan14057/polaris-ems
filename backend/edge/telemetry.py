"""
POLARIS-EMS — Edge Telemetry Normalization & Ingestion Envelopes
SIH26061: Polar Energy Management & Resilience System

Provides canonical normalization for heterogeneous telemetry coming from
polar sensors, field protocols (Modbus, CAN, BACnet, Serial), or synthetic harnesses.

INVARIANTS:
- Preserves 6-tier provenance strictly.
- Does not modify values or fabricate measurements.
- Normalizes timestamps to ISO-8601 UTC.
"""

from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone
import dateutil.parser

from backend.edge.schema import (
    TelemetryReading,
    DataQualityState,
    validate_provenance
)


class TelemetryNormalizer:
    """Normalizes raw incoming telemetry dictionaries into canonical TelemetryReading envelopes."""

    @staticmethod
    def normalize_timestamp(ts: Union[str, float, int, datetime]) -> str:
        """Parses and formats timestamps to standard UTC ISO-8601 string."""
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.isoformat()
        elif isinstance(ts, datetime):
            if ts.tzinfo is None:
                dt = ts.replace(tzinfo=timezone.utc)
            else:
                dt = ts.astimezone(timezone.utc)
            return dt.isoformat()
        elif isinstance(ts, str):
            try:
                dt = dateutil.parser.parse(ts)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt.isoformat()
            except Exception as e:
                raise ValueError(f"Invalid timestamp format: '{ts}'. Error: {e}")
        else:
            raise TypeError(f"Unsupported timestamp type: {type(ts)}")

    @classmethod
    def create_envelope(
        cls,
        station_id: str,
        device_id: str,
        channel: str,
        value: Union[float, int, str, bool],
        unit: str,
        timestamp: Optional[Union[str, float, int, datetime]] = None,
        source: str = "edge_sensor",
        sequence_number: Optional[int] = None,
        provenance: str = "SYNTHETIC",
        quality: DataQualityState = DataQualityState.VALID
    ) -> TelemetryReading:
        """Creates a validated TelemetryReading."""
        now_iso = datetime.now(timezone.utc).isoformat()
        ts_iso = cls.normalize_timestamp(timestamp) if timestamp is not None else now_iso

        prov_validated = validate_provenance(provenance)

        return TelemetryReading(
            timestamp=ts_iso,
            station_id=station_id.upper(),
            device_id=device_id,
            channel=channel,
            value=value,
            unit=unit,
            quality=quality,
            source=source,
            received_at=now_iso,
            sequence_number=sequence_number,
            provenance=prov_validated,
            validation_status="ACCEPTED" if quality == DataQualityState.VALID else "QUARANTINED",
            diagnostics=[]
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TelemetryReading:
        """Parses a dictionary payload into a TelemetryReading."""
        required = ["station_id", "device_id", "channel", "value", "unit"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required telemetry field: '{field}'")

        return cls.create_envelope(
            station_id=data["station_id"],
            device_id=data["device_id"],
            channel=data["channel"],
            value=data["value"],
            unit=data["unit"],
            timestamp=data.get("timestamp"),
            source=data.get("source", "edge_sensor"),
            sequence_number=data.get("sequence_number"),
            provenance=data.get("provenance", "SYNTHETIC"),
            quality=DataQualityState(data.get("quality", "VALID"))
        )
