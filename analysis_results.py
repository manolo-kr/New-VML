# backend/app/ui/pages/analysis_results.py

from __future__ import annotations
from typing import Dict, Any, List, Optional
import json
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/results", name="Results")

# -----------------------
# helpers
# -----------------------
TERMINAL = {"succeeded", "failed", "error", "canceled", "finished", "completed"}

def _badge(status: Optional[str]) -> dbc.Badge:
    s = (status or "-").lower()
    color = {
        "queued": "secondary",
        "pending": "secondary",
        "running": "primary",
        "cancel_requested": "warning",
        "canceled": "dark",
        "failed": "danger",
        "error": "danger",
        "succeeded": "success",
        "finished": "success",
        "completed": "success",
    }.get(s, "light")
    return dbc.Badge(s if s else "-", color=color, className="text-uppercase")

def _metrics_table(metrics: Dict[str, Any]) -> html.Div:
    if not metrics:
        return dbc.Alert("No metrics found.", color="secondary", className="py-2")
    # 간단한 key/value 테이블
    rows = []
    for k in sorted(metrics.keys()):
        v = metrics[k]
        try:
            if isinstance(v, (int, float)):
                v_str = f"{v:.6g}"
            else:
                v_str = str(v)
        except Exception:
            v_str = str(v)
        rows.append(html.Tr([html.Td(k), html.Td(v_str)]))
    return dbc.Table([html.Thead(html.Tr([html.Th("Metric"), html.Th("Value")])),
                      html.Tbody(rows)], bordered=True, hover=True, responsive=True, className="align-middle")

def _maybe_curve_block(run_id: str, model: str, name: str, path: str) -> html.Div:
    """아티팩트 JSON을 시도해서 있으면 간단한 미니 테이블로, 없으면 안내."""
    try:
        data = api.get_artifact_json(run_id, path)
    except Exception:
        data = None
    if not data:
        return dbc.Alert(f"Select a run and model", color="light", className="py-2")

    # 데이터 형태가 다양할 수 있으므로 전개 가능한 key/value 일부만 표시
    # (자세한 시각화는 후속)
    if isinstance(data, dict):
        head_items = list(data.items())[:10]
        rows = [html.Tr([html.Td(str(k)), html.Td(str(v))]) for k, v in head_items]
        return dbc.Card([
            dbc.CardHeader(name),
            dbc.CardBody(dbc.Table([html.Tbody(rows)], bordered=True, hover=True, responsive=True))
        ], className="mb-3")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        keys = list(data[0].keys())[:5]
        thead = html.Thead(html.Tr([html.Th(k) for k in keys]))
        body_rows = []
        for r in data[:20]:
            body_rows.append(html.Tr([html.Td(str(r.get(k))) for k in keys]))
        return dbc.Card([
            dbc.CardHeader(name),
            dbc.CardBody(dbc.Table([thead, html.Tbody(body_rows)], bordered=True, hover=True, responsive=True))
        ], className="mb-3")

    return dbc.Card([
        dbc.CardHeader(name),
        dbc.CardBody(dbc.Alert("Unsupported artifact format (showing raw JSON below)", color="warning")),
        dbc.CardBody(html.Pre(json.dumps(data, indent=2)[:4000]))
    ], className="mb-3")

# -----------------------
# layout
# -----------------------
layout = dbc.Container([
    dcc.Location(id="results-url"),

    dcc.Store(id="results-run-id"),
    dcc.Store(id="results-run"),
    dcc.Store(id="results-model-selected"),

    html.H2("Analysis - Results"),

    dbc.Card([
        dbc.CardHeader("Select"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Input(id="results-run-input", placeholder="Enter run_id (or via URL ?run_id=...)", type="text"), md=6),
                dbc.Col(dbc.Button("Load", id="btn-results-load", color="primary"), md="auto"),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Select(id="results-model-dropdown", options=[], placeholder="Select model family"), md=4),
            ], className="g-2 mt-2"),
        ])
    ], className="mb-3"),

    html.Div(id="results-summary"),
    html.Hr(),
    html.Div(id="results-metrics"),
    html.Hr(),
    dbc.Tabs([
        dbc.Tab(html.Div(id="results-curve-roc"), label="Curves - ROC"),
        dbc.Tab(html.Div(id="results-curve-pr"), label="Curves - PR"),
        dbc.Tab(html.Div(id="results-confusion"), label="Confusion"),
        dbc.Tab(html.Div(id="results-ks"), label="KS"),
        dbc.Tab(html.Div(id="results-threshold"), label="Threshold Sweep"),
    ]),
], fluid=True)

# -----------------------
# callbacks
# -----------------------

