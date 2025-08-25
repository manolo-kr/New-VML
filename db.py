# backend/app/db.py

from sqlmodel import SQLModel, create_engine, Session
from .config import PG_DSN

_engine = create_engine(PG_DSN, echo=False, pool_pre_ping=True)

def get_session():
    with Session(_engine) as s:
        yield s

def create_db_and_tables():
    from .models import Project, Analysis, MLTask, User
    SQLModel.metadata.create_all(_engine)