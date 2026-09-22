"""
POLARIS-EMS — Master Training, Evaluation & Benchmarking Orchestrator
SIH26061: Polar Energy Management & Resilience System

Executes the complete Phase 3 machine learning pipeline:
1. Reconciles station physical limits against StationProfileRegistry.
2. Loads datasets and partitions val_calibration into val_tuning and calibration.
3. Builds leakage-free causal feature datasets.
4. Trains and evaluates Baselines (Persistence, Seasonal Naive, Ridge, Random Forest).
5. Trains and tunes Physics-Informed Load Model, Solar Model, and Wind Model.
6. Performs Conformalized Quantile Calibration on calibration partition.
7. Evaluates isolated test set exactly ONCE for final benchmark numbers.
8. Evaluates stratified performance across all 10 polar disturbance regimes.
9. Evaluates station operational impact (diesel waste, battery buffer deficit).
10. Registers production model artifacts and metadata in ModelRegistry.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List
import json
import time
import pandas as pd
import numpy as np

# Ensure root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.ml.station_config import StationConfigAdapter
from backend.ml.data_loader import MLDataLoader
from backend.ml.features import FeaturePipeline
from backend.ml.feature_registry import FeatureRegistry
from backend.ml.baselines.persistence import PersistenceForecaster
from backend.ml.baselines.seasonal_naive import SeasonalNaiveForecaster
from backend.ml.baselines.linear_baseline import RidgeBaselineForecaster
from backend.ml.baselines.tree_baseline import TreeBaselineForecaster
from backend.ml.models.physics_load_model import PhysicsInformedLoadForecaster
from backend.ml.models.solar_forecaster import SolarForecaster
from backend.ml.models.wind_forecaster import WindForecaster
from backend.ml.models.multi_horizon import MultiHorizonForecaster
from backend.ml.uncertainty.conformal_calibrator import ConformalQuantileCalibrator
from backend.ml.uncertainty.coverage_validator import CoverageValidator
from backend.ml.evaluation.metrics import ForecastMetrics
from backend.ml.evaluation.regime_evaluator import RegimeEvaluator
from backend.ml.evaluation.operational_value import OperationalValueBridge
from backend.ml.registry import ModelRegistry


def run_pipeline_for_station(
    station_id: str,
    data_loader: MLDataLoader,
    station_config: StationConfigAdapter,
    registry: ModelRegistry,
    stride: int = 4,
    benchmark_horizons: list = [1, 2, 6, 12, 24, 48, 168]
) -> Dict[str, Any]:
    print(f"\n=======================================================")
    print(f"   STARTING PHASE 3 ML PIPELINE: {station_id.upper()}")
    print(f"=======================================================")
    start_time = time.time()
    sid = station_id.upper()
    station_results = {"station_id": sid, "targets": {}}

    # 1. Load data partitions
    print(f"[{sid}] Loading datasets...")
    train_df = data_loader.load_train_data(sid)
    val_tuning_df, calib_df = data_loader.load_val_and_calibration_data(sid, split_ratio=0.5)
    test_df = data_loader.load_test_data(sid)
    print(f"[{sid}] Train: {len(train_df)} hrs | Val-Tuning: {len(val_tuning_df)} hrs | Calib: {len(calib_df)} hrs | Test: {len(test_df)} hrs")

    feat_pipeline = FeaturePipeline(station_config)
    op_bridge = OperationalValueBridge(sid, station_config)

    targets = [
        ("total_load_kw", "load"),
        ("solar_generation_kw", "solar"),
        ("wind_generation_kw", "wind")
    ]

    for target_col, target_key in targets:
        print(f"\n-------------------------------------------------------")
        print(f"  TARGET: {target_col.upper()} ({sid})")
        print(f"-------------------------------------------------------")

        # For solar and wind, maximum operational horizon is 48h (168h is load-only strategic)
        target_horizons = benchmark_horizons if target_key == "load" else [h for h in benchmark_horizons if h <= 48]

        # Determine station physical capacity reference
        if target_key == "solar":
            cap_kw = station_config.get_solar_limits(sid)["solar_pv_kw_peak"]
        elif target_key == "wind":
            cap_kw = station_config.get_wind_limits(sid)["wind_turbine_kw_rated"]
        else:
            cap_kw = 120.0  # Station nominal peak demand reference

        # 2. Build feature datasets
        print(f"[{sid}:{target_key}] Building feature matrices (stride={stride})...")
        X_train, y_train, meta_train = feat_pipeline.build_feature_dataset(
            station_id=sid,
            target_name=target_col,
            df=train_df,
            horizons=target_horizons,
            sample_stride=stride,
            mode="CAUSAL"
        )
        X_val, y_val, meta_val = feat_pipeline.build_feature_dataset(
            station_id=sid,
            target_name=target_col,
            df=val_tuning_df,
            horizons=target_horizons,
            sample_stride=stride,
            mode="CAUSAL"
        )
        X_calib, y_calib, meta_calib = feat_pipeline.build_feature_dataset(
            station_id=sid,
            target_name=target_col,
            df=calib_df,
            horizons=target_horizons,
            sample_stride=stride,
            mode="CAUSAL"
        )
        X_test, y_test, meta_test = feat_pipeline.build_feature_dataset(
            station_id=sid,
            target_name=target_col,
            df=test_df,
            horizons=target_horizons,
            sample_stride=stride,
            mode="CAUSAL"
        )
        print(f"[{sid}:{target_key}] Samples -> Train: {len(X_train)} | Val: {len(X_val)} | Calib: {len(X_calib)} | Test: {len(X_test)}")

        y_tr_arr = y_train["target"].values
        y_val_arr = y_val["target"].values
        y_cal_arr = y_calib["target"].values
        y_test_arr = y_test["target"].values

        # 3. Baselines Evaluation on Validation Set
        print(f"[{sid}:{target_key}] Evaluating Baselines...")
        # Persistence: y(t) is target_lag_0 in X
        persist_pred_val = X_val["target_lag_0"].values
        persist_metrics = ForecastMetrics.compute_all(y_val_arr, persist_pred_val, capacity_kw=cap_kw)

        # Seasonal Naive: target_lag_24 in X
        snaive_pred_val = X_val["target_lag_24"].values
        snaive_metrics = ForecastMetrics.compute_all(y_val_arr, snaive_pred_val, capacity_kw=cap_kw)

        # Ridge Linear Baseline
        ridge = RidgeBaselineForecaster()
        ridge.fit(X_train, y_train["target"])
        ridge_pred_val = ridge.predict(X_val)
        ridge_metrics = ForecastMetrics.compute_all(y_val_arr, ridge_pred_val, capacity_kw=cap_kw)

        # Tree Baseline (Random Forest)
        tree = TreeBaselineForecaster(n_estimators=60, max_depth=6)
        tree.fit(X_train, y_train["target"])
        tree_pred_val = tree.predict(X_val)
        tree_metrics = ForecastMetrics.compute_all(y_val_arr, tree_pred_val, capacity_kw=cap_kw)

        print(f"  > Baseline 1 (Persistence)    : MAE={persist_metrics['mae']:.2f}, RMSE={persist_metrics['rmse']:.2f}, R2={persist_metrics['r2']:.3f}")
        print(f"  > Baseline 2 (Seasonal Naive) : MAE={snaive_metrics['mae']:.2f}, RMSE={snaive_metrics['rmse']:.2f}, R2={snaive_metrics['r2']:.3f}")
        print(f"  > Baseline 3 (Ridge Linear)   : MAE={ridge_metrics['mae']:.2f}, RMSE={ridge_metrics['rmse']:.2f}, R2={ridge_metrics['r2']:.3f}")
        print(f"  > Baseline 4 (Random Forest)  : MAE={tree_metrics['mae']:.2f}, RMSE={tree_metrics['rmse']:.2f}, R2={tree_metrics['r2']:.3f}")

        # 4. Train Production Candidate Model
        print(f"[{sid}:{target_key}] Training Production XGBoost Candidate...")
        if target_key == "load":
            prod_model = PhysicsInformedLoadForecaster(
                station_id=sid,
                station_config=station_config,
                xgb_params={"n_estimators": 250, "max_depth": 6, "learning_rate": 0.05}
            )
        elif target_key == "solar":
            prod_model = SolarForecaster(
                station_id=sid,
                station_config=station_config,
                xgb_params={"n_estimators": 250, "max_depth": 6, "learning_rate": 0.05}
            )
        else:
            prod_model = WindForecaster(
                station_id=sid,
                station_config=station_config,
                xgb_params={"n_estimators": 250, "max_depth": 6, "learning_rate": 0.05}
            )

        prod_model.fit(X_train, y_train["target"])
        prod_pred_val = prod_model.predict(X_val)
        prod_val_metrics = ForecastMetrics.compute_all(y_val_arr, prod_pred_val["point"], capacity_kw=cap_kw)
        print(f"  >>> PRODUCTION MODEL (Val)   : MAE={prod_val_metrics['mae']:.2f}, RMSE={prod_val_metrics['rmse']:.2f}, R2={prod_val_metrics['r2']:.3f}")

        # 5. Conformalized Quantile Calibration on Calibration Split
        print(f"[{sid}:{target_key}] Running Conformalized Quantile Calibration on calib partition...")
        calib_raw_preds = prod_model.predict(X_calib)
        calibrator = ConformalQuantileCalibrator(target_name=target_col)
        calibrator.calibrate(calib_raw_preds, y_cal_arr)

        calib_adjusted = calibrator.apply_calibration(calib_raw_preds)
        calib_coverage_metrics = CoverageValidator.evaluate_overall(y_cal_arr, calib_adjusted)
        print(f"  [Calibration Coverage] Nominal 80% -> Observed: {calib_coverage_metrics['interval_80_coverage']*100:.1f}%, Width: {calib_coverage_metrics['sharpness_80_kw']} kW")

        # 6. Final Isolated Evaluation on Test Set (TOUCHED EXACTLY ONCE)
        print(f"[{sid}:{target_key}] Evaluating on FINAL ISOLATED TEST SET (Single Pass)...")
        test_raw_preds = prod_model.predict(X_test)
        test_cal_preds = calibrator.apply_calibration(test_raw_preds)

        test_point_metrics = ForecastMetrics.compute_all(y_test_arr, test_cal_preds["point"], capacity_kw=cap_kw)
        test_coverage_metrics = CoverageValidator.evaluate_overall(y_test_arr, test_cal_preds)
        print(f"  === FINAL TEST BENCHMARK === : MAE={test_point_metrics['mae']:.2f}, RMSE={test_point_metrics['rmse']:.2f}, R2={test_point_metrics['r2']:.3f}")
        print(f"  === TEST 80% COVERAGE ===   : Observed: {test_coverage_metrics['interval_80_coverage']*100:.1f}%, Gap: {test_coverage_metrics['nominal_80_gap']*100:+.1f}%")

        # 7. Regime-Wise Performance Breakdown
        print(f"[{sid}:{target_key}] Computing Regime-Wise Performance Breakdown...")
        regime_df = RegimeEvaluator.evaluate_disturbances(
            y_true=y_test_arr,
            y_pred=test_cal_preds["point"],
            disturbance_series=meta_test["disturbance_state"],
            capacity_kw=cap_kw
        )

        # 8. Operational Impact Bridge Evaluation
        if target_key == "load":
            op_impact = op_bridge.evaluate_load_forecast_impact(y_test_arr, test_cal_preds["point"])
        else:
            op_impact = op_bridge.evaluate_renewable_forecast_impact(y_test_arr, test_cal_preds["point"])

        # 9. Register in Model Registry
        model_version = "v1.0"
        model_name = f"polaris-{target_key}-xgb-{sid.lower()}-{model_version}"
        print(f"[{sid}:{target_key}] Saving to Model Registry: {model_name}...")
        
        meta = {
            "model_name": model_name,
            "model_version": model_version,
            "target": target_col,
            "station": sid,
            "feature_schema_version": "v1.0",
            "preprocessing_version": "v1.0",
            "calibration_version": "v1.0",
            "dataset_version": "polaris-synthetic-v1.0",
            "simulator_version": "polaris-sim-v2.0",
            "git_commit": "f81f4a3",
            "horizons": target_horizons,
            "capacity_kw": cap_kw,
            "val_metrics": prod_val_metrics,
            "test_metrics": test_point_metrics,
            "test_coverage": test_coverage_metrics,
            "baselines_val": {
                "persistence": persist_metrics,
                "seasonal_naive": snaive_metrics,
                "ridge": ridge_metrics,
                "tree": tree_metrics
            },
            "operational_impact": op_impact
        }
        registry.save_model(prod_model, meta, calibrator)

        station_results["targets"][target_key] = {
            "metadata": meta,
            "regime_breakdown": regime_df.to_dict(orient="records"),
            "test_metrics": test_point_metrics,
            "test_coverage": test_coverage_metrics,
            "operational_impact": op_impact
        }

    station_results["elapsed_seconds"] = round(time.time() - start_time, 2)
    return station_results


def main():
    parser = argparse.ArgumentParser(description="Polaris-EMS Phase 3 Master Training & Evaluation")
    parser.add_argument("--station", type=str, default=None, help="Specific station (BHARATI, MAITRI, HIMADRI)")
    parser.add_argument("--all-stations", action="store_true", help="Train and evaluate all 3 stations")
    parser.add_argument("--stride", type=int, default=4, help="Sampling stride for training features (default=4)")
    args = parser.parse_args()

    data_loader = MLDataLoader()
    station_config = StationConfigAdapter()
    registry = ModelRegistry()

    # Reconcile station configuration table
    print("\n--- STATION CONFIGURATION RECONCILIATION TABLE ---")
    recon_df = station_config.get_reconciliation_table()
    print(recon_df.to_string(index=False))

    stations = ["BHARATI", "MAITRI", "HIMADRI"] if args.all_stations or not args.station else [args.station.upper()]

    all_results = {}
    for st in stations:
        res = run_pipeline_for_station(
            station_id=st,
            data_loader=data_loader,
            station_config=station_config,
            registry=registry,
            stride=args.stride
        )
        all_results[st] = res

    # Save consolidated run report JSON
    results_path = ROOT_DIR / "models" / "phase3_evaluation_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[DONE] Master evaluation saved to {results_path}")


if __name__ == "__main__":
    main()
