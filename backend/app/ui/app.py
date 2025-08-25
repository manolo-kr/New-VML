# backend/app/ui/app.py
import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# 전역 Store: 로그인 상태, 현재 프로젝트, 디자인 상태 등
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),         # {"access_token": "...", "user": {...}, "ip":"..."}
    dcc.Store(id="gs-project", storage_type="session"),      # {"id": "...", "name": "..."}
    dcc.Store(id="gs-design-state", storage_type="session"), # {"analysis_id": "...", "dataset_uri": "...", ...}
]

def _user_badge(user_data: dict | None) -> html.Div:
    if not user_data:
        return html.Div()
    name = (user_data.get("user") or {}).get("username") or "user"
    ip   = user_data.get("ip") or "-"
    return html.Div(
        [
            dbc.Badge(name, color="primary", className="me-2"),
            dbc.Badge(f"IP {ip}", color="secondary")
        ],
        className="me-3"
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
            # 라우팅/리다이렉트용
            dcc.Location(id="_router"),                 # 현재 URL
            dcc.Location(id="_auth_redirect"),         # 가드가 쓰는 강제 리다이렉트 대상
            html.Div(id="_guard_msg", style={"display": "none"}),  # 디버그 메시지 영역(숨김)

            # 전역 상태 (세션 보존)
            *GLOBAL_STORES,

            # 네비게이션 바
            dbc.Navbar(
                [
                    dbc.NavbarBrand("Visual ML", href="/", class_name="fw-bold"),
                    dbc.Nav(
                        [
                            dbc.NavItem(dcc.Link("Home",    href="/",                 className="nav-link")),
                            dbc.NavItem(dcc.Link("Design",  href="/analysis/design",  className="nav-link")),
                            dbc.NavItem(dcc.Link("Train",   href="/analysis/train",   className="nav-link")),
                            dbc.NavItem(dcc.Link("Results", href="/analysis/results", className="nav-link")),
                            dbc.NavItem(dcc.Link("Compare", href="/analysis/compare", className="nav-link")),
                        ],
                        class_name="me-auto",
                        navbar=True,
                    ),

                    # 우측 사용자/로그아웃
                    html.Div(id="_navbar_user_badges", className="d-flex align-items-center me-2"),
                    dbc.Button("Logout", id="_btn_logout", color="light", size="sm"),
                ],
                color="dark",
                dark=True,
                class_name="mb-3 rounded",
            ),

            # 페이지 컨테이너
            dash.page_container,
        ],
        fluid=True,
    )

    # -------------------------------
    # 전역 가드: 로그인 안했으면 /auth/login 로 보냄
    # -------------------------------
    @callback(
        Output("_auth_redirect", "href"),
        Output("_guard_msg", "children"),
        Input("_router", "pathname"),
        State("gs-auth", "data"),
        prevent_initial_call=False,
    )
    def _guard(pathname, auth):
        # 로그인 페이지 자체는 열어둠
        if pathname and pathname.startswith("/auth/login"):
            # 이미 로그인 한 상태면 홈으로(혹은 next 파라미터가 있다면 그곳으로) 보내도 됨
            return no_update, "on login page"
        # 인증 필요: 토큰 없으면 로그인으로 리다이렉트
        has_token = bool(auth and auth.get("access_token"))
        if not has_token:
            # 다음에 돌아올 경로 next= 로 전달
            target = f"/auth/login?next={pathname or '/'}"
            return target, "redirected to login"
        return no_update, "guard ok"

    # -------------------------------
    # 우측 상단 사용자/아이피 뱃지 렌더
    # -------------------------------
    @callback(
        Output("_navbar_user_badges", "children"),
        Input("gs-auth", "data"),
        prevent_initial_call=False,
    )
    def _navbar_user(auth):
        return _user_badge(auth)

    # -------------------------------
    # 클라이언트 로그아웃: 토큰 삭제 후 로그인으로
    # -------------------------------
    @callback(
        Output("gs-auth", "data"),
        Output("_auth_redirect", "href"),
        Input("_btn_logout", "n_clicks"),
        prevent_initial_call=True,
    )
    def _logout(n):
        if not n:
            return no_update, no_update
        # 세션 토큰 클리어 → 로그인 페이지
        return {}, "/auth/login?logged_out=1"

    return app