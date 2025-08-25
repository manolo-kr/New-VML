# backend/app/ui/pages/analysis_results.py

from __future__ import annotations
from typing import Dict, Any
import json
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/results", name="Results")

layout = dbc.Container([
    dcc.Location(id="results-url"),
    dcc.Store(id="results-run-id"),
    dcc.Store(id="results-run-info"),

    html.H3("Results"),

    dbc.Row([
        dbc.Col(dbc.Input(id="results-run-input", placeholder="run_id", type="text"), md=4),
        dbc.Col(dbc.Button("Load", id="results-load", color="primary"), width="auto")
    ], className="g-2 mb-3"),

    html.Div(id="results-meta", className="mb-3"),

    dbc.Tabs([
        dbc.Tab(label="Metrics", tab_id="tab-metrics"),
        dbc.Tab(label="Curves", tab_id="tab-curves"),
        dbc.Tab(label="Confusion", tab_id="tab-conf"),
        dbc.Tab(label="KS/Threshold", tab_id="tab-ks"),
    ], id="results-tabs", active_tab="tab-metrics", className="mb-2"),

    html.Div(id="results-body"),
], fluid=True)

@callback(
    Output("results-run-id", "data"),
    Input("results-url", "href"),
    prevent_initial_call=False
)
def _init(href):
    rid = None
    if href:
        q = up.urlparse(href).query
        params = dict(up.parse_qsl(q))
        rid = params.get("run_id")
    return rid

@callback(
    Output("results-run-info", "data"),
    Input("results-load", "n_clicks"),
    State("results-run-input", "value"),
    State("results-run-id", "data"),
    prevent_initial_call=True
)
def _load(_n, txt, rid_data):
    rid = txt or rid_data
    if not rid:
        return no_update
    try:
        return api.get_run(rid)
    except Exception:
        return {"error": "load failed"}

@callback(
    Output("results-meta", "children"),
    Input("results-run-info", "data"),
)
def _meta(info):
    if not info:
        return dbc.Alert("Select a run.", color="secondary")
    if "error" in info:
        return dbc.Alert("Load failed.", color="danger")
    ref = info.get("task_ref") or {}
    return dbc.Alert([
        html.Div(f"Run: {info.get('id')}"),
        html.Div(f"Model: {ref.get('model_family','-')}"),
        html.Div(f"Type: {ref.get('task_type','-')}"),
        html.Div(f"File: {info.get('dataset_original_name','-')}"),
        html.Div(f"Status: {info.get('status','-')}"),
    ], color="light")

@callback(
    Output("results-body", "children"),
    Input("results-tabs", "active_tab"),
    State("results-run-info", "data"),
)
def _render(tab, info):
    if not info or "error" in info:
        return dbc.Alert("Select a run and model.", color="secondary")

    rid = info.get("id")
    ref = info.get("task_ref") or {}
    model = ref.get("model_family")
    if not (rid and model):
        return dbc.Alert("Select a run and model.", color="secondary")

    if tab == "tab-metrics":
        try:
            m = api.get_artifact_json(rid, f"models/{model}/metrics/summary.json")
            items = [html.Li(f"{k}: {v}") for k, v in (m or {}).items()]
            return html.Ul(items or [html.Li("No metrics")])
        except Exception:
            return dbc.Alert("No metrics.", color="secondary")

    if tab == "tab-curves":
        # 예시: ROC AUC / PR curve PNG를 임베드
        img_src = api.get_artifact_file(rid, f"models/{model}/curves/roc.png")
        from base64 import b64encode
        if img_src:
            b64 = b64encode(img_src).decode()
            return html.Img(src=f"data:image/png;base64,{b64}", style={"maxWidth": "100%"})
        return dbc.Alert("No curve image.", color="secondary")

    if tab == "tab-conf":
        try:
            cm = api.get_artifact_json(rid, f"models/{model}/confusion_matrix.json")
            return dbc.Table([
                html.Thead(html.Tr([html.Th(c) for c in ["", "Pred 0", "Pred 1"]])),
                html.Tbody([
                    html.Tr([html.Th("True 0"), html.Td(cm["tn"]), html.Td(cm["fp"])]),
                    html.Tr([html.Th("True 1"), html.Td(cm["fn"]), html.Td(cm["tp"])]),
                ])
            ], bordered=True)
        except Exception:
            return dbc.Alert("No confusion matrix.", color="secondary")

    if tab == "tab-ks":
        try:
            ks = api.get_artifact_json(rid, f"models/{model}/ks_sweep.json")
            rows = [html.Tr([html.Td(x["threshold"]), html.Td(x["ks"])]) for x in ks.get("points", [])]
            return dbc.Table([html.Thead(html.Tr([html.Th("Threshold"), html.Th("KS")])), html.Tbody(rows)], bordered=True)
        except Exception:
            return dbc.Alert("No KS sweep.", color="secondary")

    return dbc.Alert("Select a tab.", color="secondary")
