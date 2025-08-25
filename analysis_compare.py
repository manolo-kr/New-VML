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

PREFERRED = ["auc", "accuracy", "f1", "precision", "recall", "logloss", "rmse", "mae", "r2"]

layout = dbc.Container([
    dcc.Location(id="cmp-url"),

    dcc.Store(id="cmp-run-ids"),
    dcc.Store(id="cmp-data"),  # {run_id: {...raw...}}

    html.H2("Analysis - Compare"),

    dbc.Card([
        dbc.CardHeader("Select runs"),
        dbc.CardBody([
            html.P("Enter run IDs (comma or newline-separated) or use URL ?run_ids=a,b,c"),
            dcc.Textarea(id="cmp-input", style={"width":"100%", "height":"100px"}, placeholder="e.g.\n64f...a12\n64f...b98"),
            dbc.Button("Load Runs", id="cmp-btn-load", color="primary", className="mt-2"),
        ])
    ], className="mb-3"),

    html.Div(id="cmp-table"),
], fluid=True)

@callback(
    Output("cmp-run-ids","data"),
    Input("cmp-url","href"),
    prevent_initial_call=False
)
def _init_from_url(href):
    ids: List[str] = []
    if href:
        q = up.urlparse(href).query
        params = dict(up.parse_qsl(q, keep_blank_values=True))
        if "run_ids" in params and params["run_ids"]:
            ids = [t.strip() for t in params["run_ids"].replace("\n", ",").split(",") if t.strip()]
    return ids

@callback(
    Output("cmp-run-ids", "data", allow_duplicate=True),
    Input("cmp-btn-load", "n_clicks"),
    State("cmp-input", "value"),
    prevent_initial_call=True
)
def _load_from_text(_n, val):
    if not val:
        return no_update
    ids = [t.strip() for t in val.replace("\n", ",").split(",") if t.strip()]
    return ids

@callback(
    Output("cmp-data", "data"),
    Input("cmp-run-ids", "data"),
    prevent_initial_call=True
)
def _fetch_runs(ids):
    out: Dict[str, Any] = {}
    for rid in ids or []:
        try:
            out[rid] = api.get_run(rid)
        except Exception:
            out[rid] = {"id": rid, "status": "error", "message": "fetch failed"}
    return out

def _metric_val(metrics: Dict[str, Any], key: str) -> str:
    if key not in metrics:
        return "-"
    v = metrics[key]
    try:
        return f"{float(v):.6g}"
    except Exception:
        return str(v)

@callback(
    Output("cmp-table", "children"),
    Input("cmp-data", "data"),
)
def _render_table(data):
    data = data or {}
    if not data:
        return dbc.Alert("No runs loaded.", color="light", className="py-2")

    # 헤더(대표 메트릭)
    cols_fixed = ["Run ID", "Model", "Type", "File", "Status"]
    cols_metrics = PREFERRED[:]  # 순서 고정
    header = html.Thead(html.Tr([html.Th(c) for c in cols_fixed + cols_metrics + ["Results"]]))

    # 행
    rows = []
    for rid, run in data.items():
        task_ref = (run or {}).get("task_ref") or {}
        model = task_ref.get("model_family") or "-"
        ttype = task_ref.get("task_type") or "-"
        fname = (run or {}).get("dataset_original_name") or "-"
        status = (run or {}).get("status") or "-"
        metrics = (run or {}).get("metrics") or {}
        fixed = [rid, model, ttype, fname, status]
        metric_vals = [_metric_val(metrics, k) for k in cols_metrics]
        link = dcc.Link("Open", href=f"/analysis/results?run_id={rid}&model={model}") if rid != "-" else html.Span("-")
        row = html.Tr([html.Td(v) for v in fixed + metric_vals] + [html.Td(link)])
        rows.append(row)

    table = dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, responsive=True, className="align-middle")
    return html.Div(table)