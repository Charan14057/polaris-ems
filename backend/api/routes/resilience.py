"""
POLARIS-EMS — Resilience Assessment Routes
SIH26061: Polar Energy Management & Resilience System

Provides resilience assessment endpoints powered by Phase 7:
- POST /api/v1/resilience/evaluate
"""

from fastapi import APIRouter, Depends, Request

from backend.api.responses import APIResponse
from backend.api.schemas.resilience import ResilienceEvaluateRequestSchema, ResilienceEvaluateResponseData
from backend.api.dependencies import (
    get_profile_registry,
    get_scenario_registry,
    get_resilience_engine,
    get_twin_engine
)
from backend.api.adapters.resilience_adapter import ResilienceAPIAdapter
from backend.data.station_profiles.loader import StationProfileRegistry
from backend.scenarios.registry import ScenarioRegistry
from backend.api.errors import StationNotFoundException

router = APIRouter(prefix="/resilience", tags=["Resilience"])


@router.post("/evaluate", response_model=APIResponse[ResilienceEvaluateResponseData])
async def evaluate_resilience(
    req: ResilienceEvaluateRequestSchema,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry)
) -> APIResponse[ResilienceEvaluateResponseData]:
    """
    Evaluates multi-horizon survivability, 9 resilience dimensions, composite engineering index,
    active threats, and candidate recovery options through Phase 7 ResilienceEngine.
    """
    req_id = getattr(request.state, "request_id", None)
    sid = req.station_id.upper()
    try:
        profile_reg.get(sid)
    except KeyError:
        raise StationNotFoundException(sid)

    adapter = ResilienceAPIAdapter(scenario_registry=scenario_reg)
    res_engine = get_resilience_engine(sid)
    twin_engine = get_twin_engine(sid)

    data = adapter.evaluate_resilience(req=req, resilience_engine=res_engine, twin=twin_engine)

    # Domain semantics: HTTP 200 with status=PARTIAL if station is in CRITICAL/THREATENED state
    domain_status = "PARTIAL" if data.resilience_state in ("CRITICAL", "THREATENED") else "SUCCESS"

    return APIResponse.success(
        data=data,
        request_id=req_id,
        provenance="SIMULATED",
        status=domain_status
    )
