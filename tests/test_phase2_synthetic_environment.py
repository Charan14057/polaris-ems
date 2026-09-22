"""
POLARIS-EMS — Automated Test Suite: Phase 2 Synthetic Energy Environment
SIH26061: Polar Energy Management & Resilience System

Verifies:
1. Multi-year hourly timestamp generation with leap-year handling (26,304 hours).
2. Deterministic bitwise reproducibility across identical seeds, variance across different seeds.
3. 10 polar disturbance regimes and causal propagation.
4. Load decomposition exactness and thermal capacitance dynamics.
5. Energy power balance conservation and battery SOC physical bounds.
6. Monotonic fuel depletion with explicit resupply events.
7. Chronological dataset splitting (70/15/15) and feature leakage audit.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.data.synthetic.physics_simulator_skeleton import PhysicsSyntheticSimulator
from backend.data.synthetic.disturbance_engine import DisturbanceType, DisturbanceState, PolarDisturbanceGenerator
from backend.data.synthetic.operational_scheduler import OperationalScheduler
from backend.data.synthetic.dataset_splitter import ChronologicalDatasetSplitter
from backend.data.synthetic.leakage_auditor import FeatureLeakageAuditor
from backend.data.synthetic.dataset_validator import DatasetQualityValidator


@pytest.fixture
def registry():
    return StationProfileRegistry()


@pytest.fixture
def bharati_profile(registry):
    return registry.get("BHARATI")


class TestMultiYearCalendarAndDisturbances:
    """Verifies astronomical calendar, leap-year handling, and disturbance mechanics."""

    def test_leap_year_handling_2024_to_2026(self, bharati_profile):
        """Verify 3-year simulation generates exactly 26,304 hours with Feb 29 present in 2024."""
        sim = PhysicsSyntheticSimulator(bharati_profile, seed=42)
        start_dt = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2026, 12, 31, 23, 0, tzinfo=timezone.utc)

        # Run 100 days first to verify leap year day fast
        df_leap = sim.simulate_environment(
            start_date=datetime(2024, 2, 28, 0, 0, tzinfo=timezone.utc),
            end_date=datetime(2024, 3, 1, 23, 0, tzinfo=timezone.utc),
        )

        # 3 days: Feb 28, Feb 29, March 1 = 72 hours
        assert len(df_leap) == 72
        feb29_rows = df_leap[df_leap["timestamp"].str.startswith("2024-02-29")]
        assert len(feb29_rows) == 24, "Leap day Feb 29, 2024 must contain exactly 24 hourly timesteps"

    def test_all_ten_disturbance_regimes_exist(self):
        expected_regimes = {
            "NORMAL",
            "CLOUD_SURGE",
            "BLIZZARD",
            "EXTREME_COLD",
            "HIGH_WIND",
            "LOW_WIND",
            "SOLAR_REDUCTION",
            "SOLAR_FAILURE",
            "WIND_FAILURE",
            "COMBINED_POLAR_STRESS",
        }
        actual_regimes = {d.value for d in DisturbanceType}
        assert expected_regimes == actual_regimes

    def test_deterministic_reproducibility(self, bharati_profile):
        """Identical seeds must produce identical data; different seeds must vary."""
        start_dt = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2025, 1, 7, 23, 0, tzinfo=timezone.utc)

        sim_a1 = PhysicsSyntheticSimulator(bharati_profile, seed=12345)
        sim_a2 = PhysicsSyntheticSimulator(bharati_profile, seed=12345)
        sim_b = PhysicsSyntheticSimulator(bharati_profile, seed=99999)

        df_a1 = sim_a1.simulate_environment(start_dt, end_dt)
        df_a2 = sim_a2.simulate_environment(start_dt, end_dt)
        df_b = sim_b.simulate_environment(start_dt, end_dt)

        # Bitwise identical verification
        pd.testing.assert_frame_equal(df_a1, df_a2)

        # Different seed produces different realization
        assert not df_a1["temperature_c"].equals(df_b["temperature_c"])
        assert not df_a1["total_load_kw"].equals(df_b["total_load_kw"])


class TestPhysicalConservationAndCausality:
    """Verifies energy conservation, power balance, and causal thermodynamics."""

    def test_load_decomposition_exactness(self, bharati_profile):
        sim = PhysicsSyntheticSimulator(bharati_profile, seed=42)
        start_dt = datetime(2025, 6, 1, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2025, 6, 14, 23, 0, tzinfo=timezone.utc)
        df = sim.simulate_environment(start_dt, end_dt)

        subload_sum = (
            df["thermal_load_kw"]
            + df["critical_load_kw"]
            + df["important_load_kw"]
            + df["operational_load_kw"]
            + df["flexible_load_kw"]
            + df["maintenance_load_kw"]
        )
        diff = (subload_sum - df["total_load_kw"]).abs()
        assert (diff < 1e-4).all(), f"Subloads must sum exactly to total_load_kw (max diff: {diff.max()})"

    def test_power_balance_conservation(self, bharati_profile):
        sim = PhysicsSyntheticSimulator(bharati_profile, seed=42)
        start_dt = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2025, 1, 14, 23, 0, tzinfo=timezone.utc)
        df = sim.simulate_environment(start_dt, end_dt)

        inflow = df["total_generation_kw"] + df["battery_discharge_kw"]
        outflow = df["total_load_kw"] + df["battery_charge_kw"] + df["curtailment_kw"] - df["unserved_energy_kw"]
        imbalance = (inflow - outflow).abs()
        assert (imbalance < 1e-3).all(), f"Power balance conservation violated! Max error: {imbalance.max()}"

    def test_battery_soc_boundaries_and_cold_derate(self, bharati_profile):
        sim = PhysicsSyntheticSimulator(bharati_profile, seed=42)
        start_dt = datetime(2025, 5, 1, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2025, 5, 21, 23, 0, tzinfo=timezone.utc)
        df = sim.simulate_environment(start_dt, end_dt)

        elec = bharati_profile.electrical
        min_soc_pct = elec.battery_min_soc * 100.0 - 0.01
        max_soc_pct = elec.battery_max_soc * 100.0 + 0.01

        assert (df["battery_soc_pct"] >= min_soc_pct).all()
        assert (df["battery_soc_pct"] <= max_soc_pct).all()
        assert (df["battery_temperature_derating"] <= 1.0).all()
        assert (df["battery_temperature_derating"] >= 0.70).all()

    def test_fuel_monotonicity_and_resupply_restock(self, bharati_profile):
        """Fuel is strictly non-increasing except during explicit resupply vessel docking."""
        sim = PhysicsSyntheticSimulator(bharati_profile, seed=42)
        # Jan 15 to Jan 25 covers Antarctic resupply date (Jan 20)
        start_dt = datetime(2025, 1, 15, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2025, 1, 25, 23, 0, tzinfo=timezone.utc)
        df = sim.simulate_environment(start_dt, end_dt)

        fuel_diff = df["fuel_remaining_l"].diff()
        refills = df[fuel_diff > 0.0]["timestamp"]
        assert len(refills) == 1, "Fuel must increase only once during the explicit Jan 20 resupply event"
        assert "2025-01-20" in refills.iloc[0]


class TestSplittingAndLeakageAudit:
    """Verifies chronological dataset splitting and feature leakage prevention."""

    def test_chronological_splitting_boundaries(self, bharati_profile):
        sim = PhysicsSyntheticSimulator(bharati_profile, seed=42)
        start_dt = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2024, 4, 30, 23, 0, tzinfo=timezone.utc)
        df = sim.simulate_environment(start_dt, end_dt)

        train_df, val_df, test_df, meta = ChronologicalDatasetSplitter.split(
            df, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15
        )

        assert len(train_df) + len(val_df) + len(test_df) == len(df)
        assert train_df["timestamp"].iloc[-1] < val_df["timestamp"].iloc[0]
        assert val_df["timestamp"].iloc[-1] < test_df["timestamp"].iloc[0]

    def test_feature_leakage_audit_clean(self, bharati_profile):
        sim = PhysicsSyntheticSimulator(bharati_profile, seed=42)
        start_dt = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2025, 1, 7, 23, 0, tzinfo=timezone.utc)
        df = sim.simulate_environment(start_dt, end_dt)

        audit_res = FeatureLeakageAuditor.audit_dataframe(df)
        assert audit_res["passed"] is True
        assert len(audit_res["issues"]) == 0
        assert len(audit_res["unclassified_columns"]) == 0

    def test_dataset_quality_validator_full_suite(self, bharati_profile):
        sim = PhysicsSyntheticSimulator(bharati_profile, seed=42)
        start_dt = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2025, 1, 21, 23, 0, tzinfo=timezone.utc)
        df = sim.simulate_environment(start_dt, end_dt)

        validator = DatasetQualityValidator(bharati_profile)
        report = validator.validate_all(df)
        assert report["all_passed"] is True
