"""
POLARIS-EMS — Station Configuration & Physical Limit Adapter
SIH26061: Polar Energy Management & Resilience System

Provides a dynamic, single-source-of-truth adapter loading physical parameters
from configs/station_profiles.json via StationProfileRegistry.
Eliminates hardcoded generation capacities in ML code.
"""

from typing import Dict, Any, List
from pathlib import Path
import pandas as pd

from backend.data.station_profiles.loader import StationProfileRegistry, StationProfile


class StationConfigAdapter:
    """Extracts physical and operational bounds for ML forecasting models."""

    def __init__(self, config_path: Path = None):
        self.registry = StationProfileRegistry(config_path=config_path)

    def get_profile(self, station_id: str) -> StationProfile:
        return self.registry.get(station_id.upper())

    def get_solar_limits(self, station_id: str) -> Dict[str, float]:
        """Returns peak PV capacity, tilt, and temperature derate coefficients."""
        prof = self.get_profile(station_id)
        elec = prof.electrical
        return {
            "solar_pv_kw_peak": float(elec.solar_pv_kw_peak),
            "solar_tilt_deg": float(elec.solar_tilt_deg),
            "solar_efficiency": float(elec.solar_efficiency),
            "solar_temp_coeff_pct": float(elec.solar_temp_coeff_pct),
        }

    def get_wind_limits(self, station_id: str) -> Dict[str, float]:
        """Returns wind turbine power curve specifications."""
        prof = self.get_profile(station_id)
        elec = prof.electrical
        return {
            "wind_turbine_kw_rated": float(elec.wind_turbine_kw_rated),
            "wind_cut_in_speed_ms": float(elec.wind_cut_in_speed_ms),
            "wind_rated_speed_ms": float(elec.wind_rated_speed_ms),
            "wind_cut_out_speed_ms": float(elec.wind_cut_out_speed_ms),
        }

    def get_thermal_parameters(self, station_id: str) -> Dict[str, float]:
        """Returns building thermal envelope parameters for physics baseline."""
        prof = self.get_profile(station_id)
        therm = prof.thermal
        return {
            "indoor_target_temp_c": float(therm.indoor_target_temp_c),
            "indoor_min_safe_temp_c": float(therm.indoor_min_safe_temp_c),
            "building_ua_kw_per_k": float(therm.building_ua_kw_per_k),
            "thermal_capacitance_kwh_per_k": float(therm.thermal_capacitance_kwh_per_k),
            "internal_heat_gain_kw": float(therm.internal_heat_gain_kw),
            "chp_heat_recovery_efficiency": float(therm.chp_heat_recovery_efficiency),
        }

    def get_electrical_ratings(self, station_id: str) -> Dict[str, float]:
        """Returns diesel and battery capacities."""
        prof = self.get_profile(station_id)
        elec = prof.electrical
        return {
            "diesel_generator_kw_rated": float(elec.diesel_generator_kw_rated),
            "diesel_generator_count": int(elec.diesel_generator_count),
            "battery_capacity_kwh": float(elec.battery_capacity_kwh),
            "battery_max_discharge_kw": float(elec.battery_max_discharge_kw),
            "battery_max_charge_kw": float(elec.battery_max_charge_kw),
        }

    def get_reconciliation_table(self) -> pd.DataFrame:
        """Generates the formal configuration reconciliation audit table."""
        records = []
        for sid in self.registry.list_stations():
            prof = self.registry.get(sid)
            elec = prof.electrical
            records.append({
                "station_id": sid,
                "name": prof.name,
                "pv_peak_kw": elec.solar_pv_kw_peak,
                "wind_rated_kw": elec.wind_turbine_kw_rated,
                "wind_cut_in_ms": elec.wind_cut_in_speed_ms,
                "wind_cut_out_ms": elec.wind_cut_out_speed_ms,
                "diesel_rated_kw": elec.diesel_generator_kw_rated,
                "battery_kwh": elec.battery_capacity_kwh,
                "source": "configs/station_profiles.json",
                "ml_constraint": f"PV in [0, {elec.solar_pv_kw_peak}], Wind in [0, {elec.wind_turbine_kw_rated}] with cut-in {elec.wind_cut_in_speed_ms} and cut-out {elec.wind_cut_out_speed_ms}"
            })
        return pd.DataFrame.from_records(records)
