# backend/app/middleware/inactivity_timeout.py

from __future__ import annotations
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.middleware.base import BaseHTTPMiddleware

class InactivityNoteMiddleware(BaseHTTPMiddleware):
    """
    서버 측 '비활성 자동 로그아웃'은 일반적으로 JWT의 짧은 exp + refresh 로 관리합니다.
    이 미들웨어는 큰 동작을 하지 않고, 단지 응답 헤더에 힌트를 추가하는 스텁입니다.
    클라이언트는 이 헤더를 참고하여 세션 타이머(예: 10분) UI를 띄우고 연장/로그아웃을 수행하세요.
    """
    def __init__(self, app: ASGIApp, idle_hint_seconds: int = 600):
        super().__init__(app)
        self.idle_hint_seconds = idle_hint_seconds

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Idle-Hint-Seconds"] = str(self.idle_hint_seconds)
        return response