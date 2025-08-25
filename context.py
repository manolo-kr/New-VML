# backend/app/services/context.py

from __future__ import annotations
from typing import Optional

def get_user_id_from_request_state(state) -> Optional[str]:
    # 내부 허용 모드: 사용자 구분 안함
    return None