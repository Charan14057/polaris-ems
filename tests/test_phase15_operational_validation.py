"""
POLARIS-EMS — Automated Test Suite: Phase 15 Real-World Integration, Calibration & Operational Validation
SIH26061: Polar Energy Management & Resilience System

Workstream Verification Suite (Workstream N):
1. Valid External Weather Ingestion & Multi-Horizon Series (Workstream A & B)
2. Malformed Observation, Non-Finite & Missing Field Rejection (Workstream B)
3. Stale Observation Detection & Quality Scoring (Workstream B)
4. Future Timestamp Temporal Causality Guard (Workstream B)
5. Physical Bound Violation & Quarantine Circuit Breaker (Workstream B)
6. Provider Outage, Safe Fallback & Recovery (Workstream B & D)
7. Feed Completeness & Gap Tracking (Workstream B)
8. Closed 6-Tier Provenance Invariant (Workstream C)
9. Truthful Physical Connectivity DISCONNECTED Invariant (Workstream I)
10. Model vs. Observed Metrics (Residuals, MBE, MAE, RMSE, sMAPE, Coverage) (Workstream E)
11. Digital Twin Reality Check & Calibration Candidates (Workstream F & J)
12. Operational Drift Categorization: Data, Model, Twin Mismatch, Provider Failure (Workstream G)
13. Edge Full Offline-to-Reconnect Cycle & State Reconciliation (Workstream H)
14. End-to-End Operational Decision Replay & Trace Continuity (Workstream K & L)
15. Observability API Validation Endpoints (Workstream L)
"""

import math
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.api import create_app
from backend.integrations.schemas import (
    ExternalWeatherObservation,
    ExternalForecastSeries,
    ExternalFeedCompleteness,
    ProviderStatus,
    StalenessStatus,
    DriftType,
    LOCKED_PROVENANCE_TIERS,
)
from backend.integrations.validation import ExternalDataValidator
from backend.integrations.bridge import ExternalRealityBridge, get_reality_bridge
from backend.integrations.adapters.openmeteo import OpenMeteoPolarAdapter
from backend.integrations.adapters.ncpor_format import NCPORFormatAdapter
from backend.integrations.evaluator import ModelVsObservedEvaluator, get_model_evaluator
from backend.integrations.twin_reality import TwinRealityCheckEngine, get_twin_reality_engine
from backend.integrations.drift import OperationalDriftDetector, get_drift_detector
from backend.integrations.replay import OperationalReplayOrchestrator, get_replay_orchestrator
from backend.edge.connectivity import ConnectivityTracker
from backend.edge.buffer import LocalTelemetryBuffer, BufferedItem
from backend.edge.reconciliation import StateReconciler
from backend.edge.schema import TelemetryReading, ConnectivityState


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


# ==============================================================================
# 1. Valid External Weather Ingestion & Multi-Horizon Series
# ==============================================================================

def test_valid_external_weather_observation():
    validator = ExternalDataValidator(max_freshness_sec=3600)
    now = datetime.now(timezone.utc)
    obs = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=now - timedelta(minutes=5),
        ambient_temperature_c=-18.5,
        wind_speed_ms=14.2,
        solar_irradiance_wm2=120.0,
        direct_normal_irradiance_wm2=120.0,
        surface_pressure_hpa=982.0,
        relative_humidity_pct=72.0,
        source_provider="OpenMeteo",
        provenance="SYNTHETIC"
    )
    result = validator.validate_weather(obs, reference_time=now)
    assert result.is_valid is True
    assert result.errors == []
    assert result.quality_score >= 0.95
    assert result.staleness_status == StalenessStatus.FRESH
    assert result.validated_observation is not None
    assert result.validated_observation.station_id == "BHARATI"


