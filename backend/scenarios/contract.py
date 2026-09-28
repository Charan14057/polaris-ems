"""
POLARIS-EMS — Machine-Readable Scenario Impact Contract
SIH26061: Polar Energy Management & Resilience System

Authoritative contract defining expected physical, asset, load, storage,
fuel, resilience, policy, and visual impacts for every registered scenario.
The full-circle test suite (test_scenario_full_circle.py) validates against
this contract.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path


@dataclass
class ScenarioImpactContract:
    scenario_id: str
    name: str
    category: str
    direct_inputs: Dict[str, Any]
    expected_state_changes: List[str]
    expected_asset_changes: Dict[str, Any]
    expected_load_changes: Dict[str, Any]
    expected_energy_changes: Dict[str, Any]
    expected_storage_changes: Dict[str, Any]
    expected_fuel_changes: Dict[str, Any]
    expected_resilience_changes: Dict[str, Any]
    expected_policy_changes: Dict[str, Any]
    expected_visual_changes: Dict[str, Any]


SCENARIO_CONTRACTS: Dict[str, ScenarioImpactContract] = {
    "NORMAL_BASELINE": ScenarioImpactContract(
        scenario_id="NORMAL_BASELINE",
        name="Normal Operational Baseline",
        category="ENVIRONMENTAL",
        direct_inputs={},
        expected_state_changes=["environment.ambient_temperature_c", "solar.solar_generation_kw"],
        expected_asset_changes={"solar": "ONLINE", "wind": "ONLINE", "diesel": "STANDBY_OR_ONLINE"},
        expected_load_changes={"thermal_surge": False, "load_served_nominal": True},
        expected_energy_changes={"renewable_dominant": True, "power_balance_residual_max": 0.05},
        expected_storage_changes={"battery_active": True, "capacity_derated": False},
        expected_fuel_changes={"nominal_burn": True},
        expected_resilience_changes={"threat_state": ["NORMAL", "ADVISORY"]},
        expected_policy_changes={"load_shedding_active": False},
        expected_visual_changes={"solar_color": "active", "wind_spinning": True, "diesel_glow": False}
    ),
    "CLOUDY_CONDITIONS": ScenarioImpactContract(
        scenario_id="CLOUDY_CONDITIONS",
        name="Cloudy Weather Conditions",
        category="ENVIRONMENTAL",
        direct_inputs={"cloud_fraction": 1.5, "irradiance_wm2": 0.65},
        expected_state_changes=["environment.cloud_fraction", "environment.irradiance_wm2", "solar.solar_generation_kw"],
        expected_asset_changes={"solar": "ATTENUATED"},
        expected_load_changes={"thermal_surge": False},
        expected_energy_changes={"solar_reduction_pct_min": 25.0, "power_balance_residual_max": 0.05},
        expected_storage_changes={"battery_support_increased": True},
        expected_fuel_changes={"diesel_dispatch_candidate": True},
        expected_resilience_changes={"threat_state": ["NORMAL", "ADVISORY"]},
        expected_policy_changes={"load_shedding_active": False},
        expected_visual_changes={"solar_color": "attenuated", "cloud_cover": "elevated"}
    ),
    "HEAVY_CLOUD_LOW_IRRADIANCE": ScenarioImpactContract(
        scenario_id="HEAVY_CLOUD_LOW_IRRADIANCE",
        name="Heavy Cloud & Low Irradiance",
        category="ENVIRONMENTAL",
        direct_inputs={"cloud_fraction": 2.0, "irradiance_wm2": 0.25},
        expected_state_changes=["environment.cloud_fraction", "environment.irradiance_wm2", "solar.solar_generation_kw"],
        expected_asset_changes={"solar": "SUPPRESSED"},
        expected_load_changes={"thermal_surge": False},
        expected_energy_changes={"solar_generation_suppressed": True, "power_balance_residual_max": 0.05},
        expected_storage_changes={"battery_discharge_increased": True},
        expected_fuel_changes={"diesel_spin_recommended": True},
        expected_resilience_changes={"threat_state": ["ADVISORY", "WARNING"]},
        expected_policy_changes={"load_shedding_active": False},
        expected_visual_changes={"solar_color": "dark_gold", "cloud_cover": "dense"}
    ),
    "HIGH_WIND": ScenarioImpactContract(
        scenario_id="HIGH_WIND",
        name="High Wind & Katabatic Gusts",
        category="ENVIRONMENTAL",
        direct_inputs={"wind_speed_ms": 1.4},
        expected_state_changes=["environment.wind_speed_ms", "wind.wind_generation_kw"],
        expected_asset_changes={"wind": "RAMPED_TO_RATED"},
        expected_load_changes={"thermal_surge": False},
        expected_energy_changes={"wind_generation_surge": True, "power_balance_residual_max": 0.05},
        expected_storage_changes={"battery_charge_candidate": True},
        expected_fuel_changes={"diesel_curtailed": True},
        expected_resilience_changes={"threat_state": ["NORMAL", "ADVISORY"]},
        expected_policy_changes={"curtailment_mode": "ACTIVE_IF_SURPLUS"},
        expected_visual_changes={"wind_particles_fast": True, "turbine_spin_speed": "HIGH"}
    ),
    "BLIZZARD": ScenarioImpactContract(
        scenario_id="BLIZZARD",
        name="Polar Blizzard Storm",
        category="COMPOUND",
        direct_inputs={"ambient_temperature_c": -10.0, "wind_speed_ms": 2.0, "cloud_fraction": 1.0, "irradiance_wm2": 0.0},
        expected_state_changes=["environment.ambient_temperature_c", "environment.wind_speed_ms", "loads.total_load_kw", "diesel.generator_power_kw"],
        expected_asset_changes={"solar": "ZERO", "diesel": "ONLINE", "wind": "GALE_OPERATION"},
        expected_load_changes={"heating_surge_pct_min": 15.0},
        expected_energy_changes={"thermal_load_surge": True, "power_balance_residual_max": 0.05},
        expected_storage_changes={"battery_discharge_active": True},
        expected_fuel_changes={"fuel_burn_rate_increased": True},
        expected_resilience_changes={"threat_state": ["WARNING", "CRITICAL"]},
        expected_policy_changes={"flexible_shed_candidate": True},
        expected_visual_changes={"snow_particles_dense": True, "station_heating_red": True}
    ),
    "EXTREME_COLD": ScenarioImpactContract(
        scenario_id="EXTREME_COLD",
        name="Extreme Cold Wave",
        category="ENVIRONMENTAL",
        direct_inputs={"ambient_temperature_c": -20.0},
        expected_state_changes=["environment.ambient_temperature_c", "loads.total_load_kw", "thermal.heating_demand_kw"],
        expected_asset_changes={"diesel": "ONLINE"},
        expected_load_changes={"heating_demand_surge_kw_min": 10.0},
        expected_energy_changes={"thermal_peak": True, "power_balance_residual_max": 0.05},
        expected_storage_changes={"battery_cold_derating_active": True},
        expected_fuel_changes={"high_fuel_burn": True},
        expected_resilience_changes={"threat_state": ["WARNING", "CRITICAL"]},
        expected_policy_changes={"prioritize_life_support": True},
        expected_visual_changes={"frost_shader_active": True, "thermal_glow_high": True}
    ),
    "LOW_DAYLIGHT": ScenarioImpactContract(
        scenario_id="LOW_DAYLIGHT",
        name="Low Daylight Exposure",
        category="ENVIRONMENTAL",
        direct_inputs={"irradiance_wm2": 0.30, "solar_availability": 0.40},
        expected_state_changes=["environment.irradiance_wm2", "solar.solar_generation_kw"],
        expected_asset_changes={"solar": "LOW_DAYLIGHT_ATTENUATED"},
        expected_load_changes={"thermal_surge": False},
        expected_energy_changes={"solar_generation_reduced": True, "power_balance_residual_max": 0.05},
        expected_storage_changes={"bess_cycle_active": True},
        expected_fuel_changes={"diesel_spin_standby": True},
        expected_resilience_changes={"threat_state": ["NORMAL", "ADVISORY"]},
        expected_policy_changes={"solar_priority_preserved": True},
        expected_visual_changes={"low_sun_haze": True}
    ),
    "POLAR_NIGHT": ScenarioImpactContract(
        scenario_id="POLAR_NIGHT",
        name="Astronomical Polar Night",
        category="ENVIRONMENTAL",
        direct_inputs={"irradiance_wm2": 0.0, "solar_elevation_deg": -5.0},
        expected_state_changes=["environment.irradiance_wm2", "solar.solar_generation_kw"],
        expected_asset_changes={"solar": "ZERO", "diesel": "DISPATCHED_OR_BESS"},
        expected_load_changes={"heating_continuous": True},
        expected_energy_changes={"zero_solar": True, "power_balance_residual_max": 0.05},
        expected_storage_changes={"bess_deep_cycling": True},
        expected_fuel_changes={"diesel_sustained_burn": True},
        expected_resilience_changes={"threat_state": ["ADVISORY", "WARNING"]},
        expected_policy_changes={"fuel_conservation_mode": True},
        expected_visual_changes={"dark_sky": True, "aurora_active": True, "solar_pv_dormant": True}
    ),
    "SOLAR_GENERATION_FAILURE": ScenarioImpactContract(
        scenario_id="SOLAR_GENERATION_FAILURE",
        name="Solar PV System Trip",
        category="ASSET_FAILURE",
        direct_inputs={"solar_availability": 0.0},
        expected_state_changes=["solar.solar_generation_kw", "solar.solar_available_kw"],
        expected_asset_changes={"solar": "FAULT"},
        expected_load_changes={"thermal_surge": False},
        expected_energy_changes={"solar_generation_zero": True, "power_balance_residual_max": 0.05},
        expected_storage_changes={"battery_takeover": True},
        expected_fuel_changes={"diesel_backup_spin": True},
        expected_resilience_changes={"threat_state": ["ADVISORY", "WARNING"]},
        expected_policy_changes={"alarm_raised": True},
        expected_visual_changes={"solar_array_red_fault": True, "sld_pv_breaker_open": True}
    ),
    "WIND_GENERATION_FAILURE": ScenarioImpactContract(
        scenario_id="WIND_GENERATION_FAILURE",
        name="Wind Turbine Mechanical Trip",
        category="ASSET_FAILURE",
        direct_inputs={"wind_availability": 0.0},
        expected_state_changes=["wind.wind_generation_kw", "wind.wind_available_kw"],
        expected_asset_changes={"wind": "FAULT"},
        expected_load_changes={"thermal_surge": False},
        expected_energy_changes={"wind_generation_zero": True, "power_balance_residual_max": 0.05},
        expected_storage_changes={"battery_support_active": True},
        expected_fuel_changes={"diesel_start_triggered": True},
        expected_resilience_changes={"threat_state": ["ADVISORY", "WARNING"]},
        expected_policy_changes={"reserve_defended": True},
        expected_visual_changes={"turbine_stopped": True, "sld_wind_breaker_open": True}
    ),
    "BATTERY_DEGRADATION": ScenarioImpactContract(
        scenario_id="BATTERY_DEGRADATION",
        name="Battery Capacity Degradation",
        category="ASSET_FAILURE",
        direct_inputs={"battery_capacity": 0.65},
        expected_state_changes=["battery.capacity_kwh", "battery.usable_capacity_kwh"],
        expected_asset_changes={"battery": "DERATED_65_PCT"},
        expected_load_changes={"thermal_surge": False},
        expected_energy_changes={"power_balance_residual_max": 0.05},
        expected_storage_changes={"capacity_derated_to_65_pct": True},
        expected_fuel_changes={"diesel_runtime_extended": True},
        expected_resilience_changes={"threat_state": ["ADVISORY", "WARNING"]},
        expected_policy_changes={"bess_buffer_constrained": True},
        expected_visual_changes={"bess_container_warning": True}
    ),
    "FUEL_RESUPPLY_DELAY": ScenarioImpactContract(
        scenario_id="FUEL_RESUPPLY_DELAY",
        name="Fuel Resupply Delay (7 Days)",
        category="LOGISTICS",
        direct_inputs={"fuel_resupply_delay_hours": 168.0},
        expected_state_changes=["resupply.resupply_window_days"],
        expected_asset_changes={"resupply": "WINDOW_EXTENDED_7D"},
        expected_load_changes={"thermal_surge": False},
        expected_energy_changes={"power_balance_residual_max": 0.05},
        expected_storage_changes={"preserve_soc": True},
        expected_fuel_changes={"autonomy_margin_compressed": True},
        expected_resilience_changes={"threat_state": ["WARNING", "CRITICAL"]},
        expected_policy_changes={"fuel_conservation_mode_mandatory": True},
        expected_visual_changes={"resupply_calendar_red_shift": True}
    ),
    "COMBINED_POLAR_STRESS": ScenarioImpactContract(
        scenario_id="COMBINED_POLAR_STRESS",
        name="Combined Polar Stress Disaster",
        category="COMPOUND",
        direct_inputs={"ambient_temperature_c": -15.0, "wind_speed_ms": 30.0, "cloud_fraction": 1.0, "irradiance_wm2": 0.0, "solar_availability": 0.0, "fuel_resupply_delay_hours": 168.0},
        expected_state_changes=["environment.ambient_temperature_c", "solar.solar_generation_kw", "wind.wind_generation_kw", "loads.total_load_kw", "diesel.generator_power_kw"],
        expected_asset_changes={"solar": "ZERO", "wind": "STORM_CUTOUT", "diesel": "ONLINE_EMERGENCY"},
        expected_load_changes={"thermal_surge_high": True},
        expected_energy_changes={"renewables_zero": True, "power_balance_residual_max": 0.05},
        expected_storage_changes={"deep_discharge": True},
        expected_fuel_changes={"rapid_depletion_risk": True},
        expected_resilience_changes={"threat_state": ["CRITICAL"]},
        expected_policy_changes={"p1_p8_shed_flexible_mandatory": True},
        expected_visual_changes={"extreme_storm_whiteout": True, "station_emergency_flashing": True}
    ),
    "UNFORESEEN_WEATHER": ScenarioImpactContract(
        scenario_id="UNFORESEEN_WEATHER",
        name="Unforeseen Weather Regime Shift",
        category="COMPOUND",
        direct_inputs={"ambient_temperature_c": -12.0, "wind_speed_ms": 1.8, "cloud_fraction": 0.85, "irradiance_wm2": 0.4},
        expected_state_changes=["environment.ambient_temperature_c", "environment.wind_speed_ms", "environment.cloud_fraction", "solar.solar_generation_kw", "wind.wind_generation_kw"],
        expected_asset_changes={"solar": "ATTENUATED", "wind": "SQUALL_ELEVATED"},
        expected_load_changes={"thermal_surge": True},
        expected_energy_changes={"power_balance_residual_max": 0.05},
        expected_storage_changes={"battery_active": True},
        expected_fuel_changes={"diesel_active": True},
        expected_resilience_changes={"threat_state": ["WATCH", "THREATENED", "CRITICAL", "SAFE"]},
        expected_policy_changes={"heating_protection_governed": True},
        expected_visual_changes={"weather_squall_particles": True}
    ),
    "CUSTOM": ScenarioImpactContract(
        scenario_id="CUSTOM",
        name="Custom Scenario Exploration",
        category="CUSTOM",
        direct_inputs={"ambient_temperature_c": -30.0, "wind_speed_ms": 22.0},
        expected_state_changes=["environment.ambient_temperature_c", "environment.wind_speed_ms", "loads.total_load_kw"],
        expected_asset_changes={"custom_override": True},
        expected_load_changes={"heating_load_increased": True},
        expected_energy_changes={"power_balance_residual_max": 0.05},
        expected_storage_changes={"custom_dispatch": True},
        expected_fuel_changes={"fuel_burn_responsive": True},
        expected_resilience_changes={"threat_state": ["WARNING", "CRITICAL"]},
        expected_policy_changes={"custom_policy_applied": True},
        expected_visual_changes={"custom_parameters_reflected": True}
    )
}


def export_contract_json(target_path: Path = None) -> Path:
    """Exports machine-readable contract dictionary to JSON file."""
    if target_path is None:
        target_path = Path(__file__).resolve().parent / "contract.json"
    data = {k: asdict(v) for k, v in SCENARIO_CONTRACTS.items()}
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return target_path


if __name__ == "__main__":
    p = export_contract_json()
    print(f"Exported machine-readable scenario contract to {p}")
