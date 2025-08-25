# backend/app/middleware/auth_middleware.py

from __future__ import annotations
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.auth_utils import decode_token


class AuthMiddleware(BaseHTTPMiddleware):
    """
    모든 요청은 Authorization: Bearer <token> 를 기대.
    (내부 허용 모드가 아니라면) 토큰 없으면 익명 처리.
    보호가 필요한 라우터에서 별도 검사.
    """
    async def dispatch(self, request: Request, call_next: Callable):
        auth = request.headers.get("Authorization", "")
        user_id = None
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
            except Exception:
                user_id = None
        request.state.user_id = user_id
        return await call_next(request)
