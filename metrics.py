# backend/app/services/metrics.py

from __future__ import annotations
from typing import Dict, Any, Tuple
import numpy as np

from sklearn.metrics import (
    roc_curve, auc, confusion_matrix, f1_score, accuracy_score,
    mean_squared_error, mean_absolute_error
)

def cls_metrics(y_true, y_prob, threshold: float = 0.5) -> Dict[str, Any]:
    y_pred = (y_prob >= threshold).astype(int)
    fpr, tpr, thr = roc_curve(y_true, y_prob)
    out = {
        "auc": float(auc(fpr, tpr)),
        "f1": float(f1_score(y_true, y_pred)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "roc": {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "thresholds": thr.tolist()},
        "confusion": confusion_matrix(y_true, y_pred).tolist(),
    }
    return out

def reg_metrics(y_true, y_pred) -> Dict[str, Any]:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    return {"rmse": rmse, "mae": mae}