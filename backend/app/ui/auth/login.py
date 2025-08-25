# backend/app/ui/auth/login.py

import json
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

# ✅ app 생성 이후(app.ui.app.build_dash_app 내부) import 되도록!
dash.register_page(__name__, path="/auth/login", name="Login")

_layout_form = dbc.Card(
    dbc.CardBody([
        html.H4("Sign in", className="mb-3"),

        dbc.Form([
            dbc.Label("User ID", html_for="login-username"),
            dbc.Input(id="login-username", placeholder="your id", autoComplete="username"),
            dbc.Label("Password", className="mt-3", html_for="login-password"),
            dbc.Input(id="login-password", placeholder="••••••••", type="password", autoComplete="current-password"),
            dbc.Button("Login", id="login-submit", color="primary", className="mt-3", n_clicks=0),
        ]),

        html.Div(id="login-alert", className="mt-3"),
        # 리다이렉트용 Location (이 페이지 내부 전용 id → 중복 없음)
        dcc.Location(id="login-redirect"),
    ])
)

layout = dbc.Container([
    dcc.Location(id="login-url"),  # ?next=/... 파라미터 읽기용
    _layout_form
], fluid=True)


@callback(
    Output("gs-auth", "data"),
    Output("login-alert", "children"),
    Output("login-redirect", "href"),
    Input("login-submit", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    State("login-url", "href"),
    prevent_initial_call=True
)
def _do_login(n, username, password, href):
    if not n:
        return no_update, no_update, no_update

    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        return no_update, dbc.Alert("Please enter both ID and password.", color="warning"), no_update

    try:
        resp = api.login(username, password)  # {"access_token": "...", "user": {...}}
        token = resp.get("access_token")
        user = resp.get("user") or {}
        if not token:
            raise ValueError("No token returned")

        # next 파라미터 해석
        next_href = "/"
        if href:
            q = up.urlparse(href).query
            params = dict(up.parse_qsl(q, keep_blank_values=True))
            if params.get("next"):
                next_href = params["next"]

        return {"access_token": token, "user": user}, dbc.Alert("Login success.", color="success"), next_href

    except Exception as e:
        return no_update, dbc.Alert(f"Login failed: {e}", color="danger"), no_update