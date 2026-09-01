import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server environments
import matplotlib.pyplot as plt

# Scikit-learn models
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
)

from ml.evaluate import calculate_metrics
from ml.model_utils import resolve_project_path, load_datasets, FEATURE_COLUMNS, TARGET_COLUMN

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ml_train")


def generate_evaluation_plots(
    y_test: np.ndarray,
    y_pred_test: np.ndarray,
    models_comparison_df: pd.DataFrame,
    feature_importance_df: pd.DataFrame = None,
    output_dir: str = "reports/figures",
):
    """
    Generates and saves the 4 model evaluation plots.
    """
    fig_dir = resolve_project_path(output_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. Actual vs Predicted AQI
    plt.figure(figsize=(8, 6))
    plt.scatter(y_test, y_pred_test, alpha=0.5, color="#2b5c8f", edgecolors="none")
    min_val = min(float(np.min(y_test)), float(np.min(y_pred_test)))
    max_val = max(float(np.max(y_test)), float(np.max(y_pred_test)))
    plt.plot([min_val, max_val], [min_val, max_val], "r--", lw=2, label="Ideal 1:1 Line")
    plt.title("Actual vs Predicted AQI (Test Set)", fontsize=14, pad=10)
    plt.xlabel("Actual AQI", fontsize=12)
    plt.ylabel("Predicted AQI", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "actual_vs_predicted.png", dpi=300)
    plt.close()

    # 2. Residuals Plot
    residuals = y_test - y_pred_test
    plt.figure(figsize=(8, 6))
    plt.scatter(y_pred_test, residuals, alpha=0.5, color="#d95f02", edgecolors="none")
    plt.axhline(0, color="black", linestyle="--", lw=1.5)
    plt.title("Residuals vs Predicted AQI", fontsize=14, pad=10)
    plt.xlabel("Predicted AQI", fontsize=12)
    plt.ylabel("Residuals (Actual - Predicted)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(fig_dir / "residuals.png", dpi=300)
    plt.close()

    # 3. Model RMSE Comparison
    plt.figure(figsize=(10, 5))
    sorted_df = models_comparison_df.sort_values(by="RMSE", ascending=True)
    bars = plt.barh(sorted_df["Model"], sorted_df["RMSE"], color="#31a354")
    plt.title("Model Validation RMSE Comparison (Lower is Better)", fontsize=14, pad=10)
    plt.xlabel("Validation RMSE", fontsize=12)
    plt.grid(axis="x", linestyle="--", alpha=0.6)
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height() / 2, f"{width:.2f}", va="center", fontsize=10)
    plt.tight_layout()
    plt.savefig(fig_dir / "model_comparison.png", dpi=300)
    plt.close()

    # 4. Feature Importance Plot (if available)
    if feature_importance_df is not None and not feature_importance_df.empty:
        plt.figure(figsize=(10, 6))
        top_features = feature_importance_df.head(12).sort_values(by="importance", ascending=True)
        plt.barh(top_features["feature"], top_features["importance"], color="#756bb1")
        plt.title("Top Feature Importances", fontsize=14, pad=10)
        plt.xlabel("Importance", fontsize=12)
        plt.grid(axis="x", linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(fig_dir / "feature_importance.png", dpi=300)
        plt.close()

    logger.info(f"Evaluation figures saved under: {fig_dir}")


def train_and_evaluate_models(
    train_path: str = "data/processed/train.csv",
    val_path: str = "data/processed/val.csv",
    test_path: str = "data/processed/test.csv",
    preprocessor_path: str = "models/preprocessor.joblib",
    models_dir: str = "models",
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Complete ML Model Development, Training, Model Selection, and Artifact Saving Pipeline.
    """
    logger.info("=" * 60)
    logger.info("STARTING PHASE 5: ML MODEL DEVELOPMENT & TRAINING")
    logger.info("=" * 60)

    # 1. Load Datasets
    train_df, val_df, test_df, feature_cols, target_col = load_datasets(
        train_path=train_path, val_path=val_path, test_path=test_path
    )
    logger.info(f"Target column detected: '{target_col}'")
    logger.info(f"Features detected ({len(feature_cols)}): {feature_cols}")
    logger.info(f"Dataset splits: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # 2. Extract X and y
    X_train_raw = train_df[feature_cols]
    y_train = train_df[target_col].values

    X_val_raw = val_df[feature_cols]
    y_val = val_df[target_col].values

    X_test_raw = test_df[feature_cols]
    y_test = test_df[target_col].values

    # 3. Load & Apply Preprocessor (Fitted strictly on training data from Phase 4)
    prep_p = resolve_project_path(preprocessor_path)
    if not prep_p.exists():
        raise FileNotFoundError(f"Preprocessor artifact not found at: {prep_p}")

    preprocessor = joblib.load(prep_p)
    logger.info(f"Loaded preprocessor artifact from: {prep_p}")

    # Transform features
    X_train = preprocessor.transform(X_train_raw)
    X_val = preprocessor.transform(X_val_raw)
    X_test = preprocessor.transform(X_test_raw)

    # 4. Define Candidate Models
    models: Dict[str, Any] = {
        "Dummy (Baseline)": DummyRegressor(strategy="mean"),
        "Linear Regression": LinearRegression(),
        "Ridge": Ridge(alpha=1.0, random_state=random_state),
        "Random Forest": RandomForestRegressor(
            n_estimators=100, max_depth=12, min_samples_split=4, random_state=random_state, n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=100, learning_rate=0.08, max_depth=5, random_state=random_state
        ),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=100, learning_rate=0.08, max_depth=6, random_state=random_state
        ),
    }

    # 5. Train & Evaluate on Validation Set (Strictly NO test data in selection)
    comparison_records = []
    trained_models = {}
    val_predictions = {}

    logger.info("\n--- Training and Validation Evaluation ---")
    for name, model in models.items():
        logger.info(f"Training model: {name}...")
        model.fit(X_train, y_train)
        trained_models[name] = model

        # Predict on Validation set
        y_val_pred = model.predict(X_val)
        val_predictions[name] = y_val_pred

        metrics = calculate_metrics(y_val, y_val_pred)
        comparison_records.append({
            "Model": name,
            "MAE": metrics["mae"],
            "MSE": metrics["mse"],
            "RMSE": metrics["rmse"],
            "R2": metrics["r2"],
            "MAPE": metrics["mape"],
        })
        logger.info(f"  {name} -> Val RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, R2: {metrics['r2']:.4f}")

    comparison_df = pd.DataFrame(comparison_records)
    logger.info("\n--- Model Comparison Table (Validation) ---")
    logger.info("\n" + comparison_df.to_string(index=False))

    # 6. Select Best Model using Validation RMSE (Primary Metric)
    best_row = comparison_df.loc[comparison_df["RMSE"].idxmin()]
    best_model_name = str(best_row["Model"])
    best_model = trained_models[best_model_name]
    logger.info(f"\n>>> Best Model Selected: {best_model_name} (Validation RMSE: {best_row['RMSE']}) <<<")

    # 7. Final Test Evaluation (Evaluated ONCE on test.csv after model selection)
    logger.info("\n--- Final Test Evaluation ---")
    y_test_pred = best_model.predict(X_test)
    test_metrics = calculate_metrics(y_test, y_test_pred)
    logger.info(
        f"Final Test Metrics for {best_model_name}: "
        f"RMSE={test_metrics['rmse']:.4f}, MAE={test_metrics['mae']:.4f}, R2={test_metrics['r2']:.4f}, MAPE={test_metrics['mape']:.2f}%"
    )

    # 8. Feature Importance Calculation
    feature_importance_df = pd.DataFrame()
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
        feature_importance_df = pd.DataFrame({
            "feature": feature_cols[:len(importances)],
            "importance": importances,
        }).sort_values(by="importance", ascending=False)
    elif hasattr(best_model, "coef_"):
        coefs = np.abs(best_model.coef_)
        feature_importance_df = pd.DataFrame({
            "feature": feature_cols[:len(coefs)],
            "importance": coefs,
        }).sort_values(by="importance", ascending=False)

    # 9. Save Artifacts
    out_models_dir = resolve_project_path(models_dir)
    out_models_dir.mkdir(parents=True, exist_ok=True)

    # Save best model
    best_model_path = out_models_dir / "best_model.joblib"
    joblib.dump(best_model, best_model_path)
    logger.info(f"Saved best model artifact to: {best_model_path}")

    # Save model comparison CSV
    comparison_csv_path = out_models_dir / "model_comparison.csv"
    comparison_df.to_csv(comparison_csv_path, index=False)
    logger.info(f"Saved model comparison table to: {comparison_csv_path}")

    # Save final test metrics JSON
    final_metrics = {
        "model": best_model_name,
        "validation_metrics": {
            "mae": float(best_row["MAE"]),
            "mse": float(best_row["MSE"]),
            "rmse": float(best_row["RMSE"]),
            "r2": float(best_row["R2"]),
            "mape": float(best_row["MAPE"]),
        },
        "test_metrics": test_metrics,
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
    }
    final_metrics_path = out_models_dir / "final_metrics.json"
    with open(final_metrics_path, "w", encoding="utf-8") as f:
        json.dump(final_metrics, f, indent=4)
    logger.info(f"Saved final test metrics to: {final_metrics_path}")

    # Save feature importance CSV
    feat_imp_path = out_models_dir / "feature_importance.csv"
    if not feature_importance_df.empty:
        feature_importance_df.to_csv(feat_imp_path, index=False)
        logger.info(f"Saved feature importances to: {feat_imp_path}")

    # Save model metadata JSON
    metadata = {
        "model_name": best_model_name,
        "model_type": type(best_model).__name__,
        "target_column": target_col,
        "features": feature_cols,
        "num_features": len(feature_cols),
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "random_state": random_state,
        "best_validation_rmse": float(best_row["RMSE"]),
        "final_test_rmse": float(test_metrics["rmse"]),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    metadata_path = out_models_dir / "model_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    logger.info(f"Saved model metadata to: {metadata_path}")

    # 10. Generate Evaluation Figures
    generate_evaluation_plots(
        y_test=y_test,
        y_pred_test=y_test_pred,
        models_comparison_df=comparison_df,
        feature_importance_df=feature_importance_df,
    )

    logger.info("\n" + "=" * 60)
    logger.info("PHASE 5 ML TRAINING COMPLETED SUCCESSFULLY!")
    logger.info("=" * 60)

    return {
        "best_model_name": best_model_name,
        "best_model": best_model,
        "comparison_df": comparison_df,
        "final_metrics": final_metrics,
        "metadata": metadata,
        "feature_importance_df": feature_importance_df,
    }


if __name__ == "__main__":
    train_and_evaluate_models()
