# backend/app/models.py

from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON

class Project(SQLModel, table=True):
    __tablename__ = "project"
    id: str = Field(primary_key=True)
    name: str
    created_at: datetime

class Analysis(SQLModel, table=True):
    __tablename__ = "analysis"
    id: str = Field(primary_key=True)
    project_id: str = Field(index=True)
    name: str
    dataset_uri: str
    dataset_original_name: Optional[str] = None
    created_at: datetime

class MLTask(SQLModel, table=True):
    __tablename__ = "mltask"
    id: str = Field(primary_key=True)
    analysis_id: str = Field(index=True)
    task_type: str  # "classification" | "regression"
    target: str
    split: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    model_family: str
    model_params: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = "ready"
    created_at: datetime

class User(SQLModel, table=True):
    __tablename__ = "user"
    id: str = Field(primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = None
    password_hash: str
    role: str = "user"  # "user" | "admin"
    created_at: datetime