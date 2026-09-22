"""
POLARIS-EMS — Digital Twin Diagnostic Plotting Suite
SIH26061: Polar Energy Management & Resilience System

Generates publication-quality 48-hour trajectory diagnostic plots:
- Dispatch power balance & flows
- Battery SOC dynamics vs limits
- Thermodynamic indoor habitability vs outdoor extreme cold
- Dependable reserve margins and threat state progressions

Outputs saved to docs/figures/phase4/
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.simulate_twin import run_simulation


def plot_trajectory_diagnostics(traj_df: pd.DataFrame, station_id: str, mode: str, output_path: Path):
    """Generates a 4-panel diagnostic chart of the simulated 48h trajectory."""
    fig, axes = plt.subplots(4, 1, figsize=(14, 16), sharex=True, gridspec_kw={'hspace': 0.25})
    hours = np.arange(1, len(traj_df) + 1)

    # Style settings
    plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
    plt.rcParams['axes.edgecolor'] = '#333333'
    plt.rcParams['axes.linewidth'] = 0.8

    # 1. Panel 1: Electrical Power Dispatch & Flow Balance
    ax1 = axes[0]
    ax1.plot(hours, traj_df['total_load_kw'], color='#111827', linewidth=2.0, label='Requested Load (kW)')
    ax1.plot(hours, traj_df['served_load_kw'], color='#2563EB', linewidth=1.5, linestyle='--', label='Served Load (kW)')
    ax1.plot(hours, traj_df['diesel_power_kw'], color='#DC2626', linewidth=1.8, label='Diesel Generator (kW)')
    ax1.plot(hours, traj_df['wind_generation_kw'], color='#059669', linewidth=1.5, label='Wind Turbine (kW)')
    if traj_df['solar_generation_kw'].max() > 0.01:
        ax1.plot(hours, traj_df['solar_generation_kw'], color='#D97706', linewidth=1.5, label='Solar PV (kW)')
    
    # Fill unserved if present
    if traj_df['unserved_load_kw'].max() > 0.01:
        ax1.fill_between(hours, traj_df['served_load_kw'], traj_df['total_load_kw'], color='#EF4444', alpha=0.4, label='Unserved Load (DEFICIT)')

    ax1.set_title(f"POLARIS-EMS Energy Digital Twin — {station_id} 48h Trajectory [{mode} Mode]\nDispatch Policy: BASELINE_SIMULATION_DISPATCH", fontsize=12, fontweight='bold', pad=10)
    ax1.set_ylabel("Power (kW)", fontsize=10, fontweight='semibold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', framealpha=0.9, fontsize=9, ncol=3)

    # 2. Panel 2: Battery Storage Dynamics & SOC Boundaries
    ax2 = axes[1]
    soc_pct = traj_df['battery_soc_pct'] * 100.0
    ax2.plot(hours, soc_pct, color='#7C3AED', linewidth=2.2, label='Battery SOC (%)')
    ax2.axhline(95.0, color='#9CA3AF', linestyle='--', linewidth=1.2, label='SOC Max Limit (95%)')
    ax2.axhline(20.0, color='#DC2626', linestyle='--', linewidth=1.2, label='SOC Min Cut-Off (20%)')
    ax2.axhline(25.0, color='#F59E0B', linestyle=':', linewidth=1.2, label='Warning Buffer (25%)')
    ax2.fill_between(hours, 20.0, 25.0, color='#F59E0B', alpha=0.15)
    ax2.set_ylabel("Battery SOC (%)", fontsize=10, fontweight='semibold')
    ax2.set_ylim(15.0, 100.0)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower right', framealpha=0.9, fontsize=9, ncol=4)

    # 3. Panel 3: Building Thermodynamics & Habitability
    ax3 = axes[2]
    ax3.plot(hours, traj_df['indoor_temp_c'], color='#EA580C', linewidth=2.2, label='Indoor Temperature (°C)')
    ax3.plot(hours, traj_df['ambient_temp_c'], color='#0284C7', linewidth=1.5, linestyle=':', label='Ambient Cold (°C)')
    min_safe_temp = 12.0 if station_id == "BHARATI" else (10.0 if station_id == "MAITRI" else 14.0)
    ax3.axhline(min_safe_temp, color='#DC2626', linestyle='--', linewidth=1.5, label=f'Min Safe Habitability ({min_safe_temp}°C)')
    ax3.fill_between(hours, min_safe_temp - 5, min_safe_temp, color='#DC2626', alpha=0.10)
    ax3.set_ylabel("Temperature (°C)", fontsize=10, fontweight='semibold')
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend(loc='lower right', framealpha=0.9, fontsize=9)

    # 4. Panel 4: Dependable Reserve Margin & Polar Threat State
    ax4 = axes[3]
    ax4.plot(hours, traj_df['dependable_reserve_pct'], color='#0D9488', linewidth=2.0, label='Dependable Reserve Margin (%)')
    ax4.axhline(30.0, color='#059669', linestyle=':', linewidth=1.2, label='Warning Margin (30%)')
    ax4.axhline(15.0, color='#DC2626', linestyle='--', linewidth=1.2, label='High-Risk Limit (15%)')
    
    # Colored background for threat states
    threat_colors = {
        "SAFE": "#DCFCE7",
        "AT_RISK": "#FEF3C7",
        "THREATENED": "#FFEDD5",
        "CRITICAL": "#FEE2E2"
    }
    for i in range(len(hours) - 1):
        ts = traj_df['threat_state'].iloc[i]
        c = threat_colors.get(ts, "#FFFFFF")
        ax4.axvspan(hours[i], hours[i+1], color=c, alpha=0.5, edgecolor=None)

    ax4.set_ylabel("Reserve Margin (%)", fontsize=10, fontweight='semibold')
    ax4.set_xlabel("Simulation Horizon (Hours)", fontsize=11, fontweight='bold')
    ax4.set_ylim(-20.0, max(100.0, traj_df['dependable_reserve_pct'].max() * 1.1))
    ax4.grid(True, linestyle=':', alpha=0.6)
    ax4.legend(loc='upper right', framealpha=0.9, fontsize=9)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Saved diagnostic chart to {output_path}")


def main():
    fig_dir = ROOT_DIR / "docs" / "figures" / "phase4"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("\n--- GENERATING PHASE 4 DIAGNOSTIC PLOTS ---")

    # 1. Bharati Expected 48h
    traj_b_exp = run_simulation("BHARATI", horizon_hours=48, mode="EXPECTED")
    plot_trajectory_diagnostics(traj_b_exp.to_dataframe(), "BHARATI", "EXPECTED", fig_dir / "bharati_48h_expected.png")

    # 2. Bharati Stress 48h
    traj_b_stress = run_simulation("BHARATI", horizon_hours=48, mode="CONSERVATIVE")
    plot_trajectory_diagnostics(traj_b_stress.to_dataframe(), "BHARATI", "CONSERVATIVE", fig_dir / "bharati_48h_conservative.png")

    # 3. Maitri Expected 48h
    traj_m_exp = run_simulation("MAITRI", horizon_hours=48, mode="EXPECTED")
    plot_trajectory_diagnostics(traj_m_exp.to_dataframe(), "MAITRI", "EXPECTED", fig_dir / "maitri_48h_expected.png")

    # 4. Himadri Expected 48h
    traj_h_exp = run_simulation("HIMADRI", horizon_hours=48, mode="EXPECTED")
    plot_trajectory_diagnostics(traj_h_exp.to_dataframe(), "HIMADRI", "EXPECTED", fig_dir / "himadri_48h_expected.png")

    print("\nAll Phase 4 diagnostic plots successfully created!\n")


if __name__ == "__main__":
    main()
