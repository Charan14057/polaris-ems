"""
POLARIS-EMS — Phase 3 ML Forecasting Automated Test Suite
SIH26061: Polar Energy Management & Resilience System

Validates:
1. Leakage prevention: Causal seasonal naive indexing and weather provider causality.
2. Station configuration: Dynamic physical bounds loaded from configs/station_profiles.json.
3. Physics constraints: Solar night zeroing, wind cut-out zeroing, load positivity.
4. Probabilistic calibration: Quantile monotonicity (P10 <= P50 <= P90 <= P95) and coverage sanity.
5. Model registry & inference: Serialization reproducibility and provenance="FORECAST".
"""

import pytest
from pathlib import Path
import numpy as np
import pandas as pd

from backend.ml.station_config import StationConfigAdapter
from backend.ml.weather_provider import WeatherForecastProvider
from backend.ml.data_loader import MLDataLoader
from backend.ml.features import FeaturePipeline
from backend.ml.feature_registry import FeatureRegistry
from backend.ml.baselines.persistence import PersistenceForecaster
from backend.ml.baselines.seasonal_naive import SeasonalNaiveForecaster, get_causal_seasonal_reference_index
from backend.ml.baselines.linear_baseline import RidgeBaselineForecaster
from backend.ml.models.physics_load_model import PhysicsInformedLoadForecaster
from backend.ml.models.solar_forecaster import SolarForecaster
from backend.ml.models.wind_forecaster import WindForecaster
from backend.ml.uncertainty.conformal_calibrator import ConformalQuantileCalibrator
from backend.ml.uncertainty.coverage_validator import CoverageValidator
from backend.ml.registry import ModelRegistry
from backend.ml.inference import InferenceEngine, ForecastResult


@pytest.fixture
def station_config():
    return StationConfigAdapter()


@pytest.fixture
def sample_history_df():
    # 72 hours of mock historical telemetry
    timestamps = pd.date_range("2025-01-01 00:00:00+00:00", periods=72, freq="h")
    return pd.DataFrame({
        "timestamp": timestamps,
        "temperature_c": np.linspace(-15.0, -20.0, 72),
        "wind_speed_ms": np.linspace(6.0, 12.0, 72),
        "pressure_hpa": np.linspace(990.0, 980.0, 72),
        "cloud_fraction": np.full(72, 0.4),
        "irradiance_wm2": np.full(72, 150.0),
        "solar_elevation_deg": np.full(72, 15.0),
        "total_load_kw": np.linspace(65.0, 75.0, 72),
        "solar_generation_kw": np.full(72, 5.0),
        "wind_generation_kw": np.full(72, 10.0),
        "occupancy_state": np.full(72, 0.5),
        "maintenance_state": np.zeros(72),
        "research_activity_state": np.full(72, 0.5),
        "communication_state": np.zeros(72),
        "disturbance_state": ["NORMAL"] * 72
    })


def test_station_configuration_reconciliation(station_config):
    """Verifies that physical capacities are loaded dynamically without hardcoding."""
    table = station_config.get_reconciliation_table()
    assert len(table) == 3
    stations = set(table["station_id"])
    assert "BHARATI" in stations
    assert "MAITRI" in stations
    assert "HIMADRI" in stations

    # Check verified ratings match single source of truth
    bh_pv = station_config.get_solar_limits("BHARATI")["solar_pv_kw_peak"]
    assert bh_pv == 30.0
    bh_wind = station_config.get_wind_limits("BHARATI")["wind_turbine_kw_rated"]
    assert bh_wind == 25.0

    mt_pv = station_config.get_solar_limits("MAITRI")["solar_pv_kw_peak"]
    assert mt_pv == 18.0
    mt_wind = station_config.get_wind_limits("MAITRI")["wind_turbine_kw_rated"]
    assert mt_wind == 15.0

    hm_pv = station_config.get_solar_limits("HIMADRI")["solar_pv_kw_peak"]
    assert hm_pv == 12.0
    hm_wind = station_config.get_wind_limits("HIMADRI")["wind_turbine_kw_rated"]
    assert hm_wind == 10.0


def test_seasonal_naive_causal_index_no_leakage():
    """Verifies that reference_timestamp <= origin_timestamp for all horizons k >= 1."""
    # Ensure sufficient history for 168h weekly cycle
    origin_idx = 500
    for k in range(1, 169):
        # 24h diurnal cycle
        ref_24 = get_causal_seasonal_reference_index(origin_idx, k, season_period=24)
        assert ref_24 <= origin_idx, f"Diurnal ref {ref_24} > origin {origin_idx} for k={k}"
        assert (origin_idx + k) % 24 == ref_24 % 24, "Phase mismatch in 24h seasonal naive"

        # 168h weekly cycle
        ref_168 = get_causal_seasonal_reference_index(origin_idx, k, season_period=168)
        assert ref_168 <= origin_idx, f"Weekly ref {ref_168} > origin {origin_idx} for k={k}"
        assert (origin_idx + k) % 168 == ref_168 % 168, "Phase mismatch in 168h seasonal naive"


