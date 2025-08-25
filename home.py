# backend/app/ui/pages/home.py

from __future__ import annotations
from typing import List, Dict, Any
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from app.ui.clients import api_client as api

dash.register_page(__name__, path="/", name="Home")

def _project_row(p: Dict[str, Any]) -> html.Tr:
    return html.Tr([
        html.Td(p["name"]),
        html.Td(p["id"]),
        html.Td(dbc.Button("Open", id={"type": "proj-open", "pid": p["id"]}, color="primary", size="sm")),
        html.Td(dbc.Button("Delete", id={"type": "proj-del", "pid": p["id"]}, color="danger", size="sm", outline=True)),
    ])

layout = dbc.Container([
    dcc.Store(id="home-projects"),
    dcc.Location(id="home-url"),

    html.H3("Projects"),
    dbc.Row([
        dbc.Col(dbc.Input(id="new-proj-name", placeholder="New project name", type="text"), md=4),
        dbc.Col(dbc.Button("Create", id="btn-create-proj", color="success"), width="auto")
    ], className="g-2 mb-3"),

    html.Div(id="proj-alert-area", className="mb-2"),

    html.Div(id="proj-table-wrapper"),
], fluid=True)

@callback(
    Output("home-projects", "data"),
    Input("home-url", "href"),
    Input("btn-create-proj", "n_clicks"),
    State("new-proj-name", "value"),
    prevent_initial_call=False
)
def _load_or_create(_href, n_create, name):
    trig = dash.ctx.triggered_id
    if trig == "btn-create-proj" and name:
        try:
            api.create_project(name.strip())
        except Exception as e:
            return dash.no_update
    try:
        return api.list_projects()
    except Exception:
        return []

@callback(
    Output("proj-table-wrapper", "children"),
    Input("home-projects", "data"),
)
def _render_table(projects):
    projects = projects or []
    if not projects:
        return dbc.Alert("No projects. Create one!", color="secondary")
    header = html.Thead(html.Tr([html.Th("Name"), html.Th("ID"), html.Th("Open"), html.Th("Delete")]))
    rows = [ _project_row(p) for p in projects ]
    return dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, responsive=True, className="align-middle")

@callback(
    Output("proj-alert-area", "children"),
    Output("home-url", "href"),
    Input({"type": "proj-open", "pid": dash.ALL}, "n_clicks"),
    Input({"type": "proj-del", "pid": dash.ALL}, "n_clicks"),
    State("home-projects", "data"),
    prevent_initial_call=True
)
def _open_or_delete(open_clicks, del_clicks, projects):
    trig = dash.ctx.triggered_id
    if isinstance(trig, dict) and trig.get("type") == "proj-open":
        pid = trig.get("pid")
        # 바로 Design으로 이동
        return no_update, f"/analysis/design?project_id={pid}"
    if isinstance(trig, dict) and trig.get("type") == "proj-del":
        pid = trig.get("pid")
        try:
            api.delete_project(pid)
            # 삭제 후 새로고침
            return dbc.Alert(f"Deleted project: {pid}", color="success", duration=2000), "/"
        except Exception as e:
            return dbc.Alert(f"Delete failed: {e}", color="danger", duration=4000), no_update
    return no_update, no_update