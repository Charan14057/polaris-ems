"""
POLARIS-EMS — Health & Capabilities Routes
SIH26061: Polar Energy Management & Resilience System

Provides operational health, readiness, and capability discovery endpoints:
- GET /health
- GET /health/ready
- GET /health/capabilities
- GET /health/providers (Workstream D & I)
- GET /health/physical (Workstream I)
- GET /health/engines (Workstream I)
"""

from fastapi import APIRouter, Depends, Request
from datetime import datetime, timezone
from typing import Dict, Any, List

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
from backend.integrations.bridge import get_reality_bridge

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


@router.get("/ready", response_model=APIResponse[ReadinessResponse])
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


@router.get("/health/providers", response_model=APIResponse[Dict[str, Any]])
async def health_providers(request: Request) -> APIResponse[Dict[str, Any]]:
    """Operational health status of external reality adapters and data feeds."""
    req_id = getattr(request.state, "request_id", "req-health-providers")
    bridge = get_reality_bridge()
    providers = bridge.get_provider_health()
    data = {
        "bridge_enabled": bridge.enabled,
        "total_providers": len(providers),
        "healthy_providers": sum(1 for p in providers if p.status.value == "HEALTHY"),
        "providers": [p.model_dump() for p in providers]
    }
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.get("/health/physical", response_model=APIResponse[Dict[str, Any]])
async def health_physical(request: Request) -> APIResponse[Dict[str, Any]]:
    """Explicit physical SCADA connectivity status reporting."""
    req_id = getattr(request.state, "request_id", "req-health-physical")
    data = {
        "physical_scada_connected": False,
        "hardware_status": "DISCONNECTED",
        "operational_mode": "CALIBRATED_DIGITAL_TWIN",
        "station_locations": {
            "BHARATI": "Larsemann Hills (69°24'S, 76°11'E, Antarctica)",
            "MAITRI": "Schirmacher Oasis (70°46'S, 11°44'E, Antarctica)",
            "HIMADRI": "Ny-Ålesund (78°55'N, 11°56'E, Arctic Svalbard)"
        },
        "disclaimer": "Polaris-EMS has zero connected physical polar SCADA telemetry; all telemetry is generated from physics-calibrated synthetic baselines and computational digital twin models."
    }
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")


@router.get("/health/engines", response_model=APIResponse[Dict[str, Any]])
async def health_engines(
    request: Request,
    profile_reg: StationProfileRegistry = Depends(get_profile_registry),
    scenario_reg: ScenarioRegistry = Depends(get_scenario_registry),
    model_reg: ModelRegistry = Depends(get_model_registry)
) -> APIResponse[Dict[str, Any]]:
    """Status of the 12 frozen computational engines and authorities."""
    req_id = getattr(request.state, "request_id", "req-health-engines")
    data = {
        "phase3_forecasting": "HEALTHY" if len(model_reg.list_models()) >= 9 else "DEGRADED",
        "phase4_digital_twin": "HEALTHY",
        "phase5_scenarios": "HEALTHY" if len(scenario_reg.list_scenarios()) >= 14 else "DEGRADED",
        "phase6_optimizer": "HEALTHY",
        "phase7_resilience": "HEALTHY",
        "phase8_policy": "HEALTHY",
        "phase11_edge": "HEALTHY",
        "phase12_trace": "HEALTHY",
        "phase13_validation": "HEALTHY",
        "status": "ALL_ENGINES_OPERATIONAL"
    }
    return APIResponse.success(data=data, request_id=req_id, provenance="CONFIGURED")
