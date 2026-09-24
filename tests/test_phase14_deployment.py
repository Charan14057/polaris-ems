"""
POLARIS-EMS — Automated Test Suite: Phase 14 Deployment, External Integration & Productization
SIH26061: Polar Energy Management & Resilience System

Workstream Verification Suite:
1. Environment & Hierarchical Configuration (Workstream A & B)
2. External Provider Schemas, Validation & Physical Bounds (Workstream C)
3. Provenance Preservation & Forbidden Tier Rejection (Workstream C & Provenance Rule)
4. Reality Bridge Fallback & Offline Spooler (Workstream C & Fallback Rule)
5. Runtime Observability & Metrics Endpoints (Workstream D)
6. Security Hardening, Security Headers & Payload Limiting (Workstream E)
7. Disaggregated Health Model (Workstream I)
8. Operator Review Boundary & SCADA Disclaimer Invariant (Workstream G & Acceptance Criteria)
"""

import os
import math
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.config.settings import (
    get_settings,
    PolarisSettings,
    ApplicationSettings,
    SecuritySettings,
    ExternalProviderSettings,
    DeploymentSettings,
    ProductSettings,
)
from backend.api import create_app
from backend.integrations.schemas import (
    ExternalWeatherObservation,
    ExternalTelemetryPayload,
    ProviderStatus,
    StalenessStatus,
    LOCKED_PROVENANCE_TIERS,
)

FORBIDDEN_PROVENANCE_TIERS = ["LIVE", "REAL_TIME", "OPTIMIZED", "API", "DERIVED", "PRODUCTION"]

from backend.integrations.validation import ExternalDataValidator
from backend.integrations.bridge import get_reality_bridge, ExternalRealityBridge
from backend.integrations.adapters.file_spooler import OfflineFileSpoolerAdapter
from backend.api.adapters.pipeline_orchestrator import PipelineOrchestrator
from backend.api.schemas.pipeline import PipelineAnalyzeRequestSchema


