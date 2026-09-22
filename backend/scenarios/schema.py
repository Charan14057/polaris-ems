"""
POLARIS-EMS — Scenario Definition & Result Schema
SIH26061: Polar Energy Management & Resilience System

Provides strongly typed schemas for scenario definitions, explicit transformation operators,
impact consequence metrics, and scenario simulation result contracts.
Maintains strict provenance:
- Original forecast: FORECAST
- Scenario parameters: CONFIGURED / ASSUMED
- Scenario-transformed effective inputs & trajectories: SIMULATED
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

from backend.twin.state import ProvenanceTier
from backend.twin.twin_engine import TwinTrajectory
from backend.twin.forecast_adapter import TwinInputStep


class TransformOperator(str, Enum):
    """Explicit mathematical and logical transformation operators."""
    SET = "SET"
    ADD = "ADD"
    MULTIPLY = "MULTIPLY"
    MIN = "MIN"
    MAX = "MAX"
    DELAY = "DELAY"
    DISABLE = "DISABLE"


class ScenarioCategory(str, Enum):
    """Formal categorization of polar stress scenarios."""
    ENVIRONMENTAL = "ENVIRONMENTAL"
    ASSET_FAILURE = "ASSET_FAILURE"
    LOGISTICS = "LOGISTICS"
    OPERATIONAL = "OPERATIONAL"
    COMPOUND = "COMPOUND"
    CUSTOM = "CUSTOM"


@dataclass
class ParameterTransform:
    """Explicitly declared parameter modification with operator semantics."""
    parameter: str
    operator: TransformOperator
    value: Union[float, int, str, bool]
    unit: str
    duration_hours: Optional[int] = None
    start_offset_hours: int = 0
    rationale: str = ""
    provenance: ProvenanceTier = "CONFIGURED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter": self.parameter,
            "operator": self.operator.value if isinstance(self.operator, TransformOperator) else str(self.operator),
            "value": self.value,
            "unit": self.unit,
            "duration_hours": self.duration_hours,
            "start_offset_hours": self.start_offset_hours,
            "rationale": self.rationale,
            "provenance": self.provenance
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ParameterTransform":
        op = TransformOperator(d["operator"]) if isinstance(d["operator"], str) else d["operator"]
        return cls(
            parameter=d["parameter"],
            operator=op,
            value=d["value"],
            unit=d.get("unit", ""),
            duration_hours=d.get("duration_hours"),
            start_offset_hours=d.get("start_offset_hours", 0),
            rationale=d.get("rationale", ""),
            provenance=d.get("provenance", "CONFIGURED")
        )


@dataclass
class ScenarioDefinition:
    """Strongly typed scenario definition specifying physical and operational stressors."""
    scenario_id: str
    name: str
    description: str
    category: ScenarioCategory
    duration_hours: int = 48
    start_offset_hours: int = 0
    transforms: List[ParameterTransform] = field(default_factory=list)
    active_effects: List[str] = field(default_factory=list)
    provenance: ProvenanceTier = "CONFIGURED"
    rationale: str = ""
    validation_rules: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value if isinstance(self.category, ScenarioCategory) else str(self.category),
            "duration_hours": self.duration_hours,
            "start_offset_hours": self.start_offset_hours,
            "transforms": [t.to_dict() for t in self.transforms],
            "active_effects": self.active_effects,
            "provenance": self.provenance,
            "rationale": self.rationale,
            "validation_rules": self.validation_rules
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScenarioDefinition":
        cat = ScenarioCategory(d["category"]) if isinstance(d["category"], str) else d["category"]
        transforms = [ParameterTransform.from_dict(t) for t in d.get("transforms", [])]
        return cls(
            scenario_id=d["scenario_id"],
            name=d["name"],
            description=d["description"],
            category=cat,
            duration_hours=d.get("duration_hours", 48),
            start_offset_hours=d.get("start_offset_hours", 0),
            transforms=transforms,
            active_effects=d.get("active_effects", []),
            provenance=d.get("provenance", "CONFIGURED"),
            rationale=d.get("rationale", ""),
            validation_rules=d.get("validation_rules", {})
        )


@dataclass
class ScenarioImpactMetrics:
    """Exact numerical consequence deltas comparing baseline against scenario."""
    delta_fuel_burn_liters: float
    delta_unserved_energy_kwh: float
    delta_critical_unserved_energy_kwh: float
    delta_min_battery_soc: float
    delta_reserve_margin_pct: float
    delta_continuity_horizon_hours: float
    delta_min_indoor_temperature_c: float
    delta_diesel_runtime_hours: float
    delta_renewable_utilization_pct: float
    scenario_failure_time_h: Optional[int]
    first_constraint_violation: Optional[str]
    first_threat_transition: Optional[str]
    primary_failure_signature: str
    secondary_failure_signatures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScenarioResult:
    """Authoritative result contract capturing baseline vs scenario outcomes and lineage."""
    scenario_id: str
    station_id: str
    scenario_name: str
    start_time: str
    duration_hours: int
    forecast_mode: str  # "EXPECTED" | "CONSERVATIVE" | "OPTIMISTIC" (deterministic stress trajectories)
    baseline_trajectory: TwinTrajectory
    scenario_trajectory: TwinTrajectory
    original_forecast: List[TwinInputStep]
    scenario_transforms: List[ParameterTransform]
    effective_simulation_inputs: List[TwinInputStep]
    baseline_summary: Dict[str, Any]
    scenario_summary: Dict[str, Any]
    impact_metrics: ScenarioImpactMetrics
    primary_failure_signature: str
    secondary_failure_signatures: List[str]
    constraints_violated: List[str]
    resilience_status: Dict[str, Any]
    provenance: str = "SIMULATED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "station_id": self.station_id,
            "scenario_name": self.scenario_name,
            "start_time": self.start_time,
            "duration_hours": self.duration_hours,
            "forecast_mode": self.forecast_mode,
            "baseline_summary": self.baseline_summary,
            "scenario_summary": self.scenario_summary,
            "impact_metrics": self.impact_metrics.to_dict(),
            "primary_failure_signature": self.primary_failure_signature,
            "secondary_failure_signatures": self.secondary_failure_signatures,
            "constraints_violated": self.constraints_violated,
            "resilience_status": self.resilience_status,
            "scenario_transforms": [t.to_dict() for t in self.scenario_transforms],
            "provenance": self.provenance
        }