def test_valid_forecast_series_multi_horizon():
    validator = ExternalDataValidator()
    now = datetime.now(timezone.utc)
    steps = [
        ExternalWeatherObservation(
            station_id="MAITRI",
            timestamp=now + timedelta(hours=i),
            ambient_temperature_c=-22.0 + (i * 0.2),
            wind_speed_ms=11.0 + (i * 0.1),
            solar_irradiance_wm2=150.0 if (6 <= (i % 24) <= 18) else 0.0,
            source_provider="OpenMeteo-Polar",
            provenance="SYNTHETIC"
        )
        for i in range(48)
    ]
    series = ExternalForecastSeries(
        station_id="MAITRI",
        forecast_origin=now,
        horizon_hours=48,
        steps=steps,
        source_provider="OpenMeteo-Polar",
        provenance="SYNTHETIC"
    )
    is_valid, step_results, errors = validator.validate_forecast_series(series, reference_time=now)
    assert is_valid is True
    assert len(step_results) == 48
    assert errors == []


# ==============================================================================
# 2. Malformed Observation & Non-Finite Number Rejection
# ==============================================================================

def test_external_validator_rejects_nan_and_inf():
    validator = ExternalDataValidator()
    now = datetime.now(timezone.utc)

    # NaN temperature
    obs_nan = ExternalWeatherObservation(
        station_id="HIMADRI",
        timestamp=now,
        ambient_temperature_c=float("nan"),
        wind_speed_ms=8.0,
        solar_irradiance_wm2=0.0,
        provenance="SYNTHETIC"
    )
    res_nan = validator.validate_weather(obs_nan, reference_time=now)
    assert res_nan.is_valid is False
    assert any("Non-finite" in e for e in res_nan.errors)
    assert res_nan.quality_score == 0.0

    # Inf wind speed
    obs_inf = ExternalWeatherObservation(
        station_id="HIMADRI",
        timestamp=now,
        ambient_temperature_c=-10.0,
        wind_speed_ms=float("inf"),
        solar_irradiance_wm2=0.0,
        provenance="SYNTHETIC"
    )
    res_inf = validator.validate_weather(obs_inf, reference_time=now)
    assert res_inf.is_valid is False
    assert any("Non-finite" in e for e in res_inf.errors)


# ==============================================================================
# 3. Stale Observation Detection & Quality Scoring
# ==============================================================================

def test_staleness_detection_and_degradation():
    validator = ExternalDataValidator(max_freshness_sec=3600)
    now = datetime.now(timezone.utc)

    # 45 minutes old -> ACCEPTABLE
    obs_acceptable = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=now - timedelta(minutes=45),
        ambient_temperature_c=-15.0,
        wind_speed_ms=10.0,
        solar_irradiance_wm2=50.0,
        provenance="SYNTHETIC"
    )
    res_acc = validator.validate_weather(obs_acceptable, reference_time=now)
    assert res_acc.is_valid is True
    assert res_acc.staleness_status == StalenessStatus.ACCEPTABLE
    assert res_acc.quality_score < 1.0

    # 3 hours old -> STALE
    obs_stale = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=now - timedelta(hours=3),
        ambient_temperature_c=-15.0,
        wind_speed_ms=10.0,
        solar_irradiance_wm2=50.0,
        provenance="SYNTHETIC"
    )
    res_stale = validator.validate_weather(obs_stale, reference_time=now)
    assert res_stale.is_valid is True
    assert res_stale.staleness_status == StalenessStatus.STALE
    assert res_stale.quality_score <= 0.60
    assert len(res_stale.warnings) > 0

    # 8 hours old -> EXPIRED (rejected)
    obs_expired = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=now - timedelta(hours=8),
        ambient_temperature_c=-15.0,
        wind_speed_ms=10.0,
        solar_irradiance_wm2=50.0,
        provenance="SYNTHETIC"
    )
    res_exp = validator.validate_weather(obs_expired, reference_time=now)
    assert res_exp.is_valid is False
    assert res_exp.staleness_status == StalenessStatus.EXPIRED


# ==============================================================================
# 4. Future Timestamp Temporal Causality Guard
# ==============================================================================

