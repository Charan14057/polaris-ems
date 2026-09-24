"""
POLARIS-EMS — External Reality Bridge API Endpoints
SIH26061: Polar Energy Management & Resilience System

Provides external provider discovery, reality bridge diagnostics, and weather observation queries.
- GET /api/v1/integrations/status
- GET /api/v1/integrations/providers
- GET /api/v1/integrations/weather/{station_id}
- GET /api/v1/integrations/freshness
"""

from fastapi import APIRouter, Request, Query, Path
from typing import Optional, List, Dict, Any

from backend.api.responses import APIResponse
from backend.integrations.bridge import get_reality_bridge, ExternalRealityBridge
from backend.integrations.schemas import (
    ProviderHealthRecord,
    ExternalValidationResult,
)

router = APIRouter(prefix="/integrations", tags=["External Integrations"])


@router.get("/status", response_model=APIResponse[Dict[str, Any]])
async def get_bridge_status(request: Request) -> APIResponse[Dict[str, Any]]:
    """Executive status of the external reality bridge and connected adapters."""
    req_id = getattr(request.state, "request_id", "req-bridge-status")
    bridge = get_reality_bridge()
    summary = bridge.get_bridge_summary()
    return APIResponse.success(data=summary, request_id=req_id, provenance="CONFIGURED")


@router.get("/providers", response_model=APIResponse[List[ProviderHealthRecord]])
async def list_providers(request: Request) -> APIResponse[List[ProviderHealthRecord]]:
    """Lists all registered external reality adapters and their operational health."""
    req_id = getattr(request.state, "request_id", "req-providers")
    bridge = get_reality_bridge()
    records = bridge.get_provider_health()
    return APIResponse.success(data=records, request_id=req_id, provenance="CONFIGURED")


@router.get("/weather/{station_id}", response_model=APIResponse[ExternalValidationResult])
async def get_station_weather(
    request: Request,
    station_id: str = Path(..., description="Target polar research station (BHARATI, MAITRI, HIMADRI)"),
    provider: Optional[str] = Query(None, description="Preferred provider adapter (e.g. openmeteo, ncpor, spooler)")
) -> APIResponse[ExternalValidationResult]:
    """Queries external weather observation for a polar station with quality validation and fallback."""
    req_id = getattr(request.state, "request_id", f"req-weather-{station_id.lower()}")
    bridge = get_reality_bridge()
    result = bridge.get_weather_observation(station_id=station_id, preferred_provider=provider)
    return APIResponse.success(data=result, request_id=req_id, provenance=result.provenance)


@router.get("/freshness", response_model=APIResponse[Dict[str, Any]])
async def get_data_freshness(request: Request) -> APIResponse[Dict[str, Any]]:
    """Reports data freshness across all monitored stations and external bridges."""
    req_id = getattr(request.state, "request_id", "req-freshness")
    bridge = get_reality_bridge()
    providers = bridge.get_provider_health()

    data = {
        "overall_freshness": "ACCEPTABLE" if bridge.enabled else "OFFLINE_CALIBRATED",
        "external_data_enabled": bridge.enabled,
        "providers_freshness": {p.provider_name: p.freshness_status.value for p in providers},
        "physical_scada_connected": False,
        "operational_posture": "CALIBRATED_DIGITAL_TWIN"
    }
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")
