# backend/app/config.py

from __future__ import annotations
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core
    API_BASE: str = Field(default="/api")
    CORS_ORIGINS: List[str] = Field(default=["*"])

    # DB
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "vml"
    POSTGRES_USER: str = "ml"
    POSTGRES_PASSWORD: str = "ml"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Mongo
    MONGO_URI: str = "mongodb://127.0.0.1:27017"
    MONGO_DB: str = "vml"
    MONGO_COLLECTION: str = "jobs"

    # Artifacts / MLflow (Z 드라이브)
    ARTIFACT_ROOT: str = r"Z:\vml_artifacts"
    MLFLOW_URI: str = r"file:Z:\mlflow"

    # Auth / JWT
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 토큰 자체 만료
    INACTIVITY_MINUTES: int = 10          # 비활성 최대 시간(프론트 + 토큰 TTL)

    # Quotas
    MAX_ACTIVE_RUNS_GLOBAL: int = 20
    MAX_ACTIVE_RUNS_PER_USER: int = 5
    RESERVED_CPUS: int = 4  # 워커 CPU 여유 예약(지표)

settings = Settings()
