# backend/app/services/quotas.py

from __future__ import annotations

from typing import Optional

from pymongo.collection import Collection

from ..config import GLOBAL_MAX_CONCURRENT, USER_MAX_CONCURRENT
from ..queue_mongo import _jobs

ACTIVE_STATUSES = ["queued", "running"]


def _count_active(coll: Collection, query: dict) -> int:
    return coll.count_documents(query)


def count_active_jobs_global() -> int:
    return _count_active(_jobs, {"status": {"$in": ACTIVE_STATUSES}})


def count_active_jobs_for_user(user_id: Optional[str]) -> int:
    if not user_id:
        return 0
    return _count_active(_jobs, {"status": {"$in": ACTIVE_STATUSES}, "user_id": user_id})


def can_enqueue(user_id: Optional[str]) -> tuple[bool, str]:
    g = count_active_jobs_global()
    if g >= GLOBAL_MAX_CONCURRENT:
        return False, f"Global concurrency limit reached ({g}/{GLOBAL_MAX_CONCURRENT})."

    u = count_active_jobs_for_user(user_id)
    if u >= USER_MAX_CONCURRENT:
        return False, f"User concurrency limit reached ({u}/{USER_MAX_CONCURRENT})."

    return True, "ok"