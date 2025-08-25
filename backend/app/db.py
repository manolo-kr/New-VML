# backend/app/db.py

from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

_engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(_engine)

def get_session():
    with Session(_engine) as s:
        yield s