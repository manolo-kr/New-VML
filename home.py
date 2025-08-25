# backend/app/ui/pages/home.py

from __future__ import annotations
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from app.ui.clients import api_client as api

dash.register_page(__name__, path="/", name="Home")

layout = dbc.Container([
    dcc.Store(id="gs-auth", storage_type="session"),
    dcc.Store(id="gs-project", storage_type="session"),

    html.H3("Projects"),
    dbc.Row([
        dbc.Col(dbc.Input(id="proj-name", placeholder="New project name", type="text"), md=6),
        dbc.Col(dbc.Button("Create", id="btn-proj-create", color="primary"), md="auto"),
    ], className="g-2 mb-3"),

    html.Div(id="proj-list"),
], fluid=True)

@callback(
    Output("proj-list", "children"),
    Input("btn-proj-create", "n_clicks"),
    State("proj-name", "value"),
    prevent_initial_call=True
)
def _create_project(n, name):
    try:
        name = (name or "").strip() or "Project"
        api.create_project(name)
    except Exception:
        pass
    projs = api.list_projects()
    return _render_list(projs)

@callback(
    Output("proj-list", "children", allow_duplicate=True),
    Input("proj-list", "children"),
    prevent_initial_call=False
)
def _init(_):
    projs = api.list_projects()
    return _render_list(projs)

def _render_list(projs):
    rows = []
    for p in projs or []:
        pid = p["id"]
        row = dbc.ListGroupItem([
            html.Div([
                html.Strong(p["name"]),
                html.Span(f"  ({pid})", className="text-muted ms-2"),
            ]),
            dbc.ButtonGroup([
                dcc.Link("Open", href=f"/analysis/design?project_id={pid}", className="btn btn-sm btn-primary"),
                dbc.Button("Delete", id={"type":"btn-del-proj","pid":pid}, size="sm", color="danger", outline=True)
            ], className="mt-1")
        ])
        rows.append(row)
    return dbc.ListGroup(rows, flush=True)

@callback(
    Output("proj-list", "children", allow_duplicate=True),
    Input({"type":"btn-del-proj","pid":dash.ALL}, "n_clicks"),
    State({"type":"btn-del-proj","pid":dash.ALL}, "id"),
    prevent_initial_call=True
)
def _delete_project(n_clicks, ids):
    ctx = dash.ctx
    if not ctx.triggered_id:
        raise dash.exceptions.PreventUpdate
    pid = ctx.triggered_id.get("pid")
    if pid:
        try:
            api.delete_project(pid)
        except Exception:
            pass
    projs = api.list_projects()
    return _render_list(projs)