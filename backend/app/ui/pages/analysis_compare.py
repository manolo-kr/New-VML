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
    dcc.Store(id="compare-run-ids"),
    dcc.Store(id="compare-models"),  # {run_id: model_key}

    html.H3("Compare runs"),

    dbc.Row([
        dbc.Col(dbc.Input(id="compare-runs-input", placeholder="Comma-separated run_ids", type="text"), md=6),
        dbc.Col(dbc.Button("Load", id="compare-load", color="primary"), width="auto"),
    ], className="g-2 mb-3"),

    html.Div(id="compare-banner"),
    html.Div(id="compare-table"),
], fluid=True)


@callback(
    Output("compare-runs-input", "value"),
    Output("compare-run-ids", "data"),
    Input("compare-url", "href"),
    prevent_initial_call=False
)
def _init(href):
    if not href:
        return no_update, no_update
    q = up.urlparse(href).query
    params = dict(up.parse_qsl(q, keep_blank_values=True))
    runs = []
    if "run_ids" in params and params["run_ids"]:
        runs = [x for x in params["run_ids"].split(",") if x]
    return ",".join(runs), runs


@callback(
    Output("compare-run-ids", "data"),
    Input("compare-load", "n_clicks"),
    State("compare-runs-input", "value"),
    prevent_initial_call=True
)
def _load(_n, s):
    if not s:
        return no_update
    runs = [x.strip() for x in s.split(",") if x.strip()]
    return runs


@callback(
    Output("compare-banner", "children"),
    Input("compare-run-ids", "data")
)
def _banner(runs):
    if not runs:
        return dbc.Alert("Enter run IDs above.", color="secondary", className="py-2")
    return no_update


@callback(
    Output("compare-table", "children"),
    Input("compare-run-ids", "data"),
    State("gs-auth", "data")
)
def _render(runs, auth):
    runs = runs or []
    if not runs:
        return no_update
    token = (auth or {}).get("access_token")

    rows = []
    for rid in runs:
        try:
            run = api.get_run(rid, token=token)
        except Exception:
            run = {}
        status = run.get("status", "-")
        model = (run.get("task_ref") or {}).get("model_family", "-")
        ttype = (run.get("task_ref") or {}).get("task_type", "-")
        fname = run.get("dataset_original_name") or "-"
        # 핵심 메트릭(예: auc, acc 등 요약)
        try:
            summary = api.get_artifact_json(rid, f"models/{model}/metrics/summary.json", token=token) if model and model != "-" else {}
        except Exception:
            summary = {}
        core = ", ".join(f"{k}={v}" for k, v in (summary or {}).items())
        rows.append(html.Tr([
            html.Td(rid),
            html.Td(model), html.Td(ttype), html.Td(fname), html.Td(status),
            html.Td(core or "-"),
            html.Td(dcc.Link("Open", href=f"/analysis/results?run_id={rid}")),
        ]))

    header = html.Thead(html.Tr([html.Th("Run ID"), html.Th("Model"), html.Th("Type"),
                                 html.Th("File"), html.Th("Status"), html.Th("Summary"), html.Th("Results")]))
    return dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, responsive=True, className="align-middle")