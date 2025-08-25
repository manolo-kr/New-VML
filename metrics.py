# backend/app/services/metrics.py

from __future__ import annotations
from typing import Dict, Any, List


def summarize_binary_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["auc", "accuracy", "precision", "recall", "f1"]
    return {k: metrics.get(k) for k in keys if k in metrics}


def compare_runs(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in runs:
        row = {
            "run_id": r.get("id"),
            "status": r.get("status"),
            **summarize_binary_metrics(r.get("metrics") or {})
        }
        out.append(row)
    return out