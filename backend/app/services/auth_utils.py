# backend/app/services/auth_utils.py

from __future__ import annotations
from typing import Optional, Tuple, Any, Dict
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Request

from app.config import settings


# ------------------------
# Password hashing / verify
# ------------------------
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ------------------------
# JWT helpers
# ------------------------
class JWTPayload:
    def __init__(self, sub: str, role: str, exp: int):
        self.sub = sub
        self.role = role
        self.exp = exp


def create_access_token(*, sub: str, role: str, ttl: timedelta) -> Tuple[str, int]:
    """
    반환: (token, exp_unix_ts)
    """
    now = datetime.now(timezone.utc)
    exp = now + ttl
    payload = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return token, int(exp.timestamp())


def decode_token_optional(request: Request) -> Optional[JWTPayload]:
    """
    Authorization: Bearer <token> → payload
    유효하지 않으면 None
    """
    auth = request.headers.get("Authorization") or ""
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    try:
        payload: Dict[str, Any] = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
            audience=settings.JWT_AUDIENCE,
            options={"require": ["exp", "sub"]},
        )
        return JWTPayload(sub=payload.get("sub"), role=payload.get("role", "user"), exp=int(payload.get("exp")))
    except Exception:
        return None