# backend/app/ui/auth/guard.py

from __future__ import annotations
from dash import html, dcc
import dash_bootstrap_components as dbc

def require_auth(children, message: str = "Login required."):
    """
    페이지 상단에 붙여서 gs-auth 가 비어 있을 때 로그인 페이지 안내를 보여주는 가드 스텁.
    (완전한 리디렉트 콜백을 두기보다, 페이지 당 include 방식으로 간단히 사용)
    사용 예:
        layout = dbc.Container([
            require_auth(dash.page_container),
        ], fluid=True)
    """
    return html.Div([
        dcc.Store(id="gs-auth", storage_type="session"),
        html.Div(id="__guard_panel"),
        html.Div(children=children, id="__guard_content")
    ])

# 참고:
#  - 완전 자동 리디렉트가 필요하면, 각 페이지에서 gs-auth를 읽어 href를 /auth/login 으로 바꾸는
#    경량 콜백을 추가하세요. (현재 프로젝트에서는 서버측 JWT 만료로 401이 나면
#    프론트가 다시 로그인 유도 토스트를 띄우는 UX를 권장)