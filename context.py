# backend/app/services/context.py

from __future__ import annotations
from typing import Optional
from fastapi import Request


def current_user_id(request: Request) -> Optional[str]:
    """
    미들웨어(auth_middleware)가 세팅한 request.state.user에서 user_id를 꺼냅니다.
    없으면 None.
    """
    u = getattr(request.state, "user", None)
    if not u:
        return None
    # 토큰 payload에 "sub" 또는 "user_id"로 저장한다고 가정
    return u.get("user_id") or u.get("sub")