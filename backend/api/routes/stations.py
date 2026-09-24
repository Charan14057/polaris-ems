"""
POLARIS-EMS — Station Profile Routes
SIH26061: Polar Energy Management & Resilience System

Provides discovery and configuration inspection for verified polar stations:
- GET /api/v1/stations
- GET /api/v1/stations/{station_id}
"""

from typing import List
from fastapi import APIRouter, Depends, Request

from backend.api.responses import APIResponse
from backend.api.schemas.station import StationSummarySchema, StationDetailResponse
from backend.api.dependencies import get_profile_registry
from backend.api.adapters.station_adapter import StationAdapter
from backend.data.station_profiles.loader import StationProfileRegistry
from backend.api.errors import StationNotFoundException

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=APIResponse[List[StationSummarySchema]])
async def list_stations(
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry)
) -> APIResponse[List[StationSummarySchema]]:
    """Lists summary metadata for all registered polar stations."""
    req_id = getattr(request.state, "request_id", None)
    station_ids = profile_reg.list_stations()
    summaries = [
        StationAdapter.to_summary(profile_reg.get(sid))
        for sid in station_ids
    ]
    return APIResponse.success(data=summaries, request_id=req_id, provenance="CONFIGURED")


@router.get("/{station_id}", response_model=APIResponse[StationDetailResponse])
async def get_station(
    station_id: str,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry)
) -> APIResponse[StationDetailResponse]:
    """Retrieves full validated profile configuration for a specific polar station."""
    req_id = getattr(request.state, "request_id", None)
    try:
        profile = profile_reg.get(station_id.upper())
    except KeyError:
        raise StationNotFoundException(station_id)

    detail = StationAdapter.to_detail(profile)
    return APIResponse.success(data=detail, request_id=req_id, provenance="CONFIGURED")
