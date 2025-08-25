# backend/app/ui/auth/login.py

from __future__ import annotations
from typing import Any, Dict
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import requests
import os

API_DIR = os.getenv("API_DIR", "http://127.0.0.1:8065").rstrip("/")
API_BASE = os.getenv("API_BASE", "/api").rstrip("/")

dash.register_page(__name__, path="/login", name="Login")

def _url(p: str) -> str:
    if not p.startswith("/"):
        p = "/" + p
    return f"{API_DIR}{API_BASE}{p}"

layout = dbc.Container([
    dcc.Location(id="login-url"),
    dcc.Store(id="gs-auth", storage_type="session"),
    dbc.Row([
        dbc.Col(width=3),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Sign In"),
            dbc.CardBody([
                dbc.FormFloating([
                    dbc.Input(id="login-username", placeholder="username", type="text"),
                    dbc.Label("Username"),
                ], className="mb-2"),
                dbc.FormFloating([
                    dbc.Input(id="login-password", placeholder="password", type="password"),
                    dbc.Label("Password"),
                ], className="mb-3"),
                dbc.Button("Login", id="btn-login", color="primary", className="w-100"),
                html.Div(id="login-alert", className="mt-3"),
            ])
        ], className="mt-5"), width=6),
        dbc.Col(width=3),
    ])
], fluid=True)

@callback(
    Output("gs-auth", "data"),
    Output("login-alert", "children"),
    Input("btn-login", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def _do_login(n, username, password):
    if not username or not password:
        return no_update, dbc.Alert("Enter username and password", color="warning")
    try:
        r = requests.post(_url("/auth/login"), json={"username": username, "password": password}, timeout=20)
        r.raise_for_status()
        bundle = r.json()
        return bundle, dbc.Alert("Login success", color="success")
    except Exception as e:
        return no_update, dbc.Alert(f"Login failed: {e}", color="danger")