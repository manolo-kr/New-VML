# backend/app/services/auth_utils.py

from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import bcrypt, jwt
from app.config import settings


def hash_password(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(sub: str, extra: Optional[Dict[str, Any]] = None, expires_minutes: Optional[int] = None) -> str:
    now = datetime.utcnow()
    exp = now + timedelta(minutes=expires_minutes or settings.JWT_EXPIRE_MIN)
    payload = {"sub": sub, "iat": now, "exp": exp, **(extra or {})}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])