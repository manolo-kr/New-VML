# backend/app/services/auth_utils.py

from __future__ import annotations
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
import bcrypt
import jwt

from ..config import JWT_SECRET, JWT_ALG, ACCESS_TOKEN_MIN, REFRESH_TOKEN_MIN


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(sub: str, extra: Optional[Dict[str, Any]] = None) -> Tuple[str, int]:
    exp = _now_utc() + timedelta(minutes=ACCESS_TOKEN_MIN)
    payload = {
        "sub": sub,
        "typ": "access",
        "iat": int(time.time()),
        "exp": int(exp.timestamp()),
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token, payload["exp"]


def create_refresh_token(sub: str, extra: Optional[Dict[str, Any]] = None) -> Tuple[str, int]:
    exp = _now_utc() + timedelta(minutes=REFRESH_TOKEN_MIN)
    payload = {
        "sub": sub,
        "typ": "refresh",
        "iat": int(time.time()),
        "exp": int(exp.timestamp()),
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token, payload["exp"]


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])