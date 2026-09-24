"""
POLARIS-EMS — Machine Learning Forecasting Routes
SIH26061: Polar Energy Management & Resilience System

Provides multi-horizon probabilistic forecasting endpoints powered by Phase 3 ML models:
- POST /api/v1/forecast
"""

from fastapi import APIRouter, Depends, Request

from backend.api.responses import APIResponse
from backend.api.schemas.forecast import ForecastRequestSchema, ForecastResponseData
from backend.api.dependencies import get_inference_engine, get_profile_registry
from backend.api.adapters.forecast_adapter import ForecastAPIAdapter
from backend.ml.inference import InferenceEngine
from backend.data.station_profiles.loader import StationProfileRegistry
from backend.api.errors import StationNotFoundException

router = APIRouter(prefix="/forecast", tags=["Forecasting"])


@router.post("", response_model=APIResponse[ForecastResponseData])
async def execute_forecast(
    req: ForecastRequestSchema,
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    inference_engine: InferenceEngine = Depends(get_inference_engine)
) -> APIResponse[ForecastResponseData]:
    """
    Executes a causal multi-horizon probabilistic forecast for a station energy target.
    Outputs point predictions and calibrated P10, P50, P90, P95 intervals.
    """
    req_id = getattr(request.state, "request_id", None)
    sid = req.station_id.upper()
    try:
        profile_reg.get(sid)
    except KeyError:
        raise StationNotFoundException(sid)

    adapter = ForecastAPIAdapter(inference_engine=inference_engine)
    data = adapter.execute_forecast(req)

    return APIResponse.success(
        data=data,
        request_id=req_id,
        provenance="FORECAST"
    )
