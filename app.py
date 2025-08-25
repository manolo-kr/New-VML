# backend/app/ui/app.py

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),
    dcc.Store(id="gs-project", storage_type="session"),
    dcc.Store(id="gs-design-state", storage_type="session"),
]

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
        dcc.Store(id="_page_store"),
        *GLOBAL_STORES,

        dcc.Interval(id="auth-keepalive-global", interval=30_000, n_intervals=0),

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
                dbc.NavItem(dcc.Link("Login", href="/login", className="nav-link")),
            ]
        ),

        dash.page_container
    ], fluid=True)

    @app.callback(
        dash.Output("._dummy", "children", allow_duplicate=True),
        dash.Input("auth-keepalive-global", "n_intervals"),
        dash.State("gs-auth", "data"),
        prevent_initial_call=True
    )
    def _keepalive_global(_n, auth_bundle):
        from app.ui.clients import api_client as api
        api.set_auth(auth_bundle or {})
        return dash.no_update

    return app