"""
POLARIS-EMS — Digital Twin Battery Subsystem Engine
SIH26061: Polar Energy Management & Resilience System

Simulates electrochemical energy storage dynamics with polar cold temperature derating:
- Temperature derating reduces usable capacity under sub-zero conditions
- Square-root roundtrip efficiency splitting for charge and discharge
- Physical SOC enforcement: SOC_min <= SOC <= SOC_max
- Energy conservation: delta_E = P_charge * eta_chg * dt - (P_discharge / eta_dis) * dt
"""

from typing import Tuple, Optional
import numpy as np

from backend.twin.state import BatteryState
from backend.data.station_profiles.loader import StationProfile


class BatteryEngine:
    """Manages electrochemical storage states, temperature derating, and power limits."""

    def __init__(self, profile: StationProfile):
        self.profile = profile
        self.b_spec = profile.electrical

    def compute_derating(self, ambient_temp_c: float, nominal_capacity_kwh: Optional[float] = None) -> Tuple[float, float]:
        """
        Calculates temperature derating factor and current usable capacity in kWh.
        """
        base_cap = float(nominal_capacity_kwh if nominal_capacity_kwh is not None else self.b_spec.battery_capacity_kwh)
        derate_coeff = float(self.b_spec.battery_cold_derate_coeff)
        # Derating kicks in below -10°C, capped at 30% reduction (derate >= 0.70)
        derate = max(0.70, 1.0 - derate_coeff * max(0.0, -10.0 - ambient_temp_c))
        usable_kwh = float(base_cap * derate)
        return float(round(derate, 4)), float(round(usable_kwh, 2))

    def get_dispatch_limits(
        self,
        current_state: BatteryState,
        ambient_temp_c: float,
        dt_hours: float = 1.0
    ) -> Tuple[float, float]:
        """
        Calculates maximum possible charge power (kW) and discharge power (kW)
        for the current timestep based on SOC room, inverter ratings, and efficiencies.
        
        Returns:
            (max_charge_kw, max_discharge_kw)
        """
        _, usable_kwh = self.compute_derating(ambient_temp_c, nominal_capacity_kwh=current_state.capacity_kwh)
        eta_chg = current_state.charge_efficiency
        eta_dis = current_state.discharge_efficiency

        # Room to charge up to SOC_max
        room_kwh = max(0.0, (current_state.soc_max - current_state.soc_pct) * usable_kwh)
        max_chg_kw = min(
            float(self.b_spec.battery_max_charge_kw),
            (room_kwh / max(0.01, eta_chg)) / max(0.01, dt_hours)
        )

        # Available energy to discharge down to SOC_min
        avail_kwh = max(0.0, (current_state.soc_pct - current_state.soc_min) * usable_kwh)
        max_dis_kw = min(
            float(self.b_spec.battery_max_discharge_kw),
            (avail_kwh * eta_dis) / max(0.01, dt_hours)
        )

        return float(round(max_chg_kw, 2)), float(round(max_dis_kw, 2))

    def step(
        self,
        current_state: BatteryState,
        ambient_temp_c: float,
        charge_kw: float,
        discharge_kw: float,
        dt_hours: float = 1.0
    ) -> BatteryState:
        """
        Executes discrete state transition for the battery storage.
        """
        cap_kwh = current_state.capacity_kwh
        derate, usable_kwh = self.compute_derating(ambient_temp_c, nominal_capacity_kwh=cap_kwh)
        eta_chg = current_state.charge_efficiency
        eta_dis = current_state.discharge_efficiency

        min_soc = current_state.soc_min
        max_soc = current_state.soc_max
        min_energy = min_soc * usable_kwh
        max_energy = max_soc * usable_kwh

        # Net energy transferred into the chemical cells
        delta_e_kwh = (
            charge_kw * eta_chg * dt_hours
            - (discharge_kw / max(0.01, eta_dis)) * dt_hours
        )

        new_energy_kwh = current_state.energy_kwh + delta_e_kwh
        new_soc = new_energy_kwh / max(1.0, usable_kwh)

        # Numerical clamping to physical limits (SOC_min <= SOC <= SOC_max)
        clamped_soc = float(np.clip(new_soc, min_soc, max_soc))
        clamped_energy = float(np.clip(new_energy_kwh, min_energy, max_energy))

        return BatteryState(
            soc_pct=round(clamped_soc, 4),
            energy_kwh=round(clamped_energy, 2),
            charge_kw=round(charge_kw, 2),
            discharge_kw=round(discharge_kw, 2),
            capacity_kwh=cap_kwh,
            usable_capacity_kwh=usable_kwh,
            charge_efficiency=eta_chg,
            discharge_efficiency=eta_dis,
            temperature_derating=derate,
            soc_min=current_state.soc_min,
            soc_max=current_state.soc_max,
            provenance="SIMULATED"
        )
