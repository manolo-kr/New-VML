# backend/app/services/metrics.py

from __future__ import annotations
from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score, confusion_matrix

def basic_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, proba: np.ndarray | None = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        out["accuracy"] = float(accuracy_score(y_true, y_pred))
        out["f1"] = float(f1_score(y_true, y_pred, average="weighted"))
        if proba is not None and proba.ndim == 1:
            out["auc"] = float(roc_auc_score(y_true, proba))
    except Exception:
        pass
    try:
        cm = confusion_matrix(y_true, y_pred)
        out["confusion_matrix"] = cm.tolist()
    except Exception:
        pass
    return out