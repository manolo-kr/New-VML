# backend/app/services/data_loader.py

from __future__ import annotations
import os
import pandas as pd

def load_dataset(uri: str) -> pd.DataFrame:
    """
    file:// 경로만 지원 (필요 시 s3:// 등 확장)
    """
    if uri.startswith("file://"):
        path = uri.replace("file://", "", 1)
        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            return pd.read_csv(path)
        if ext == ".xlsx":
            return pd.read_excel(path)
        if ext == ".parquet":
            return pd.read_parquet(path)
        raise ValueError(f"unsupported extension: {ext}")
    raise ValueError("only file:// supported for now")