# backend/app/ui/pages/analysis_results.py

from __future__ import annotations
from typing import Dict, Any, List
import json
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/results", name="Results")

layout = dbc.Container([
    dcc.Location(id="results-url"),
    dcc.Store(id="results-run-id"),
    dcc.Store(id="results-model-key"),

    html.H2("Results"),

    dbc.Row([
        dbc.Col(dbc.InputGroup([
            dbc.InputGroupText("Run ID"),
            dbc.Input(id="results-run-input", placeholder="Enter run id", type="text"),
            dbc.Button("Load", id="results-load", color="primary")
        ]), md=8),
        dbc.Col(dbc.InputGroup([
            dbc.InputGroupText("Model"),
            dbc.Input(id="results-model-input", placeholder="e.g. xgboost", type="text"),
        ]), md=4),
    ], className="g-2 mb-3"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Metrics"),
            dbc.CardBody(html.Div(id="results-metrics"))
        ]), md=4),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Threshold sweep"),
            dbc.CardBody(dcc.Graph(id="results-thres-graph"))
        ]), md=8)
    ], className="g-2 mb-3"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Curves"),
            dbc.CardBody(dcc.Graph(id="results-roc-graph"))
        ]), md=6),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Confusion"),
            dbc.CardBody(dcc.Graph(id="results-cm-graph"))
        ]), md=6),
    ], className="g-2 mb-3"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("KS / Gain / Lift"),
            dbc.CardBody(dcc.Graph(id="results-ks-graph"))
        ]))
    ])
], fluid=True)

# URL → Store
@callback(
    Output("results-run-id","data"),
    Output("results-model-key","data"),
    Input("results-url","href"),
    prevent_initial_call=False
)
def _init_from_url(href):
    if not href:
        return None, None
    q = up.urlparse(href).query
    params = dict(up.parse_qsl(q, keep_blank_values=True))
    return params.get("run_id"), params.get("model")

# Load 버튼 → 입력 상자 → store 덮기
@callback(
    Output("results-run-id","data", allow_duplicate=True),
    Output("results-model-key","data", allow_duplicate=True),
    Input("results-load","n_clicks"),
    State("results-run-input","value"),
    State("results-model-input","value"),
    prevent_initial_call=True
)
def _manual_load(n, run_id, model):
    if not run_id:
        return no_update, no_update
    return run_id.strip(), (model or "").strip() or None

# Store → 결과 렌더
@callback(
    Output("results-metrics","children"),
    Output("results-thres-graph","figure"),
    Output("results-roc-graph","figure"),
    Output("results-cm-graph","figure"),
    Output("results-ks-graph","figure"),
    Input("results-run-id","data"),
    Input("results-model-key","data"),
)
def _render(run_id, model_key):
    if not run_id or not model_key:
        msg = dbc.Alert("Select a run and model to view results.", color="secondary")
        return msg, go.Figure(), go.Figure(), go.Figure(), go.Figure()

    # metrics.json
    try:
        m = api.get_artifact_json(run_id, f"models/{model_key}/metrics/metrics.json")
    except Exception:
        m = {}
    metrics_list = []
    for k, v in (m or {}).items():
        metrics_list.append(html.Div(f"{k}: {v}"))
    metrics_dom = html.Div(metrics_list) if metrics_list else html.Small("No metrics.", className="text-muted")

    # threshold_sweep.json
    try:
        sweep = api.get_artifact_json(run_id, f"models/{model_key}/metrics/threshold_sweep.json")
    except Exception:
        sweep = None
    thres_fig = go.Figure()
    if isinstance(sweep, dict) and "thresholds" in sweep and "tpr" in sweep and "fpr" in sweep:
        thres_fig.add_trace(go.Scatter(x=sweep["thresholds"], y=sweep["tpr"], mode="lines", name="TPR"))
        thres_fig.add_trace(go.Scatter(x=sweep["thresholds"], y=sweep["fpr"], mode="lines", name="FPR"))
        thres_fig.update_layout(margin=dict(l=10,r=10,t=10,b=10))

    # roc.json
    try:
        roc = api.get_artifact_json(run_id, f"models/{model_key}/curves/roc.json")
    except Exception:
        roc = None
    roc_fig = go.Figure()
    if isinstance(roc, dict) and "fpr" in roc and "tpr" in roc:
        roc_fig.add_trace(go.Scatter(x=roc["fpr"], y=roc["tpr"], mode="lines", name="ROC"))
        roc_fig.add_trace(go.Scatter(x=[0,1], y=[0,1], mode="lines", name="random", line=dict(dash="dash")))
        roc_fig.update_layout(margin=dict(l=10,r=10,t=10,b=10))

    # confusion.json
    try:
        cm = api.get_artifact_json(run_id, f"models/{model_key}/confusion/confusion.json")
    except Exception:
        cm = None
    cm_fig = go.Figure()
    if isinstance(cm, dict) and "matrix" in cm and "labels" in cm:
        z = cm["matrix"]
        cm_fig.add_trace(go.Heatmap(z=z, x=cm["labels"], y=cm["labels"], showscale=True))
        cm_fig.update_layout(margin=dict(l=10,r=10,t=30,b=10))

    # ks_gain_lift.json
    try:
        kgl = api.get_artifact_json(run_id, f"models/{model_key}/metrics/ks_gain_lift.json")
    except Exception:
        kgl = None
    ks_fig = go.Figure()
    if isinstance(kgl, dict):
        if "ks" in kgl:
            ks = kgl["ks"]
            ks_fig.add_trace(go.Scatter(x=ks.get("x", []), y=ks.get("y", []), mode="lines", name="KS"))
        if "gain" in kgl:
            g = kgl["gain"]
            ks_fig.add_trace(go.Scatter(x=g.get("x", []), y=g.get("y", []), mode="lines", name="Gain"))
        if "lift" in kgl:
            lf = kgl["lift"]
            ks_fig.add_trace(go.Scatter(x=lf.get("x", []), y=lf.get("y", []), mode="lines", name="Lift"))
        ks_fig.update_layout(margin=dict(l=10,r=10,t=10,b=10))

    return metrics_dom, thres_fig, roc_fig, cm_fig, ks_fig