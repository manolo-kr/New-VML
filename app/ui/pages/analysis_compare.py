# backend/app/ui/pages/analysis_compare.py

from __future__ import annotations
from typing import List, Dict, Any
import urllib.parse as up
import json

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/compare", name="Compare")

layout = dbc.Container([
    dcc.Location(id="compare-url"),
    dcc.Store(id="compare-run-ids"),
    html.H3("Compare Runs"),

    dbc.Row([
        dbc.Col(dbc.Input(id="compare-input", placeholder="Comma-separated run_ids", type="text"), md=6),
        dbc.Col(dbc.Button("Load", id="compare-load", color="primary"), width="auto"),
    ], className="g-2 mb-3"),

    html.Div(id="compare-table"),
], fluid=True)

@callback(
    Output("compare-run-ids", "data"),
    Input("compare-url", "href"),
    prevent_initial_call=False
)
def _init(href):
    if not href:
        return []
    q = up.urlparse(href).query
    params = dict(up.parse_qsl(q))
    ids = params.get("run_ids", "")
    return [x for x in ids.split(",") if x]

@callback(
    Output("compare-table", "children"),
    Input("compare-load", "n_clicks"),
    State("compare-input", "value"),
    State("compare-run-ids", "data"),
    prevent_initial_call=True
)
def _load(_n, txt, rid_list):
    ids = [x.strip() for x in (txt or "").split(",") if x.strip()] or (rid_list or [])
    if not ids:
        return dbc.Alert("Enter run_ids.", color="secondary")

    rows = []
    header = html.Thead(html.Tr([html.Th(x) for x in ["Run ID", "Model", "Type", "AUC", "ACC", "F1", "Status"]]))
    for rid in ids:
        try:
            info = api.get_run(rid)
        except Exception:
            info = {}
        ref = info.get("task_ref") or {}
        m = ref.get("model_family", "-")
        t = ref.get("task_type", "-")
        met = (info.get("metrics") or {})
        rows.append(html.Tr([
            html.Td(rid),
            html.Td(m),
            html.Td(t),
            html.Td(met.get("auc","-")),
            html.Td(met.get("accuracy","-")),
            html.Td(met.get("f1","-")),
            html.Td(info.get("status","-")),
        ]))
    return dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, responsive=True)
