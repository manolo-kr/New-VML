# backend/app/services/data_loader.py

from __future__ import annotations
from pathlib import Path
import pandas as pd

def load_dataset(uri: str) -> pd.DataFrame:
    """
    file:// 경로만 지원 (로컬 파일)
    """
    if not uri.startswith("file://"):
        raise ValueError("only file:// uri supported for now")
    p = Path(uri.replace("file://", "", 1))
    ext = p.suffix.lower()
    if ext == ".csv":
        return pd.read_csv(p)
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(p)
    if ext == ".parquet":
        return pd.read_parquet(p)
    raise ValueError(f"unsupported extension: {ext}")