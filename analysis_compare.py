# backend/app/ui/pages/analysis_compare.py

from __future__ import annotations
from typing import List, Dict, Any
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/compare", name="Compare")

# -----------------------
# helpers
# -----------------------
KEY_METRICS = ["accuracy", "auc", "roc_auc", "f1", "precision", "recall", "logloss", "rmse", "mae", "mape"]

def _metric_pick(m: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k in KEY_METRICS:
        if k in m:
            v = m.get(k)
            try:
                if isinstance(v, (int, float)):
                    out[k] = f"{v:.6g}"
                else:
                    out[k] = str(v)
            except Exception:
                out[k] = str(v)
    return out

def _render_table(rows: List[Dict[str, Any]]) -> html.Div:
    if not rows:
        return dbc.Alert("No runs to compare. Enter run IDs and click Load.", color="light", className="py-2")
    # header
    cols = ["Run ID", "Model", "Type", "File", "Status"] + KEY_METRICS
    thead = html.Thead(html.Tr([html.Th(c) for c in cols]))
    tb_rows = []
    for r in rows:
        cells = [
            html.Td(html.Code(r.get("id","-"))),
            html.Td(r.get("model","-")),
            html.Td(r.get("task_type","-")),
            html.Td(r.get("file","-")),
            html.Td(r.get("status","-")),
        ]
        for k in KEY_METRICS:
            cells.append(html.Td(r.get(k, "-")))
        tb_rows.append(html.Tr(cells))
    return dbc.Table([thead, html.Tbody(tb_rows)], bordered=True, hover=True, responsive=True, className="align-middle")

# -----------------------
# layout
# -----------------------
layout = dbc.Container([
    dcc.Location(id="compare-url"),

    html.H2("Analysis - Compare"),

    dbc.Card([
        dbc.CardHeader("Select runs"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Textarea(id="compare-run-ids", placeholder="Enter run IDs separated by commas", rows=3), md=7),
                dbc.Col(dbc.Button("Load", id="btn-compare-load", color="primary"), md="auto"),
            ], className="g-2"),
            html.Small("Tip: You can paste a list like: 64f2...,7d09...,a321...", className="text-muted")
        ])
    ], className="mb-3"),

    html.Div(id="compare-table"),
], fluid=True)

# -----------------------
# callbacks
# -----------------------

# 1) URL → run_ids 초기화 (?runs=id1,id2,...)
@callback(
    Output("compare-run-ids", "value"),
    Input("compare-url", "href"),
    prevent_initial_call=False
)
def _init_from_url(href):
    if not href:
        return ""
    q = up.urlparse(href).query
    params = dict(up.parse_qsl(q, keep_blank_values=True))
    runs = params.get("runs") or ""
    return runs

# 2) Load → 비교 테이블 작성
@callback(
    Output("compare-table", "children"),
    Input("btn-compare-load", "n_clicks"),
    State("compare-run-ids", "value"),
    prevent_initial_call=True
)
def _load_compare(_n, raw):
    run_ids = [r.strip() for r in (raw or "").split(",") if r.strip()]
    rows = []
    for rid in run_ids:
        try:
            info = api.get_run(rid)
        except Exception:
            continue
        task_ref = info.get("task_ref") or {}
        model = task_ref.get("model_family") or "-"
        ttype = task_ref.get("task_type") or "-"
        fname = info.get("dataset_original_name") or "-"
        status = info.get("status") or "-"
        metrics = info.get("metrics") or {}
        picks = _metric_pick(metrics)
        row = {"id": rid, "model": model, "task_type": ttype, "file": fname, "status": status, **picks}
        rows.append(row)
    return _render_table(rows)