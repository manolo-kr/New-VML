# backend/app/db.py

from __future__ import annotations
from sqlmodel import SQLModel, Session, create_engine
from app.config import settings

_engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
    echo=False,
)

def get_session():
    with Session(_engine) as s:
        yield s

def create_db_and_tables():
    SQLModel.metadata.create_all(_engine)
