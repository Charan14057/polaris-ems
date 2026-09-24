"""
POLARIS-EMS — End-to-End Pipeline API Schemas
SIH26061: Polar Energy Management & Resilience System

Typed schemas for the unified pipeline orchestration endpoint:
Forecast -> Scenario -> Optimize -> Twin Replay -> Resilience -> Policy.
Preserves execution stage lineages and reports granular failures without fabricating downstream data.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from backend.api.schemas.forecast import ForecastResponseData
from backend.api.schemas.scenario import ScenarioEvaluateResponseData
from backend.api.schemas.optimizer import OptimizeResponseData
from backend.api.schemas.resilience import ResilienceEvaluateResponseData
from backend.api.schemas.policy import PolicyEvaluateResponseData, HysteresisStateSchema


class PipelineStageStatus(BaseModel):
    """Execution status and duration for a single pipeline stage."""
    stage_name: str = Field(..., description="FORECAST | SCENARIO | OPTIMIZER | TWIN_REPLAY | RESILIENCE | POLICY")
    status: str = Field(..., description="COMPLETED | SKIPPED | FAILED")
    duration_sec: float
    message: str


class PipelineAnalyzeRequestSchema(BaseModel):
    """Input payload to execute the full end-to-end Polaris-EMS decision pipeline."""
    station_id: str = Field(..., description="BHARATI | MAITRI | HIMADRI")
    horizon_hours: int = Field(48, ge=1, le=168, description="Analysis horizon in hours (1-168)")
    scenario_id: Optional[str] = Field(None, description="Optional polar stress scenario ID")
    mode: str = Field("EXPECTED", description="EXPECTED | CONSERVATIVE | SCENARIO_ROBUST")
    start_timestamp: Optional[str] = Field("2026-06-01T00:00:00Z", description="Starting observation timestamp")
    generator_overrides: Optional[Dict[int, str]] = Field(None, description="e.g. {1: 'ONLINE', 2: 'FAULT'}")
    previous_hysteresis: Optional[HysteresisStateSchema] = Field(None, description="Previous hysteresis state")

    @field_validator("station_id")
    @classmethod
    def validate_station(cls, v: str) -> str:
        s = v.upper()
        if s not in {"BHARATI", "MAITRI", "HIMADRI"}:
            raise ValueError(f"Station '{v}' is invalid")
        return s

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        valid_modes = {"EXPECTED", "CONSERVATIVE", "SCENARIO_ROBUST"}
        if v.upper() not in valid_modes:
            raise ValueError(f"Mode '{v}' must be one of {valid_modes}")
        return v.upper()


class PipelineAnalyzeResponseData(BaseModel):
    """Consolidated results of the full end-to-end intelligence pipeline."""
    pipeline_run_id: str
    station_id: str
    horizon_hours: int
    scenario_id: Optional[str] = None
    overall_status: str = Field(..., description="SUCCESS | PARTIAL | ERROR")
    stages: List[PipelineStageStatus] = Field(default_factory=list)
    forecast: Optional[ForecastResponseData] = None
    scenario: Optional[ScenarioEvaluateResponseData] = None
    optimizer: Optional[OptimizeResponseData] = None
    resilience: Optional[ResilienceEvaluateResponseData] = None
    policy: Optional[PolicyEvaluateResponseData] = None
    decision_trace_id: Optional[str] = Field(None, description="Unique linked Phase 12 Decision Trace ID")
    provenance: str = "SIMULATED"
