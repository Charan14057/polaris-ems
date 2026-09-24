"""
POLARIS-EMS — External Reality Bridge & Operational Validation API Endpoints
SIH26061: Polar Energy Management & Resilience System

Provides external provider discovery, reality bridge diagnostics, weather queries,
model-vs-observed metrics, operational drift monitoring, twin reality checks, and replay.

Endpoints:
- GET  /api/v1/integrations/status
- GET  /api/v1/integrations/providers
- GET  /api/v1/integrations/weather/{station_id}
- GET  /api/v1/integrations/series/{station_id}
- GET  /api/v1/integrations/freshness
- GET  /api/v1/integrations/validation/metrics
- GET  /api/v1/integrations/validation/drift
- GET  /api/v1/integrations/validation/twin-check
- GET  /api/v1/integrations/validation/candidates
- POST /api/v1/integrations/replay
- POST /api/v1/integrations/ingest
"""

from fastapi import APIRouter, Request, Query, Path, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from backend.api.responses import APIResponse
from backend.integrations.bridge import get_reality_bridge, ExternalRealityBridge
from backend.integrations.schemas import (
    ProviderHealthRecord,
    ExternalValidationResult,
    ExternalWeatherObservation,
    ExternalForecastSeries,
    ModelVsObservedMetric,
    TwinRealityMetric,
    CalibrationCandidate,
    DriftIndicator,
    OperationalReplayResult,
)
from backend.integrations.evaluator import get_model_evaluator
from backend.integrations.twin_reality import get_twin_reality_engine
from backend.integrations.drift import get_drift_detector

router = APIRouter(prefix="/integrations", tags=["External Integrations"])


class ReplayRequestSchema(BaseModel):
    """Payload for initiating an operational decision replay."""
    station_id: str = Field(..., description="Target polar research station")
    horizon_hours: int = Field(default=48, ge=1, le=168, description="Replay horizon in hours")
    mode: str = Field(default="EXPECTED", description="Optimizer mode (EXPECTED, CONSERVATIVE, SCENARIO_ROBUST)")
    scenario_id: Optional[str] = Field(None, description="Optional stress scenario preset")


@router.get("/status", response_model=APIResponse[Dict[str, Any]])
async def get_bridge_status(request: Request) -> APIResponse[Dict[str, Any]]:
    """Executive status of the external reality bridge and connected adapters."""
    req_id = getattr(request.state, "request_id", "req-bridge-status")
    bridge = get_reality_bridge()
    summary = bridge.get_bridge_summary()
    return APIResponse.success(data=summary, request_id=req_id, provenance="CONFIGURED")


@router.get("/providers", response_model=APIResponse[List[ProviderHealthRecord]])
async def list_providers(request: Request) -> APIResponse[List[ProviderHealthRecord]]:
    """Lists all registered external reality adapters and their operational health."""
    req_id = getattr(request.state, "request_id", "req-providers")
    bridge = get_reality_bridge()
    records = bridge.get_provider_health()
    return APIResponse.success(data=records, request_id=req_id, provenance="CONFIGURED")


@router.get("/weather/{station_id}", response_model=APIResponse[ExternalValidationResult])
async def get_station_weather(
    request: Request,
    station_id: str = Path(..., description="Target polar research station (BHARATI, MAITRI, HIMADRI)"),
    provider: Optional[str] = Query(None, description="Preferred provider adapter (e.g. openmeteo, ncpor, spooler)")
) -> APIResponse[ExternalValidationResult]:
    """Queries external weather observation for a polar station with quality validation and fallback."""
    req_id = getattr(request.state, "request_id", f"req-weather-{station_id.lower()}")
    bridge = get_reality_bridge()
    result = bridge.get_weather_observation(station_id=station_id, preferred_provider=provider)
    return APIResponse.success(data=result, request_id=req_id, provenance=result.provenance)


@router.get("/series/{station_id}", response_model=APIResponse[Optional[ExternalForecastSeries]])
async def get_station_weather_series(
    request: Request,
    station_id: str = Path(..., description="Target polar research station (BHARATI, MAITRI, HIMADRI)"),
    horizon_hours: int = Query(48, ge=1, le=168, description="Forward forecast horizon in hours"),
    provider: Optional[str] = Query(None, description="Preferred provider adapter")
) -> APIResponse[Optional[ExternalForecastSeries]]:
    """Fetches and validates multi-horizon forward forecast series."""
    req_id = getattr(request.state, "request_id", f"req-series-{station_id.lower()}")
    bridge = get_reality_bridge()
    series = bridge.get_forecast_series(station_id=station_id, horizon_hours=horizon_hours, preferred_provider=provider)
    provenance = series.provenance if series else "CONFIGURED"
    return APIResponse.success(data=series, request_id=req_id, provenance=provenance)


