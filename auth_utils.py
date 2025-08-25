# backend/app/services/auth_utils.py

# 내부 허용 모드: 실제 로그인/JWT 미사용. 훅만 남겨둠.

from __future__ import annotations
from typing import Tuple

def hash_password(pw: str) -> str:
    return pw  # placeholder

def verify_password(pw: str, hashed: str) -> bool:
    return pw == hashed

def create_access_token(user_id: str) -> str:
    return "INTERNAL_MODE"