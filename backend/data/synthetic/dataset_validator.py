"""
POLARIS-EMS — Comprehensive Dataset Quality-Control Validator
SIH26061: Polar Energy Management & Resilience System

Validates structural, physical, energy conservation, and causal invariants
across multi-year synthetic polar datasets.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from backend.data.station_profiles.loader import StationProfile


class DatasetQualityValidator:
    """Executes automated quality-control validation on synthetic datasets."""

    def __init__(self, profile: StationProfile):
        self.profile = profile

    def validate_all(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Runs the complete battery of quality-control checks."""
        time_res = self.check_temporal_continuity(df)
        phys_res = self.check_physical_bounds(df)
        energy_res = self.check_energy_balance(df)
        causal_res = self.check_causal_relationships(df)
        stats = self.compute_summary_statistics(df)

        all_passed = (
            time_res["passed"]
            and phys_res["passed"]
            and energy_res["passed"]
            and causal_res["passed"]
        )

        return {
            "all_passed": all_passed,
            "station_id": self.profile.station_id,
            "total_rows": len(df),
            "temporal_checks": time_res,
            "physical_bounds_checks": phys_res,
            "energy_balance_checks": energy_res,
            "causal_checks": causal_res,
            "summary_statistics": stats,
        }

    def check_temporal_continuity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Verifies strictly ascending, uninterrupted hourly timestamps."""
        failures = []
        ts = pd.to_datetime(df["timestamp"])

        if not ts.is_monotonic_increasing:
            failures.append("Timestamps are not strictly monotonically increasing")

        if ts.duplicated().sum() > 0:
            failures.append(f"Found {ts.duplicated().sum()} duplicate timestamps")

        diffs = ts.diff().dropna()
        non_1h_gaps = (diffs != pd.Timedelta(hours=1)).sum()
        if non_1h_gaps > 0:
            failures.append(f"Found {non_1h_gaps} non-1-hour timestamp intervals")

        return {
            "passed": len(failures) == 0,
            "failures": failures,
            "start_timestamp": str(ts.iloc[0]),
            "end_timestamp": str(ts.iloc[-1]),
            "total_hours": len(df),
        }

    def check_physical_bounds(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Verifies all variables conform to realistic physical and equipment limits."""
        failures = []
        elec = self.profile.electrical
        fuel = self.profile.fuel

        # Non-negative generation
        for col in ["solar_generation_kw", "wind_generation_kw", "generator_power_kw", "total_generation_kw"]:
            if (df[col] < -1e-5).any():
                failures.append(f"Negative values detected in {col} (min: {df[col].min():.4f})")

        # Capacity limits
        if (df["solar_generation_kw"] > elec.solar_pv_kw_peak + 1e-3).any():
            failures.append(f"Solar generation exceeded peak capacity ({df['solar_generation_kw'].max():.2f} > {elec.solar_pv_kw_peak})")

        if (df["wind_generation_kw"] > elec.wind_turbine_kw_rated + 1e-3).any():
            failures.append(f"Wind generation exceeded rated capacity ({df['wind_generation_kw'].max():.2f} > {elec.wind_turbine_kw_rated})")

        if (df["generator_power_kw"] > elec.diesel_generator_kw_rated + 1e-3).any():
            failures.append(f"Diesel power exceeded generator rated capacity ({df['generator_power_kw'].max():.2f} > {elec.diesel_generator_kw_rated})")

        # Battery SOC bounds
        min_soc_pct = elec.battery_min_soc * 100.0 - 0.05
        max_soc_pct = elec.battery_max_soc * 100.0 + 0.05
        if (df["battery_soc_pct"] < min_soc_pct).any():
            failures.append(f"Battery SOC dropped below minimum threshold ({df['battery_soc_pct'].min():.2f}% < {min_soc_pct:.1f}%)")
        if (df["battery_soc_pct"] > max_soc_pct).any():
            failures.append(f"Battery SOC exceeded maximum threshold ({df['battery_soc_pct'].max():.2f}% > {max_soc_pct:.1f}%)")

        # Fuel bounds
        if (df["fuel_remaining_l"] < 0.0).any():
            failures.append(f"Fuel remaining dropped below zero ({df['fuel_remaining_l'].min():.1f} L)")
        if (df["fuel_remaining_l"] > fuel.storage_capacity_liters + 1e-3).any():
            failures.append(f"Fuel remaining exceeded tank capacity ({df['fuel_remaining_l'].max():.1f} > {fuel.storage_capacity_liters})")

        # Temperature limits
        if (df["temperature_c"] < self.profile.extreme_min_temp_c - 10.0).any():
            failures.append(f"Temperature fell below extreme station minimum ({df['temperature_c'].min():.1f} °C)")

        return {
            "passed": len(failures) == 0,
            "failures": failures,
        }

    def check_energy_balance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Checks exact load decomposition and power balance conservation at every timestep."""
        failures = []

        # 1. Subloads sum to total load
        subloads_sum = (
            df["thermal_load_kw"]
            + df["critical_load_kw"]
            + df["important_load_kw"]
            + df["operational_load_kw"]
            + df["flexible_load_kw"]
            + df["maintenance_load_kw"]
        )
        load_discrepancy = (subloads_sum - df["total_load_kw"]).abs()
        max_load_disc = load_discrepancy.max()
        if max_load_disc > 0.05:
            failures.append(f"Subload decomposition discrepancy detected: max discrepancy = {max_load_disc:.4f} kW")

        # 2. Power Balance Conservation
        # Available inflow = total_generation_kw + battery_discharge_kw
        # Outflow = total_load_kw + battery_charge_kw + curtailment_kw - unserved_energy_kw
        inflow = df["total_generation_kw"] + df["battery_discharge_kw"]
        outflow = df["total_load_kw"] + df["battery_charge_kw"] + df["curtailment_kw"] - df["unserved_energy_kw"]
        power_imbalance = (inflow - outflow).abs()
        max_power_imb = power_imbalance.max()
        if max_power_imb > 0.05:
            failures.append(f"Power balance conservation violated: max imbalance = {max_power_imb:.4f} kW")

        return {
            "passed": len(failures) == 0,
            "failures": failures,
            "max_load_decomposition_error_kw": float(round(max_load_disc, 5)),
            "max_power_balance_error_kw": float(round(max_power_imb, 5)),
        }

    def check_causal_relationships(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Verifies physical cause-and-effect relationships."""
        failures = []

        # 1. Temperature vs Heating load: Negative correlation (colder ambient -> higher heating demand)
        corr_temp_heat = df["temperature_c"].corr(df["thermal_load_kw"])
        if corr_temp_heat > -0.50:
            failures.append(f"Expected strong negative correlation between ambient temperature and thermal load, got {corr_temp_heat:.3f}")

        # 2. Solar generation at night: Must be 0 when solar elevation <= 0
        night_mask = df["solar_elevation_deg"] <= 0.0
        night_solar_sum = df.loc[night_mask, "solar_generation_kw"].sum()
        if night_solar_sum > 1e-4:
            failures.append(f"Solar generation occurred during night/sub-horizon elevation (total {night_solar_sum:.2f} kW)")

        # 3. Wind cut-out: When wind exceeds cut-out, generation must be 0
        cut_out = self.profile.electrical.wind_cut_out_speed_ms
        storm_mask = df["wind_speed_ms"] >= cut_out
        if storm_mask.sum() > 0:
            storm_gen = df.loc[storm_mask, "wind_generation_kw"].sum()
            if storm_gen > 1e-4:
                failures.append(f"Wind generation occurred above cut-out speed of {cut_out} m/s ({storm_gen:.2f} kW)")

        return {
            "passed": len(failures) == 0,
            "failures": failures,
            "temperature_vs_thermal_load_correlation": float(round(corr_temp_heat, 3)),
            "night_solar_generation_total_kw": float(round(night_solar_sum, 4)),
        }

    def compute_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculates descriptive distribution statistics for key metrics."""
        cols = [
            "temperature_c",
            "wind_speed_ms",
            "irradiance_wm2",
            "total_load_kw",
            "thermal_load_kw",
            "critical_load_kw",
            "solar_generation_kw",
            "wind_generation_kw",
            "battery_soc_pct",
            "generator_power_kw",
            "fuel_consumed_l",
            "curtailment_kw",
        ]
        stats = {}
        for col in cols:
            if col in df.columns:
                s = df[col]
                stats[col] = {
                    "mean": float(round(s.mean(), 2)),
                    "median": float(round(s.median(), 2)),
                    "std": float(round(s.std(), 2)),
                    "min": float(round(s.min(), 2)),
                    "max": float(round(s.max(), 2)),
                    "p10": float(round(s.quantile(0.10), 2)),
                    "p50": float(round(s.quantile(0.50), 2)),
                    "p90": float(round(s.quantile(0.90), 2)),
                }
        return stats
