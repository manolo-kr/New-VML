# backend/app/ui/pages/home.py

from __future__ import annotations
from typing import Any, Dict, List
import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ALL
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/", name="Home")

layout = dbc.Container([
    dcc.Store(id="home-projects"),
    dcc.Store(id="home-delete-inbox"),  # 삭제 버튼 신호만 담는 인박스 (API 호출은 메인 콜백에서)
    html.H2("Projects"),
    dbc.Row([
        dbc.Col(dbc.Input(id="home-new-name", placeholder="New project name"), md=4),
        dbc.Col(dbc.Button("Create", id="home-btn-create", color="primary"), width="auto"),
        dbc.Col(html.Div(id="home-alert"), width=True),
    ], className="g-2 mb-2"),
    html.Div(id="home-table"),
], fluid=True)

def _projects_table(items: List[Dict[str, Any]]):
    rows = []
    for p in items or []:
        rows.append(html.Tr([
            html.Td(p["id"]),
            html.Td(p["name"]),
            html.Td(dcc.Link("Open", href=f"/analysis/design?project_id={p['id']}")),
            html.Td(dbc.Button("Delete", id={"type":"home-del","id":p["id"]}, color="danger", outline=True, size="sm")),
        ]))
    return dbc.Table([html.Thead(html.Tr([html.Th("ID"), html.Th("Name"), html.Th("Open"), html.Th("Delete")])),
                      html.Tbody(rows)], bordered=True, hover=True, responsive=True)

# 1) Delete 버튼 → 인박스 세팅(한 콜백만 home-delete-inbox.data 출력)
@callback(
    Output("home-delete-inbox", "data"),
    Input({"type":"home-del","id":ALL}, "n_clicks"),
    prevent_initial_call=True
)
def _delete_inbox(n_clicks_list):
    trig = dash.ctx.triggered_id
    if isinstance(trig, dict) and trig.get("type") == "home-del":
        return {"delete_id": trig.get("id")}
    return no_update

# 2) 프로젝트 로드/생성/삭제 → home-projects.data & home-alert.children & 입력 클리어
#    (home-projects.data는 오직 이 콜백만 출력)
@callback(
    Output("home-projects", "data"),
    Output("home-alert", "children"),
    Output("home-new-name", "value"),
    Input("gs-auth", "data"),
    Input("home-btn-create", "n_clicks"),
    Input("home-delete-inbox", "data"),
    State("home-new-name", "value"),
    prevent_initial_call=True
)
def _mutate_projects(auth, n_create, delete_inbox, new_name):
    token = (auth or {}).get("access_token")
    trig = dash.ctx.triggered_id

    # 현재 목록
    items: List[Dict[str, Any]] = []
    alert = no_update
    clear_val = no_update

    def load() -> List[Dict[str, Any]]:
        try:
            return api.list_projects(token=token)
        except Exception:
            return []

    # 최초 로그인/리프레시/일반 로드
    if trig == "gs-auth":
        items = load()
        return items, no_update, no_update

    # 생성
    if trig == "home-btn-create":
        if not (new_name and new_name.strip()):
            return no_update, dbc.Alert("Enter a project name.", color="warning", className="py-2"), no_update
        try:
            api.create_project(new_name.strip(), token=token)
            items = load()
            alert = dbc.Alert("Project created.", color="success", className="py-2")
            clear_val = ""
        except Exception as e:
            alert = dbc.Alert(f"Create failed: {e}", color="danger", className="py-2")
            items = load()
        return items, alert, clear_val

    # 삭제
    if trig == "home-delete-inbox" and delete_inbox and delete_inbox.get("delete_id"):
        try:
            api.delete_project(delete_inbox["delete_id"], token=token)
            items = load()
            alert = dbc.Alert("Project deleted.", color="secondary", className="py-2")
        except Exception as e:
            alert = dbc.Alert(f"Delete failed: {e}", color="danger", className="py-2")
            items = load()
        return items, alert, no_update

    # 기타
    items = load()
    return items, alert, clear_val

# 3) 테이블 렌더 (읽기 전용)
@callback(
    Output("home-table", "children"),
    Input("home-projects", "data"),
)
def _render_table(items):
    return _projects_table(items or [])