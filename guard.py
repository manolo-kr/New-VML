# backend/app/ui/auth/guard.py

from __future__ import annotations
import dash
from dash import dcc, html, callback, Input, Output, State, no_update

# 내부 허용 모드에서는 가드가 noop 이지만, 토큰 필요 모드로 전환 시 이 페이지로 리다이렉트 구성 가능
dash.register_page(__name__, path="/auth/guard", name="Guard")

layout = html.Div([
    dcc.Location(id="guard-loc"),
    html.Div("Access guard (internal mode: pass-through)"),
])