# 1) URL → run_id / model 초기화
@callback(
    Output("results-run-id", "data"),
    Output("results-model-selected", "data"),
    Input("results-url", "href"),
    prevent_initial_call=False
)
def _init_from_url(href):
    run_id = None
    model = None
    if href:
        q = up.urlparse(href).query
        params = dict(up.parse_qsl(q, keep_blank_values=True))
        run_id = params.get("run_id") or None
        model = params.get("model") or None
    return run_id, model

# 2) Load 버튼 → run_id 세팅 (텍스트 입력값 사용)
@callback(
    Output("results-run-id", "data", allow_duplicate=True),
    Input("btn-results-load", "n_clicks"),
    State("results-run-input", "value"),
    prevent_initial_call=True
)
def _load_run_id(_n, val):
    if not val:
        return no_update
    return str(val).strip()

# 3) run_id 변경 → run 정보 fetch + 모델 드롭다운 옵션 채우기
@callback(
    Output("results-run", "data"),
    Output("results-model-dropdown", "options"),
    Output("results-model-dropdown", "value"),
    Input("results-run-id", "data"),
    State("results-model-selected", "data"),
    prevent_initial_call=True
)
def _fetch_run(run_id, preselected):
    if not run_id:
        return None, [], None
    try:
        info = api.get_run(run_id)
    except Exception:
        return None, [], None

    # 모델 후보: run.task_ref.model_family 가 최우선
    task_ref = info.get("task_ref") or {}
    model = task_ref.get("model_family")
    options = []
    if model:
        options = [{"label": model, "value": model}]
        value = preselected or model
    else:
        # artifacts dict 키로 추정 (없으면 빈 옵션)
        arts = info.get("artifacts") or {}
        if isinstance(arts, dict):
            keys = [k for k, v in arts.items() if isinstance(v, dict) or v is None]
            options = [{"label": k, "value": k} for k in keys]
        value = preselected or (options[0]["value"] if options else None)

    return info, options, value

# 4) 모델 드롭다운 선택 저장
@callback(
    Output("results-model-selected", "data", allow_duplicate=True),
    Input("results-model-dropdown", "value"),
    prevent_initial_call=True
)
def _save_model_selected(v):
    return v

# 5) Summary / Metrics / Curves 렌더
@callback(
    Output("results-summary", "children"),
    Output("results-metrics", "children"),
    Output("results-curve-roc", "children"),
    Output("results-curve-pr", "children"),
    Output("results-confusion", "children"),
    Output("results-ks", "children"),
    Output("results-threshold", "children"),
    Input("results-run", "data"),
    Input("results-model-selected", "data"),
)
def _render_all(run, model):
    if not run:
        empty = dbc.Alert("Select a run and model", color="light", className="py-2")
        return empty, empty, empty, empty, empty, empty, empty

    run_id = run.get("id") or "-"
    status = run.get("status")
    msg = run.get("message") or "-"
    fname = run.get("dataset_original_name") or "-"
    task_ref = run.get("task_ref") or {}
    ttype = task_ref.get("task_type") or "-"
    mfamily = model or task_ref.get("model_family") or "-"

    summary = dbc.Card([
        dbc.CardHeader("Summary"),
        dbc.CardBody([
            html.Div([html.Strong("Run ID: "), html.Code(run_id, className="me-2")]),
            html.Div([html.Strong("Status: "), _badge(status)]),
            html.Div([html.Strong("Message: "), html.Span(msg)]),
            html.Div([html.Strong("File: "), html.Span(fname)]),
            html.Div([html.Strong("Task type: "), html.Span(ttype)]),
            html.Div([html.Strong("Model: "), html.Span(mfamily)]),
        ])
    ], className="mb-3")

    # metrics
    metrics = run.get("metrics") or {}
    metrics_block = _metrics_table(metrics) if metrics else dbc.Alert("No metrics logged.", color="secondary", className="py-2")

    # artifacts blocks (없으면 안내)
    if not model:
        empty = dbc.Alert("Select a run and model", color="light", className="py-2")
        return summary, metrics_block, empty, empty, empty, empty, empty

    roc = _maybe_curve_block(run_id, model, "ROC Curve", f"models/{model}/curves/roc.json")
    prc = _maybe_curve_block(run_id, model, "Precision-Recall Curve", f"models/{model}/curves/pr.json")
    conf = _maybe_curve_block(run_id, model, "Confusion Matrix", f"models/{model}/confusion.json")
    ks = _maybe_curve_block(run_id, model, "KS Curve", f"models/{model}/curves/ks.json")
    thr = _maybe_curve_block(run_id, model, "Threshold Sweep", f"models/{model}/thresholds.json")

    return summary, metrics_block, roc, prc, conf, ks, thr