"""
POLARIS-EMS — Policy Engine & Decision Trace Routes
SIH26061: Polar Energy Management & Resilience System

Provides decision governance and decision trace endpoints powered by Phase 8:
- POST /api/v1/policy/evaluate
- POST /api/v1/decision-trace (Option A: Trace Transformation)
"""

from fastapi import APIRouter, Depends, Request

from backend.api.responses import APIResponse
from backend.api.schemas.policy import PolicyEvaluateRequestSchema, PolicyEvaluateResponseData
from backend.api.dependencies import (
    get_profile_registry,
    get_scenario_registry,
    get_policy_engine,
    get_resilience_engine,
    get_twin_engine
)
from backend.api.adapters.policy_adapter import PolicyAPIAdapter
from backend.data.station_profiles.loader import StationProfileRegistry
from backend.scenarios.registry import ScenarioRegistry
from backend.api.errors import StationNotFoundException

router = APIRouter(tags=["Policy"])


@router.post("/policy/evaluate", response_model=APIResponse[PolicyEvaluateResponseData])
async def evaluate_policy(
    req: PolicyEvaluateRequestSchema,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry)
) -> APIResponse[PolicyEvaluateResponseData]:
    """
    Evaluates explicit, deterministic policy rules across all 8 families.
    Returns primary/active/suppressed directives, 4-tier optimizer handoff requirements,
    and stateful hysteresis tracking.
    """
    req_id = getattr(request.state, "request_id", None)
    sid = req.station_id.upper()
    try:
        profile_reg.get(sid)
    except KeyError:
        raise StationNotFoundException(sid)

    adapter = PolicyAPIAdapter(scenario_registry=scenario_reg)
    pol_engine = get_policy_engine(sid)
    res_engine = get_resilience_engine(sid)
    twin_engine = get_twin_engine(sid)

    data = adapter.evaluate_policy(
        req=req,
        policy_engine=pol_engine,
        resilience_engine=res_engine,
        twin=twin_engine
    )

    # Domain semantics: HTTP 200 with status=PARTIAL if policy is BLOCKED or REQUIRES_OPTIMIZATION
    domain_status = "PARTIAL" if data.policy_state == "BLOCKED" or data.validation_status in ("BLOCKED", "REQUIRES_OPTIMIZATION") else "SUCCESS"

    return APIResponse.success(
        data=data,
        request_id=req_id,
        provenance="SIMULATED",
        status=domain_status,
        diagnostics=data.diagnostics
    )


@router.post("/decision-trace", response_model=APIResponse[PolicyEvaluateResponseData])
async def generate_decision_trace(
    req: PolicyEvaluateRequestSchema,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry)
) -> APIResponse[PolicyEvaluateResponseData]:
    """
    Option A: Trace Transformation endpoint.
    Accepts operational context and returns the complete, auditable PolicyDecisionTrace
    with full condition lineage, threshold checks, and conflict resolution logs.
    """
    # Enforce trace inclusion for decision trace endpoint
    req.include_evaluation_trace = True
    req.include_suppressed = True
    return await evaluate_policy(req=req, request=request, profile_reg=profile_reg, scenario_reg=scenario_reg)
