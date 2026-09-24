"""
POLARIS-EMS — Edge Field Resilience & Device Intelligence Routes
SIH26061: Polar Energy Management & Resilience System

Provides RESTful endpoints for edge telemetry ingestion, quality monitoring,
fleet health inspection, connectivity tracking, and reconnection reconciliation:
- GET  /api/v1/edge/{station_id}/state
- GET  /api/v1/edge/{station_id}/devices
- GET  /api/v1/edge/{station_id}/telemetry
- GET  /api/v1/edge/{station_id}/health
- GET  /api/v1/edge/{station_id}/connectivity
- POST /api/v1/edge/{station_id}/telemetry/ingest
- POST /api/v1/edge/{station_id}/sync
- POST /api/v1/edge/{station_id}/evaluate
- POST /api/v1/edge/{station_id}/simulate-condition
"""

from typing import List
from fastapi import APIRouter, Depends, Request

from backend.api.responses import APIResponse
from backend.api.errors import StationNotFoundException
from backend.data.station_profiles.loader import StationProfileRegistry
from backend.api.dependencies import get_profile_registry
from backend.edge.devices import DeviceRegistry, get_device_registry
from backend.edge.engine import get_edge_engine, EdgeEngine
from backend.api.adapters.edge_adapter import EdgeAPIAdapter
from backend.edge.schema import TelemetryReading
from backend.api.schemas.edge import (
    EdgeStateResponseData,
    DeviceSummarySchema,
    TelemetryItemResponseSchema,
    DeviceHealthItemSchema,
    ConnectivityResponseData,
    TelemetryIngestRequestSchema,
    TelemetryIngestResponseData,
    SyncResponseData,
    EdgeEvaluateResponseData,
    SimulateConditionRequestSchema
)

router = APIRouter(prefix="/edge", tags=["Edge & Device Intelligence"])


def _get_engine_or_404(
    station_id: str,
    profile_reg: StationProfileRegistry,
    device_reg: DeviceRegistry
) -> EdgeEngine:
    sid = station_id.upper()
    try:
        profile_reg.get(sid)
    except KeyError:
        raise StationNotFoundException(sid)

    if sid not in device_reg.list_stations():
        raise StationNotFoundException(sid)

    return get_edge_engine(sid, device_registry=device_reg)


@router.get("/{station_id}/state", response_model=APIResponse[EdgeStateResponseData])
async def get_edge_state(
    station_id: str,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    device_reg: DeviceRegistry = Depends(get_device_registry)
) -> APIResponse[EdgeStateResponseData]:
    """Retrieves current operational state snapshot of the station edge node."""
    req_id = getattr(request.state, "request_id", None)
    engine = _get_engine_or_404(station_id, profile_reg, device_reg)

    snapshot = engine.get_state()
    data = EdgeAPIAdapter.to_edge_state_response(snapshot)

    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.get("/{station_id}/devices", response_model=APIResponse[List[DeviceSummarySchema]])
async def list_devices(
    station_id: str,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    device_reg: DeviceRegistry = Depends(get_device_registry)
) -> APIResponse[List[DeviceSummarySchema]]:
    """Lists all physical and virtual field devices configured for the station."""
    req_id = getattr(request.state, "request_id", None)
    _get_engine_or_404(station_id, profile_reg, device_reg)

    devices = device_reg.list_devices(station_id)
    summaries = [EdgeAPIAdapter.to_device_summary(d) for d in devices]

    return APIResponse.success(data=summaries, request_id=req_id, provenance="CONFIGURED")


@router.get("/{station_id}/telemetry", response_model=APIResponse[List[TelemetryItemResponseSchema]])
async def get_latest_telemetry(
    station_id: str,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    device_reg: DeviceRegistry = Depends(get_device_registry)
) -> APIResponse[List[TelemetryItemResponseSchema]]:
    """Retrieves latest validated telemetry readings across all station devices."""
    req_id = getattr(request.state, "request_id", None)
    engine = _get_engine_or_404(station_id, profile_reg, device_reg)

    snapshot = engine.get_state()
    readings = list(snapshot.latest_readings.values())
    items = [EdgeAPIAdapter.to_telemetry_schema(r) for r in readings]

    return APIResponse.success(data=items, request_id=req_id, provenance="SYNTHETIC")


@router.get("/{station_id}/health", response_model=APIResponse[List[DeviceHealthItemSchema]])
async def get_fleet_health(
    station_id: str,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    device_reg: DeviceRegistry = Depends(get_device_registry)
) -> APIResponse[List[DeviceHealthItemSchema]]:
    """Retrieves deterministic health assessments for all station devices."""
    req_id = getattr(request.state, "request_id", None)
    engine = _get_engine_or_404(station_id, profile_reg, device_reg)

    fleet = engine.get_fleet_health()
    items = [EdgeAPIAdapter.to_device_health(dh) for dh in fleet]

    return APIResponse.success(data=items, request_id=req_id, provenance="CONFIGURED")


