"""
POLARIS-EMS — Phase 16 Fault Injection Framework (Workstream F)
SIH26061: Polar Energy Management & Resilience System

Provides a reusable, deterministic fault-injection layer for Phase 16
field / HIL / reliability validation.

Fault injection occurs at integration boundaries ONLY.
Does NOT modify Phase 4 physics or Phase 6 optimization mathematics.

Uses deterministic seeds and reproducible schedules.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.edge.schema import (
    TelemetryReading,
    DataQualityState,
    ConnectivityState,
    DeviceHealthState,
    validate_provenance,
)
from backend.edge.telemetry import TelemetryNormalizer


class DeviceFault(str, Enum):
    DEVICE_UNAVAILABLE = "DEVICE_UNAVAILABLE"
    DEVICE_DEGRADED = "DEVICE_DEGRADED"
    DEVICE_INTERMITTENT = "DEVICE_INTERMITTENT"
    SENSOR_FAILURE = "SENSOR_FAILURE"
    ACTUATOR_UNAVAILABLE = "ACTUATOR_UNAVAILABLE"


class TelemetryFault(str, Enum):
    MISSING = "MISSING"
    STALE = "STALE"
    DUPLICATE = "DUPLICATE"
    DELAYED = "DELAYED"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    MALFORMED = "MALFORMED"


class ConnectivityFault(str, Enum):
    DISCONNECT = "DISCONNECT"
    INTERMITTENT_LINK = "INTERMITTENT_LINK"
    PROLONGED_OUTAGE = "PROLONGED_OUTAGE"
    RECONNECT_STORM = "RECONNECT_STORM"


class InterfaceFault(str, Enum):
    GENERATOR_UNAVAILABLE = "GENERATOR_UNAVAILABLE"
    BATTERY_INTERFACE_UNAVAILABLE = "BATTERY_INTERFACE_UNAVAILABLE"
    RENEWABLE_TELEMETRY_UNAVAILABLE = "RENEWABLE_TELEMETRY_UNAVAILABLE"
    LOAD_TELEMETRY_UNAVAILABLE = "LOAD_TELEMETRY_UNAVAILABLE"


class FaultScheduleEntry(BaseModel):
    """A single scheduled fault event."""
    fault_type: str
    fault_class: str  # DEVICE | TELEMETRY | CONNECTIVITY | INTERFACE
    target_device_id: Optional[str] = None
    target_channel: Optional[str] = None
    trigger_offset_sec: float = 0.0
    duration_sec: float = 60.0
    parameters: Dict[str, Any] = Field(default_factory=dict)


class FaultInjectionResult(BaseModel):
    """Record of an injected fault and its effect."""
    fault_type: str
    fault_class: str
    target: str
    timestamp: str
    effect: str
    readings_affected: int = 0
    provenance: str = "SIMULATED"


class FaultInjector:
    """Deterministic fault-injection engine for Phase 16 validation.

    All fault injection happens at integration boundaries and uses
    deterministic seeds for reproducibility.
    """

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        self._schedule: List[FaultScheduleEntry] = []
        self._results: List[FaultInjectionResult] = []

    def add_fault(self, entry: FaultScheduleEntry) -> None:
        """Add a fault to the injection schedule."""
        self._schedule.append(entry)

    def clear_schedule(self) -> None:
        """Remove all scheduled faults."""
        self._schedule.clear()

    @property
    def results(self) -> List[FaultInjectionResult]:
        return list(self._results)

    def inject_telemetry_fault(
        self,
        reading: TelemetryReading,
        fault: TelemetryFault,
        current_time: Optional[datetime] = None,
    ) -> TelemetryReading:
        """Apply a telemetry fault to a reading and record the injection."""
        now = current_time or datetime.now(timezone.utc)

        if fault == TelemetryFault.STALE:
            # Push timestamp back 5 minutes
            stale_ts = now - timedelta(seconds=300)
            reading.timestamp = stale_ts.isoformat()
            reading.quality = DataQualityState.STALE

        elif fault == TelemetryFault.MISSING:
            reading.value = None  # type: ignore
            reading.quality = DataQualityState.MISSING

        elif fault == TelemetryFault.DUPLICATE:
            # No mutation needed — caller should re-inject the same reading
            reading.quality = DataQualityState.DUPLICATE

        elif fault == TelemetryFault.DELAYED:
            # Push timestamp back 90 seconds
            delayed_ts = now - timedelta(seconds=90)
            reading.timestamp = delayed_ts.isoformat()

        elif fault == TelemetryFault.OUT_OF_ORDER:
            if reading.sequence_number is not None:
                reading.sequence_number = max(0, reading.sequence_number - 5)
            reading.quality = DataQualityState.OUT_OF_ORDER

        elif fault == TelemetryFault.OUT_OF_RANGE:
            if isinstance(reading.value, (int, float)):
                reading.value = reading.value * 100  # Force out of range
            reading.quality = DataQualityState.OUT_OF_RANGE

        elif fault == TelemetryFault.MALFORMED:
            reading.value = "MALFORMED_DATA_###"
            reading.quality = DataQualityState.SUSPECT

        reading.diagnostics.append(f"[FAULT_INJECTED] {fault.value}")
        self._results.append(FaultInjectionResult(
            fault_type=fault.value,
            fault_class="TELEMETRY",
            target=f"{reading.device_id}::{reading.channel}",
            timestamp=now.isoformat(),
            effect=f"Telemetry fault {fault.value} applied",
            readings_affected=1,
        ))
        return reading

    def inject_device_fault(
        self,
        device_id: str,
        fault: DeviceFault,
        current_time: Optional[datetime] = None,
    ) -> FaultInjectionResult:
        """Record a device-level fault injection."""
        now = current_time or datetime.now(timezone.utc)
        result = FaultInjectionResult(
            fault_type=fault.value,
            fault_class="DEVICE",
            target=device_id,
            timestamp=now.isoformat(),
            effect=f"Device fault {fault.value} injected on {device_id}",
        )
        self._results.append(result)
        return result

    def inject_connectivity_fault(
        self,
        fault: ConnectivityFault,
        station_id: str = "",
        current_time: Optional[datetime] = None,
    ) -> FaultInjectionResult:
        """Record a connectivity fault injection."""
        now = current_time or datetime.now(timezone.utc)
        result = FaultInjectionResult(
            fault_type=fault.value,
            fault_class="CONNECTIVITY",
            target=station_id or "STATION",
            timestamp=now.isoformat(),
            effect=f"Connectivity fault {fault.value} injected",
        )
        self._results.append(result)
        return result

    def inject_interface_fault(
        self,
        fault: InterfaceFault,
        station_id: str = "",
        current_time: Optional[datetime] = None,
    ) -> FaultInjectionResult:
        """Record an interface fault injection."""
        now = current_time or datetime.now(timezone.utc)
        result = FaultInjectionResult(
            fault_type=fault.value,
            fault_class="INTERFACE",
            target=station_id or "STATION",
            timestamp=now.isoformat(),
            effect=f"Interface fault {fault.value} injected",
        )
        self._results.append(result)
        return result

    def run_schedule(
        self,
        base_time: Optional[datetime] = None,
    ) -> List[FaultInjectionResult]:
        """Execute all scheduled faults and return results."""
        t0 = base_time or datetime.now(timezone.utc)
        results: List[FaultInjectionResult] = []
        for entry in self._schedule:
            trigger_time = t0 + timedelta(seconds=entry.trigger_offset_sec)
            if entry.fault_class == "DEVICE":
                r = self.inject_device_fault(
                    entry.target_device_id or "unknown",
                    DeviceFault(entry.fault_type),
                    current_time=trigger_time,
                )
            elif entry.fault_class == "CONNECTIVITY":
                r = self.inject_connectivity_fault(
                    ConnectivityFault(entry.fault_type),
                    current_time=trigger_time,
                )
            elif entry.fault_class == "INTERFACE":
                r = self.inject_interface_fault(
                    InterfaceFault(entry.fault_type),
                    current_time=trigger_time,
                )
            else:
                r = FaultInjectionResult(
                    fault_type=entry.fault_type,
                    fault_class=entry.fault_class,
                    target=entry.target_device_id or "unknown",
                    timestamp=trigger_time.isoformat(),
                    effect=f"Scheduled fault {entry.fault_type}",
                )
                self._results.append(r)
            results.append(r)
        return results