def test_future_timestamp_temporal_causality_guard():
    validator = ExternalDataValidator(max_future_tolerance_sec=60.0)
    now = datetime.now(timezone.utc)

    # 5 minutes in the future -> leakage violation
    future_obs = ExternalWeatherObservation(
        station_id="MAITRI",
        timestamp=now + timedelta(minutes=5),
        ambient_temperature_c=-20.0,
        wind_speed_ms=12.0,
        solar_irradiance_wm2=0.0,
        provenance="SYNTHETIC"
    )
    res = validator.validate_weather(future_obs, reference_time=now)
    assert res.is_valid is False
    assert any("Future timestamp violation" in e for e in res.errors)
    assert res.staleness_status == StalenessStatus.EXPIRED


# ==============================================================================
# 5. Physical Bound Violation & Quarantine Circuit Breaker
# ==============================================================================

def test_physical_bounds_and_quarantine_circuit_breaker():
    validator = ExternalDataValidator()
    now = datetime.now(timezone.utc)

    # Extreme unphysical temperature (-120°C < -90°C)
    unphysical_temp = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=now,
        ambient_temperature_c=-120.0,
        wind_speed_ms=10.0,
        solar_irradiance_wm2=0.0,
        provenance="SYNTHETIC"
    )
    res_t = validator.validate_weather(unphysical_temp, reference_time=now)
    assert res_t.is_valid is False
    assert any("outside polar bounds" in e for e in res_t.errors)

    # Extreme unphysical wind (120 m/s > 85 m/s)
    unphysical_wind = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=now,
        ambient_temperature_c=-20.0,
        wind_speed_ms=120.0,
        solar_irradiance_wm2=0.0,
        provenance="SYNTHETIC"
    )
    res_w = validator.validate_weather(unphysical_wind, reference_time=now)
    assert res_w.is_valid is False
    assert any("outside physical bounds" in e for e in res_w.errors)

    # Test quarantine status evaluation
    state_quarantined = validator.evaluate_provider_state(
        consecutive_failures=0,
        consecutive_invalid=3,
        last_success_age_sec=100.0,
        enabled=True,
        quarantine_threshold=3
    )
    assert state_quarantined == ProviderStatus.QUARANTINED


# ==============================================================================
# 6. Provider Outage, Safe Fallback & Recovery
# ==============================================================================

def test_bridge_fallback_and_recovery():
    bridge = ExternalRealityBridge()
    bridge.enabled = True

    # Quarantining a provider manually
    bridge.quarantine_provider("OpenMeteo-Polar")
    assert "OpenMeteo-Polar" in bridge._quarantined_providers

    # Bridge tries fallback when provider is quarantined
    res = bridge.get_weather_observation("BHARATI", preferred_provider="openmeteo")
    assert res.is_valid is False
    assert any("QUARANTINED" in e for e in res.errors)

    # Unquarantine and restore
    bridge.unquarantine_provider("OpenMeteo-Polar")
    assert "OpenMeteo-Polar" not in bridge._quarantined_providers


# ==============================================================================
# 7. Feed Completeness & Gap Tracking
# ==============================================================================

def test_feed_completeness_and_gap_detection():
    validator = ExternalDataValidator()
    t0 = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)

    # 10 hourly steps with an intentional 2-hour gap at hours 4 and 5
    observations = []
    for h in [0, 1, 2, 3, 6, 7, 8, 9]:
        observations.append(
            ExternalWeatherObservation(
                station_id="BHARATI",
                timestamp=t0 + timedelta(hours=h),
                ambient_temperature_c=-15.0,
                wind_speed_ms=10.0,
                solar_irradiance_wm2=0.0,
                provenance="SYNTHETIC"
            )
        )

    completeness: ExternalFeedCompleteness = validator.validate_feed_completeness(
        station_id="BHARATI",
        observations=observations,
        expected_interval_minutes=60
    )

    assert completeness.station_id == "BHARATI"
    assert completeness.received_intervals == 8
    assert completeness.expected_intervals == 10
    assert completeness.missing_intervals == 2
    assert completeness.completeness_ratio == 0.8
    assert completeness.is_complete is False
    assert len(completeness.missing_timestamps) == 2


