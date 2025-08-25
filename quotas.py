# backend/app/services/quotas.py

from __future__ import annotations
from typing import Optional
from app.config import settings
from app.queue_mongo import _jobs


def count_running_jobs(user_id: Optional[str] = None) -> int:
    q = {"status": {"$in": ["queued", "running"]}}
    if user_id:
        q["user_id"] = user_id
    return _jobs.count_documents(q)


def can_enqueue(user_id: Optional[str]) -> bool:
    # 글로벌
    if count_running_jobs(None) >= settings.GLOBAL_MAX_RUNNING:
        return False
    # 유저별
    if user_id and count_running_jobs(user_id) >= settings.USER_MAX_CONCURRENT:
        return False
    return True