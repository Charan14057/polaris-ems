"""
POLARIS-EMS — Health & Capabilities Routes
SIH26061: Polar Energy Management & Resilience System

Provides operational health, readiness, and capability discovery endpoints.
- GET /health
- GET /health/ready
- GET /health/capabilities
"""

from fastapi import APIRouter, Depends, Request
from datetime import datetime, timezone

from backend.api.responses import APIResponse
from backend.api.schemas.common import HealthResponse, ReadinessResponse, CapabilitiesResponse
from backend.api.dependencies import (
    get_profile_registry,
    get_scenario_registry,
    get_model_registry
)
from backend.data.station_profiles.loader import StationProfileRegistry
from backend.scenarios.registry import ScenarioRegistry
from backend.ml.registry import ModelRegistry

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=APIResponse[HealthResponse])
async def health(request: Request) -> APIResponse[HealthResponse]:
    """Basic operational liveness probe."""
    req_id = getattr(request.state, "request_id", "req-health")
    data = HealthResponse(
        service_status="HEALTHY",
        api_version="v1",
        project_name="Polaris-EMS — Polar Energy Management & Resilience System",
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.get("/health/ready", response_model=APIResponse[ReadinessResponse])
async def readiness(
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry),
    model_reg: ModelRegistry = Depends(get_model_registry)
) -> APIResponse[ReadinessResponse]:
    """Readiness probe checking availability of core station, scenario, and model registries."""
    req_id = getattr(request.state, "request_id", "req-ready")
    stations = profile_reg.list_stations()
    scenarios = scenario_reg.list_scenarios()
    models = model_reg.list_models()

    is_ready = len(stations) >= 3 and len(scenarios) >= 14
    data = ReadinessResponse(
        ready=is_ready,
        loaded_stations=stations,
        loaded_scenarios=len(scenarios),
        loaded_models=models,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.get("/health/capabilities", response_model=APIResponse[CapabilitiesResponse])
async def capabilities(
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry)
) -> APIResponse[CapabilitiesResponse]:
    """Discovers supported capabilities, horizons, and intelligence engines."""
    req_id = getattr(request.state, "request_id", "req-cap")
    data = CapabilitiesResponse(
        stations=profile_reg.list_stations(),
        horizons_supported_hours=[1, 6, 12, 24, 48, 168],
        forecasting={
            "owning_phase": "Phase 3",
            "targets": ["total_load_kw", "solar_generation_kw", "wind_generation_kw"],
            "calibrated_quantiles": ["P10", "P50", "P90", "P95"],
            "uncertainty_calibration": "Split Conformal Prediction"
        },
        twin_simulation={
            "owning_phase": "Phase 4",
            "physical_subsystems": ["electrical", "battery", "diesel", "fuel", "thermal", "environment"],
            "constraints_evaluated": 10,
            "power_balance_tolerance_kw": 0.02
        },
        scenarios={
            "owning_phase": "Phase 5",
            "registered_count": len(scenario_reg.list_scenarios()),
            "categories": ["ENVIRONMENTAL", "ASSET_FAILURE", "LOGISTICAL", "COMPOUND"]
        },
        optimizer={
            "owning_phase": "Phase 6",
            "solver": "HiGHS MILP",
            "modes": ["EXPECTED", "CONSERVATIVE", "SCENARIO_ROBUST"],
            "relative_gap_tolerance": 0.03
        },
        resilience={
            "owning_phase": "Phase 7",
            "states": ["SAFE", "WATCH", "AT_RISK", "THREATENED", "CRITICAL", "RECOVERY"],
            "dimensions_count": 9,
            "horizons": ["battery", "thermal", "fuel", "critical_load", "resupply_gap"]
        },
        policy_governance={
            "owning_phase": "Phase 8",
            "states": ["NO_ACTION", "MONITOR", "PREPARE", "MITIGATE", "PROTECT", "RECOVER", "ESCALATE", "BLOCKED", "INVALID_INPUT"],
            "priorities": ["P1_CRITICAL_LIFE_SAFETY", "P2_CRITICAL_LOAD_PROTECTION", "P3_GENERATION_RESERVE_PROTECTION", "P4_THERMAL_SAFETY", "P5_FUEL_RESUPPLY_PROTECTION", "P6_STORAGE_PROTECTION", "P7_NONCRITICAL_OPTIMIZATION", "P8_MONITORING"],
            "enforcement_tiers": ["DIRECTLY_SUPPORTED", "DERIVED_FROM_SUPPORTED_INPUT", "DECLARATIVE_ONLY", "REQUIRES_OPTIMIZATION"]
        },
        provenance_tiers_supported=["REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"]
    )
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")
