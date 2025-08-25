# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

from app.config import settings
from app.db import create_db_and_tables
from app.api import router as api_router
from app.auth.router_auth import router as auth_router
from app.queue_mongo import ensure_indexes
from app.ui.app import build_dash_app

app = FastAPI(
    title="Visual ML",
    version="1.0.0",
    docs_url=f"{settings.API_BASE}/docs",
    openapi_url=f"{settings.API_BASE}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth 엔드포인트
app.include_router(auth_router, prefix=f"{settings.API_BASE}/auth", tags=["auth"])
# 도메인 API
app.include_router(api_router, prefix=settings.API_BASE, tags=["api"])

# Dash mount at "/"
dash_app = build_dash_app()
app.mount("/", WSGIMiddleware(dash_app.server))


@app.on_event("startup")
def _init():
    # DB 테이블 생성
    create_db_and_tables()
    # Mongo 인덱스
    ensure_indexes()
