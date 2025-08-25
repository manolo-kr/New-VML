# backend/app/ui/pages/home.py

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/", name="Home")

layout = dbc.Container([
    dcc.Store(id="home-projects"),
    dbc.Row([
        dbc.Col(dbc.Input(id="home-new-name", placeholder="New project name", type="text"), md=4),
        dbc.Col(dbc.Button("Create", id="home-btn-create", color="primary"), md="auto"),
        dbc.Col(html.Div(id="home-alert"), md=True),
    ], class_name="g-2 mb-4"),
    html.Div(id="home-list"),
], fluid=True)

@callback(
    Output("home-projects", "data"),
    Output("home-new-name", "value"),
    Output("home-alert", "children"),
    Input("home-btn-create", "n_clicks"),
    State("home-new-name", "value"),
    prevent_initial_call=True,
)
def _create_project(n, name):
    if not n:
        return no_update, no_update, no_update
    try:
        nm = (name or "").strip()
        if not nm:
            return no_update, no_update, dbc.Alert("Enter a project name.", color="warning", class_name="py-2")
        api.create_project(nm)  # ← token 인자 제거
        projs = api.list_projects()
        return projs, "", dbc.Alert("Created.", color="success", class_name="py-2")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Create failed: {e}", color="danger", class_name="py-2")

@callback(
    Output("home-list", "children"),
    Input("home-projects", "data"),
    prevent_initial_call=False,
)
def _render_list(_projs):
    try:
        projs = _projs or api.list_projects()
    except Exception as e:
        return dbc.Alert(f"Load projects failed: {e}", color="danger", class_name="py-2")

    if not projs:
        return html.Div("No projects yet.", className="text-muted")

    rows = []
    for p in projs:
        rows.append(
            dbc.ListGroupItem(
                html.Div([
                    html.Div(html.Strong(p["name"])),
                    dcc.Link("Open →", href=f"/analysis/design?project_id={p['id']}"),
                ])
            )
        )
    return dbc.ListGroup(rows, flush=True)