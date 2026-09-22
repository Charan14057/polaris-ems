"""
POLARIS-EMS — Digital Twin Solar Subsystem Engine
SIH26061: Polar Energy Management & Resilience System

Simulates solar PV generation with cell temperature derating and astronomical constraints:
- Zero generation during polar night and astronomical night (solar_elevation <= 0)
- Clamped above by station-specific PV peak capacity from StationProfile
- Supports Phase 3 solar forecast integration
"""

from typing import Optional
from backend.twin.state import SolarState
from backend.data.station_profiles.loader import StationProfile


class SolarEngine:
    """Manages solar PV potential, physical capacity bounds, and generation status."""

    def __init__(self, profile: StationProfile):
        self.profile = profile
        self.pv_spec = profile.electrical

    def step(
        self,
        irradiance_wm2: float,
        ambient_temp_c: float,
        solar_elevation_deg: float,
        curtailed_kw: float = 0.0,
        forecast_solar_kw: Optional[float] = None
    ) -> SolarState:
        """
        Computes solar generation state for the current timestep.
        """
        cap_kw = float(self.pv_spec.solar_pv_kw_peak)

        # Astronomical night or zero irradiance condition
        if solar_elevation_deg <= 0.0 or irradiance_wm2 <= 0.0:
            return SolarState(
                solar_available_kw=0.0,
                solar_generation_kw=0.0,
                solar_curtailed_kw=0.0,
                solar_capacity_kw=cap_kw,
                solar_status="NIGHT",
                provenance="SIMULATED"
            )

        if forecast_solar_kw is not None:
            available_kw = float(min(cap_kw, max(0.0, forecast_solar_kw)))
        else:
            # Physical cell temperature derating calculation
            t_cell = ambient_temp_c + (irradiance_wm2 / 800.0) * 25.0
            temp_derate = 1.0 + (self.pv_spec.solar_temp_coeff_pct / 100.0) * (t_cell - 25.0)
            temp_derate = max(0.65, min(1.25, temp_derate))

            potential_kw = cap_kw * (irradiance_wm2 / 1000.0) * temp_derate
            available_kw = float(min(cap_kw, max(0.0, potential_kw)))

        actual_gen_kw = float(max(0.0, available_kw - curtailed_kw))
        status = "CURTAILED" if curtailed_kw > 0.01 else "ONLINE"

        return SolarState(
            solar_available_kw=round(available_kw, 2),
            solar_generation_kw=round(actual_gen_kw, 2),
            solar_curtailed_kw=round(curtailed_kw, 2),
            solar_capacity_kw=cap_kw,
            solar_status=status,
            provenance="SIMULATED"
        )
