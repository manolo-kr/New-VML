# backend/app/ui/app.py

import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# 프런트 API 클라이언트(토큰 주입용)
from app.ui.clients import api_client as api

# ─────────────────────────────────────────────────────────────
# 전역 Store 정의 (세션 스토리지)
# ─────────────────────────────────────────────────────────────
GLOBAL_STORES = [
    # 로그인 상태: {"access_token": "...", "user": {"username": "...", "ip": "..."}}
    dcc.Store(id="gs-auth", storage_type="session"),
    # 현재 프로젝트: {"id": "...", "name": "..."}
    dcc.Store(id="gs-project", storage_type="session"),
    # 디자인/선택 상태 등: {"analysis_id": "...", ...}
    dcc.Store(id="gs-design-state", storage_type="session"),
]

def _navbar():
    """상단 네비게이션 바 (우측에 사용자/아이피/로그아웃)"""
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("Visual ML", href="/"),
            dbc.Nav([
                dbc.NavItem(dcc.Link("Home", className="nav-link", href="/")),
                dbc.NavItem(dcc.Link("Design", className="nav-link", href="/analysis/design")),
                dbc.NavItem(dcc.Link("Train", className="nav-link", href="/analysis/train")),
                dbc.NavItem(dcc.Link("Results", className="nav-link", href="/analysis/results")),
                dbc.NavItem(dcc.Link("Compare", className="nav-link", href="/analysis/compare")),
            ], className="me-auto", navbar=True),

            # 우측: 사용자/아이피 배지 + 로그아웃 링크
            dbc.NavbarText([
                html.Span("User: "), dbc.Badge("-", id="nav-user-badge", color="info", className="me-2"),
                html.Span("IP: "), dbc.Badge("-", id="nav-ip-badge", color="secondary", className="me-3"),
                # FastAPI에 /auth/logout 라우트가 있으므로 단순 링크로 처리(콜백 없음 → 중복 위험 제거)
                html.A("Logout", href="/auth/logout", className="btn btn-outline-light btn-sm"),
            ]),
        ], fluid=True),
        color="dark",
        dark=True,
        sticky="top",
        className="mb-3",
    )


def build_dash_app() -> dash.Dash:
    """Dash 앱 팩토리 (use_pages=True / Navbar / 전역 Store / 인증 동기화 콜백)"""
    app = dash.Dash(
        __name__,
        use_pages=True,
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="Visual ML",
    )

    # 페이지 컨테이너 + 인증용 리디렉션 Location
    app.layout = dbc.Container([
        # 현재 페이지 경로
        dcc.Location(id="_page_location"),

        # 인증 리디렉트 전용 Location (href를 콜백에서 갱신)
        dcc.Location(id="_auth_redirect"),

        # 내부 메시지(디버깅/상태표시용, 화면에 노출 X)
        html.Div(id="_auth_message", style={"display": "none"}),

        *_hide_on_pure_api_clients(GLOBAL_STORES),

        _navbar(),

        # 페이지 컨테이너
        dash.page_container,
    ], fluid=True)

    # ─────────────────────────────────────────────────────────
    # 인증 동기화 콜백
    # - gs-auth가 없으면 /auth/login 으로 1회만 리디렉션
    # - 이미 /auth/login에 있다면 추가 리디렉션 없음(루프 방지)
    # - 토큰을 api_client에 주입하여 이후 모든 API 호출에 Bearer 삽입
    # - 네비게이션 배지(유저/아이피) 렌더
    # ─────────────────────────────────────────────────────────
    @callback(
        Output("_auth_message", "children"),
        Output("_auth_redirect", "href"),
        Output("nav-user-badge", "children"),
        Output("nav-ip-badge", "children"),
        Input("gs-auth", "data"),
        State("_page_location", "pathname"),
        prevent_initial_call=False
    )
    def _sync_auth(gs_auth, pathname):
        token = None
        username = "-"
        ip = "-"

        if isinstance(gs_auth, dict):
            token = gs_auth.get("access_token")
            user = gs_auth.get("user") or {}
            username = user.get("username") or "-"
            ip = user.get("ip") or "-"

        # 프런트 API 클라이언트에 토큰 주입 (없으면 None으로 초기화)
        try:
            api.set_bearer_token(token)
        except Exception:
            pass

        # 인증되지 않았고, 지금 위치가 로그인 페이지가 아니면 로그인으로 이동
        if not token:
            if pathname != "/auth/login":
                # next 파라미터로 현재 경로를 넘겨 로그인 후 원위치
                next_path = pathname or "/"
                return "no-auth", f"/auth/login?next={next_path}", username, ip
            else:
                # 이미 로그인 페이지면 추가 리디렉트 안 함(루프 방지)
                return "no-auth", no_update, username, ip

        # 인증 상태 OK
        return "ok", no_update, username, ip

    return app


def _hide_on_pure_api_clients(stores):
    """
    (옵션) API-only 클라이언트에서 Store 생성이 문제 될 때를 대비한 헬퍼.
    지금은 그대로 반환.
    """
    return stores