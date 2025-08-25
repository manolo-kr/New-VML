# backend/app/middleware/auth_middleware.py

from __future__ import annotations

import ipaddress
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import BYPASS_AUTH_INTERNAL
from ..services.auth_utils import decode_access_token


def _is_private_ip(ip: Optional[str]) -> bool:
    try:
        if not ip:
            return False
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback
    except Exception:
        return False


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 내부 IP이면 토큰 없어도 통과(옵션)
        if BYPASS_AUTH_INTERNAL and _is_private_ip(request.client.host):
            request.state.user = {"id": "internal", "email": "internal@local", "role": "admin", "name": "internal"}
            return await call_next(request)

        # Authorization: Bearer <token>
        auth = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
            try:
                payload = decode_access_token(token)
                request.state.user = {
                    "id": payload.get("sub"),
                    "email": payload.get("email"),
                    "name": payload.get("name"),
                    "role": payload.get("role", "user"),
                }
            except Exception:
                request.state.user = None
        else:
            request.state.user = None

        return await call_next(request)