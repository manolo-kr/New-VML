# backend/app/auth/router_auth.py

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.auth.schemas import LoginRequest, TokenResponse
from app.services.auth_utils import create_access_token, verify_password, hash_password

router_auth = APIRouter(prefix="/auth", tags=["auth"])

# 데모 계정(실운영에선 DB 사용자 테이블 사용)
_USERS = {
    "admin": hash_password("admin"),
    "ml": hash_password("ml"),
}

@router_auth.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    h = _USERS.get(body.username)
    if not h or not verify_password(body.password, h):
        raise HTTPException(401, "invalid credentials")
    token = create_access_token(sub=body.username, extra={"role": "user"})
    return TokenResponse(access_token=token)
