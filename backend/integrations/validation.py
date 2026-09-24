"""
POLARIS-EMS — External Reality Bridge Validation & Quality Filter
SIH26061: Polar Energy Management & Resilience System

Workstream C: Physical Boundary & Sanity Checks for Polar Microgrids
Enforces realistic Antarctic/Arctic environmental constraints:
- Temperature: -90.0°C to +30.0°C
- Wind Speed: 0.0 m/s to 85.0 m/s
- Solar Irradiance: 0.0 W/m² to 1400.0 W/m²
- Surface Pressure: 500.0 hPa to 1100.0 hPa
- Humidity: 0.0% to 100.0%
- Temporal Causality: timestamp <= evaluation_time (zero future leakage)
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, Dict, Any

from backend.integrations.schemas import (
    ExternalWeatherObservation,
    ExternalForecastSeries,
    ExternalFeedCompleteness,
    ExternalValidationResult,
    ProviderStatus,
    StalenessStatus,
)

# Authoritative physical domain boundaries for polar environments
POLAR_BOUNDS = {
    "temperature_c": (-90.0, 30.0),       # Record low is -89.2°C at Vostok; Svalbard summer up to +20°C
    "wind_speed_ms": (0.0, 85.0),          # Katabatic storm gusts up to 80+ m/s
    "solar_irradiance_wm2": (0.0, 1400.0), # Solar constant is ~1361 W/m²
    "surface_pressure_hpa": (500.0, 1100.0),
    "relative_humidity_pct": (0.0, 100.0),
}


class ExternalDataValidator:
    """Validates external observations against physical sanity rules and temporal causality."""

    def __init__(
        self,
        max_freshness_sec: int = 3600,
        max_future_tolerance_sec: float = 60.0
    ):
        self.max_freshness_sec = max_freshness_sec
        self.max_future_tolerance_sec = max_future_tolerance_sec

    def validate_weather(
        self,
        obs: ExternalWeatherObservation,
        reference_time: Optional[datetime] = None
    ) -> ExternalValidationResult:
        """Validates an incoming external weather observation."""
        errors: List[str] = []
        warnings: List[str] = []
        now = reference_time or datetime.now(timezone.utc)

        # 1. Temporal Causality & Freshness Guard
        obs_time = obs.timestamp
        if obs_time.tzinfo is None:
            obs_time = obs_time.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        age_seconds = (now - obs_time).total_seconds()

        # Check for future timestamp (leakage violation)
        if age_seconds < -self.max_future_tolerance_sec:
            errors.append(
                f"Future timestamp violation: observation time {obs_time.isoformat()} is "
                f"{-age_seconds:.1f}s ahead of reference time {now.isoformat()} (leakage guard triggered)."
            )
            freshness_status = StalenessStatus.EXPIRED
        elif age_seconds < 0:
            # Within minor clock skew tolerance (0 to 60s)
            freshness_status = StalenessStatus.FRESH
            age_seconds = 0.0
        elif age_seconds <= 900:  # < 15 min
            freshness_status = StalenessStatus.FRESH
        elif age_seconds <= self.max_freshness_sec:  # < 1 hour
            freshness_status = StalenessStatus.ACCEPTABLE
        elif age_seconds <= self.max_freshness_sec * 6:  # < 6 hours
            freshness_status = StalenessStatus.STALE
            warnings.append(f"Observation is stale: age {age_seconds/60:.1f} min > {self.max_freshness_sec/60:.1f} min threshold.")
        else:
            freshness_status = StalenessStatus.EXPIRED
            errors.append(f"Observation expired: age {age_seconds/3600:.1f} hours exceeds 6h operational limit.")

        # 2. Non-Finite Number Checks (NaN / Inf)
        metrics = {
            "ambient_temperature_c": obs.ambient_temperature_c,
            "wind_speed_ms": obs.wind_speed_ms,
            "solar_irradiance_wm2": obs.solar_irradiance_wm2,
        }
        for name, val in metrics.items():
            if val is None or math.isnan(val) or math.isinf(val):
                errors.append(f"Non-finite value in '{name}': {val}")

        # 3. Physical Sanity Bound Verification
        if not errors:
            # Temperature
            t_min, t_max = POLAR_BOUNDS["temperature_c"]
            if not (t_min <= obs.ambient_temperature_c <= t_max):
                errors.append(f"Ambient temperature {obs.ambient_temperature_c}°C outside polar bounds [{t_min}, {t_max}]°C")

            # Wind speed
            w_min, w_max = POLAR_BOUNDS["wind_speed_ms"]
            if not (w_min <= obs.wind_speed_ms <= w_max):
                errors.append(f"Wind speed {obs.wind_speed_ms} m/s outside physical bounds [{w_min}, {w_max}] m/s")

            # Solar irradiance
            s_min, s_max = POLAR_BOUNDS["solar_irradiance_wm2"]
            if not (s_min <= obs.solar_irradiance_wm2 <= s_max):
                errors.append(f"Solar irradiance {obs.solar_irradiance_wm2} W/m² outside physical bounds [{s_min}, {s_max}] W/m²")

            # Night check for high solar irradiance
            # In polar winter / night, irradiance should be 0
            if obs.solar_irradiance_wm2 < 0.0:
                errors.append(f"Negative solar irradiance: {obs.solar_irradiance_wm2} W/m²")

            # Optional: surface pressure
            if obs.surface_pressure_hpa is not None:
                p_min, p_max = POLAR_BOUNDS["surface_pressure_hpa"]
                if not (p_min <= obs.surface_pressure_hpa <= p_max):
                    warnings.append(f"Pressure {obs.surface_pressure_hpa} hPa outside nominal bounds [{p_min}, {p_max}] hPa")

            # Optional: relative humidity
            if obs.relative_humidity_pct is not None:
                h_min, h_max = POLAR_BOUNDS["relative_humidity_pct"]
                if not (h_min <= obs.relative_humidity_pct <= h_max):
                    warnings.append(f"Humidity {obs.relative_humidity_pct}% outside [0, 100]%")

        # 4. Compute Quality Score
        is_valid = len(errors) == 0
        if not is_valid:
            quality_score = 0.0
        else:
            base_score = 1.0
            if freshness_status == StalenessStatus.ACCEPTABLE:
                base_score -= 0.15
            elif freshness_status == StalenessStatus.STALE:
                base_score -= 0.40
            if len(warnings) > 0:
                base_score -= min(0.20, len(warnings) * 0.05)
            quality_score = max(0.1, round(base_score, 2))

        return ExternalValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            quality_score=quality_score,
            freshness_seconds=max(0.0, age_seconds),
            staleness_status=freshness_status,
            validated_observation=obs if is_valid else None,
            provenance=obs.provenance
        )

    def validate_forecast_series(
        self,
        series: ExternalForecastSeries,
        reference_time: Optional[datetime] = None
    ) -> Tuple[bool, List[ExternalValidationResult], List[str]]:
        """Validates a multi-horizon forecast series against polar bounds and temporal order."""
        now = reference_time or datetime.now(timezone.utc)
        step_results: List[ExternalValidationResult] = []
        series_errors: List[str] = []

        if not series.steps:
            return False, [], ["Empty forecast series (0 steps provided)"]

        # Check origin timestamp
        origin = series.forecast_origin
        if origin.tzinfo is None:
            origin = origin.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # Origin should not be in the distant future
        age_sec = (now - origin).total_seconds()
        if age_sec < -self.max_future_tolerance_sec:
            series_errors.append(f"Forecast origin {origin.isoformat()} is in the future relative to {now.isoformat()}")

        # Check steps
        last_ts = None
        for idx, step in enumerate(series.steps):
            step_ts = step.timestamp
            if step_ts.tzinfo is None:
                step_ts = step_ts.replace(tzinfo=timezone.utc)
            if last_ts is not None and step_ts <= last_ts:
                series_errors.append(f"Step {idx} timestamp {step_ts.isoformat()} is not strictly monotonic after {last_ts.isoformat()}")
            last_ts = step_ts

            # Validate physical metrics using validate_weather but skipping freshness check for forward forecast steps
            res = self.validate_weather(step, reference_time=step_ts)
            step_results.append(res)
            if not res.is_valid:
                series_errors.extend([f"Step {idx} ({step_ts.isoformat()}): {e}" for e in res.errors])

        is_valid = len(series_errors) == 0
        return is_valid, step_results, series_errors

    def validate_feed_completeness(
        self,
        station_id: str,
        observations: List[ExternalWeatherObservation],
        expected_interval_minutes: int = 60
    ) -> ExternalFeedCompleteness:
        """Evaluates timestamp continuity and identifies missing intervals."""
        if not observations:
            now = datetime.now(timezone.utc)
            return ExternalFeedCompleteness(
                station_id=station_id.upper(),
                start_time=now,
                end_time=now,
                expected_intervals=0,
                received_intervals=0,
                missing_intervals=0,
                completeness_ratio=0.0,
                is_complete=False,
                missing_timestamps=[]
            )

        sorted_obs = sorted(observations, key=lambda o: o.timestamp)
        start_ts = sorted_obs[0].timestamp
        end_ts = sorted_obs[-1].timestamp
        if start_ts.tzinfo is None:
            start_ts = start_ts.replace(tzinfo=timezone.utc)
        if end_ts.tzinfo is None:
            end_ts = end_ts.replace(tzinfo=timezone.utc)

        interval_delta = timedelta(minutes=expected_interval_minutes)
        total_span_sec = (end_ts - start_ts).total_seconds()
        expected_intervals = max(1, int(round(total_span_sec / (expected_interval_minutes * 60))) + 1)
        received_intervals = len(sorted_obs)

        # Detect gaps
        obs_times = {o.timestamp.replace(tzinfo=timezone.utc) if o.timestamp.tzinfo is None else o.timestamp for o in sorted_obs}
        missing_timestamps: List[datetime] = []
        curr = start_ts
        while curr <= end_ts:
            if not any(abs((curr - t).total_seconds()) < (expected_interval_minutes * 30) for t in obs_times):
                missing_timestamps.append(curr)
            curr += interval_delta

        missing_count = len(missing_timestamps)
        completeness_ratio = min(1.0, max(0.0, (expected_intervals - missing_count) / expected_intervals))
        is_complete = missing_count == 0

        return ExternalFeedCompleteness(
            station_id=station_id.upper(),
            start_time=start_ts,
            end_time=end_ts,
            expected_intervals=expected_intervals,
            received_intervals=received_intervals,
            missing_intervals=missing_count,
            completeness_ratio=round(completeness_ratio, 4),
            is_complete=is_complete,
            missing_timestamps=missing_timestamps
        )

    def evaluate_provider_state(
        self,
        consecutive_failures: int,
        consecutive_invalid: int,
        last_success_age_sec: Optional[float],
        enabled: bool = True,
        quarantine_threshold: int = 3
    ) -> ProviderStatus:
        """Determines provider operational state matching Phase 15 requirements."""
        if not enabled:
            return ProviderStatus.DISABLED
        if consecutive_invalid >= quarantine_threshold:
            return ProviderStatus.QUARANTINED
        if consecutive_failures >= 5:
            return ProviderStatus.FAILED
        if consecutive_failures > 0:
            return ProviderStatus.DEGRADED
        if last_success_age_sec is not None and last_success_age_sec > self.max_freshness_sec:
            return ProviderStatus.STALE
        return ProviderStatus.AVAILABLE
