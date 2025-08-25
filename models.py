from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String


class Project(SQLModel, table=True):
    """프로젝트 메타"""
    __tablename__ = "project"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Analysis(SQLModel, table=True):
    """분석 단위(데이터세트 포함)"""
    __tablename__ = "analysis"

    id: str = Field(primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    name: str
    dataset_uri: str
    # ✅ 오타 없이 일관: dataset_original_name
    dataset_original_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MLTask(SQLModel, table=True):
    """학습 태스크(모델/타깃/스플릿/파라미터)"""
    # ❗️기존 DB가 mltask 테이블명을 사용하고 있으므로 그대로 맞춥니다.
    __tablename__ = "mltask"

    id: str = Field(primary_key=True)
    analysis_id: str = Field(foreign_key="analysis.id", index=True)

    # "classification" | "regression"
    task_type: str = Field(index=True)

    target: str

    # PostgreSQL JSONB로 고정 (마이그레이션에서 json→jsonb 변환 완료 가정)
    split: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    model_family: str = Field(index=True)
    model_params: dict = Field(default_factory=dict, sa_column=Column(JSONB))

    status: str = Field(default="ready", index=True)  # ready|queued|running|succeeded|failed|canceled ...
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    """로그인 사용자(로컬 인증/JWT 발급용)"""
    __tablename__ = "app_user"

    id: str = Field(primary_key=True)
    # SQLModel의 unique=True는 일부 버전에서 동작 보장이 약해 명시적으로 Column 사용
    email: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    password_hash: str  # bcrypt 등
    role: str = Field(default="user", index=True)  # admin|user
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)