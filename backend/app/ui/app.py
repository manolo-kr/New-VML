# backend/app/ui/app.py

from pathlib import Path
import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# 전역 Store: 로그인 상태, 현재 프로젝트, 디자인 상태 등
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),          # {"access_token": "...", "user": {...}}
    dcc.Store(id="gs-project", storage_type="session"),       # {"id": "...", "name": "..."}
    dcc.Store(id="gs-design-state", storage_type="session"),  # {"analysis_id": "...", ...}
]

# pages 디렉토리 경로를 명시적으로 지정 (이 파일 기준 app/ui/pages)
_PAGES_DIR = str((Path(__file__).resolve().parent / "pages").as_posix())

def build_dash_app() -> dash.Dash:
    """Dash 앱 팩토리"""
    app = dash.Dash(
        __name__,
        use_pages=True,
        pages_folder=_PAGES_DIR,              # ✅ 명시적으로 지정
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="Visual ML",
    )

    # 로그인 페이지는 pages 폴더 밖(app/ui/auth)에 있으므로, 앱 생성 "후" import하여 register_page 실행
    from app.ui.auth import login as _login  # noqa: F401

    navbar = dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.NavbarBrand("Visual ML", className="me-3"),
                href="/",
                className="navbar-brand-link",
            ),
            dbc.Nav(
                [
                    dbc.NavItem(dcc.Link("Home", href="/", className="nav-link")),
                    dbc.NavItem(dcc.Link("Design", href="/analysis/design", className="nav-link")),
                    dbc.NavItem(dcc.Link("Train", href="/analysis/train", className="nav-link")),
                    dbc.NavItem(dcc.Link("Results", href="/analysis/results", className="nav-link")),
                    dbc.NavItem(dcc.Link("Compare", href="/analysis/compare", className="nav-link")),
                ],
                className="me-auto",
                navbar=True,
            ),
            # 우측: 사용자/아이피/로그아웃/연장
            dbc.Nav(
                [
                    html.Span(id="nav-user-badge", className="me-2"),
                    html.Span(id="nav-ip-badge", className="me-2"),
                    dbc.Button("Extend 10 min", id="nav-extend", size="sm", color="secondary", className="me-2"),
                    dbc.Button("Logout", id="nav-logout", size="sm", color="danger", outline=True),
                ],
                navbar=True,
            ),
        ]),
        color="dark",
        dark=True,
        className="mb-3",
    )

    app.layout = dbc.Container([
        dcc.Location(id="_page_location"),
        dcc.Store(id="_page_store"),
        *GLOBAL_STORES,

        navbar,

        # 로그인/리디렉트/토큰 동기화용 보조 컴포넌트
        dcc.Location(id="_auth_redirect"),
        dcc.Interval(id="_auth_heartbeat", interval=60_000, disabled=False),  # 60초마다 토큰 체크/연장 신호에 사용 가능
        html.Div(id="_auth_message", style={"display": "none"}),

        dash.page_container
    ], fluid=True)

    # -----------------------------
    # 공통 콜백들
    # -----------------------------
    from app.ui.clients import api_client as api

    # 1) gs-auth 변경 → api_client에 토큰 주입 + 우측 뱃지 렌더 + (미로그인 시 /auth/login 리디렉트)
    @callback(
        Output("_auth_message", "children"),
        Output("_auth_redirect", "href"),
        Output("nav-user-badge", "children"),
        Output("nav-ip-badge", "children"),
        Input("gs-auth", "data"),
        State("_page_location", "href"),
        prevent_initial_call=False
    )
    def _sync_auth(gs_auth, href):
        token = None
        username = "-"
        ip = "-"

        if gs_auth and isinstance(gs_auth, dict):
            token = gs_auth.get("access_token")
            user = gs_auth.get("user") or {}
            username = user.get("username") or "-"
            ip = user.get("ip") or "-"

        # api_client 에 토큰 주입
        try:
            api.set_bearer_token(token)
        except Exception:
            pass

        # 표시용 뱃지
        user_badge = dbc.Badge(username, color="info")
        ip_badge = dbc.Badge(ip, color="secondary")

        # 미로그인 → 로그인 페이지로
        if not token:
            # next 파라미터로 현재 위치 전달
            next_href = "/"
            if href:
                next_href = href
            return "no-auth", f"/auth/login?next={next_href}", user_badge, ip_badge

        # 로그인 상태 유지
        return "ok", dash.no_update, user_badge, ip_badge

    # 2) Logout 버튼 → gs-auth 초기화(=미로그인 상태로 전환되어 위 콜백이 /auth/login으로 보냄)
    @callback(
        Output("gs-auth", "data", allow_duplicate=True),
        Input("nav-logout", "n_clicks"),
        prevent_initial_call=True
    )
    def _logout(n):
        if not n:
            return no_update
        return None

    # 3) Extend 버튼(10분 연장 UI 신호만) — 실제 토큰 refresh는 필요시 별도 구현
    @callback(
        Output("_auth_message", "children", allow_duplicate=True),
        Input("nav-extend", "n_clicks"),
        prevent_initial_call=True
    )
    def _extend(n):
        if not n:
            return no_update
        return "extend"

    return app