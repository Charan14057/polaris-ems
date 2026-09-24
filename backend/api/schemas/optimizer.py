"""
POLARIS-EMS — Optimizer API Schemas
SIH26061: Polar Energy Management & Resilience System

Typed schemas for Phase 6 Energy Optimizer endpoint:
- Solves multi-horizon dispatch with HiGHS MILP and validates via Digital Twin replay.
- Preserves explicit HiGHS optimality semantics (EXACT_OPTIMAL, MIP_GAP_OPTIMAL, FALLBACK).
- Controls serialization payload size via include_schedule flag.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class DecisionStepSchema(BaseModel):
    """Step-by-step dispatch decision output."""
    t: int
    timestamp: str
    p_diesel_kw: float
    p_battery_charge_kw: float
    p_battery_discharge_kw: float
    p_solar_kw: float
    p_wind_kw: float
    p_served_load_kw: float
    p_unserved_load_kw: float
    battery_soc: float
    fuel_remaining_l: float
    indoor_temp_c: float
    reserve_margin_pct: float


class OptimizationSummarySchema(BaseModel):
    """Summary metrics of the optimized dispatch."""
    total_cost: float
    total_fuel_consumed_liters: float
    total_unserved_load_kwh: float
    total_critical_unserved_kwh: float
    total_curtailed_renewable_kwh: float
    min_reserve_margin_pct: float
    final_battery_soc_pct: float
    final_fuel_remaining_liters: float
    min_indoor_temp_c: float


class OptimizeRequestSchema(BaseModel):
    """Input payload to trigger Phase 6 microgrid optimization."""
    station_id: str = Field(..., description="BHARATI | MAITRI | HIMADRI")
    horizon_hours: int = Field(48, ge=1, le=168, description="Optimization horizon in hours (1 to 168)")
    mode: str = Field("EXPECTED", description="EXPECTED | CONSERVATIVE | SCENARIO_ROBUST")
    generator_overrides: Optional[Dict[int, str]] = Field(None, description="e.g. {1: 'ONLINE', 2: 'FAULT'}")
    scenario_id: Optional[str] = Field(None, description="Optional scenario ID from ScenarioRegistry")
    start_timestamp: Optional[str] = Field("2026-06-01T00:00:00Z", description="Starting observation timestamp")
    include_schedule: bool = Field(False, description="Whether to include full per-step dispatch schedule array")

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


class OptimizeResponseData(BaseModel):
    """Complete optimization result preserving HiGHS optimality semantics."""
    station_id: str
    horizon_hours: int
    mode: str
    solver_status: str
    optimality_tier: str = Field(..., description="EXACT_OPTIMAL | MIP_GAP_OPTIMAL | FALLBACK | INFEASIBLE")
    objective_value: float
    best_bound: Optional[float] = None
    relative_gap: Optional[float] = None
    solve_time_sec: float
    is_valid: bool
    twin_replay_valid: bool
    summary: OptimizationSummarySchema
    schedule: Optional[List[DecisionStepSchema]] = None
    generator_schedules: Optional[Dict[int, List[Dict[str, Any]]]] = None
    provenance: str = "SIMULATED"
    diagnostics: List[str] = Field(default_factory=list)
