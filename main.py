# backend/app/main.py

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

from .config import CORS_ORIGINS, API_BASE
from .db import create_db_and_tables
from .api import router as api_router
from .auth.router_auth import router as auth_router
from .middleware.auth_middleware import AuthMiddleware
from .queue_mongo import ensure_indexes
from .ui.app import build_dash_app


def create_app() -> FastAPI:
    app = FastAPI(
        title="Visual ML",
        version="1.0.0",
        docs_url=f"{API_BASE}/docs",
        openapi_url=f"{API_BASE}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if CORS_ORIGINS == ["*"] else CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuthMiddleware)

    # REST routers
    app.include_router(auth_router, prefix=f"{API_BASE}/auth", tags=["auth"])
    app.include_router(api_router, prefix=API_BASE, tags=["api"])

    # Mount Dash at "/"
    dash_app = build_dash_app()
    app.mount("/", WSGIMiddleware(dash_app.server))

    @app.on_event("startup")
    def _startup() -> None:
        create_db_and_tables()
        ensure_indexes()

    return app


app = create_app()