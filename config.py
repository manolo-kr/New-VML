# backend/app/config.py

from __future__ import annotations
from pydantic import BaseSettings, Field, AnyHttpUrl
from typing import List, Optional


class Settings(BaseSettings):
    # ── API / CORS ────────────────────────────────────────────────
    API_BASE: str = "/api"
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # ── DB (PostgreSQL) ──────────────────────────────────────────
    # 예: postgresql+psycopg2://ml:ml@127.0.0.1:5432/vml?sslmode=disable
    DATABASE_URL: str = "postgresql+psycopg2://ml:ml@127.0.0.1:5432/vml?sslmode=disable"

    # ── Mongo (Queue) ────────────────────────────────────────────
    MONGO_URI: str = "mongodb://127.0.0.1:27017"
    MONGO_DB: str = "vml"
    MONGO_COLLECTION: str = "jobs"

    # ── MLflow ───────────────────────────────────────────────────
    MLFLOW_URI: str = "http://127.0.0.1:5000"

    # ── 파일/아티팩트 루트 ───────────────────────────────────────
    ARTIFACT_ROOT: str = "./artifacts"

    # ── 인증 (JWT) ───────────────────────────────────────────────
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MIN: int = 60
    JWT_REFRESH_EXPIRE_MIN: int = 60 * 24 * 14

    # ── UI에서 백엔드 접근용 베이스 (Dash 클라이언트에서 사용) ──
    # 예: http://127.0.0.1:8065  (None이면 동일 오리진)
    API_ORIGIN: Optional[AnyHttpUrl] = None

    # ── 워커/큐 제한(예시) ───────────────────────────────────────
    GLOBAL_MAX_RUNNING: int = 8
    WORKER_RESERVE_CPU: int = 4
    USER_MAX_CONCURRENT: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()