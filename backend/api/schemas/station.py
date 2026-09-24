"""
POLARIS-EMS — Station Profile API Schemas
SIH26061: Polar Energy Management & Resilience System

Provides Pydantic schemas for station profile discovery and detailed inspection.
Sourced strictly from the authoritative StationProfileRegistry.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DeviceSummarySchema(BaseModel):
    id: str
    name: str
    category: str
    priority_rank: int
    nominal_power_kw: float
    deferrable: bool


class ElectricalDetailSchema(BaseModel):
    nominal_voltage_v: int
    grid_frequency_hz: int
    solar_pv_kw_peak: float
    wind_turbine_kw_rated: float
    diesel_generator_count: int
    diesel_generator_kw_rated: float
    total_diesel_capacity_kw: float
    battery_capacity_kwh: float
    battery_min_soc: float
    battery_max_soc: float
    battery_max_charge_kw: float
    battery_max_discharge_kw: float


class ThermalDetailSchema(BaseModel):
    indoor_target_temp_c: float
    indoor_min_safe_temp_c: float
    building_ua_kw_per_k: float
    thermal_capacitance_kwh_per_k: float
    internal_heat_gain_kw: float


class FuelDetailSchema(BaseModel):
    storage_capacity_liters: float
    initial_fuel_liters: float
    critical_fuel_reserve_liters: float
    fuel_type: str


class StationSummarySchema(BaseModel):
    """Compact summary of a polar station."""
    station_id: str
    name: str
    region: str
    location: str
    classification: str
    latitude: float
    longitude: float
    total_diesel_capacity_kw: float
    battery_capacity_kwh: float
    fuel_capacity_liters: float
    min_safe_temp_c: float


class StationDetailResponse(BaseModel):
    """Complete validated station profile configuration."""
    station_id: str
    name: str
    region: str
    location: str
    latitude: float
    longitude: float
    altitude_m: float
    classification: str
    climate_zone: str
    polar_day_range: List[str]
    polar_night_range: List[str]
    resupply_interval_days: int
    electrical: ElectricalDetailSchema
    thermal: ThermalDetailSchema
    fuel: FuelDetailSchema
    devices: List[DeviceSummarySchema]
    provenance: str = "CONFIGURED"
