# backend/app/services/quotas.py

from __future__ import annotations
from typing import Dict, Any

from app.config import settings
from app.queue_mongo import count_active_jobs_global, count_active_jobs_by_user

def can_enqueue(user_id: str) -> Dict[str, Any]:
    now_global = count_active_jobs_global()
    now_user = count_active_jobs_by_user(user_id)

    reasons = []
    if now_global >= settings.MAX_ACTIVE_RUNS_GLOBAL:
        reasons.append(f"global active runs limit reached ({now_global}/{settings.MAX_ACTIVE_RUNS_GLOBAL})")
    if now_user >= settings.MAX_ACTIVE_RUNS_PER_USER:
        reasons.append(f"user active runs limit reached ({now_user}/{settings.MAX_ACTIVE_RUNS_PER_USER})")

    return {
        "ok": len(reasons) == 0,
        "reasons": reasons,
        "global_active": now_global,
        "user_active": now_user,
        "reserved_cpus": settings.RESERVED_CPUS,
    }