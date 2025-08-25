# backend/app/auth/router_auth.py

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.db import get_session
from app.store_sql import Repo
from app.services.auth_utils import verify_password, create_access_token
from app.auth.schemas import LoginRequest, TokenResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, s: Session = Depends(get_session)):
    repo = Repo(s)
    user = repo.get_user_by_email(body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role}
    )
    return TokenResponse(access_token=token, user={"id": user.id, "email": user.email, "name": user.name, "role": user.role})