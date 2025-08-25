# backend/app/models.py

from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


def now_utc() -> datetime:
    return datetime.utcnow()


# ---------- Users ----------
class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    role: str = Field(default="user")  # "user" | "admin"
    password_hash: str
    created_at: datetime = Field(default_factory=now_utc)


# ---------- Projects / Analyses / Tasks ----------
class Project(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=now_utc)


class Analysis(SQLModel, table=True):
    id: str = Field(primary_key=True)
    project_id: str = Field(index=True)
    name: str
    dataset_uri: str
    dataset_original_name: Optional[str] = None  # ← 오타 수정된 확정 컬럼명
    created_at: datetime = Field(default_factory=now_utc)


class MLTask(SQLModel, table=True):
    id: str = Field(primary_key=True)
    analysis_id: str = Field(index=True)
    task_type: str  # "classification" | "regression"
    target: str
    split: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    model_family: str
    model_params: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    status: str = Field(default="ready")
    created_at: datetime = Field(default_factory=now_utc)