"""
POLARIS-EMS — Dataset Quality-Control & Validation CLI
SIH26061: Polar Energy Management & Resilience System

Inspects, validates, and quality-checks generated multi-year synthetic polar datasets.
"""

import sys
import argparse
from pathlib import Path
import pandas as pd

# Add repository root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.data.synthetic.dataset_validator import DatasetQualityValidator
from backend.data.synthetic.leakage_auditor import FeatureLeakageAuditor


def validate_station_directory(station_dir: Path, registry: StationProfileRegistry) -> bool:
    station_id = station_dir.name.upper()
    try:
        profile = registry.get(station_id)
    except KeyError:
        print(f"Skipping directory {station_dir.name}: not a known station ID.")
        return True

    csv_file = station_dir / "full_3yr_hourly.csv"
    if not csv_file.exists():
        print(f"[ERROR] {csv_file} does not exist!")
        return False

    print(f"\n{'='*70}")
    print(f"VALIDATING DATASET: {profile.name} ({station_id})")
    print(f"File: {csv_file}")
    print(f"{'='*70}")

    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df):,} rows and {len(df.columns)} columns.")

    # 1. Feature Leakage Audit
    print("\n[Check 1/4] Feature Leakage Audit...")
    leak_report = FeatureLeakageAuditor.audit_dataframe(df)
    if leak_report["passed"]:
        print("   -> PASS: Strictly monotonic timestamps, no duplicates, valid taxonomy.")
    else:
        print("   -> FAIL: Feature leakage or structural issues:")
        for issue in leak_report["issues"]:
            print(f"      * {issue}")

    # 2. Quality Control & Physical Invariants
    print("\n[Check 2/4] Physical & Thermodynamic Invariants...")
    validator = DatasetQualityValidator(profile)
    val_report = validator.validate_all(df)

    phys = val_report["physical_bounds_checks"]
    if phys["passed"]:
        print("   -> PASS: Solar, wind, diesel, SOC, fuel, and temperature within physical bounds.")
    else:
        print("   -> FAIL: Physical bounds violated:")
        for f in phys["failures"]:
            print(f"      * {f}")

    # 3. Energy Balance & Load Decomposition
    print("\n[Check 3/4] Energy Conservation & Load Decomposition...")
    energy = val_report["energy_balance_checks"]
    if energy["passed"]:
        print(f"   -> PASS: Power balance conserved. Max error: {energy['max_power_balance_error_kw']:.5f} kW.")
        print(f"   -> PASS: Load decomposition exact. Max error: {energy['max_load_decomposition_error_kw']:.5f} kW.")
    else:
        print("   -> FAIL: Energy conservation violations:")
        for f in energy["failures"]:
            print(f"      * {f}")

    # 4. Causal Correlations
    print("\n[Check 4/4] Causal Dynamics...")
    causal = val_report["causal_checks"]
    if causal["passed"]:
        print(f"   -> PASS: Temperature vs Thermal Load correlation: {causal['temperature_vs_thermal_load_correlation']:.3f} (strong negative).")
        print(f"   -> PASS: Night solar generation: {causal['night_solar_generation_total_kw']:.4f} kW (strictly 0).")
    else:
        print("   -> FAIL: Causal checks failed:")
        for f in causal["failures"]:
            print(f"      * {f}")

    # Print summary key percentiles
    print("\nKey Metrics Summary (P10 / P50 / P90):")
    stats = val_report["summary_statistics"]
    for k in ["temperature_c", "wind_speed_ms", "irradiance_wm2", "total_load_kw", "solar_generation_kw", "wind_generation_kw", "battery_soc_pct"]:
        if k in stats:
            s = stats[k]
            print(f"   - {k:<24}: P10={s['p10']:>7.2f} | P50={s['p50']:>7.2f} | P90={s['p90']:>7.2f} (Min={s['min']:>6.1f}, Max={s['max']:>6.1f})")

    overall = leak_report["passed"] and val_report["all_passed"]
    print(f"\nOVERALL RESULT: {'[PASSED]' if overall else '[FAILED]'}")
    return overall


def main():
    parser = argparse.ArgumentParser(description="Validate synthetic polar energy datasets.")
    parser.add_argument("--dataset", type=str, default="datasets", help="Path to datasets folder or station folder")
    args = parser.parse_args()

    target_path = Path(args.dataset)
    if not target_path.is_absolute():
        target_path = REPO_ROOT / target_path

    registry = StationProfileRegistry()

    if not target_path.exists():
        print(f"[ERROR] Path {target_path} does not exist.")
        sys.exit(1)

    all_passed = True
    if (target_path / "full_3yr_hourly.csv").exists():
        all_passed = validate_station_directory(target_path, registry)
    else:
        # Check subdirectories
        station_dirs = [d for d in target_path.iterdir() if d.is_dir() and (d / "full_3yr_hourly.csv").exists()]
        if not station_dirs:
            print(f"No station datasets found in {target_path}")
            sys.exit(1)
        for sdir in station_dirs:
            passed = validate_station_directory(sdir, registry)
            if not passed:
                all_passed = False

    if not all_passed:
        sys.exit(1)
    else:
        print(f"\nAll datasets verified successfully!")


if __name__ == "__main__":
    main()
