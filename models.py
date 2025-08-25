# backend/app/models.py

from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON

class Project(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    created_at: datetime

class Analysis(SQLModel, table=True):
    id: str = Field(primary_key=True)
    project_id: str = Field(index=True)
    name: str
    dataset_uri: str
    # 오타 호환 컬럼(기존): dataset_orinial_name
    dataset_orinial_name: Optional[str] = None
    # 정식 컬럼
    dataset_original_name: Optional[str] = None
    created_at: datetime

class MLTask(SQLModel, table=True):
    id: str = Field(primary_key=True)
    analysis_id: str = Field(index=True)
    task_type: str  # "classification" | "regression"
    target: str
    split: dict = Field(default_factory=dict, sa_column=Column(JSON))
    model_family: str
    model_params: dict = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = "ready"
    created_at: datetime

class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: str = "user"  # "admin" | "user"
    meta: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime