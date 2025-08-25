# backend/app/middleware/auth_middleware.py

from __future__ import annotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional, Dict, Any
import re
from ..services.auth_utils import decode_token

PUBLIC_PATHS = [
    r"^/auth/login$",
    r"^/auth/refresh$",
    r"^/auth/logout$",
    r"^/api/docs",
    r"^/api/openapi.json",
    r"^/_dash-.*",
    r"^/assets/.*",
    r"^/$",
]

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._compiled = [re.compile(p) for p in PUBLIC_PATHS]

    def _is_public(self, path: str) -> bool:
        return any(r.match(path) for r in self._compiled)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if self._is_public(path):
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse({"detail": "missing token"}, status_code=401)
        token = auth.split(" ", 1)[1].strip()
        try:
            payload: Dict[str, Any] = decode_token(token)
        except Exception:
            return JSONResponse({"detail": "invalid token"}, status_code=401)

        if payload.get("typ") != "access":
            return JSONResponse({"detail": "invalid token type"}, status_code=401)

        request.state.user = {
            "id": payload.get("sub"),
            "role": payload.get("role", "user"),
        }
        return await call_next(request)