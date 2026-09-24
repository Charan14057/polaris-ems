"""
POLARIS-EMS — Scenario API Adapter
SIH26061: Polar Energy Management & Resilience System

Translates API requests into calls to Phase 5 ScenarioRegistry and ScenarioEngine.
Executes scenario transformations and compares baseline vs scenario trajectories through Digital Twin replay.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.scenarios.registry import ScenarioRegistry
from backend.scenarios.engine import ScenarioEngine
from backend.scenarios.schema import ScenarioDefinition, ScenarioResult
from backend.twin.twin_engine import TwinEngine
from backend.twin.forecast_adapter import TwinInputStep
from backend.twin.state import TwinState
from backend.api.schemas.scenario import (
    ScenarioSummarySchema,
    ScenarioDetailSchema,
    ParameterTransformSchema,
    ScenarioEvaluateRequestSchema,
    ScenarioEvaluateResponseData,
    ScenarioImpactMetricsSchema
)
from backend.api.errors import ScenarioNotFoundException, InvalidRequestException


class ScenarioAPIAdapter:
    """Adapts Phase 5 Scenario catalog and stress execution engine."""

    def __init__(self, scenario_registry: Optional[ScenarioRegistry] = None):
        self.registry = scenario_registry or ScenarioRegistry()

    def list_scenarios(self) -> List[ScenarioSummarySchema]:
        """Returns summaries of all 14 locked polar stress scenarios."""
        scenarios = self.registry.list_scenarios()
        return [
            ScenarioSummarySchema(
                scenario_id=s.scenario_id,
                name=s.name,
                description=s.description,
                category=s.category.value if hasattr(s.category, "value") else str(s.category),
                duration_hours=s.duration_hours,
                active_effects=s.active_effects,
                provenance=s.provenance
            )
            for s in scenarios
        ]

    def get_scenario(self, scenario_id: str) -> ScenarioDetailSchema:
        """Retrieves complete scenario definition with explicit parameter transforms."""
        sid = scenario_id.upper()
        try:
            s = self.registry.get(sid)
        except KeyError:
            raise ScenarioNotFoundException(scenario_id)

        return ScenarioDetailSchema(
            scenario_id=s.scenario_id,
            name=s.name,
            description=s.description,
            category=s.category.value if hasattr(s.category, "value") else str(s.category),
            duration_hours=s.duration_hours,
            active_effects=s.active_effects,
            provenance=s.provenance,
            rationale=s.rationale,
            transforms=[
                ParameterTransformSchema(
                    parameter=t.parameter,
                    operator=t.operator.value if hasattr(t.operator, "value") else str(t.operator),
                    value=t.value,
                    unit=t.unit,
                    rationale=t.rationale
                )
                for t in s.transforms
            ]
        )

    def evaluate_scenario(
        self,
        req: ScenarioEvaluateRequestSchema,
        engine: ScenarioEngine,
        twin: TwinEngine
    ) -> ScenarioEvaluateResponseData:
        """Executes scenario stress test through Twin replay."""
        sid = req.station_id.upper()
        scen_id = req.scenario_id.upper()
        horizon_h = req.horizon_hours or 48
        start_ts = req.start_timestamp or "2026-06-01T00:00:00Z"

        # 1. Initialize Authoritative Initial State from Twin
        initial_state: TwinState = twin.initialize_twin(start_ts)

        # 2. Build Driving Baseline Steps
        baseline_steps = []
        for h in range(1, horizon_h + 1):
            day = 1 + (h - 1) // 24
            hour = (h - 1) % 24
            # Nominal standard polar daytime / conditions
            ghi = 200.0 if (6 <= hour <= 18) else 0.0
            baseline_steps.append(TwinInputStep(
                timestamp=f"2026-06-{day:02d}T{hour:02d}:00:00Z",
                horizon_h=h,
                ambient_temp_c=-20.0,
                wind_speed_m_per_s=10.0,
                ghi_w_per_m2=ghi,
                load_kw=45.0,
                solar_kw=15.0 if ghi > 0 else 0.0,
                wind_kw=25.0,
                mode=req.forecast_mode
            ))

        # 3. Execute Scenario Run
        try:
            res: ScenarioResult = engine.run_scenario(
                scenario_id=scen_id,
                initial_state=initial_state,
                baseline_inputs=baseline_steps,
                forecast_mode=req.forecast_mode,
                horizon_hours=horizon_h
            )
        except KeyError:
            raise ScenarioNotFoundException(scen_id)
        except Exception as e:
            raise InvalidRequestException(f"Scenario execution failed: {str(e)}")

        scen_def = self.registry.get(scen_id)
        cat_val = scen_def.category.value if hasattr(scen_def.category, "value") else str(scen_def.category)
        impact = ScenarioImpactMetricsSchema(
            delta_unserved_energy_kwh=res.impact_metrics.delta_unserved_energy_kwh,
            delta_critical_unserved_kwh=res.impact_metrics.delta_critical_unserved_energy_kwh,
            delta_diesel_fuel_liters=res.impact_metrics.delta_fuel_burn_liters,
            delta_min_indoor_temp_c=res.impact_metrics.delta_min_indoor_temperature_c,
            delta_min_battery_soc=res.impact_metrics.delta_min_battery_soc,
            primary_failure_mode=res.impact_metrics.primary_failure_signature,
            earliest_failure_hour=float(res.impact_metrics.scenario_failure_time_h) if res.impact_metrics.scenario_failure_time_h is not None else None,
            failure_occurred=(res.impact_metrics.scenario_failure_time_h is not None or len(res.constraints_violated) > 0)
        )

        return ScenarioEvaluateResponseData(
            scenario_id=res.scenario_id,
            station_id=res.station_id,
            category=cat_val,
            duration_hours=res.duration_hours,
            impact_metrics=impact,
            violated_constraints=list(res.constraints_violated),
            failure_indicators=[res.primary_failure_signature] if res.primary_failure_signature else [],
            baseline_trajectory_summary=res.baseline_summary,
            scenario_trajectory_summary=res.scenario_summary,
            trajectory_states=None,  # controlled response size
            provenance="SIMULATED"
        )
