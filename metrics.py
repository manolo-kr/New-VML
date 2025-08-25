# backend/app/services/metrics.py

from __future__ import annotations
from typing import Dict, Any

def safe_number(x):
    try:
        return float(x)
    except Exception:
        return None

def summarize_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    워커가 남긴 메트릭 dict를 테이블/차트용으로 정리할 때 사용 (선택).
    """
    return {k: safe_number(v) for k, v in (metrics or {}).items()}