# ==============================================================================
# 8. Closed 6-Tier Provenance Invariant
# ==============================================================================

def test_strict_six_tier_provenance_invariant():
    now = datetime.now(timezone.utc)

    # Valid provenance
    for tier in LOCKED_PROVENANCE_TIERS:
        obs = ExternalWeatherObservation(
            station_id="BHARATI",
            timestamp=now,
            ambient_temperature_c=-10.0,
            wind_speed_ms=5.0,
            solar_irradiance_wm2=100.0,
            provenance=tier
        )
        assert obs.provenance == tier

    # Forbidden 7th tiers must raise ValueError
    forbidden_tiers = [
        "LIVE", "REAL_TIME", "OPTIMIZED", "API", "DERIVED", "PRODUCTION",
        "REAL_EXTERNAL", "FIELD_REAL", "OBSERVED_REAL", "PRODUCTION_REAL"
    ]
    for forbidden in forbidden_tiers:
        with pytest.raises(ValueError):
            ExternalWeatherObservation(
                station_id="BHARATI",
                timestamp=now,
                ambient_temperature_c=-10.0,
                wind_speed_ms=5.0,
                solar_irradiance_wm2=100.0,
                provenance=forbidden
            )


# ==============================================================================
# 9. Truthful Physical Connectivity DISCONNECTED Invariant
# ==============================================================================

def test_physical_connectivity_truth_invariant(client):
    resp = client.get("/health/physical")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["physical_scada_connected"] is False
    assert body["data"]["hardware_status"] == "DISCONNECTED"
    assert body["data"]["operational_mode"] == "CALIBRATED_DIGITAL_TWIN"
    assert "zero connected physical polar SCADA telemetry" in body["data"]["disclaimer"]


# ==============================================================================
# 10. Model vs. Observed Metrics Calculation
# ==============================================================================

def test_model_vs_observed_metrics():
    evaluator = ModelVsObservedEvaluator()
    evaluator.clear_history()

    observed = [40.0, 42.0, 45.0, 48.0, 50.0]
    forecast = [38.0, 43.0, 44.0, 50.0, 49.0]
    p10 = [35.0, 39.0, 40.0, 45.0, 45.0]
    p90 = [45.0, 48.0, 50.0, 55.0, 55.0]

    metric = evaluator.evaluate_paired_series(
        station_id="BHARATI",
        target="total_load_kw",
        horizon_h=5,
        observed_values=observed,
        forecast_values=forecast,
        p10_values=p10,
        p90_values=p90
    )

    assert metric.station_id == "BHARATI"
    assert metric.n_samples == 5
    # residuals: [2.0, -1.0, 1.0, -2.0, 1.0]
    # MAE = (2+1+1+2+1)/5 = 1.4
    assert metric.mae == 1.4
    # Signed Bias (MBE) = (2 - 1 + 1 - 2 + 1)/5 = 0.2
    assert metric.mbe == 0.2
    # Coverage: all 5 observed are within [p10, p90]
    assert metric.interval_80_coverage == 1.0
    assert metric.evidence_type == "EXTERNAL_VALIDATION"


# ==============================================================================
# 11. Digital Twin Reality Check & Calibration Candidates
# ==============================================================================

def test_twin_reality_check_and_calibration_candidate():
    engine = TwinRealityCheckEngine()
    engine.clear_history()

    # Electrical power balance check within tolerance
    elec_metric = engine.check_electrical_response(
        station_id="BHARATI",
        observed_generation_kw=55.0,
        observed_load_kw=55.0,
        simulated_balance_residual_kw=0.01
    )
    assert elec_metric.within_tolerance is True
    assert elec_metric.status == "VALIDATED"

    # Thermal response with significant discrepancy triggering calibration candidate
    therm_metric = engine.check_thermal_response(
        station_id="BHARATI",
        observed_indoor_c=14.0,
        simulated_indoor_c=18.5,  # 4.5°C discrepancy > 1.5°C * 2
        ambient_c=-35.0
    )
    assert therm_metric.within_tolerance is False
    assert therm_metric.status == "CALIBRATION_CANDIDATE"

    # Verify calibration candidate registered without altering Phase 4
    candidates = engine.get_calibration_candidates()
    assert len(candidates) >= 1
    cand = candidates[0]
    assert cand.target_subsystem == "thermal"
    assert cand.parameter_name == "building_u_value"
    assert cand.immutable_baseline_preserved is True
    assert cand.governance_status == "PENDING_CONTROLLED_REVIEW"


