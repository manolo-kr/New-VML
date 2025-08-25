# backend/app/middleware/auth_middleware.py

from __future__ import annotations
from typing import Optional, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.auth_utils import decode_token

class AuthMiddleware(BaseHTTPMiddleware):
    """
    모든 요청에서 Authorization: Bearer <token> 을 파싱해 request.state.user 로 저장.
    /auth/*, /docs 등은 라우터 측에서 따로 허용.
    """
    async def dispatch(self, request: Request, call_next):
        user: Optional[Dict[str, Any]] = None
        auth = request.headers.get("Authorization") or ""
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
            payload = decode_token(token)
            if payload:
                user = {
                    "user_id": payload.get("sub"),
                    "email": payload.get("email"),
                    "role": payload.get("role", "user")
                }
        request.state.user = user
        response = await call_next(request)
        return response