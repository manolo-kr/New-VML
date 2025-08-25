# backend/app/ui/pages/home.py

from __future__ import annotations
import json
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/", name="Home")

def _proj_row(p: dict) -> dbc.ListGroupItem:
    pid = p["id"]
    name = p.get("name") or "(unnamed)"
    open_url = f"/analysis/design?project_id={pid}"
    return dbc.ListGroupItem(
        dbc.Row([
            dbc.Col(html.Div([html.B(name), html.Small(f"  (id={pid})", className="text-muted")]), md=7),
            dbc.Col(dbc.Button("Open", href=open_url, color="primary", size="sm"), md="auto"),
            dbc.Col(dbc.Button("Delete", id={"type":"proj-del-btn", "id":pid}, color="danger", outline=True, size="sm"), md="auto"),
        ], className="g-2 align-items-center"),
        className="py-2"
    )

layout = dbc.Container([
    dcc.Store(id="home-reload-token"),  # 삭제/생성 후 리스트 새로고침 트리거용

    html.H2("Projects"),

    dbc.Row([
        dbc.Col(
            dbc.InputGroup([
                dbc.Input(id="home-new-proj-name", placeholder="New project name", type="text"),
                dbc.Button("Create", id="home-btn-create", color="primary"),
            ]),
            md=6
        ),
    ], className="mb-3"),

    dbc.ListGroup(id="home-proj-list"),

    # 삭제 확인 모달
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Delete project")),
        dbc.ModalBody(id="home-del-modal-body"),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="home-del-cancel", className="me-2"),
            dbc.Button("Delete", id="home-del-confirm", color="danger"),
        ])
    ], id="home-del-modal", is_open=False),
], fluid=True)

# 프로젝트 목록 로드
@callback(
    Output("home-proj-list","children"),
    Input("home-reload-token","data"),
    prevent_initial_call=False
)
def _load_projects(_token):
    projs = api.list_projects()
    if not projs:
        return dbc.Alert("No projects yet. Create one above.", color="secondary")
    return [_proj_row(p) for p in projs]

# 생성
@callback(
    Output("home-reload-token","data"),
    Input("home-btn-create","n_clicks"),
    State("home-new-proj-name","value"),
    prevent_initial_call=True
)
def _create_project(n, name):
    if not name:
        return no_update
    api.create_project(name)
    return "reload"

# 삭제 플로우 (모달 열기 -> 확인 시 삭제)
@callback(
    Output("home-del-modal","is_open"),
    Output("home-del-modal-body","children"),
    Output("home-del-confirm","n_clicks"),
    Input({"type":"proj-del-btn", "id":dash.ALL},"n_clicks"),
    Input("home-del-cancel","n_clicks"),
    Input("home-del-confirm","n_clicks"),
    State("home-del-modal","is_open"),
    prevent_initial_call=True
)
def _delete_flow(btns, cancel_n, confirm_n, is_open):
    ctx = dash.ctx
    tid = ctx.triggered_id
    if isinstance(tid, dict) and tid.get("type") == "proj-del-btn":
        pid = tid["id"]
        body = html.Div([
            html.Div("Are you sure you want to delete this project (and its analyses & tasks)?"),
            html.Small(f"project_id = {pid}", id="home-del-pid", style={"display":"block","marginTop":"6px"})
        ])
        return True, body, 0
    if ctx.triggered_id == "home-del-cancel":
        return False, no_update, 0
    if ctx.triggered_id == "home-del-confirm" and is_open:
        # 실제 삭제
        # project_id는 모달 바디 텍스트에서 추출하지 않고, 최신 트리거에서 관리하도록 단순화
        # 모달이 열릴 때 최신 버튼의 id가 ctx.triggered_props에 포함되므로 재활용
        return False, no_update, 0
    return is_open, no_update, no_update

# 실제 삭제 수행 + 리스트 새로고침
@callback(
    Output("home-reload-token","data", allow_duplicate=True),
    Input("home-del-confirm","n_clicks"),
    State("home-del-modal-body","children"),
    prevent_initial_call=True
)
def _confirm_delete(n, body_children):
    if not n:
        return no_update
    # body_children[1] 의 텍스트에서 project_id 추출
    try:
        txt = body_children[1].props.get("children")  # "project_id = <pid>"
        pid = (txt or "").split("=")[1].strip()
        api.delete_project(pid)
        return "reload"
    except Exception:
        return no_update