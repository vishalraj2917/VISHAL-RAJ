import numpy as np
from typing import Dict, Any, Union
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error,
)


def calculate_metrics(
    y_true: Union[np.ndarray, list], y_pred: Union[np.ndarray, list]
) -> Dict[str, float]:
    """
    Computes regression evaluation metrics:
    - MAE: Mean Absolute Error
    - MSE: Mean Squared Error
    - RMSE: Root Mean Squared Error
    - R2: Coefficient of Determination
    - MAPE: Mean Absolute Percentage Error (percentage)
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))

    # Safe MAPE calculation avoiding zero division
    mask = y_true != 0
    if np.any(mask):
        mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)
    else:
        mape = 0.0

    return {
        "mae": round(mae, 4),
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "mape": round(mape, 4),
    }
