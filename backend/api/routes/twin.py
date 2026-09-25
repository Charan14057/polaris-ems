"""
POLARIS-EMS — Digital Twin Spatial & Replay Routes
SIH26061: Polar Energy Management & Resilience System

Exposes spatial schematics, current physical state, and forward replay trajectories
computed strictly by the authoritative Phase 4 TwinEngine.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, Path, Body

from backend.api.responses import APIResponse
from backend.api.schemas.twin import (
    TwinSpatialProfileSchema,
    TwinTrajectoryRequestSchema,
    TwinTrajectoryResponseData
)
from backend.api.adapters.twin_adapter import TwinAPIAdapter
from backend.api.dependencies import (
    get_profile_registry,
    get_safety_registry,
    get_scenario_registry
)

router = APIRouter(prefix="/twin", tags=["Digital Twin"])


def get_twin_adapter(
    profile_reg=Depends(get_profile_registry),
    safety_reg=Depends(get_safety_registry),
    scen_reg=Depends(get_scenario_registry)
) -> TwinAPIAdapter:
    return TwinAPIAdapter(
        profile_registry=profile_reg,
        safety_registry=safety_reg,
        scenario_registry=scen_reg
    )


@router.get("/spatial/{station_id}", response_model=APIResponse[TwinSpatialProfileSchema])
async def get_station_spatial_profile(
    station_id: str = Path(..., description="Target polar research station (BHARATI, MAITRI, HIMADRI)"),
    request: Request = None,
    adapter: TwinAPIAdapter = Depends(get_twin_adapter)
) -> APIResponse[TwinSpatialProfileSchema]:
    """Retrieves validated representative spatial layout schematic for a polar station."""
    req_id = getattr(request.state, "request_id", "req-twin-spatial") if request else "req-twin-spatial"
    data = adapter.get_spatial_profile(station_id)
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.get("/state/{station_id}", response_model=APIResponse[Dict[str, Any]])
async def get_station_current_state(
    station_id: str = Path(..., description="Target polar research station"),
    timestamp: Optional[str] = None,
    request: Request = None,
    adapter: TwinAPIAdapter = Depends(get_twin_adapter)
) -> APIResponse[Dict[str, Any]]:
    """Retrieves instantaneous strongly typed physical state from Phase 4 Digital Twin."""
    req_id = getattr(request.state, "request_id", "req-twin-state") if request else "req-twin-state"
    state = adapter.get_current_state(station_id, timestamp=timestamp)
    return APIResponse.success(data=state, request_id=req_id, provenance="SIMULATED")


@router.post("/trajectory", response_model=APIResponse[TwinTrajectoryResponseData])
async def simulate_twin_trajectory(
    payload: TwinTrajectoryRequestSchema = Body(...),
    request: Request = None,
    adapter: TwinAPIAdapter = Depends(get_twin_adapter)
) -> APIResponse[TwinTrajectoryResponseData]:
    """
    Executes a multi-timestep forward simulation trajectory using the authoritative TwinEngine.
    Supports 24h, 48h, and 168h horizons with optional stress scenario perturbations.
    """
    req_id = getattr(request.state, "request_id", "req-twin-trajectory") if request else "req-twin-trajectory"
    trajectory_data = adapter.simulate_trajectory(payload)
    return APIResponse.success(data=trajectory_data, request_id=req_id, provenance="SIMULATED")
