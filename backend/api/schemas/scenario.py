"""
POLARIS-EMS — Scenario API Schemas
SIH26061: Polar Energy Management & Resilience System

Typed schemas for Phase 5 Scenario Engine endpoints:
- Listing and inspecting the 14 locked polar stress scenarios.
- Executing stress tests through Twin replay and extracting impact metrics.
- Serialization size control via include_trajectory flag.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ParameterTransformSchema(BaseModel):
    parameter: str
    operator: str
    value: float
    unit: str
    rationale: str


class ScenarioSummarySchema(BaseModel):
    """Summary of a registered polar stress scenario."""
    scenario_id: str
    name: str
    description: str
    category: str
    duration_hours: int
    active_effects: List[str]
    provenance: str = "CONFIGURED"


class ScenarioDetailSchema(ScenarioSummarySchema):
    """Complete scenario definition with explicit parameter transforms."""
    transforms: List[ParameterTransformSchema]
    rationale: str


class ScenarioEvaluateRequestSchema(BaseModel):
    """Request payload to evaluate a scenario stress test."""
    station_id: str = Field(..., description="BHARATI | MAITRI | HIMADRI")
    scenario_id: str = Field(..., description="One of the 14 locked polar stress scenarios")
    horizon_hours: Optional[int] = Field(48, ge=1, le=168, description="Horizon duration in hours (1-168)")
    forecast_mode: str = Field("EXPECTED", description="EXPECTED | CONSERVATIVE | OPTIMISTIC")
    start_timestamp: Optional[str] = Field("2026-06-01T00:00:00Z", description="Starting observation timestamp")
    include_trajectory: bool = Field(False, description="Whether to include full per-step trajectory states")

    @field_validator("station_id")
    @classmethod
    def validate_station(cls, v: str) -> str:
        s = v.upper()
        if s not in {"BHARATI", "MAITRI", "HIMADRI"}:
            raise ValueError(f"Station '{v}' is invalid")
        return s


class ScenarioImpactMetricsSchema(BaseModel):
    delta_unserved_energy_kwh: float
    delta_critical_unserved_kwh: float
    delta_diesel_fuel_liters: float
    delta_min_indoor_temp_c: float
    delta_min_battery_soc: float
    primary_failure_mode: str
    earliest_failure_hour: Optional[float]
    failure_occurred: bool


class ScenarioEvaluateResponseData(BaseModel):
    """Result of scenario stress evaluation through Twin replay."""
    scenario_id: str
    station_id: str
    category: str
    duration_hours: int
    impact_metrics: ScenarioImpactMetricsSchema
    violated_constraints: List[str]
    failure_indicators: List[str]
    baseline_trajectory_summary: Dict[str, Any]
    scenario_trajectory_summary: Dict[str, Any]
    trajectory_states: Optional[List[Dict[str, Any]]] = None
    provenance: str = "SIMULATED"
