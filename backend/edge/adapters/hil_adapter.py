"""
backend/edge/adapters/hil_adapter.py
"""
"""HILAdapter – a concrete DeviceAdapter for Hardware-in-the-Loop devices.

Mock HIL interface suitable for unit tests — no real hardware required.
Telemetry is marked ``SIMULATED`` provenance, ``environment=HIL`` metadata.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone

from backend.edge.adapters.base_adapter import DeviceAdapter
from backend.edge.schema import DeviceProfile, DeviceType, DeviceChannelConfig


class HILAdapter(DeviceAdapter):
    def __init__(self, source: str = "default") -> None:
        self._source = source

    @property
    def environment(self) -> str:
        return "HIL"

    @property
    def source(self) -> str:
        return self._source

    def discover_devices(self) -> List[DeviceProfile]:
        return [DeviceProfile(
            device_id="hil-gen-001", station_id="HIL_STATION",
            device_type=DeviceType.DIESEL_GENERATOR, name="HIL Generator",
            rated_capacity=4500.0, unit="kW", provenance="SIMULATED",
            telemetry_channels=[DeviceChannelConfig(channel="power", unit="kW", min_val=0.0, max_val=5000.0)],
            source_metadata={"environment": self.environment, "source": self.source},
        )]

    def read_telemetry(self, device_id: str) -> List[Dict[str, Any]]:
        if device_id != "hil-gen-001":
            raise KeyError(f"Device '{device_id}' not found in HIL adapter.")
        return [{"station_id": "HIL_STATION", "device_id": device_id, "channel": "power",
                 "timestamp": datetime.now(timezone.utc).isoformat(), "value": 2250.0,
                 "unit": "kW", "quality": "VALID", "provenance": "SIMULATED", "source": "hil"}]

    def write_actuation(self, device_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        if device_id != "hil-gen-001":
            raise KeyError(f"Device '{device_id}' not found in HIL adapter.")
        return {"device_id": device_id, "status": "HIL", "command": command,
                "environment": self.environment, "source": self.source}
