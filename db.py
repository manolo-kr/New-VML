# backend/app/db.py

from sqlmodel import SQLModel, create_engine, Session
from .config import DATABASE_URL

_engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)

def get_engine():
    return _engine

def get_session():
    with Session(_engine) as session:
        yield session

def create_db_and_tables():
    from . import models  # ensure models imported
    SQLModel.metadata.create_all(_engine)