# backend/app/ui/pages/analysis_compare.py

from __future__ import annotations
from typing import List, Dict, Any
import json
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/compare", name="Compare")

layout = dbc.Container([
    dcc.Location(id="compare-url"),
    dcc.Store(id="compare-run-ids"),       # 유일 작성 스토어
    dcc.Store(id="compare-patch"),         # 추가/삭제 인박스

    html.H2("Compare Runs"),
    dbc.Row([
        dbc.Col(dbc.Input(id="compare-add-run", placeholder="Run ID to add"), md=6),
        dbc.Col(dbc.Button("Add", id="compare-btn-add", color="primary"), width="auto"),
        dbc.Col(dbc.Button("Clear", id="compare-btn-clear", color="secondary", outline=True), width="auto"),
    ], className="g-2 mb-2"),

    html.Div(id="compare-table"),
], fluid=True)

# 0) Add/Clear → patch (compare-patch만 출력)
@callback(
    Output("compare-patch", "data"),
    Input("compare-btn-add", "n_clicks"),
    Input("compare-btn-clear", "n_clicks"),
    State("compare-add-run", "value"),
    prevent_initial_call=True
)
def _patch(n_add, n_clear, value):
    trig = dash.ctx.triggered_id
    if trig == "compare-btn-add" and value:
        return {"op":"add","run_id":value.strip()}
    if trig == "compare-btn-clear":
        return {"op":"clear"}
    return no_update

# 1) URL + patch → compare-run-ids.data (유일 작성)
@callback(
    Output("compare-run-ids", "data"),
    Input("compare-url", "href"),
    Input("compare-patch", "data"),
    State("compare-run-ids", "data"),
    prevent_initial_call=False
)
def _set_run_ids(href, patch, current):
    runs: List[str] = list(current or [])
    if dash.ctx.triggered_id == "compare-url":
        if href:
            q = up.urlparse(href).query
            params = dict(up.parse_qsl(q, keep_blank_values=True))
            if "run_ids" in params and params["run_ids"]:
                runs = [r for r in params["run_ids"].split(",") if r]
            else:
                runs = []
        return runs
    # patch
    if patch:
        op = patch.get("op")
        if op == "add" and patch.get("run_id"):
            rid = patch["run_id"]
            if rid not in runs:
                runs.append(rid)
        elif op == "clear":
            runs = []
    return runs

# 2) 테이블 렌더
@callback(
    Output("compare-table", "children"),
    Input("compare-run-ids", "data"),
    State("gs-auth", "data"),
)
def _render_table(run_ids, auth):
    token = (auth or {}).get("access_token")
    run_ids = run_ids or []
    if not run_ids:
        return dbc.Alert("Add run IDs to compare.", color="secondary")
    rows = []
    for rid in run_ids:
        try:
            info = api.get_run(rid, token=token)
            task = info.get("task_ref") or {}
            rows.append(html.Tr([
                html.Td(rid),
                html.Td(task.get("model_family") or "-"),
                html.Td(task.get("task_type") or "-"),
                html.Td(info.get("status") or "-"),
                html.Td(dcc.Link("View", href=f"/analysis/results?run_id={rid}")),
            ]))
        except Exception:
            rows.append(html.Tr([html.Td(rid), html.Td("-", colSpan=4)]))
    table = dbc.Table([html.Thead(html.Tr([html.Th("Run ID"), html.Th("Model"), html.Th("Type"), html.Th("Status"), html.Th("Results")])),
                       html.Tbody(rows)], bordered=True, hover=True, responsive=True)
    return table