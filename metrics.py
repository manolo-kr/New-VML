# backend/app/services/metrics.py

from __future__ import annotations
from typing import Dict, Any, Tuple
import numpy as np

def basic_classification_metrics(y_true, y_prob) -> Dict[str, Any]:
    """
    간단 예시(워커에서 주로 계산). 여기선 placeholder.
    """
    y_pred = (np.array(y_prob) >= 0.5).astype(int)
    acc = float((y_pred == np.array(y_true)).mean()) if len(y_true) else 0.0
    return {"accuracy": acc}

def gain_lift_at_k(y_true, y_score, k: float = 0.1) -> Tuple[float, float]:
    """
    상위 k 비율 구간의 누적 Lift/Gain (간단 버전)
    """
    n = len(y_true)
    if n == 0:
        return 0.0, 0.0
    k = max(min(k, 1.0), 0.0)
    top = max(int(n * k), 1)
    idx = np.argsort(-np.array(y_score))
    y_top = np.array(y_true)[idx][:top]
    base_rate = float(np.mean(y_true))
    top_rate = float(np.mean(y_top))
    lift = (top_rate / base_rate) if base_rate > 0 else 0.0
    gain = float(y_top.sum()) / float(np.sum(y_true)) if np.sum(y_true) > 0 else 0.0
    return gain, lift