"""
POLARIS-EMS — Digital Twin Diesel & Fuel Subsystem Engine
SIH26061: Polar Energy Management & Resilience System

Simulates diesel generator output, fuel burn curves, and tank farm levels:
- Fuel burn rate: F = P_diesel * fuel_curve + idle_fuel * (P_diesel > 0)
- Monotonic fuel accounting: Fuel(t+1) = max(0, Fuel(t) - F * dt + Resupply(t))
- Never silently refills; requires explicit resupply delivery events
- Computes days of fuel remaining based on recent consumption
"""

from typing import Tuple, Optional
from backend.twin.state import DieselState, FuelState, ResupplyState
from backend.data.station_profiles.loader import StationProfile


class DieselFuelEngine:
    """Manages generator operating constraints, fuel consumption, and tank inventory."""

    def __init__(self, profile: StationProfile):
        self.profile = profile
        self.d_spec = profile.electrical
        self.f_spec = profile.fuel

    def calculate_fuel_consumption(
        self,
        generator_power_kw: float,
        dt_hours: float = 1.0
    ) -> float:
        """
        Calculates fuel consumed in liters for the given generator output over dt.
        """
        if generator_power_kw <= 0.01:
            return 0.0
        
        fuel_per_kwh = float(self.d_spec.diesel_fuel_curve_l_per_kwh)
        idle_fuel_per_h = float(self.d_spec.diesel_idle_fuel_l_per_h)
        
        rate_l_per_h = (generator_power_kw * fuel_per_kwh) + idle_fuel_per_h
        return float(round(rate_l_per_h * dt_hours, 2))

    def step(
        self,
        diesel_state: DieselState,
        fuel_state: FuelState,
        requested_gen_power_kw: float,
        resupply_state: Optional[ResupplyState] = None,
        dt_hours: float = 1.0
    ) -> Tuple[DieselState, FuelState]:
        """
        Updates generator output and fuel inventory.
        """
        p_max = float(self.d_spec.diesel_generator_kw_rated)
        min_loading_pct = float(self.d_spec.diesel_min_loading_pct)
        p_min = p_max * min_loading_pct

        # If generator is called, clamp between min loading and max rated capacity
        if requested_gen_power_kw > 0.01:
            actual_gen_kw = float(min(p_max, max(p_min, requested_gen_power_kw)))
            gen_status = "ONLINE"
            online_count = 1
        else:
            actual_gen_kw = 0.0
            gen_status = "STANDBY"
            online_count = 0

        # Calculate fuel consumption
        fuel_burn_l = self.calculate_fuel_consumption(actual_gen_kw, dt_hours)
        burn_rate_l_per_h = fuel_burn_l / max(0.01, dt_hours)

        # Check explicit resupply restock
        resupply_inflow_l = 0.0
        if resupply_state and resupply_state.resupply_event_active:
            resupply_inflow_l = resupply_state.fuel_delivered_liters

        # Update remaining fuel (strictly non-negative)
        new_fuel_remaining = max(
            0.0,
            fuel_state.fuel_remaining_l - fuel_burn_l + resupply_inflow_l
        )
        new_fuel_consumed = fuel_state.fuel_consumed_l + fuel_burn_l

        # Days of fuel remaining based on nominal daily baseline (~350 L/day)
        nominal_daily_burn = max(50.0, burn_rate_l_per_h * 24.0 if actual_gen_kw > 0 else 300.0)
        days_remaining = round(new_fuel_remaining / nominal_daily_burn, 1)

        new_diesel_state = DieselState(
            generator_status=gen_status,
            online_count=online_count,
            generator_power_kw=round(actual_gen_kw, 2),
            generator_min_power_kw=round(p_min, 2),
            generator_max_power_kw=round(p_max, 2),
            fuel_consumption_l_per_h=round(burn_rate_l_per_h, 2),
            cumulative_runtime_h=diesel_state.cumulative_runtime_h + (dt_hours if actual_gen_kw > 0 else 0.0),
            provenance="SIMULATED"
        )

        new_fuel_state = FuelState(
            fuel_remaining_l=round(new_fuel_remaining, 1),
            fuel_initial_l=fuel_state.fuel_initial_l,
            fuel_consumed_l=round(new_fuel_consumed, 1),
            fuel_reserve_l=fuel_state.fuel_reserve_l,
            fuel_capacity_l=fuel_state.fuel_capacity_l,
            days_of_fuel_remaining=days_remaining,
            provenance="SIMULATED"
        )

        return new_diesel_state, new_fuel_state
