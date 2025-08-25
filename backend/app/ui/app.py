# backend/app/ui/app.py

import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# 전역 Store: 로그인/프로젝트/디자인 상태 (세션 스토리지)
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),         # {"access_token": "...", "user": {..., "ip": "..."}}
    dcc.Store(id="gs-project", storage_type="session"),      # {"id": "...", "name": "..."}
    dcc.Store(id="gs-design-state", storage_type="session"), # 필요시 분석 설계 중간상태
]

def _user_badge():
    # 내용은 콜백으로 채움
    return html.Span(id="nav-user-badge")

def _ip_badge():
    return html.Span(id="nav-ip-badge", className="ms-2")

def _logout_button():
    return dbc.Button("Logout", id="nav-logout", color="light", size="sm", className="ms-3")

def _extend_toast():
    # 유휴 만료 경고 토스트 (is_open은 콜백에서 제어)
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
            dcc.Location(id="_auth_redirect"),   # 리다이렉트용 (href만 갱신)
            *GLOBAL_STORES,

            # 상단 네비게이션
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
                        # 우측 사용자/아이피/로그아웃
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

            # 세션 만료 토스트 + 하트비트
            _extend_toast(),
            dcc.Interval(id="_auth_heartbeat", interval=60_000, disabled=False),

            # 페이지 컨테이너
            dash.page_container,
        ],
        fluid=True,
    )

    return app


# ─────────────────────────────────────────────────────────────
# 콜백들
# ─────────────────────────────────────────────────────────────

# 1) 로그인 가드: 토큰 없으면 /auth/login 으로
@callback(
    Output("_auth_redirect", "href"),
    Input("_page_location", "href"),
    State("gs-auth", "data"),
    prevent_initial_call=False,
)
def _guard_route(href, auth):
    protected_paths = ("/analysis/design", "/analysis/train", "/analysis/results", "/analysis/compare", "/")
    if not href:
        return no_update
    try:
        # href에서 path만 떼기
        from urllib.parse import urlparse, quote_plus
        path = urlparse(href).path or "/"
        token = (auth or {}).get("access_token")
        if path.startswith(protected_paths) and not token:
            # next 파라미터로 현재 페이지 복귀
            return f"/auth/login?next={quote_plus(path)}"
    except Exception:
        pass
    return no_update


# 2) 네비 바 - 사용자/아이피 배지 내용 채우기
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


# 3) 로그아웃: gs-auth 초기화 + 루트로 이동(가드가 로그인화면으로 보냄)
@callback(
    Output("gs-auth", "data"),
    Output("_auth_redirect", "href"),
    Input("nav-logout", "n_clicks"),
    prevent_initial_call=True,
)
def _logout(_n):
    return {}, "/"


# 4) 세션 만료 토스트: 남은 시간 정보를 토큰 페이로드에 넣어뒀다고 가정 (exp, now 비교)
@callback(
    Output("_extend_toast", "is_open"),
    Input("_auth_heartbeat", "n_intervals"),
    State("gs-auth", "data"),
    prevent_initial_call=False,
)
def _tick_heartbeat(_n, auth):
    import time, base64, json
    token = (auth or {}).get("access_token")
    if not token:
        # 미로그인 상태에서는 토스트 숨김
        return False
    # JWT exp 확인 (페이크/커스텀 토큰이면 서버가 별도 user.expires_at을 내려줘도 됨)
    try:
        # 매우 단순한 JWT payload 파서 (검증 목적 아님)
        payload_b64 = token.split(".")[1]
        # padding
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8"))
        exp = int(payload.get("exp", 0))
        now = int(time.time())
        # 남은 시간이 60초 미만이면 토스트 열기
        return (exp - now) < 60
    except Exception:
        # 파싱 실패 시 토스트 끄기
        return False


# 5) 연장 버튼 → /auth/refresh 호출은 프런트에서 api_client로 처리하는 대신 여기선 Store만 트리거
#    (실제 토큰 갱신은 로그인 페이지나 각 페이지 내 별도 콜백에서 처리 가능)
@callback(
    Output("_extend_toast", "is_open"),
    Input("_extend_btn", "n_clicks"),
    prevent_initial_call=True,
)
def _extend_now(_n):
    # 버튼 클릭 시 토스트 닫고, 각 페이지에서 실제 refresh 호출 처리(이미 구현돼 있다면 거기 재사용)
    return False