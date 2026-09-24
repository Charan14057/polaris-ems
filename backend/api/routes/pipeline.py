"""
POLARIS-EMS — End-to-End Pipeline Routes
SIH26061: Polar Energy Management & Resilience System

Provides unified pipeline orchestration endpoint:
- POST /api/v1/pipeline/analyze
Executes: Forecast -> Scenario -> Optimize -> Twin Replay -> Resilience -> Policy.
"""

from fastapi import APIRouter, Depends, Request

from backend.api.responses import APIResponse
from backend.api.schemas.pipeline import PipelineAnalyzeRequestSchema, PipelineAnalyzeResponseData
from backend.api.dependencies import (
    get_profile_registry,
    get_safety_registry,
    get_scenario_registry,
    get_inference_engine
)
from backend.api.adapters.pipeline_orchestrator import PipelineOrchestrator
from backend.data.station_profiles.loader import StationProfileRegistry
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.scenarios.registry import ScenarioRegistry
from backend.ml.inference import InferenceEngine
from backend.api.errors import StationNotFoundException

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.post("/analyze", response_model=APIResponse[PipelineAnalyzeResponseData])
async def analyze_pipeline(
    req: PipelineAnalyzeRequestSchema,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    safety_reg: SafetyThresholdRegistry = Depends(get_safety_registry),
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry),
    inference_engine: InferenceEngine = Depends(get_inference_engine)
) -> APIResponse[PipelineAnalyzeResponseData]:
    """
    Executes the complete unified Polaris-EMS intelligence pipeline:
    Forecast (Phase 3) -> Scenario (Phase 5) -> Optimizer (Phase 6) ->
    Twin Replay (Phase 4) -> Resilience (Phase 7) -> Policy (Phase 8).
    """
    req_id = getattr(request.state, "request_id", None)
    sid = req.station_id.upper()
    try:
        profile_reg.get(sid)
    except KeyError:
        raise StationNotFoundException(sid)

    orchestrator = PipelineOrchestrator(
        profile_registry=profile_reg,
        safety_registry=safety_reg,
        scenario_registry=scenario_reg,
        inference_engine=inference_engine
    )

    data = orchestrator.run_pipeline(req)

    return APIResponse.success(
        data=data,
        request_id=req_id,
        provenance="SIMULATED",
        status=data.overall_status
    )
