# backend/app/ui/app.py

import os
import requests
import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# 전역 Store: 인증, 프로젝트, 디자인 상태, 로그인 인박스(로그인 페이지 → 허브 전달 전용)
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),          # {"access_token","user","client_ip","exp"}
    dcc.Store(id="gs-project", storage_type="session"),       # {"id","name"} (선택)
    dcc.Store(id="gs-design-state", storage_type="session"),  # 디자인 페이지 임시 상태 (선택)
    dcc.Store(id="gs-auth-inbox", storage_type="session"),    # login.py가 여기에만 씀 → 허브가 소비
]

API_DIR = os.getenv("API_DIR", "http://127.0.0.1:8065").rstrip("/")
API_BASE = os.getenv("API_BASE", "/api")

def build_dash_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        use_pages=True,
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="Visual ML",
    )

    app.layout = dbc.Container([
        # 전역 라우팅 및 메시지/리다이렉트 앵커
        dcc.Location(id="_page_location"),
        dcc.Location(id="auth-redirect"),

        # 전역 보관
        *GLOBAL_STORES,

        # 상단 네비게이션 바
        dbc.Navbar(
            [
                dbc.NavbarBrand("Visual ML", href="/"),
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Home", href="/")),
                        dbc.NavItem(dbc.NavLink("Design", href="/analysis/design")),
                        dbc.NavItem(dbc.NavLink("Train", href="/analysis/train")),
                        dbc.NavItem(dbc.NavLink("Results", href="/analysis/results")),
                        dbc.NavItem(dbc.NavLink("Compare", href="/analysis/compare")),
                    ],
                    className="me-auto",
                    navbar=True,
                ),
                dbc.Nav(
                    [
                        # 사용자/IP 뱃지
                        html.Div(id="navbar-user", className="me-2 small text-muted"),
                        # 세션 연장 / 로그아웃
                        dbc.Button("Extend 10m", id="btn-extend-session", color="secondary", size="sm", outline=True, className="me-1"),
                        dbc.Button("Logout", id="btn-logout", color="danger", size="sm"),
                    ],
                    navbar=True,
                )
            ],
            color="dark",
            dark=True,
            className="mb-3"
        ),

        # 전역 인증/안내 메시지 출력용
        html.Div(id="auth-message", className="mb-2"),

        dash.page_container,
    ], fluid=True)

    return app


# ─────────────────────────────────────────────────────────
# Auth Hub
#   - 전역 인증 상태를 ‘오직 이 콜백’만 갱신(= gs-auth.data 단일 작성자)
#   - login.py → gs-auth-inbox.data 로 들어온 토큰을 수리/반영
#   - 연장/로그아웃도 여기에서 처리 → 메시지/리다이렉트도 여기서만 출력
# ─────────────────────────────────────────────────────────
@callback(
    Output("gs-auth", "data"),
    Output("auth-message", "children"),
    Output("auth-redirect", "href"),
    Output("navbar-user", "children"),
    Input("gs-auth-inbox", "data"),
    Input("btn-extend-session", "n_clicks"),
    Input("btn-logout", "n_clicks"),
    State("gs-auth", "data"),
    prevent_initial_call=True,
)
def _auth_hub(inbox, n_extend, n_logout, current):
    trig = dash.ctx.triggered_id
    auth = current or {}
    msg = no_update
    href = no_update

    # 1) 로그인 페이지가 전달한 신규 인증 (gs-auth-inbox)
    if trig == "gs-auth-inbox" and inbox and inbox.get("access_token"):
        auth = {
            "access_token": inbox.get("access_token"),
            "user": inbox.get("user"),
            "client_ip": inbox.get("client_ip"),
            "exp": inbox.get("exp"),
        }
        msg = dbc.Alert("Login success.", color="success", className="py-2")
        href = "/"

    # 2) 세션 연장 (서버 토큰 갱신 호출 권장)
    elif trig == "btn-extend-session":
        if not auth or not auth.get("access_token"):
            msg = dbc.Alert("Not logged in.", color="warning", className="py-2")
        else:
            try:
                r = requests.post(f"{API_DIR}{API_BASE}/auth/refresh",
                                  headers={"Authorization": f"Bearer {auth['access_token']}"},
                                  timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    auth = {
                        "access_token": data["access_token"],
                        "user": data.get("user") or auth.get("user"),
                        "client_ip": data.get("client_ip") or auth.get("client_ip"),
                        "exp": data.get("exp"),
                    }
                    msg = dbc.Alert("Session extended.", color="info", className="py-2")
                else:
                    msg = dbc.Alert(f"Extend failed: {r.text}", color="danger", className="py-2")
            except Exception as e:
                msg = dbc.Alert(f"Extend error: {e}", color="danger", className="py-2")

    # 3) 로그아웃
    elif trig == "btn-logout":
        auth = {}
        msg = dbc.Alert("Logged out.", color="secondary", className="py-2")
        href = "/login"

    # 우측 상단 사용자/아이피 표기
    if auth and auth.get("user"):
        u = auth["user"]
        email = u.get("email") or "-"
        role = u.get("role") or "user"
        ip = auth.get("client_ip") or "-"
        navbar = html.Span([f"{email} ({role}) — IP: {ip}"])
    else:
        navbar = html.Span("Anonymous — IP: -")

    return auth or {}, msg, href, navbar