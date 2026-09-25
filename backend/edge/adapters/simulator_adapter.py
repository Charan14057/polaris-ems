"""
backend/edge/adapters/simulator_adapter.py
"""
"""SimulatorAdapter – a concrete DeviceAdapter for pure software simulation.

The simulator returns deterministic, pre-configured device profiles and generates
synthetic telemetry readings. It never produces ``REAL`` provenance – all
telemetry is marked ``SIMULATED``.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone

from backend.edge.adapters.base_adapter import DeviceAdapter
from backend.edge.schema import DeviceProfile, DeviceType, DeviceHealthState, ConnectivityState, DeviceChannelConfig


class SimulatorAdapter(DeviceAdapter):
    """Concrete adapter for a software-only simulator.

    * ``environment`` – ``"SIMULATOR"``
    * ``source`` – identifier for the simulator instance (default ``"default"``)
    """

    def __init__(self, source: str = "default") -> None:
        self._source = source

    @property
    def environment(self) -> str:
        return "SIMULATOR"

    @property
    def source(self) -> str:
        return self._source

    def discover_devices(self) -> List[DeviceProfile]:
        profile = DeviceProfile(
            device_id="sim-gen-001",
            station_id="SIM_STATION",
            device_type=DeviceType.DIESEL_GENERATOR,
            name="Simulated Generator",
            rated_capacity=5000.0,
            unit="kW",
            enabled=True,
            expected_reporting_interval_sec=10.0,
            freshness_threshold_sec=60.0,
            health_state=DeviceHealthState.HEALTHY,
            connectivity_state=ConnectivityState.CONNECTED,
            provenance="SIMULATED",
            last_seen=None,
            configured_metadata={},
            telemetry_channels=[
                DeviceChannelConfig(channel="power", unit="kW", min_val=0.0, max_val=5500.0),
                DeviceChannelConfig(channel="status", unit="enum", min_val=0.0, max_val=1.0),
            ],
            source_metadata={"environment": self.environment, "source": self.source},
        )
        return [profile]

    def read_telemetry(self, device_id: str) -> List[Dict[str, Any]]:
        if device_id != "sim-gen-001":
            raise KeyError(f"Device '{device_id}' not found in simulator.")
        return [{
            "station_id": "SIM_STATION",
            "device_id": device_id,
            "channel": "power",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": 2500.0,
            "unit": "kW",
            "quality": "VALID",
            "provenance": "SIMULATED",
            "source": "simulator",
        }]

    def write_actuation(self, device_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        if device_id != "sim-gen-001":
            raise KeyError(f"Device '{device_id}' not found in simulator.")
        return {
            "device_id": device_id,
            "status": "SIMULATED",
            "command": command,
            "environment": self.environment,
            "source": self.source,
        }

# End of file
