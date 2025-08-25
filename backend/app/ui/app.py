# backend/app/ui/app.py

import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# 전역 Store: 로그인/프로젝트/디자인 상태
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),
    dcc.Store(id="gs-project", storage_type="session"),
    dcc.Store(id="gs-design-state", storage_type="session"),
]

def _navbar():
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("Visual ML", href="/"),
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
            # 우측: 사용자 / IP / 로그아웃
            html.Div(
                [
                    html.Span(id="nav-user-badge", className="me-2"),
                    html.Span(id="nav-ip-badge", className="me-2"),
                    dbc.Button("Logout", id="btn-logout", size="sm", color="secondary", outline=True, className="ms-2"),
                ],
                className="d-flex align-items-center",
            ),
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-3",
    )

def build_dash_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        use_pages=True,
        # ✅ None 금지. 문자열 경로로 비활성화(실제 폴더가 없어도 됨)
        pages_folder="__no_auto_pages__",
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="Visual ML",
    )

    # 여기서 수동 임포트로 등록 (중복 방지)
    from app.ui.auth import login as _login       # noqa: F401
    from app.ui.pages import home as _home        # noqa: F401
    from app.ui.pages import analysis_design as _design     # noqa: F401
    from app.ui.pages import analysis_train as _train       # noqa: F401
    from app.ui.pages import analysis_results as _results   # noqa: F401
    from app.ui.pages import analysis_compare as _compare   # noqa: F401

    app.layout = dbc.Container([
        dcc.Location(id="_url"),
        dcc.Location(id="_guard_redirect", refresh=True),
        # auth 콜백 체인에서만 쓰는 더미 sink (출력 충돌 방지용)
        dcc.Location(id="_auth_redirect_sink"),

        *GLOBAL_STORES,
        _navbar(),
        dash.page_container,
    ], fluid=True)

    # 1) 인증 가드
    @callback(
        Output("_guard_redirect", "href"),
        Input("_url", "pathname"),
        State("gs-auth", "data"),
        prevent_initial_call=False,
    )
    def _guard(pathname, gs_auth):
        path = pathname or "/"
        # 로그인 페이지는 가드 예외
        if path.startswith("/auth/login"):
            return no_update
        token = (gs_auth or {}).get("access_token")
        if not token:
            # 로그인으로 리다이렉트
            return f"/auth/login?next={path}"
        return no_update

    # 2) 네비바 뱃지
    @callback(
        Output("nav-user-badge", "children"),
        Output("nav-ip-badge", "children"),
        Input("gs-auth", "data"),
        prevent_initial_call=False,
    )
    def _nav_badges(gs_auth):
        user = (gs_auth or {}).get("user") or {}
        name = user.get("display_name") or user.get("username") or "-"
        ip = user.get("last_ip") or "-"
        return (
            dbc.Badge(f"User: {name}", color="info", class_name="me-1"),
            dbc.Badge(f"IP: {ip}", color="secondary"),
        )

    # 3) 로그아웃 → gs-auth 초기화 (가드가 자동으로 로그인으로 보냄)
    @callback(
        Output("gs-auth", "data"),
        Input("btn-logout", "n_clicks"),
        prevent_initial_call=True,
    )
    def _logout(_n):
        return None

    return app