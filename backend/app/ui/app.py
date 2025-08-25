# backend/app/ui/app.py

import re
from urllib.parse import urlparse, parse_qs, quote_plus

import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# ✅ 로그인 페이지를 Dash에 등록시키기 위해 반드시 import!
#    (use_pages=True는 pages 패키지만 자동 스캔하므로 auth/login은 직접 import 필요)
from app.ui.auth import login as _login  # noqa: F401  (side-effect로 /auth/login 등록)

# 전역 Store: 로그인 상태, 현재 프로젝트, 디자인 상태 등
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),         # {"access_token": "...", "user": {...}}
    dcc.Store(id="gs-project", storage_type="session"),      # {"id": "...", "name": "..."}
    dcc.Store(id="gs-design-state", storage_type="session"), # {"analysis_id": "...", ...}
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
                # 우측 비어있어도 레이아웃 안정
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

    app.layout = dbc.Container(
        [
            # 현재 URL
            dcc.Location(id="_page_location"),
            # 프로그램적 리다이렉트를 위한 Location (href 세팅 시 페이지 이동)
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
    #  - 무한루프 방지: 현재 리다이렉트 대상과 동일하면 no_update
    # ─────────────────────────────────────────────────────────────
    @callback(
        Output("_auth_redirect", "href"),
        Input("_page_location", "href"),
        Input("gs-auth", "data"),
        State("_auth_redirect", "href"),
        prevent_initial_call=False,
    )
    def _nav_router(href, auth, current_redirect):
        # 현재 경로
        path = urlparse(href or "/").path or "/"

        # 로그인 페이지 여부
        is_login_page = path.startswith("/auth/login")

        # 로그인 토큰
        token = (auth or {}).get("access_token")

        # 로그인 페이지가 아닌데 토큰이 없으면 → 로그인으로
        if not is_login_page and not token:
            target = f"/auth/login?next={quote_plus(path or '/')}"
            if (current_redirect or "") != target:
                return target
            return no_update

        # 로그인 페이지인데 이미 토큰이 있으면 → next로 이동
        if is_login_page and token:
            qs = parse_qs(urlparse(href or "").query or "")
            next_target = (qs.get("next") or ["/"])[0] or "/"
            # 방어적: next에 /로 시작하지 않으면 루트로
            if not next_target.startswith("/"):
                next_target = "/"
            if (current_redirect or "") != next_target:
                return next_target
            return no_update

        # 그 외에는 아무 것도 하지 않음
        return no_update

    return app