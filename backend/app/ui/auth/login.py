# backend/app/ui/auth/login.py

import urllib.parse as up
from datetime import datetime

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/auth/login", name="Login")

def _card():
    return dbc.Card([
        dbc.CardHeader(html.H5("Sign in")),
        dbc.CardBody([
            dbc.Alert(id="_auth_message", is_open=False, color="danger", class_name="py-2 mb-3"),
            dbc.Input(id="login-username", placeholder="Username", type="text", class_name="mb-2"),
            dbc.Input(id="login-password", placeholder="Password", type="password", class_name="mb-3"),
            dbc.Button("Login", id="btn-login", color="primary", class_name="w-100"),
            html.Div(dcc.Link("Back to Home", href="/", className="d-block text-center mt-3")),
        ]),
    ], class_name="shadow-sm")

layout = dbc.Container([
    dcc.Location(id="login-url"),
    dcc.Location(id="_auth_redirect", refresh=True),  # ← app.py의 가드와 분리된 Location
    dbc.Row([dbc.Col([], md=3), dbc.Col(_card(), md=6), dbc.Col([], md=3)], class_name="mt-5"),
], fluid=True)

@callback(
    Output("gs-auth", "data"),
    Output("_auth_redirect", "href"),
    Output("_auth_message", "children"),
    Output("_auth_message", "is_open"),
    Input("btn-login", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    State("login-url", "href"),
    prevent_initial_call=True,
)
def _do_login(n, username, password, href):
    if not n:
        return no_update, no_update, no_update, no_update

    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        return no_update, no_update, "Please enter username and password.", True

    try:
        resp = api.login(username=username, password=password)
        access_token = resp.get("access_token")
        user = resp.get("user") or {}
        if not access_token:
            raise ValueError("No access_token in response")

        # 전역 헤더세팅
        api.set_auth(access_token)

        # next 파라미터
        next_href = "/"
        if href:
            q = up.urlparse(href).query
            params = dict(up.parse_qsl(q, keep_blank_values=True))
            nxt = params.get("next")
            if nxt:
                next_href = nxt

        gs = {"access_token": access_token, "user": user, "login_at": datetime.utcnow().isoformat() + "Z"}
        return gs, next_href, no_update, False

    except Exception as e:
        return no_update, no_update, f"Login failed: {e}", True