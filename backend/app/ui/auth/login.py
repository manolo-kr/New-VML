# backend/app/ui/auth/login.py
# (최신본) 로그인 페이지. 제출 시 gs-auth 저장 + 해당 페이지 전용 리다이렉트 컴포넌트로 이동.
# 전역 가드가 사용하는 _auth_redirect 와 Output 충돌하지 않도록 login-redirect 를 별도로 둡니다.

import urllib.parse as up
from typing import Any, Dict

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/auth/login", name="Login")

layout = dbc.Container([
    dcc.Location(id="login-url"),
    # 로그인 전용 리다이렉트(전역 가드와 Output 충돌 방지)
    dcc.Location(id="login-redirect"),

    dbc.Row([
        dbc.Col(width=3),
        dbc.Col([
            html.H3("Sign in"),
            dbc.Alert(id="login-message", color="danger", is_open=False, className="py-2"),

            dbc.Form([
                dbc.Label("Username"),
                dbc.Input(id="login-username", type="text", placeholder="Enter username"),

                dbc.Label("Password", className="mt-2"),
                dbc.Input(id="login-password", type="password", placeholder="Enter password"),

                dbc.Button("Sign in", id="login-submit", color="primary", className="mt-3 w-100"),
            ], className="mt-3")
        ], md=6),
        dbc.Col(width=3),
    ], className="mt-5")
], fluid=True)

@callback(
    Output("gs-auth", "data"),
    Output("login-message", "children"),
    Output("login-message", "is_open"),
    Output("login-redirect", "href"),
    Input("login-submit", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    State("login-url", "href"),
    prevent_initial_call=True
)
def _do_login(n, username, password, href):
    if not n:
        return no_update, no_update, no_update, no_update
    username = (username or "").strip()
    password = (password or "").strip()
    if not (username and password):
        return no_update, "Please enter username and password.", True, no_update

    try:
        resp: Dict[str, Any] = api.login(username, password)
        token = resp.get("access_token")
        user = resp.get("user")
        ip = resp.get("ip")  # 서버가 내려주면 사용
        gs = {"access_token": token, "user": user, "ip": ip}
    except Exception as e:
        return no_update, f"Login failed: {e}", True, no_update

    # next 파라미터 해석
    next_path = "/"
    if href:
        q = up.urlparse(href).query
        params = dict(up.parse_qsl(q, keep_blank_values=True))
        if "next" in params and params["next"]:
            next_path = params["next"]
    return gs, "", False, next_path