# backend/app/ui/auth/login.py

import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/auth/login", name="Login")

_layout_form = dbc.Card(
    [
        dbc.CardHeader("Sign in"),
        dbc.CardBody(
            [
                dbc.Alert(id="_auth_message", color="info", is_open=False),
                dbc.Input(id="_auth_username", placeholder="Username", type="text", className="mb-2"),
                dbc.Input(id="_auth_password", placeholder="Password", type="password", className="mb-3"),
                dbc.Button("Login", id="_auth_submit", color="primary", className="w-100"),
                html.Small(
                    "세션은 비활성 10분 후 만료됩니다. 'Extend 10m'로 연장할 수 있어요.",
                    className="text-muted d-block mt-3",
                ),
            ]
        ),
    ],
    class_name="mx-auto",
    style={"maxWidth": "420px"},
)

layout = dbc.Container(
    [
        dcc.Location(id="_auth_location"),
        dcc.Location(id="_auth_redirection"),
        _layout_form,
    ],
    fluid=True,
    class_name="py-5",
)

# 이미 로그인 상태면 next 또는 홈으로 이동
@callback(
    Output("_auth_redirection", "href"),
    Input("gs-auth", "data"),
    State("_auth_location", "href"),
    prevent_initial_call=False,
)
def _already_logged_in(auth, href):
    if not auth or not auth.get("access_token"):
        return no_update
    next_path = "/"
    if href:
        q = up.urlparse(href).query
        params = dict(up.parse_qsl(q, keep_blank_values=True))
        next_path = params.get("next") or "/"
    return next_path

# 로그인 요청
@callback(
    Output("gs-auth", "data"),
    Output("_auth_redirection", "href"),
    Output("_auth_message", "is_open"),
    Output("_auth_message", "children"),
    Input("_auth_submit", "n_clicks"),
    State("_auth_username", "value"),
    State("_auth_password", "value"),
    State("_auth_location", "href"),
    prevent_initial_call=True,
)
def _do_login(n, username, password, href):
    if not n:
        return no_update, no_update, no_update, no_update
    try:
        res = api.login(username or "", password or "")
        auth = {
            "access_token": res.get("access_token"),
            "user": res.get("user"),
            "ip": res.get("ip"),
        }
        next_path = "/"
        if href:
            q = up.urlparse(href).query
            params = dict(up.parse_qsl(q, keep_blank_values=True))
            next_path = params.get("next") or "/"
        return auth, next_path, False, no_update
    except Exception as e:
        return no_update, no_update, True, f"로그인 실패: {e}"