@pytest.fixture(scope="module")
def client():
    """Module-scoped FastAPI TestClient instance."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


# ==============================================================================
# 1. CONFIGURATION & HIERARCHICAL SETTINGS (WORKSTREAM A & B)
# ==============================================================================

def test_settings_hierarchy_and_defaults():
    """Verifies settings load correctly with required sub-models and safe production defaults."""
    settings = get_settings()
    assert isinstance(settings, PolarisSettings)
    assert isinstance(settings.app, ApplicationSettings)
    assert isinstance(settings.security, SecuritySettings)
    assert isinstance(settings.providers, ExternalProviderSettings)
    assert isinstance(settings.external_providers, ExternalProviderSettings)
    assert isinstance(settings.deployment, DeploymentSettings)
    assert isinstance(settings.product, ProductSettings)

    # Invariants
    assert settings.product.physical_scada_connected is False, "Physical SCADA must remain disconnected"
    assert settings.product.operator_mode == "ADVISORY"
    assert settings.security.enable_security_headers is True
    assert settings.security.max_request_bytes == 10 * 1024 * 1024
    assert settings.external_providers.enabled is False  # Safe default


def test_settings_environment_overrides(monkeypatch):
    """Verifies that environment variables override settings values without affecting code."""
    monkeypatch.setenv("POLARIS_ENVIRONMENT", "STAGING")
    monkeypatch.setenv("POLARIS_MAX_REQUEST_BYTES", "5242880")
    monkeypatch.setenv("POLARIS_EXTERNAL_TIMEOUT_SEC", "12")

    # Clear lru_cache to pick up env vars
    get_settings.cache_clear()
    try:
        new_settings = get_settings()
        assert new_settings.deployment.environment == "STAGING"
        assert new_settings.security.max_request_bytes == 5242880
        assert new_settings.external_providers.request_timeout_sec == 12
    finally:
        get_settings.cache_clear()


# ==============================================================================
# 2. EXTERNAL DATA SCHEMAS & PHYSICAL BOUNDARIES (WORKSTREAM C)
# ==============================================================================

def test_external_weather_schema_and_physical_boundaries():
    """Valid polar weather observation passes validation with FRESH status and quality score 1.0."""
    validator = ExternalDataValidator()
    obs = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=datetime.now(timezone.utc),
        ambient_temperature_c=-28.4,
        wind_speed_ms=14.5,
        solar_irradiance_wm2=0.0,
        source_provider="Satcom-Station-Feed",
        provenance="SYNTHETIC",
    )
    result = validator.validate_weather(obs)
    assert result.is_valid is True
    assert result.quality_score == 1.0
    assert result.staleness_status == StalenessStatus.FRESH
    assert len(result.errors) == 0


def test_external_validator_quarantines_extreme_temperatures():
    """Out-of-bounds temperatures (< -90°C or > +30°C) are quarantined."""
    validator = ExternalDataValidator()

    # Extreme sub-zero below physical polar minimum
    obs_too_cold = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=datetime.now(timezone.utc),
        ambient_temperature_c=-105.0,
        wind_speed_ms=10.0,
        solar_irradiance_wm2=0.0,
        source_provider="Demonstration-Source",
        provenance="SYNTHETIC",
    )
    res_cold = validator.validate_weather(obs_too_cold)
    assert res_cold.is_valid is False
    assert any("outside polar bounds" in err for err in res_cold.errors)

    # Above maximum polar threshold
    obs_too_warm = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=datetime.now(timezone.utc),
        ambient_temperature_c=45.0,
        wind_speed_ms=5.0,
        solar_irradiance_wm2=500.0,
        source_provider="Demonstration-Source",
        provenance="SYNTHETIC",
    )
    res_warm = validator.validate_weather(obs_too_warm)
    assert res_warm.is_valid is False
    assert any("outside polar bounds" in err for err in res_warm.errors)


def test_external_validator_quarantines_extreme_winds_and_solar():
    """Winds > 85 m/s or solar irradiance > 1400 W/m² are quarantined."""
    validator = ExternalDataValidator()

    # Extreme wind (hurricane category 5+ > 85 m/s)
    obs_wind = ExternalWeatherObservation(
        station_id="MAITRI",
        timestamp=datetime.now(timezone.utc),
        ambient_temperature_c=-15.0,
        wind_speed_ms=95.0,
        solar_irradiance_wm2=0.0,
        source_provider="Demonstration-Source",
        provenance="SYNTHETIC",
    )
    res_wind = validator.validate_weather(obs_wind)
    assert res_wind.is_valid is False
    assert any("wind speed" in err.lower() for err in res_wind.errors)

    # Extreme solar (exceeding extraterrestrial solar constant)
    obs_solar = ExternalWeatherObservation(
        station_id="HIMADRI",
        timestamp=datetime.now(timezone.utc),
        ambient_temperature_c=-2.0,
        wind_speed_ms=8.0,
        solar_irradiance_wm2=1800.0,
        source_provider="Demonstration-Source",
        provenance="SYNTHETIC",
    )
    res_solar = validator.validate_weather(obs_solar)
    assert res_solar.is_valid is False
    assert any("solar irradiance" in err.lower() for err in res_solar.errors)


def test_external_validator_rejects_non_finite_values():
    """NaN or Inf floating-point values are rejected."""
    validator = ExternalDataValidator()
    obs_nan = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=datetime.now(timezone.utc),
        ambient_temperature_c=float("nan"),
        wind_speed_ms=10.0,
        solar_irradiance_wm2=0.0,
        source_provider="Demonstration-Source",
        provenance="SYNTHETIC",
    )
    res_nan = validator.validate_weather(obs_nan)
    assert res_nan.is_valid is False
    assert any("non-finite" in err.lower() for err in res_nan.errors)


def test_external_validator_detects_staleness():
    """Observations older than 1 hour are marked STALE."""
    validator = ExternalDataValidator(max_freshness_sec=3600)

    # 3 hours old
    old_time = datetime.now(timezone.utc) - timedelta(hours=3)
    obs_old = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=old_time,
        ambient_temperature_c=-20.0,
        wind_speed_ms=12.0,
        solar_irradiance_wm2=0.0,
        source_provider="Demonstration-Source",
        provenance="SYNTHETIC",
    )
    res_old = validator.validate_weather(obs_old)
    assert res_old.is_valid is True  # Valid within physical bounds
    assert res_old.staleness_status == StalenessStatus.STALE
    assert res_old.quality_score < 1.0


# ==============================================================================
# 3. PROVENANCE INTEGRITY & FORBIDDEN TIERS
# ==============================================================================

def test_provenance_taxonomy_invariants():
    """The 6-tier provenance taxonomy is strictly maintained; forbidden tiers are rejected."""
    assert len(LOCKED_PROVENANCE_TIERS) == 6
    assert LOCKED_PROVENANCE_TIERS == {"REAL", "CONFIGURED", "ASSUMED", "SYNTHETIC", "FORECAST", "SIMULATED"}

    # Attempting to assign forbidden tier must raise ValueError
    for forbidden in FORBIDDEN_PROVENANCE_TIERS:
        with pytest.raises(ValueError, match="Invalid provenance"):
            ExternalWeatherObservation(
                station_id="BHARATI",
                timestamp=datetime.now(timezone.utc),
                ambient_temperature_c=-20.0,
                wind_speed_ms=10.0,
                solar_irradiance_wm2=0.0,
                provenance=forbidden,
            )


# ==============================================================================
# 4. REALITY BRIDGE ORCHESTRATION & FALLBACK
# ==============================================================================

def test_reality_bridge_fallback_when_providers_disabled():
    """When providers are disabled or unreachable, the bridge falls back cleanly without crashing."""
    bridge = get_reality_bridge()
    res = bridge.get_weather_observation("BHARATI")
    assert res is not None
    # When disabled in default config, returns safe fallback validation result
    assert res.provenance in LOCKED_PROVENANCE_TIERS
    assert res.is_valid is False
    assert any("disabled" in err.lower() for err in res.errors)


def test_reality_bridge_summary_reporting():
    """Reality bridge reports registered providers, active adapters, and strict provenance policy."""
    bridge = get_reality_bridge()
    summary = bridge.get_bridge_summary()
    assert summary["registered_providers"] >= 1
    assert "provenance_policy" in summary
    assert "Strict 6-tier" in summary["provenance_policy"]


def test_offline_file_spooler_adapter():
    """Offline satcom file spooler simulates or reads spool files with correct validation."""
    spooler = OfflineFileSpoolerAdapter()
    assert spooler.name == "Offline-Satcom-Spooler"
    health = spooler.get_health_record()
    assert health.status == ProviderStatus.HEALTHY


# ==============================================================================
# 5. DISAGGREGATED DEPLOYMENT HEALTH MODEL (WORKSTREAM I)
# ==============================================================================

def test_health_liveness_and_readiness(client):
    """GET /health and GET /ready return 200 with proper structure."""
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "SUCCESS"

    resp_ready = client.get("/ready")
    assert resp_ready.status_code == 200
    assert resp_ready.json()["status"] == "SUCCESS"


def test_disaggregated_health_endpoints(client):
    """Verifies separate endpoints for providers, computational engines, and physical connectivity."""
    # 1. Provider health
    resp_prov = client.get("/health/providers")
    assert resp_prov.status_code == 200
    data_prov = resp_prov.json()["data"]
    assert "providers" in data_prov
    assert data_prov["total_providers"] >= 1

    # 2. Physical connectivity (Strictly disconnected)
    resp_phys = client.get("/health/physical")
    assert resp_phys.status_code == 200
    data_phys = resp_phys.json()["data"]
    assert data_phys["physical_scADA_connected".lower()] is False
    assert "zero connected physical" in data_phys["disclaimer"].lower()

    # 3. Computational engines
    resp_eng = client.get("/health/engines")
    assert resp_eng.status_code == 200
    data_eng = resp_eng.json()["data"]
    assert data_eng["phase3_forecasting"] == "HEALTHY"
    assert data_eng["phase4_digital_twin"] == "HEALTHY"
    assert data_eng["phase6_optimizer"] == "HEALTHY"
    assert data_eng["phase7_resilience"] == "HEALTHY"
    assert data_eng["phase8_policy"] == "HEALTHY"


# ==============================================================================
# 6. INTEGRATIONS & OBSERVABILITY ROUTES (WORKSTREAM C & D)
# ==============================================================================

def test_integrations_routes(client):
    """GET /api/v1/integrations/* returns valid bridge metadata and station weather."""
    resp_status = client.get("/api/v1/integrations/status")
    assert resp_status.status_code == 200
    assert resp_status.json()["data"]["registered_providers"] >= 1

    resp_providers = client.get("/api/v1/integrations/providers")
    assert resp_providers.status_code == 200
    assert isinstance(resp_providers.json()["data"], list)

    resp_fresh = client.get("/api/v1/integrations/freshness")
    assert resp_fresh.status_code == 200
    assert "providers_freshness" in resp_fresh.json()["data"]

    resp_weather = client.get("/api/v1/integrations/weather/BHARATI")
    assert resp_weather.status_code == 200
    assert resp_weather.json()["status"] == "SUCCESS"


def test_observability_routes(client):
    """GET /api/v1/observability/* returns runtime metrics and deployment audit posture."""
    resp_metrics = client.get("/api/v1/observability/metrics")
    assert resp_metrics.status_code == 200
    data_metrics = resp_metrics.json()["data"]
    assert "service" in data_metrics
    assert "uptime_seconds" in data_metrics["service"]
    assert "environment" in data_metrics["service"]
    assert data_metrics["security_posture"]["security_headers_active"] is True

    resp_audit = client.get("/api/v1/observability/audit")
    assert resp_audit.status_code == 200
    data_audit = resp_audit.json()["data"]
    assert data_audit["provenance_taxonomy_compliance"]["status"] == "PASS"
    assert data_audit["physical_scada_limitation"]["physical_telemetry_connected"] is False


# ==============================================================================
# 7. SECURITY HARDENING & MIDDLEWARE (WORKSTREAM E)
# ==============================================================================

def test_security_headers_middleware(client):
    """All API responses contain standard production security headers."""
    resp = client.get("/health")
    headers = resp.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in headers
    assert "X-Request-ID" in headers
    assert "X-Process-Time-Sec" in headers


def test_payload_limit_middleware_allows_reasonable_payloads(client):
    """Normal-sized request payloads pass cleanly through the limiter."""
    resp = client.post(
        "/api/v1/pipeline/analyze",
        json={"station_id": "BHARATI", "horizon_hours": 12, "mode": "EXPECTED"}
    )
    # Status can be 200 or validation error, but NOT 413
    assert resp.status_code != 413


def test_payload_limit_middleware_blocks_oversized_payloads():
    """Oversized payloads exceeding max_request_bytes are rejected with 413."""
    app = create_app()
    with TestClient(app) as test_client:
        # Send a header claiming content-length larger than max allowed
        large_headers = {"content-length": str(15 * 1024 * 1024)}
        resp = test_client.post("/api/v1/pipeline/analyze", headers=large_headers, content=b"x")
        assert resp.status_code == 413
        assert resp.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


# ==============================================================================
# 8. OPERATOR APPROVAL & PIPELINE INTEGRITY (WORKSTREAM G & DEMO)
# ==============================================================================

def test_operator_approval_boundary_and_scada_disclaimer():
    """Verifies architectural invariants: advisory operator mode and zero SCADA connectivity."""
    settings = get_settings()
    assert settings.product.operator_mode == "ADVISORY"
    assert settings.product.physical_scada_connected is False


def test_pipeline_trace_continuity_and_provenance():
    """Pipeline orchestrator executes end-to-end, producing an auditable trace with valid provenance."""
    orchestrator = PipelineOrchestrator()
    req = PipelineAnalyzeRequestSchema(
        station_id="BHARATI",
        horizon_hours=24,
        scenario_id="BLIZZARD",
        mode="SCENARIO_ROBUST"
    )
    resp = orchestrator.run_pipeline(req)
    assert resp.overall_status in {"SUCCESS", "PARTIAL"}
    assert resp.decision_trace_id is not None
    assert resp.decision_trace_id.startswith("DT-")
    assert resp.provenance in LOCKED_PROVENANCE_TIERS
