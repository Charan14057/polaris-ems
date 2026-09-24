"""
POLARIS-EMS — Resilience Engine Schemas & Contracts
SIH26061: Polar Energy Management & Resilience System

Defines strongly typed, deterministic data contracts for Phase 7 Resilience Engine:
- States: SAFE, WATCH, AT_RISK, THREATENED, CRITICAL, RECOVERY
- 9 Resilience Dimensions & Explainable Engineering Index
- Multi-Horizon Survival & Earliest Time-to-Critical
- Threat Decomposition & Failure Propagation Chains
- Candidate Advisory Recovery Options (Non-Executing)
- Counterfactual Resilience Comparisons
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum


class ResilienceStateEnum(str, Enum):
    """
    Deterministic resilience state classifications.
    Severity Precedence:
        CRITICAL > THREATENED > AT_RISK > WATCH > RECOVERY > SAFE
    """
    CRITICAL = "CRITICAL"
    THREATENED = "THREATENED"
    AT_RISK = "AT_RISK"
    WATCH = "WATCH"
    RECOVERY = "RECOVERY"
    SAFE = "SAFE"


class ResilienceThreatEnum(str, Enum):
    """Identifiable physical and operational threat drivers."""
    EXTREME_COLD = "EXTREME_COLD"
    LOW_DAYLIGHT = "LOW_DAYLIGHT"
    POLAR_NIGHT = "POLAR_NIGHT"
    RENEWABLE_SHORTFALL = "RENEWABLE_SHORTFALL"
    SOLAR_FAILURE = "SOLAR_FAILURE"
    WIND_FAILURE = "WIND_FAILURE"
    BATTERY_DERATING = "BATTERY_DERATING"
    GENERATOR_OUTAGE = "GENERATOR_OUTAGE"
    MAINTENANCE_AVAILABILITY_LOSS = "MAINTENANCE_AVAILABILITY_LOSS"
    FUEL_SHORTAGE = "FUEL_SHORTAGE"
    RESUPPLY_DELAY = "RESUPPLY_DELAY"
    RESERVE_EROSION = "RESERVE_EROSION"
    THERMAL_STRESS = "THERMAL_STRESS"
    COMBINED_POLAR_STRESS = "COMBINED_POLAR_STRESS"


class FailureSeverityEnum(str, Enum):
    """Severity tier for threats and propagation steps."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class RecoveryActionTypeEnum(str, Enum):
    """Candidate resilience recovery actions (Advisory Only)."""
    INCREASE_DIESEL_COMMITMENT = "INCREASE_DIESEL_COMMITMENT"
    PRESERVE_BATTERY_RESERVE = "PRESERVE_BATTERY_RESERVE"
    SHED_NONCRITICAL_LOAD = "SHED_NONCRITICAL_LOAD"
    SHIFT_FLEXIBLE_LOAD = "SHIFT_FLEXIBLE_LOAD"
    PROTECT_CRITICAL_THERMAL = "PROTECT_CRITICAL_THERMAL"
    PREPARE_GENERATOR_HOT_STANDBY = "PREPARE_GENERATOR_HOT_STANDBY"
    PRESERVE_FUEL_UNTIL_RESUPPLY = "PRESERVE_FUEL_UNTIL_RESUPPLY"
    REDUCE_RENEWABLE_DEPENDENCY = "REDUCE_RENEWABLE_DEPENDENCY"
    ENTER_STATION_RECOVERY_MODE = "ENTER_STATION_RECOVERY_MODE"
    MAINTAIN_ADDITIONAL_RESERVE = "MAINTAIN_ADDITIONAL_RESERVE"


class AssessmentStatusEnum(str, Enum):
    """Execution status of the resilience assessment."""
    COMPLETED = "COMPLETED"
    INPUT_INVALID = "INPUT_INVALID"
    INCOMPLETE = "INCOMPLETE"
    NO_DATA = "NO_DATA"


@dataclass
class SurvivalHorizons:
    """
    Subsystem-level survival durations and overall binding limit.
    All horizons are bounded by the input trajectory length [0.0, horizon_hours].
    """
    critical_load_survival_horizon_h: float
    thermal_habitability_horizon_h: float
    battery_endurance_horizon_h: float
    fuel_endurance_horizon_h: float
    dependable_generation_horizon_h: float
    resupply_gap_survivability_h: float
    overall_station_survival_horizon_h: float
    binding_subsystem: str  # "CRITICAL_LOAD" | "THERMAL" | "BATTERY" | "FUEL" | "GENERATION" | "RESUPPLY" | "NONE"
    survives_full_horizon: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ThreatIndicator:
    """Detailed metadata for an active threat condition."""
    threat_type: ResilienceThreatEnum
    severity: FailureSeverityEnum
    trigger_condition: str
    affected_subsystems: List[str]
    first_observed_timestep: Optional[str] = None
    first_observed_hour: Optional[float] = None
    provenance: str = "SIMULATED"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["threat_type"] = self.threat_type.value
        d["severity"] = self.severity.value
        return d


