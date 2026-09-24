"""
POLARIS-EMS — Decision Trace & Explainability Routes
SIH26061: Polar Energy Management & Resilience System

Provides RESTful endpoints for trace inspection, causal event auditing,
deterministic "Why?" explanations, two-trace comparative deltas, and export.
- GET /api/v1/traces
- GET /api/v1/traces/{trace_id}
- GET /api/v1/traces/{trace_id}/events
- GET /api/v1/traces/{trace_id}/summary
- GET /api/v1/traces/{trace_id}/explanation
- GET /api/v1/traces/{trace_id}/compare/{other_trace_id}
- GET /api/v1/traces/{trace_id}/export
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Response, Query
from starlette.exceptions import HTTPException

from backend.api.responses import APIResponse
from backend.trace.engine import TraceService, get_trace_service
from backend.api.adapters.trace_adapter import TraceAPIAdapter
from backend.api.schemas.trace import (
    TraceSummaryResponseSchema,
    TraceDetailResponseSchema,
    TraceEventResponseSchema,
    DecisionExplanationResponseSchema,
    DecisionDeltaResponseSchema
)

router = APIRouter(prefix="/traces", tags=["Decision Trace & Explainability"])


@router.get("", response_model=APIResponse[List[TraceSummaryResponseSchema]])
async def list_traces(
    request: Request,
    station_id: Optional[str] = Query(None, description="Optional station filter"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    policy_state: Optional[str] = Query(None, description="Optional policy state filter"),
    resilience_state: Optional[str] = Query(None, description="Optional resilience state filter"),
    limit: int = Query(50, ge=1, le=200, description="Max traces to return"),
    trace_service: TraceService = Depends(get_trace_service)
) -> APIResponse[List[TraceSummaryResponseSchema]]:
    """Lists compact summaries of recorded decision traces with filtering."""
    req_id = getattr(request.state, "request_id", None)
    summaries = trace_service.list_traces(
        station_id=station_id,
        status=status,
        policy_state=policy_state,
        resilience_state=resilience_state,
        limit=limit
    )
    items = [TraceAPIAdapter.to_summary_schema(s) for s in summaries]
    return APIResponse.success(data=items, request_id=req_id, provenance="SIMULATED")


@router.get("/{trace_id}", response_model=APIResponse[TraceDetailResponseSchema])
async def get_trace(
    trace_id: str,
    request: Request,
    trace_service: TraceService = Depends(get_trace_service)
) -> APIResponse[TraceDetailResponseSchema]:
    """Retrieves full auditable DecisionTrace record including stage events and lineage."""
    req_id = getattr(request.state, "request_id", None)
    trace = trace_service.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"DecisionTrace '{trace_id}' not found.")

    detail = TraceAPIAdapter.to_detail_schema(trace)
    return APIResponse.success(data=detail, request_id=req_id, provenance="SIMULATED")


@router.get("/{trace_id}/events", response_model=APIResponse[List[TraceEventResponseSchema]])
async def get_trace_events(
    trace_id: str,
    request: Request,
    trace_service: TraceService = Depends(get_trace_service)
) -> APIResponse[List[TraceEventResponseSchema]]:
    """Retrieves ordered sequence of atomic decision events for a trace."""
    req_id = getattr(request.state, "request_id", None)
    try:
        events = trace_service.repository.get_events(trace_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"DecisionTrace '{trace_id}' not found.")

    items = [TraceAPIAdapter.to_event_schema(e) for e in events]
    return APIResponse.success(data=items, request_id=req_id, provenance="SIMULATED")


@router.get("/{trace_id}/summary", response_model=APIResponse[TraceSummaryResponseSchema])
async def get_trace_summary(
    trace_id: str,
    request: Request,
    trace_service: TraceService = Depends(get_trace_service)
) -> APIResponse[TraceSummaryResponseSchema]:
    """Retrieves compact summary of a decision trace."""
    req_id = getattr(request.state, "request_id", None)
    trace = trace_service.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"DecisionTrace '{trace_id}' not found.")

    summary = TraceAPIAdapter.to_summary_schema(trace.to_summary())
    return APIResponse.success(data=summary, request_id=req_id, provenance="SIMULATED")


@router.get("/{trace_id}/explanation", response_model=APIResponse[DecisionExplanationResponseSchema])
async def get_trace_explanation(
    trace_id: str,
    request: Request,
    trace_service: TraceService = Depends(get_trace_service)
) -> APIResponse[DecisionExplanationResponseSchema]:
    """Retrieves deterministic, human-readable 'Why?' explanation for the decision."""
    req_id = getattr(request.state, "request_id", None)
    trace = trace_service.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"DecisionTrace '{trace_id}' not found.")

    if trace.explanation is None:
        raise HTTPException(status_code=404, detail=f"Explanation for '{trace_id}' unavailable.")

    exp = TraceAPIAdapter.to_explanation_schema(trace.explanation)
    return APIResponse.success(data=exp, request_id=req_id, provenance="SIMULATED")


@router.get("/{trace_id}/compare/{other_trace_id}", response_model=APIResponse[DecisionDeltaResponseSchema])
async def compare_traces(
    trace_id: str,
    other_trace_id: str,
    request: Request,
    trace_service: TraceService = Depends(get_trace_service)
) -> APIResponse[DecisionDeltaResponseSchema]:
    """Computes factual comparative delta between two decision traces."""
    req_id = getattr(request.state, "request_id", None)
    try:
        delta = trace_service.compare_traces(trace_id, other_trace_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    res = TraceAPIAdapter.to_delta_schema(delta)
    return APIResponse.success(data=res, request_id=req_id, provenance="SIMULATED")


@router.get("/{trace_id}/export")
async def export_trace(
    trace_id: str,
    format: str = Query("json", description="Export format: json | csv"),
    trace_service: TraceService = Depends(get_trace_service)
) -> Response:
    """Exports structured DecisionTrace record in JSON or CSV format."""
    try:
        content = trace_service.export_trace(trace_id, format_type=format)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"DecisionTrace '{trace_id}' not found.")

    if format.lower() == "csv":
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={trace_id}.csv"}
        )
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={trace_id}.json"}
    )
