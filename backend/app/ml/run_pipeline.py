"""
Main CLI & Execution Script for Phase 4 Preprocessing Pipeline
"""
import sys
import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.ml.data_loader import DataLoader
from app.ml.dataset import AirQualityDatasetPipeline
from app.ml.generate_demo_data import generate_demo_dataset


def run_pipeline(
    dataset_path: str = None,
    output_dir: str = "data/processed",
    preprocessor_path: str = "models/preprocessor.joblib",
    n_days_demo: int = 180,
):
    print("=" * 60)
    print("AI AIR QUALITY PREDICTION - PHASE 4 PREPROCESSING PIPELINE")
    print("=" * 60)

    # 1. Dataset Resolution
    if not dataset_path or not Path(dataset_path).exists():
        demo_file = Path("data/sample/demo_air_quality_weather.csv")
        if not demo_file.exists():
            print(f"\n[1/5] Generating reference sample dataset ({n_days_demo} days)...")
            demo_file = generate_demo_dataset(str(demo_file), n_days=n_days_demo)
        dataset_path = str(demo_file)
        print(f"\n[1/5] Using reference demo dataset: {dataset_path}")
    else:
        print(f"\n[1/5] Using user-provided dataset: {dataset_path}")

    # 2. Pipeline Initialization
    print("\n[2/5] Initializing Dataset Pipeline (70% Train / 15% Val / 15% Test)...")
    pipeline = AirQualityDatasetPipeline(
        train_ratio=0.70, val_ratio=0.15, test_ratio=0.15
    )

    # 3. Processing
    print("\n[3/5] Cleaning data, resolving outliers, engineering features & splitting...")
    result = pipeline.process(dataset_path, is_file=True)

    stats = result["cleaning_stats"]
    print("\n---------------- Cleaning Statistics ----------------")
    print(f"Total Rows Loaded:         {stats['rows_loaded']}")
    print(f"Duplicates Removed:        {stats['duplicates_removed']}")
    print(f"Missing Values (Before):   {stats['missing_values_before']}")
    print(f"Missing Values (After):    {stats['missing_values_after']}")
    print(f"Total Clean Rows Retained: {stats['rows_retained']}")
    print("-----------------------------------------------------")

    print("\n----------------- Dataset Splits --------------------")
    print(f"Training Set Rows:         {len(result['train_df'])} (70%)")
    print(f"Validation Set Rows:       {len(result['val_df'])} (15%)")
    print(f"Testing Set Rows:          {len(result['test_df'])} (15%)")
    print(f"Total Features ({len(result['features'])}): {result['features']}")
    print(f"Target Variable:           {result['target']}")
    print("-----------------------------------------------------")

    # 4. Save artifacts
    print("\n[4/5] Saving processed artifacts & scikit-learn preprocessor pipeline...")
    saved = pipeline.save_artifacts(
        result, output_dir=output_dir, preprocessor_path=preprocessor_path
    )
    for k, v in saved.items():
        print(f"  - {k}: {v}")

    # 5. Verification Checks
    print("\n[5/5] Performing rigorous data leakage & type verifications...")
    train_max_date = pd.to_datetime(result["train_df"]["timestamp"]).max()
    val_min_date = pd.to_datetime(result["val_df"]["timestamp"]).min()
    val_max_date = pd.to_datetime(result["val_df"]["timestamp"]).max()
    test_min_date = pd.to_datetime(result["test_df"]["timestamp"]).min()

    assert (
        train_max_date < val_min_date
    ), "Data Leakage Error: Train set overlaps with Validation set!"
    assert (
        val_max_date < test_min_date
    ), "Data Leakage Error: Validation set overlaps with Test set!"
    assert not np.isnan(result["X_train"]).any(), "NaN values found in X_train!"
    assert not np.isnan(result["X_val"]).any(), "NaN values found in X_val!"
    assert not np.isnan(result["X_test"]).any(), "NaN values found in X_test!"

    print("  [PASSED] Chronological boundaries verified (Train < Val < Test).")
    print("  [PASSED] Zero data leakage across temporal splits.")
    print("  [PASSED] Zero NaNs in scaled feature matrices.")
    print("  [PASSED] Preprocessing pipeline successfully saved.")
    print("\n=======================================================")
    print("PHASE 4 PREPROCESSING PIPELINE COMPLETED SUCCESSFULLY!")
    print("=======================================================\n")
    return result


if __name__ == "__main__":
    import pandas as pd
    parser = argparse.ArgumentParser(description="Run Phase 4 Air Quality Preprocessing Pipeline")
    parser.add_argument("--data", type=str, default=None, help="Path to raw CSV dataset")
    parser.add_argument("--out", type=str, default="data/processed", help="Output directory")
    args = parser.parse_args()
    run_pipeline(dataset_path=args.data, output_dir=args.out)
