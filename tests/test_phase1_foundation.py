"""
POLARIS-EMS — Automated Test Suite: Phase 1 Data Foundation
SIH26061: Polar Energy Management & Resilience System

Verifies:
1. Station profiles load accurately and validate all physical constraints.
2. Provenance tagging enforces transparency.
3. Synthetic physics simulator obeys thermodynamic, electrical, and causal laws.
4. Weather ingestion pipeline standardizes and quality-checks data.
"""

import math
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

from backend.data.provenance.metadata import ProvenanceTier, ProvenanceRecord, ProvenanceMetric
from backend.data.station_profiles.loader import StationProfileRegistry, StationProfile
from backend.data.synthetic.physics_simulator_skeleton import PhysicsSyntheticSimulator
from backend.data.connectors.weather_ingestion import WeatherIngestionAdapter, WeatherStandardSchema


@pytest.fixture
def registry():
    return StationProfileRegistry()


class TestStationProfiles:
    """Validates station profile configurations for Bharati, Maitri, and Himadri."""

    def test_all_stations_present(self, registry):
        stations = registry.list_stations()
        assert "BHARATI" in stations
        assert "MAITRI" in stations
        assert "HIMADRI" in stations

    @pytest.mark.parametrize("station_id", ["BHARATI", "MAITRI", "HIMADRI"])
    def test_station_physical_constraints(self, registry, station_id):
        prof = registry.get(station_id)

        # Coordinate sanity
        if "Antarctica" in prof.region:
            assert -90.0 <= prof.latitude <= -60.0, "Antarctic stations must be in Southern high latitudes"
        else:
            assert 70.0 <= prof.latitude <= 90.0, "Himadri must be in Arctic high latitudes"

        # Electrical bounds
        elec = prof.electrical
        assert elec.solar_pv_kw_peak > 0
        assert elec.wind_turbine_kw_rated > 0
        assert elec.diesel_generator_count >= 2, "Station must have at least N+1 generator redundancy"
        assert 0.10 <= elec.battery_min_soc < elec.battery_max_soc <= 1.0
        assert elec.battery_capacity_kwh > 0

        # Thermal bounds
        therm = prof.thermal
        assert 15.0 <= therm.indoor_target_temp_c <= 24.0
        assert therm.building_ua_kw_per_k > 0
        assert therm.thermal_capacitance_kwh_per_k > 0

        # Fuel bounds
        fuel = prof.fuel
        assert fuel.storage_capacity_liters >= fuel.initial_fuel_liters > fuel.critical_fuel_reserve_liters > 0

        # Devices validation
        assert len(prof.devices) >= 5
        categories = {d.category for d in prof.devices}
        assert "CRITICAL" in categories
        assert "IMPORTANT" in categories
        assert "OPERATIONAL" in categories
        assert "FLEXIBLE" in categories

        # Minimum required power check
        for dev in prof.devices:
            assert dev.min_required_power_kw <= dev.nominal_power_kw
            if dev.category == "CRITICAL":
                assert dev.min_required_power_kw > 0, "Critical device cannot have 0 minimum power"
                assert dev.deferrable is False, "Critical device cannot be deferrable"


class TestDataProvenance:
    """Validates the strict 6-tier provenance system."""

    def test_provenance_tiers_complete(self):
        expected = {"REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"}
        actual = {tier.value for tier in ProvenanceTier}
        assert expected == actual

    def test_provenance_metric_summary(self):
        rec = ProvenanceRecord(
            tier=ProvenanceTier.REAL,
            source="NCPOR_AWS_BHARATI",
            description="Verified calibrated ultrasonic anemometer",
            is_verified=True
        )
        metric = ProvenanceMetric(
            metric_name="wind_speed",
            value=14.2,
            unit="m/s",
            provenance=rec
        )
        summary = metric.summary()
        assert "[REAL]" in summary
        assert "14.20 m/s" in summary
        assert "NCPOR_AWS_BHARATI" in summary


