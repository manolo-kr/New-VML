# backend/app/services/context.py

from __future__ import annotations
from fastapi import Request
from typing import Optional, Dict, Any

def current_user(request: Request) -> Optional[Dict[str, Any]]:
    u = getattr(request.state, "user", None)
    if not u:
        return None
    return {"id": u.get("id"), "role": u.get("role", "user")}