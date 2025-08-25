# backend/app/config.py

import os
from typing import List

# FastAPI base path for API
API_BASE = os.getenv("API_BASE", "/api").strip()

# CORS
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS: List[str] = ["*"] if CORS_ORIGINS_ENV.strip() == "*" else [o.strip() for o in CORS_ORIGINS_ENV.split(",") if o.strip()]

# Postgres
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/visualml")

# Mongo
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "visualml")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "jobs")

# MLflow & artifacts
MLFLOW_URI = os.getenv("MLFLOW_URI", "http://localhost:5000")
ARTIFACT_ROOT = os.getenv("ARTIFACT_ROOT", os.path.abspath("./artifacts"))

# Worker quotas (내부 허용 모드 기본값)
WORKER_MAX_PARALLEL = int(os.getenv("WORKER_MAX_PARALLEL", "2"))   # 워커 동시 최대 잡
WORKER_RESERVE_CPUS = int(os.getenv("WORKER_RESERVE_CPUS", "4"))   # 남겨둘 CPU 코어 수
USER_MAX_QUEUE = int(os.getenv("USER_MAX_QUEUE", "10"))            # 유저별 큐 상한 (내부 모드에선 사용 안함)

# Auth (내부 허용 모드에서는 실사용 X, 형태만 보유)
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ISSUER = os.getenv("JWT_ISSUER", "visualml")
JWT_EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MIN", "60"))