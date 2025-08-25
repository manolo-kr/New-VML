# backend/app/ui/auth/login.py

import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from app.ui.clients import api_client as api

dash.register_page(__name__, path="/login", name="Login")

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Login", className="mb-4"),
            dbc.Input(id="login-email", type="email", placeholder="Email", className="mb-2"),
            dbc.Input(id="login-password", type="password", placeholder="Password", className="mb-3"),
            dbc.Button("Login", id="btn-login", color="primary", className="w-100"),
            html.Div(id="login-alert", className="mt-3"),
        ], width=4)
    ], justify="center", className="mt-5"),

    dcc.Store(id="login-redirect"),
])

# ------------------------
# Callback
# ------------------------
@callback(
    Output("gs-auth", "data"),
    Output("login-alert", "children"),
    Input("btn-login", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def _do_login(n, email, password):
    try:
        resp = api.login(email, password)
        token = resp.get("access_token")
        user = resp.get("user")
        ip = resp.get("ip")  # ← 서버에서 전달받은 IP 저장

        if not token or not user:
            return None, dbc.Alert("Invalid login response", color="danger")

        return {"access_token": token, "user": user, "ip": ip}, dbc.Alert("Login successful!", color="success")
    except Exception as e:
        return None, dbc.Alert(f"Login failed: {e}", color="danger")