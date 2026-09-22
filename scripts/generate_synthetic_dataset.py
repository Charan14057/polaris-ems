"""
POLARIS-EMS — Production Multi-Year Synthetic Dataset Generator CLI
SIH26061: Polar Energy Management & Resilience System

Generates 3-year hourly synthetic polar datasets (26,304 hours per station)
for Bharati, Maitri, and Himadri with leap-year handling and deterministic seeds.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add repository root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.data.synthetic.physics_simulator_skeleton import (
    PhysicsSyntheticSimulator,
    DATASET_VERSION,
    SIMULATOR_VERSION,
)
from backend.data.synthetic.dataset_splitter import ChronologicalDatasetSplitter
from backend.data.synthetic.dataset_validator import DatasetQualityValidator


def generate_for_station(
    station_id: str,
    start_dt: datetime,
    end_dt: datetime,
    global_seed: int,
    output_base_dir: Path,
):
    registry = StationProfileRegistry()
    profile = registry.get(station_id)

    print(f"\n{'='*70}")
    print(f"POLARIS-EMS DATASET GENERATION: {profile.name} ({profile.station_id})")
    print(f"Location: {profile.location} ({profile.latitude:.4f}, {profile.longitude:.4f})")
    print(f"Time Range: {start_dt.isoformat()} to {end_dt.isoformat()} UTC")
    print(f"Global Seed: {global_seed}")
    print(f"{'='*70}")

    station_dir = output_base_dir / station_id.lower()
    station_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic hierarchical seed
    station_offset = {"BHARATI": 100, "MAITRI": 200, "HIMADRI": 300}.get(station_id, 0)
    seed = global_seed + station_offset

    simulator = PhysicsSyntheticSimulator(
        profile=profile,
        seed=seed,
        weather_seed=seed + 1,
        operational_seed=seed + 2,
        disturbance_seed=seed + 3,
    )

    print("Step 1/4: Simulating coupled polar weather, disturbances, operations, and energy...")
    df = simulator.simulate_environment(start_date=start_dt, end_date=end_dt)
    total_hours = len(df)
    print(f"   -> Generated {total_hours:,} hourly records with {len(df.columns)} features.")

    print("Step 2/4: Executing quality-control validation and energy conservation checks...")
    validator = DatasetQualityValidator(profile)
    val_report = validator.validate_all(df)
    if not val_report["all_passed"]:
        print("   [WARNING] Quality validation reported discrepancies:")
        for section in ["temporal_checks", "physical_bounds_checks", "energy_balance_checks", "causal_checks"]:
            if not val_report[section]["passed"]:
                print(f"      - {section}: {val_report[section]['failures']}")
    else:
        print("   -> All temporal, physical, energy balance, and causal invariant checks PASSED.")

    print("Step 3/4: Splitting chronologically (70% Train, 15% Validation, 15% Test)...")
    train_df, val_df, test_df, split_meta = ChronologicalDatasetSplitter.split(
        df, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15
    )
    print(f"   -> Train: {len(train_df):,} hrs ({split_meta['train']['start_timestamp'][:10]} to {split_meta['train']['end_timestamp'][:10]})")
    print(f"   -> Val:   {len(val_df):,} hrs ({split_meta['validation_calibration']['start_timestamp'][:10]} to {split_meta['validation_calibration']['end_timestamp'][:10]})")
    print(f"   -> Test:  {len(test_df):,} hrs ({split_meta['test']['start_timestamp'][:10]} to {split_meta['test']['end_timestamp'][:10]})")

    print("Step 4/4: Writing dataset artifacts and metadata...")
    ChronologicalDatasetSplitter.save_split_files(
        output_dir=station_dir,
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        split_meta=split_meta,
    )
    df.to_csv(station_dir / "full_3yr_hourly.csv", index=False)

    # Save comprehensive metadata
    meta = {
        "dataset_version": DATASET_VERSION,
        "simulator_version": SIMULATOR_VERSION,
        "station_id": station_id,
        "station_name": profile.name,
        "location": profile.location,
        "latitude": profile.latitude,
        "longitude": profile.longitude,
        "altitude_m": profile.altitude_m,
        "climate_zone": profile.climate_zone,
        "global_seed": global_seed,
        "station_seed": seed,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_hours": total_hours,
        "calendar_policy": "Explicit UTC datetime with leap-year handling (2024=366d, 2025=365d, 2026=365d)",
        "split_summary": split_meta,
        "summary_statistics": val_report["summary_statistics"],
    }
    with open(station_dir / "dataset_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[COMPLETED] Station {station_id} artifacts saved to {station_dir}")


def main():
    parser = argparse.ArgumentParser(description="Generate multi-year polar synthetic energy datasets.")
    parser.add_argument("--station", type=str, default="BHARATI", choices=["BHARATI", "MAITRI", "HIMADRI"], help="Target station")
    parser.add_argument("--all-stations", action="store_true", help="Generate datasets for all 3 configured stations")
    parser.add_argument("--years", type=int, default=3, help="Number of years (default: 3)")
    parser.add_argument("--start", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2026-12-31", help="End date (YYYY-MM-DD)")
    parser.add_argument("--seed", type=int, default=42, help="Global deterministic seed")
    parser.add_argument("--output", type=str, default=None, help="Base output directory")
    args = parser.parse_args()

    start_dt = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc, hour=0, minute=0, second=0)
    end_dt = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc, hour=23, minute=0, second=0)

    out_base = Path(args.output) if args.output else REPO_ROOT / "datasets"

    if args.all_stations:
        for sid in ["BHARATI", "MAITRI", "HIMADRI"]:
            generate_for_station(sid, start_dt, end_dt, args.seed, out_base)
    else:
        generate_for_station(args.station, start_dt, end_dt, args.seed, out_base)


if __name__ == "__main__":
    main()
