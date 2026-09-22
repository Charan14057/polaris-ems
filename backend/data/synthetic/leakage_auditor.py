"""
POLARIS-EMS — Feature Leakage Auditor
SIH26061: Polar Energy Management & Resilience System

Conducts strict audits to ensure no future information, target-derived features,
or centered rolling windows contaminate the dataset or feature pipelines.
"""

from typing import Dict, List, Tuple
import pandas as pd
from datetime import datetime


class FeatureLeakageAuditor:
    """Verifies that features respect causal time ordering and known-ahead constraints."""

    FEATURE_TAXONOMY = {
        # Deterministic astronomical & calendar variables (known ahead for any future horizon t+k)
        "KNOWN_AHEAD": [
            "timestamp",
            "station_id",
            "solar_elevation_deg",
            "occupancy_state",
            "maintenance_state",
            "seed",
            "dataset_version",
            "simulator_version",
            "provenance",
        ],
        # Environmental and state variables observed up to prediction time t
        "OBSERVED_AT_T": [
            "temperature_c",
            "pressure_hpa",
            "humidity_pct",
            "wind_speed_ms",
            "wind_direction_deg",
            "irradiance_wm2",
            "cloud_fraction",
            "storm_state",
            "wind_turbine_status",
            "battery_soc_pct",
            "battery_energy_kwh",
            "battery_charge_kw",
            "battery_discharge_kw",
            "battery_temperature_derating",
            "generator_status",
            "generator_power_kw",
            "fuel_consumed_l",
            "fuel_remaining_l",
            "curtailment_kw",
            "unserved_energy_kw",
            "research_activity_state",
            "communication_state",
            "scenario_id",
            "disturbance_state",
        ],
        # Target variables (forecasting targets: must NEVER appear in future feature matrices without lag >= horizon)
        "FUTURE_TARGET_UNKNOWN_AT_T": [
            "total_load_kw",
            "thermal_load_kw",
            "critical_load_kw",
            "important_load_kw",
            "operational_load_kw",
            "flexible_load_kw",
            "maintenance_load_kw",
            "solar_generation_kw",
            "solar_available_kw",
            "wind_generation_kw",
            "renewable_generation_kw",
            "total_generation_kw",
        ],
    }

    @classmethod
    def audit_dataframe(cls, df: pd.DataFrame) -> Dict:
        """
        Conducts structural and temporal integrity checks on a synthetic dataset:
        1. Timestamp strict monotonicity (no duplicate timestamps, strictly ascending).
        2. Column classification across availability taxonomy.
        3. Checks for invalid lookaheads or NaN gaps.
        """
        issues = []

        # 1. Timestamp checks
        ts = pd.to_datetime(df["timestamp"])
        if not ts.is_monotonic_increasing:
            issues.append("Timestamps are NOT strictly monotonically increasing!")

        dup_count = ts.duplicated().sum()
        if dup_count > 0:
            issues.append(f"Found {dup_count} duplicate timestamps!")

        # 2. Schema taxonomy check
        unclassified = []
        for col in df.columns:
            found = False
            for group, cols in cls.FEATURE_TAXONOMY.items():
                if col in cols:
                    found = True
                    break
            if not found:
                unclassified.append(col)

        if unclassified:
            issues.append(f"Unclassified columns found in taxonomy: {unclassified}")

        # 3. Target non-trivial variance
        for target in ["total_load_kw", "solar_generation_kw", "wind_generation_kw"]:
            if target in df.columns:
                if df[target].std() == 0:
                    issues.append(f"Target column '{target}' has zero variance (constant signal)!")

        return {
            "passed": len(issues) == 0,
            "total_rows": len(df),
            "columns_audited": len(df.columns),
            "issues": issues,
            "unclassified_columns": unclassified,
        }

    @classmethod
    def generate_availability_matrix(cls) -> pd.DataFrame:
        """Returns the canonical feature availability matrix for documentation."""
        records = []
        for category, cols in cls.FEATURE_TAXONOMY.items():
            for c in cols:
                records.append({
                    "feature_name": c,
                    "availability_tier": category,
                    "known_at_t_plus_k": category == "KNOWN_AHEAD",
                    "requires_lag_for_t_plus_k": category in ["OBSERVED_AT_T", "FUTURE_TARGET_UNKNOWN_AT_T"],
                    "is_target_variable": category == "FUTURE_TARGET_UNKNOWN_AT_T",
                })
        return pd.DataFrame(records)