def test_weather_forecast_provider_causality(sample_history_df):
    """Verifies that WeatherForecastProvider generates causal forecasts without reading future rows."""
    provider = WeatherForecastProvider()
    origin_time = sample_history_df.iloc[40]["timestamp"]
    history_cut = sample_history_df.iloc[:41]
    horizons = [1, 6, 12, 24, 48]

    res = provider.predict(
        station_id="BHARATI",
        forecast_origin=origin_time,
        horizons=horizons,
        historical_weather_df=history_cut,
        mode="CAUSAL"
    )

    assert res.provenance == "FORECAST"
    assert len(res.df) == len(horizons)
    assert (res.df["temperature_c"] < 10.0).all()  # Antarctic realistic temps
    assert (res.df["wind_speed_ms"] >= 0.0).all()
    assert (res.df["cloud_fraction"] >= 0.0).all() and (res.df["cloud_fraction"] <= 1.0).all()


def test_feature_pipeline_no_future_leakage(sample_history_df):
    """Verifies that feature extraction consumes only <= origin_t telemetry."""
    pipeline = FeaturePipeline()
    origin_time = sample_history_df.iloc[50]["timestamp"]
    history_cut = sample_history_df.iloc[:51]

    feats = pipeline.extract_features_step(
        station_id="BHARATI",
        target_name="total_load_kw",
        forecast_origin=origin_time,
        horizon_k=6,
        history_df=history_cut
    )

    # Check that origin telemetry matches the exact cut row
    assert feats["origin_temperature_c"] == sample_history_df.iloc[50]["temperature_c"]
    assert feats["target_lag_0"] == sample_history_df.iloc[50]["total_load_kw"]
    assert feats["target_lag_1"] == sample_history_df.iloc[49]["total_load_kw"]
    assert feats["horizon_k"] == 6.0


def test_solar_forecaster_night_zero_constraint(station_config):
    """Verifies that solar forecasts strictly produce 0.0 kW when sun is below horizon."""
    forecaster = SolarForecaster(station_id="BHARATI", station_config=station_config)
    
    # Create synthetic training and test features
    X = pd.DataFrame({
        "solar_elevation_deg": [-15.0, -5.0, 0.0, 10.0, 25.0],
        "is_daylight": [0.0, 0.0, 0.0, 1.0, 1.0],
        "forecast_cloud_fraction": [0.5, 0.5, 0.5, 0.2, 0.1],
        "forecast_irradiance_wm2": [0.0, 0.0, 0.0, 200.0, 500.0],
        "forecast_temperature_c": [-10.0, -10.0, -10.0, -5.0, 0.0],
        "target_lag_0": [0.0, 0.0, 0.0, 5.0, 12.0]
    })
    y = pd.Series([0.0, 0.0, 0.0, 5.5, 14.0])

    forecaster.fit(X, y)
    preds = forecaster.predict(X)

    # First 3 samples have elevation <= 0 -> MUST be exactly 0.0 kW
    assert np.all(preds["point"][:3] == 0.0)
    assert np.all(preds["P10"][:3] == 0.0)
    assert np.all(preds["P90"][:3] == 0.0)
    assert np.all(preds["P95"][:3] == 0.0)
    # Daylight samples must be bounded by PV peak (30 kW)
    assert np.all(preds["point"][3:] <= 30.0)


def test_wind_forecaster_cut_in_cut_out_constraint(station_config):
    """Verifies that wind turbine cut-in (<3 m/s) and cut-out (>25 m/s) zero generation."""
    forecaster = WindForecaster(station_id="BHARATI", station_config=station_config)
    
    # Bharati cut-in = 3.0 m/s, cut-out = 25.0 m/s, rated = 25.0 kW
    X = pd.DataFrame({
        "forecast_wind_speed_ms": [1.5, 2.8, 8.0, 15.0, 26.5, 32.0],
        "origin_wind_speed_ms": [1.5, 2.8, 8.0, 15.0, 26.5, 32.0],
        "origin_pressure_hpa": [990.0, 990.0, 985.0, 975.0, 960.0, 955.0],
        "barometric_trend_3h": [0.0, 0.0, -2.0, -5.0, -12.0, -15.0],
        "target_lag_0": [0.0, 0.0, 10.0, 22.0, 0.0, 0.0]
    })
    y = pd.Series([0.0, 0.0, 11.0, 24.0, 0.0, 0.0])

    forecaster.fit(X, y)
    preds = forecaster.predict(X)

    # Sub-cut-in (indices 0, 1) and storm cut-out (indices 4, 5) MUST produce 0.0 kW
    assert preds["point"][0] == 0.0
    assert preds["point"][1] == 0.0
    assert preds["point"][4] == 0.0
    assert preds["point"][5] == 0.0
    # Operating regime must be clamped to rated capacity (25 kW)
    assert (preds["point"] <= 25.0).all()


