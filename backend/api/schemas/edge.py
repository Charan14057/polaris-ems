"""
POLARIS-EMS — API Schemas for Edge & Device Intelligence
SIH26061: Polar Energy Management & Resilience System
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class TelemetryIngestItemSchema(BaseModel):
    """Payload for single telemetry reading ingestion."""
    device_id: str = Field(..., description="Target device identifier")
    channel: str = Field(..., description="Telemetry channel identifier")
    value: Union[float, int, str, bool] = Field(..., description="Raw observed sensor value")
    unit: str = Field(..., description="Measurement engineering unit")
    timestamp: Optional[str] = Field(None, description="ISO-8601 observation timestamp")
    source: str = Field("api_ingest", description="Data source protocol or adapter")
    sequence_number: Optional[int] = Field(None, description="Monotonically increasing sequence ID")
    provenance: str = Field("SYNTHETIC", description="Locked 6-tier provenance value")


class TelemetryIngestRequestSchema(BaseModel):
    """Batch or single ingestion request."""
    readings: List[TelemetryIngestItemSchema] = Field(..., description="List of readings to ingest")


class TelemetryItemResponseSchema(BaseModel):
    """Response envelope for a validated telemetry observation."""
    timestamp: str
    station_id: str
    device_id: str
    channel: str
    value: Union[float, int, str, bool]
    unit: str
    quality: str
    source: str
    received_at: str
    sequence_number: Optional[int] = None
    provenance: str
    validation_status: str
    diagnostics: List[str] = Field(default_factory=list)


class TelemetryIngestResponseData(BaseModel):
    """Response for telemetry ingestion."""
    station_id: str
    accepted_count: int
    rejected_count: int
    quarantined_count: int
    buffered_count: int
    readings: List[TelemetryItemResponseSchema]


class DeviceChannelSchema(BaseModel):
    channel: str
    unit: str
    min_val: float
    max_val: float
    freshness_limit_seconds: float


class DeviceSummarySchema(BaseModel):
    device_id: str
    station_id: str
    device_type: str
    name: str
    rated_capacity: Optional[float] = None
    unit: str
    enabled: bool
    health_state: str
    connectivity_state: str
    provenance: str
    last_seen: Optional[str] = None
    telemetry_channels: List[DeviceChannelSchema] = Field(default_factory=list)
    source_metadata: Dict[str, Any] = Field(default_factory=dict)


class DeviceHealthItemSchema(BaseModel):
    device_id: str
    station_id: str
    device_type: str
    health_state: str
    health_score: float
    contributing_signals: List[str]
    last_seen: Optional[str] = None
    last_valid_telemetry: Optional[str] = None
    provenance: str
    diagnostics: List[str]


class ConnectivityResponseData(BaseModel):
    station_id: str
    connectivity_state: str
    last_successful_contact: Optional[str] = None
    heartbeat_age_sec: float
    packet_loss_pct: float
    buffered_count: int
    consecutive_failures: int
    sync_in_progress: bool
    diagnostics: List[str]
    provenance: str


class EdgeStateResponseData(BaseModel):
    station_id: str
    edge_node_id: str
    edge_mode: str
    connectivity_state: str
    fallback_posture: str
    active_devices_count: int
    healthy_devices_count: int
    degraded_devices_count: int
    fault_devices_count: int
    buffer_depth: int
    last_sync_time: Optional[str] = None
    sync_freshness_sec: float
    latest_readings: Dict[str, TelemetryItemResponseSchema]
    quality_summary: Dict[str, int]
    health_summary: Dict[str, int]
    provenance: str
    timestamp: str


class ReconciliationAuditSchema(BaseModel):
    timestamp: str
    station_id: str
    device_id: str
    channel: str
    action: str
    sequence_number: Optional[int] = None
    reason: str


class SyncResponseData(BaseModel):
    station_id: str
    total_buffered: int
    processed_count: int
    duplicate_count: int
    gap_count: int
    conflict_count: int
    execution_duration_ms: float
    audit_log: List[ReconciliationAuditSchema]
    status: str
    provenance: str


class EdgeEvaluateResponseData(BaseModel):
    station_id: str
    pathway: str
    edge_mode: str
    fallback_posture: str
    action_taken: str
    dispatch_authorized: bool
    buffered_telemetry_count: int
    provenance: str
    diagnostics: List[str]


class SimulateConditionRequestSchema(BaseModel):
    condition: str = Field(..., description="Condition: NORMAL | OFFLINE | DEGRADED | SAFE_HOLD | CONNECTED")
