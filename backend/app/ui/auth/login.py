# backend/app/ui/auth/login.py

import json
import urllib.parse as up
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/auth/login", name="Login")

_layout_card = dbc.Card(
    [
        dbc.CardHeader(html.H5("Sign in")),
        dbc.CardBody(
            [
                dbc.Alert(id="_auth_message", color="danger", is_open=False, class_name="py-2"),
                dbc.Input(id="_auth_username", placeholder="Username", type="text", class_name="mb-2"),
                dbc.Input(id="_auth_password", placeholder="Password", type="password", class_name="mb-2"),
                dbc.Button("Login", id="_auth_submit", color="primary", class_name="w-100"),
            ]
        ),
        dbc.CardFooter(
            html.Small("You will be redirected to your target page after login.", className="text-muted")
        ),
    ],
    class_name="shadow-sm",
)

layout = dbc.Container(
    [
        dcc.Location(id="_auth_loc"),
        dcc.Location(id="_auth_redirection"),
        dbc.Row(
            dbc.Col(_layout_card, md=4),
            class_name="justify-content-center mt-5",
        ),
    ],
    fluid=True,
)

# 로그인 성공 시 리다이렉트 경로 계산 (next 파라미터)
def _next_from_search(search: str | None) -> str:
    if not search:
        return "/"
    qs = dict(up.parse_qsl((search or "").lstrip("?"), keep_blank_values=True))
    nxt = qs.get("next") or "/"
    # 보안상 절대경로만 허용(외부 URL 차단)
    if not str(nxt).startswith("/"):
        return "/"
    return nxt


@callback(
    Output("_auth_message", "children"),
    Output("_auth_message", "is_open"),
    Output("gs-auth", "data", allow_duplicate=True),
    Output("_auth_redirection", "href"),
    Input("_auth_submit", "n_clicks"),
    State("_auth_username", "value"),
    State("_auth_password", "value"),
    State("_auth_loc", "search"),
    prevent_initial_call=True,
)
def _do_login(n, username, password, search):
    if not n:
        return no_update, no_update, no_update, no_update
    if not username or not password:
        return "Please enter username & password.", True, no_update, no_update
    try:
        # 서버에 로그인 요청 (IP는 서버가 채워서 반환)
        res = api.login(username=username.strip(), password=password)
        token = res.get("access_token")
        user = res.get("user")
        ip   = res.get("ip")
        if not token:
            return "Login failed: no token.", True, no_update, no_update

        # 세션 저장
        auth_data = {"access_token": token, "user": user, "ip": ip}
        # next 계산 후 이동
        target = _next_from_search(search)
        return no_update, False, auth_data, target
    except Exception as e:
        return f"Login failed: {e}", True, no_update, no_update