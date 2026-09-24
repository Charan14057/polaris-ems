"""
POLARIS-EMS — Real-World Model vs. Observation Evaluation Engine
SIH26061: Polar Energy Management & Resilience System

Phase 15 Workstream E: Model vs. Observation Evaluation Layer
Computes operational residuals, signed bias, MAE, RMSE, sMAPE, and conformal coverage
between paired external real-world observations and frozen Phase 3 predictions.

INVARIANT:
Does NOT overwrite Phase 13 benchmark artifacts. Creates a separate operational evaluation layer.
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from backend.integrations.schemas import (
    ModelVsObservedMetric,
    ExternalWeatherObservation,
)


class ModelVsObservedEvaluator:
    """Evaluates operational predictive performance against external observations."""

    def __init__(self):
        # Rolling repository of operational evaluation records
        self._history: List[ModelVsObservedMetric] = []

    def evaluate_paired_series(
        self,
        station_id: str,
        target: str,
        horizon_h: int,
        observed_values: List[float],
        forecast_values: List[float],
        p10_values: Optional[List[float]] = None,
        p90_values: Optional[List[float]] = None,
        weather_regime: str = "NORMAL",
        data_source: str = "OpenMeteo",
        reference_provenance: str = "SYNTHETIC"
    ) -> ModelVsObservedMetric:
        """
        Computes exhaustive operational verification metrics for a paired observed vs forecast series.
        """
        n = min(len(observed_values), len(forecast_values))
        if n == 0:
            return ModelVsObservedMetric(
                station_id=station_id.upper(),
                target=target,
                horizon_h=horizon_h,
                n_samples=0,
                observed_mean=0.0,
                forecast_mean=0.0,
                residuals=[],
                mae=0.0,
                rmse=0.0,
                mbe=0.0,
                smape=0.0,
                interval_80_coverage=1.0,
                evidence_type="EXTERNAL_VALIDATION",
                reference_provenance=reference_provenance
            )

        obs = observed_values[:n]
        fc = forecast_values[:n]
        residuals = [float(o - f) for o, f in zip(obs, fc)]

        obs_mean = sum(obs) / n
        fc_mean = sum(fc) / n

        # MAE
        mae = sum(abs(r) for r in residuals) / n

        # RMSE
        rmse = math.sqrt(sum(r ** 2 for r in residuals) / n)

        # Signed Bias (MBE: Mean Bias Error = mean(observed - forecast))
        mbe = sum(residuals) / n

        # sMAPE
        smape_sum = 0.0
        for o, f in zip(obs, fc):
            denom = abs(o) + abs(f) + 1e-6
            smape_sum += (2.0 * abs(o - f)) / denom
        smape = (smape_sum / n) * 100.0

        # Empirical 80% conformal interval coverage [P10, P90]
        coverage = 1.0
        if p10_values and p90_values and len(p10_values) >= n and len(p90_values) >= n:
            in_interval = sum(
                1 for i in range(n)
                if p10_values[i] <= obs[i] <= p90_values[i]
            )
            coverage = in_interval / n

        metric = ModelVsObservedMetric(
            station_id=station_id.upper(),
            target=target,
            horizon_h=horizon_h,
            n_samples=n,
            observed_mean=round(obs_mean, 3),
            forecast_mean=round(fc_mean, 3),
            residuals=[round(r, 3) for r in residuals],
            mae=round(mae, 3),
            rmse=round(rmse, 3),
            mbe=round(mbe, 3),
            smape=round(smape, 2),
            interval_80_coverage=round(coverage, 4),
            evidence_type="EXTERNAL_VALIDATION",
            reference_provenance=reference_provenance
        )

        self._history.append(metric)
        return metric

    def get_summary_by_station(self, station_id: str) -> List[ModelVsObservedMetric]:
        """Returns all historical operational evaluations for a station."""
        sid = station_id.upper()
        return [m for m in self._history if m.station_id == sid]

    def get_all_metrics(self) -> List[ModelVsObservedMetric]:
        """Returns all recorded operational evaluation metrics."""
        return list(self._history)

    def clear_history(self):
        """Clears memory history (primarily for test isolation)."""
        self._history.clear()


_evaluator_instance: Optional[ModelVsObservedEvaluator] = None


def get_model_evaluator() -> ModelVsObservedEvaluator:
    """Singleton getter for operational model evaluator."""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = ModelVsObservedEvaluator()
    return _evaluator_instance
