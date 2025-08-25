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
    dcc.Store(id="compare-models"),

    html.H2("Compare runs"),

    dbc.Row([
        dbc.Col(dbc.InputGroup([
            dbc.InputGroupText("Run IDs (comma)"),
            dbc.Input(id="compare-input-ids", placeholder="rid1,rid2,..."),
            dbc.Button("Load", id="compare-load", color="primary")
        ]), md=8),
        dbc.Col(dbc.InputGroup([
            dbc.InputGroupText("Model (optional)"),
            dbc.Input(id="compare-input-model", placeholder="xgboost"),
        ]), md=4),
    ], className="g-2 mb-3"),

    html.Div(id="compare-table"),
], fluid=True)

@callback(
    Output("compare-run-ids","data"),
    Output("compare-models","data"),
    Input("compare-url","href"),
    prevent_initial_call=False
)
def _init_from_url(href):
    if not href:
        return [], None
    q = up.urlparse(href).query
    params = dict(up.parse_qsl(q, keep_blank_values=True))
    rids = [r for r in (params.get("run_ids") or "").split(",") if r]
    model = params.get("model")
    return rids, model

@callback(
    Output("compare-run-ids","data", allow_duplicate=True),
    Output("compare-models","data", allow_duplicate=True),
    Input("compare-load","n_clicks"),
    State("compare-input-ids","value"),
    State("compare-input-model","value"),
    prevent_initial_call=True
)
def _manual(n, ids, model):
    if not ids:
        return no_update, no_update
    rids = [r.strip() for r in ids.split(",") if r.strip()]
    return rids, (model or "").strip() or None

@callback(
    Output("compare-table","children"),
    Input("compare-run-ids","data"),
    Input("compare-models","data"),
)
def _render_table(run_ids, model_key):
    run_ids = run_ids or []
    if not run_ids:
        return dbc.Alert("Enter run ids to compare.", color="secondary")

    rows = []
    header = html.Thead(html.Tr([
        html.Th("Run ID"),
        html.Th("Model"),
        html.Th("Metric (AUC/F1/RMSE)"),
        html.Th("Status"),
        html.Th("Open"),
    ]))

    for rid in run_ids:
        try:
            info = api.get_run(rid)
        except Exception:
            info = {}
        tf = (info.get("task_ref") or {})
        model = model_key or tf.get("model_family") or "-"
        status = info.get("status") or "-"
        # 간단히 auc/f1/rmse 중 존재하는 것 하나 선택
        metric_show = "-"
        try:
            m = api.get_artifact_json(rid, f"models/{model}/metrics/metrics.json")
            for k in ["auc","f1","rmse","mae","accuracy"]:
                if k in m:
                    metric_show = f"{k}: {m[k]}"
                    break
        except Exception:
            pass
        open_link = dcc.Link("Results", href=f"/analysis/results?run_id={rid}&model={model}")
        rows.append(html.Tr([
            html.Td(rid),
            html.Td(model),
            html.Td(metric_show),
            html.Td(status),
            html.Td(open_link),
        ]))
    return dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, responsive=True)