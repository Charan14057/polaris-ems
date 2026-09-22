"""
POLARIS-EMS — Machine Learning Model Registry
SIH26061: Polar Energy Management & Resilience System

Maintains versioned artifacts, schemas, calibration parameters, and metadata.
Enforces reproducible saving and loading of all production forecasting models.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import joblib
from datetime import datetime, timezone


class ModelRegistry:
    """Manages versioned model artifacts under models/registry/."""

    def __init__(self, registry_root: Optional[Path] = None):
        if registry_root is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            registry_root = base_dir / "models" / "registry"
        self.registry_root = Path(registry_root)
        self.registry_root.mkdir(parents=True, exist_ok=True)

    def save_model(
        self,
        model: Any,
        metadata: Dict[str, Any],
        calibrator: Optional[Any] = None
    ) -> Path:
        """
        Saves a trained model, optional calibrator, and metadata JSON.
        
        Args:
            model: Trained model instance
            metadata: Comprehensive metadata dictionary
            calibrator: Fitted ConformalQuantileCalibrator instance
        """
        model_name = metadata["model_name"]
        model_dir = self.registry_root / model_name
        model_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save trained model artifact
        model_file = model_dir / "model.joblib"
        joblib.dump(model, model_file)

        # 2. Save calibrator if present
        if calibrator is not None:
            calib_file = model_dir / "calibrator.joblib"
            joblib.dump(calibrator, calib_file)
            metadata["has_calibrator"] = True
            metadata["calibration_parameters"] = calibrator.get_calibration_metadata()
        else:
            metadata["has_calibrator"] = False

        # 3. Add timestamp and save metadata JSON
        metadata["saved_at"] = datetime.now(timezone.utc).isoformat()
        meta_file = model_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return model_dir

    def load_model(self, model_name: str) -> tuple[Any, Optional[Any], Dict[str, Any]]:
        """
        Loads model artifact, calibrator (if present), and metadata JSON.
        """
        model_dir = self.registry_root / model_name
        if not model_dir.exists():
            raise FileNotFoundError(f"Model '{model_name}' not found in registry {self.registry_root}")

        model_file = model_dir / "model.joblib"
        model = joblib.load(model_file)

        calib_file = model_dir / "calibrator.joblib"
        calibrator = joblib.load(calib_file) if calib_file.exists() else None

        meta_file = model_dir / "metadata.json"
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        return model, calibrator, metadata

    def list_models(self) -> List[str]:
        """Returns list of registered model names."""
        return [
            d.name for d in self.registry_root.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        ]