@dataclass
class TimeToThreat:
    """
    Earliest validated chronological timestamps and hours to threshold breach.
    None indicates no threshold breach observed within the evaluated trajectory.
    """
    time_to_reserve_violation_h: Optional[float] = None
    time_to_reserve_violation_timestamp: Optional[str] = None

    time_to_battery_terminal_threshold_h: Optional[float] = None
    time_to_battery_terminal_threshold_timestamp: Optional[str] = None

    time_to_fuel_threshold_h: Optional[float] = None
    time_to_fuel_threshold_timestamp: Optional[str] = None

    time_to_thermal_safety_threshold_h: Optional[float] = None
    time_to_thermal_safety_threshold_timestamp: Optional[str] = None

    time_to_critical_load_failure_h: Optional[float] = None
    time_to_critical_load_failure_timestamp: Optional[str] = None

    time_to_resupply_related_vulnerability_h: Optional[float] = None
    time_to_resupply_related_vulnerability_timestamp: Optional[str] = None

    time_to_overall_critical_state_h: Optional[float] = None
    time_to_overall_critical_state_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DimensionScore:
    """Explainable scoring details for an individual resilience dimension."""
    dimension_name: str
    raw_metric: float
    normalized_score: float  # [0.0, 100.0]
    weight: float            # Configured weight contribution
    weighted_contribution: float
    reference_threshold: str
    normalization_logic: str
    provenance: str = "CONFIGURED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResilienceDimensions:
    """
    The 9 observable resilience dimensions and explainable composite index.
    """
    energy_adequacy: DimensionScore
    critical_load_resilience: DimensionScore
    thermal_resilience: DimensionScore
    generation_resilience: DimensionScore
    storage_resilience: DimensionScore
    fuel_resilience: DimensionScore
    logistics_resilience: DimensionScore
    renewable_resilience: DimensionScore
    recovery_resilience: DimensionScore
    composite_resilience_index: float  # [0.0, 100.0] engineering index
    provenance: str = "CONFIGURED"

    @property
    def energy_adequacy_score(self) -> float:
        return self.energy_adequacy.normalized_score

    @property
    def critical_load_resilience_score(self) -> float:
        return self.critical_load_resilience.normalized_score

    @property
    def thermal_resilience_score(self) -> float:
        return self.thermal_resilience.normalized_score

    @property
    def generation_resilience_score(self) -> float:
        return self.generation_resilience.normalized_score

    @property
    def storage_resilience_score(self) -> float:
        return self.storage_resilience.normalized_score

    @property
    def fuel_resilience_score(self) -> float:
        return self.fuel_resilience.normalized_score

    @property
    def logistics_resilience_score(self) -> float:
        return self.logistics_resilience.normalized_score

    @property
    def renewable_resilience_score(self) -> float:
        return self.renewable_resilience.normalized_score

    @property
    def recovery_resilience_score(self) -> float:
        return self.recovery_resilience.normalized_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "energy_adequacy": self.energy_adequacy.to_dict(),
            "critical_load_resilience": self.critical_load_resilience.to_dict(),
            "thermal_resilience": self.thermal_resilience.to_dict(),
            "generation_resilience": self.generation_resilience.to_dict(),
            "storage_resilience": self.storage_resilience.to_dict(),
            "fuel_resilience": self.fuel_resilience.to_dict(),
            "logistics_resilience": self.logistics_resilience.to_dict(),
            "renewable_resilience": self.renewable_resilience.to_dict(),
            "recovery_resilience": self.recovery_resilience.to_dict(),
            "composite_resilience_index": self.composite_resilience_index,
            "provenance": self.provenance
        }


