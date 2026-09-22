"""
POLARIS-EMS — Composable Scenario Transformation Framework
SIH26061: Polar Energy Management & Resilience System

Transforms physical and operational driving inputs under explicit mathematical operators:
SET | ADD | MULTIPLY | MIN | MAX | DELAY | DISABLE

Guarantees:
1. Astronomical solar elevation is never altered under LOW_DAYLIGHT (Correction #1).
2. Input lineage is strictly maintained: original FORECAST preserved, effective inputs tagged SIMULATED (Correction #3).
3. Resupply delays shift fuel delivery timing to re-evaluate continuity (Phase 4 Hardening #2).
"""

from typing import List, Dict, Any, Tuple
import copy

from backend.scenarios.schema import (
    ScenarioDefinition,
    ParameterTransform,
    TransformOperator
)
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep


def apply_operator(base_val: float, operator: TransformOperator, operand: float) -> float:
    """Applies an explicit mathematical transformation operator to a base value."""
    if operator == TransformOperator.SET:
        return float(operand)
    elif operator == TransformOperator.ADD:
        return float(base_val + operand)
    elif operator == TransformOperator.MULTIPLY:
        return float(base_val * operand)
    elif operator == TransformOperator.MIN:
        return float(min(base_val, operand))
    elif operator == TransformOperator.MAX:
        return float(max(base_val, operand))
    elif operator == TransformOperator.DELAY:
        return float(base_val + operand)
    elif operator == TransformOperator.DISABLE:
        return 0.0
    return float(base_val)


class ScenarioTransformer:
    """Composes and executes physical scenario transformations on Twin states and driving inputs."""

    def __init__(self, scenario: ScenarioDefinition):
        self.scenario = scenario

    def transform(
        self,
        initial_state: TwinState,
        driving_steps: List[TwinInputStep]
    ) -> Tuple[TwinState, List[TwinInputStep]]:
        """
        Executes scenario transformations, returning:
        1. Transformed initial TwinState (with overrides for initial SOC, capacity, generator availability, or fuel).
        2. Transformed List[TwinInputStep] with provenance='SIMULATED' preserving original forecast lineage.
        """
        # Deepcopy to prevent mutating baseline reference
        t_state = copy.deepcopy(initial_state)
        t_steps = copy.deepcopy(driving_steps)

        # 1. Apply Initial State Overrides (Battery, Fuel, Resupply, Generator Asset)
        for t in self.scenario.transforms:
            param = t.parameter
            op = t.operator
            val = float(t.value) if isinstance(t.value, (int, float)) else 0.0

            if param == "battery_capacity":
                t_state.battery.capacity_kwh = apply_operator(t_state.battery.capacity_kwh, op, val)
                t_state.battery.usable_capacity_kwh = apply_operator(t_state.battery.usable_capacity_kwh, op, val)
                t_state.battery.energy_kwh = min(t_state.battery.energy_kwh, t_state.battery.usable_capacity_kwh)

            elif param == "battery_initial_soc":
                new_soc = apply_operator(t_state.battery.soc_pct, op, val)
                t_state.battery.soc_pct = max(0.0, min(1.0, new_soc))
                t_state.battery.energy_kwh = t_state.battery.soc_pct * t_state.battery.usable_capacity_kwh

            elif param == "fuel_available":
                t_state.fuel.fuel_remaining_l = max(0.0, apply_operator(t_state.fuel.fuel_remaining_l, op, val))

            elif param == "generator_availability":
                # Scale generator max power rating
                avail_factor = max(0.0, min(1.0, apply_operator(1.0, op, val)))
                t_state.diesel.generator_max_power_kw = round(t_state.diesel.generator_max_power_kw * avail_factor, 2)
                if avail_factor <= 0.01:
                    t_state.diesel.generator_status = "FAULT"
                    t_state.diesel.generator_power_kw = 0.0

            elif param == "fuel_resupply_delay_hours":
                # Shift resupply window
                delay_days = round(val / 24.0, 1)
                t_state.resupply.resupply_window_days += int(delay_days)
                t_state.resupply.resupply_event_active = False  # Deactivate baseline event during delay

        # 2. Apply Time-Series Driving Input Transforms (Weather, Load, Renewable Availability)
        for step in t_steps:
            # Tag transformed input as SIMULATED to preserve lineage
            step.provenance = "SIMULATED"

            for t in self.scenario.transforms:
                param = t.parameter
                op = t.operator
                val = float(t.value) if isinstance(t.value, (int, float)) else 0.0

                if param == "ambient_temperature_c":
                    step.ambient_temp_c = round(apply_operator(step.ambient_temp_c, op, val), 2)

                elif param == "wind_speed_ms":
                    step.wind_speed_m_per_s = max(0.0, round(apply_operator(step.wind_speed_m_per_s, op, val), 2))

                elif param == "irradiance_wm2":
                    step.ghi_w_per_m2 = max(0.0, round(apply_operator(step.ghi_w_per_m2, op, val), 2))

                elif param == "load_multiplier":
                    step.load_kw = max(0.0, round(apply_operator(step.load_kw, op, val), 2))

                elif param == "solar_availability":
                    # Reduces or zeroes solar power potential
                    avail_factor = max(0.0, min(1.0, apply_operator(1.0, op, val)))
                    step.solar_kw = round(step.solar_kw * avail_factor, 2)
                    if avail_factor <= 0.001:
                        step.ghi_w_per_m2 = 0.0  # Zero irradiance if solar disabled

                elif param == "wind_availability":
                    # Reduces or zeroes wind power potential
                    avail_factor = max(0.0, min(1.0, apply_operator(1.0, op, val)))
                    step.wind_kw = round(step.wind_kw * avail_factor, 2)
                    if avail_factor <= 0.001:
                        step.wind_speed_m_per_s = 0.0

                elif param == "cloud_fraction":
                    # Cloud attenuation directly reduces irradiance
                    cloud_mult = max(0.0, apply_operator(1.0, op, val))
                    step.ghi_w_per_m2 = max(0.0, round(step.ghi_w_per_m2 / max(0.1, cloud_mult), 2))

        return t_state, t_steps
