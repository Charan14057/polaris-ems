"""
POLARIS-EMS — External Reality Bridge & Integration Architecture
SIH26061: Polar Energy Management & Resilience System

Workstream C: Provider-Agnostic External Data Integration
Defines normalized schemas, validation, freshness guards, and adapters.
"""

from backend.integrations.schemas import (
    ExternalWeatherObservation,
    ExternalTelemetryPayload,
    ExternalValidationResult,
    ProviderStatus,
    ProviderHealthRecord,
)
from backend.integrations.base import AbstractBaseProviderAdapter
from backend.integrations.bridge import ExternalRealityBridge, get_reality_bridge

__all__ = [
    "ExternalWeatherObservation",
    "ExternalTelemetryPayload",
    "ExternalValidationResult",
    "ProviderStatus",
    "ProviderHealthRecord",
    "AbstractBaseProviderAdapter",
    "ExternalRealityBridge",
    "get_reality_bridge",
]
