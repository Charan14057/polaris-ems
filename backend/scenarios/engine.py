"""
POLARIS-EMS — Scenario Orchestration Engine
SIH26061: Polar Energy Management & Resilience System

The authoritative orchestration layer for multi-horizon polar stress testing:
Predict (Phase 3 ML) -> Simulate (Phase 4 Twin) -> Stress Test (Phase 5 Scenarios) -> Optimize (Phase 6)

Guarantees:
- Pure orchestration reusing Phase 4 TwinEngine without duplicating physical equations.
- Baseline/scenario isolation: baseline run remains completely unchanged.
- Multi-horizon support (1h, 6h, 12h, 24h, 48h, 168h).
- Deterministic stress trajectory modes (EXPECTED, CONSERVATIVE, OPTIMISTIC).
- Full input lineage retention (Correction #3).
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import pandas as pd
import copy

from backend.scenarios.schema import (
    ScenarioDefinition,
    ParameterTransform,
    TransformOperator,
    ScenarioCategory,
    ScenarioResult,
    ScenarioImpactMetrics
)
from backend.scenarios.registry import ScenarioRegistry
from backend.scenarios.validator import ScenarioValidator, ScenarioValidationError
from backend.scenarios.transformations import ScenarioTransformer
from backend.scenarios.comparator import ScenarioComparator

from backend.twin.twin_engine import TwinEngine, TwinTrajectory
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.data.station_profiles.loader import StationProfileRegistry, StationProfile
from backend.twin.safety_thresholds import SafetyThresholdRegistry


class ScenarioEngine:
    """Orchestrates scenario transformations, baseline vs scenario execution, and impact analysis."""

    def __init__(
        self,
        station_id: str,
        profile: Optional[StationProfile] = None,
        safety_registry: Optional[SafetyThresholdRegistry] = None,
        scenario_registry: Optional[ScenarioRegistry] = None
    ):
        self.station_id = station_id.upper()
        self.scenario_registry = scenario_registry or ScenarioRegistry()
        self.validator = ScenarioValidator()

        # Instantiate authoritative Phase 4 Digital Twin
        self.twin = TwinEngine(
            station_id=self.station_id,
            profile=profile,
            safety_registry=safety_registry
        )

    def run_scenario(
        self,
        scenario_id: str,
        initial_state: TwinState,
        baseline_inputs: List[TwinInputStep],
        forecast_mode: str = "EXPECTED",
        horizon_hours: Optional[int] = None,
        custom_overrides: Optional[Dict[str, Any]] = None
    ) -> ScenarioResult:
        """
        Executes a scenario stress test against the baseline trajectory.

        Args:
            scenario_id: One of the 14 locked scenario IDs or "CUSTOM"
            initial_state: Authoritative initial TwinState (observed/configured)
            baseline_inputs: Driving input steps from Phase 3 forecast / weather
            forecast_mode: "EXPECTED" | "CONSERVATIVE" | "OPTIMISTIC"
            horizon_hours: Optional horizon lead time in hours (1h, 6h, 12h, 24h, 48h, 168h)
            custom_overrides: Optional parameter overrides for custom scenarios
        """
        sid = scenario_id.upper()

        # 1. Retrieve or Build Scenario Definition
        if sid == "CUSTOM" or custom_overrides:
            scenario = self._build_custom_scenario(custom_overrides or {})
        else:
            scenario = copy.deepcopy(self.scenario_registry.get(sid))

        # 2. Validate Scenario
        self.validator.validate_scenario(scenario)

        # 3. Restrict Horizon if Specified
        h_limit = horizon_hours or scenario.duration_hours or len(baseline_inputs)
        b_inputs = baseline_inputs[:h_limit]

        # 4. Execute Baseline Simulation through Twin
        baseline_trajectory = self.twin.simulate(
            initial_state=initial_state,
            trajectory_steps=b_inputs,
            dt_hours=1.0
        )

        # 5. Execute Scenario Transformations (Weather, Load, Assets, Resupply)
        transformer = ScenarioTransformer(scenario)
        t_state, t_inputs = transformer.transform(initial_state, b_inputs)

        # 6. Execute Scenario Simulation through Twin
        scenario_trajectory = self.twin.simulate(
            initial_state=t_state,
            trajectory_steps=t_inputs,
            dt_hours=1.0
        )

        # 7. Compare Trajectories and Detect Deterministic Failure Signatures
        impact_metrics = ScenarioComparator.compare(baseline_trajectory, scenario_trajectory)

        # 8. Extract Violated Constraints from Scenario Trajectory
        all_violated = set()
        for st in scenario_trajectory.states:
            for c in st.constraints:
                if c.status == "VIOLATED":
                    all_violated.add(c.constraint_name)

        # 9. Resilience Status
        final_state = scenario_trajectory.states[-1] if scenario_trajectory.states else initial_state
        resilience_status = {
            "critical_survival": scenario_trajectory.summary.get("critical_survival", "UNKNOWN"),
            "threat_state": final_state.resilience.threat_state if final_state.resilience else "UNKNOWN",
            "dependable_reserve_pct": final_state.resilience.dependable_reserve_pct if final_state.resilience else 0.0,
            "continuity_horizon_hours": final_state.resilience.continuity_horizon_hours if final_state.resilience else 0.0,
            "threat_distribution": scenario_trajectory.summary.get("threat_state_distribution", {})
        }

        # 10. Assemble and Return Authoritative ScenarioResult Contract
        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            station_id=self.station_id,
            scenario_name=scenario.name,
            start_time=initial_state.timestamp,
            duration_hours=len(b_inputs),
            forecast_mode=forecast_mode,
            baseline_trajectory=baseline_trajectory,
            scenario_trajectory=scenario_trajectory,
            original_forecast=b_inputs,
            scenario_transforms=scenario.transforms,
            effective_simulation_inputs=t_inputs,
            baseline_summary=baseline_trajectory.summary,
            scenario_summary=scenario_trajectory.summary,
            impact_metrics=impact_metrics,
            primary_failure_signature=impact_metrics.primary_failure_signature,
            secondary_failure_signatures=impact_metrics.secondary_failure_signatures,
            constraints_violated=sorted(list(all_violated)),
            resilience_status=resilience_status,
            provenance="SIMULATED"
        )

    def _build_custom_scenario(self, overrides: Dict[str, Any]) -> ScenarioDefinition:
        """Synthesizes a typed ScenarioDefinition from user overrides."""
        clean_overrides = copy.deepcopy(overrides)
        dur_hours = int(clean_overrides.pop("duration_hours", 48))
        self.validator.validate_custom_overrides(clean_overrides)
        transforms: List[ParameterTransform] = []

        for param, val in clean_overrides.items():
            if param in ["ambient_temperature_c", "battery_initial_soc_delta"]:
                op = TransformOperator.ADD
            elif param in ["solar_availability", "wind_availability", "generator_availability"]:
                if val == 0 or val == 0.0:
                    op = TransformOperator.DISABLE
                else:
                    op = TransformOperator.MULTIPLY
            elif param in ["cloud_fraction", "irradiance_wm2", "wind_speed_ms", "load_multiplier", "battery_capacity"]:
                op = TransformOperator.MULTIPLY
            elif param == "fuel_resupply_delay_hours":
                op = TransformOperator.DELAY
            else:
                op = TransformOperator.SET

            transforms.append(ParameterTransform(
                parameter=param,
                operator=op,
                value=val,
                unit="",
                rationale="User-defined custom stress override"
            ))

        return ScenarioDefinition(
            scenario_id="CUSTOM",
            name="Custom User Scenario",
            description="User-defined scenario synthesized from validated parameter overrides.",
            category=ScenarioCategory.CUSTOM,
            duration_hours=dur_hours,
            transforms=transforms,
            active_effects=list(clean_overrides.keys()),
            provenance="CONFIGURED",
            rationale="Exploratory user what-if test."
        )

    def build_resilience_envelope(
        self,
        scenario_id: str,
        initial_state: TwinState,
        forecast_inputs: Dict[str, List[TwinInputStep]],
        horizon_hours: int = 48
    ) -> Dict[str, ScenarioResult]:
        """
        Runs a scenario under EXPECTED, CONSERVATIVE, and OPTIMISTIC driving inputs,
        separating forecast uncertainty from scenario stress.
        """
        envelope = {}
        for mode in ["EXPECTED", "CONSERVATIVE", "OPTIMISTIC"]:
            if mode in forecast_inputs:
                res = self.run_scenario(
                    scenario_id=scenario_id,
                    initial_state=initial_state,
                    baseline_inputs=forecast_inputs[mode],
                    forecast_mode=mode,
                    horizon_hours=horizon_hours
                )
                envelope[mode] = res
        return envelope
