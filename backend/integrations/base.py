"""
POLARIS-EMS — Base Provider Adapter Interface
SIH26061: Polar Energy Management & Resilience System

Workstream C: Provider-Agnostic Adapter Contract
Ensures external sources are isolated behind standard interfaces without leaking vendor APIs.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from backend.integrations.schemas import (
    ExternalWeatherObservation,
    ProviderHealthRecord,
    ProviderStatus,
    StalenessStatus,
)


class AbstractBaseProviderAdapter(ABC):
    """Abstract interface that all external reality adapters must implement."""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self._last_contact: Optional[datetime] = None
        self._last_success: Optional[datetime] = None
        self._consecutive_failures: int = 0
        self._last_error: Optional[str] = None
        self._total_requests: int = 0
        self._successful_requests: int = 0
        self._latency_sum_ms: float = 0.0

    @abstractmethod
    def fetch_latest_weather(self, station_id: str) -> Optional[ExternalWeatherObservation]:
        """Fetches normalized weather observation for the given station.

        Returns None if provider is disabled, times out, or encounters errors.
        Must never throw unhandled exceptions to callers.
        """
        pass

    @abstractmethod
    def test_connectivity(self) -> bool:
        """Tests network / endpoint reachability to the external service."""
        pass

    def record_success(self, latency_ms: float):
        """Records a successful provider fetch."""
        now = datetime.now(timezone.utc)
        self._last_contact = now
        self._last_success = now
        self._consecutive_failures = 0
        self._last_error = None
        self._total_requests += 1
        self._successful_requests += 1
        self._latency_sum_ms += latency_ms

    def record_failure(self, error_message: str):
        """Records a failed provider fetch."""
        self._last_contact = datetime.now(timezone.utc)
        self._consecutive_failures += 1
        self._last_error = error_message
        self._total_requests += 1

    def get_health_record(self) -> ProviderHealthRecord:
        """Generates real-time health diagnostic record."""
        avg_latency = (
            self._latency_sum_ms / self._successful_requests
            if self._successful_requests > 0
            else 0.0
        )

        if not self.enabled:
            status = ProviderStatus.DISABLED
        elif self._consecutive_failures >= 5:
            status = ProviderStatus.UNAVAILABLE
        elif self._consecutive_failures > 0:
            status = ProviderStatus.DEGRADED
        elif self._last_success is None:
            status = ProviderStatus.HEALTHY
        else:
            status = ProviderStatus.HEALTHY

        # Freshness of last successful contact
        freshness_status = StalenessStatus.EXPIRED
        if self._last_success is not None:
            age = (datetime.now(timezone.utc) - self._last_success).total_seconds()
            if age <= 900:
                freshness_status = StalenessStatus.FRESH
            elif age <= 3600:
                freshness_status = StalenessStatus.ACCEPTABLE
            elif age <= 21600:
                freshness_status = StalenessStatus.STALE

        return ProviderHealthRecord(
            provider_name=self.name,
            status=status,
            enabled=self.enabled,
            last_contact=self._last_contact,
            last_success=self._last_success,
            consecutive_failures=self._consecutive_failures,
            last_error=self._last_error,
            total_requests=self._total_requests,
            successful_requests=self._successful_requests,
            average_latency_ms=round(avg_latency, 2),
            freshness_status=freshness_status
        )
