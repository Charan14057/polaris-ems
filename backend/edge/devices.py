"""
POLARIS-EMS — Edge Device Registry & Model
SIH26061: Polar Energy Management & Resilience System

Loads and manages station-aware physical and virtual device profiles from
authoritative configuration (configs/device_profiles.json).

INVARIANTS:
- No hardcoded station-specific capacities in logic.
- Dynamic support for BHARATI, MAITRI, and HIMADRI.
- Strict validation of station/device membership.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import os

from backend.edge.schema import (
    DeviceProfile,
    StationDeviceCatalog,
    DeviceType,
    DeviceHealthState,
    ConnectivityState
)


class DeviceRegistry:
    """Station-aware registry of field and virtual edge devices."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Resolve relative to repo root
            base_dir = Path(__file__).resolve().parent.parent.parent
            config_path = str(base_dir / "configs" / "device_profiles.json")

        self.config_path = config_path
        self._catalogs: Dict[str, StationDeviceCatalog] = {}
        self._load()

    def _load(self) -> None:
        """Parses and validates device_profiles.json."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Device profiles configuration not found at: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        for station_id, station_cfg in raw_data.items():
            sid_upper = station_id.upper()
            devices: List[DeviceProfile] = []
            for dev_raw in station_cfg.get("devices", []):
                profile = DeviceProfile(
                    device_id=dev_raw["device_id"],
                    station_id=sid_upper,
                    device_type=DeviceType(dev_raw["device_type"]),
                    name=dev_raw["name"],
                    rated_capacity=dev_raw.get("rated_capacity"),
                    unit=dev_raw["unit"],
                    enabled=dev_raw.get("enabled", True),
                    expected_reporting_interval_sec=dev_raw.get("expected_reporting_interval_sec", 10.0),
                    freshness_threshold_sec=dev_raw.get("freshness_threshold_sec", 60.0),
                    health_state=DeviceHealthState(dev_raw.get("health_state", "HEALTHY")),
                    connectivity_state=ConnectivityState(dev_raw.get("connectivity_state", "CONNECTED")),
                    provenance=dev_raw.get("provenance", "CONFIGURED"),
                    last_seen=dev_raw.get("last_seen"),
                    configured_metadata=dev_raw.get("configured_metadata", {}),
                    telemetry_channels=dev_raw.get("telemetry_channels", []),
                    source_metadata=dev_raw.get("source_metadata", {})
                )
                devices.append(profile)

            catalog = StationDeviceCatalog(
                station_id=sid_upper,
                station_name=station_cfg.get("station_name", sid_upper),
                edge_node_id=station_cfg.get("edge_node_id", f"{sid_upper.lower()}_edge_node"),
                default_reporting_interval_sec=station_cfg.get("default_reporting_interval_sec", 10.0),
                default_freshness_threshold_sec=station_cfg.get("default_freshness_threshold_sec", 60.0),
                devices=devices
            )
            self._catalogs[sid_upper] = catalog

    def get_catalog(self, station_id: str) -> StationDeviceCatalog:
        """Retrieves the full device catalog for a station."""
        sid_upper = station_id.upper()
        if sid_upper not in self._catalogs:
            raise KeyError(f"Station '{station_id}' not found in device registry. Available: {list(self._catalogs.keys())}")
        return self._catalogs[sid_upper]

    def list_devices(self, station_id: str, device_type: Optional[DeviceType] = None) -> List[DeviceProfile]:
        """Lists devices for a station, optionally filtered by device class."""
        catalog = self.get_catalog(station_id)
        if device_type is None:
            return list(catalog.devices)
        return [d for d in catalog.devices if d.device_type == device_type]

    def get_device(self, station_id: str, device_id: str) -> DeviceProfile:
        """Retrieves a single device by ID for a station."""
        catalog = self.get_catalog(station_id)
        for dev in catalog.devices:
            if dev.device_id == device_id:
                return dev
        raise KeyError(f"Device '{device_id}' not found at station '{station_id}'.")

    def has_device(self, station_id: str, device_id: str) -> bool:
        """Checks if a device exists for a station."""
        try:
            self.get_device(station_id, device_id)
            return True
        except KeyError:
            return False

    def list_stations(self) -> List[str]:
        """Returns all configured station IDs."""
        return list(self._catalogs.keys())


# Singleton instance
_device_registry: Optional[DeviceRegistry] = None


def get_device_registry(config_path: Optional[str] = None) -> DeviceRegistry:
    """Factory/singleton provider for DeviceRegistry."""
    global _device_registry
    if _device_registry is None or config_path is not None:
        _device_registry = DeviceRegistry(config_path)
    return _device_registry
