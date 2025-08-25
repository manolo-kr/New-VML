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
    """Dash 앱 팩토리"""
    app = dash.Dash(
        __name__,
        use_pages=True,
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="Visual ML",
    )

    app.layout = dbc.Container([
        dcc.Location(id="_page_location"),
        dcc.Store(id="_page_store"),   # 내부 라우팅용
        *GLOBAL_STORES,

        dbc.NavbarSimple(
            brand="Visual ML",
            brand_href="/",
            color="dark",
            dark=True,
            children=[
                dbc.NavItem(dcc.Link("Home", href="/", className="nav-link")),
                dbc.NavItem(dcc.Link("Design", href="/analysis/design", className="nav-link")),
                dbc.NavItem(dcc.Link("Train", href="/analysis/train", className="nav-link")),
                dbc.NavItem(dcc.Link("Results", href="/analysis/results", className="nav-link")),
                dbc.NavItem(dcc.Link("Compare", href="/analysis/compare", className="nav-link")),
            ]
        ),

        dash.page_container
    ], fluid=True)

    return app