@router.get("/freshness", response_model=APIResponse[Dict[str, Any]])
async def get_data_freshness(request: Request) -> APIResponse[Dict[str, Any]]:
    """Reports data freshness across all monitored stations and external bridges."""
    req_id = getattr(request.state, "request_id", "req-freshness")
    bridge = get_reality_bridge()
    providers = bridge.get_provider_health()

    data = {
        "overall_freshness": "ACCEPTABLE" if bridge.enabled else "OFFLINE_CALIBRATED",
        "external_data_enabled": bridge.enabled,
        "providers_freshness": {p.provider_name: p.freshness_status.value for p in providers},
        "physical_scada_connected": False,
        "operational_posture": "CALIBRATED_DIGITAL_TWIN"
    }
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.get("/validation/metrics", response_model=APIResponse[List[ModelVsObservedMetric]])
async def get_validation_metrics(
    request: Request,
    station_id: Optional[str] = Query(None, description="Optional station filter")
) -> APIResponse[List[ModelVsObservedMetric]]:
    """Retrieves operational model-vs-observed accuracy and calibration metrics."""
    req_id = getattr(request.state, "request_id", "req-val-metrics")
    evaluator = get_model_evaluator()
    if station_id:
        data = evaluator.get_summary_by_station(station_id)
    else:
        data = evaluator.get_all_metrics()
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.get("/validation/drift", response_model=APIResponse[List[DriftIndicator]])
async def get_operational_drift(
    request: Request,
    active_only: bool = Query(False, description="Filter for active drift detections only")
) -> APIResponse[List[DriftIndicator]]:
    """Reports active operational drift indicators across environmental, predictive, and physical layers."""
    req_id = getattr(request.state, "request_id", "req-drift")
    detector = get_drift_detector()
    data = detector.get_active_drift() if active_only else detector.get_all_indicators()
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.get("/validation/twin-check", response_model=APIResponse[List[TwinRealityMetric]])
async def get_twin_reality_checks(request: Request) -> APIResponse[List[TwinRealityMetric]]:
    """Reports Digital Twin physical conservation residuals against field observations."""
    req_id = getattr(request.state, "request_id", "req-twin-check")
    engine = get_twin_reality_engine()
    data = engine.get_all_metrics()
    return APIResponse.success(data=data, request_id=req_id, provenance="SIMULATED")


@router.get("/validation/candidates", response_model=APIResponse[List[CalibrationCandidate]])
async def get_calibration_candidates(request: Request) -> APIResponse[List[CalibrationCandidate]]:
    """Lists proposed model recalibration candidates governed under change-control protocols."""
    req_id = getattr(request.state, "request_id", "req-candidates")
    engine = get_twin_reality_engine()
    data = engine.get_calibration_candidates()
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.post("/replay", response_model=APIResponse[OperationalReplayResult])
async def execute_operational_replay(
    request: Request,
    body: ReplayRequestSchema = Body(...)
) -> APIResponse[OperationalReplayResult]:
    """Replays external weather series through the full frozen decision pipeline."""
    req_id = getattr(request.state, "request_id", "req-replay")
    bridge = get_reality_bridge()
    series = bridge.get_forecast_series(station_id=body.station_id, horizon_hours=body.horizon_hours)

    if not series:
        # Fallback to a synthetic observation series if external provider is disabled
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        steps = [
            ExternalWeatherObservation(
                station_id=body.station_id.upper(),
                timestamp=now + timedelta(hours=i),
                ambient_temperature_c=-15.0 - (5.0 if i > 12 else 0.0),
                wind_speed_ms=12.0 + (6.0 if i > 20 else 0.0),
                solar_irradiance_wm2=180.0 if (6 <= (i % 24) <= 18) else 0.0,
                direct_normal_irradiance_wm2=180.0 if (6 <= (i % 24) <= 18) else 0.0,
                surface_pressure_hpa=985.0,
                relative_humidity_pct=65.0,
                source_provider="CalibratedBaselineSpooler",
                provenance="SYNTHETIC"
            )
            for i in range(body.horizon_hours)
        ]
        series = ExternalForecastSeries(
            station_id=body.station_id.upper(),
            forecast_origin=now,
            horizon_hours=body.horizon_hours,
            steps=steps,
            source_provider="CalibratedBaselineSpooler",
            provenance="SYNTHETIC"
        )

    from backend.integrations.replay import get_replay_orchestrator
    replay_orch = get_replay_orchestrator()
    result = replay_orch.replay_external_series(
        station_id=body.station_id,
        series=series,
        mode=body.mode,
        scenario_id=body.scenario_id
    )
    return APIResponse.success(data=result, request_id=req_id, provenance="SIMULATED")


@router.post("/ingest", response_model=APIResponse[ExternalValidationResult])
async def ingest_external_observation(
    request: Request,
    observation: ExternalWeatherObservation = Body(...)
) -> APIResponse[ExternalValidationResult]:
    """Ingests and validates an ad-hoc external observation (e.g. from satcom spool or operator input)."""
    req_id = getattr(request.state, "request_id", "req-ingest")
    bridge = get_reality_bridge()
    result = bridge.validator.validate_weather(observation)
    return APIResponse.success(data=result, request_id=req_id, provenance=result.provenance)
