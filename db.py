# backend/app/db.py

from __future__ import annotations
from sqlmodel import SQLModel, create_engine, Session
from .config import DATABASE_URL

_engine = create_engine(DATABASE_URL, echo=False, future=True)

def get_session() -> Session:
    with Session(_engine) as s:
        yield s

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(_engine)