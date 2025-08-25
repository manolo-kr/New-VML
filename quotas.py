# backend/app/services/quotas.py

from __future__ import annotations
from typing import Optional

# 내부 허용 모드: 항상 허용
def can_enqueue_for_user(user_id: Optional[str], current_active: int, user_limit: int) -> bool:
    return True

def can_worker_start_job(current_running: int, max_parallel: int) -> bool:
    return current_running < max_parallel