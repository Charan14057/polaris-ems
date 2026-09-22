"""
POLARIS-EMS — Digital Twin Simulation CLI
SIH26061: Polar Energy Management & Resilience System

Executes forward simulation trajectories using the computational Energy Digital Twin:
Predict (ML) -> Simulate (Twin) -> Optimize (Phase 6) -> Protect -> Preserve

Usage:
    python scripts/simulate_twin.py --station BHARATI --horizon 48 --mode EXPECTED
    python scripts/simulate_twin.py --station MAITRI --horizon 48 --mode CONSERVATIVE
    python scripts/simulate_twin.py --station HIMADRI --horizon 48 --mode OPTIMISTIC
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.twin_engine import TwinEngine
from backend.twin.forecast_adapter import ForecastAdapter, TwinInputStep
from backend.ml.inference import InferenceEngine


def run_simulation(
    station_id: str,
    horizon_hours: int = 48,
    mode: str = "EXPECTED",
    output_csv: str = None
):
    sid = station_id.upper()
    print(f"\n=======================================================")
    print(f"POLARIS-EMS — DIGITAL TWIN SIMULATION ENGINE")
    print(f"Station: {sid} | Horizon: {horizon_hours}h | Mode: {mode}")
    print(f"Policy: BASELINE_SIMULATION_DISPATCH (Deterministic Rule)")
    print(f"=======================================================\n")

    profile_reg = StationProfileRegistry()
    safety_reg = SafetyThresholdRegistry()
    profile = profile_reg.get(sid)

    # 1. Load Station Baseline Data for Initial Telemetry
    data_path = ROOT_DIR / "datasets" / f"{sid.lower()}_14d_baseline.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")
    
    df = pd.read_csv(data_path)
    # Pick a winter blizzard or cold slice (e.g. index 100 to 100 + horizon)
    start_idx = 100
    if start_idx + horizon_hours > len(df):
        start_idx = max(0, len(df) - horizon_hours - 1)
    
    slice_df = df.iloc[start_idx : start_idx + horizon_hours].copy()
    init_row = df.iloc[start_idx]

    initial_telem = {
        "ambient_temp_c": float(init_row.get("temperature_c", -18.0)),
        "wind_speed_m_per_s": float(init_row.get("wind_speed_ms", 10.0)),
        "ghi_w_per_m2": float(init_row.get("irradiance_wm2", 0.0)),
        "total_load_kw": float(init_row.get("total_load_kw", 42.0)),
        "soc_pct": float(profile.electrical.battery_nominal_soc),
        "fuel_remaining_l": float(profile.fuel.initial_fuel_liters),
        "indoor_temp_c": float(profile.thermal.indoor_target_temp_c)
    }

    # 2. Initialize Twin
    twin = TwinEngine(sid, profile, safety_reg)
    init_state = twin.initialize_twin(
        timestamp=str(init_row.get("timestamp", "2026-06-01T00:00:00Z")),
        initial_telemetry=initial_telem
    )

    print(f"[INITIAL STATE]")
    print(f"  Indoor Temp: {init_state.thermal.indoor_temperature_c:.1f}°C (Safe Min: {init_state.thermal.indoor_min_safe_temp_c:.1f}°C)")
    print(f"  Battery SOC: {init_state.battery.soc_pct * 100.0:.1f}% ({init_state.battery.usable_capacity_kwh:.1f} kWh usable)")
    print(f"  Fuel Stock:  {init_state.fuel.fuel_remaining_l:.0f} L ({init_state.fuel.days_of_fuel_remaining:.1f} days)")
    print(f"  Reserve:     {init_state.resilience.dependable_reserve_kw:.1f} kW ({init_state.resilience.dependable_reserve_pct:.1f}%)")
    print(f"  Threat:      {init_state.resilience.threat_state}\n")

    # 3. Build Driving Input Steps (using slice telemetry and risk mode)
    steps = []
    h = 1
    for _, row in slice_df.iterrows():
        base_load = float(row.get("total_load_kw", 40.0))
        base_solar = float(row.get("solar_generation_kw", 0.0))
        base_wind = float(row.get("wind_generation_kw", 0.0))

        # Adjust by risk mode
        if mode == "CONSERVATIVE":
            step_load = base_load * 1.15
            step_solar = base_solar * 0.70
            step_wind = base_wind * 0.70
        elif mode == "OPTIMISTIC":
            step_load = base_load * 0.85
            step_solar = base_solar * 1.15
            step_wind = base_wind * 1.15
        else:
            step_load = base_load
            step_solar = base_solar
            step_wind = base_wind

        steps.append(TwinInputStep(
            timestamp=str(row.get("timestamp", f"T+{h}")),
            horizon_h=h,
            ambient_temp_c=float(row.get("temperature_c", -18.0)),
            wind_speed_m_per_s=float(row.get("wind_speed_ms", 10.0)),
            ghi_w_per_m2=float(row.get("irradiance_wm2", 0.0)),
            load_kw=round(step_load, 2),
            solar_kw=round(step_solar, 2),
            wind_kw=round(step_wind, 2),
            mode=mode,
            provenance="FORECAST"
        ))
        h += 1

    # 4. Execute Multi-Step Forward Simulation
    print(f"Simulating {len(steps)} steps under {mode} scenario...")
    trajectory = twin.simulate(init_state, steps, dt_hours=1.0)
    traj_df = trajectory.to_dataframe()

    # 5. Output Summary Report
    s = trajectory.summary
    print("\n---------------- SIMULATION SUMMARY ----------------")
    print(f"Station:                 {s['station_id']}")
    print(f"Scenario Mode:           {s['mode']}")
    print(f"Duration:                {s['duration_hours']:.0f} hours")
    print(f"Total Unserved Load:     {s['total_unserved_kwh']:.2f} kWh")
    print(f"Critical Unserved Load:  {s['total_critical_unserved_kwh']:.2f} kWh")
    print(f"Critical Survival:       {s['critical_survival']}")
    print(f"Total Diesel Generation: {s['total_diesel_generated_kwh']:.2f} kWh")
    print(f"Total Fuel Consumed:     {s['total_fuel_burned_liters']:.2f} L")
    print(f"Final Fuel Remaining:    {s['final_fuel_remaining_liters']:.1f} L")
    print(f"Final Battery SOC:       {s['final_battery_soc'] * 100.0:.1f}%")
    print(f"Final Indoor Temp:       {s['final_indoor_temp_c']:.1f}°C")
    print(f"Threat Distribution:     {s['threat_state_distribution']}")
    print("----------------------------------------------------\n")

    if output_csv:
        out_path = Path(output_csv)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        traj_df.to_csv(out_path, index=False)
        print(f"Trajectory saved to {out_path} ({len(traj_df)} rows)")

    return trajectory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Polaris-EMS Digital Twin Simulation")
    parser.add_argument("--station", type=str, default="BHARATI", help="Station ID (BHARATI, MAITRI, HIMADRI)")
    parser.add_argument("--horizon", type=int, default=48, help="Simulation lead time in hours")
    parser.add_argument("--mode", type=str, default="EXPECTED", choices=["EXPECTED", "CONSERVATIVE", "OPTIMISTIC"], help="Trajectory mode")
    parser.add_argument("--output", type=str, default=None, help="Optional output CSV path")
    args = parser.parse_args()

    run_simulation(args.station, args.horizon, args.mode, args.output)
