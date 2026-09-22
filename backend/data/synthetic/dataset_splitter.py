"""
POLARIS-EMS — Chronological Dataset Splitter & Walk-Forward Protocol
SIH26061: Polar Energy Management & Resilience System

Enforces strictly chronological, non-shuffled, non-leaking dataset splits:
- 70% Train
- 15% Validation / Conformal Calibration
- 15% Test
And provides rolling walk-forward evaluation splits for Phase 3 ML forecasting.
"""

from typing import Dict, List, Tuple, Generator
import pandas as pd
import json
from pathlib import Path


class ChronologicalDatasetSplitter:
    """Manages chronological dataset partitioning and walk-forward rolling windows."""

    @staticmethod
    def split(
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
        """
        Splits a chronologically ordered dataframe into Train, Validation, and Test sets.
        Ensures ratios sum to 1.0 and records exact timestamp boundaries.
        """
        assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-6, "Ratios must sum to 1.0"
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_df = df.iloc[:train_end].copy().reset_index(drop=True)
        val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
        test_df = df.iloc[val_end:].copy().reset_index(drop=True)

        meta = {
            "total_rows": n,
            "train": {
                "rows": len(train_df),
                "ratio": train_ratio,
                "start_timestamp": str(train_df["timestamp"].iloc[0]),
                "end_timestamp": str(train_df["timestamp"].iloc[-1]),
            },
            "validation_calibration": {
                "rows": len(val_df),
                "ratio": val_ratio,
                "start_timestamp": str(val_df["timestamp"].iloc[0]),
                "end_timestamp": str(val_df["timestamp"].iloc[-1]),
            },
            "test": {
                "rows": len(test_df),
                "ratio": test_ratio,
                "start_timestamp": str(test_df["timestamp"].iloc[0]),
                "end_timestamp": str(test_df["timestamp"].iloc[-1]),
            },
        }

        return train_df, val_df, test_df, meta

    @staticmethod
    def walk_forward_folds(
        df: pd.DataFrame,
        initial_train_hours: int = 8760,  # 1 year initial train
        val_hours: int = 720,             # 30 days validation
        step_hours: int = 168,            # 7 days forward slide
    ) -> Generator[Tuple[pd.DataFrame, pd.DataFrame, Dict], None, None]:
        """
        Yields expanding-window or rolling-window walk-forward folds:
        (train_fold, val_fold, fold_meta)
        """
        n = len(df)
        fold_idx = 0
        current_train_end = initial_train_hours

        while current_train_end + val_hours <= n:
            train_fold = df.iloc[:current_train_end].copy().reset_index(drop=True)
            val_fold = df.iloc[current_train_end : current_train_end + val_hours].copy().reset_index(drop=True)

            fold_meta = {
                "fold": fold_idx,
                "train_start": str(train_fold["timestamp"].iloc[0]),
                "train_end": str(train_fold["timestamp"].iloc[-1]),
                "val_start": str(val_fold["timestamp"].iloc[0]),
                "val_end": str(val_fold["timestamp"].iloc[-1]),
            }
            yield train_fold, val_fold, fold_meta

            fold_idx += 1
            current_train_end += step_hours

    @staticmethod
    def save_split_files(
        output_dir: Path,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        split_meta: Dict,
    ) -> None:
        """Saves partition CSVs and split metadata JSON to disk."""
        output_dir.mkdir(parents=True, exist_ok=True)
        train_df.to_csv(output_dir / "train.csv", index=False)
        val_df.to_csv(output_dir / "val_calibration.csv", index=False)
        test_df.to_csv(output_dir / "test.csv", index=False)

        with open(output_dir / "split_metadata.json", "w", encoding="utf-8") as f:
            json.dump(split_meta, f, indent=2)
