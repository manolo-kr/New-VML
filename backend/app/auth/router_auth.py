# backend/app/auth/router_auth.py

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import jwt

from app.config import settings
from app.store_sql import Repo
from app.db import get_session, Session
from app.services.auth_utils import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginReq(BaseModel):
    username: str
    password: str

class LoginRes(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

def _create_access_token(sub: str, role: str, expires_minutes: int = 60) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "iss": "visual-ml",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

@router.post("/login", response_model=LoginRes)
def login(body: LoginReq, request: Request, s: Session = Depends(get_session)):
    repo = Repo(s)
    user = repo.get_user_by_username(body.username)

    # DB 사용자 우선. 없으면 .env 의 ADMIN_USER / ADMIN_PASS 허용(옵션)
    if user:
        if not verify_password(body.password, user.password_hash):
            raise HTTPException(401, "invalid credentials")
        uid = user.id
        role = user.role or "user"
        display_name = user.display_name or user.username
    else:
        # fallback to admin in env
        if not (settings.ADMIN_USER and settings.ADMIN_PASS):
            raise HTTPException(401, "invalid credentials")
        if not (body.username == settings.ADMIN_USER and body.password == settings.ADMIN_PASS):
            raise HTTPException(401, "invalid credentials")
        uid = "admin"
        role = "admin"
        display_name = "Administrator"

    client_ip = request.client.host if request.client else None
    if user:
        # 마지막 로그인/아이피 저장(있다면)
        repo.update_user_login(user_id=uid, last_ip=client_ip)

    token = _create_access_token(sub=uid, role=role, expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    return {
        "access_token": token,
        "user": {
            "id": uid,
            "username": body.username,
            "role": role,
            "display_name": display_name,
            "last_ip": client_ip,
        }
    }

@router.post("/logout")
def logout():
    # JWT는 stateless. 클라이언트에서 토큰 삭제하면 끝.
    return {"ok": True}

@router.get("/me")
def me(request: Request):
    # 미들웨어로 검증했다면 request.state.user 가 있을 수 있음 (옵션)
    uid = getattr(request.state, "user_id", None)
    role = getattr(request.state, "user_role", None)
    return {"user_id": uid, "role": role, "ip": request.client.host if request.client else None}