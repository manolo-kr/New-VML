# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

from .config import CORS_ORIGINS, API_BASE
from .db import create_db_and_tables
from .api import router
from .ui.app import build_dash_app
from .queue_mongo import ensure_indexes
from .middleware.auth_middleware import AuthMiddleware

app = FastAPI(
    title="Visual ML",
    version="1.0.0",
    docs_url=f"{API_BASE}/docs",
    openapi_url=f"{API_BASE}/openapi.json"
)

# 내부요청 우선 인식
app.add_middleware(AuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if CORS_ORIGINS == ["*"] else CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=API_BASE)

# Dash mount at "/"
dash_app = build_dash_app()
app.mount("/", WSGIMiddleware(dash_app.server))

@app.on_event("startup")
def _init():
    create_db_and_tables()
    ensure_indexes()