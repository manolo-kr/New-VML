# backend/app/services/data_loader.py

from __future__ import annotations
from typing import Optional
import os
import pandas as pd

def _load_file_local(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[-1].lower()
    if ext == ".csv":
        return pd.read_csv(path)
    if ext in [".xls", ".xlsx"]:
        return pd.read_excel(path)
    if ext == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"unsupported file extension: {ext}")

def load_dataset(uri: str) -> pd.DataFrame:
    """
    현재는 file:// 만 지원. s3:// 등은 확장 가능.
    """
    if uri.startswith("file://"):
        return _load_file_local(uri[len("file://"):])
    if os.path.exists(uri):
        return _load_file_local(uri)
    raise ValueError(f"unsupported uri: {uri}")