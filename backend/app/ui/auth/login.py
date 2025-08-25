# backend/app/ui/auth/login.py

import time
from typing import Any, Dict

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

import requests
import os

dash.register_page(__name__, path="/login", name="Login")

API_DIR = os.getenv("API_DIR", "http://127.0.0.1:8065")  # 프론트에서 직접 호출 시 사용


def _card(body):
    return dbc.Card([dbc.CardHeader("Sign in"), dbc.CardBody(body)], className="mx-auto", style={"maxWidth": "560px"})


layout = dbc.Container([
    dcc.Store(id="login-auth"),
    html.Div(className="d-flex justify-content-center", children=[
        _card([
            dbc.Alert(id="login-alert", color="secondary", is_open=False, className="py-2"),
            dbc.Row([
                dbc.Col(dbc.InputGroup([
                    dbc.InputGroupText("Email"),
                    dbc.Input(id="login-email", type="email", placeholder="you@example.com"),
                ]), md=12, className="mb-2"),
                dbc.Col(dbc.InputGroup([
                    dbc.InputGroupText("Password"),
                    dbc.Input(id="login-password", type="password", placeholder="••••••••"),
                ]), md=12, className="mb-3"),
            ], className="g-2"),
            dbc.Button("Login", id="login-submit", color="primary", className="w-100"),
            html.Div(className="mt-3 small text-muted", children=[
                "Session: 10 minutes default. You can extend in the navbar."
            ])
        ])
    ]),
    dcc.Location(id="login-redirect"),
], fluid=True)


@callback(
    Output("login-alert", "children"),
    Output("login-alert", "is_open"),
    Output("gs-auth", "data"),
    Output("login-redirect", "href"),
    Input("login-submit", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def _do_login(_n, email, password):
    if not _n:
        return no_update, no_update, no_update, no_update
    if not email or not password:
        return "Email and password required.", True, no_update, no_update
    try:
        r = requests.post(f"{API_DIR}/api/auth/login", json={"email": email, "password": password}, timeout=15)
        if r.status_code != 200:
            return f"Login failed: {r.text}", True, no_update, no_update
        data: Dict[str, Any] = r.json()
        # gs-auth 형태 통일: {access_token,user,client_ip,exp}
        auth = {
            "access_token": data["access_token"],
            "user": data.get("user"),
            "client_ip": data.get("client_ip"),
            "exp": data.get("exp"),
        }
        return "Login success. Redirecting…", True, auth, "/"
    except Exception as e:
        return f"Error: {e}", True, no_update, no_update