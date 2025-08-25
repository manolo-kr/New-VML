# backend/app/auth/router_auth.py

from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import Dict, Any

from ..db import get_session
from ..models import User
from ..services.auth_utils import (
    verify_password, create_access_token, create_refresh_token, decode_token
)
from .schemas import LoginRequest, TokenPair, RefreshRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

def _user_out(u: User) -> UserOut:
    return UserOut(id=u.id, username=u.username, role=u.role or "user", meta=u.meta or {})

@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, s: Session = Depends(get_session)) -> TokenPair:
    q = select(User).where(User.username == body.username)
    u = s.exec(q).first()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    access, access_exp = create_access_token(u.id, {"role": u.role or "user"})
    refresh, refresh_exp = create_refresh_token(u.id, {"role": u.role or "user"})
    return TokenPair(
        access_token=access,
        access_exp=access_exp,
        refresh_token=refresh,
        refresh_exp=refresh_exp,
    )

@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, s: Session = Depends(get_session)) -> TokenPair:
    try:
        payload: Dict[str, Any] = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid refresh token")

    if payload.get("typ") != "refresh":
        raise HTTPException(status_code=400, detail="not a refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="invalid refresh token")

    u = s.get(User, user_id)
    if not u:
        raise HTTPException(status_code=401, detail="user not found")

    access, access_exp = create_access_token(u.id, {"role": u.role or "user"})
    refresh, refresh_exp = create_refresh_token(u.id, {"role": u.role or "user"})

    return TokenPair(
        access_token=access,
        access_exp=access_exp,
        refresh_token=refresh,
        refresh_exp=refresh_exp,
    )

@router.post("/logout")
def logout() -> dict:
    return {"ok": True}