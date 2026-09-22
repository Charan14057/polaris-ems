"""
POLARIS-EMS — Scenario Validator
SIH26061: Polar Energy Management & Resilience System

Validates scenario definitions, parameter overrides, and proxy inputs before simulation.
Rejects impossible, negative, or physically inconsistent stress configurations.
"""

from typing import Dict, List, Any
from backend.scenarios.schema import ScenarioDefinition, ParameterTransform, TransformOperator


class ScenarioValidationError(ValueError):
    """Raised when a scenario definition or parameter configuration violates physical bounds."""
    pass


class ScenarioValidator:
    """Enforces strict physical bounds and logical consistency checks on scenario definitions."""

    # Recognized simulation proxy parameters
    VALID_PARAMETERS = {
        "ambient_temperature_c",
        "wind_speed_ms",
        "cloud_fraction",
        "irradiance_wm2",
        "solar_elevation_deg",
        "solar_availability",
        "wind_availability",
        "battery_capacity",
        "battery_initial_soc",
        "fuel_available",
        "fuel_resupply_delay_hours",
        "generator_availability",
        "load_multiplier",
        "occupancy_modifier",
        "maintenance_modifier"
    }

    @classmethod
    def validate_scenario(cls, scenario: ScenarioDefinition) -> None:
        """
        Validates the complete scenario definition.
        Raises ScenarioValidationError on any invalid configuration.
        """
        if not scenario.scenario_id or not isinstance(scenario.scenario_id, str):
            raise ScenarioValidationError("Scenario must have a valid non-empty string scenario_id.")

        if scenario.duration_hours <= 0 or scenario.duration_hours > 720:
            raise ScenarioValidationError(
                f"duration_hours must be between 1 and 720 hours (30 days), got {scenario.duration_hours}."
            )

        if scenario.start_offset_hours < 0:
            raise ScenarioValidationError(
                f"start_offset_hours cannot be negative, got {scenario.start_offset_hours}."
            )

        for transform in scenario.transforms:
            cls.validate_transform(transform)

    @classmethod
    def validate_transform(cls, transform: ParameterTransform) -> None:
        """Validates an individual parameter transform."""
        param = transform.parameter
        if param not in cls.VALID_PARAMETERS:
            raise ScenarioValidationError(
                f"Unrecognized scenario parameter '{param}'. Allowed: {sorted(cls.VALID_PARAMETERS)}"
            )

        op = transform.operator
        val = transform.value

        # Operator validations
        if op == TransformOperator.DISABLE:
            return  # Disabling an asset is always valid

        if op in [TransformOperator.MULTIPLY, TransformOperator.SET, TransformOperator.ADD, TransformOperator.MIN, TransformOperator.MAX, TransformOperator.DELAY]:
            if not isinstance(val, (int, float)):
                raise ScenarioValidationError(
                    f"Operator '{op}' requires numeric value for parameter '{param}', got {type(val)}: {val}"
                )

        num_val = float(val) if isinstance(val, (int, float)) else 0.0

        # Parameter-specific physical bounds
        if param == "cloud_fraction":
            if op == TransformOperator.SET and not (0.0 <= num_val <= 1.0):
                raise ScenarioValidationError(f"cloud_fraction SET value must be in [0.0, 1.0], got {num_val}.")
            if op == TransformOperator.MULTIPLY and num_val < 0.0:
                raise ScenarioValidationError(f"cloud_fraction MULTIPLY value cannot be negative, got {num_val}.")

        elif param == "wind_speed_ms":
            if op == TransformOperator.MULTIPLY and num_val < 0.0:
                raise ScenarioValidationError(f"wind_speed_ms MULTIPLY cannot be negative, got {num_val}.")
            if op == TransformOperator.SET and not (0.0 <= num_val <= 100.0):
                raise ScenarioValidationError(f"wind_speed_ms SET must be in [0.0, 100.0 m/s], got {num_val}.")

        elif param == "irradiance_wm2":
            if op == TransformOperator.MULTIPLY and num_val < 0.0:
                raise ScenarioValidationError(f"irradiance_wm2 MULTIPLY cannot be negative, got {num_val}.")
            if op == TransformOperator.SET and not (0.0 <= num_val <= 1500.0):
                raise ScenarioValidationError(f"irradiance_wm2 SET must be in [0.0, 1500.0 W/m2], got {num_val}.")

        elif param == "ambient_temperature_c":
            if op == TransformOperator.SET and not (-90.0 <= num_val <= 35.0):
                raise ScenarioValidationError(f"ambient_temperature_c SET must be in [-90.0, 35.0 deg_C], got {num_val}.")

        elif param == "fuel_resupply_delay_hours":
            if num_val < 0.0:
                raise ScenarioValidationError(f"fuel_resupply_delay_hours cannot be negative, got {num_val}.")

        elif param == "battery_capacity":
            if op == TransformOperator.MULTIPLY and (num_val <= 0.0 or num_val > 2.0):
                raise ScenarioValidationError(f"battery_capacity multiplier must be in (0.0, 2.0], got {num_val}.")

        elif param == "battery_initial_soc":
            if op == TransformOperator.SET and not (0.0 <= num_val <= 1.0):
                raise ScenarioValidationError(f"battery_initial_soc must be in [0.0, 1.0], got {num_val}.")

        elif param == "generator_availability":
            if not (0.0 <= num_val <= 1.0):
                raise ScenarioValidationError(f"generator_availability must be in [0.0, 1.0], got {num_val}.")

        elif param == "load_multiplier":
            if num_val < 0.0 or num_val > 5.0:
                raise ScenarioValidationError(f"load_multiplier must be in [0.0, 5.0], got {num_val}.")

    @classmethod
    def validate_custom_overrides(cls, overrides: Dict[str, Any]) -> None:
        """Validates a dictionary of custom parameter overrides."""
        for param, val in overrides.items():
            if param not in cls.VALID_PARAMETERS:
                raise ScenarioValidationError(f"Custom override parameter '{param}' is unrecognized.")
            # Synthesize a temporary transform to check bounds
            cls.validate_transform(ParameterTransform(
                parameter=param,
                operator=TransformOperator.SET if isinstance(val, (int, float)) else TransformOperator.DISABLE,
                value=val,
                unit=""
            ))
