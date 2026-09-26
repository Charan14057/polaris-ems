"""
POLARIS-EMS — Digital Twin API Adapter
SIH26061: Polar Energy Management & Resilience System

Adapter layer exposing the authoritative Phase 4 TwinEngine and spatial configurations.
Zero duplicated physics: delegates all state calculations to TwinEngine and ScenarioEngine.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.twin_engine import TwinEngine, TwinTrajectory
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.scenarios.registry import ScenarioRegistry
from backend.scenarios.engine import ScenarioEngine
from backend.api.schemas.twin import (
    TwinSpatialProfileSchema,
    TwinTrajectoryRequestSchema,
    TwinTrajectoryResponseData
)
from backend.api.errors import StationNotFoundException, ScenarioNotFoundException, InvalidRequestException


class TwinAPIAdapter:
    """Read-only adapter for Digital Twin spatial profiles and forward simulation trajectories."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        profile_registry: Optional[StationProfileRegistry] = None,
        safety_registry: Optional[SafetyThresholdRegistry] = None,
        scenario_registry: Optional[ScenarioRegistry] = None
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.config_path = config_path or (base_dir / "configs" / "station_spatial_profiles.json")
        self.profile_registry = profile_registry or StationProfileRegistry()
        self.safety_registry = safety_registry or SafetyThresholdRegistry()
        self.scenario_registry = scenario_registry or ScenarioRegistry()

    def get_spatial_profile(self, station_id: str) -> Dict[str, Any]:
        """Loads and returns spatial layout profile for a given station."""
        sid = station_id.upper()
        if not self.config_path.exists():
            raise FileNotFoundError(f"Spatial profiles configuration not found at {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            profiles = json.load(f)

        if sid not in profiles:
            raise StationNotFoundException(f"Spatial profile for station '{sid}' not found.")

        return profiles[sid]

    def get_current_state(self, station_id: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Initializes and returns instantaneous TwinState for a station."""
        sid = station_id.upper()
        ts = timestamp or "2026-06-01T12:00:00Z"
        profile = self.profile_registry.get(sid)
        engine = TwinEngine(station_id=sid, profile=profile, safety_registry=self.safety_registry)

        state: TwinState = engine.initialize_twin(timestamp=ts)
        return state.to_dict()

    def simulate_trajectory(
        self,
        req: TwinTrajectoryRequestSchema
    ) -> TwinTrajectoryResponseData:
        """
        Executes a multi-timestep forward simulation trajectory using the authoritative TwinEngine.
        If scenario_id is provided, runs scenario-perturbed trajectory.
        """
        sid = req.station_id.upper()
        horizon_h = req.horizon_hours or 24
        mode = req.mode or "EXPECTED"
        start_ts = req.start_timestamp or "2026-06-01T00:00:00Z"

        profile = self.profile_registry.get(sid)
        engine = TwinEngine(station_id=sid, profile=profile, safety_registry=self.safety_registry)
        initial_state: TwinState = engine.initialize_twin(timestamp=start_ts)

        # Build baseline driving steps
        driving_steps: List[TwinInputStep] = []
        is_polar_day = (sid == "HIMADRI")  # High Arctic summer polar day in June
        for h in range(1, horizon_h + 1):
            day = 1 + (h - 1) // 24
            hour = (h - 1) % 24
            ts = f"2026-06-{day:02d}T{hour:02d}:00:00Z"

            # Realistic solar diurnal cycle (or polar night/day)
            if is_polar_day:
                ghi = 150.0 + 80.0 * max(0.0, -((hour - 12) / 6.0) ** 2 + 1)
            else:
                ghi = 220.0 * max(0.0, 1.0 - abs(hour - 12) / 6.0) if 6 <= hour <= 18 else 0.0

            # Wind diurnal pattern with realistic variability
            wind_spd = 9.0 + 3.5 * ((hour % 8) / 8.0 - 0.5)

            # Load pattern peaking around galley and meal times
            base_load = float(profile.devices[0].nominal_power_kw * 1.5)
            load_factor = 1.25 if (hour in [7, 8, 12, 13, 19, 20]) else (0.85 if 0 <= hour <= 5 else 1.0)
            target_load = round(base_load * load_factor, 1)

            # Renewable estimations
            solar_kw = round((ghi / 1000.0) * profile.electrical.solar_pv_kw_peak * profile.electrical.solar_efficiency * 4.0, 1)
            wind_ratio = max(0.0, min(1.0, (wind_spd - profile.electrical.wind_cut_in_speed_ms) / (profile.electrical.wind_rated_speed_ms - profile.electrical.wind_cut_in_speed_ms)))
            wind_kw = round(profile.electrical.wind_turbine_kw_rated * wind_ratio, 1)

            driving_steps.append(TwinInputStep(
                timestamp=ts,
                horizon_h=h,
                ambient_temp_c=-22.0 if sid != "HIMADRI" else -5.0,
                wind_speed_m_per_s=round(wind_spd, 1),
                ghi_w_per_m2=round(ghi, 1),
                load_kw=target_load,
                solar_kw=solar_kw,
                wind_kw=wind_kw,
                mode=mode,
                provenance="FORECAST"
            ))

        # Check if scenario perturbation is requested
        if req.scenario_id:
            scen_id = req.scenario_id.upper()
            try:
                scen_engine = ScenarioEngine(
                    station_id=sid,
                    profile=profile,
                    safety_registry=self.safety_registry,
                    scenario_registry=self.scenario_registry
                )
                scen_res = scen_engine.run_scenario(
                    scenario_id=scen_id,
                    initial_state=initial_state,
                    baseline_inputs=driving_steps,
                    forecast_mode=mode,
                    horizon_hours=horizon_h
                )
                # Scenario execution generates baseline and perturbed trajectories
                # Use the perturbed scenario state sequence
                trajectory = scen_res.scenario_trajectory
                # Attach scenario summary indicators
                summary = trajectory.summary
                summary["scenario_id"] = scen_id
                summary["scenario_failure"] = (scen_res.impact_metrics.scenario_failure_time_h is not None)
                summary["impact_metrics"] = {
                    "delta_unserved_energy_kwh": scen_res.impact_metrics.delta_unserved_energy_kwh,
                    "delta_fuel_burn_liters": scen_res.impact_metrics.delta_fuel_burn_liters,
                    "primary_failure_signature": scen_res.impact_metrics.primary_failure_signature
                }
            except KeyError:
                raise ScenarioNotFoundException(scen_id)
        else:
            trajectory = engine.simulate(initial_state=initial_state, trajectory_steps=driving_steps)

        return TwinTrajectoryResponseData(
            station_id=trajectory.station_id,
            mode=trajectory.mode,
            steps_count=len(trajectory.states),
            duration_hours=len(trajectory.states) * 1.0,
            states=[s.to_dict() for s in trajectory.states],
            summary=trajectory.summary,
            provenance="SIMULATED"
        )


twin_adapter = TwinAPIAdapter()

