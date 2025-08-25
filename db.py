# backend/app/db.py

from __future__ import annotations

from sqlmodel import SQLModel, create_engine, Session

from .config import DB_URL

_engine = create_engine(DB_URL, echo=False, pool_pre_ping=True)


def get_session() -> Session:
    with Session(_engine) as s:
        yield s


def create_db_and_tables() -> None:
    from . import models  # ensure models are imported
    SQLModel.metadata.create_all(_engine)