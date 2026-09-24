"""
POLARIS-EMS — Station API Adapter
SIH26061: Polar Energy Management & Resilience System

Translates StationProfile models from StationProfileRegistry into API response schemas.
Sourced strictly from the authoritative configuration (zero hardcoded values).
"""

from typing import List
from backend.data.station_profiles.loader import StationProfile, StationProfileRegistry
from backend.api.schemas.station import (
    StationSummarySchema,
    StationDetailResponse,
    ElectricalDetailSchema,
    ThermalDetailSchema,
    FuelDetailSchema,
    DeviceSummarySchema
)


class StationAdapter:
    """Adapts StationProfile domain models to API presentation schemas."""

    @staticmethod
    def to_summary(profile: StationProfile) -> StationSummarySchema:
        total_diesel_kw = profile.electrical.diesel_generator_count * profile.electrical.diesel_generator_kw_rated
        return StationSummarySchema(
            station_id=profile.station_id.upper(),
            name=profile.name,
            region=profile.region,
            location=profile.location,
            classification=profile.classification,
            latitude=profile.latitude,
            longitude=profile.longitude,
            total_diesel_capacity_kw=total_diesel_kw,
            battery_capacity_kwh=profile.electrical.battery_capacity_kwh,
            fuel_capacity_liters=profile.fuel.storage_capacity_liters,
            min_safe_temp_c=profile.thermal.indoor_min_safe_temp_c
        )

    @staticmethod
    def to_detail(profile: StationProfile) -> StationDetailResponse:
        total_diesel_kw = profile.electrical.diesel_generator_count * profile.electrical.diesel_generator_kw_rated
        return StationDetailResponse(
            station_id=profile.station_id.upper(),
            name=profile.name,
            region=profile.region,
            location=profile.location,
            latitude=profile.latitude,
            longitude=profile.longitude,
            altitude_m=profile.altitude_m,
            classification=profile.classification,
            climate_zone=profile.climate_zone,
            polar_day_range=profile.polar_day_range,
            polar_night_range=profile.polar_night_range,
            resupply_interval_days=profile.resupply_interval_days,
            electrical=ElectricalDetailSchema(
                nominal_voltage_v=profile.electrical.nominal_voltage_v,
                grid_frequency_hz=profile.electrical.grid_frequency_hz,
                solar_pv_kw_peak=profile.electrical.solar_pv_kw_peak,
                wind_turbine_kw_rated=profile.electrical.wind_turbine_kw_rated,
                diesel_generator_count=profile.electrical.diesel_generator_count,
                diesel_generator_kw_rated=profile.electrical.diesel_generator_kw_rated,
                total_diesel_capacity_kw=total_diesel_kw,
                battery_capacity_kwh=profile.electrical.battery_capacity_kwh,
                battery_min_soc=profile.electrical.battery_min_soc,
                battery_max_soc=profile.electrical.battery_max_soc,
                battery_max_charge_kw=profile.electrical.battery_max_charge_kw,
                battery_max_discharge_kw=profile.electrical.battery_max_discharge_kw
            ),
            thermal=ThermalDetailSchema(
                indoor_target_temp_c=profile.thermal.indoor_target_temp_c,
                indoor_min_safe_temp_c=profile.thermal.indoor_min_safe_temp_c,
                building_ua_kw_per_k=profile.thermal.building_ua_kw_per_k,
                thermal_capacitance_kwh_per_k=profile.thermal.thermal_capacitance_kwh_per_k,
                internal_heat_gain_kw=profile.thermal.internal_heat_gain_kw
            ),
            fuel=FuelDetailSchema(
                storage_capacity_liters=profile.fuel.storage_capacity_liters,
                initial_fuel_liters=profile.fuel.initial_fuel_liters,
                critical_fuel_reserve_liters=profile.fuel.critical_fuel_reserve_liters,
                fuel_type=profile.fuel.fuel_type
            ),
            devices=[
                DeviceSummarySchema(
                    id=dev.id,
                    name=dev.name,
                    category=dev.category,
                    priority_rank=dev.priority_rank,
                    nominal_power_kw=dev.nominal_power_kw,
                    deferrable=dev.deferrable
                )
                for dev in profile.devices
            ],
            provenance="CONFIGURED"
        )
