"""
POLARIS-EMS — Digital Twin Thermal Subsystem Engine
SIH26061: Polar Energy Management & Resilience System

Simulates the persistent thermodynamic state transition of the station building:
T_indoor(t+1) = T_indoor(t) + (dt / C_th) * (Q_in - Q_loss)
Where:
Q_loss = UA * (T_indoor - T_ambient) * (1 + ventilation_loss_coeff)
Q_in = P_heating + internal_heat_gains + Q_chp_recovered (optional=0.0)
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np

from backend.twin.state import ThermalState
from backend.twin.safety_thresholds import SafetyThresholdRegistry


class ThermalEngine:
    """Manages building thermal mass thermodynamics and heating demand evolution."""

    def __init__(self, safety_registry: Optional[SafetyThresholdRegistry] = None):
        self.safety_registry = safety_registry or SafetyThresholdRegistry()

    def calculate_heating_demand(
        self,
        thermal_state: ThermalState,
        ambient_temp_c: float
    ) -> Tuple[float, float]:
        """
        Calculates thermal heat loss (Q_loss) and required electric heating power to meet setpoint.
        
        Returns:
            (required_heating_kw, thermal_loss_kw)
        """
        # Temperature difference across building envelope
        temp_diff = max(0.0, thermal_state.thermal_setpoint_c - ambient_temp_c)
        ua_loss = thermal_state.building_ua_kw_per_k * temp_diff
        vent_loss = ua_loss * thermal_state.ventilation_loss_coeff
        total_q_loss = ua_loss + vent_loss

        # Required electric heating power (after internal gains and optional CHP)
        net_heating_kw = max(
            0.0,
            total_q_loss - thermal_state.internal_heat_gain_kw - thermal_state.chp_heat_recovered_kw
        )
        return float(round(net_heating_kw, 2)), float(round(total_q_loss, 2))

    def step(
        self,
        current_state: ThermalState,
        ambient_temp_c: float,
        actual_heating_power_kw: float,
        dt_hours: float = 1.0
    ) -> ThermalState:
        """
        Executes discrete thermal state update:
        T_next = T_current + (dt / C_th) * (Q_in - Q_loss)
        """
        # Actual heat loss based on current indoor temperature
        temp_gradient = current_state.indoor_temperature_c - ambient_temp_c
        ua_loss = current_state.building_ua_kw_per_k * max(0.0, temp_gradient)
        vent_loss = ua_loss * current_state.ventilation_loss_coeff
        q_loss = ua_loss + vent_loss

        # Total heat into the building volume
        q_in = (
            actual_heating_power_kw
            + current_state.internal_heat_gain_kw
            + current_state.chp_heat_recovered_kw
        )

        net_heat_flow = q_in - q_loss  # kWh / h

        # Thermal persistence update
        c_th = max(1.0, current_state.thermal_capacitance_kwh_per_k)
        delta_temp = (net_heat_flow * dt_hours) / c_th

        # Evolution bounded by realistic physical ranges (prevents infinite runaway)
        new_indoor_temp = float(np.clip(
            current_state.indoor_temperature_c + delta_temp,
            -30.0,
            current_state.thermal_setpoint_c + 5.0
        ))

        is_safe = new_indoor_temp >= current_state.indoor_min_safe_temp_c

        return ThermalState(
            indoor_temperature_c=round(new_indoor_temp, 2),
            thermal_setpoint_c=current_state.thermal_setpoint_c,
            indoor_min_safe_temp_c=current_state.indoor_min_safe_temp_c,
            building_ua_kw_per_k=current_state.building_ua_kw_per_k,
            thermal_capacitance_kwh_per_k=current_state.thermal_capacitance_kwh_per_k,
            ventilation_loss_coeff=current_state.ventilation_loss_coeff,
            internal_heat_gain_kw=current_state.internal_heat_gain_kw,
            heating_power_kw=round(actual_heating_power_kw, 2),
            thermal_loss_kw=round(q_loss, 2),
            chp_heat_recovered_kw=current_state.chp_heat_recovered_kw,
            is_safe=is_safe,
            provenance="SIMULATED"
        )
