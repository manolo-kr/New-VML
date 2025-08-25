# backend/app/auth/router_auth.py

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from ..db import get_session
from ..store_sql import Repo
from ..services.auth_utils import verify_password, create_access_token

router = APIRouter()


@router.post("/login")
def login(body: dict, s: Session = Depends(get_session)):
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    if not email or not password:
        raise HTTPException(400, "email and password required")

    repo = Repo(s)
    user = repo.get_user_by_email(email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(401, "invalid credentials")

    token = create_access_token(
        user.id,
        extra_claims={"email": user.email, "name": user.name, "role": user.role},
    )
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}}


@router.get("/me")
def me(request: Request):
    u = getattr(request.state, "user", None)
    if not u:
        raise HTTPException(401, "unauthorized")
    return u