# backend/app/auth/router_auth.py

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.store_sql import Repo
from app.services.auth_utils import (
    verify_password,
    create_access_token,
    decode_token_optional,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    client_ip: Optional[str] = None
    exp: Optional[int] = None  # unix ts


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, s: Session = Depends(get_session)):
    repo = Repo(s)
    user = repo.get_user_by_email(body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    # TTL (분): settings.SESSION_TTL_MINUTES (기본 10)
    ttl = timedelta(minutes=settings.SESSION_TTL_MINUTES)
    token, exp_ts = create_access_token(sub=user.id, role=user.role, ttl=ttl)

    client_ip = request.client.host if request.client else None
    return TokenOut(
        access_token=token,
        user={"id": user.id, "email": user.email, "role": user.role},
        client_ip=client_ip,
        exp=exp_ts,
    )


@router.post("/refresh", response_model=TokenOut)
def refresh(request: Request, s: Session = Depends(get_session)):
    """
    유효 토큰 전제(Authorization 헤더). 새 토큰 재발급(연장).
    """
    payload = decode_token_optional(request)
    if not payload:
        raise HTTPException(status_code=401, detail="invalid or expired token")

    repo = Repo(s)
    user = repo.get_user(payload.sub)
    if not user:
        raise HTTPException(status_code=401, detail="user not found")

    ttl = timedelta(minutes=settings.SESSION_TTL_MINUTES)
    token, exp_ts = create_access_token(sub=user.id, role=user.role, ttl=ttl)
    client_ip = request.client.host if request.client else None
    return TokenOut(
        access_token=token,
        user={"id": user.id, "email": user.email, "role": user.role},
        client_ip=client_ip,
        exp=exp_ts,
    )


@router.get("/me")
def me(request: Request, s: Session = Depends(get_session)):
    payload = decode_token_optional(request)
    if not payload:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    repo = Repo(s)
    user = repo.get_user(payload.sub)
    if not user:
        raise HTTPException(status_code=401, detail="user not found")
    client_ip = request.client.host if request.client else None
    return {
        "user": {"id": user.id, "email": user.email, "role": user.role},
        "client_ip": client_ip,
        "exp": payload.exp,
    }


@router.post("/logout")
def logout():
    """
    서버측 세션 상태를 따로 유지하지 않으므로 클라이언트가 토큰을 폐기하면 됨.
    (추후 서버 블랙리스트/세션 테이블을 두는 경우 이곳에서 무효화 처리)
    """
    return {"ok": True}