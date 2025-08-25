# backend/app/services/auth_utils.py

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt  # PyJWT

from ..config import JWT_SECRET, JWT_ALG, JWT_EXP_MINUTES


# -------------------------------
# Password hashing (PBKDF2-SHA256)
# -------------------------------
_PBKDF2_ITER = 200_000
_SCHEME = "pbkdf2"
_HASH = "sha256"


def _b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")


def _b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("utf-8"))


def hash_password(plain: str) -> str:
    if not isinstance(plain, str) or not plain:
        raise ValueError("empty password")
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac(_HASH, plain.encode("utf-8"), salt, _PBKDF2_ITER)
    return f"{_SCHEME}${_HASH}${_PBKDF2_ITER}${_b64e(salt)}${_b64e(dk)}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        scheme, algo, iter_s, salt_b64, hash_b64 = stored.split("$", 4)
        if scheme != _SCHEME or algo != _HASH:
            return False
        iters = int(iter_s)
        salt = _b64d(salt_b64)
        target = _b64d(hash_b64)
        dk = hashlib.pbkdf2_hmac(_HASH, plain.encode("utf-8"), salt, iters)
        return hmac.compare_digest(dk, target)
    except Exception:
        return False


# -------------------------------
# JWT (access token)
# -------------------------------
def create_access_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=int(expires_minutes or JWT_EXP_MINUTES))
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])