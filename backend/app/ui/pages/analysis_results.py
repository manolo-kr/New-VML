# backend/app/ui/pages/analysis_results.py

from __future__ import annotations
from typing import Any, Dict
import urllib.parse as up
import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/results", name="Results")

layout = dbc.Container([
    dcc.Location(id="results-url"),
    dcc.Store(id="results-run-id"),     # 오직 한 콜백만 씀

    html.H2("Results"),
    dbc.Row([
        dbc.Col(dbc.Input(id="results-run-input", placeholder="Run ID (auto-filled from URL)", disabled=True), md=6),
        dbc.Col(dcc.Dropdown(id="results-model", placeholder="Select a model key"), md=6),
    ], className="g-2 mb-2"),
    html.Div(id="results-summary"),
    html.Hr(),
    dbc.Tabs(id="results-tabs", children=[
        dbc.Tab(label="Metrics", tab_id="metrics"),
        dbc.Tab(label="Curves", tab_id="curves"),
        dbc.Tab(label="Confusion", tab_id="confusion"),
        dbc.Tab(label="KS", tab_id="ks"),
    ], active_tab="metrics"),
    html.Div(id="results-body"),
], fluid=True)

# 1) URL → results-run-id (유일 작성)
@callback(
    Output("results-run-id", "data"),
    Output("results-run-input", "value"),
    Input("results-url", "href"),
    prevent_initial_call=False
)
def _parse_url(href):
    run_id = ""
    if href:
        q = up.urlparse(href).query
        params = dict(up.parse_qsl(q, keep_blank_values=True))
        run_id = params.get("run_id") or ""
    return run_id, run_id

# 2) 모델 키 로드
@callback(
    Output("results-model", "options"),
    Input("results-run-id", "data"),
    State("gs-auth", "data"),
    prevent_initial_call=True
)
def _load_models(run_id, auth):
    token = (auth or {}).get("access_token")
    if not run_id:
        return []
    try:
        keys = api.list_models(run_id, token=token)
        return [{"label": k, "value": k} for k in keys]
    except Exception:
        return []

# 3) Summary & Body
@callback(
    Output("results-summary", "children"),
    Output("results-body", "children"),
    Input("results-run-id", "data"),
    Input("results-model", "value"),
    Input("results-tabs", "active_tab"),
    State("gs-auth", "data"),
)
def _render(run_id, model_key, tab, auth):
    token = (auth or {}).get("access_token")
    if not run_id:
        return dbc.Alert("Select a run.", color="secondary"), html.Div()
    # summary
    info = api.get_run(run_id, token=token)
    head = dbc.Alert(
        [html.Div(f"Run: {run_id}"),
         html.Div(f"Status: {info.get('status')}"),
         html.Div(f"Model keys: {', '.join(api.list_models(run_id, token=token) or [])}")],
        color="light"
    )
    if not model_key:
        return head, dbc.Alert("Select a run and model.", color="secondary")

    # tab content (간단 placeholder — 실제 곡선/이미지/표는 artifact 호출로 완성)
    if tab == "metrics":
        try:
            m = api.get_artifact_json(run_id, f"models/{model_key}/metrics/summary.json", token=token)
            body = dbc.Table([
                html.Thead(html.Tr([html.Th("Metric"), html.Th("Value")])),
                html.Tbody([html.Tr([html.Td(k), html.Td(v)]) for k, v in (m or {}).items()])
            ], bordered=True, hover=True, responsive=True)
        except Exception:
            body = dbc.Alert("No metrics yet.", color="secondary")
        return head, body

    if tab == "curves":
        # 예시: ROC PNG
        png = api.get_artifact_png_src(run_id, f"models/{model_key}/curves/roc.png", token=token)
        if png:
            return head, html.Img(src=png, style={"maxWidth":"100%"})
        return head, dbc.Alert("Select a run and model.", color="secondary")

    if tab == "confusion":
        try:
            cm = api.get_artifact_json(run_id, f"models/{model_key}/confusion_matrix.json", token=token)
            body = dbc.Pre(str(cm))
        except Exception:
            body = dbc.Alert("Select a run and model.", color="secondary")
        return head, body

    if tab == "ks":
        try:
            ks = api.get_artifact_json(run_id, f"models/{model_key}/ks.json", token=token)
            body = dbc.Pre(str(ks))
        except Exception:
            body = dbc.Alert("Select a run and model.", color="secondary")
        return head, body

    return head, html.Div()