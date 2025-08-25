# backend/app/ui/app.py

import json
import time
from typing import Optional

import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# 전역 Store: 로그인 상태, 현재 프로젝트, 디자인 상태 등
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),         # {"access_token","user","client_ip","exp"}
    dcc.Store(id="gs-project", storage_type="session"),      # {"id","name"}
    dcc.Store(id="gs-design-state", storage_type="session"), # {"analysis_id", ...}
]

PROTECTED_PREFIXES = ("/", "/analysis")  # 홈/Design/Train/Results/Compare 모두 보호
PUBLIC_PATHS = ("/login",)

def _nav_user_badge():
    return html.Div(
        id="nav-user-box",
        children=[
            html.Small(id="nav-user-email", className="me-2 text-muted"),
            html.Small(id="nav-user-ip", className="me-3 text-muted"),
            dbc.Button("Extend +10m", id="nav-extend", size="sm", color="secondary", outline=True, className="me-2"),
            dbc.Button("Logout", id="nav-logout", size="sm", color="danger", outline=True),
        ],
        className="d-flex align-items-center",
        style={"gap": "0.5rem"},
    )

def build_dash_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        use_pages=True,
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="Visual ML",
    )

    app.layout = dbc.Container([
        dcc.Location(id="_page_location"),
        dcc.Location(id="_auth_redirect"),  # guard 리다이렉트 전용
        dcc.Interval(id="_auth_tick", interval=30_000, n_intervals=0),  # 30초마다 만료 확인
        dcc.Store(id="_auth_banner"),  # 만료 임박 등 배너 표시용
        *GLOBAL_STORES,

        dbc.Navbar(
            dbc.Container([
                dbc.NavbarBrand("Visual ML", href="/"),
                dbc.Nav(
                    [
                        dbc.NavItem(dcc.Link("Home", href="/", className="nav-link")),
                        dbc.NavItem(dcc.Link("Design", href="/analysis/design", className="nav-link")),
                        dbc.NavItem(dcc.Link("Train", href="/analysis/train", className="nav-link")),
                        dbc.NavItem(dcc.Link("Results", href="/analysis/results", className="nav-link")),
                        dbc.NavItem(dcc.Link("Compare", href="/analysis/compare", className="nav-link")),
                    ],
                    className="me-auto", navbar=True
                ),
                _nav_user_badge(),
            ]),
            color="dark", dark=True, className="mb-3"
        ),

        html.Div(id="_auth_message"),
        dash.page_container
    ], fluid=True)

    return app


# --------------------------
# Guard: 로그인 요구/리다이렉트
# --------------------------
@callback(
    Output("_auth_redirect", "href"),
    Output("_auth_message", "children"),
    Input("_page_location", "pathname"),
    State("gs-auth", "data"),
    prevent_initial_call=False
)
def _guard(pathname: str, auth):
    if not pathname:
        return no_update, no_update

    # public은 통과
    if any(pathname.startswith(p) for p in PUBLIC_PATHS):
        return no_update, no_update

    # 보호 경로 & 미로그인 → 로그인으로
    need_protect = any(pathname.startswith(p) for p in PROTECTED_PREFIXES)
    if need_protect and not (auth and auth.get("access_token")):
        return "/login", dbc.Alert("Please login to continue.", color="warning", className="py-2")
    return no_update, no_update


# --------------------------
# Navbar 사용자/IP 표시
# --------------------------
@callback(
    Output("nav-user-email", "children"),
    Output("nav-user-ip", "children"),
    Input("gs-auth", "data"),
)
def _nav_user(auth):
    if not auth or not auth.get("access_token"):
        return "", ""
    email = (auth.get("user") or {}).get("email", "")
    ip = auth.get("client_ip") or "-"
    return f"{email}", f"@ {ip}"


# --------------------------
# Logout
# --------------------------
@callback(
    Output("gs-auth", "data"),
    Output("_auth_redirect", "href"),
    Input("nav-logout", "n_clicks"),
    prevent_initial_call=True
)
def _logout(_n):
    return None, "/login"


# --------------------------
# Extend(Refresh) — 토큰 연장
# --------------------------
@callback(
    Output("gs-auth", "data"),
    Input("nav-extend", "n_clicks"),
    State("gs-auth", "data"),
    prevent_initial_call=True
)
def _extend(_n, auth):
    if not auth or not auth.get("access_token"):
        return no_update
    # 클라이언트 측 API 클라이언트 호출이 아니라, 페이지 콜백마다 refresh 호출은 부담이므로
    # 간단히 Fetch API를 쓰는 대신 서버측 요청 도우미를 써도 됨.
    # 여기서는 페이지 콜백에서 직접 refresh를 호출하지 않고,
    # 결과 auth 저장은 login 페이지 콜백 패턴을 그대로 사용하도록 구성할 수도 있음.
    # 👉 간단화를 위해, 이 콜백은 "프런트에서 /auth/refresh를 AJAX로 부르는 구현"을 권장.
    # 다만 현재 Dash 서버 콜백에서는 requests를 이용해도 됨:
    import os, requests
    API_DIR = os.getenv("API_DIR", "http://127.0.0.1:8065")
    r = requests.post(f"{API_DIR}/api/auth/refresh", headers={
        "Authorization": f"Bearer {auth['access_token']}"
    }, timeout=10)
    if r.status_code == 200:
        data = r.json()
        return {
            "access_token": data["access_token"],
            "user": data["user"],
            "client_ip": data.get("client_ip"),
            "exp": data.get("exp"),
        }
    return no_update


# --------------------------
# 토큰 만료 감지: 30초마다 체크
# --------------------------
@callback(
    Output("_auth_message", "children"),
    Output("_auth_redirect", "href"),
    Input("_auth_tick", "n_intervals"),
    State("gs-auth", "data"),
)
def _check_exp(_n, auth):
    if not auth or not auth.get("exp"):
        return no_update, no_update
    now = int(time.time())
    # 만료
    if now >= int(auth["exp"]):
        # 세션 만료 알림 & 로그인 리다이렉트 유도
        msg = dbc.Alert("Session expired. Please login again.", color="danger", className="py-2")
        return msg, "/login"
    # 만료 임박 (1분 이내) → 메시지
    if int(auth["exp"]) - now <= 60:
        msg = dbc.Alert("Session will expire soon. Click 'Extend +10m' to continue.", color="warning", className="py-2")
        return msg, no_update
    return no_update, no_update