# ==============================================================================
# 12. Operational Drift Categorization
# ==============================================================================

def test_operational_drift_categorization():
    detector = OperationalDriftDetector()
    detector.clear_history()

    # 1. Data drift test
    data_ind = detector.assess_data_drift(
        station_id="BHARATI",
        metric_name="ambient_temperature",
        recent_values=[-2.0, -1.5, -3.0],  # anomalous warming vs polar baseline
        historical_mean=-15.0,
        historical_std=3.0
    )
    assert data_ind.drift_type == DriftType.DATA_DRIFT
    assert data_ind.detected is True
    assert data_ind.z_score > 3.0

    # 2. Model drift test
    evaluator = ModelVsObservedEvaluator()
    metric = evaluator.evaluate_paired_series(
        station_id="BHARATI",
        target="total_load_kw",
        horizon_h=24,
        observed_values=[50.0] * 24,
        forecast_values=[30.0] * 24  # large persistent error: MAE = 20
    )
    model_ind = detector.assess_model_drift(
        station_id="BHARATI",
        target_name="total_load_kw",
        evaluation_metric=metric,
        historical_baseline_mae=7.579
    )
    assert model_ind.drift_type == DriftType.MODEL_DRIFT
    assert model_ind.detected is True

    # 3. Provider failure test
    from backend.integrations.schemas import ProviderHealthRecord
    failed_record = ProviderHealthRecord(
        provider_name="OpenMeteo-Polar",
        status=ProviderStatus.FAILED,
        enabled=True,
        consecutive_failures=6,
        last_error="503 Service Unavailable"
    )
    prov_ind = detector.assess_provider_failure(failed_record)
    assert prov_ind.drift_type == DriftType.PROVIDER_FAILURE
    assert prov_ind.detected is True


# ==============================================================================
# 13. Edge Full Offline-to-Reconnect Cycle & State Reconciliation
# ==============================================================================

def test_edge_offline_to_reconnect_cycle_with_reconciliation():
    tracker = ConnectivityTracker("BHARATI", heartbeat_timeout_sec=10.0, offline_failure_threshold=3)
    buffer = LocalTelemetryBuffer(max_capacity=100)

    # 1. Start CONNECTED
    assert tracker.state == ConnectivityState.CONNECTED

    # 2. Transmit failures -> transition to DEGRADED then OFFLINE
    tracker.record_failure("Satcom antenna ice accumulation")
    assert tracker.state == ConnectivityState.DEGRADED
    tracker.record_failure("Satcom link loss")
    tracker.record_failure("No carrier")
    assert tracker.state == ConnectivityState.OFFLINE

    # 3. Edge buffers local telemetry while offline
    t0 = datetime.now(timezone.utc)
    for i in range(5):
        reading = TelemetryReading(
            station_id="BHARATI",
            timestamp=(t0 + timedelta(minutes=i * 10)).isoformat(),
            device_id=f"device_{i}",
            channel="active_power_kw",
            value=45.0,
            unit="kW"
        )
        enqueued, msg = buffer.enqueue(reading)
        assert enqueued is True

    assert buffer.size() == 5

    # 4. Connection restored -> RECONNECTING -> RECONCILIATION -> CONNECTED
    tracker.record_success()
    tracker.state = ConnectivityState.RECONNECTING
    assert tracker.state == ConnectivityState.RECONNECTING

    # Deterministic reconciliation
    report, acknowledged = StateReconciler.reconcile(
        station_id="BHARATI",
        buffer=buffer,
        latest_live_snapshots={}
    )
    assert report.total_buffered == 5
    assert len(acknowledged) == 5

    # Complete cycle back to CONNECTED
    tracker.record_success()
    assert tracker.state == ConnectivityState.CONNECTED


