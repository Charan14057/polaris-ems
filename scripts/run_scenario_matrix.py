"""
POLARIS-EMS — Scenario Matrix Runner
SIH26061: Polar Energy Management & Resilience System

Executes the locked set of 14 scenarios across Bharati, Maitri, and Himadri.
Generates structured comparative consequence reports and saves reports/phase5_scenario_matrix.csv.

Usage:
    python scripts/run_scenario_matrix.py
    python scripts/run_scenario_matrix.py --stations BHARATI MAITRI --horizon 48
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
from backend.scenarios.registry import ScenarioRegistry
from backend.scenarios.engine import ScenarioEngine
from backend.twin.forecast_adapter import TwinInputStep


def load_station_inputs(station_id: str, horizon_hours: int = 48):
    """Loads baseline slice inputs and initial telemetry for a station."""
    data_path = ROOT_DIR / "datasets" / f"{station_id.lower()}_14d_baseline.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    df = pd.read_csv(data_path)
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
        "indoor_temp_c": float(init_row.get("indoor_temp_c", 20.0))
    }

    steps = []
    h = 1
    for _, row in slice_df.iterrows():
        steps.append(TwinInputStep(
            timestamp=str(row.get("timestamp", f"T+{h}")),
            horizon_h=h,
            ambient_temp_c=float(row.get("temperature_c", -18.0)),
            wind_speed_m_per_s=float(row.get("wind_speed_ms", 10.0)),
            ghi_w_per_m2=float(row.get("irradiance_wm2", 0.0)),
            load_kw=float(row.get("total_load_kw", 40.0)),
            solar_kw=0.0,
            wind_kw=0.0,
            mode="EXPECTED",
            provenance="FORECAST"
        ))
        h += 1

    return initial_telem, str(init_row.get("timestamp", "2026-06-01T00:00:00Z")), steps


def run_matrix(stations: list = None, horizon_hours: int = 48, output_csv: str = None):
    stations = stations or ["BHARATI", "MAITRI", "HIMADRI"]
    profile_reg = StationProfileRegistry()
    safety_reg = SafetyThresholdRegistry()
    scenario_reg = ScenarioRegistry()

    scenario_ids = scenario_reg.list_ids()
    records = []

    print("\n=========================================================================")
    print("POLARIS-EMS — SCENARIO STRESS TESTING MATRIX")
    print(f"Stations: {', '.join(stations)} | Horizon: {horizon_hours}h | Scenarios: {len(scenario_ids)}")
    print("=========================================================================\n")

    for sid in stations:
        profile = profile_reg.get(sid)
        engine = ScenarioEngine(sid, profile, safety_reg, scenario_reg)
        initial_telem, init_ts, driving_inputs = load_station_inputs(sid, horizon_hours)
        init_state = engine.twin.initialize_twin(init_ts, initial_telem)

        print(f"--- Running 14 Scenarios for Station: {sid} ---")

        for scen_id in scenario_ids:
            res = engine.run_scenario(
                scenario_id=scen_id,
                initial_state=init_state,
                baseline_inputs=driving_inputs,
                forecast_mode="EXPECTED",
                horizon_hours=horizon_hours
            )

            metrics = res.impact_metrics
            s_sum = res.scenario_summary
            s_df = res.scenario_trajectory.to_dataframe()

            min_soc = round(s_df["battery_soc_pct"].min() * 100.0, 1) if not s_df.empty else 0.0
            min_res = round(s_df["dependable_reserve_pct"].min(), 1) if not s_df.empty else 0.0
            min_cont = round(s_df["continuity_horizon_hours"].min(), 1) if not s_df.empty else 0.0
            min_temp = round(s_df["indoor_temp_c"].min(), 1) if not s_df.empty else 0.0
            final_threat = res.resilience_status.get("threat_state", "UNKNOWN")

            records.append({
                "station_id": sid,
                "scenario_id": scen_id,
                "scenario_name": res.scenario_name,
                "duration_hours": res.duration_hours,
                "delta_fuel_liters": metrics.delta_fuel_burn_liters,
                "total_unserved_kwh": s_sum.get("total_unserved_kwh", 0.0),
                "critical_unserved_kwh": s_sum.get("total_critical_unserved_kwh", 0.0),
                "critical_survival": s_sum.get("critical_survival", "UNKNOWN"),
                "min_battery_soc_pct": min_soc,
                "min_reserve_margin_pct": min_res,
                "min_continuity_horizon_h": min_cont,
                "min_indoor_temp_c": min_temp,
                "final_threat_state": final_threat,
                "primary_failure_signature": res.primary_failure_signature
            })

            print(f"  [{scen_id:<27}] Survival: {s_sum.get('critical_survival'):<6} | Unserved: {s_sum.get('total_unserved_kwh'):>6.1f} kWh | Threat: {final_threat:<10} | Failure: {res.primary_failure_signature}")

    matrix_df = pd.DataFrame(records)

    out_path = Path(output_csv or (ROOT_DIR / "reports" / "phase5_scenario_matrix.csv"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_df.to_csv(out_path, index=False)
    print(f"\nSaved consolidated scenario matrix to: {out_path} ({len(matrix_df)} evaluations)\n")

    return matrix_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Polaris-EMS Scenario Matrix")
    parser.add_argument("--stations", nargs="+", default=["BHARATI", "MAITRI", "HIMADRI"], help="Station IDs")
    parser.add_argument("--horizon", type=int, default=48, help="Simulation lead time in hours")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    args = parser.parse_args()

    run_matrix(args.stations, args.horizon, args.output)
