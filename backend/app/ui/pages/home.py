# backend/app/ui/pages/home.py

# 홈: 프로젝트 목록 / 생성 / 삭제
# - gs-auth(session)에서 토큰을 읽어 API 호출
# - 콜백 출력 충돌 피하도록 각 콜백의 Output을 고유하게 분리

from __future__ import annotations
from typing import List, Dict, Any

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ALL
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/", name="Home")

# ----------------------------
# Layout
# ----------------------------
layout = dbc.Container([
    # 전역 스토어(로그인 정보)에서 토큰을 읽어 사용
    dcc.Store(id="home-projects"),  # [{id,name,created_at}, ...]
    dcc.Location(id="home-url"),

    html.H2("Projects"),

    dbc.Row([
        dbc.Col(
            dbc.InputGroup([
                dbc.InputGroupText("New Project"),
                dbc.Input(id="home-new-name", placeholder="Enter project name"),
                dbc.Button("Create", id="home-btn-create", color="primary"),
            ]),
            md=7
        ),
        dbc.Col(
            html.Div(id="home-alert"),  # 생성/삭제 결과 메시지
            md=5
        ),
    ], className="g-2 mb-3"),

    html.Div(id="home-list")  # 프로젝트 목록 테이블 렌더링
], fluid=True)


# ----------------------------
# Callbacks
# ----------------------------

# 1) 페이지 진입 → 프로젝트 목록 로딩
@callback(
    Output("home-projects", "data"),
    Input("home-url", "href"),
    State("gs-auth", "data"),
    prevent_initial_call=False
)
def _load_projects(_href, auth):
    token = (auth or {}).get("access_token")
    try:
        items: List[Dict[str, Any]] = api.list_projects(token=token)
        return items
    except Exception:
        return []


# 2) 목록 렌더링 (스토어 → 테이블)
@callback(
    Output("home-list", "children"),
    Input("home-projects", "data")
)
def _render_projects(items):
    items = items or []
    if not items:
        return dbc.Alert("No projects yet. Create one above.", color="secondary")

    header = html.Thead(html.Tr([
        html.Th("Project"),
        html.Th("Created At"),
        html.Th("Actions"),
    ]))

    rows = []
    for p in items:
        pid = p.get("id")
        pname = p.get("name")
        created = p.get("created_at") or "-"
        # Design 진입 링크
        to_design = dcc.Link("Open", href=f"/analysis/design?project_id={pid}")

        # 삭제 버튼(패턴매칭 ID)
        del_btn = dbc.Button("Delete", id={"type": "home-del", "pid": pid}, color="danger", outline=True, size="sm")

        rows.append(html.Tr([
            html.Td(pname),
            html.Td(created),
            html.Td(dbc.ButtonGroup([to_design, html.Span(" "), del_btn]))
        ]))

    table = dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, responsive=True)
    return table


# 3) 프로젝트 생성 → 성공 시 목록 갱신 + 메시지
@callback(
    Output("home-projects", "data", allow_duplicate=True),
    Output("home-alert", "children"),
    Input("home-btn-create", "n_clicks"),
    State("home-new-name", "value"),
    State("gs-auth", "data"),
    prevent_initial_call=True
)
def _create_project(n, name, auth):
    if not n:
        return no_update, no_update
    token = (auth or {}).get("access_token")
    nm = (name or "").strip()
    if not nm:
        return no_update, dbc.Alert("Please enter a project name.", color="warning", className="py-2")

    try:
        _ = api.create_project(nm, token=token)
        items = api.list_projects(token=token)
        return items, dbc.Alert("Project created.", color="success", className="py-2")
    except Exception as e:
        return no_update, dbc.Alert(f"Create failed: {e}", color="danger", className="py-2")


# 4) 삭제 버튼 → 삭제 후 목록 갱신 + 메시지
@callback(
    Output("home-projects", "data", allow_duplicate=True),
    Output("home-alert", "children", allow_duplicate=True),
    Input({"type": "home-del", "pid": ALL}, "n_clicks"),
    State("home-projects", "data"),
    State("gs-auth", "data"),
    prevent_initial_call=True
)
def _delete_project(n_clicks_list, items, auth):
    token = (auth or {}).get("access_token")
    if not n_clicks_list or not items:
        return no_update, no_update

    # 어떤 버튼이 눌렸는지 파악
    trig = dash.ctx.triggered_id
    if not isinstance(trig, dict):
        return no_update, no_update
    pid = trig.get("pid")
    if not pid:
        return no_update, no_update

    try:
        api.delete_project(pid, token=token)
        items = api.list_projects(token=token)
        return items, dbc.Alert("Project deleted.", color="info", className="py-2")
    except Exception as e:
        return no_update, dbc.Alert(f"Delete failed: {e}", color="danger", className="py-2")