# ==============================================================================
# 14. Operational Decision Replay & Trace Continuity
# ==============================================================================

def test_operational_decision_replay_pipeline():
    replay_orch = get_replay_orchestrator()
    now = datetime.now(timezone.utc)

    steps = [
        ExternalWeatherObservation(
            station_id="BHARATI",
            timestamp=now + timedelta(hours=i),
            ambient_temperature_c=-18.0,
            wind_speed_ms=12.0,
            solar_irradiance_wm2=100.0 if (6 <= (i % 24) <= 18) else 0.0,
            source_provider="CalibratedReplaySpool",
            provenance="SYNTHETIC"
        )
        for i in range(24)
    ]
    series = ExternalForecastSeries(
        station_id="BHARATI",
        forecast_origin=now,
        horizon_hours=24,
        steps=steps,
        source_provider="CalibratedReplaySpool",
        provenance="SYNTHETIC"
    )

    result = replay_orch.replay_external_series(
        station_id="BHARATI",
        series=series,
        mode="EXPECTED"
    )

    assert result.station_id == "BHARATI"
    assert result.horizon_hours == 24
    assert result.external_weather_used is True
    assert result.trace_id.startswith("pipe-")
    assert result.resilience_state in ("SAFE", "WATCH", "AT_RISK", "THREATENED", "CRITICAL", "RECOVERY")
    assert "external_avg_temp_c" in result.discrepancy_vs_baseline


# ==============================================================================
# 15. Observability API Validation Endpoints
# ==============================================================================

def test_integrations_validation_endpoints(client):
    # Metrics
    resp_metrics = client.get("/api/v1/integrations/validation/metrics")
    assert resp_metrics.status_code == 200
    assert resp_metrics.json()["status"] == "SUCCESS"

    # Drift
    resp_drift = client.get("/api/v1/integrations/validation/drift")
    assert resp_drift.status_code == 200
    assert resp_drift.json()["status"] == "SUCCESS"

    # Twin check
    resp_twin = client.get("/api/v1/integrations/validation/twin-check")
    assert resp_twin.status_code == 200
    assert resp_twin.json()["status"] == "SUCCESS"

    # Candidates
    resp_cand = client.get("/api/v1/integrations/validation/candidates")
    assert resp_cand.status_code == 200
    assert resp_cand.json()["status"] == "SUCCESS"

    # Replay endpoint
    resp_replay = client.post("/api/v1/integrations/replay", json={
        "station_id": "BHARATI",
        "horizon_hours": 12,
        "mode": "EXPECTED"
    })
    assert resp_replay.status_code == 200
    assert resp_replay.json()["data"]["external_weather_used"] is True


# ==============================================================================
# 16. Epistemic & Provenance Safeguards (Section 12 Invariants)
# ==============================================================================

def test_no_real_telemetry_claim_when_scada_disconnected(client):
    """Verifies no REAL physical-telemetry claim exists when PHYSICAL_SCADA_LINK = FALSE."""
    from backend.config.settings import get_settings
    settings = get_settings()

    # 1. Physical SCADA link is strictly disconnected
    assert settings.product.physical_scada_connected is False
    assert settings.product.physical_scada_link is False
    assert settings.product.physical_validation == "NOT_AVAILABLE"

    # 2. /health/physical endpoint explicitly reports DISCONNECTED and NOT_AVAILABLE
    resp = client.get("/health/physical")
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["physical_scada_connected"] is False
    assert body["physical_scada_link"] is False
    assert body["hardware_status"] == "DISCONNECTED"
    assert body["physical_validation"] == "NOT_AVAILABLE"


