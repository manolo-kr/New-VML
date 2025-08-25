# backend/app/ui/app.py

from urllib.parse import urlparse, parse_qs, quote_plus

import os
import requests
import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc


# 전역 Store: 로그인 상태, 현재 프로젝트, 디자인 상태 등
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),          # {"access_token": "...", "user": {..., "ip": "..."}}
    dcc.Store(id="gs-project", storage_type="session"),       # {"id": "...", "name": "..."}
    dcc.Store(id="gs-design-state", storage_type="session"),  # {"analysis_id": "...", ...}
]

def _navbar() -> dbc.Navbar:
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand("Visual ML", href="/", className="fw-semibold"),
                dbc.Nav(
                    [
                        dbc.NavItem(dcc.Link("Home", className="nav-link", href="/")),
                        dbc.NavItem(dcc.Link("Design", className="nav-link", href="/analysis/design")),
                        dbc.NavItem(dcc.Link("Train", className="nav-link", href="/analysis/train")),
                        dbc.NavItem(dcc.Link("Results", className="nav-link", href="/analysis/results")),
                        dbc.NavItem(dcc.Link("Compare", className="nav-link", href="/analysis/compare")),
                    ],
                    navbar=True,
                ),
                html.Div(id="nav-right", className="d-flex align-items-center gap-2"),
            ],
            fluid=True,
        ),
        color="dark",
        dark=True,
        className="mb-3",
    )


def build_dash_app() -> dash.Dash:
    """Dash 앱 팩토리"""
    app = dash.Dash(
        __name__,
        use_pages=True,
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="Visual ML",
    )

    # ✅ 앱 생성 이후에 페이지/로그인 모듈 임포트(이 시점에 register_page 실행)
    from app.ui.auth import login as _login  # noqa: F401
    from app.ui.pages import home as _p_home  # noqa: F401
    from app.ui.pages import analysis_design as _p_design  # noqa: F401
    from app.ui.pages import analysis_train as _p_train  # noqa: F401
    from app.ui.pages import analysis_results as _p_results  # noqa: F401
    from app.ui.pages import analysis_compare as _p_compare  # noqa: F401

    app.layout = dbc.Container(
        [
            # 현재 URL
            dcc.Location(id="_page_location"),
            # 프로그램적 리다이렉트를 위한 Location
            dcc.Location(id="_auth_redirect"),
            # 내부 라우팅용 (필요시)
            dcc.Store(id="_page_store"),

            # 전역 세션 스토어들
            *GLOBAL_STORES,

            _navbar(),
            dash.page_container,
        ],
        fluid=True,
    )

    # ─────────────────────────────────────────────────────────────
    # 전역 네비게이션 가드
    #  - 토큰 없으면 /auth/login?next=<현재경로> 로 이동
    #  - 로그인 상태에서 /auth/login에 있으면 next 로 이동
    # ─────────────────────────────────────────────────────────────
    @callback(
        Output("_auth_redirect", "href"),
        Input("_page_location", "href"),
        Input("gs-auth", "data"),
        State("_auth_redirect", "href"),
        prevent_initial_call=False,
    )
    def _nav_guard(href, auth, current_redirect):
        path = urlparse(href or "/").path or "/"
        is_login_page = path.startswith("/auth/login")
        token = (auth or {}).get("access_token")

        # 로그인 페이지가 아닌데 토큰이 없으면 → 로그인으로
        if not is_login_page and not token:
            target = f"/auth/login?next={quote_plus(path or '/')}"
            return target if (current_redirect or "") != target else no_update

        # 로그인 페이지인데 이미 토큰이 있으면 → next로 이동
        if is_login_page and token:
            qs = parse_qs(urlparse(href or "").query or "")
            next_target = (qs.get("next") or ["/"])[0] or "/"
            if not next_target.startswith("/"):
                next_target = "/"
            return next_target if (current_redirect or "") != next_target else no_update

        return no_update

    # ─────────────────────────────────────────────────────────────
    # 우상단 사용자 영역 렌더 (이름/역할/IP + 연장/로그아웃)
    # ─────────────────────────────────────────────────────────────
    @callback(
        Output("nav-right", "children"),
        Input("gs-auth", "data"),
        prevent_initial_call=False,
    )
    def _render_nav(auth):
        user = (auth or {}).get("user") or {}
        name = user.get("name") or user.get("username") or "-"
        role = (user.get("role") or "user").upper()
        ip = user.get("ip") or "-"

        if not (auth and auth.get("access_token")):
            # 비로그인 상태 → 로그인 링크만 노출
            return dcc.Link("Login", href="/auth/login", className="nav-link text-white")

        return dbc.ButtonGroup(
            [
                dbc.Badge(name, color="light", text_color="dark"),
                dbc.Badge(role, color="info"),
                dbc.Badge(ip, color="secondary"),
                dbc.Button("Extend", id="nav-extend", color="success", outline=True),
                dbc.Button("Logout", id="nav-logout", color="danger", outline=True),
            ],
            size="sm",
            className="ms-2",
        )

    # ─────────────────────────────────────────────────────────────
    # 연장/로그아웃 처리 (gs-auth 갱신 & 리다이렉트)
    #  - gs-auth.data 는 login.py에서도 갱신되므로 allow_duplicate=True 사용
    # ─────────────────────────────────────────────────────────────
    @callback(
        Output("gs-auth", "data", allow_duplicate=True),
        Output("_auth_redirect", "href", allow_duplicate=True),
        Input("nav-extend", "n_clicks"),
        Input("nav-logout", "n_clicks"),
        State("gs-auth", "data"),
        prevent_initial_call=True,
    )
    def _auth_actions(n_ext, n_out, auth):
        trig = dash.ctx.triggered_id
        auth = auth or {}
        API_DIR = os.getenv("API_DIR", "http://127.0.0.1:8065").rstrip("/")
        API_BASE = os.getenv("API_BASE", "/api").rstrip("/")

        if trig == "nav-extend":
            token = auth.get("access_token")
            if not token:
                # 토큰 없으면 로그인으로
                return no_update, "/auth/login?next=/"
            try:
                r = requests.post(
                    f"{API_DIR}{API_BASE}/auth/refresh",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=8,
                )
                if r.status_code == 200:
                    data = r.json()  # {"access_token": "...", "user": {...}}
                    return data, no_update
                # 실패 시 로그인으로
                return no_update, "/auth/login?next=/"
            except Exception:
                return no_update, "/auth/login?next=/"

        if trig == "nav-logout":
            # 세션 클리어 후 로그인으로
            return {}, "/auth/login?next=/"

        return no_update, no_update

    return app