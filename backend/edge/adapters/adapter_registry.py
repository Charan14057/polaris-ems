"""
backend/edge/adapters/adapter_registry.py
"""
"""Adapter registry for EdgeEngine.

The registry holds concrete ``DeviceAdapter`` implementations and provides a
deterministic lookup based on an ``environment`` identifier (e.g. ``SIMULATOR``,
``EMULATOR``, ``HIL``, ``LAB``).

It enforces:
* no duplicate registration of the same environment name,
* explicit error for unknown adapters,
* ability to list all registered adapter types.

The global singleton ``_global_adapter_registry`` is exposed via
``get_global_adapter_registry`` for import by the EdgeEngine and tests.
"""

from typing import Dict, Type

from .base_adapter import DeviceAdapter


class AdapterRegistry:
    """Registry mapping environment names to concrete ``DeviceAdapter`` classes."""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[DeviceAdapter]] = {}

    # ---------------------------------------------------------------------
    # Registration API
    # ---------------------------------------------------------------------
    def register(self, environment: str, adapter_cls: Type[DeviceAdapter]) -> None:
        env_key = environment.upper()
        if env_key in self._registry:
            raise ValueError(f"Adapter for environment '{environment}' already registered.")
        if not issubclass(adapter_cls, DeviceAdapter):
            raise TypeError("Adapter class must inherit from DeviceAdapter.")
        self._registry[env_key] = adapter_cls

    # ---------------------------------------------------------------------
    # Retrieval API
    # ---------------------------------------------------------------------
    def get(self, environment: str, *args, **kwargs) -> DeviceAdapter:
        """Instantiate and return the adapter for ``environment``.

        ``*args`` and ``**kwargs`` are forwarded to the adapter constructor.
        """
        env_key = environment.upper()
        if env_key not in self._registry:
            raise KeyError(f"Adapter for environment '{environment}' is not registered.")
        return self._registry[env_key](*args, **kwargs)

    def list_adapters(self) -> Dict[str, str]:
        """Return a mapping of environment → fully‑qualified class name."""
        return {env: cls.__module__ + "." + cls.__qualname__ for env, cls in self._registry.items()}


# Global singleton registry -------------------------------------------------
_global_adapter_registry = AdapterRegistry()


def get_global_adapter_registry() -> AdapterRegistry:
    """Accessor for the module‑level singleton registry.

    The function is used by the EdgeEngine and the test suite to avoid import
    cycles.
    """
    return _global_adapter_registry

# Register the built-in adapters that exist at import time.
try:
    from .simulator_adapter import SimulatorAdapter
    _global_adapter_registry.register("SIMULATOR", SimulatorAdapter)
except Exception:
    pass

try:
    from .emulator_adapter import EmulatorAdapter
    _global_adapter_registry.register("EMULATOR", EmulatorAdapter)
except Exception:
    pass

try:
    from .hil_adapter import HILAdapter
    _global_adapter_registry.register("HIL", HILAdapter)
except Exception:
    pass

try:
    from .lab_adapter import LabAdapter
    _global_adapter_registry.register("LAB", LabAdapter)
except Exception:
    pass

"""End of adapter_registry.py"""

