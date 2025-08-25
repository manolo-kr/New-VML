# backend/app/models.py

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON

class Project(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Analysis(SQLModel, table=True):
    id: str = Field(primary_key=True)
    project_id: str = Field(index=True)
    name: str
    dataset_uri: str
    dataset_original_name: Optional[str] = None  # ← 올바른 컬럼명
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MLTask(SQLModel, table=True):
    id: str = Field(primary_key=True)
    analysis_id: str = Field(index=True)
    task_type: str  # "classification" | "regression"
    target: str
    split: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    model_family: str
    model_params: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = Field(default="ready")
    created_at: datetime = Field(default_factory=datetime.utcnow)