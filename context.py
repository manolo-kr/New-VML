# backend/app/services/context.py

from __future__ import annotations
from typing import Optional, Dict, Any

from fastapi import Request, HTTPException, status


def get_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    return getattr(request.state, "user", None)


def require_user_id(request: Request) -> str:
    user = get_user_from_request(request)
    if not user or not user.get("id"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user["id"]