# -*- coding: utf-8 -*-
"""
Polaris-EMS — Edge Device Adapter Base

This module defines the abstract base class that all device adapters must implement.
It provides a clean separation between the EdgeEngine core (frozen) and the
various field‑/HIL‑specific back‑ends.

The adapter hierarchy respects the six‑tier provenance taxonomy – adapters
add metadata about *environment* and *source* but never introduce new provenance
tiers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from backend.edge.schema import (
    DeviceProfile,
    DeviceHealthState,
    ConnectivityState,
    DeviceType,
)


class DeviceAdapter(ABC):
    """Abstract base for all device adapters.

    Each concrete adapter must expose a stable interface that the EdgeEngine can
    call without knowing the underlying source (simulator, emulator, HIL, lab).
    """

    @property
    @abstractmethod
    def environment(self) -> str:
        """Human‑readable identifier of the adapter's environment.

        Expected values: ``SIMULATOR``, ``EMULATOR``, ``HIL``, ``LAB``.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def source(self) -> str:
        """Name or identifier of the concrete source (e.g. ``"sim-v1"``)."""
        raise NotImplementedError

    @abstractmethod
    def discover_devices(self) -> List[DeviceProfile]:
        """Return a list of :class:`DeviceProfile` objects for this adapter.

        The returned profiles must include ``environment`` and ``source`` metadata
        via the ``configured_metadata`` field of ``DeviceProfile``. Provenance is
        ``CONFIGURED`` because the adapter provides the ground‑truth configuration.
        """
        raise NotImplementedError

    @abstractmethod
    def read_telemetry(self, device_id: str) -> List[Dict[str, Any]]:
        """Retrieve pending telemetry records for *device_id*.

        Each record is a dict compatible with :class:`TelemetryReading` schema.
        The adapter is responsible for attaching ``environment`` and ``source``
        metadata to each reading – these are later stored in the ``source_metadata``
        field of the reading model.
        """
        raise NotImplementedError

    @abstractmethod
    def write_actuation(self, device_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Accept an actuation command and return a result dict.

        The result must contain at least ``status`` (one of ``SIMULATED``, ``HIL``,
        ``LAB``, ``UNAVAILABLE``) and optional diagnostic fields. The EdgeEngine
        will forward this dict to the :class:`ActuationBoundary` for audit.
        """
        raise NotImplementedError

    def health_check(self) -> Dict[str, Any]:
        """Optional health probe – defaults to ``{"status": "OK"}``.

        Concrete adapters may override to expose richer health information.
        """
        return {"status": "OK", "environment": self.environment, "source": self.source}

# End of file
