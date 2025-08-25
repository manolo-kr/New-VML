# backend/app/ui/app.py

import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# 전역 Store: 로그인/프로젝트/디자인 상태 (세션 스토리지)
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),         # {"access_token":"...", "user": {..., "ip":"..."}}
    dcc.Store(id="gs-project", storage_type="session"),
    dcc.Store(id="gs-design-state", storage_type="session"),
]

def _user_badge():
    return html.Span(id="nav-user-badge")

def _ip_badge():
    return html.Span(id="nav-ip-badge", className="ms-2")

def _logout_button():
    return dbc.Button("Logout", id="nav-logout", color="light", size="sm", className="ms-3")

def _extend_toast():
    return dbc.Toast(
        [
            html.Div("Session will expire soon.", className="fw-semibold mb-1"),
            html.Small("Click to extend by 10 minutes."),
            dbc.Button("Extend 10 min", id="_extend_btn", color="primary", size="sm", className="mt-2"),
        ],
        id="_extend_toast",
        header="Session Timeout",
        icon="warning",
        is_open=False,
        dismissable=True,
        duration=None,
        style={"position": "fixed", "top": 70, "right": 20, "zIndex": 2000},
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
            dcc.Location(id="_page_location"),
            dcc.Location(id="_auth_redirect"),
            *GLOBAL_STORES,

            dbc.Navbar(
                dbc.Container(
                    [
                        dbc.NavbarBrand("Visual ML", href="/"),
                        dbc.Nav(
                            [
                                dbc.NavItem(dcc.Link("Home", href="/", className="nav-link")),
                                dbc.NavItem(dcc.Link("Design", href="/analysis/design", className="nav-link")),
                                dbc.NavItem(dcc.Link("Train", href="/analysis/train", className="nav-link")),
                                dbc.NavItem(dcc.Link("Results", href="/analysis/results", className="nav-link")),
                                dbc.NavItem(dcc.Link("Compare", href="/analysis/compare", className="nav-link")),
                            ],
                            navbar=True,
                            className="me-auto",
                        ),
                        dbc.Nav(
                            [
                                dbc.NavItem(_user_badge()),
                                dbc.NavItem(_ip_badge()),
                                dbc.NavItem(_logout_button()),
                            ],
                            navbar=True,
                            className="ms-auto",
                        ),
                    ],
                    fluid=True,
                ),
                color="dark",
                dark=True,
                className="mb-3",
            ),

            _extend_toast(),
            dcc.Interval(id="_auth_heartbeat", interval=60_000, disabled=False),

            dash.page_container,
        ],
        fluid=True,
    )
    return app


# ─────────────────────────────────────────
# 콜백: 네비 바 배지 (유저/아이피)
# ─────────────────────────────────────────
@callback(
    Output("nav-user-badge", "children"),
    Output("nav-ip-badge", "children"),
    Input("gs-auth", "data"),
    prevent_initial_call=False,
)
def _fill_nav_badges(auth):
    user = (auth or {}).get("user") or {}
    name = user.get("name") or user.get("username") or "-"
    role = user.get("role") or "user"
    ip = user.get("ip") or "-"
    user_badge = dbc.Badge(f"{name} ({role})", color="info", className="text-uppercase")
    ip_badge = dbc.Badge(ip, color="secondary")
    return user_badge, ip_badge


# ─────────────────────────────────────────
# 콜백: 라우팅(가드+로그아웃) → 유일하게 _auth_redirect.href 만 제어
# ─────────────────────────────────────────
@callback(
    Output("_auth_redirect", "href"),
    Input("_page_location", "href"),
    Input("gs-auth", "data"),      # 토큰 변화도 트리거
    Input("nav-logout", "n_clicks"),
    prevent_initial_call=False,
)
def _nav_router(href, auth, n_logout):
    from urllib.parse import urlparse, quote_plus

    # 로그아웃 버튼이 트리거면 → 로그인 페이지로 보냄 (Store는 login.py에서 정리)
    if dash.ctx.triggered_id == "nav-logout":
        return "/auth/login?logout=1&next=%2F"

    # 토큰 검사(보호 경로 이동 시)
    token = (auth or {}).get("access_token")
    path = (urlparse(href).path if href else "/") or "/"
    protected = ("/", "/analysis/design", "/analysis/train", "/analysis/results", "/analysis/compare")
    if path.startswith(protected) and not token:
        return f"/auth/login?next={quote_plus(path)}"

    return no_update


# ─────────────────────────────────────────
# 콜백: 세션 만료 토스트 (하트비트 + 연장 버튼) → 유일하게 _extend_toast.is_open 제어
# ─────────────────────────────────────────
@callback(
    Output("_extend_toast", "is_open"),
    Input("_auth_heartbeat", "n_intervals"),
    Input("_extend_btn", "n_clicks"),
    State("gs-auth", "data"),
    State("_extend_toast", "is_open"),
    prevent_initial_call=False,
)
def _toast_controller(_tick, _extend_clicks, auth, is_open):
    import time, base64, json

    trig = dash.ctx.triggered_id

    # 연장 버튼 클릭 → 토스트 닫기 (실제 refresh는 login.py 또는 별도 콜백에서 수행)
    if trig == "_extend_btn":
        return False

    # 하트비트에선 토큰 exp 확인
    token = (auth or {}).get("access_token")
    if not token:
        return False  # 미로그인 상태는 토스트 숨김

    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8"))
        exp = int(payload.get("exp", 0))
        now = int(time.time())
        # 남은 시간 60초 미만이면 열기, 아니면 닫기
        return (exp - now) < 60
    except Exception:
        return False