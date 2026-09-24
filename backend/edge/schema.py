"""
POLARIS-EMS — Edge Domain Schemas & Contracts
SIH26061: Polar Energy Management & Resilience System

Defines typed schemas and enums for device intelligence, telemetry normalization,
data quality, device health, edge connectivity, bounded buffering, and reconciliation.

STRICT INVARIANTS:
1. Locked 6-tier provenance taxonomy: {REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED}.
2. Quality states and Edge modes are operational states, NEVER provenance tiers.
3. No solver code (Pyomo, HiGHS) or physical power balance math.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


# Locked 6-tier provenance taxonomy across Polaris-EMS
LOCKED_PROVENANCE_TIERS = {
    "REAL",
    "CONFIGURED",
    "ASSUMED",
    "SYNTHETIC",
    "FORECAST",
    "SIMULATED"
}


def validate_provenance(v: str) -> str:
    v_upper = v.upper()
    if v_upper not in LOCKED_PROVENANCE_TIERS:
        raise ValueError(
            f"Provenance '{v}' violates the locked 6-tier taxonomy: {sorted(list(LOCKED_PROVENANCE_TIERS))}"
        )
    return v_upper


class DeviceType(str, Enum):
    """Supported field device classes."""
    SOLAR = "SOLAR"
    WIND = "WIND"
    DIESEL_GENERATOR = "DIESEL_GENERATOR"
    BATTERY = "BATTERY"
    THERMAL = "THERMAL"
    WEATHER = "WEATHER"
    POWER_METER = "POWER_METER"
    FUEL = "FUEL"
    GPS = "GPS"
    COMMUNICATIONS = "COMMUNICATIONS"


class DataQualityState(str, Enum):
    """Data quality classification for ingested telemetry (NOT a provenance tier)."""
    VALID = "VALID"
    STALE = "STALE"
    MISSING = "MISSING"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    SUSPECT = "SUSPECT"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"


class DeviceHealthState(str, Enum):
    """Deterministic device health assessment states."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    FAULT = "FAULT"
    UNKNOWN = "UNKNOWN"


class ConnectivityState(str, Enum):
    """Edge node to backend connectivity state."""
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    RECONNECTING = "RECONNECTING"
    UNKNOWN = "UNKNOWN"


class EdgeMode(str, Enum):
    """Operational mode of the local edge node."""
    CONNECTED_OPERATION = "CONNECTED_OPERATION"
    DEGRADED_CONNECTIVITY = "DEGRADED_CONNECTIVITY"
    OFFLINE_EDGE = "OFFLINE_EDGE"
    RECOVERY_SYNC = "RECOVERY_SYNC"
    SAFE_HOLD = "SAFE_HOLD"


class FallbackPosture(str, Enum):
    """Safe, bounded operational posture when backend decision pathway is unreachable."""
    HOLD_LAST_VALIDATED_STATE = "HOLD_LAST_VALIDATED_STATE"
    SAFE_HOLD = "SAFE_HOLD"
    PROTECT_CRITICAL_SYSTEMS = "PROTECT_CRITICAL_SYSTEMS"
    SUSPEND_NONCRITICAL_REQUESTS = "SUSPEND_NONCRITICAL_REQUESTS"
    BUFFER_AND_FORWARD = "BUFFER_AND_FORWARD"
    REQUEST_RECONNECTION = "REQUEST_RECONNECTION"
    WAIT_FOR_BACKEND_DECISION = "WAIT_FOR_BACKEND_DECISION"


class DeviceChannelConfig(BaseModel):
    """Configuration for an individual telemetry channel."""
    channel: str
    unit: str
    min_val: float
    max_val: float
    freshness_limit_seconds: float = 60.0


class DeviceProfile(BaseModel):
    """Typed device model representation."""
    device_id: str
    station_id: str
    device_type: DeviceType
    name: str
    rated_capacity: Optional[float] = None
    unit: str
    enabled: bool = True
    expected_reporting_interval_sec: float = 10.0
    freshness_threshold_sec: float = 60.0
    health_state: DeviceHealthState = DeviceHealthState.HEALTHY
    connectivity_state: ConnectivityState = ConnectivityState.CONNECTED
    provenance: str = Field(default="CONFIGURED")
    last_seen: Optional[str] = None
    configured_metadata: Dict[str, Any] = Field(default_factory=dict)
    telemetry_channels: List[DeviceChannelConfig] = Field(default_factory=list)
    source_metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("provenance")
    @classmethod
    def check_prov(cls, v: str) -> str:
        return validate_provenance(v)


