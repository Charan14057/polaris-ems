"""
POLARIS-EMS — API Adapter for Edge & Device Intelligence
SIH26061: Polar Energy Management & Resilience System
"""

from typing import List, Dict, Any

from backend.edge.schema import (
    TelemetryReading,
    DeviceProfile,
    DeviceHealthStatus,
    ConnectivityStatus,
    EdgeStateSnapshot,
    ReconciliationReport
)
from backend.api.schemas.edge import (
    TelemetryItemResponseSchema,
    DeviceSummarySchema,
    DeviceChannelSchema,
    DeviceHealthItemSchema,
    ConnectivityResponseData,
    EdgeStateResponseData,
    SyncResponseData,
    ReconciliationAuditSchema
)


class EdgeAPIAdapter:
    """Transforms backend edge domain dataclasses and models into API response schemas."""

    @staticmethod
    def to_telemetry_schema(reading: TelemetryReading) -> TelemetryItemResponseSchema:
        return TelemetryItemResponseSchema(
            timestamp=reading.timestamp,
            station_id=reading.station_id,
            device_id=reading.device_id,
            channel=reading.channel,
            value=reading.value,
            unit=reading.unit,
            quality=reading.quality.value,
            source=reading.source,
            received_at=reading.received_at,
            sequence_number=reading.sequence_number,
            provenance=reading.provenance,
            validation_status=reading.validation_status,
            diagnostics=list(reading.diagnostics)
        )

    @classmethod
    def to_device_summary(cls, dev: DeviceProfile) -> DeviceSummarySchema:
        channels = [
            DeviceChannelSchema(
                channel=ch.channel,
                unit=ch.unit,
                min_val=ch.min_val,
                max_val=ch.max_val,
                freshness_limit_seconds=ch.freshness_limit_seconds
            )
            for ch in dev.telemetry_channels
        ]
        return DeviceSummarySchema(
            device_id=dev.device_id,
            station_id=dev.station_id,
            device_type=dev.device_type.value,
            name=dev.name,
            rated_capacity=dev.rated_capacity,
            unit=dev.unit,
            enabled=dev.enabled,
            health_state=dev.health_state.value,
            connectivity_state=dev.connectivity_state.value,
            provenance=dev.provenance,
            last_seen=dev.last_seen,
            telemetry_channels=channels,
            source_metadata=dict(dev.source_metadata)
        )

    @staticmethod
    def to_device_health(dh: DeviceHealthStatus) -> DeviceHealthItemSchema:
        return DeviceHealthItemSchema(
            device_id=dh.device_id,
            station_id=dh.station_id,
            device_type=dh.device_type.value,
            health_state=dh.health_state.value,
            health_score=dh.health_score,
            contributing_signals=list(dh.contributing_signals),
            last_seen=dh.last_seen,
            last_valid_telemetry=dh.last_valid_telemetry,
            provenance=dh.provenance,
            diagnostics=list(dh.diagnostics)
        )

    @staticmethod
    def to_connectivity_response(cs: ConnectivityStatus) -> ConnectivityResponseData:
        return ConnectivityResponseData(
            station_id=cs.station_id,
            connectivity_state=cs.connectivity_state.value,
            last_successful_contact=cs.last_successful_contact,
            heartbeat_age_sec=cs.heartbeat_age_sec,
            packet_loss_pct=cs.packet_loss_pct,
            buffered_count=cs.buffered_count,
            consecutive_failures=cs.consecutive_failures,
            sync_in_progress=cs.sync_in_progress,
            diagnostics=list(cs.diagnostics),
            provenance=cs.provenance
        )

    @classmethod
    def to_edge_state_response(cls, snapshot: EdgeStateSnapshot) -> EdgeStateResponseData:
        readings_map = {
            k: cls.to_telemetry_schema(v)
            for k, v in snapshot.latest_readings.items()
        }
        return EdgeStateResponseData(
            station_id=snapshot.station_id,
            edge_node_id=snapshot.edge_node_id,
            edge_mode=snapshot.edge_mode.value,
            connectivity_state=snapshot.connectivity_state.value,
            fallback_posture=snapshot.fallback_posture.value,
            active_devices_count=snapshot.active_devices_count,
            healthy_devices_count=snapshot.healthy_devices_count,
            degraded_devices_count=snapshot.degraded_devices_count,
            fault_devices_count=snapshot.fault_devices_count,
            buffer_depth=snapshot.buffer_depth,
            last_sync_time=snapshot.last_sync_time,
            sync_freshness_sec=snapshot.sync_freshness_sec,
            latest_readings=readings_map,
            quality_summary=dict(snapshot.quality_summary),
            health_summary=dict(snapshot.health_summary),
            provenance=snapshot.provenance,
            timestamp=snapshot.timestamp
        )

    @staticmethod
    def to_sync_response(report: ReconciliationReport) -> SyncResponseData:
        audit_items = [
            ReconciliationAuditSchema(
                timestamp=e.timestamp,
                station_id=e.station_id,
                device_id=e.device_id,
                channel=e.channel,
                action=e.action,
                sequence_number=e.sequence_number,
                reason=e.reason
            )
            for e in report.audit_log
        ]
        return SyncResponseData(
            station_id=report.station_id,
            total_buffered=report.total_buffered,
            processed_count=report.processed_count,
            duplicate_count=report.duplicate_count,
            gap_count=report.gap_count,
            conflict_count=report.conflict_count,
            execution_duration_ms=report.execution_duration_ms,
            audit_log=audit_items,
            status=report.status,
            provenance=report.provenance
        )
