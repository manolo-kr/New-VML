# backend/app/ui/app.py

import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# 전역 Store: 로그인 상태, 현재 프로젝트, 디자인 상태 등
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),         # {"access_token": "...", "user": {...}, "ip":"..."}
    dcc.Store(id="gs-project", storage_type="session"),      # {"id": "...", "name": "..."}
    dcc.Store(id="gs-design-state", storage_type="session"), # {"analysis_id": "...", ...}
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
            dcc.Location(id="_router"),              # 현재 URL
            dcc.Location(id="_auth_redirect"),       # 가드 리다이렉트 전용
            dcc.Location(id="_logout_redirect"),     # 로그아웃 리다이렉트 전용(중복 방지)
            html.Div(id="_guard_msg", style={"display": "none"}),

            # 전역 상태
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

                    # 우측 사용자/아이피 뱃지 + 연장/로그아웃
                    html.Div(id="_navbar_user_badges", className="d-flex align-items-center me-2"),
                    dbc.Button("Extend 10m", id="_btn_extend", color="warning", size="sm", class_name="me-2"),
                    dbc.Button("Logout", id="_btn_logout", color="light", size="sm"),
                ],
                color="dark",
                dark=True,
                class_name="mb-3 rounded",
            ),

            # 연장 성공 토스트
            dbc.Toast(
                "Session extended by 10 minutes.",
                id="_extend_toast",
                header="OK",
                is_open=False,
                dismissable=True,
                icon="primary",
                duration=2500,
                style={"position": "fixed", "top": 80, "right": 20, "zIndex": 1080},
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
        if pathname and pathname.startswith("/auth/login"):
            return no_update, "on login page"
        has_token = bool(auth and auth.get("access_token"))
        if not has_token:
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
    # 클라이언트 로그아웃 (중복 방지: _logout_redirect 사용)
    # -------------------------------
    @callback(
        Output("gs-auth", "data"),
        Output("_logout_redirect", "href"),
        Input("_btn_logout", "n_clicks"),
        prevent_initial_call=True,
    )
    def _logout(n):
        if not n:
            return no_update, no_update
        return {}, "/auth/login?logged_out=1"

    # -------------------------------
    # 세션 연장 (10분): /auth/refresh 호출 → 토큰 갱신
    # -------------------------------
    @callback(
        Output("gs-auth", "data"),
        Output("_extend_toast", "is_open"),
        Input("_btn_extend", "n_clicks"),
        State("gs-auth", "data"),
        prevent_initial_call=True,
    )
    def _extend(n, auth):
        if not n:
            return no_update, no_update
        if not auth or not auth.get("access_token"):
            # 미로그인 상태면 아무 처리 없음
            return no_update, False
        try:
            # api_client.refresh()는 새 access_token 및 exp 갱신값을 돌려준다고 가정
            from app.ui.clients import api_client as api
            res = api.refresh(auth.get("access_token"))
            new_auth = {
                "access_token": res.get("access_token") or auth.get("access_token"),
                "user": auth.get("user"),
                "ip": auth.get("ip"),
            }
            return new_auth, True
        except Exception:
            # 실패 시 토스트는 띄우지 않음
            return no_update, False

    return app