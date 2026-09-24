"""
POLARIS-EMS — External Reality Bridge & Integration Architecture
SIH26061: Polar Energy Management & Resilience System

Workstream C: Provider-Agnostic External Data Integration
Defines normalized schemas, validation, freshness guards, and adapters.
"""

from backend.integrations.schemas import (
    ExternalWeatherObservation,
    ExternalForecastSeries,
    ExternalFeedCompleteness,
    ExternalTelemetryPayload,
    ExternalValidationResult,
    ProviderStatus,
    ProviderHealthRecord,
    ModelVsObservedMetric,
    TwinRealityMetric,
    CalibrationCandidate,
    DriftType,
    DriftIndicator,
    OperationalReplayResult,
)
from backend.integrations.base import AbstractBaseProviderAdapter
from backend.integrations.validation import ExternalDataValidator
from backend.integrations.bridge import ExternalRealityBridge, get_reality_bridge
from backend.integrations.evaluator import ModelVsObservedEvaluator, get_model_evaluator
from backend.integrations.twin_reality import TwinRealityCheckEngine, get_twin_reality_engine
from backend.integrations.drift import OperationalDriftDetector, get_drift_detector
from backend.integrations.replay import OperationalReplayOrchestrator, get_replay_orchestrator

__all__ = [
    "ExternalWeatherObservation",
    "ExternalForecastSeries",
    "ExternalFeedCompleteness",
    "ExternalTelemetryPayload",
    "ExternalValidationResult",
    "ProviderStatus",
    "ProviderHealthRecord",
    "ModelVsObservedMetric",
    "TwinRealityMetric",
    "CalibrationCandidate",
    "DriftType",
    "DriftIndicator",
    "OperationalReplayResult",
    "AbstractBaseProviderAdapter",
    "ExternalDataValidator",
    "ExternalRealityBridge",
    "get_reality_bridge",
    "ModelVsObservedEvaluator",
    "get_model_evaluator",
    "TwinRealityCheckEngine",
    "get_twin_reality_engine",
    "OperationalDriftDetector",
    "get_drift_detector",
    "OperationalReplayOrchestrator",
    "get_replay_orchestrator",
]
