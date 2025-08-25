# backend/app/ui/auth/login.py

import os
import requests
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# 이 모듈은 app 인스턴스 생성 이후에 임포트되어야 합니다!
dash.register_page(__name__, path="/auth/login", name="Login")

layout = dbc.Container(
    [
        dcc.Location(id="login-url"),
        dcc.Store(id="login-error"),

        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Sign in"),
                        dbc.CardBody(
                            [
                                dbc.Alert(
                                    id="login-err-alert",
                                    color="danger",
                                    is_open=False,
                                    className="py-2",
                                ),
                                dbc.Input(
                                    id="login-username",
                                    placeholder="Username",
                                    type="text",
                                    className="mb-2",
                                    autoComplete="username",
                                ),
                                dbc.Input(
                                    id="login-password",
                                    placeholder="Password",
                                    type="password",
                                    className="mb-3",
                                    autoComplete="current-password",
                                ),
                                dbc.Button(
                                    "Login",
                                    id="login-submit",
                                    color="primary",
                                    className="w-100",
                                ),
                            ]
                        ),
                    ],
                    className="mt-5 shadow-sm",
                    style={"maxWidth": 380},
                ),
                width="auto",
            ),
            justify="center",
        ),
    ],
    fluid=True,
)

# 에러 표시
@callback(
    Output("login-err-alert", "children"),
    Output("login-err-alert", "is_open"),
    Input("login-error", "data"),
    prevent_initial_call=True,
)
def _show_err(err):
    if not err:
        return no_update, False
    return str(err), True


# 로그인 처리: 성공 시 gs-auth 갱신 (리다이렉트는 app.py 가드가 담당)
@callback(
    Output("gs-auth", "data", allow_duplicate=True),
    Output("login-error", "data"),
    Input("login-submit", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    State("login-url", "href"),
    prevent_initial_call=True,
)
def _do_login(n, username, password, href):
    if not n:
        return no_update, no_update

    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        return no_update, "Please enter username and password."

    try:
        API_DIR = os.getenv("API_DIR", "http://127.0.0.1:8065").rstrip("/")
        API_BASE = os.getenv("API_BASE", "/api").rstrip("/")
        url = f"{API_DIR}{API_BASE}/auth/login"
        r = requests.post(url, json={"username": username, "password": password}, timeout=10)
        if r.status_code != 200:
            return no_update, f"Login failed: {r.text}"
        data = r.json()  # {"access_token": "...", "user": {..., "ip": "..."}}
        return data, None
    except Exception as e:
        return no_update, f"Login error: {e}"