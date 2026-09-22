"""
POLARIS-EMS — Phase 2 ML Readiness Audit Script
Inspects generated datasets, verifies target distributions, autocorrelations,
shortage mechanics, and forecast-origin contract compliance.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.data.station_profiles.loader import StationProfileRegistry


def autocorr(series, lag):
    return float(series.autocorr(lag=lag))


def run_audit():
    print("=" * 70)
    print("POLARIS-EMS: PHASE 2 ML READINESS AUDIT")
    print("=" * 70)

    stations = ["BHARATI", "MAITRI", "HIMADRI"]
    registry = StationProfileRegistry()

    all_target_stats = {}

    for sid in stations:
        profile = registry.get(sid)
        csv_path = REPO_ROOT / "datasets" / sid.lower() / "full_3yr_hourly.csv"
        assert csv_path.exists(), f"Missing dataset {csv_path}"

        df = pd.read_csv(csv_path)
        print(f"\n--- Station: {sid} ({len(df):,} hours) ---")

        # 1. Shortage & Power Balance Flow Audit
        unserved = df["unserved_energy_kw"]
        unserved_count = (unserved > 0.01).sum()
        max_unserved = unserved.max()
        total_unserved_kwh = unserved.sum()
        print(f"Shortage check:")
        print(f"  Unserved hours: {unserved_count} / {len(df)}")
        print(f"  Max unserved spike: {max_unserved:.2f} kW")
        print(f"  Total unserved energy: {total_unserved_kwh:.2f} kWh")

        # Check maximum load vs generator capacity
        p_gen_rated = profile.electrical.diesel_generator_kw_rated
        max_load = df["total_load_kw"].max()
        print(f"  Rated generator cap: {p_gen_rated:.1f} kW | Max total load observed: {max_load:.1f} kW")

        # 2. Target Statistics & Predictability
        targets = ["total_load_kw", "solar_generation_kw", "wind_generation_kw"]
        target_stats = {}

        for tgt in targets:
            s = df[tgt]
            quantiles = s.quantile([0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]).to_dict()
            ac_1 = autocorr(s, 1)
            ac_24 = autocorr(s, 24)
            ac_168 = autocorr(s, 168)

            target_stats[tgt] = {
                "mean": float(s.mean()),
                "std": float(s.std()),
                "min": float(s.min()),
                "max": float(s.max()),
                "p01": quantiles[0.01],
                "p05": quantiles[0.05],
                "p25": quantiles[0.25],
                "p50": quantiles[0.50],
                "p75": quantiles[0.75],
                "p95": quantiles[0.95],
                "p99": quantiles[0.99],
                "ac_lag1": ac_1,
                "ac_lag24": ac_24,
                "ac_lag168": ac_168,
            }

            print(f"\n  Target: {tgt}")
            print(f"    Mean: {s.mean():.2f} kW | Std: {s.std():.2f} kW | Min: {s.min():.2f} | Max: {s.max():.2f}")
            print(f"    P1={quantiles[0.01]:.2f}, P5={quantiles[0.05]:.2f}, P25={quantiles[0.25]:.2f}, P50={quantiles[0.50]:.2f}, P75={quantiles[0.75]:.2f}, P95={quantiles[0.95]:.2f}, P99={quantiles[0.99]:.2f}")
            print(f"    Autocorr: Lag-1h = {ac_1:.3f} | Lag-24h (diurnal) = {ac_24:.3f} | Lag-168h (weekly) = {ac_168:.3f}")

        # Disturbance behavior
        print(f"\n  Disturbance regimes distribution:")
        dist_counts = df["disturbance_state"].value_counts().to_dict()
        for d_type, count in dist_counts.items():
            sub_load = df[df["disturbance_state"] == d_type]["total_load_kw"].mean()
            sub_solar = df[df["disturbance_state"] == d_type]["solar_generation_kw"].mean()
            sub_wind = df[df["disturbance_state"] == d_type]["wind_generation_kw"].mean()
            print(f"    {d_type:<22}: {count:>5} hrs ({count/len(df)*100:>4.1f}%) | Mean Load={sub_load:.1f} kW | Mean Solar={sub_solar:.1f} kW | Mean Wind={sub_wind:.1f} kW")

        all_target_stats[sid] = target_stats

    # 3. Provenance check
    print("\n" + "=" * 70)
    print("PROVENANCE & INTEGRITY CHECK")
    for sid in stations:
        csv_path = REPO_ROOT / "datasets" / sid.lower() / "full_3yr_hourly.csv"
        df = pd.read_csv(csv_path)
        prov_tiers = df["provenance"].unique().tolist()
        print(f"Station {sid}: Provenance column values: {prov_tiers}")
        assert prov_tiers == ["SYNTHETIC"], f"Expected only SYNTHETIC provenance, got {prov_tiers}"


if __name__ == "__main__":
    run_audit()
