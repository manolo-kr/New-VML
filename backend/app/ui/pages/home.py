# backend/app/ui/pages/home.py

import json
import urllib.parse as up
from typing import Any, Dict, List

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/", name="Home")

layout = dbc.Container([
    dcc.Store(id="home-projects"),
    dcc.Store(id="home-delete-id"),

    html.H3("Projects"),

    dbc.Row([
        dbc.Col(dbc.Input(id="home-new-name", placeholder="New project name", type="text"), md=6),
        dbc.Col(dbc.Button("Create", id="home-btn-create", color="primary"), width="auto"),
    ], className="g-2 mb-3"),

    html.Div(id="home-alert"),
    html.Div(id="home-list"),
], fluid=True)


def _row(proj: Dict[str, Any]):
    return html.Tr([
        html.Td(proj["id"]),
        html.Td(proj["name"]),
        html.Td(proj.get("created_at", "-")),
        html.Td(dbc.Button("Open", id={"t":"home-open","id":proj["id"]}, size="sm", color="info")),
        html.Td(dbc.Button("Delete", id={"t":"home-del","id":proj["id"]}, size="sm", color="danger", outline=True)),
    ])


@callback(
    Output("home-projects", "data"),
    Output("home-alert", "children"),
    Input("gs-auth", "data"),
    prevent_initial_call=False
)
def _load_projects(auth):
    if not auth or not auth.get("access_token"):
        return [], no_update
    try:
        projs = api.list_projects(token=auth["access_token"])
        return projs, no_update
    except Exception as e:
        return [], dbc.Alert(f"Failed to load projects: {e}", color="danger")


@callback(
    Output("home-projects", "data"),
    Output("home-new-name", "value"),
    Output("home-alert", "children"),
    Input("home-btn-create", "n_clicks"),
    State("home-new-name", "value"),
    State("gs-auth", "data"),
    State("home-projects", "data"),
    prevent_initial_call=True
)
def _create(_n, name, auth, projects):
    if not _n:
        return no_update, no_update, no_update
    if not auth or not auth.get("access_token"):
        return no_update, no_update, dbc.Alert("Please login", color="warning")
    if not (name and name.strip()):
        return no_update, no_update, dbc.Alert("Project name required", color="warning")
    try:
        p = api.create_project(name.strip(), token=auth["access_token"])
        lst = [p] + (projects or [])
        return lst, "", dbc.Alert("Project created", color="success")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Create failed: {e}", color="danger")


@callback(
    Output("home-delete-id", "data"),
    Input({"t":"home-del","id":dash.dependencies.ALL}, "n_clicks"),
    State("home-projects", "data"),
    prevent_initial_call=True
)
def _on_del_click(_clicks, projects):
    trig = dash.ctx.triggered_id
    if isinstance(trig, dict) and trig.get("t") == "home-del":
        return trig.get("id")
    return no_update


@callback(
    Output("home-projects", "data"),
    Output("home-alert", "children"),
    Input("home-delete-id", "data"),
    State("home-projects", "data"),
    State("gs-auth", "data"),
    prevent_initial_call=True
)
def _delete_one(pid, projects, auth):
    if not pid:
        return no_update, no_update
    if not auth or not auth.get("access_token"):
        return no_update, dbc.Alert("Please login", color="warning")
    try:
        api.delete_project(pid, token=auth["access_token"])
        remain = [p for p in (projects or []) if p["id"] != pid]
        return remain, dbc.Alert("Project deleted", color="success")
    except Exception as e:
        return no_update, dbc.Alert(f"Delete failed: {e}", color="danger")


@callback(
    Output("gs-project", "data"),
    Output("_auth_redirect", "href"),
    Input({"t":"home-open","id":dash.dependencies.ALL}, "n_clicks"),
    State("home-projects", "data"),
    prevent_initial_call=True
)
def _open(_clicks, projects):
    trig = dash.ctx.triggered_id
    if isinstance(trig, dict) and trig.get("t") == "home-open":
        pid = trig.get("id")
        p = next((x for x in (projects or []) if x["id"] == pid), None)
        if p:
            return {"id": p["id"], "name": p["name"]}, "/analysis/design"
    return no_update, no_update


@callback(
    Output("home-list", "children"),
    Input("home-projects", "data"),
)
def _render_list(projects):
    header = html.Thead(html.Tr([
        html.Th("ID"), html.Th("Name"), html.Th("Created"), html.Th("Open"), html.Th("Delete")
    ]))
    rows = [_row(p) for p in (projects or [])]
    return dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, responsive=True, className="align-middle")