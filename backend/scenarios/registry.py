"""
POLARIS-EMS — Scenario Registry
SIH26061: Polar Energy Management & Resilience System

Maintains the authoritative catalog of the 14 locked polar stress scenarios.
Every predefined scenario declares explicit operator transformations, units,
duration, category, and engineering rationales.
"""

from typing import Dict, List, Optional
from backend.scenarios.schema import (
    ScenarioDefinition,
    ParameterTransform,
    TransformOperator,
    ScenarioCategory
)


class ScenarioRegistry:
    """Authoritative registry for predefined and custom polar stress scenarios."""

    def __init__(self):
        self._scenarios: Dict[str, ScenarioDefinition] = {}
        self._register_locked_scenarios()

    def _register_locked_scenarios(self):
        """Registers the 14 locked scenarios defined in the Master Prompt."""

        # 1. NORMAL_BASELINE
        self.register(ScenarioDefinition(
            scenario_id="NORMAL_BASELINE",
            name="Normal Operational Baseline",
            description="Unperturbed reference simulation trajectory under standard forecast conditions.",
            category=ScenarioCategory.ENVIRONMENTAL,
            duration_hours=48,
            transforms=[],
            active_effects=["baseline_reference"],
            provenance="CONFIGURED",
            rationale="Benchmark trajectory against which all stress scenarios are compared."
        ))

        # 2. CLOUDY_CONDITIONS
        self.register(ScenarioDefinition(
            scenario_id="CLOUDY_CONDITIONS",
            name="Cloudy Weather Conditions",
            description="Elevated cloud attenuation leading to reduced solar PV irradiance.",
            category=ScenarioCategory.ENVIRONMENTAL,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="cloud_fraction",
                    operator=TransformOperator.MULTIPLY,
                    value=1.5,
                    unit="fraction",
                    rationale="Stratus cloud deck increasing cloud attenuation factor."
                ),
                ParameterTransform(
                    parameter="irradiance_wm2",
                    operator=TransformOperator.MULTIPLY,
                    value=0.65,
                    unit="W/m2",
                    rationale="35% solar irradiance attenuation through cloud layer."
                )
            ],
            active_effects=["cloud_attenuation", "solar_reduction"],
            provenance="CONFIGURED",
            rationale="Frequent Antarctic summer cloud deck attenuating solar PV generation."
        ))

        # 3. HEAVY_CLOUD_LOW_IRRADIANCE
        self.register(ScenarioDefinition(
            scenario_id="HEAVY_CLOUD_LOW_IRRADIANCE",
            name="Heavy Cloud & Low Irradiance",
            description="Severe overcast cloud cover causing substantial solar irradiance shortfall.",
            category=ScenarioCategory.ENVIRONMENTAL,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="cloud_fraction",
                    operator=TransformOperator.MULTIPLY,
                    value=2.0,
                    unit="fraction",
                    rationale="Dense storm overcast."
                ),
                ParameterTransform(
                    parameter="irradiance_wm2",
                    operator=TransformOperator.MULTIPLY,
                    value=0.25,
                    unit="W/m2",
                    rationale="75% reduction in ground global horizontal irradiance."
                )
            ],
            active_effects=["dense_cloud", "severe_solar_reduction"],
            provenance="CONFIGURED",
            rationale="Severe overcast frontal system reducing PV generation to minimal levels."
        ))

        # 4. HIGH_WIND
        self.register(ScenarioDefinition(
            scenario_id="HIGH_WIND",
            name="High Wind & Katabatic Gusts",
            description="Elevated wind speeds testing aerodynamic power ramp and rated region limits.",
            category=ScenarioCategory.ENVIRONMENTAL,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="wind_speed_ms",
                    operator=TransformOperator.MULTIPLY,
                    value=1.4,
                    unit="m/s",
                    rationale="Katabatic wind surge across coastal ice shelf."
                )
            ],
            active_effects=["wind_amplification"],
            provenance="CONFIGURED",
            rationale="Antarctic katabatic wind surge testing turbine power ramp."
        ))

        # 5. BLIZZARD
        self.register(ScenarioDefinition(
            scenario_id="BLIZZARD",
            name="Polar Blizzard Storm",
            description="Coupled polar storm: temperature drop, gale-force winds with cut-out risk, and zero solar.",
            category=ScenarioCategory.COMPOUND,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="ambient_temperature_c",
                    operator=TransformOperator.ADD,
                    value=-10.0,
                    unit="deg_C",
                    rationale="Blizzard wind-chill temperature depression."
                ),
                ParameterTransform(
                    parameter="wind_speed_ms",
                    operator=TransformOperator.MULTIPLY,
                    value=2.0,
                    unit="m/s",
                    rationale="Storm gale winds pushing turbine toward emergency cut-out (25 m/s)."
                ),
                ParameterTransform(
                    parameter="cloud_fraction",
                    operator=TransformOperator.SET,
                    value=1.0,
                    unit="fraction",
                    rationale="Complete whiteout blizzard cloud cover."
                ),
                ParameterTransform(
                    parameter="irradiance_wm2",
                    operator=TransformOperator.SET,
                    value=0.0,
                    unit="W/m2",
                    rationale="Zero solar irradiance during dense blowing snow."
                )
            ],
            active_effects=["cold_front", "wind_gale", "solar_whiteout", "cutout_risk"],
            provenance="CONFIGURED",
            rationale="Typical polar blizzard causing coupled electrical, aerodynamic, and thermal stress."
        ))

        # 6. EXTREME_COLD
        self.register(ScenarioDefinition(
            scenario_id="EXTREME_COLD",
            name="Extreme Cold Wave",
            description="Deep sub-zero cold wave causing high building heat loss and battery cold derating.",
            category=ScenarioCategory.ENVIRONMENTAL,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="ambient_temperature_c",
                    operator=TransformOperator.ADD,
                    value=-20.0,
                    unit="deg_C",
                    rationale="Polar vortex plunge to -35°C to -45°C."
                )
            ],
            active_effects=["severe_cold", "thermal_loss_surge", "battery_cold_derate"],
            provenance="CONFIGURED",
            rationale="Mid-winter polar vortex drop testing building insulation and heating survival."
        ))

        # 7. LOW_DAYLIGHT
        self.register(ScenarioDefinition(
            scenario_id="LOW_DAYLIGHT",
            name="Low Daylight Exposure",
            description="Atmospheric obstruction reducing solar opportunity while preserving astronomical geometry.",
            category=ScenarioCategory.ENVIRONMENTAL,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="irradiance_wm2",
                    operator=TransformOperator.MULTIPLY,
                    value=0.30,
                    unit="W/m2",
                    rationale="Heavy atmospheric haze reducing solar irradiance."
                ),
                ParameterTransform(
                    parameter="solar_availability",
                    operator=TransformOperator.MULTIPLY,
                    value=0.40,
                    unit="fraction",
                    rationale="Low daylight opportunity; astronomical solar elevation remains unchanged."
                )
            ],
            active_effects=["daylight_reduction"],
            provenance="CONFIGURED",
            rationale="Seasonal low daylight and atmospheric scattering reducing solar availability."
        ))

        # 8. POLAR_NIGHT
        self.register(ScenarioDefinition(
            scenario_id="POLAR_NIGHT",
            name="Astronomical Polar Night",
            description="Winter polar night regime where the Sun remains below the horizon continuously.",
            category=ScenarioCategory.ENVIRONMENTAL,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="irradiance_wm2",
                    operator=TransformOperator.SET,
                    value=0.0,
                    unit="W/m2",
                    rationale="True astronomical night zero solar irradiance."
                ),
                ParameterTransform(
                    parameter="solar_elevation_deg",
                    operator=TransformOperator.SET,
                    value=-5.0,
                    unit="deg",
                    rationale="Sun below horizon during astronomical polar night."
                )
            ],
            active_effects=["zero_solar", "polar_night"],
            provenance="CONFIGURED",
            rationale="Continuous polar night regime requiring 100% dispatchable power."
        ))

        # 9. SOLAR_GENERATION_FAILURE
        self.register(ScenarioDefinition(
            scenario_id="SOLAR_GENERATION_FAILURE",
            name="Solar PV System Trip",
            description="Inverter fault or DC bus breaker trip causing immediate loss of all solar generation.",
            category=ScenarioCategory.ASSET_FAILURE,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="solar_availability",
                    operator=TransformOperator.DISABLE,
                    value=0.0,
                    unit="fraction",
                    rationale="Solar inverter hardware failure."
                )
            ],
            active_effects=["solar_failure"],
            provenance="CONFIGURED",
            rationale="Hardware breaker trip on main solar inverter array."
        ))

        # 10. WIND_GENERATION_FAILURE
        self.register(ScenarioDefinition(
            scenario_id="WIND_GENERATION_FAILURE",
            name="Wind Turbine Mechanical Trip",
            description="Turbine mechanical failure or pitch actuator jam rendering turbine unavailable.",
            category=ScenarioCategory.ASSET_FAILURE,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="wind_availability",
                    operator=TransformOperator.DISABLE,
                    value=0.0,
                    unit="fraction",
                    rationale="Mechanical pitch jam or gearbox fault."
                )
            ],
            active_effects=["wind_failure"],
            provenance="CONFIGURED",
            rationale="Wind turbine mechanical shutdown requiring diesel and battery backup."
        ))

        # 11. BATTERY_DEGRADATION
        self.register(ScenarioDefinition(
            scenario_id="BATTERY_DEGRADATION",
            name="Battery Capacity Degradation",
            description="Electrochemical cell aging or sub-module fault reducing usable battery storage capacity.",
            category=ScenarioCategory.ASSET_FAILURE,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="battery_capacity",
                    operator=TransformOperator.MULTIPLY,
                    value=0.65,
                    unit="fraction",
                    rationale="Battery usable capacity degraded to 65% of rated."
                )
            ],
            active_effects=["battery_degradation"],
            provenance="CONFIGURED",
            rationale="Degraded BESS capacity due to sub-zero cycling stress."
        ))

        # 12. FUEL_RESUPPLY_DELAY
        self.register(ScenarioDefinition(
            scenario_id="FUEL_RESUPPLY_DELAY",
            name="Fuel Resupply Delay (7 Days)",
            description="Resupply vessel or convoy delayed by 7 days (+168h), testing fuel stock autonomy.",
            category=ScenarioCategory.LOGISTICS,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="fuel_resupply_delay_hours",
                    operator=TransformOperator.DELAY,
                    value=168.0,
                    unit="hours",
                    rationale="7-day sea ice blockage delaying polar fuel delivery vessel."
                )
            ],
            active_effects=["resupply_delay"],
            provenance="CONFIGURED",
            rationale="Sea ice congestion preventing tanker mooring at Bharati/Maitri."
        ))

        # 13. COMBINED_POLAR_STRESS
        self.register(ScenarioDefinition(
            scenario_id="COMBINED_POLAR_STRESS",
            name="Combined Polar Stress Disaster",
            description="Compound disaster combining severe cold, blizzard gale, zero renewables, and resupply delay.",
            category=ScenarioCategory.COMPOUND,
            duration_hours=48,
            transforms=[
                ParameterTransform(
                    parameter="ambient_temperature_c",
                    operator=TransformOperator.ADD,
                    value=-15.0,
                    unit="deg_C",
                    rationale="Severe polar cold wave."
                ),
                ParameterTransform(
                    parameter="wind_speed_ms",
                    operator=TransformOperator.SET,
                    value=30.0,
                    unit="m/s",
                    rationale="Blizzard winds at 30 m/s triggering storm cut-out (25 m/s)."
                ),
                ParameterTransform(
                    parameter="cloud_fraction",
                    operator=TransformOperator.SET,
                    value=1.0,
                    unit="fraction",
                    rationale="Total overcast whiteout."
                ),
                ParameterTransform(
                    parameter="irradiance_wm2",
                    operator=TransformOperator.SET,
                    value=0.0,
                    unit="W/m2",
                    rationale="Zero solar irradiance."
                ),
                ParameterTransform(
                    parameter="solar_availability",
                    operator=TransformOperator.DISABLE,
                    value=0.0,
                    unit="fraction",
                    rationale="Solar PV system tripped."
                ),
                ParameterTransform(
                    parameter="fuel_resupply_delay_hours",
                    operator=TransformOperator.DELAY,
                    value=168.0,
                    unit="hours",
                    rationale="7-day resupply convoy delay."
                )
            ],
            active_effects=["extreme_cold", "blizzard", "zero_renewables", "resupply_delay"],
            provenance="CONFIGURED",
            rationale="Worst-case polar emergency evaluating multi-tier station survivability."
        ))

        # 14. CUSTOM
        self.register(ScenarioDefinition(
            scenario_id="CUSTOM",
            name="Custom Scenario Exploration",
            description="User-defined validated scenario with customizable parameter overrides.",
            category=ScenarioCategory.CUSTOM,
            duration_hours=48,
            transforms=[],
            active_effects=["custom_exploration"],
            provenance="CONFIGURED",
            rationale="User-controlled what-if stress exploration."
        ))

    def register(self, scenario: ScenarioDefinition) -> None:
        """Registers a scenario definition."""
        self._scenarios[scenario.scenario_id.upper()] = scenario

    def get(self, scenario_id: str) -> ScenarioDefinition:
        """Retrieves a scenario definition by ID."""
        sid = scenario_id.upper()
        if sid not in self._scenarios:
            raise KeyError(f"Scenario '{scenario_id}' not found. Available: {list(self._scenarios.keys())}")
        return self._scenarios[sid]

    def list_scenarios(self) -> List[ScenarioDefinition]:
        """Returns all registered scenarios."""
        return list(self._scenarios.values())

    def list_ids(self) -> List[str]:
        """Returns all registered scenario IDs."""
        return list(self._scenarios.keys())
