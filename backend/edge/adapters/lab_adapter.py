"""
backend/edge/adapters/lab_adapter.py
"""
"""LabAdapter – a concrete DeviceAdapter for laboratory device abstractions.

Mock laboratory interface for unit tests — no real lab hardware required.
Telemetry is marked ``SIMULATED`` provenance, ``environment=LAB`` metadata.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone

from backend.edge.adapters.base_adapter import DeviceAdapter
from backend.edge.schema import DeviceProfile, DeviceType, DeviceChannelConfig


class LabAdapter(DeviceAdapter):
    def __init__(self, source: str = "default") -> None:
        self._source = source

    @property
    def environment(self) -> str:
        return "LAB"

    @property
    def source(self) -> str:
        return self._source

    def discover_devices(self) -> List[DeviceProfile]:
        return [DeviceProfile(
            device_id="lab-gen-001", station_id="LAB_STATION",
            device_type=DeviceType.DIESEL_GENERATOR, name="Lab Generator",
            rated_capacity=3000.0, unit="kW", provenance="SIMULATED",
            telemetry_channels=[DeviceChannelConfig(channel="power", unit="kW", min_val=0.0, max_val=3500.0)],
            source_metadata={"environment": self.environment, "source": self.source},
        )]

    def read_telemetry(self, device_id: str) -> List[Dict[str, Any]]:
        if device_id != "lab-gen-001":
            raise KeyError(f"Device '{device_id}' not found in lab adapter.")
        return [{"station_id": "LAB_STATION", "device_id": device_id, "channel": "power",
                 "timestamp": datetime.now(timezone.utc).isoformat(), "value": 1800.0,
                 "unit": "kW", "quality": "VALID", "provenance": "SIMULATED", "source": "lab"}]

    def write_actuation(self, device_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        if device_id != "lab-gen-001":
            raise KeyError(f"Device '{device_id}' not found in lab adapter.")
        return {"device_id": device_id, "status": "LAB", "command": command,
                "environment": self.environment, "source": self.source}
