"""
POLARIS-EMS — Synthetic Dataset Baseline Generator CLI
SIH26061: Polar Energy Management & Resilience System

Generates multi-day/multi-year hourly synthetic polar datasets for Bharati, Maitri, and Himadri.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.data.synthetic.physics_simulator_skeleton import PhysicsSyntheticSimulator


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic polar weather and energy datasets.")
    parser.add_argument("--station", type=str, default="BHARATI", choices=["BHARATI", "MAITRI", "HIMADRI"], help="Target station")
    parser.add_argument("--days", type=int, default=14, help="Number of days to simulate (e.g. 14, 365, 730)")
    parser.add_argument("--start-date", type=str, default="2025-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    args = parser.parse_args()

    registry = StationProfileRegistry()
    profile = registry.get(args.station)

    start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
    total_hours = args.days * 24

    print(f"============================================================")
    print(f"POLARIS-EMS: Generating {args.days} days ({total_hours} hours) baseline for {profile.name}")
    print(f"Location: {profile.location} ({profile.latitude:.4f}, {profile.longitude:.4f})")
    print(f"Deterministic seed: {args.seed} | Resupply window: {profile.default_resupply_window_days} days")
    print(f"============================================================")

    simulator = PhysicsSyntheticSimulator(profile, seed=args.seed)

    print("Step 1/2: Simulating environmental weather time series...")
    weather_df = simulator.generate_weather_timeseries(start_dt, hours=total_hours)

    print("Step 2/2: Simulating coupled electrical, thermal, battery, and fuel dynamics...")
    energy_df = simulator.simulate_station_energy(weather_df)

    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        repo_root = Path(__file__).resolve().parent.parent
        out_path = repo_root / "datasets" / f"{args.station.lower()}_{args.days}d_baseline.csv"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    energy_df.to_csv(out_path, index=False)

    print(f"\n[SUCCESS] Dataset generated and written to: {out_path}")
    print(f"Total Rows: {len(energy_df)}")
    print(f"Summary Statistics:")
    print(f" - Ambient Temp: Min {energy_df['ambient_temperature_c'].min():.1f} °C, Max {energy_df['ambient_temperature_c'].max():.1f} °C, Mean {energy_df['ambient_temperature_c'].mean():.1f} °C")
    print(f" - Total Load: Min {energy_df['total_load_kw'].min():.1f} kW, Max {energy_df['total_load_kw'].max():.1f} kW, Mean {energy_df['total_load_kw'].mean():.1f} kW")
    print(f" - Solar Peak: {energy_df['solar_generation_kw'].max():.1f} kW (Capacity: {profile.electrical.solar_pv_kw_peak} kWp)")
    print(f" - Wind Peak: {energy_df['wind_generation_kw'].max():.1f} kW (Capacity: {profile.electrical.wind_turbine_kw_rated} kW)")
    print(f" - Fuel Burned: {energy_df['fuel_burned_liters'].sum():.1f} Liters | Remaining: {energy_df['fuel_remaining_liters'].iloc[-1]:.1f} Liters")
    print(f" - Battery SOC: Final {energy_df['battery_soc'].iloc[-1]*100:.1f}% [Min: {energy_df['battery_soc'].min()*100:.1f}%, Max: {energy_df['battery_soc'].max()*100:.1f}%]")
    print(f"============================================================")


if __name__ == "__main__":
    main()
