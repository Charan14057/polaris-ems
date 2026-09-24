"""
POLARIS-EMS — Optimizer Result and Decision Schemas
SIH26061: Polar Energy Management & Resilience System

Provides strongly typed contracts for MILP decision schedules, per-generator unit commitment,
effective resupply schedules, summary KPIs, and overall optimization results.
Strictly adheres to:
- Per-generator decision variables and aggregate mapping
- Battery throughput and wear proxy terminology (no unsupported degradation claims)
- Effective resupply schedule integration
- Strict provenance="SIMULATED"
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class OptimizationMode(str, Enum):
    """Operational mode driving optimizer quantile selections and reserve parameters."""
    EXPECTED = "EXPECTED"                # P50 load, P50 solar, P50 wind
    CONSERVATIVE = "CONSERVATIVE"        # P90 load, P10 solar, P10 wind, elevated reserve
    SCENARIO_ROBUST = "SCENARIO_ROBUST"  # Phase 5 scenario stress regime


class SolverStatus(str, Enum):
    """Standardized solver execution outcome."""
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    UNBOUNDED = "UNBOUNDED"
    TIME_LIMIT = "TIME_LIMIT"
    ERROR = "ERROR"


@dataclass
class GeneratorScheduleStep:
    """Per-generator dispatch decision at a specific timestep."""
    generator_id: int
    is_online: bool
    is_started: bool
    is_stopped: bool
    power_kw: float
    rated_kw: float
    min_power_kw: float


@dataclass
class DecisionStep:
    """Comprehensive microgrid dispatch decision for a single timestep."""
    timestamp: str
    horizon_h: int
    diesel_total_kw: float
    online_generator_count: int
    generator_schedules: List[GeneratorScheduleStep]
    battery_charge_kw: float
    battery_discharge_kw: float
    battery_soc_pct: float
    battery_energy_kwh: float
    solar_generation_kw: float
    solar_curtailed_kw: float
    wind_generation_kw: float
    wind_curtailed_kw: float
    load_served_kw: float
    load_unserved_kw: float
    critical_served_kw: float
    critical_unserved_kw: float
    flexible_served_kw: float
    heating_power_kw: float
    indoor_temp_c: float
    fuel_burned_liters: float
    fuel_remaining_liters: float
    dependable_reserve_kw: float
    reserve_margin_pct: float


@dataclass
class EffectiveResupplyEvent:
    """Synthesized resupply arrival event accounting for baseline schedules and scenario delays."""
    step_index: int
    timestamp: str
    fuel_delivered_liters: float
    is_delayed: bool = False
    delay_hours: int = 0
    provenance: str = "CONFIGURED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizationSummary:
    """Aggregated operational metrics computed across the optimized horizon."""
    total_fuel_consumed_liters: float
    final_fuel_remaining_liters: float
    total_renewable_generation_kwh: float
    total_renewable_curtailment_kwh: float
    renewable_utilization_pct: float
    battery_throughput_kwh: float          # Cumulative kWh charged + discharged
    min_battery_soc_pct: float
    final_battery_soc_pct: float
    total_critical_unserved_kwh: float
    total_noncritical_unserved_kwh: float
    critical_survival_passed: bool
    total_generator_starts: int
    total_generator_runtime_hours: float
    min_indoor_temp_c: float
    thermal_violation_degree_hours: float
    min_reserve_margin_pct: float
    objective_value: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizationResult:
    """Complete output contract of the Polaris-EMS Optimization Engine."""
    run_id: str
    station_id: str
    forecast_origin: str
    horizon_hours: int
    optimization_mode: OptimizationMode
    scenario_id: str
    solver_status: SolverStatus
    solver_time_seconds: float
    solver_termination_condition: str
    is_valid: bool
    validation_messages: List[str]
    decision_schedule: List[DecisionStep]
    effective_resupply_schedule: List[EffectiveResupplyEvent]
    summary: OptimizationSummary
    fallback_used: bool = False
    incumbent_objective: Optional[float] = None
    best_bound: Optional[float] = None
    relative_mip_gap: Optional[float] = None
    optimality_tier: str = "MIP_GAP_OPTIMAL"  # EXACT_OPTIMAL | MIP_GAP_OPTIMAL | GAP_ACCEPTED | FALLBACK
    model_version: str = "0.6.0"
    optimizer_version: str = "0.6.0"
    provenance: str = "SIMULATED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "station_id": self.station_id,
            "forecast_origin": self.forecast_origin,
            "horizon_hours": self.horizon_hours,
            "optimization_mode": self.optimization_mode.value if isinstance(self.optimization_mode, OptimizationMode) else str(self.optimization_mode),
            "scenario_id": self.scenario_id,
            "solver_status": self.solver_status.value if isinstance(self.solver_status, SolverStatus) else str(self.solver_status),
            "solver_time_seconds": round(self.solver_time_seconds, 3),
            "solver_termination_condition": self.solver_termination_condition,
            "is_valid": self.is_valid,
            "validation_messages": self.validation_messages,
            "effective_resupply_schedule": [e.to_dict() for e in self.effective_resupply_schedule],
            "summary": self.summary.to_dict(),
            "fallback_used": self.fallback_used,
            "incumbent_objective": self.incumbent_objective,
            "best_bound": self.best_bound,
            "relative_mip_gap": self.relative_mip_gap,
            "optimality_tier": self.optimality_tier,
            "model_version": self.model_version,
            "optimizer_version": self.optimizer_version,
            "provenance": self.provenance
        }
