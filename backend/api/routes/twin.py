"""
POLARIS-EMS — Digital Twin Spatial, Real-Time Live Session, & Replay Routes
SIH26061: Polar Energy Management & Resilience System

Exposes:
- Spatial layout schematics
- Instantaneous physical state snapshots
- Multi-horizon forward replay trajectories
- Stateful Live Twin Session snapshots & SSE real-time event streams
- Authoritative manual and automated advisory control dispatch
- Live scenario perturbation injection and closure verification
- Trace Power and Trace Impact topological causal chains
"""

import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, Path, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

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
from backend.twin.live_session import live_twin_manager

router = APIRouter(prefix="/twin", tags=["Digital Twin"])


class ManualControlRequest(BaseModel):
    station_id: str = Field(..., description="Target station (BHARATI, MAITRI, HIMADRI)")
    action_id: str = Field(..., description="Action ID e.g. dg1_start, dg1_stop, bess_charge_force, shed_flexible, restore_all_loads")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Action parameter overrides")


class AutoApproveRequest(BaseModel):
    station_id: str = Field(..., description="Target station")


class ScenarioApplyRequest(BaseModel):
    station_id: str = Field(..., description="Target station")
    scenario_id: str = Field(..., description="Locked scenario ID e.g. BLIZZARD, GEN_FAILURE_BLIZZARD")


class ScenarioClearRequest(BaseModel):
    station_id: str = Field(..., description="Target station")


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


# =========================================================================
# REAL-TIME LIVE TWIN SESSION & EVENT STREAM ENDPOINTS
# =========================================================================

@router.get("/live/{station_id}", response_model=APIResponse[Dict[str, Any]])
async def get_live_twin_session(
    station_id: str = Path(..., description="Target polar research station"),
    request: Request = None
) -> APIResponse[Dict[str, Any]]:
    """
    Retrieves full instantaneous computational snapshot of the stateful LiveTwinSession.
    Simulates real-time physics advancement according to elapsed wall clock.
    """
    req_id = getattr(request.state, "request_id", "req-twin-live") if request else "req-twin-live"
    session = live_twin_manager.get_session(station_id)
    session.advance_clock()
    snapshot = session.get_snapshot()
    return APIResponse.success(data=snapshot, request_id=req_id, provenance="SIMULATED")


@router.get("/live/{station_id}/stream")
async def stream_live_twin_events(
    station_id: str = Path(..., description="Target polar research station")
):
    """
    Server-Sent Events (SSE) stream providing real-time computational twin state updates.
    Advances simulation clock synchronously with wall-clock execution.
    """
    session = live_twin_manager.get_session(station_id)

    async def event_generator():
        try:
            while True:
                session.advance_clock()
                snapshot = session.get_snapshot()
                event_data = json.dumps(snapshot)
                yield f"data: {event_data}\n\n"
                await asyncio.sleep(1.5)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/control/manual", response_model=APIResponse[Dict[str, Any]])
async def dispatch_manual_control(
    payload: ManualControlRequest = Body(...),
    request: Request = None
) -> APIResponse[Dict[str, Any]]:
    """
    Dispatches operator manual control action through authoritative backend validation.
    Recalculates instantaneous twin state and returns physical delta and trace evidence.
    """
    req_id = getattr(request.state, "request_id", "req-twin-manual") if request else "req-twin-manual"
    session = live_twin_manager.get_session(payload.station_id)
    result = session.apply_manual_action(payload.action_id, payload.parameters)
    return APIResponse.success(data=result, request_id=req_id, provenance="SIMULATED")


@router.post("/control/auto-approve", response_model=APIResponse[Dict[str, Any]])
async def approve_auto_recommendation(
    payload: AutoApproveRequest = Body(...),
    request: Request = None
) -> APIResponse[Dict[str, Any]]:
    """
    Applies approved Phase 6 optimizer advisory recommendation to the live digital twin session.
    """
    req_id = getattr(request.state, "request_id", "req-twin-auto") if request else "req-twin-auto"
    session = live_twin_manager.get_session(payload.station_id)
    result = session.approve_auto_recommendation()
    return APIResponse.success(data=result, request_id=req_id, provenance="SIMULATED")


@router.post("/scenario/apply", response_model=APIResponse[Dict[str, Any]])
async def apply_live_scenario(
    payload: ScenarioApplyRequest = Body(...),
    request: Request = None
) -> APIResponse[Dict[str, Any]]:
    """
    Injects a scenario perturbation directly into the stateful live session.
    Recalculates downstream power flow, source mix, loads, battery, diesel, and resilience.
    """
    req_id = getattr(request.state, "request_id", "req-twin-scen-apply") if request else "req-twin-scen-apply"
    session = live_twin_manager.get_session(payload.station_id)
    try:
        result = session.apply_scenario(payload.scenario_id)
    except KeyError:
        from backend.api.errors import ScenarioNotFoundException
        raise ScenarioNotFoundException(payload.scenario_id)
    return APIResponse.success(data=result, request_id=req_id, provenance="SIMULATED")


@router.post("/scenario/clear", response_model=APIResponse[Dict[str, Any]])
async def clear_live_scenario(
    payload: ScenarioClearRequest = Body(...),
    request: Request = None
) -> APIResponse[Dict[str, Any]]:
    """
    Clears active scenario perturbation from live session, restoring baseline driving conditions.
    """
    req_id = getattr(request.state, "request_id", "req-twin-scen-clear") if request else "req-twin-scen-clear"
    session = live_twin_manager.get_session(payload.station_id)
    result = session.clear_scenario()
    return APIResponse.success(data=result, request_id=req_id, provenance="SIMULATED")


@router.get("/trace/power/{station_id}/{target_id}", response_model=APIResponse[Dict[str, Any]])
async def trace_power_flow(
    station_id: str = Path(..., description="Target polar research station"),
    target_id: str = Path(..., description="Load circuit or panel node ID"),
    request: Request = None
) -> APIResponse[Dict[str, Any]]:
    """
    Traces exact topological power path from active generation sources down to the target load.
    """
    req_id = getattr(request.state, "request_id", "req-trace-power") if request else "req-trace-power"
    session = live_twin_manager.get_session(station_id)
    data = session.trace_power_path(target_id)
    return APIResponse.success(data=data, request_id=req_id, provenance="SIMULATED")


@router.get("/trace/impact/{station_id}/{asset_id}", response_model=APIResponse[Dict[str, Any]])
async def trace_asset_impact(
    station_id: str = Path(..., description="Target polar research station"),
    asset_id: str = Path(..., description="Generation source, bus, or feeder ID"),
    request: Request = None
) -> APIResponse[Dict[str, Any]]:
    """
    Traces downstream system impact if the specified asset is degraded, faulted, or lost.
    """
    req_id = getattr(request.state, "request_id", "req-trace-impact") if request else "req-trace-impact"
    session = live_twin_manager.get_session(station_id)
    data = session.trace_impact(asset_id)
    return APIResponse.success(data=data, request_id=req_id, provenance="SIMULATED")
