"""
POLARIS-EMS — Scenario Diagnostic Plotting Suite
SIH26061: Polar Energy Management & Resilience System

Generates comparative Baseline vs Scenario diagnostic plots:
- Load & Dispatch comparison
- Battery SOC degradation
- Building indoor temperature & habitability
- Threat state transitions and failure signatures

Outputs saved to docs/figures/phase5/
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.scenarios.registry import ScenarioRegistry
from backend.scenarios.engine import ScenarioEngine
from scripts.run_scenario_matrix import load_station_inputs


def plot_scenario_comparison(scenario_result, output_path: Path):
    """Generates a 4-panel comparative chart of Baseline vs Scenario trajectories."""
    b_df = scenario_result.baseline_trajectory.to_dataframe()
    s_df = scenario_result.scenario_trajectory.to_dataframe()
    hours = np.arange(1, len(b_df) + 1)
    scen_name = scenario_result.scenario_name
    sid = scenario_result.station_id

    fig, axes = plt.subplots(4, 1, figsize=(14, 16), sharex=True, gridspec_kw={'hspace': 0.25})

    # Style
    plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
    plt.rcParams['axes.edgecolor'] = '#333333'
    plt.rcParams['axes.linewidth'] = 0.8

    # Panel 1: Electrical Load & Generation Dispatch Comparison
    ax1 = axes[0]
    ax1.plot(hours, b_df['total_load_kw'], color='#4B5563', linewidth=1.5, linestyle=':', label='Baseline Load (kW)')
    ax1.plot(hours, s_df['total_load_kw'], color='#111827', linewidth=2.0, label='Scenario Load (kW)')
    ax1.plot(hours, b_df['diesel_power_kw'], color='#F87171', linewidth=1.2, linestyle='--', label='Baseline Diesel (kW)')
    ax1.plot(hours, s_df['diesel_power_kw'], color='#DC2626', linewidth=2.0, label='Scenario Diesel (kW)')
    if s_df['unserved_load_kw'].max() > 0.01:
        ax1.fill_between(hours, s_df['served_load_kw'], s_df['total_load_kw'], color='#EF4444', alpha=0.4, label='Unserved Deficit (kW)')

    ax1.set_title(f"POLARIS-EMS What-If Stress Analysis — {sid}\nBaseline vs {scen_name}", fontsize=12, fontweight='bold', pad=10)
    ax1.set_ylabel("Power (kW)", fontsize=10, fontweight='semibold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', framealpha=0.9, fontsize=9, ncol=3)

    # Panel 2: Battery SOC Dynamics Comparison
    ax2 = axes[1]
    ax2.plot(hours, b_df['battery_soc_pct'] * 100.0, color='#60A5FA', linewidth=1.5, linestyle='--', label='Baseline SOC (%)')
    ax2.plot(hours, s_df['battery_soc_pct'] * 100.0, color='#7C3AED', linewidth=2.2, label='Scenario SOC (%)')
    ax2.axhline(95.0, color='#9CA3AF', linestyle='--', linewidth=1.0)
    ax2.axhline(20.0, color='#DC2626', linestyle='--', linewidth=1.2, label='SOC Min (20%)')
    ax2.set_ylabel("Battery SOC (%)", fontsize=10, fontweight='semibold')
    ax2.set_ylim(15.0, 100.0)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower right', framealpha=0.9, fontsize=9)

    # Panel 3: Building Indoor Temperature & Habitability
    ax3 = axes[2]
    ax3.plot(hours, b_df['indoor_temp_c'], color='#34D399', linewidth=1.5, linestyle='--', label='Baseline Indoor (°C)')
    ax3.plot(hours, s_df['indoor_temp_c'], color='#EA580C', linewidth=2.2, label='Scenario Indoor (°C)')
    ax3.plot(hours, s_df['ambient_temp_c'], color='#0284C7', linewidth=1.2, linestyle=':', label='Scenario Ambient (°C)')
    min_safe = 12.0 if sid == "BHARATI" else (10.0 if sid == "MAITRI" else 14.0)
    ax3.axhline(min_safe, color='#DC2626', linestyle='--', linewidth=1.5, label=f'Safe Minimum ({min_safe}°C)')
    ax3.set_ylabel("Temperature (°C)", fontsize=10, fontweight='semibold')
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend(loc='lower right', framealpha=0.9, fontsize=9)

    # Panel 4: Dependable Reserve Margin & Threat State Transition
    ax4 = axes[3]
    ax4.plot(hours, b_df['dependable_reserve_pct'], color='#6B7280', linewidth=1.2, linestyle='--', label='Baseline Reserve (%)')
    ax4.plot(hours, s_df['dependable_reserve_pct'], color='#0D9488', linewidth=2.0, label='Scenario Reserve (%)')
    ax4.axhline(30.0, color='#059669', linestyle=':', linewidth=1.0, label='Warning Limit (30%)')
    ax4.axhline(15.0, color='#DC2626', linestyle='--', linewidth=1.2, label='High-Risk Limit (15%)')

    # Threat state shading for scenario
    threat_colors = {"SAFE": "#DCFCE7", "AT_RISK": "#FEF3C7", "THREATENED": "#FFEDD5", "CRITICAL": "#FEE2E2"}
    for i in range(len(hours) - 1):
        ts = s_df['threat_state'].iloc[i]
        ax4.axvspan(hours[i], hours[i+1], color=threat_colors.get(ts, "#FFFFFF"), alpha=0.5, edgecolor=None)

    ax4.set_ylabel("Reserve Margin (%)", fontsize=10, fontweight='semibold')
    ax4.set_xlabel("Simulation Horizon (Hours)", fontsize=11, fontweight='bold')
    ax4.grid(True, linestyle=':', alpha=0.6)
    ax4.legend(loc='upper right', framealpha=0.9, fontsize=9)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Saved scenario diagnostic chart to: {output_path}")


def main():
    fig_dir = ROOT_DIR / "docs" / "figures" / "phase5"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("\n--- GENERATING PHASE 5 SCENARIO DIAGNOSTIC PLOTS ---")

    profile_reg = StationProfileRegistry()
    safety_reg = SafetyThresholdRegistry()
    scenario_reg = ScenarioRegistry()

    engine = ScenarioEngine("BHARATI", profile_reg.get("BHARATI"), safety_reg, scenario_reg)
    initial_telem, init_ts, driving_inputs = load_station_inputs("BHARATI", horizon_hours=48)
    init_state = engine.twin.initialize_twin(init_ts, initial_telem)

    # 1. Blizzard Comparison
    res_blizzard = engine.run_scenario("BLIZZARD", init_state, driving_inputs, horizon_hours=48)
    plot_scenario_comparison(res_blizzard, fig_dir / "bharati_blizzard_comparison.png")

    # 2. Combined Polar Stress Comparison
    res_compound = engine.run_scenario("COMBINED_POLAR_STRESS", init_state, driving_inputs, horizon_hours=48)
    plot_scenario_comparison(res_compound, fig_dir / "bharati_combined_stress_comparison.png")

    # 3. Solar & Wind Failure Comparisons
    res_solar = engine.run_scenario("SOLAR_GENERATION_FAILURE", init_state, driving_inputs, horizon_hours=48)
    plot_scenario_comparison(res_solar, fig_dir / "bharati_solar_failure_comparison.png")

    res_wind = engine.run_scenario("WIND_GENERATION_FAILURE", init_state, driving_inputs, horizon_hours=48)
    plot_scenario_comparison(res_wind, fig_dir / "bharati_wind_failure_comparison.png")

    print("\nAll Phase 5 diagnostic charts successfully generated!\n")


if __name__ == "__main__":
    main()
