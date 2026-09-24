"""
POLARIS-EMS — Resilience API Adapter
SIH26061: Polar Energy Management & Resilience System

Translates API requests into calls to the Phase 7 ResilienceEngine.
Evaluates multi-horizon survivability, 9 resilience dimensions, composite index,
threat decomposition, and candidate recovery options without recalculating physics in routes.
"""

from typing import Optional, List, Dict, Any

from backend.resilience.engine import ResilienceEngine
from backend.resilience.schema import ResilienceAssessment
from backend.scenarios.registry import ScenarioRegistry
from backend.twin.twin_engine import TwinEngine
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.api.schemas.resilience import (
    ResilienceEvaluateRequestSchema,
    ResilienceEvaluateResponseData,
    SurvivalHorizonsSchema,
    ResilienceDimensionsSchema,
    ThreatIndicatorSchema,
    CandidateRecoveryOptionSchema
)
from backend.api.errors import InvalidRequestException, ScenarioNotFoundException


class ResilienceAPIAdapter:
    """Adapts Phase 7 ResilienceEngine to API presentation schemas."""

    def __init__(self, scenario_registry: Optional[ScenarioRegistry] = None):
        self.scenario_registry = scenario_registry or ScenarioRegistry()

    def evaluate_resilience(
        self,
        req: ResilienceEvaluateRequestSchema,
        resilience_engine: ResilienceEngine,
        twin: TwinEngine
    ) -> ResilienceEvaluateResponseData:
        """Executes resilience assessment on simulated Twin trajectory."""
        sid = req.station_id.upper()
        horizon_h = req.horizon_hours
        start_ts = req.start_timestamp or "2026-06-01T00:00:00Z"

        # 1. Initialize Authoritative Initial State from Twin
        initial_state: TwinState = twin.initialize_twin(start_ts)

        # 2. Resolve Scenario if requested
        scenario_def = None
        if req.scenario_id:
            try:
                scenario_def = self.scenario_registry.get(req.scenario_id.upper())
            except KeyError:
                raise ScenarioNotFoundException(req.scenario_id)

        # 3. Build Driving Baseline Steps
        trajectory_steps = []
        for h in range(1, horizon_h + 1):
            day = 1 + (h - 1) // 24
            hour = (h - 1) % 24
            ghi = 200.0 if (6 <= hour <= 18) else 0.0
            trajectory_steps.append(TwinInputStep(
                timestamp=f"2026-06-{day:02d}T{hour:02d}:00:00Z",
                horizon_h=h,
                ambient_temp_c=-20.0,
                wind_speed_m_per_s=10.0,
                ghi_w_per_m2=ghi,
                load_kw=45.0,
                solar_kw=15.0 if ghi > 0 else 0.0,
                wind_kw=25.0,
                mode="EXPECTED"
            ))

        # 4. Simulate Baseline Trajectory through Twin
        trajectory = twin.simulate(initial_state, trajectory_steps)

        # 5. Assess Trajectory Resilience
        try:
            assessment: ResilienceAssessment = resilience_engine.assess_trajectory(
                trajectory=trajectory,
                scenario=scenario_def
            )
        except Exception as e:
            raise InvalidRequestException(f"Resilience assessment failed: {str(e)}")

        return self.to_schema(assessment, include_propagation=req.include_propagation)

    @staticmethod
    def to_schema(assessment: ResilienceAssessment, include_propagation: bool = False) -> ResilienceEvaluateResponseData:
        """Converts ResilienceAssessment domain dataclass into API response schema."""
        sh = assessment.survival_horizons
        surv_schema = SurvivalHorizonsSchema(
            overall_station_survival_horizon_h=sh.overall_station_survival_horizon_h,
            battery_endurance_horizon_h=sh.battery_endurance_horizon_h,
            thermal_habitability_horizon_h=sh.thermal_habitability_horizon_h,
            fuel_endurance_horizon_h=sh.fuel_endurance_horizon_h,
            critical_load_survival_horizon_h=sh.critical_load_survival_horizon_h,
            resupply_gap_survivability_h=sh.resupply_gap_survivability_h,
            dependable_generation_horizon_h=getattr(sh, "dependable_generation_horizon_h", 0.0),
            binding_subsystem=sh.binding_subsystem,
            survives_full_horizon=sh.survives_full_horizon
        )

        dim_schema = None
        if assessment.dimensions:
            d = assessment.dimensions
            # Normalized score [0, 1] for composite_index
            comp_idx_norm = round(d.composite_resilience_index / 100.0, 4) if d.composite_resilience_index > 1.0 else round(d.composite_resilience_index, 4)
            dim_schema = ResilienceDimensionsSchema(
                energy_adequacy=round(d.energy_adequacy.normalized_score, 2),
                critical_load_resilience=round(d.critical_load_resilience.normalized_score, 2),
                thermal_resilience=round(d.thermal_resilience.normalized_score, 2),
                generation_resilience=round(d.generation_resilience.normalized_score, 2),
                storage_resilience=round(d.storage_resilience.normalized_score, 2),
                fuel_resilience=round(d.fuel_resilience.normalized_score, 2),
                logistics_resilience=round(d.logistics_resilience.normalized_score, 2),
                renewable_resilience=round(d.renewable_resilience.normalized_score, 2),
                recovery_resilience=round(d.recovery_resilience.normalized_score, 2),
                composite_index=comp_idx_norm,
                composite_resilience_index=round(d.composite_resilience_index, 2),
                electrical_autonomy=round(d.energy_adequacy.normalized_score, 2),
                thermal_habitability=round(d.thermal_resilience.normalized_score, 2),
                fuel_endurance=round(d.fuel_resilience.normalized_score, 2),
                renewable_penetration=round(d.renewable_resilience.normalized_score, 2),
                generation_headroom=round(d.generation_resilience.normalized_score, 2),
                storage_health=round(d.storage_resilience.normalized_score, 2),
                operational_margin=round(d.recovery_resilience.normalized_score, 2),
                logistics_buffer=round(d.logistics_resilience.normalized_score, 2),
                mission_continuity=round(d.critical_load_resilience.normalized_score, 2),
                explainable_loss={
                    "energy_adequacy": round(100.0 - d.energy_adequacy.normalized_score, 2),
                    "critical_load": round(100.0 - d.critical_load_resilience.normalized_score, 2),
                    "thermal": round(100.0 - d.thermal_resilience.normalized_score, 2),
                    "generation": round(100.0 - d.generation_resilience.normalized_score, 2),
                    "storage": round(100.0 - d.storage_resilience.normalized_score, 2),
                    "fuel": round(100.0 - d.fuel_resilience.normalized_score, 2),
                    "logistics": round(100.0 - d.logistics_resilience.normalized_score, 2),
                    "renewable": round(100.0 - d.renewable_resilience.normalized_score, 2),
                    "recovery": round(100.0 - d.recovery_resilience.normalized_score, 2)
                }
            )

        threats = [
            ThreatIndicatorSchema(
                threat_type=t.threat_type.value if hasattr(t.threat_type, "value") else str(t.threat_type),
                severity=t.severity.value if hasattr(t.severity, "value") else str(t.severity),
                trigger_condition=t.trigger_condition,
                affected_subsystems=t.affected_subsystems
            )
            for t in assessment.threat_decomposition
        ]

        recovery = [
            CandidateRecoveryOptionSchema(
                action_type=opt.action_type.value if hasattr(opt.action_type, "value") else str(opt.action_type),
                description=opt.description,
                target_subsystem=opt.target_subsystem,
                rationale=opt.rationale,
                expected_survival_horizon_gain_h=opt.expected_survival_horizon_gain_h,
                expected_reserve_margin_gain_pct=opt.expected_reserve_margin_gain_pct,
                urgency=opt.urgency.value if hasattr(opt.urgency, "value") else str(opt.urgency),
                validation_tier=opt.validation_tier,
                limitations=opt.limitations,
                action_id=f"rec-{idx+1}",
                expected_gain_h=opt.expected_survival_horizon_gain_h,
                fuel_penalty_l=0.0,
                advisory_only=True
            )
            for idx, opt in enumerate(assessment.candidate_recovery_options)
        ]

        propagation = None
        if include_propagation and assessment.failure_propagation:
            propagation = [p.to_dict() for p in assessment.failure_propagation]

        return ResilienceEvaluateResponseData(
            station_id=assessment.station_id,
            assessment_timestamp=assessment.assessment_timestamp,
            horizon_hours=assessment.horizon_hours,
            assessment_status=assessment.assessment_status.value if hasattr(assessment.assessment_status, "value") else str(assessment.assessment_status),
            resilience_state=assessment.resilience_state.value if hasattr(assessment.resilience_state, "value") else str(assessment.resilience_state),
            survival_horizons=surv_schema,
            dimensions=dim_schema,
            threat_decomposition=threats,
            candidate_recovery_options=recovery,
            failure_propagation=propagation,
            provenance="SIMULATED"
        )
