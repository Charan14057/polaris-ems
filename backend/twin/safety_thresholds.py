"""
POLARIS-EMS — Configurable Safety & Threat Threshold Registry
SIH26061: Polar Energy Management & Resilience System

Loads and provides station-specific safety limits and risk thresholds from
configs/safety_thresholds.json. Enforces explicit CONFIGURED / ASSUMED provenance.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json
from dataclasses import dataclass


@dataclass
class ThresholdParameter:
    value: float
    unit: str
    provenance: str
    rationale: str


class SafetyThresholdRegistry:
    """Manages configurable safety limits and resilience thresholds."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            config_path = base_dir / "configs" / "safety_thresholds.json"
        self.config_path = Path(config_path)
        self._data: Dict[str, Dict[str, ThresholdParameter]] = {}
        self.load()

    def load(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Safety thresholds config not found at {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for st, thresholds in raw.items():
            self._data[st.upper()] = {
                param_name: ThresholdParameter(**param_dict)
                for param_name, param_dict in thresholds.items()
            }

    def get_threshold(self, station_id: str, param_name: str) -> ThresholdParameter:
        sid = station_id.upper()
        if sid not in self._data:
            sid = "BHARATI"
        station_thresholds = self._data[sid]
        if param_name not in station_thresholds:
            raise KeyError(f"Threshold '{param_name}' not defined for station '{sid}'")
        return station_thresholds[param_name]

    def get_value(self, station_id: str, param_name: str, default: float = 0.0) -> float:
        try:
            return self.get_threshold(station_id, param_name).value
        except KeyError:
            return default
