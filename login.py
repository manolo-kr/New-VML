# backend/app/ui/auth/login.py

from __future__ import annotations
from typing import Any, Dict

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/auth/login", name="Login")

layout = dbc.Container([
    html.H2("Login"),
    dbc.Row([
        dbc.Col(dbc.InputGroup([
            dbc.InputGroupText("Username"),
            dbc.Input(id="login-username", placeholder="username"),
        ]), md=6)
    ], className="mb-2"),
    dbc.Row([
        dbc.Col(dbc.InputGroup([
            dbc.InputGroupText("Password"),
            dbc.Input(id="login-password", type="password", placeholder="password"),
        ]), md=6)
    ], className="mb-3"),
    dbc.Button("Login", id="login-submit", color="primary"),
    html.Div(id="login-alert", className="mt-3"),
    dcc.Store(id="gs-auth", storage_type="session"),  # 보장(중복 생성 허용)
    dcc.Location(id="login-redirect"),
], fluid=True)

@callback(
    Output("gs-auth","data"),
    Output("login-alert","children"),
    Output("login-redirect","href"),
    Input("login-submit","n_clicks"),
    State("login-username","value"),
    State("login-password","value"),
    prevent_initial_call=True
)
def _do_login(n, u, p):
    if not (u and p):
        return no_update, dbc.Alert("Enter username/password", color="warning"), no_update
    # 내부 허용 모드라면 백엔드 토큰이 옵션일 수 있지만, 여긴 형태만 유지
    try:
        # 가짜 성공(실서비스에선 /auth/login 호출 후 token 저장)
        token = {"access_token": "INTERNAL_MODE", "user": {"username": u}}
        # api.set_token(...) 을 사용할 수도 있음
        return token, dbc.Alert("Logged in (internal mode).", color="success"), "/"
    except Exception as e:
        return no_update, dbc.Alert(f"Login failed: {e}", color="danger"), no_update