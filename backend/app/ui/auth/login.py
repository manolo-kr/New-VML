# backend/app/ui/auth/login.py

import os
import requests
from typing import Any, Dict

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/login", name="Login")

API_DIR = os.getenv("API_DIR", "http://127.0.0.1:8065").rstrip("/")
API_BASE = os.getenv("API_BASE", "/api")

def _card(body):
    return dbc.Card([dbc.CardHeader("Sign in"), dbc.CardBody(body)], className="mx-auto", style={"maxWidth": "560px"})

layout = dbc.Container([
    dbc.Row([
        dbc.Col(_card([
            dbc.Alert(id="login-alert", color="secondary", is_open=False, className="py-2"),
            dbc.InputGroup([
                dbc.InputGroupText("Email"),
                dbc.Input(id="login-email", type="email", placeholder="you@example.com"),
            ], className="mb-2"),
            dbc.InputGroup([
                dbc.InputGroupText("Password"),
                dbc.Input(id="login-password", type="password", placeholder="••••••••"),
            ], className="mb-3"),
            dbc.Button("Login", id="login-submit", color="primary", className="w-100"),
            html.Div(className="mt-3 small text-muted", children="Session defaults to 10 minutes. Use the navbar to extend."),
        ]), md=8, lg=6),
    ], className="justify-content-center"),
], fluid=True)

@callback(
    Output("login-alert", "children"),
    Output("login-alert", "is_open"),
    Output("gs-auth-inbox", "data"),   # ← 허브로 전달 (gs-auth는 허브만 씀)
    Input("login-submit", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def _do_login(_n, email, password):
    if not _n:
        return no_update, no_update, no_update
    if not email or not password:
        return "Email and password required.", True, no_update
    try:
        r = requests.post(f"{API_DIR}{API_BASE}/auth/login", json={"email": email, "password": password}, timeout=15)
        if r.status_code != 200:
            return f"Login failed: {r.text}", True, no_update
        data: Dict[str, Any] = r.json()
        auth = {
            "access_token": data["access_token"],
            "user": data.get("user"),
            "client_ip": data.get("client_ip"),
            "exp": data.get("exp"),
        }
        return "Login success. Redirecting…", True, auth
    except Exception as e:
        return f"Error: {e}", True, no_update