# backend/app/ui/app.py

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

# 전역 Store: 로그인 상태, 현재 프로젝트, 디자인 상태 등
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),         # {"access_token": "...", "user": {...}}
    dcc.Store(id="gs-project", storage_type="session"),      # {"id": "...", "name": "..."}
    dcc.Store(id="gs-design-state", storage_type="session"), # {"analysis_id": "...", ...}
]

def build_dash_app() -> dash.Dash:
    """
    Dash 앱 팩토리
    - pages_folder=None: 루트의 pages/ 자동 스캔 비활성화 (중복 등록 방지)
    - 각 page 모듈은 app 생성 *이후*에 임포트하여 register_page가 정상 작동
    """
    app = dash.Dash(
        __name__,
        use_pages=True,
        pages_folder=None,                 # ✅ 자동 pages 스캔 끔 (중복 방지)
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="Visual ML",
    )

    # ⚠️ app 생성 이후에 page 모듈 임포트 (이 시점에 register_page 호출됨)
    from app.ui.auth import login as _login              # noqa: F401
    from app.ui.pages import home as _p_home             # noqa: F401
    from app.ui.pages import analysis_design as _p_des   # noqa: F401
    from app.ui.pages import analysis_train as _p_trn    # noqa: F401
    from app.ui.pages import analysis_results as _p_res  # noqa: F401
    from app.ui.pages import analysis_compare as _p_cmp  # noqa: F401

    # 상단 네비게이션 바
    navbar = dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.Row([
                    dbc.Col(dbc.NavbarBrand("Visual ML", className="ms-1")),
                ], align="center", className="g-0"),
                href="/",
                style={"textDecoration": "none"},
            ),

            dbc.Nav([
                dbc.NavItem(dcc.Link("Home", href="/",              className="nav-link")),
                dbc.NavItem(dcc.Link("Design", href="/analysis/design",  className="nav-link")),
                dbc.NavItem(dcc.Link("Train", href="/analysis/train",    className="nav-link")),
                dbc.NavItem(dcc.Link("Results", href="/analysis/results",className="nav-link")),
                dbc.NavItem(dcc.Link("Compare", href="/analysis/compare",className="nav-link")),
            ], className="me-auto", navbar=True),

            # 우측: 사용자/아이피/로그아웃 (내용은 각 페이지/로그인 콜백에서 채워짐)
            dbc.Nav([
                html.Div(id="nav-user-badge",  className="me-2"),
                html.Div(id="nav-ip-badge",    className="me-2"),
                html.Div(id="nav-logout"),  # 예: dcc.Link("Logout", href="/auth/login?logout=1", className="nav-link")
            ], navbar=True),
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-4",
    )

    app.layout = dbc.Container([
        dcc.Location(id="_page_location"),
        dcc.Store(id="_page_store"),     # 내부 라우팅/리다이렉션 보조
        *GLOBAL_STORES,                  # 세션 상태

        navbar,

        # 페이지 컨테이너
        dash.page_container,
    ], fluid=True)

    return app