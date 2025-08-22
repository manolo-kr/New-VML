# backend/app/middleware/auth_middleware.py

from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from ..config import INTERNAL_ALLOW, TRUSTED_INTERNAL_IPS, TRUST_PROXY, FORWARDED_FOR_HEADER

class AuthMiddleware(BaseHTTPMiddleware):
    """
    내부 요청(신뢰 IP)은 인증 우회: request.state.user = {"id":"internal"} 로 표시
    외부 요청은 현재 별도 검증 없음(필요시 확장 가능)
    """
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        if INTERNAL_ALLOW and client_ip in TRUSTED_INTERNAL_IPS:
            request.state.user = {"id": "internal", "role": "system"}
            return await call_next(request)
        # 외부는 통과(보안 강화 필요 시 여기서 토큰 검증 추가)
        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        if TRUST_PROXY:
            hdr = request.headers.get(FORWARDED_FOR_HEADER)
            if hdr:
                first = hdr.split(",")[0].strip()
                if first:
                    return first
        return request.client.host if request.client else ""