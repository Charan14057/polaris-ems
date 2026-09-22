"""
POLARIS-EMS — Machine Learning Data Access Layer
SIH26061: Polar Energy Management & Resilience System

Loads chronological partitions for Bharati, Maitri, and Himadri.
Enforces the data split contract:
- Train: 70% (2024-01-01 00:00Z to 2026-01-31 16:00Z, 18,412 hrs)
- Val/Calibration: 15% (2026-01-31 17:00Z to 2026-07-16 20:00Z, 3,946 hrs)
    - Subdivided into Val-Tuning (1,973 hrs) and Calibration (1,973 hrs)
- Test: 15% (2026-07-16 21:00Z to 2026-12-31 23:00Z, 3,946 hrs) [ISOLATED]
"""

from pathlib import Path
from typing import Dict, Tuple, Optional
import pandas as pd


class MLDataLoader:
    """Manages loading and chronological partitioning of station datasets."""

    def __init__(self, data_root: Optional[Path] = None):
        if data_root is None:
            # Default to datasets/ relative to repository root
            base_dir = Path(__file__).resolve().parent.parent.parent
            data_root = base_dir / "datasets"
        self.data_root = Path(data_root)

    def load_raw_partition(self, station_id: str, partition: str) -> pd.DataFrame:
        """Loads a specific partition CSV (train, val_calibration, test)."""
        sid = station_id.lower()
        filepath = self.data_root / sid / f"{partition}.csv"
        if not filepath.exists():
            raise FileNotFoundError(f"Partition file not found: {filepath}")

        df = pd.read_csv(filepath)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        # Ensure chronological ordering
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    def load_train_data(self, station_id: str) -> pd.DataFrame:
        """Loads the training partition (70%)."""
        return self.load_raw_partition(station_id, "train")

    def load_val_and_calibration_data(
        self, station_id: str, split_ratio: float = 0.5
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Loads the 15% validation/calibration partition and splits it chronologically
        into val_tuning and calibration subsets.
        
        Args:
            station_id: BHARATI | MAITRI | HIMADRI
            split_ratio: Fraction allocated to val_tuning (default 0.5 = 1,973 hrs each)
            
        Returns:
            (val_tuning_df, calibration_df)
        """
        val_calib_df = self.load_raw_partition(station_id, "val_calibration")
        split_idx = int(len(val_calib_df) * split_ratio)
        
        val_tuning = val_calib_df.iloc[:split_idx].copy().reset_index(drop=True)
        calibration = val_calib_df.iloc[split_idx:].copy().reset_index(drop=True)
        
        return val_tuning, calibration

    def load_test_data(self, station_id: str) -> pd.DataFrame:
        """
        Loads the untouched 15% final test set.
        WARNING: Must only be evaluated ONCE after all model selection is complete.
        """
        return self.load_raw_partition(station_id, "test")

    def load_full_contiguous(self, station_id: str) -> pd.DataFrame:
        """
        Loads the complete 3-year contiguous hourly dataset (full_3yr_hourly.csv)
        Useful for building rolling lag windows at the partition boundaries without leakage.
        """
        sid = station_id.lower()
        filepath = self.data_root / sid / "full_3yr_hourly.csv"
        if not filepath.exists():
            raise FileNotFoundError(f"Contiguous 3-year file not found: {filepath}")
        df = pd.read_csv(filepath)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df.sort_values("timestamp").reset_index(drop=True)
