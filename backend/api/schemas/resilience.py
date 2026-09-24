"""
POLARIS-EMS — Resilience API Schemas
SIH26061: Polar Energy Management & Resilience System

Typed schemas for Phase 7 Resilience Engine endpoint:
- Exposes multi-horizon survivability, 9 resilience dimensions, composite index,
  threat decomposition, and candidate advisory recovery options.
- Controls response size via include_propagation flag.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class SurvivalHorizonsSchema(BaseModel):
    overall_station_survival_horizon_h: float
    battery_endurance_horizon_h: float
    thermal_habitability_horizon_h: float
    fuel_endurance_horizon_h: float
    critical_load_survival_horizon_h: float
    resupply_gap_survivability_h: float
    dependable_generation_horizon_h: float = 0.0
    binding_subsystem: str
    survives_full_horizon: bool


class ResilienceDimensionsSchema(BaseModel):
    energy_adequacy: float
    critical_load_resilience: float
    thermal_resilience: float
    generation_resilience: float
    storage_resilience: float
    fuel_resilience: float
    logistics_resilience: float
    renewable_resilience: float
    recovery_resilience: float
    composite_index: float
    composite_resilience_index: float
    electrical_autonomy: Optional[float] = None
    thermal_habitability: Optional[float] = None
    fuel_endurance: Optional[float] = None
    renewable_penetration: Optional[float] = None
    generation_headroom: Optional[float] = None
    storage_health: Optional[float] = None
    operational_margin: Optional[float] = None
    logistics_buffer: Optional[float] = None
    mission_continuity: Optional[float] = None
    explainable_loss: Optional[Dict[str, float]] = None


class ThreatIndicatorSchema(BaseModel):
    threat_type: str
    severity: str
    trigger_condition: str
    affected_subsystems: List[str]


class CandidateRecoveryOptionSchema(BaseModel):
    action_type: str
    description: str
    target_subsystem: str
    rationale: str = ""
    expected_survival_horizon_gain_h: float = 0.0
    expected_reserve_margin_gain_pct: float = 0.0
    urgency: str = "INFO"
    validation_tier: str = "ESTIMATED"
    limitations: str = "Advisory recommendation only; policy engine execution reserved for Phase 8"
    action_id: Optional[str] = None
    expected_gain_h: Optional[float] = None
    fuel_penalty_l: Optional[float] = 0.0
    advisory_only: bool = True


class ResilienceEvaluateRequestSchema(BaseModel):
    """Request payload to evaluate station resilience."""
    station_id: str = Field(..., description="BHARATI | MAITRI | HIMADRI")
    horizon_hours: int = Field(48, ge=1, le=168, description="Horizon duration in hours (1-168)")
    scenario_id: Optional[str] = Field(None, description="Optional scenario ID from ScenarioRegistry")
    start_timestamp: Optional[str] = Field("2026-06-01T00:00:00Z", description="Starting observation timestamp")
    include_propagation: bool = Field(False, description="Whether to include full failure propagation chain")

    @field_validator("station_id")
    @classmethod
    def validate_station(cls, v: str) -> str:
        s = v.upper()
        if s not in {"BHARATI", "MAITRI", "HIMADRI"}:
            raise ValueError(f"Station '{v}' is invalid")
        return s


class ResilienceEvaluateResponseData(BaseModel):
    """Structured resilience assessment output from Phase 7."""
    station_id: str
    assessment_timestamp: str
    horizon_hours: int
    assessment_status: str
    resilience_state: str = Field(..., description="SAFE | WATCH | AT_RISK | THREATENED | CRITICAL | RECOVERY")
    survival_horizons: SurvivalHorizonsSchema
    dimensions: Optional[ResilienceDimensionsSchema] = None
    threat_decomposition: List[ThreatIndicatorSchema] = Field(default_factory=list)
    candidate_recovery_options: List[CandidateRecoveryOptionSchema] = Field(default_factory=list)
    failure_propagation: Optional[List[Dict[str, Any]]] = None
    provenance: str = "SIMULATED"
