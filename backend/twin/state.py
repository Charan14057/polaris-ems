"""
POLARIS-EMS — Digital Twin State Model & Field-Level Provenance
SIH26061: Polar Energy Management & Resilience System

Defines strongly typed state representations for all station subsystems:
Environment, Thermal, Load, Solar, Wind, Battery, Diesel, Fuel, Resupply, Operational,
Constraints, and Resilience. Enforces field-level provenance tracking.
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime


ProvenanceTier = Literal["OBSERVED", "FORECAST", "CONFIGURED", "ASSUMED", "SIMULATED"]


@dataclass
class ProvenanceRecord:
    tier: ProvenanceTier
    source: str
    timestamp: str


@dataclass
class EnvironmentState:
    ambient_temperature_c: float
    wind_speed_ms: float
    irradiance_wm2: float
    pressure_hpa: float = 1013.25
    humidity_pct: float = 75.0
    cloud_fraction: float = 0.5
    solar_elevation_deg: float = 0.0
    storm_state: str = "NORMAL"
    provenance: ProvenanceTier = "SIMULATED"

    @property
    def temperature_c(self) -> float:
        return self.ambient_temperature_c

    @property
    def wind_speed_m_per_s(self) -> float:
        return self.wind_speed_ms

    @property
    def ghi_w_per_m2(self) -> float:
        return self.irradiance_wm2


@dataclass
class ThermalState:
    indoor_temperature_c: float
    thermal_setpoint_c: float
    indoor_min_safe_temp_c: float
    building_ua_kw_per_k: float
    thermal_capacitance_kwh_per_k: float
    ventilation_loss_coeff: float
    internal_heat_gain_kw: float
    heating_power_kw: float = 0.0
    thermal_loss_kw: float = 0.0
    chp_heat_recovered_kw: float = 0.0  # Optional, default 0.0
    is_safe: bool = True
    provenance: ProvenanceTier = "SIMULATED"

    @property
    def indoor_temp_c(self) -> float:
        return self.indoor_temperature_c


@dataclass
class LoadState:
    thermal_load_kw: float
    critical_load_kw: float
    important_load_kw: float
    operational_load_kw: float
    flexible_load_kw: float
    maintenance_load_kw: float
    total_load_kw: float
    served_load_kw: float = 0.0
    unserved_load_kw: float = 0.0
    served_critical_kw: float = 0.0
    unserved_critical_kw: float = 0.0
    provenance: ProvenanceTier = "SIMULATED"

    @property
    def unserved_total_kw(self) -> float:
        return self.unserved_load_kw

    @property
    def unserved_non_critical_kw(self) -> float:
        return max(0.0, self.unserved_load_kw - self.unserved_critical_kw)


@dataclass
class SolarState:
    solar_available_kw: float
    solar_generation_kw: float
    solar_curtailed_kw: float
    solar_capacity_kw: float
    solar_status: str  # "ONLINE" | "NIGHT" | "CURTAILED" | "FAULT"
    provenance: ProvenanceTier = "SIMULATED"


@dataclass
class WindState:
    wind_available_kw: float
    wind_generation_kw: float
    wind_curtailed_kw: float
    wind_capacity_kw: float
    wind_status: str  # "BELOW_CUT_IN" | "OPERATING_RAMP" | "OPERATING_RATED" | "STORM_CUT_OUT" | "FAULT"
    provenance: ProvenanceTier = "SIMULATED"


@dataclass
class BatteryState:
    soc_pct: float
    energy_kwh: float
    charge_kw: float
    discharge_kw: float
    capacity_kwh: float
    usable_capacity_kwh: float
    charge_efficiency: float
    discharge_efficiency: float
    temperature_derating: float
    soc_min: float
    soc_max: float
    provenance: ProvenanceTier = "SIMULATED"

    @property
    def charge_power_kw(self) -> float:
        return self.charge_kw

    @property
    def discharge_power_kw(self) -> float:
        return self.discharge_kw

    @property
    def max_charge_kw(self) -> float:
        return self.capacity_kwh * 0.5  # Inverter max charge rating proxy if accessed directly

    @property
    def max_discharge_kw(self) -> float:
        return self.capacity_kwh * 0.5  # Inverter max discharge rating proxy if accessed directly


@dataclass
class DieselState:
    generator_status: str  # "ONLINE" | "STANDBY" | "MAINTENANCE" | "FAULT"
    online_count: int
    generator_power_kw: float
    generator_min_power_kw: float
    generator_max_power_kw: float
    fuel_consumption_l_per_h: float
    cumulative_runtime_h: float = 0.0
    provenance: ProvenanceTier = "SIMULATED"


@dataclass
class FuelState:
    fuel_remaining_l: float
    fuel_initial_l: float
    fuel_consumed_l: float
    fuel_reserve_l: float
    fuel_capacity_l: float
    days_of_fuel_remaining: float
    provenance: ProvenanceTier = "SIMULATED"


@dataclass
class ResupplyState:
    next_resupply_date: str
    resupply_window_days: int
    resupply_event_active: bool
    fuel_delivered_liters: float = 0.0
    provenance: ProvenanceTier = "CONFIGURED"


@dataclass
class OperationalState:
    occupancy_factor: float
    research_activity: float
    communication_activity: float
    maintenance_active: float
    flexible_load_schedule: float = 0.0
    provenance: ProvenanceTier = "CONFIGURED"


@dataclass
class ConstraintEvaluation:
    constraint_name: str
    value: float
    limit: float
    status: Literal["SATISFIED", "WARNING", "VIOLATED"]
    violation_magnitude: float
    unit: str
    provenance: ProvenanceTier = "CONFIGURED"


@dataclass
class ResilienceState:
    nameplate_reserve_kw: float
    dependable_reserve_kw: float
    dependable_reserve_pct: float
    fuel_constrained_reserve_kw: float
    critical_load_survival_status: Literal["SURVIVED", "FAILED"]
    continuity_horizon_hours: float
    threat_state: Literal["SAFE", "AT_RISK", "THREATENED", "CRITICAL"]
    provenance: ProvenanceTier = "SIMULATED"


@dataclass
class TwinState:
    """Composite computational state of the Polaris-EMS Energy Digital Twin."""
    station_id: str
    timestamp: str
    environment: EnvironmentState
    thermal: ThermalState
    loads: LoadState
    solar: SolarState
    wind: WindState
    battery: BatteryState
    diesel: DieselState
    fuel: FuelState
    resupply: ResupplyState
    operational: OperationalState
    constraints: List[ConstraintEvaluation] = field(default_factory=list)
    resilience: Optional[ResilienceState] = None
    dispatch_policy: str = "BASELINE_SIMULATION_DISPATCH"
    provenance: ProvenanceTier = "SIMULATED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
