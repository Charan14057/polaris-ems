"""
POLARIS-EMS — Polar Disturbance Engine
SIH26061: Polar Energy Management & Resilience System

Implements 10 distinct polar disturbance regimes that causally transform
physical and operational conditions:
- NORMAL
- CLOUD_SURGE
- BLIZZARD
- EXTREME_COLD
- HIGH_WIND
- LOW_WIND
- SOLAR_REDUCTION
- SOLAR_FAILURE
- WIND_FAILURE
- COMBINED_POLAR_STRESS

Disturbances propagate through the causal chain (wind, cloud, temperature, asset availability)
rather than applying arbitrary output multipliers alone.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np


class DisturbanceType(str, Enum):
    NORMAL = "NORMAL"
    CLOUD_SURGE = "CLOUD_SURGE"
    BLIZZARD = "BLIZZARD"
    EXTREME_COLD = "EXTREME_COLD"
    HIGH_WIND = "HIGH_WIND"
    LOW_WIND = "LOW_WIND"
    SOLAR_REDUCTION = "SOLAR_REDUCTION"
    SOLAR_FAILURE = "SOLAR_FAILURE"
    WIND_FAILURE = "WIND_FAILURE"
    COMBINED_POLAR_STRESS = "COMBINED_POLAR_STRESS"


class DisturbanceState:
    """Represents the active disturbance regime and its physical modifier parameters."""

    def __init__(
        self,
        disturbance_type: DisturbanceType = DisturbanceType.NORMAL,
        temp_delta_c: float = 0.0,
        wind_speed_multiplier: float = 1.0,
        wind_gust_delta_ms: float = 0.0,
        cloud_cover_override: Optional[float] = None,
        solar_pv_availability: float = 1.0,
        wind_turbine_availability: float = 1.0,
        heating_demand_multiplier: float = 1.0,
        duration_hours: int = 1,
        remaining_hours: int = 1,
    ):
        self.disturbance_type = disturbance_type
        self.temp_delta_c = temp_delta_c
        self.wind_speed_multiplier = wind_speed_multiplier
        self.wind_gust_delta_ms = wind_gust_delta_ms
        self.cloud_cover_override = cloud_cover_override
        self.solar_pv_availability = solar_pv_availability
        self.wind_turbine_availability = wind_turbine_availability
        self.heating_demand_multiplier = heating_demand_multiplier
        self.duration_hours = duration_hours
        self.remaining_hours = remaining_hours


class PolarDisturbanceGenerator:
    """
    Schedules and manages disturbance regimes across multi-year time series
    using a deterministic random generator.
    """

    def __init__(self, seed: int = 42, station_id: str = "BHARATI"):
        self.seed = seed
        self.station_id = station_id.upper()
        self.rng = np.random.default_rng(seed)
        self.current_state = DisturbanceState(DisturbanceType.NORMAL)

    def _sample_new_disturbance(self, is_winter: bool) -> DisturbanceState:
        """Sample a new disturbance event based on polar seasonal probabilities."""
        # Seasonal probabilities: Blizzards & extreme cold are more frequent during winter
        if is_winter:
            choices = [
                DisturbanceType.NORMAL,
                DisturbanceType.CLOUD_SURGE,
                DisturbanceType.BLIZZARD,
                DisturbanceType.EXTREME_COLD,
                DisturbanceType.HIGH_WIND,
                DisturbanceType.LOW_WIND,
                DisturbanceType.SOLAR_REDUCTION,
                DisturbanceType.SOLAR_FAILURE,
                DisturbanceType.WIND_FAILURE,
                DisturbanceType.COMBINED_POLAR_STRESS,
            ]
            probs = [0.60, 0.08, 0.10, 0.08, 0.05, 0.03, 0.01, 0.01, 0.02, 0.02]
        else:
            choices = [
                DisturbanceType.NORMAL,
                DisturbanceType.CLOUD_SURGE,
                DisturbanceType.BLIZZARD,
                DisturbanceType.EXTREME_COLD,
                DisturbanceType.HIGH_WIND,
                DisturbanceType.LOW_WIND,
                DisturbanceType.SOLAR_REDUCTION,
                DisturbanceType.SOLAR_FAILURE,
                DisturbanceType.WIND_FAILURE,
                DisturbanceType.COMBINED_POLAR_STRESS,
            ]
            probs = [0.72, 0.12, 0.03, 0.02, 0.04, 0.03, 0.02, 0.01, 0.01, 0.00]

        # Normalize probabilities to sum to 1.0 exactly
        probs = np.array(probs) / np.sum(probs)
        choice_idx = int(self.rng.choice(len(choices), p=probs))
        selected_type = choices[choice_idx]

        # Build physical modifiers based on regime
        if selected_type == DisturbanceType.NORMAL:
            duration = int(self.rng.integers(12, 72))
            return DisturbanceState(
                disturbance_type=DisturbanceType.NORMAL,
                duration_hours=duration,
                remaining_hours=duration,
            )

        elif selected_type == DisturbanceType.CLOUD_SURGE:
            duration = int(self.rng.integers(6, 36))
            cloud_val = float(self.rng.uniform(0.85, 1.00))
            return DisturbanceState(
                disturbance_type=DisturbanceType.CLOUD_SURGE,
                cloud_cover_override=cloud_val,
                temp_delta_c=float(self.rng.uniform(1.0, 3.0)),  # Clouds trap heat slightly in polar nights
                duration_hours=duration,
                remaining_hours=duration,
            )

        elif selected_type == DisturbanceType.BLIZZARD:
            duration = int(self.rng.integers(12, 48))
            return DisturbanceState(
                disturbance_type=DisturbanceType.BLIZZARD,
                wind_speed_multiplier=float(self.rng.uniform(1.8, 2.5)),
                wind_gust_delta_ms=float(self.rng.uniform(12.0, 22.0)),
                cloud_cover_override=1.0,
                temp_delta_c=float(self.rng.uniform(-10.0, -4.0)),
                solar_pv_availability=0.05,  # Heavy blowing snow obliterates solar
                heating_demand_multiplier=float(self.rng.uniform(1.25, 1.45)),  # High wind infiltration loss
                duration_hours=duration,
                remaining_hours=duration,
            )

        elif selected_type == DisturbanceType.EXTREME_COLD:
            duration = int(self.rng.integers(24, 96))
            return DisturbanceState(
                disturbance_type=DisturbanceType.EXTREME_COLD,
                temp_delta_c=float(self.rng.uniform(-18.0, -10.0)),
                cloud_cover_override=float(self.rng.uniform(0.0, 0.20)),  # Clear-sky radiative cooling
                heating_demand_multiplier=float(self.rng.uniform(1.30, 1.60)),
                duration_hours=duration,
                remaining_hours=duration,
            )

        elif selected_type == DisturbanceType.HIGH_WIND:
            duration = int(self.rng.integers(8, 36))
            return DisturbanceState(
                disturbance_type=DisturbanceType.HIGH_WIND,
                wind_speed_multiplier=float(self.rng.uniform(1.4, 1.9)),
                wind_gust_delta_ms=float(self.rng.uniform(6.0, 12.0)),
                duration_hours=duration,
                remaining_hours=duration,
            )

        elif selected_type == DisturbanceType.LOW_WIND:
            duration = int(self.rng.integers(12, 48))
            return DisturbanceState(
                disturbance_type=DisturbanceType.LOW_WIND,
                wind_speed_multiplier=0.25,
                duration_hours=duration,
                remaining_hours=duration,
            )

        elif selected_type == DisturbanceType.SOLAR_REDUCTION:
            duration = int(self.rng.integers(12, 72))
            return DisturbanceState(
                disturbance_type=DisturbanceType.SOLAR_REDUCTION,
                solar_pv_availability=float(self.rng.uniform(0.20, 0.40)),  # Snow/rime blanket on panels
                duration_hours=duration,
                remaining_hours=duration,
            )

        elif selected_type == DisturbanceType.SOLAR_FAILURE:
            duration = int(self.rng.integers(8, 48))
            return DisturbanceState(
                disturbance_type=DisturbanceType.SOLAR_FAILURE,
                solar_pv_availability=0.0,
                duration_hours=duration,
                remaining_hours=duration,
            )

        elif selected_type == DisturbanceType.WIND_FAILURE:
            duration = int(self.rng.integers(12, 48))
            return DisturbanceState(
                disturbance_type=DisturbanceType.WIND_FAILURE,
                wind_turbine_availability=0.0,
                duration_hours=duration,
                remaining_hours=duration,
            )

        elif selected_type == DisturbanceType.COMBINED_POLAR_STRESS:
            duration = int(self.rng.integers(24, 72))
            return DisturbanceState(
                disturbance_type=DisturbanceType.COMBINED_POLAR_STRESS,
                temp_delta_c=float(self.rng.uniform(-16.0, -8.0)),
                wind_speed_multiplier=float(self.rng.uniform(1.8, 2.3)),
                cloud_cover_override=1.0,
                solar_pv_availability=0.0,
                wind_turbine_availability=0.50,  # Turbine de-icing strain
                heating_demand_multiplier=float(self.rng.uniform(1.35, 1.70)),
                duration_hours=duration,
                remaining_hours=duration,
            )

        # Fallback
        return DisturbanceState(DisturbanceType.NORMAL)

    def step(self, is_winter: bool) -> DisturbanceState:
        """Advance simulation by 1 hour, transitioning to a new disturbance when expired."""
        if self.current_state.remaining_hours <= 1:
            self.current_state = self._sample_new_disturbance(is_winter)
        else:
            self.current_state.remaining_hours -= 1
        return self.current_state
