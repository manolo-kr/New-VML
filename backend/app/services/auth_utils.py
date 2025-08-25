# backend/app/services/auth_utils.py

from __future__ import annotations
from datetime import datetime, timedelta
import bcrypt
import jwt
from typing import Optional, Dict, Any

from app.config import settings

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False

def create_access_token(subject: str, claims: Optional[Dict[str, Any]] = None, expires_minutes: Optional[int] = None) -> str:
    to_encode = {
        "sub": subject,
        "iat": int(datetime.utcnow().timestamp()),
    }
    if claims:
        to_encode.update(claims)
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except Exception:
        return None