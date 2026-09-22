"""
POLARIS-EMS — Digital Twin Wind Subsystem Engine
SIH26061: Polar Energy Management & Resilience System

Simulates wind turbine power using the station-specific aerodynamic power curve:
- Zero generation below cut-in speed (BELOW_CUT_IN)
- Cubic power ramp between cut-in and rated speed (OPERATING_RAMP)
- Constant rated power between rated and storm cut-out speed (OPERATING_RATED)
- Zero generation above storm cut-out speed to protect turbine blades (STORM_CUT_OUT)
- Supports Phase 3 wind forecast integration
"""

from typing import Optional
from backend.twin.state import WindState
from backend.data.station_profiles.loader import StationProfile


class WindEngine:
    """Manages wind turbine power curve, aerodynamic states, and curtailment."""

    def __init__(self, profile: StationProfile):
        self.profile = profile
        self.w_spec = profile.electrical

    def step(
        self,
        wind_speed_ms: float,
        curtailed_kw: float = 0.0,
        forecast_wind_kw: Optional[float] = None
    ) -> WindState:
        """
        Computes wind turbine generation state for the current timestep.
        """
        v_in = float(self.w_spec.wind_cut_in_speed_ms)
        v_rat = float(self.w_spec.wind_rated_speed_ms)
        v_out = float(self.w_spec.wind_cut_out_speed_ms)
        p_rat = float(self.w_spec.wind_turbine_kw_rated)

        if wind_speed_ms < v_in:
            available_kw = 0.0
            status = "BELOW_CUT_IN"
        elif v_in <= wind_speed_ms < v_rat:
            cubic_factor = (wind_speed_ms**3 - v_in**3) / max(1.0, (v_rat**3 - v_in**3))
            available_kw = float(min(p_rat, max(0.0, p_rat * cubic_factor)))
            status = "OPERATING_RAMP"
        elif v_rat <= wind_speed_ms < v_out:
            available_kw = p_rat
            status = "OPERATING_RATED"
        else:
            # Blizzard storm cut-out
            available_kw = 0.0
            status = "STORM_CUT_OUT"

        if forecast_wind_kw is not None:
            # If forecast provided, apply aerodynamic cut-in/cut-out safety boundaries
            if status in ["BELOW_CUT_IN", "STORM_CUT_OUT"]:
                available_kw = 0.0
            else:
                available_kw = float(min(p_rat, max(0.0, forecast_wind_kw)))

        actual_gen_kw = float(max(0.0, available_kw - curtailed_kw))
        if curtailed_kw > 0.01:
            status = f"{status}_CURTAILED"

        return WindState(
            wind_available_kw=round(available_kw, 2),
            wind_generation_kw=round(actual_gen_kw, 2),
            wind_curtailed_kw=round(curtailed_kw, 2),
            wind_capacity_kw=p_rat,
            wind_status=status,
            provenance="SIMULATED"
        )
