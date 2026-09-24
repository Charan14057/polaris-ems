"""
POLARIS-EMS — Common API Schemas
SIH26061: Polar Energy Management & Resilience System

Common shared Pydantic models:
- Health and readiness schemas
- Capability schema
- Provenance validations
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness check response schema."""
    service_status: str = "HEALTHY"
    api_version: str = "v1"
    project_name: str = "Polaris-EMS"
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness probe response schema."""
    ready: bool
    loaded_stations: List[str]
    loaded_scenarios: int
    loaded_models: List[str]
    timestamp: str


class CapabilitiesResponse(BaseModel):
    """Supported Polaris-EMS intelligence capabilities matrix."""
    stations: List[str]
    horizons_supported_hours: List[int]
    forecasting: Dict[str, Any]
    twin_simulation: Dict[str, Any]
    scenarios: Dict[str, Any]
    optimizer: Dict[str, Any]
    resilience: Dict[str, Any]
    policy_governance: Dict[str, Any]
    provenance_tiers_supported: List[str]
