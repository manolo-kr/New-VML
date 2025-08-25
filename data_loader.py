# backend/app/services/data_loader.py

from __future__ import annotations

import os
import pandas as pd


def _normalize_path(uri: str) -> str:
    if not uri:
        raise ValueError("empty dataset uri")
    if uri.startswith("file://"):
        return uri.replace("file://", "", 1)
    return uri


def load_dataset(uri: str) -> pd.DataFrame:
    path = _normalize_path(uri)
    ext = os.path.splitext(path)[-1].lower()
    if ext == ".csv":
        return pd.read_csv(path)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if ext == ".parquet":
        return pd.read_parquet(path)
    try:
        return pd.read_csv(path)
    except Exception as e:
        raise ValueError(f"unsupported dataset format: {ext}, path={path}, err={e}")