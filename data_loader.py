# backend/app/services/data_loader.py

from __future__ import annotations
from typing import Union
import os
import pandas as pd
from urllib.parse import urlparse
from ..config import DATA_SOURCE_ONLY_FILES, DATA_SOURCE_ALLOWED_EXT

def _ensure_file_uri(uri: str) -> str:
    # "file://..." 로 통일
    if uri.startswith("file://"):
        return uri
    if "://" not in uri:
        # 로컬 경로
        return f"file://{os.path.abspath(uri)}"
    return uri

def _read_local(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[-1].lower().lstrip(".")
    if ext not in DATA_SOURCE_ALLOWED_EXT:
        raise ValueError(f"extension '.{ext}' not allowed; allowed={DATA_SOURCE_ALLOWED_EXT}")
    if ext == "csv":
        return pd.read_csv(path)
    if ext == "xlsx":
        return pd.read_excel(path)
    if ext == "parquet":
        return pd.read_parquet(path)
    raise ValueError(f"unsupported extension: .{ext}")

def load_dataset(uri_or_path: str) -> pd.DataFrame:
    """
    현재는 file:// 만 허용. (S3/DB 커넥터는 비활성)
    """
    uri = _ensure_file_uri(uri_or_path)
    if DATA_SOURCE_ONLY_FILES and not uri.startswith("file://"):
        raise ValueError("only file:// datasets are allowed in current config")

    parsed = urlparse(uri)
    if parsed.scheme == "file":
        path = parsed.path
        return _read_local(path)

    raise ValueError(f"unsupported scheme for dataset: {parsed.scheme}")