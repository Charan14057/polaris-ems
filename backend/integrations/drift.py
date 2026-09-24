"""
POLARIS-EMS — Real-Time Operational Drift Detection Engine
SIH26061: Polar Energy Management & Resilience System

Phase 15 Workstream G: Operational Drift Monitoring
Evaluates distribution shifts and operational degradations across polar microgrid assets.
Distinguishes between:
1. DATA_DRIFT: Input distribution changes (ambient temperature, wind velocity shifts)
2. MODEL_DRIFT: ML forecast accuracy degradation on nominal input distributions
3. PHYSICAL_MODEL_MISMATCH: Systematic divergence between Twin physics and sensor observations
4. PROVIDER_FAILURE: Missing feeds, timeouts, physical bound violations, or packet corruption

INVARIANT:
Does NOT treat every operational anomaly as an ML degradation. Distinguishes failure modes cleanly.
"""

import math
from typing import Dict, List, Optional
from datetime import datetime, timezone

from backend.integrations.schemas import (
    DriftType,
    DriftIndicator,
    ExternalValidationResult,
    ModelVsObservedMetric,
    TwinRealityMetric,
    ProviderHealthRecord,
    ProviderStatus,
)


class OperationalDriftDetector:
    """Detects and categorizes operational drift across environmental, predictive, physical, and transport layers."""

    def __init__(self):
        self._drift_history: List[DriftIndicator] = []

    def assess_data_drift(
        self,
        station_id: str,
        metric_name: str,
        recent_values: List[float],
        historical_mean: float,
        historical_std: float,
        significance_threshold_z: float = 2.5
    ) -> DriftIndicator:
        """
        Detects statistical distribution shift in raw environmental or load inputs.
        Category: DATA_DRIFT
        """
        if not recent_values or historical_std <= 1e-4:
            return DriftIndicator(
                metric_name=metric_name,
                drift_type=DriftType.NOMINAL,
                detected=False,
                severity="LOW",
                z_score=0.0,
                description=f"Insufficient telemetry to assess data drift for {metric_name}",
                recommendation="Continue background telemetry accumulation"
            )

        recent_mean = sum(recent_values) / len(recent_values)
        z = (recent_mean - historical_mean) / historical_std
        abs_z = abs(z)

        detected = abs_z >= significance_threshold_z
        severity = "CRITICAL" if abs_z > 4.0 else ("HIGH" if abs_z > 3.0 else ("MEDIUM" if detected else "LOW"))

        indicator = DriftIndicator(
            metric_name=f"{station_id}_{metric_name}",
            drift_type=DriftType.DATA_DRIFT if detected else DriftType.NOMINAL,
            detected=detected,
            severity=severity,
            z_score=round(z, 2),
            description=(
                f"Observed mean {recent_mean:.2f} differs by {z:+.2f}σ from climatological baseline "
                f"({historical_mean:.2f} ± {historical_std:.2f})"
                if detected else f"Input distribution stable at {z:+.2f}σ"
            ),
            recommendation=(
                "Alert operators of severe climatic shift; engage conservative microgrid reserve posture"
                if detected else "Input distribution nominal"
            )
        )
        self._drift_history.append(indicator)
        return indicator

    def assess_model_drift(
        self,
        station_id: str,
        target_name: str,
        evaluation_metric: ModelVsObservedMetric,
        historical_baseline_mae: float,
        drift_factor_threshold: float = 1.6
    ) -> DriftIndicator:
        """
        Detects predictive accuracy degradation on valid input distributions.
        Category: MODEL_DRIFT
        """
        if evaluation_metric.n_samples == 0:
            return DriftIndicator(
                metric_name=f"{station_id}_{target_name}_forecast",
                drift_type=DriftType.NOMINAL,
                detected=False,
                severity="LOW",
                z_score=0.0,
                description="Zero samples available for model drift evaluation",
                recommendation="Wait for forecast evaluation window"
            )

        current_mae = evaluation_metric.mae
        ratio = current_mae / max(0.1, historical_baseline_mae)
        detected = ratio >= drift_factor_threshold
        severity = "CRITICAL" if ratio > 2.5 else ("HIGH" if ratio > 2.0 else ("MEDIUM" if detected else "LOW"))

        indicator = DriftIndicator(
            metric_name=f"{station_id}_{target_name}_model",
            drift_type=DriftType.MODEL_DRIFT if detected else DriftType.NOMINAL,
            detected=detected,
            severity=severity,
            z_score=round((ratio - 1.0) * 3.0, 2),
            description=(
                f"Forecast MAE {current_mae:.2f} exceeds baseline {historical_baseline_mae:.2f} "
                f"by ratio {ratio:.2f}x (coverage: {evaluation_metric.interval_80_coverage:.1%})"
                if detected else f"Forecast error within baseline bounds (ratio: {ratio:.2f}x)"
            ),
            recommendation=(
                "Queue model for controlled recalibration candidate analysis under Phase 15 protocol"
                if detected else "Model predictive performance nominal"
            )
        )
        self._drift_history.append(indicator)
        return indicator

    def assess_physical_mismatch(
        self,
        station_id: str,
        twin_metrics: List[TwinRealityMetric]
    ) -> DriftIndicator:
        """
        Detects systematic divergences between Digital Twin equations and reference benchmark observations.
        Category: PHYSICAL_MODEL_MISMATCH
        """
        failing = [m for m in twin_metrics if not m.within_tolerance]
        detected = len(failing) >= 2 or any(m.status == "CALIBRATION_CANDIDATE" for m in twin_metrics)
        severity = "HIGH" if len(failing) >= 3 else ("MEDIUM" if detected else "LOW")

        details_str = "; ".join([f"{m.subsystem} res={m.residual:+.2f}" for m in failing]) if failing else "All within tolerance"

        indicator = DriftIndicator(
            metric_name=f"{station_id}_twin_physics",
            drift_type=DriftType.PHYSICAL_MODEL_MISMATCH if detected else DriftType.NOMINAL,
            detected=detected,
            severity=severity,
            z_score=round(float(len(failing)), 1),
            description=(
                f"Physical simulation mismatch detected in subsystems: {details_str}"
                if detected else "Digital twin physical simulation matches reference benchmark within tolerances"
            ),
            recommendation=(
                "Review candidate calibration proposals; verify sensor physical calibration before adjusting twin parameters"
                if detected else "Physical simulation envelope verified"
            )
        )
        self._drift_history.append(indicator)
        return indicator

    def assess_provider_failure(
        self,
        provider_record: ProviderHealthRecord
    ) -> DriftIndicator:
        """
        Detects transport, network, or external data feed outages.
        Category: PROVIDER_FAILURE
        """
        is_failed = provider_record.status in (ProviderStatus.FAILED, ProviderStatus.QUARANTINED, ProviderStatus.UNAVAILABLE)
        is_degraded = provider_record.status in (ProviderStatus.DEGRADED, ProviderStatus.STALE)
        detected = is_failed or is_degraded
        severity = "CRITICAL" if is_failed else ("MEDIUM" if is_degraded else "LOW")

        indicator = DriftIndicator(
            metric_name=f"provider_{provider_record.provider_name}",
            drift_type=DriftType.PROVIDER_FAILURE if detected else DriftType.NOMINAL,
            detected=detected,
            severity=severity,
            z_score=float(provider_record.consecutive_failures),
            description=(
                f"Provider {provider_record.provider_name} status is {provider_record.status.value} "
                f"with {provider_record.consecutive_failures} failures. Last error: {provider_record.last_error or 'None'}"
                if detected else f"Provider {provider_record.provider_name} operating nominally ({provider_record.status.value})"
            ),
            recommendation=(
                "Engage autonomous offline digital twin mode; inspect network link and satcom gateway"
                if detected else "Provider feed healthy"
            )
        )
        self._drift_history.append(indicator)
        return indicator

    def get_all_indicators(self) -> List[DriftIndicator]:
        """Returns all computed drift indicators."""
        return list(self._drift_history)

    def get_active_drift(self) -> List[DriftIndicator]:
        """Returns only indicators where drift was detected."""
        return [ind for ind in self._drift_history if ind.detected]

    def clear_history(self):
        """Clears in-memory drift history."""
        self._drift_history.clear()


_drift_detector_instance: Optional[OperationalDriftDetector] = None


def get_drift_detector() -> OperationalDriftDetector:
    """Singleton getter for Operational Drift Detector."""
    global _drift_detector_instance
    if _drift_detector_instance is None:
        _drift_detector_instance = OperationalDriftDetector()
    return _drift_detector_instance