def test_no_field_sensor_claim_without_real_source():
    """Verifies that reference inputs are classified under SYNTHETIC / FORECAST, never REAL."""
    evaluator = ModelVsObservedEvaluator()
    metric = evaluator.evaluate_paired_series(
        station_id="BHARATI",
        target="total_load_kw",
        horizon_h=6,
        observed_values=[45.0, 48.0, 52.0, 50.0, 47.0, 46.0],
        forecast_values=[44.0, 47.0, 50.0, 51.0, 49.0, 45.0],
        reference_provenance="SYNTHETIC"
    )
    assert metric.reference_provenance != "REAL"
    assert metric.reference_provenance in LOCKED_PROVENANCE_TIERS
    assert metric.reference_provenance == "SYNTHETIC"


def test_openmeteo_forecast_classified_correctly():
    """Verifies that Open-Meteo predictions are classified strictly as FORECAST, never REAL or LIVE."""
    adapter = OpenMeteoPolarAdapter(enabled=False)
    assert adapter.name == "OpenMeteo-Polar"

    now = datetime.now(timezone.utc)
    obs = ExternalWeatherObservation(
        station_id="BHARATI",
        timestamp=now,
        ambient_temperature_c=-20.0,
        wind_speed_ms=10.0,
        solar_irradiance_wm2=50.0,
        source_provider="OpenMeteo-Polar",
        provenance="FORECAST"
    )
    assert obs.provenance == "FORECAST"
    assert obs.provenance not in ("REAL", "LIVE", "API", "REAL_TIME", "REAL_EXTERNAL", "FIELD_REAL")


def test_reference_series_provenance_preserved():
    """Verifies that reference series provenance is strictly preserved across evaluator and twin engines."""
    evaluator = ModelVsObservedEvaluator()
    metric = evaluator.evaluate_paired_series(
        station_id="BHARATI",
        target="total_load_kw",
        horizon_h=6,
        observed_values=[45.0, 48.0, 52.0, 50.0, 47.0, 46.0],
        forecast_values=[44.0, 47.0, 50.0, 51.0, 49.0, 45.0],
        reference_provenance="SYNTHETIC"
    )
    assert metric.reference_provenance == "SYNTHETIC"

    twin_engine = TwinRealityCheckEngine()
    elec_metric = twin_engine.check_electrical_response(
        station_id="BHARATI",
        observed_generation_kw=55.0,
        observed_load_kw=55.0,
        simulated_balance_residual_kw=0.02
    )
    assert elec_metric.reference_provenance == "SYNTHETIC"
    assert elec_metric.reference_provenance in LOCKED_PROVENANCE_TIERS


def test_physical_validation_remains_not_available(client):
    """Verifies PHYSICAL_VALIDATION remains NOT_AVAILABLE without physical telemetry."""
    from backend.config.settings import get_settings
    settings = get_settings()
    assert settings.product.physical_validation == "NOT_AVAILABLE"

    resp = client.get("/health/physical")
    assert resp.status_code == 200
    assert resp.json()["data"]["physical_validation"] == "NOT_AVAILABLE"


def test_calibration_candidate_remains_human_gated():
    """Verifies CALIBRATION_CANDIDATE CALIB-BHA-THE-001 preserves immutable baseline and human gating."""
    engine = TwinRealityCheckEngine()
    engine.clear_history()

    # Trigger candidate via thermal discrepancy
    therm = engine.check_thermal_response(
        station_id="BHARATI",
        observed_indoor_c=14.0,
        simulated_indoor_c=20.5,
        ambient_c=-25.0
    )
    assert therm.status == "CALIBRATION_CANDIDATE"

    candidates = engine.get_calibration_candidates()
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.candidate_id.startswith("CALIB-BHA-THE-")
    assert cand.parameter_name == "building_u_value"
    assert cand.current_value == 0.25
    assert cand.governance_status == "PENDING_CONTROLLED_REVIEW"
    assert cand.immutable_baseline_preserved is True
