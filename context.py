# backend/app/services/context.py

from __future__ import annotations
from typing import Optional
from fastapi import Request


def get_user_id(req: Request) -> Optional[str]:
    # 인증 미들웨어가 request.state.user_id 를 세팅했다고 가정
    return getattr(req.state, "user_id", None)