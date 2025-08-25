# backend/app/services/data_loader.py

from __future__ import annotations
import os
import pandas as pd


def load_dataset(uri: str) -> pd.DataFrame:
    """
    지원: file://*.csv|.xlsx|.parquet
    """
    if not uri.startswith("file://"):
        raise ValueError("only file:// supported")
    path = uri[len("file://"):]
    ext = os.path.splitext(path)[-1].lower()
    if ext == ".csv":
        return pd.read_csv(path)
    if ext == ".xlsx":
        return pd.read_excel(path)
    if ext == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"unsupported extension: {ext}")
