# backend/app/models.py

from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON

# Project
class Project(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Analysis
class Analysis(SQLModel, table=True):
    id: str = Field(primary_key=True)
    project_id: str = Field(index=True)
    name: str
    dataset_uri: str
    # 철자 수정: dataset_original_name (과거 오타 호환은 Store에서 처리)
    dataset_original_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# MLTask
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