@dataclass
class FailurePropagationStep:
    """Traceable causal transition step within an observed failure chain."""
    step_number: int
    timestamp: str
    trigger: str
    affected_subsystem: str
    observed_state_change: str
    severity: FailureSeverityEnum
    resulting_constraint: str
    possible_recovery_opportunity: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class CandidateRecoveryOption:
    """
    Advisory mitigation / recovery intervention.
    Does NOT execute policy. Provides predicted or physically validated gains.
    """
    action_type: RecoveryActionTypeEnum
    description: str
    target_subsystem: str
    rationale: str
    expected_survival_horizon_gain_h: float
    expected_reserve_margin_gain_pct: float
    urgency: FailureSeverityEnum
    validation_tier: Literal["PHYSICALLY_VALIDATED", "ESTIMATED"] = "ESTIMATED"
    limitations: str = "Advisory recommendation only; policy engine execution reserved for Phase 8"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["action_type"] = self.action_type.value
        d["urgency"] = self.urgency.value
        return d


@dataclass
class ResilienceAssessment:
    """Master output contract of the Polaris-EMS Phase 7 Resilience Engine."""
    station_id: str
    assessment_timestamp: str
    horizon_hours: int
    assessment_status: AssessmentStatusEnum
    resilience_state: ResilienceStateEnum
    active_threat_states: List[ResilienceStateEnum]
    survival_horizons: SurvivalHorizons
    time_to_threat: TimeToThreat
    threat_decomposition: List[ThreatIndicator]
    dimensions: Optional[ResilienceDimensions] = None
    failure_propagation: List[FailurePropagationStep] = field(default_factory=list)
    candidate_recovery_options: List[CandidateRecoveryOption] = field(default_factory=list)
    previous_resilience_state: Optional[ResilienceStateEnum] = None
    recovery_direction: Optional[str] = None
    scenario_id: Optional[str] = None
    scenario_lineage: Optional[Dict[str, Any]] = None
    provenance: str = "SIMULATED"
    diagnostics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "station_id": self.station_id,
            "assessment_timestamp": self.assessment_timestamp,
            "horizon_hours": self.horizon_hours,
            "assessment_status": self.assessment_status.value,
            "resilience_state": self.resilience_state.value,
            "active_threat_states": [s.value for s in self.active_threat_states],
            "previous_resilience_state": self.previous_resilience_state.value if self.previous_resilience_state else None,
            "recovery_direction": self.recovery_direction,
            "survival_horizons": self.survival_horizons.to_dict() if self.survival_horizons else None,
            "time_to_threat": self.time_to_threat.to_dict() if self.time_to_threat else None,
            "threat_decomposition": [t.to_dict() for t in self.threat_decomposition],
            "dimensions": self.dimensions.to_dict() if self.dimensions else None,
            "failure_propagation": [f.to_dict() for f in self.failure_propagation],
            "candidate_recovery_options": [c.to_dict() for c in self.candidate_recovery_options],
            "scenario_id": self.scenario_id,
            "scenario_lineage": self.scenario_lineage,
            "provenance": self.provenance,
            "diagnostics": self.diagnostics
        }


@dataclass
class CounterfactualResilienceComparison:
    """Factual comparative analysis between two resilience trajectories."""
    comparison_name: str
    baseline_assessment: ResilienceAssessment
    counterfactual_assessment: ResilienceAssessment
    delta_overall_survival_horizon_h: float
    delta_critical_load_survival_h: float
    delta_composite_index: float
    delta_min_reserve_margin_pct: float
    delta_fuel_endurance_h: float
    delta_battery_throughput_kwh: float  # Wear-proxy delta
    critical_load_exposure_eliminated_kwh: float
    thermal_exposure_eliminated_degree_h: float
    time_to_critical_delay_h: float
    summary_narrative: str
    provenance: str = "SIMULATED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_name": self.comparison_name,
            "baseline_assessment": self.baseline_assessment.to_dict(),
            "counterfactual_assessment": self.counterfactual_assessment.to_dict(),
            "delta_overall_survival_horizon_h": self.delta_overall_survival_horizon_h,
            "delta_critical_load_survival_h": self.delta_critical_load_survival_h,
            "delta_composite_index": self.delta_composite_index,
            "delta_min_reserve_margin_pct": self.delta_min_reserve_margin_pct,
            "delta_fuel_endurance_h": self.delta_fuel_endurance_h,
            "delta_battery_throughput_kwh": self.delta_battery_throughput_kwh,
            "critical_load_exposure_eliminated_kwh": self.critical_load_exposure_eliminated_kwh,
            "thermal_exposure_eliminated_degree_h": self.thermal_exposure_eliminated_degree_h,
            "time_to_critical_delay_h": self.time_to_critical_delay_h,
            "summary_narrative": self.summary_narrative,
            "provenance": self.provenance
        }
