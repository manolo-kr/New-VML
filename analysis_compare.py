# backend/app/ui/pages/analysis_compare.py

from __future__ import annotations
from typing import List, Dict, Any
import urllib.parse as up
import json

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/compare", name="Compare")

layout = dbc.Container([
    dcc.Location(id="compare-url"),
    dcc.Store(id="gs-auth", storage_type="session"),

    html.H2("Compare Runs"),

    dbc.Row([
        dbc.Col(dbc.Textarea(id="compare-run-ids", placeholder="Enter run IDs (comma-separated)"), md=8),
        dbc.Col(dbc.Button("Load", id="compare-load", color="primary"), width="auto"),
    ], className="g-2 mb-3"),

    html.Div(id="compare-table"),
], fluid=True)


@callback(
    Output("compare-run-ids","value"),
    Input("compare-url","href"),
    prevent_initial_call=False
)
def _init_ids(href):
    if not href:
        return ""
    q = up.urlparse(href).query
    p = dict(up.parse_qsl(q))
    return p.get("run_ids","")


@callback(
    Output("compare-table","children"),
    Input("compare-load","n_clicks"),
    State("compare-run-ids","value"),
    State("gs-auth","data"),
    prevent_initial_call=True
)
def _load(_n, run_ids_raw, auth):
    token = (auth or {}).get("access_token")
    if not run_ids_raw:
        return dbc.Alert("Enter run IDs first.", color="warning")
    run_ids = [r.strip() for r in run_ids_raw.split(",") if r.strip()]
    if not run_ids:
        return dbc.Alert("No valid run IDs.", color="warning")

    rows = []
    for rid in run_ids:
        try:
            info = api.get_run(rid, token)
            status = info.get("status")
            tf = info.get("task_ref") or {}
            model = tf.get("model_family", "-")
            ttype = tf.get("task_type", "-")
            fname = info.get("dataset_original_name", "-")
            # 간단 메트릭 예: auc, rmse 등 (없으면 -)
            auc = (info.get("metrics") or {}).get("auc", "-")
            rmse = (info.get("metrics") or {}).get("rmse", "-")
        except Exception:
            model = ttype = fname = auc = rmse = "-"
            status = "error"

        rows.append(html.Tr([
            html.Td(rid),
            html.Td(model),
            html.Td(ttype),
            html.Td(fname),
            html.Td(str(auc)),
            html.Td(str(rmse)),
            html.Td(dcc.Link("Open", href=f"/analysis/results?run_id={rid}", target="_blank")),
            html.Td(status),
        ]))

    head = html.Thead(html.Tr([
        html.Th("Run ID"),
        html.Th("Model"),
        html.Th("Type"),
        html.Th("File"),
        html.Th("AUC"),
        html.Th("RMSE"),
        html.Th("Results"),
        html.Th("Status"),
    ]))
    return dbc.Table([head, html.Tbody(rows)], bordered=True, hover=True, responsive=True, className="align-middle")