"""
POLARIS-EMS — External Reality Bridge Orchestrator
SIH26061: Polar Energy Management & Resilience System

Workstream C: Reality Bridge Orchestrator
Implements the pipeline:
External Provider -> Provider Adapter -> Schema Validation -> Quality/Freshness Check -> Provenance Assignment -> Frozen Interfaces.

Fallback Invariant:
If an external provider is disabled, times out, rate-limited, stale, or malformed:
1. Rejects / quarantines invalid data.
2. Retains safe existing pipeline (synthetic base environment / frozen physics).
3. Reports degraded integration state.
4. NEVER manufactures 'live' or fake telemetry.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone
from functools import lru_cache

from backend.config.settings import get_settings
from backend.integrations.schemas import (
    ExternalWeatherObservation,
    ExternalForecastSeries,
    ExternalValidationResult,
    ProviderHealthRecord,
    ProviderStatus,
    StalenessStatus,
)
from backend.integrations.base import AbstractBaseProviderAdapter
from backend.integrations.validation import ExternalDataValidator
from backend.integrations.adapters.openmeteo import OpenMeteoPolarAdapter
from backend.integrations.adapters.ncpor_format import NCPORFormatAdapter
from backend.integrations.adapters.file_spooler import OfflineFileSpoolerAdapter

logger = logging.getLogger("polaris.integrations.bridge")


class ExternalRealityBridge:
    """Master orchestrator for external reality feeds and reality data adapters."""

    def __init__(self):
        settings = get_settings()
        self.enabled = settings.providers.enabled
        self.validator = ExternalDataValidator(
            max_freshness_sec=settings.providers.max_freshness_sec
        )

        # Register standard adapters
        self.adapters: Dict[str, AbstractBaseProviderAdapter] = {
            "openmeteo": OpenMeteoPolarAdapter(
                endpoint=settings.providers.openmeteo_endpoint,
                timeout_sec=settings.providers.request_timeout_sec,
                enabled=self.enabled
            ),
            "ncpor": NCPORFormatAdapter(
                gateway_url=settings.providers.ncpor_gateway_url,
                enabled=self.enabled and bool(settings.providers.ncpor_gateway_url)
            ),
            "spooler": OfflineFileSpoolerAdapter(
                enabled=True
            ),
        }

        # Cache of latest validated observations by station
        self._latest_validated: Dict[str, ExternalWeatherObservation] = {}
        self._consecutive_invalid: Dict[str, int] = {}
        self._quarantined_providers: Set[str] = set()

    def register_adapter(self, adapter: AbstractBaseProviderAdapter):
        """Registers a custom provider adapter."""
        self.adapters[adapter.name.lower()] = adapter
        logger.info(f"Registered external reality adapter: {adapter.name}")

    def quarantine_provider(self, provider_name: str):
        """Explicitly quarantines a provider adapter."""
        self._quarantined_providers.add(provider_name)
        logger.warning(f"Provider '{provider_name}' manually or automatically QUARANTINED.")

    def unquarantine_provider(self, provider_name: str):
        """Restores a provider from quarantine."""
        self._quarantined_providers.discard(provider_name)
        self._consecutive_invalid[provider_name] = 0
        logger.info(f"Provider '{provider_name}' restored from quarantine.")

    def get_weather_observation(
        self,
        station_id: str,
        preferred_provider: Optional[str] = None
    ) -> ExternalValidationResult:
        """Attempts to fetch and validate external weather observation for a station.

        If external providers are disabled, fail, or produce invalid data:
        returns a validation result with is_valid=False and explicit fallback rationale.
        """
        station_key = station_id.upper()
        now = datetime.now(timezone.utc)

        # 1. Check if external integrations are enabled
        if not self.enabled and preferred_provider != "spooler":
            return ExternalValidationResult(
                is_valid=False,
                errors=["External reality integrations are disabled in configuration."],
                warnings=["System operating in autonomous calibrated digital twin mode."],
                quality_score=0.0,
                freshness_seconds=0.0,
                staleness_status=StalenessStatus.EXPIRED,
                validated_observation=None,
                provenance="CONFIGURED"
            )

        # 2. Select target adapters (preferred first, then fallback to others)
        adapters_to_try: List[AbstractBaseProviderAdapter] = []
        if preferred_provider and preferred_provider.lower() in self.adapters:
            adapters_to_try.append(self.adapters[preferred_provider.lower()])
        else:
            for adp in self.adapters.values():
                if adp.enabled:
                    adapters_to_try.append(adp)

        if not adapters_to_try:
            return ExternalValidationResult(
                is_valid=False,
                errors=["No active external adapters configured."],
                warnings=["Retaining safe offline baseline pipeline."],
                quality_score=0.0,
                freshness_seconds=0.0,
                staleness_status=StalenessStatus.EXPIRED,
                validated_observation=None,
                provenance="CONFIGURED"
            )

        # 3. Query adapters in order
        all_errors: List[str] = []
        for adp in adapters_to_try:
            if adp.name in self._quarantined_providers:
                all_errors.append(f"Provider '{adp.name}' is QUARANTINED due to repeated integrity/bound violations")
                continue

            try:
                obs = adp.fetch_latest_weather(station_key)
                if obs is None:
                    all_errors.append(f"Provider '{adp.name}' returned no observation for {station_key}")
                    continue

                # 4. Validate through physical sanity & freshness filter
                result = self.validator.validate_weather(obs, reference_time=now)
                if result.is_valid and result.validated_observation:
                    self._latest_validated[station_key] = result.validated_observation
                    self._consecutive_invalid[adp.name] = 0
                    logger.info(f"Validated external weather from {adp.name} for {station_key} (Quality: {result.quality_score})")
                    return result
                else:
                    self._consecutive_invalid[adp.name] = self._consecutive_invalid.get(adp.name, 0) + 1
                    if self._consecutive_invalid[adp.name] >= 3:
                        self._quarantined_providers.add(adp.name)
                        logger.error(f"Provider '{adp.name}' QUARANTINED after 3 consecutive invalid payloads.")
                    all_errors.extend([f"[{adp.name}] {e}" for e in result.errors])

            except Exception as e:
                all_errors.append(f"Unexpected error in provider '{adp.name}': {str(e)}")

        # 5. Safe Fallback Behaviour
        logger.warning(f"External reality bridge fallback triggered for {station_key}: {'; '.join(all_errors)}")
        return ExternalValidationResult(
            is_valid=False,
            errors=all_errors,
            warnings=["Retaining safe existing pipeline; reporting degraded integration state."],
            quality_score=0.0,
            freshness_seconds=0.0,
            staleness_status=StalenessStatus.EXPIRED,
            validated_observation=None,
            provenance="CONFIGURED"
        )

    def get_forecast_series(
        self,
        station_id: str,
        horizon_hours: int = 48,
        preferred_provider: Optional[str] = None
    ) -> Optional[ExternalForecastSeries]:
        """Fetches and validates a multi-horizon forward forecast series."""
        if not self.enabled and preferred_provider != "spooler":
            logger.info("External reality bridge disabled; forecast series fallback active.")
            return None

        station_key = station_id.upper()
        now = datetime.now(timezone.utc)

        target_adapter = None
        if preferred_provider and preferred_provider.lower() in self.adapters:
            target_adapter = self.adapters[preferred_provider.lower()]
        else:
            target_adapter = self.adapters.get("openmeteo")

        if not target_adapter or not target_adapter.enabled:
            return None

        if target_adapter.name in self._quarantined_providers:
            logger.warning(f"Cannot fetch series: provider '{target_adapter.name}' is QUARANTINED")
            return None

        if hasattr(target_adapter, "fetch_forecast_series"):
            try:
                series = target_adapter.fetch_forecast_series(station_key, horizon_hours=horizon_hours)
                if series:
                    is_valid, step_results, errors = self.validator.validate_forecast_series(series, reference_time=now)
                    if is_valid:
                        logger.info(f"Validated multi-horizon forecast series ({len(series.steps)} steps) from {target_adapter.name}")
                        return series
                    else:
                        logger.warning(f"Forecast series validation failed: {'; '.join(errors)}")
            except Exception as e:
                logger.error(f"Error fetching forecast series from {target_adapter.name}: {e}")

        return None

    def get_provider_health(self) -> List[ProviderHealthRecord]:
        """Returns diagnostic health records for all registered external providers."""
        records = []
        for adp in self.adapters.values():
            rec = adp.get_health_record()
            if adp.name in self._quarantined_providers:
                rec.status = ProviderStatus.QUARANTINED
            records.append(rec)
        return records

    def get_bridge_summary(self) -> Dict[str, Any]:
        """Provides an executive status of the reality bridge."""
        providers = self.get_provider_health()
        active_count = sum(1 for p in providers if p.status == ProviderStatus.HEALTHY)
        return {
            "bridge_enabled": self.enabled,
            "registered_providers": len(providers),
            "healthy_providers": active_count,
            "active_adapters": [p.provider_name for p in providers if p.enabled],
            "physical_scada_connected": False,  # Strictly False under current polar deployment constraint
            "provenance_policy": "Strict 6-tier taxonomy enforced (REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED)"
        }


@lru_cache(maxsize=1)
def get_reality_bridge() -> ExternalRealityBridge:
    """Singleton instance of the External Reality Bridge."""
    return ExternalRealityBridge()