@router.get("/{station_id}/connectivity", response_model=APIResponse[ConnectivityResponseData])
async def get_connectivity(
    station_id: str,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    device_reg: DeviceRegistry = Depends(get_device_registry)
) -> APIResponse[ConnectivityResponseData]:
    """Retrieves edge-to-backend connectivity status and buffer depth."""
    req_id = getattr(request.state, "request_id", None)
    engine = _get_engine_or_404(station_id, profile_reg, device_reg)

    status = engine.get_connectivity()
    data = EdgeAPIAdapter.to_connectivity_response(status)

    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.post("/{station_id}/telemetry/ingest", response_model=APIResponse[TelemetryIngestResponseData])
async def ingest_telemetry(
    station_id: str,
    req: TelemetryIngestRequestSchema,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    device_reg: DeviceRegistry = Depends(get_device_registry)
) -> APIResponse[TelemetryIngestResponseData]:
    """Ingests, normalizes, and validates a batch of field telemetry readings."""
    req_id = getattr(request.state, "request_id", None)
    engine = _get_engine_or_404(station_id, profile_reg, device_reg)

    accepted = 0
    rejected = 0
    quarantined = 0
    processed_schemas = []

    for item in req.readings:
        payload = {
            "station_id": station_id.upper(),
            "device_id": item.device_id,
            "channel": item.channel,
            "value": item.value,
            "unit": item.unit,
            "timestamp": item.timestamp,
            "source": item.source,
            "sequence_number": item.sequence_number,
            "provenance": item.provenance
        }
        reading, val_res = engine.ingest_telemetry(payload)
        if reading.validation_status == "ACCEPTED":
            accepted += 1
        elif reading.validation_status == "QUARANTINED":
            quarantined += 1
        else:
            rejected += 1

        processed_schemas.append(EdgeAPIAdapter.to_telemetry_schema(reading))

    response_data = TelemetryIngestResponseData(
        station_id=station_id.upper(),
        accepted_count=accepted,
        rejected_count=rejected,
        quarantined_count=quarantined,
        buffered_count=engine.buffer.size(),
        readings=processed_schemas
    )

    domain_status = "SUCCESS" if rejected == 0 else "PARTIAL"
    return APIResponse.success(
        data=response_data,
        request_id=req_id,
        provenance="SYNTHETIC",
        status=domain_status
    )


@router.post("/{station_id}/sync", response_model=APIResponse[SyncResponseData])
async def sync_edge_buffer(
    station_id: str,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    device_reg: DeviceRegistry = Depends(get_device_registry)
) -> APIResponse[SyncResponseData]:
    """Triggers state reconciliation between local edge buffer and central backend."""
    req_id = getattr(request.state, "request_id", None)
    engine = _get_engine_or_404(station_id, profile_reg, device_reg)

    report = engine.sync_telemetry()
    data = EdgeAPIAdapter.to_sync_response(report)

    return APIResponse.success(data=data, request_id=req_id, provenance="SIMULATED")


@router.post("/{station_id}/evaluate", response_model=APIResponse[EdgeEvaluateResponseData])
async def evaluate_edge_decision(
    station_id: str,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    device_reg: DeviceRegistry = Depends(get_device_registry)
) -> APIResponse[EdgeEvaluateResponseData]:
    """Evaluates operational posture and decision pathway for edge node."""
    req_id = getattr(request.state, "request_id", None)
    engine = _get_engine_or_404(station_id, profile_reg, device_reg)

    res = engine.evaluate_decision()
    data = EdgeEvaluateResponseData(
        station_id=res["station_id"],
        pathway=res["pathway"],
        edge_mode=res["edge_mode"],
        fallback_posture=res["fallback_posture"],
        action_taken=res["action_taken"],
        dispatch_authorized=res["dispatch_authorized"],
        buffered_telemetry_count=res["buffered_telemetry_count"],
        provenance=res["provenance"],
        diagnostics=res["diagnostics"]
    )

    return APIResponse.success(data=data, request_id=req_id, provenance=res["provenance"])


@router.post("/{station_id}/simulate-condition", response_model=APIResponse[EdgeStateResponseData])
async def simulate_condition(
    station_id: str,
    req: SimulateConditionRequestSchema,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    device_reg: DeviceRegistry = Depends(get_device_registry)
) -> APIResponse[EdgeStateResponseData]:
    """Sets a simulated field/connectivity condition for testing."""
    req_id = getattr(request.state, "request_id", None)
    engine = _get_engine_or_404(station_id, profile_reg, device_reg)

    engine.set_simulation_condition(req.condition.upper())
    snapshot = engine.get_state()
    data = EdgeAPIAdapter.to_edge_state_response(snapshot)

    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")