class TestPhysicsSimulatorCausalLaws:
    """Verifies physical and thermodynamic consistency of the synthetic generator."""

    def test_temperature_drop_increases_heating_load(self, registry):
        prof = registry.get("BHARATI")
        sim = PhysicsSyntheticSimulator(prof, seed=101)

        heat_warm = sim.calculate_thermal_heating_load(ambient_temp_c=-5.0)
        heat_cold = sim.calculate_thermal_heating_load(ambient_temp_c=-35.0)

        assert heat_cold > heat_warm, "Extreme cold must causally increase building heat demand"

    def test_solar_elevation_and_cloud_attenuation(self, registry):
        prof = registry.get("BHARATI")
        sim = PhysicsSyntheticSimulator(prof, seed=101)

        # Midday summer in Antarctica (day 15, hour 12)
        elev = sim._calculate_solar_elevation(day_of_year=15, hour=12.0)
        assert elev > 20.0, "Austral summer midday should have positive solar elevation"

        # Midday winter in Antarctica (day 172, hour 12)
        elev_winter = sim._calculate_solar_elevation(day_of_year=172, hour=12.0)
        assert elev_winter < 0.0, "Antarctic mid-winter must have negative solar elevation (polar night)"

        p_solar_clear = sim.calculate_solar_power(irradiance_wm2=800.0, ambient_temp_c=-10.0)
        p_solar_dark = sim.calculate_solar_power(irradiance_wm2=0.0, ambient_temp_c=-10.0)
        assert p_solar_clear > 10.0
        assert p_solar_dark == 0.0

    def test_wind_power_curve_and_cut_out(self, registry):
        prof = registry.get("BHARATI")
        sim = PhysicsSyntheticSimulator(prof, seed=101)
        w_spec = prof.electrical

        # Below cut-in
        assert sim.calculate_wind_power(w_spec.wind_cut_in_speed_ms - 0.5) == 0.0
        # At rated
        assert sim.calculate_wind_power(w_spec.wind_rated_speed_ms) == pytest.approx(w_spec.wind_turbine_kw_rated, rel=1e-3)
        # Extreme wind cut-out
        assert sim.calculate_wind_power(w_spec.wind_cut_out_speed_ms + 1.0) == 0.0

    def test_energy_simulation_power_and_storage_conservation(self, registry):
        prof = registry.get("BHARATI")
        sim = PhysicsSyntheticSimulator(prof, seed=42)

        start = datetime(2026, 1, 1, 0, 0)
        weather_df = sim.generate_weather_timeseries(start, hours=48)
        energy_df = sim.simulate_station_energy(weather_df)

        assert len(energy_df) == 48

        # Invariants:
        # 1. Total load > 0
        assert (energy_df["total_load_kw"] > 0).all()
        # 2. Battery SOC bounded
        assert (energy_df["battery_soc"] >= prof.electrical.battery_min_soc - 1e-4).all()
        assert (energy_df["battery_soc"] <= prof.electrical.battery_max_soc + 1e-4).all()
        # 3. Fuel decreases or stays constant, never increases without resupply
        fuel_diff = energy_df["fuel_remaining_liters"].diff().dropna()
        assert (fuel_diff <= 0.0).all()


class TestWeatherIngestionQC:
    """Verifies that weather ingestion correctly cleans and validates data."""

    def test_clean_and_validate(self):
        raw_df = pd.DataFrame({
            "timestamp": ["2026-01-01 01:00:00", "2026-01-01 00:00:00"],
            "ambient_temperature_c": [-95.0, 15.0],  # -95 is unphysical, should clip to -75
            "wind_speed_ms": [-5.0, 85.0],           # -5 clipped to 0, 85 clipped to 70
            "wind_direction_deg": [380.0, 180.0],    # 380 mod 360 = 20
            "solar_irradiance_wm2": [-10.0, 500.0],  # -10 clipped to 0
            "provenance_tier": ["REAL", "REAL"],
        })

        cleaned = WeatherIngestionAdapter.validate_and_clean(raw_df, "BHARATI")

        # Sorted by timestamp
        assert cleaned.iloc[0]["ambient_temperature_c"] == 15.0
        assert cleaned.iloc[1]["ambient_temperature_c"] == -75.0
        assert cleaned.iloc[0]["wind_speed_ms"] == 70.0
        assert cleaned.iloc[1]["wind_speed_ms"] == 0.0
        assert cleaned.iloc[1]["wind_direction_deg"] == 20.0
        assert cleaned.iloc[1]["solar_irradiance_wm2"] == 0.0
        assert cleaned.iloc[0]["station_id"] == "BHARATI"
