# backend/app/services/metrics.py

from __future__ import annotations

from typing import Dict, Any, Optional

import numpy as np
from sklearn import metrics


def classification_report(
    y_true: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    y_pred: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    if y_proba is None and y_pred is None:
        raise ValueError("y_proba or y_pred required")

    if y_pred is None and y_proba is not None:
        y_pred = (y_proba >= 0.5).astype(int)

    out["accuracy"] = float(metrics.accuracy_score(y_true, y_pred))
    try:
        out["auc_roc"] = float(metrics.roc_auc_score(y_true, y_proba)) if y_proba is not None else None
    except Exception:
        out["auc_roc"] = None
    try:
        out["auc_pr"] = float(metrics.average_precision_score(y_true, y_proba)) if y_proba is not None else None
    except Exception:
        out["auc_pr"] = None
    out["f1"] = float(metrics.f1_score(y_true, y_pred))

    cm = metrics.confusion_matrix(y_true, y_pred, labels=[0, 1])
    out["confusion_matrix"] = cm.tolist()

    if y_proba is not None:
        fpr, tpr, roc_th = metrics.roc_curve(y_true, y_proba)
        prec, rec, pr_th = metrics.precision_recall_curve(y_true, y_proba)
        out["roc_curve"] = {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "thresholds": roc_th.tolist()}
        out["pr_curve"] = {"precision": prec.tolist(), "recall": rec.tolist(), "thresholds": pr_th.tolist()}

        ks_vals = tpr - fpr
        ks_idx = int(np.argmax(ks_vals))
        out["ks"] = {"ks": float(ks_vals[ks_idx]), "threshold": float(roc_th[min(ks_idx, len(roc_th) - 1)])}

        out["gains"] = gains_table(y_true, y_proba, buckets=10)

    return out


def gains_table(y_true: np.ndarray, y_proba: np.ndarray, buckets: int = 10) -> Dict[str, Any]:
    n = len(y_true)
    order = np.argsort(-y_proba)
    y_sorted = y_true[order]

    bucket_size = max(1, n // buckets)
    totals = int(y_true.sum())
    rows = []
    cum_pos = 0
    for i in range(buckets):
        start = i * bucket_size
        end = n if i == buckets - 1 else (i + 1) * bucket_size
        seg = y_sorted[start:end]
        pos = int(seg.sum())
        cum_pos += pos
        capture = (cum_pos / totals) * 100.0 if totals > 0 else 0.0
        lift = (pos / len(seg)) / (totals / n) if (len(seg) > 0 and totals > 0) else 0.0
        rows.append({
            "bucket": i + 1,
            "n": int(len(seg)),
            "positives": pos,
            "cum_capture_rate": capture,
            "lift": lift,
        })
    return {"rows": rows, "total_positives": totals, "n": n}