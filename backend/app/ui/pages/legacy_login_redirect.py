# backend/app/ui/pages/legacy_login_redirect.py

import dash
from dash import dcc, html, callback, Input, Output, State, no_update

# "/login"로 들어온 구(舊) 경로를 최신 경로 "/auth/login"으로 안전하게 리다이렉트
dash.register_page(__name__, path="/login", name="Login (legacy redirect)")

layout = html.Div([
    dcc.Location(id="legacy_login_loc"),
    dcc.Location(id="legacy_login_go"),
    html.Div("Redirecting to /auth/login ..."),
])


@callback(
    Output("legacy_login_go", "href"),
    Input("legacy_login_loc", "search"),
    prevent_initial_call=False,
)
def _go_auth_login(search):
    # 예: /login?next=/analysis → /auth/login?next=/analysis
    return f"/auth/login{search or ''}"