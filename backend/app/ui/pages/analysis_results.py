# backend/app/ui/pages/analysis_results.py

from __future__ import annotations
from typing import Any, Dict
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
    dcc.Store(id="results-model-key"),  # 선택된 모델
    html.H3("Results"),

    dbc.Row([
        dbc.Col(dbc.Input(id="results-run-input", placeholder="Run ID (paste here or via URL)", type="text"), md=4),
        dbc.Col(dbc.Select(id="results-model-select", options=[], placeholder="Select model"), md=3),
        dbc.Col(dbc.Button("Load", id="results-load", color="primary"), width="auto"),
    ], className="g-2 mb-3"),

    html.Div(id="results-banner"),

    dbc.Tabs([
        dbc.Tab(label="Metrics", tab_id="tab-metrics"),
        dbc.Tab(label="Threshold sweep", tab_id="tab-threshold"),
        dbc.Tab(label="Curves", tab_id="tab-curves"),
        dbc.Tab(label="Confusion", tab_id="tab-confusion"),
        dbc.Tab(label="KS", tab_id="tab-ks"),
    ], id="results-tabs", active_tab="tab-metrics", className="mb-3"),

    html.Div(id="results-body")
], fluid=True)


@callback(
    Output("results-run-input", "value"),
    Output("results-run-id", "data"),
    Input("results-url", "href"),
    prevent_initial_call=False
)
def _init(href):
    if not href:
        return no_update, no_update
    q = up.urlparse(href).query
    params = dict(up.parse_qsl(q, keep_blank_values=True))
    rid = params.get("run_id")
    return rid, rid


@callback(
    Output("results-model-select", "options"),
    Input("results-run-id", "data"),
    State("gs-auth", "data")
)
def _load_models(run_id, auth):
    if not run_id:
        return []
    token = (auth or {}).get("access_token")
    try:
        # 서버가 list_models 유틸(artifact ping) or run.artifacts 키 제공
        models = api.list_models(run_id=run_id, token=token)
        return [{"label": m, "value": m} for m in models]
    except Exception:
        return []


@callback(
    Output("results-banner", "children"),
    Input("results-run-id", "data"),
    prevent_initial_call=False
)
def _banner(run_id):
    if not run_id:
        return dbc.Alert("Select a run and model.", color="secondary", className="py-2")
    return no_update


@callback(
    Output("results-model-key", "data"),
    Input("results-model-select", "value"),
    prevent_initial_call=True
)
def _set_model_key(v):
    return v


def _card(title: str, body: Any):
    return dbc.Card([dbc.CardHeader(title), dbc.CardBody(body)], className="mb-3")


@callback(
    Output("results-body", "children"),
    Input("results-tabs", "active_tab"),
    State("results-run-id", "data"),
    State("results-model-key", "data"),
    State("gs-auth", "data"),
)
def _render(tab, run_id, model_key, auth):
    if not run_id or not model_key:
        return dbc.Alert("Select a run and model.", color="secondary", className="py-2")

    token = (auth or {}).get("access_token")

    try:
        if tab == "tab-metrics":
            meta = api.get_artifact_json(run_id, f"models/{model_key}/metrics/summary.json", token=token)
            table = dbc.Table(
                [html.Thead(html.Tr([html.Th("Metric"), html.Th("Value")]))] +
                [html.Tbody([html.Tr([html.Td(k), html.Td(str(v))]) for k,v in (meta or {}).items()])],
                bordered=True, hover=True, responsive=True
            )
            return _card("Metrics", table)

        if tab == "tab-threshold":
            thr = api.get_artifact_json(run_id, f"models/{model_key}/metrics/threshold_sweep.json", token=token)
            if not thr:
                return _card("Threshold sweep", html.Div("No data"))
            header = html.Thead(html.Tr([html.Th(k) for k in thr["columns"]]))
            rows = [html.Tr([html.Td(x) for x in r]) for r in thr["rows"]]
            return _card("Threshold sweep", dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, responsive=True))

        if tab == "tab-curves":
            # ROC / PR 커브 JSON → 간단 표기(차트는 worker/MLflow 이미지로 확장 가능)
            roc = api.get_artifact_json(run_id, f"models/{model_key}/curves/roc.json", token=token)
            prc = api.get_artifact_json(run_id, f"models/{model_key}/curves/prc.json", token=token)
            cont = []
            if roc: cont.append(_card("ROC", html.Pre(json.dumps(roc, indent=2)[:2000] + "...")))
            if prc: cont.append(_card("PR", html.Pre(json.dumps(prc, indent=2)[:2000] + "...")))
            if not cont: cont = [_card("Curves", html.Div("No curve data"))]
            return html.Div(cont)

        if tab == "tab-confusion":
            cm = api.get_artifact_json(run_id, f"models/{model_key}/metrics/confusion.json", token=token)
            return _card("Confusion", html.Pre(json.dumps(cm, indent=2) if cm else "No data"))

        if tab == "tab-ks":
            ks = api.get_artifact_json(run_id, f"models/{model_key}/metrics/ks.json", token=token)
            return _card("KS", html.Pre(json.dumps(ks, indent=2) if ks else "No data"))
    except Exception as e:
        return dbc.Alert(f"Load error: {e}", color="danger")
    return no_update