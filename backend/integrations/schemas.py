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
    """Health and operational classification for external providers."""
    AVAILABLE = "AVAILABLE"
    HEALTHY = "HEALTHY"          # backward compatibility alias for AVAILABLE
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"  # backward compatibility alias for FAILED
    QUARANTINED = "QUARANTINED"
    DISABLED = "DISABLED"


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


class ExternalForecastSeries(BaseModel):
    """Multi-horizon time series of external weather forecasts (e.g. 48h/168h)."""
    station_id: str
    forecast_origin: datetime
    horizon_hours: int
    steps: List[ExternalWeatherObservation]
    source_provider: str
    provenance: str = "SYNTHETIC"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("provenance")
    @classmethod
    def validate_provenance(cls, v: str) -> str:
        if v not in LOCKED_PROVENANCE_TIERS:
            raise ValueError(f"Invalid provenance '{v}'. Must be one of: {sorted(LOCKED_PROVENANCE_TIERS)}")
        return v


class ExternalFeedCompleteness(BaseModel):
    """Tracking of feed completeness, missing intervals, and arrival frequency."""
    station_id: str
    start_time: datetime
    end_time: datetime
    expected_intervals: int
    received_intervals: int
    missing_intervals: int
    completeness_ratio: float = Field(..., ge=0.0, le=1.0)
    is_complete: bool
    missing_timestamps: List[datetime] = Field(default_factory=list)


class ModelVsObservedMetric(BaseModel):
    """Real-world operational accuracy and calibration metrics against paired observations."""
    station_id: str
    target: str
    horizon_h: int
    n_samples: int
    observed_mean: float
    forecast_mean: float
    residuals: List[float] = Field(default_factory=list)
    mae: float
    rmse: float
    mbe: float  # Signed Mean Bias Error (observed - forecast)
    smape: float
    interval_80_coverage: float
    evidence_type: str = "EXTERNAL_VALIDATION"
    reference_provenance: str = "SYNTHETIC"

    @field_validator("reference_provenance")
    @classmethod
    def validate_reference_provenance(cls, v: str) -> str:
        if v not in LOCKED_PROVENANCE_TIERS:
            raise ValueError(f"Invalid reference_provenance '{v}'. Must be one of: {sorted(LOCKED_PROVENANCE_TIERS)}")
        return v


class TwinRealityMetric(BaseModel):
    """Evaluation of Digital Twin physical conservation against reference measurements."""
    station_id: str
    subsystem: str  # electrical, thermal, battery, fuel
    n_evaluations: int
    observed_value: float
    simulated_value: float
    residual: float
    residual_pct: float
    within_tolerance: bool
    status: str  # VALIDATED, DISCREPANCY_NOTED, CALIBRATION_CANDIDATE
    reference_provenance: str = "SYNTHETIC"
    details: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("reference_provenance")
    @classmethod
    def validate_reference_provenance(cls, v: str) -> str:
        if v not in LOCKED_PROVENANCE_TIERS:
            raise ValueError(f"Invalid reference_provenance '{v}'. Must be one of: {sorted(LOCKED_PROVENANCE_TIERS)}")
        return v


class CalibrationCandidate(BaseModel):
    """Governed proposal for future model recalibration (preserves frozen baseline)."""
    candidate_id: str
    target_subsystem: str
    parameter_name: str
    current_value: float
    proposed_value: float
    deviation_reason: str
    empirical_residual_reduction_pct: float
    governance_status: str = "PENDING_CONTROLLED_REVIEW"
    immutable_baseline_preserved: bool = True


class DriftType(str, Enum):
    """Taxonomy of operational drift categories."""
    DATA_DRIFT = "DATA_DRIFT"
    MODEL_DRIFT = "MODEL_DRIFT"
    PHYSICAL_MODEL_MISMATCH = "PHYSICAL_MODEL_MISMATCH"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    NOMINAL = "NOMINAL"


class DriftIndicator(BaseModel):
    """Real-time operational drift detection indicator."""
    metric_name: str
    drift_type: DriftType
    detected: bool
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    z_score: float
    p_value: Optional[float] = None
    description: str
    recommendation: str


class OperationalReplayResult(BaseModel):
    """Result of passing external weather through the full frozen intelligence pipeline."""
    replay_id: str
    station_id: str
    horizon_hours: int
    trace_id: str
    external_weather_used: bool
    optimization_status: str
    twin_replay_pass: bool
    resilience_state: str
    policy_directive: str
    discrepancy_vs_baseline: Dict[str, Any] = Field(default_factory=dict)
