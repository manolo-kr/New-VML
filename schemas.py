# backend/app/auth/schemas.py

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Dict, Any

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenPair(BaseModel):
    access_token: str
    access_exp: int
    refresh_token: str
    refresh_exp: int
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class UserOut(BaseModel):
    id: str
    username: str
    role: str = "user"
    meta: Optional[Dict[str, Any]] = None