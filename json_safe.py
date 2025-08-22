# backend/app/utils/json_safe.py

"""
JSON 직렬화 안전 헬퍼
- NaN, +Inf, -Inf -> None
- numpy/pandas/native 혼합 타입을 재귀적으로 처리
- datetime -> ISO8601
- DataFrame 미리보기 편의 함수 제공
"""
from __future__ import annotations
from typing import Any, Mapping, List, Dict
import math
import numpy as np
import pandas as pd
from datetime import datetime, date
from decimal import Decimal

Finite = (int, float, np.integer, np.floating)

def _finite_or_none(x: Any) -> Any:
    if isinstance(x, Finite):
        xf = float(x)
        if math.isfinite(xf):
            return xf
        return None
    return x

def _to_builtin(x: Any) -> Any:
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (Decimal,)):
        return float(x)
    if isinstance(x, (datetime, date)):
        return x.isoformat()
    return x

def json_safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, bytes)):
        return obj

    obj = _to_builtin(obj)
    obj = _finite_or_none(obj)

    if isinstance(obj, (type(None), bool, int, float, str)):
        return obj

    if obj is pd.NA:
        return None

    if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)

    if isinstance(obj, Mapping):
        return {str(k): json_safe(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [json_safe(v) for v in obj]

    if isinstance(obj, np.ndarray):
        return [json_safe(v) for v in obj.tolist()]

    if isinstance(obj, pd.Series):
        return [json_safe(v) for v in obj.tolist()]

    if isinstance(obj, pd.DataFrame):
        return {
            "columns": [str(c) for c in obj.columns],
            "rows": [[json_safe(v) for v in row] for row in obj.itertuples(index=False, name=None)]
        }

    try:
        return str(obj)
    except Exception:
        return None

def df_preview_safe(df: pd.DataFrame, limit: int = 50) -> Dict[str, Any]:
    head = df.head(int(limit)).copy()
    rows: List[List[Any]] = []
    for row in head.itertuples(index=False, name=None):
        rows.append([json_safe(v) for v in row])
    return {"columns": [str(c) for c in head.columns.tolist()], "rows": rows}