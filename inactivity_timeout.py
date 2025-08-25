# backend/app/middleware/inactivity_timeout.py

from __future__ import annotations

"""
주의: 실제 무활동 감지는 보통 프론트에서 '사용자 활동'을 감지해 토큰을 갱신/만료 처리합니다.
여기 미들웨어는 서버 측에서 별도 동작을 하지 않고, 참고용 주석만 유지합니다.
- 권장: JWT 만료(JWT_EXP_MINUTES) + 프론트에서 마지막 활동시각을 추적해 경고 → 갱신.
"""