def test_conformal_calibrator_monotonicity():
    """Verifies that ConformalQuantileCalibrator enforces P10 <= P50 <= P90 <= P95."""
    calibrator = ConformalQuantileCalibrator()
    
    # Calibration data
    n_cal = 100
    y_cal = np.random.uniform(50.0, 80.0, n_cal)
    raw_cal = {
        "point": y_cal + np.random.normal(0, 3, n_cal),
        "P10": y_cal - 6.0,
        "P50": y_cal,
        "P90": y_cal + 6.0,
        "P95": y_cal + 9.0
    }
    calibrator.calibrate(raw_cal, y_cal)

    # Test raw predictions with intentional crossings
    raw_test = {
        "point": np.array([60.0, 70.0]),
        "P10": np.array([65.0, 68.0]),  # Intentionally higher than P50 in sample 0
        "P50": np.array([60.0, 70.0]),
        "P90": np.array([58.0, 75.0]),  # Intentionally lower in sample 0
        "P95": np.array([62.0, 80.0])
    }
    cal_out = calibrator.apply_calibration(raw_test)

    # Check monotonicity invariant
    for i in range(len(raw_test["point"])):
        assert cal_out["P10"][i] <= cal_out["P50"][i], f"Crossing at idx {i}: P10 > P50"
        assert cal_out["P50"][i] <= cal_out["P90"][i], f"Crossing at idx {i}: P50 > P90"
        assert cal_out["P90"][i] <= cal_out["P95"][i], f"Crossing at idx {i}: P90 > P95"
        assert cal_out["P10"][i] >= 0.0


def test_model_registry_save_load_roundtrip(tmp_path):
    """Verifies that ModelRegistry saves and loads model artifacts with perfect fidelity."""
    registry = ModelRegistry(registry_root=tmp_path)
    forecaster = RidgeBaselineForecaster()
    X = pd.DataFrame({"feat1": [1.0, 2.0, 3.0], "feat2": [4.0, 5.0, 6.0]})
    y = pd.Series([10.0, 20.0, 30.0])
    forecaster.fit(X, y)

    meta = {
        "model_name": "test-ridge-bharati-v1.0",
        "model_version": "v1.0",
        "target": "total_load_kw",
        "station": "BHARATI",
        "feature_schema_version": "v1.0",
        "git_commit": "f81f4a3"
    }
    registry.save_model(forecaster, meta)

    loaded_model, calibrator, loaded_meta = registry.load_model("test-ridge-bharati-v1.0")
    assert loaded_meta["model_name"] == meta["model_name"]
    assert loaded_meta["git_commit"] == "f81f4a3"

    # Compare predictions
    orig_pred = forecaster.predict(X)
    load_pred = loaded_model.predict(X)
    np.testing.assert_allclose(orig_pred, load_pred, rtol=1e-5)


def test_inference_engine_provenance_and_schema(tmp_path, sample_history_df):
    """Verifies that InferenceEngine outputs typed ForecastResult with provenance='FORECAST'."""
    registry = ModelRegistry(registry_root=tmp_path)
    
    # Train and register a simple forecaster
    station_config = StationConfigAdapter()
    load_model = PhysicsInformedLoadForecaster(station_id="BHARATI", station_config=station_config)
    pipeline = FeaturePipeline(station_config)
    
    # Build minimal features
    origin_time = sample_history_df.iloc[48]["timestamp"]
    history_cut = sample_history_df.iloc[:49]
    feat_row = pipeline.extract_features_step("BHARATI", "total_load_kw", origin_time, 1, history_cut)
    X = pd.DataFrame([feat_row, feat_row])
    y = pd.Series([70.0, 72.0])
    load_model.fit(X, y)

    meta = {
        "model_name": "polaris-load-xgb-bharati-v1.0",
        "model_version": "v1.0",
        "target": "total_load_kw",
        "station": "BHARATI",
        "feature_schema_version": "v1.0",
        "git_commit": "f81f4a3"
    }
    registry.save_model(load_model, meta)

    # Execute inference
    engine = InferenceEngine(registry=registry, station_config=station_config)
    horizons = [1, 2, 6, 12, 24]
    result = engine.forecast(
        station_id="BHARATI",
        target_name="total_load_kw",
        forecast_origin=origin_time,
        horizons=horizons,
        historical_df=history_cut
    )

    assert isinstance(result, ForecastResult)
    assert result.provenance == "FORECAST"
    assert result.station_id == "BHARATI"
    assert len(result.point_predictions) == len(horizons)
    assert len(result.p10) == len(horizons)
    assert len(result.p95) == len(horizons)
    # Check that quantiles are ordered
    for i in range(len(horizons)):
        assert result.p10[i] <= result.p50[i] <= result.p90[i] <= result.p95[i]