class StationDeviceCatalog(BaseModel):
    """Catalog of all configured devices for a specific polar station."""
    station_id: str
    station_name: str
    edge_node_id: str
    default_reporting_interval_sec: float = 10.0
    default_freshness_threshold_sec: float = 60.0
    devices: List[DeviceProfile] = Field(default_factory=list)


class TelemetryReading(BaseModel):
    """Canonical normalized telemetry envelope for edge ingestion."""
    timestamp: str = Field(description="ISO-8601 telemetry observation timestamp")
    station_id: str
    device_id: str
    channel: str
    value: Union[float, int, str, bool]
    unit: str
    quality: DataQualityState = DataQualityState.VALID
    source: str = "edge_sensor"
    received_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sequence_number: Optional[int] = None
    provenance: str = Field(default="SYNTHETIC")
    validation_status: str = "ACCEPTED"
    diagnostics: List[str] = Field(default_factory=list)

    @field_validator("provenance")
    @classmethod
    def check_prov(cls, v: str) -> str:
        return validate_provenance(v)


class QualityValidationResult(BaseModel):
    """Detailed result of deterministic data quality checks."""
    is_valid: bool
    quality: DataQualityState
    reason: Optional[str] = None
    rejection_code: Optional[str] = None
    checked_channel: str
    observed_value: Any
    expected_range: Optional[List[float]] = None
    latency_sec: float = 0.0


class DeviceHealthStatus(BaseModel):
    """Deterministic device health assessment output."""
    device_id: str
    station_id: str
    device_type: DeviceType
    health_state: DeviceHealthState
    health_score: float = Field(ge=0.0, le=1.0, description="Normalized health score [0.0 - 1.0]")
    contributing_signals: List[str] = Field(default_factory=list)
    last_seen: Optional[str] = None
    last_valid_telemetry: Optional[str] = None
    provenance: str = Field(default="CONFIGURED")
    diagnostics: List[str] = Field(default_factory=list)

    @field_validator("provenance")
    @classmethod
    def check_prov(cls, v: str) -> str:
        return validate_provenance(v)


class ConnectivityStatus(BaseModel):
    """Edge-to-backend connectivity state report."""
    station_id: str
    connectivity_state: ConnectivityState
    last_successful_contact: Optional[str] = None
    heartbeat_age_sec: float = 0.0
    packet_loss_pct: float = 0.0
    buffered_count: int = 0
    consecutive_failures: int = 0
    sync_in_progress: bool = False
    diagnostics: List[str] = Field(default_factory=list)
    provenance: str = Field(default="CONFIGURED")

    @field_validator("provenance")
    @classmethod
    def check_prov(cls, v: str) -> str:
        return validate_provenance(v)


class EdgeStateSnapshot(BaseModel):
    """Canonical edge state representation for polar station."""
    station_id: str
    edge_node_id: str
    edge_mode: EdgeMode
    connectivity_state: ConnectivityState
    fallback_posture: FallbackPosture
    active_devices_count: int
    healthy_devices_count: int
    degraded_devices_count: int
    fault_devices_count: int
    buffer_depth: int
    last_sync_time: Optional[str] = None
    sync_freshness_sec: float = 0.0
    latest_readings: Dict[str, TelemetryReading] = Field(default_factory=dict)
    quality_summary: Dict[str, int] = Field(default_factory=dict)
    health_summary: Dict[str, int] = Field(default_factory=dict)
    provenance: str = Field(default="CONFIGURED")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("provenance")
    @classmethod
    def check_prov(cls, v: str) -> str:
        return validate_provenance(v)


class ReconciliationAuditEntry(BaseModel):
    """Audit log entry for state reconciliation actions."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    station_id: str
    device_id: str
    channel: str
    action: str  # ACCEPTED_NEW | BUFFER_LOGGED | DUPLICATE_DROPPED | CONFLICT_RESOLVED | GAP_FLAGGED
    sequence_number: Optional[int] = None
    reason: str


class ReconciliationReport(BaseModel):
    """Outcome of telemetry buffer reconciliation after reconnect."""
    station_id: str
    total_buffered: int
    processed_count: int
    duplicate_count: int
    gap_count: int
    conflict_count: int
    execution_duration_ms: float
    audit_log: List[ReconciliationAuditEntry] = Field(default_factory=list)
    status: str = "COMPLETED"
    provenance: str = Field(default="SIMULATED")

    @field_validator("provenance")
    @classmethod
    def check_prov(cls, v: str) -> str:
        return validate_provenance(v)
