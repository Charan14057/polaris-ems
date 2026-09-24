"""
POLARIS-EMS — Energy Optimizer Routes
SIH26061: Polar Energy Management & Resilience System

Provides microgrid dispatch optimization endpoints powered by Phase 6:
- POST /api/v1/optimize
"""

from fastapi import APIRouter, Depends, Request

from backend.api.responses import APIResponse
from backend.api.schemas.optimizer import OptimizeRequestSchema, OptimizeResponseData
from backend.api.dependencies import (
    get_profile_registry,
    get_scenario_registry,
    get_optimizer_engine,
    get_twin_engine
)
from backend.api.adapters.optimizer_adapter import OptimizerAPIAdapter
from backend.data.station_profiles.loader import StationProfileRegistry
from backend.scenarios.registry import ScenarioRegistry
from backend.api.errors import StationNotFoundException

router = APIRouter(prefix="/optimize", tags=["Optimizer"])


@router.post("", response_model=APIResponse[OptimizeResponseData])
async def optimize_microgrid(
    req: OptimizeRequestSchema,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry)
) -> APIResponse[OptimizeResponseData]:
    """
    Solves multi-horizon microgrid dispatch with HiGHS MILP and validates via Digital Twin replay.
    Preserves explicit optimality semantics (EXACT_OPTIMAL, MIP_GAP_OPTIMAL, FALLBACK).
    """
    req_id = getattr(request.state, "request_id", None)
    sid = req.station_id.upper()
    try:
        profile_reg.get(sid)
    except KeyError:
        raise StationNotFoundException(sid)

    adapter = OptimizerAPIAdapter(scenario_registry=scenario_reg)
    opt_engine = get_optimizer_engine(sid)
    twin_engine = get_twin_engine(sid)

    data = adapter.execute_optimization(req=req, optimizer=opt_engine, twin=twin_engine)

    # Domain semantics: HTTP 200 with status=PARTIAL if solver used fallback or was suboptimal
    domain_status = "PARTIAL" if data.optimality_tier in ("FALLBACK", "INFEASIBLE") or not data.is_valid else "SUCCESS"

    return APIResponse.success(
        data=data,
        request_id=req_id,
        provenance="SIMULATED",
        status=domain_status,
        diagnostics=data.diagnostics
    )
