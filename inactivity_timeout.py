# backend/app/middleware/inactivity_timeout.py

# (선택 사항) 서버에서 강제 만료를 때릴 수도 있지만,
# 현재 구성은 클라이언트(Dash) 타이머 + 토큰 만료로 커버하므로 비워둡니다.
# 필요시 요청 타임스탬프를 보고 401로 강제 만료하는 로직을 추가하세요.