# backend/app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# --- 기본 ---
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
API_PORT = int(os.getenv("API_PORT", "8065"))
API_BASE = os.getenv("API_BASE", "/api").strip()

# --- DB ---
# 예: postgresql+psycopg2://user:pass@localhost:5432/visualml
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/visualml")

# --- ML/Artifacts ---
MLFLOW_URI = os.getenv("MLFLOW_URI", "file:./mlruns")
ARTIFACT_ROOT = os.getenv("ARTIFACT_ROOT", "./artifacts")

# --- Mongo Queue ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "vml")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "jobs")

# --- Data Source 제한 ---
DATA_SOURCE_ONLY_FILES = os.getenv("DATA_SOURCE_ONLY_FILES", "true").lower() == "true"
DATA_SOURCE_ALLOWED_EXT = [e.strip().lower() for e in os.getenv("DATA_SOURCE_ALLOWED_EXT", "csv,xlsx,parquet").split(",")]

# --- 내부 요청 허용(동일 서버에서 오는 요청은 인증 우회) ---
INTERNAL_ALLOW = (os.getenv("INTERNAL_ALLOW", "true").lower() == "true")
TRUSTED_INTERNAL_IPS = [ip.strip() for ip in os.getenv("TRUSTED_INTERNAL_IPS", "127.0.0.1,::1").split(",")]
TRUST_PROXY = (os.getenv("TRUST_PROXY", "false").lower() == "true")
FORWARDED_FOR_HEADER = os.getenv("FORWARDED_FOR_HEADER", "X-Forwarded-For")