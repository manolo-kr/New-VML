# backend/app/main.py

from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

from app.config import settings
from app.db import create_db_and_tables
from app.api import router
from app.ui.app import build_dash_app
from app.queue_mongo import ensure_indexes
from app.middleware.auth_middleware import AuthMiddleware

app = FastAPI(
    title="Visual ML",
    version="1.0.0",
    docs_url=f"{settings.API_BASE}/docs",
    openapi_url=f"{settings.API_BASE}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == ["*"] else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

app.include_router(router, prefix=settings.API_BASE)

dash_app = build_dash_app()
app.mount("/", WSGIMiddleware(dash_app.server))

@app.on_event("startup")
def _init():
    create_db_and_tables()
    ensure_indexes()
