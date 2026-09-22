"""
POLARIS-EMS — Station Profile Loader & Validator
SIH26061: Polar Energy Management & Resilience System

Loads and validates verified public station parameters for Bharati, Maitri, and Himadri.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DeviceProfile(BaseModel):
    id: str
    name: str
    category: str = Field(..., description="CRITICAL | IMPORTANT | OPERATIONAL | FLEXIBLE")
    priority_rank: int
    nominal_power_kw: float
    min_required_power_kw: float
    deferrable: bool
    thermal_consequence: str = Field("NONE", description="NONE | LOW | MEDIUM | HIGH | EXTREME")
    default_status: str = Field("ONLINE", description="ONLINE | DEFERRED | OFF")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid = {"CRITICAL", "IMPORTANT", "OPERATIONAL", "FLEXIBLE"}
        if v.upper() not in valid:
            raise ValueError(f"Category must be one of {valid}, got {v}")
        return v.upper()


class ElectricalProfile(BaseModel):
    nominal_voltage_v: int = 400
    grid_frequency_hz: int = 50
    solar_pv_kw_peak: float
    solar_tilt_deg: float
    solar_efficiency: float
    solar_temp_coeff_pct: float
    wind_turbine_kw_rated: float
    wind_cut_in_speed_ms: float
    wind_rated_speed_ms: float
    wind_cut_out_speed_ms: float
    diesel_generator_count: int
    diesel_generator_kw_rated: float
    diesel_min_loading_pct: float
    diesel_fuel_curve_l_per_kwh: float
    diesel_idle_fuel_l_per_h: float
    battery_capacity_kwh: float
    battery_min_soc: float
    battery_max_soc: float
    battery_nominal_soc: float
    battery_max_charge_kw: float
    battery_max_discharge_kw: float
    battery_roundtrip_efficiency: float
    battery_cold_derate_coeff: float


class ThermalProfile(BaseModel):
    indoor_target_temp_c: float
    indoor_min_safe_temp_c: float
    building_ua_kw_per_k: float
    thermal_capacitance_kwh_per_k: float
    ventilation_loss_coeff: float
    internal_heat_gain_kw: float
    chp_heat_recovery_efficiency: float


class FuelProfile(BaseModel):
    storage_capacity_liters: float
    initial_fuel_liters: float
    critical_fuel_reserve_liters: float
    fuel_type: str


class StationProfile(BaseModel):
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
    typical_summer_temp_c: List[float]
    typical_winter_temp_c: List[float]
    extreme_min_temp_c: float
    extreme_wind_gust_ms: float
    resupply_interval_days: int
    default_resupply_window_days: int
    electrical: ElectricalProfile
    thermal: ThermalProfile
    fuel: FuelProfile
    devices: List[DeviceProfile]


class StationProfileRegistry:
    """Singleton-style cache and loader for verified station profiles."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            # Default to configs/station_profiles.json relative to repository root
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            config_path = base_dir / "configs" / "station_profiles.json"
        self.config_path = config_path
        self._profiles: Dict[str, StationProfile] = {}
        self.load()

    def load(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Station profiles configuration not found at {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        for station_id, data in raw_data.items():
            self._profiles[station_id.upper()] = StationProfile(**data)

    def get(self, station_id: str) -> StationProfile:
        sid = station_id.upper()
        if sid not in self._profiles:
            raise KeyError(f"Station '{station_id}' not found. Available: {list(self._profiles.keys())}")
        return self._profiles[sid]

    def list_stations(self) -> List[str]:
        return list(self._profiles.keys())
