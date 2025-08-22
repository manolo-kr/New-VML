# backend/app/ui/pages/home.py

from __future__ import annotations
from typing import List, Dict, Any

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/", name="Home")

layout = dbc.Container([
    dcc.Store(id="home-projects"),           # [{id,name,created_at}, ...]
    dcc.Store(id="home-refresh", data=0),    # 강제 리프레시 트리거
    dcc.Store(id="gs-auth", storage_type="session"),      # 전역 (app.py에서도 생성)
    dcc.Store(id="gs-project", storage_type="session"),   # 전역 (선택된 프로젝트)

    html.H2("Projects"),

    # Create row (상단 고정)
    dbc.Row([
        dbc.Col(dbc.Input(id="home-new-name", placeholder="New project name", type="text"), md=4),
        dbc.Col(dbc.Button("Create", id="home-btn-create", color="primary"), width="auto"),
        dbc.Col(html.Div(id="home-alert"), md=6),
    ], className="g-2 mb-3"),

    # List
    html.Div(id="home-list"),
], fluid=True)


# ---- Load list ------------------------------------------------------
@callback(
    Output("home-projects", "data"),
    Input("home-refresh", "data"),
    State("gs-auth", "data"),
    prevent_initial_call=False
)
def _load_projects(_n, auth):
    token = (auth or {}).get("access_token")
    try:
        projs = api.list_projects(token)
        return projs
    except Exception as e:
        return []


# ---- Render list ----------------------------------------------------
@callback(
    Output("home-list", "children"),
    Input("home-projects", "data"),
)
def _render_list(projs: List[Dict[str, Any]]):
    projs = projs or []
    if not projs:
        return dbc.Alert("No projects yet. Create one above.", color="secondary")

    rows = []
    for p in projs:
        rows.append(
            dbc.ListGroupItem(
                dbc.Row([
                    dbc.Col(html.Div([html.B(p["name"]), html.Small(f"  (id={p['id']})", className="text-muted")] ), md=6),
                    dbc.Col(
                        dbc.ButtonGroup([
                            dcc.Link(dbc.Button("Open", color="info", outline=True, size="sm"),
                                     href=f"/analysis/design?project_id={p['id']}"),
                            dbc.Button("Delete", id={"type":"home-del", "pid":p["id"]}, color="danger", outline=True, size="sm"),
                        ]),
                        md=6, className="text-end"
                    ),
                ], className="align-items-center"),
            )
        )
    return dbc.ListGroup(rows, flush=True)


# ---- Create project -------------------------------------------------
@callback(
    Output("home-alert", "children"),
    Output("home-new-name", "value"),
    Output("home-refresh", "data"),
    Input("home-btn-create", "n_clicks"),
    State("home-new-name", "value"),
    State("home-refresh", "data"),
    State("gs-auth", "data"),
    prevent_initial_call=True
)
def _create(_n, name, refresh, auth):
    token = (auth or {}).get("access_token")
    if not name:
        return dbc.Alert("Enter a project name.", color="warning"), no_update, no_update
    try:
        api.create_project(name, token)
        return dbc.Alert("Created!", color="success"), "", (refresh or 0) + 1
    except Exception as e:
        return dbc.Alert(f"Create failed: {e}", color="danger"), no_update, no_update


# ---- Delete project (pattern-matching IDs) --------------------------
@callback(
    Output("home-refresh", "data"),
    Input({"type":"home-del","pid":dash.ALL}, "n_clicks"),
    State("home-refresh", "data"),
    State("home-projects", "data"),
    State("gs-auth", "data"),
    prevent_initial_call=True
)
def _delete(n_clicks_list, refresh, projs, auth):
    token = (auth or {}).get("access_token")
    if not n_clicks_list or not projs:
        return no_update
    # 어떤 버튼이 눌렸는지 식별
    ctx = dash.ctx.triggered_id
    if isinstance(ctx, dict) and ctx.get("type") == "home-del":
        pid = ctx.get("pid")
        try:
            api.delete_project(pid, token)
            return (refresh or 0) + 1
        except Exception:
            return no_update
    return no_update