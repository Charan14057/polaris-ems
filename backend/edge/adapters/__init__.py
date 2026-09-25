"""
backend/edge/adapters/__init__.py
"""
"""Edge Adapter package

Exports concrete adapter classes and the registry for use by the EdgeEngine.
"""

from .base_adapter import DeviceAdapter
from .simulator_adapter import SimulatorAdapter
from .emulator_adapter import EmulatorAdapter
from .hil_adapter import HILAdapter
from .lab_adapter import LabAdapter
from .adapter_registry import AdapterRegistry, get_global_adapter_registry
from .bridge import EdgeToTwinAdapter, EdgeDecisionBridge

__all__ = [
    "DeviceAdapter",
    "SimulatorAdapter",
    "EmulatorAdapter",
    "HILAdapter",
    "LabAdapter",
    "AdapterRegistry",
    "get_global_adapter_registry",
    "EdgeToTwinAdapter",
    "EdgeDecisionBridge",
]
