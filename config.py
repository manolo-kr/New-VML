# backend/app/config.py

import os

# API base
API_BASE = os.getenv("API_BASE", "/api")

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Postgres
PG_DSN = os.getenv("PG_DSN", "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/vml")

# Mongo
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
MONGO_DB = os.getenv("MONGO_DB", "vml")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "jobs")

# Artifacts/MLflow
ARTIFACT_ROOT = os.getenv("ARTIFACT_ROOT", "./artifacts")
MLFLOW_URI = os.getenv("MLFLOW_URI", "http://127.0.0.1:5000")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACCESS_TOKEN_MIN = int(os.getenv("ACCESS_TOKEN_MIN", "10"))       # 10분
REFRESH_TOKEN_MIN = int(os.getenv("REFRESH_TOKEN_MIN", "1440"))   # 24시간

# Quotas (기본값: 완화)
USER_MAX_CONCURRENT = int(os.getenv("USER_MAX_CONCURRENT", "2"))
USER_MAX_QUEUED = int(os.getenv("USER_MAX_QUEUED", "10"))
GLOBAL_MAX_CONCURRENT = int(os.getenv("GLOBAL_MAX_CONCURRENT", "8"))
GLOBAL_MAX_QUEUED = int(os.getenv("GLOBAL_MAX_QUEUED", "100"))