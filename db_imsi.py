# backend/app/db.py (요지)

import os
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://ml:ml@127.0.0.1:5432/vml?sslmode=disable")

# 디버그용: 비밀번호 마스킹 로그
def _mask_dsn(url: str) -> str:
    # postgresql+psycopg2://user:pass@host:port/db?... -> pass 마스킹
    try:
        import re
        return re.sub(r":([^:@/]+)@", r":***@", url)
    except Exception:
        return url

print(f"[DB] Connecting to: {_mask_dsn(DATABASE_URL)}")

_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},  # 연결 지연 시 빠르게 실패
    echo=False,
)

def get_session():
    with Session(_engine) as s:
        yield s

def create_db_and_tables():
    SQLModel.metadata.create_all(_engine)