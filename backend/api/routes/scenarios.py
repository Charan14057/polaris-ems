"""
POLARIS-EMS — Scenario Stress Testing Routes
SIH26061: Polar Energy Management & Resilience System

Provides scenario catalog exploration and stress simulation endpoints powered by Phase 5:
- GET /api/v1/scenarios
- GET /api/v1/scenarios/{scenario_id}
- POST /api/v1/scenarios/evaluate
"""

from typing import List
from fastapi import APIRouter, Depends, Request

from backend.api.responses import APIResponse
from backend.api.schemas.scenario import (
    ScenarioSummarySchema,
    ScenarioDetailSchema,
    ScenarioEvaluateRequestSchema,
    ScenarioEvaluateResponseData
)
from backend.api.dependencies import (
    get_scenario_registry,
    get_profile_registry,
    get_scenario_engine,
    get_twin_engine
)
from backend.api.adapters.scenario_adapter import ScenarioAPIAdapter
from backend.scenarios.registry import ScenarioRegistry
from backend.data.station_profiles.loader import StationProfileRegistry
from backend.api.errors import StationNotFoundException

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("", response_model=APIResponse[List[ScenarioSummarySchema]])
async def list_scenarios(
    request: Request,
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry)
) -> APIResponse[List[ScenarioSummarySchema]]:
    """Lists all 14 locked polar stress scenarios with categories and active effects."""
    req_id = getattr(request.state, "request_id", None)
    adapter = ScenarioAPIAdapter(scenario_registry=scenario_reg)
    data = adapter.list_scenarios()
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.get("/{scenario_id}", response_model=APIResponse[ScenarioDetailSchema])
async def get_scenario(
    scenario_id: str,
    request: Request,
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry)
) -> APIResponse[ScenarioDetailSchema]:
    """Retrieves complete scenario definition including parameter transforms and rationales."""
    req_id = getattr(request.state, "request_id", None)
    adapter = ScenarioAPIAdapter(scenario_registry=scenario_reg)
    data = adapter.get_scenario(scenario_id)
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.post("/evaluate", response_model=APIResponse[ScenarioEvaluateResponseData])
async def evaluate_scenario(
    req: ScenarioEvaluateRequestSchema,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry)
) -> APIResponse[ScenarioEvaluateResponseData]:
    """
    Executes a scenario stress test through Digital Twin forward simulation and extracts impact deltas.
    """
    req_id = getattr(request.state, "request_id", None)
    sid = req.station_id.upper()
    try:
        profile_reg.get(sid)
    except KeyError:
        raise StationNotFoundException(sid)

    adapter = ScenarioAPIAdapter(scenario_registry=scenario_reg)
    scen_engine = get_scenario_engine(sid)
    twin_engine = get_twin_engine(sid)

    data = adapter.evaluate_scenario(req=req, engine=scen_engine, twin=twin_engine)
    return APIResponse.success(data=data, request_id=req_id, provenance="SIMULATED")
