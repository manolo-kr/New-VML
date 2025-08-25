# backend/app/config.py

from __future__ import annotations

import os
from typing import List

# ---------- API ----------
API_BASE = os.getenv("API_BASE", "/api").strip()
CORS_ORIGINS: List[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

# ---------- DB ----------
# e.g. postgresql+psycopg2://user:pass@localhost:5432/visualml
DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/visualml")

# ---------- Mongo (Queue) ----------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
MONGO_DB = os.getenv("MONGO_DB", "visualml")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "jobs")

# ---------- Artifacts / MLflow ----------
ARTIFACT_ROOT = os.getenv("ARTIFACT_ROOT", os.path.abspath(os.path.join(os.getcwd(), "artifacts")))
MLFLOW_URI = os.getenv("MLFLOW_URI", "file:" + os.path.join(ARTIFACT_ROOT, "mlruns"))

# ---------- JWT ----------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))  # 1h

# ---------- Auth Bypass for Internal Requests ----------
BYPASS_AUTH_INTERNAL = os.getenv("BYPASS_AUTH_INTERNAL", "1") == "1"

# ---------- Quotas (API side) ----------
GLOBAL_MAX_CONCURRENT = int(os.getenv("GLOBAL_MAX_CONCURRENT", "32"))
USER_MAX_CONCURRENT = int(os.getenv("USER_MAX_CONCURRENT", "8"))

# ---------- Worker Settings ----------
WORKER_MAX_CONCURRENT = int(os.getenv("WORKER_MAX_CONCURRENT", "8"))
WORKER_RESERVE_CPU = int(os.getenv("WORKER_RESERVE_CPU", "4"))  # keep free cores
WORKER_DEVICE = os.getenv("WORKER_DEVICE", "cpu")  # or "cuda:0"