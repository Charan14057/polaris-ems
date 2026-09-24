"""
POLARIS-EMS — External Reality Bridge Schemas
SIH26061: Polar Energy Management & Resilience System

Workstream C: External Schemas & Quality Statuses
Strictly enforces 6-tier provenance taxonomy:
REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ProviderStatus(str, Enum):
    """Health classification for external providers."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED = "DISABLED"
    STALE = "STALE"


class StalenessStatus(str, Enum):
    """Observation data freshness rating."""
    FRESH = "FRESH"          # < 15 minutes old
    ACCEPTABLE = "ACCEPTABLE" # 15 min - 1 hour old
    STALE = "STALE"          # 1 - 6 hours old
    EXPIRED = "EXPIRED"      # > 6 hours old or future


LOCKED_PROVENANCE_TIERS = {"REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"}


class ExternalWeatherObservation(BaseModel):
    """Normalized external weather observation payload."""
    station_id: str = Field(..., description="Target polar research station identifier (BHARATI, MAITRI, HIMADRI)")
    timestamp: datetime = Field(..., description="Observation recorded UTC timestamp")
    ambient_temperature_c: float = Field(..., description="Ambient air temperature in degrees Celsius")
    wind_speed_ms: float = Field(..., description="Wind speed in meters per second")
    solar_irradiance_wm2: float = Field(..., description="Global horizontal solar irradiance in W/m²")
    direct_normal_irradiance_wm2: Optional[float] = Field(None, description="Direct normal irradiance in W/m²")
    diffuse_horizontal_irradiance_wm2: Optional[float] = Field(None, description="Diffuse horizontal irradiance in W/m²")
    surface_pressure_hpa: Optional[float] = Field(None, description="Atmospheric surface pressure in hPa")
    relative_humidity_pct: Optional[float] = Field(None, description="Relative humidity percentage (0-100)")
    source_provider: str = Field(default="ExternalProvider", description="Name of external adapter / provider")
    provenance: str = Field(default="SYNTHETIC", description="Strict 6-tier provenance classification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Provider diagnostic metadata")

    @field_validator("provenance")
    @classmethod
    def validate_provenance(cls, v: str) -> str:
        if v not in LOCKED_PROVENANCE_TIERS:
            raise ValueError(f"Invalid provenance '{v}'. Must be one of: {sorted(LOCKED_PROVENANCE_TIERS)}")
        return v

    @field_validator("station_id")
    @classmethod
    def validate_station(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ("BHARATI", "MAITRI", "HIMADRI"):
            raise ValueError(f"Unknown polar station '{v}'. Allowed: BHARATI, MAITRI, HIMADRI")
        return v_upper


class ExternalTelemetryPayload(BaseModel):
    """Generic structured payload from an external field gateway or sensor logger."""
    station_id: str
    timestamp: datetime
    metrics: Dict[str, float]
    source: str
    provenance: str = "SYNTHETIC"
    raw_payload_checksum: Optional[str] = None

    @field_validator("provenance")
    @classmethod
    def validate_provenance(cls, v: str) -> str:
        if v not in LOCKED_PROVENANCE_TIERS:
            raise ValueError(f"Invalid provenance '{v}'. Must be one of: {sorted(LOCKED_PROVENANCE_TIERS)}")
        return v


class ExternalValidationResult(BaseModel):
    """Output of schema validation, physical boundary checking, and freshness verification."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score (0.0 to 1.0)")
    freshness_seconds: float = Field(..., description="Age of observation in seconds relative to evaluation time")
    staleness_status: StalenessStatus
    validated_observation: Optional[ExternalWeatherObservation] = None
    provenance: str = "SYNTHETIC"


class ProviderHealthRecord(BaseModel):
    """Status report for a registered external data provider."""
    provider_name: str
    status: ProviderStatus
    enabled: bool
    last_contact: Optional[datetime] = None
    last_success: Optional[datetime] = None
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    total_requests: int = 0
    successful_requests: int = 0
    average_latency_ms: float = 0.0
    freshness_status: StalenessStatus = StalenessStatus.EXPIRED
