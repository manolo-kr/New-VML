# backend/app/services/context.py

from __future__ import annotations
from fastapi import Request, HTTPException, status

def require_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user