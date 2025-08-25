# backend/app/services/quotas.py

from __future__ import annotations
from typing import Optional
from .config import (
    USER_MAX_CONCURRENT, USER_MAX_QUEUED,
    GLOBAL_MAX_CONCURRENT, GLOBAL_MAX_QUEUED
)

def can_enqueue(user_id: Optional[str]) -> bool:
    """
    현재는 하드 제한만 스텁. (실사용은 Mongo 상태 카운팅으로 보완)
    """
    return True