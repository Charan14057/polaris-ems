"""
POLARIS-EMS — Enterprise Configuration Hierarchy
SIH26061: Polar Energy Management & Resilience System

Workstream B: Environment Configuration
Separates:
1. Application Settings: host, port, workers, debug, log_level, shutdown_timeout_sec
2. Security Settings: cors_origins, max_request_bytes, enable_security_headers
3. External Provider Settings: provider enablement, timeouts, freshness limits, rate limits
4. Deployment Settings: environment (PRODUCTION/STAGING/DEVELOPMENT), static file serving
5. Product Settings: system title, operator mode, environment badge
"""

import os
from typing import List, Optional
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class ApplicationSettings:
    """Runtime server host, port, concurrency, and logging."""
    host: str = field(default_factory=lambda: os.getenv("POLARIS_API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("POLARIS_API_PORT", "8000")))
    workers: int = field(default_factory=lambda: int(os.getenv("POLARIS_WORKERS", "1")))
    debug: bool = field(default_factory=lambda: os.getenv("POLARIS_DEBUG", "false").lower() in ("true", "1", "yes"))
    log_level: str = field(default_factory=lambda: os.getenv("POLARIS_LOG_LEVEL", "INFO").upper())
    shutdown_timeout_sec: float = field(default_factory=lambda: float(os.getenv("POLARIS_SHUTDOWN_TIMEOUT_SEC", "15.0")))


@dataclass
class SecuritySettings:
    """Network, CORS, request payload size limits, and security headers."""
    cors_origins: List[str] = field(default_factory=lambda: [
        origin.strip()
        for origin in os.getenv("POLARIS_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    ])
    max_request_bytes: int = field(default_factory=lambda: int(os.getenv("POLARIS_MAX_REQUEST_BYTES", "10485760")))  # 10 MB limit
    enable_security_headers: bool = field(default_factory=lambda: os.getenv("POLARIS_SECURITY_HEADERS", "true").lower() in ("true", "1", "yes"))


@dataclass
class ExternalProviderSettings:
    """Configuration for external reality bridges, weather APIs, and telemetry adapters."""
    enabled: bool = field(default_factory=lambda: os.getenv("POLARIS_EXTERNAL_DATA_ENABLED", "false").lower() in ("true", "1", "yes"))
    request_timeout_sec: float = field(default_factory=lambda: float(os.getenv("POLARIS_EXTERNAL_TIMEOUT_SEC", "10.0")))
    max_freshness_sec: int = field(default_factory=lambda: int(os.getenv("POLARIS_EXTERNAL_MAX_FRESHNESS_SEC", "3600")))  # 1 hour max age
    rate_limit_rpm: int = field(default_factory=lambda: int(os.getenv("POLARIS_EXTERNAL_RATE_LIMIT_RPM", "60")))
    # Provider-specific endpoints (empty by default to defend zero-telemetry limitation)
    openmeteo_endpoint: str = field(default_factory=lambda: os.getenv("POLARIS_OPENMETEO_ENDPOINT", "https://api.open-meteo.com/v1/forecast"))
    ncpor_gateway_url: Optional[str] = field(default_factory=lambda: os.getenv("POLARIS_NCPOR_GATEWAY_URL"))
    weather_api_key: Optional[str] = field(default_factory=lambda: os.getenv("POLARIS_WEATHER_API_KEY"))


@dataclass
class DeploymentSettings:
    """Container, environment mode, and static asset serving settings."""
    environment: str = field(default_factory=lambda: os.getenv("POLARIS_ENVIRONMENT", "LOCAL_INTEGRATED").upper())
    serve_frontend: bool = field(default_factory=lambda: os.getenv("POLARIS_SERVE_FRONTEND", "false").lower() in ("true", "1", "yes"))
    frontend_dist_dir: str = field(default_factory=lambda: os.getenv("POLARIS_FRONTEND_DIST", "frontend/dist"))
    trace_dir: str = field(default_factory=lambda: os.getenv("POLARIS_TRACE_DIR", "reports/traces"))
    trace_retention_limit: int = field(default_factory=lambda: int(os.getenv("POLARIS_TRACE_RETENTION_LIMIT", "500")))


@dataclass
class ProductSettings:
    """Platform identification, operational mode, and operator boundary."""
    product_name: str = "Polaris-EMS"
    system_title: str = "Polar Energy Management & Resilience System"
    version: str = "1.0.0"
    api_version: str = "v1"
    # Operator modes: ADVISORY (default), SUPERVISED_DISPATCH, SIMULATION_OFFLINE
    operator_mode: str = field(default_factory=lambda: os.getenv("POLARIS_OPERATOR_MODE", "ADVISORY").upper())
    # Physical SCADA presence flag: Strictly False unless physical hardware exists
    physical_scada_connected: bool = False  # Strictly False under current polar deployment constraint
    physical_scada_link: bool = False
    physical_validation: str = "NOT_AVAILABLE"


@dataclass
class PolarisSettings:
    """Unified master settings container."""
    app: ApplicationSettings = field(default_factory=ApplicationSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    providers: ExternalProviderSettings = field(default_factory=ExternalProviderSettings)
    deployment: DeploymentSettings = field(default_factory=DeploymentSettings)
    product: ProductSettings = field(default_factory=ProductSettings)

    @property
    def external_providers(self) -> ExternalProviderSettings:
        return self.providers


@lru_cache(maxsize=1)
def get_settings() -> PolarisSettings:
    """Cached settings singleton."""
    return PolarisSettings()
