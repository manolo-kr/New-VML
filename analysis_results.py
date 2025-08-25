# backend/app/ui/pages/analysis_results.py

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import json
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np

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
    rows = []
    for k in sorted(metrics.keys()):
        v = metrics[k]
        try:
            v_str = f"{v:.6g}" if isinstance(v, (int, float)) else str(v)
        except Exception:
            v_str = str(v)
        rows.append(html.Tr([html.Td(k), html.Td(v_str)]))
    return dbc.Table(
        [html.Thead(html.Tr([html.Th("Metric"), html.Th("Value")])), html.Tbody(rows)],
        bordered=True, hover=True, responsive=True, className="align-middle"
    )

def _try_get_json(run_id: str, name: str) -> Optional[Any]:
    try:
        return api.get_artifact_json(run_id, name)
    except Exception:
        return None

# ---------- parsers for artifacts → (x, y, ...)

def _parse_roc(obj: Any) -> Optional[Tuple[List[float], List[float]]]:
    if not obj:
        return None
    if isinstance(obj, dict):
        fpr = obj.get("fpr") or obj.get("x")
        tpr = obj.get("tpr") or obj.get("y")
        if isinstance(fpr, list) and isinstance(tpr, list) and len(fpr) == len(tpr):
            return list(map(float, fpr)), list(map(float, tpr))
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        fpr = [float(d.get("fpr")) for d in obj if "fpr" in d]
        tpr = [float(d.get("tpr")) for d in obj if "tpr" in d]
        if len(fpr) == len(tpr) and len(fpr) > 0:
            return fpr, tpr
    return None

def _parse_pr(obj: Any) -> Optional[Tuple[List[float], List[float]]]:
    if not obj:
        return None
    if isinstance(obj, dict):
        prec = obj.get("precision")
        rec = obj.get("recall")
        x = obj.get("x"); y = obj.get("y")
        if isinstance(prec, list) and isinstance(rec, list) and len(prec) == len(rec):
            return list(map(float, rec)), list(map(float, prec))
        if isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
            return list(map(float, x)), list(map(float, y))
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        prec = [float(d.get("precision")) for d in obj if "precision" in d]
        rec = [float(d.get("recall")) for d in obj if "recall" in d]
        if len(prec) == len(rec) and len(prec) > 0:
            return rec, prec
    return None

def _parse_confusion(obj: Any) -> Optional[Tuple[List[str], List[str], List[List[float]]]]:
    if not obj:
        return None
    if isinstance(obj, dict):
        mat = obj.get("matrix") or obj.get("data")
        if isinstance(mat, list) and mat and isinstance(mat[0], list):
            lab = obj.get("labels")
            xlab = obj.get("x_labels") or lab
            ylab = obj.get("y_labels") or lab
            n = len(mat)
            x = xlab if isinstance(xlab, list) and len(xlab) == n else [f"C{i}" for i in range(n)]
            y = ylab if isinstance(ylab, list) and len(ylab) == n else [f"C{i}" for i in range(n)]
            return x, y, [[float(v) for v in row] for row in mat]
    if isinstance(obj, list) and obj and isinstance(obj[0], list):
        n = len(obj)
        x = [f"C{i}" for i in range(n)]
        y = [f"C{i}" for i in range(n)]
        return x, y, [[float(v) for v in row] for row in obj]
    return None

def _parse_ks(obj: Any) -> Optional[Tuple[List[float], List[float], List[float]]]:
    if not obj:
        return None
    if isinstance(obj, dict):
        thr = obj.get("threshold")
        cg = obj.get("cum_good")
        cb = obj.get("cum_bad")
        if all(isinstance(v, list) for v in [thr, cg, cb]) and len(thr) == len(cg) == len(cb):
            return list(map(float, thr)), list(map(float, cg)), list(map(float, cb))
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        thr = [float(d.get("threshold")) for d in obj if "threshold" in d]
        cg = [float(d.get("cum_good")) for d in obj if "cum_good" in d]
        cb = [float(d.get("cum_bad")) for d in obj if "cum_bad" in d]
        if len(thr) == len(cg) == len(cb) and len(thr) > 0:
            return thr, cg, cb
    return None

def _parse_thresholds(obj: Any) -> Optional[Tuple[List[float], Dict[str, List[float]]]]:
    if not obj:
        return None
    if isinstance(obj, dict):
        thr = obj.get("threshold")
        if isinstance(thr, list):
            series = {k: v for k, v in obj.items()
                      if k != "threshold" and isinstance(v, list) and len(v) == len(thr)}
            return list(map(float, thr)), {k: list(map(float, v)) for k, v in series.items()}
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        keys = set().union(*[d.keys() for d in obj])
        if "threshold" not in keys:
            return None
        thr = [float(d.get("threshold")) for d in obj]
        series: Dict[str, List[float]] = {}
        for k in sorted(keys):
            if k == "threshold":
                continue
            try:
                series[k] = [float(d.get(k)) if d.get(k) is not None else np.nan for d in obj]
            except Exception:
                continue
        return thr, series
    return None

# ---------- figure builders

def _fig_roc(fpr: List[float], tpr: List[float]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines", name="ROC"))
    fig.add_trace(go.Scatter(x=[0,1], y=[0,1], mode="lines", name="Random", line=dict(dash="dash")))
    fig.update_layout(xaxis_title="FPR", yaxis_title="TPR", template="plotly_white", margin=dict(l=40,r=10,t=10,b=40))
    return fig

def _fig_pr(recall: List[float], precision: List[float]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recall, y=precision, mode="lines", name="PR"))
    fig.update_layout(xaxis_title="Recall", yaxis_title="Precision", template="plotly_white", margin=dict(l=40,r=10,t=10,b=40))
    return fig

def _row_normalize(mat: List[List[float]]) -> List[List[float]]:
    out = []
    for row in mat:
        s = float(sum(row)) if row else 0.0
        out.append([ (v / s if s > 0 else 0.0) for v in row ])
    return out

def _fig_confusion(xlab: List[str], ylab: List[str], mat: List[List[float]]) -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=mat, x=xlab, y=ylab, colorscale="Blues", showscale=True, colorbar=dict(title="Value")
    ))
    fig.update_layout(template="plotly_white", margin=dict(l=60,r=10,t=10,b=40), xaxis_side="top")
    return fig

def _fig_ks(thr: List[float], cg: List[float], cb: List[float]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=thr, y=cg, mode="lines", name="Cum Good"))
    fig.add_trace(go.Scatter(x=thr, y=cb, mode="lines", name="Cum Bad"))
    diff = np.array(cg) - np.array(cb)
    if len(diff):
        ks = float(np.nanmax(np.abs(diff)))
        where = int(np.nanargmax(np.abs(diff)))
        if len(thr) > where:
            fig.add_trace(go.Scatter(
                x=[thr[where], thr[where]],
                y=[cb[where], cg[where]],
                mode="lines",
                name=f"KS = {ks:.3f}",
                line=dict(dash="dash")
            ))
    fig.update_layout(xaxis_title="Threshold", yaxis_title="Cumulative Rate", template="plotly_white",
                      margin=dict(l=40,r=10,t=10,b=40))
    return fig

def _fig_thresholds(thr: List[float], series: Dict[str, List[float]], pick: Optional[List[str]]) -> go.Figure:
    fig = go.Figure()
    series_keys = pick if (pick and len(pick) > 0) else sorted(series.keys())
    for k in series_keys:
        if k in series:
            fig.add_trace(go.Scatter(x=thr, y=series[k], mode="lines", name=k))
    fig.update_layout(
        xaxis_title="Threshold", yaxis_title="Metric", template="plotly_white",
        margin=dict(l=40,r=10,t=10,b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0)
    )
    return fig

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
                dbc.Col(dbc.Checklist(
                    id="results-conf-norm",
                    options=[{"label": "Row-normalize confusion", "value": "row"}],
                    value=[]
                ), md="auto"),
                dbc.Col(dcc.Dropdown(id="results-thr-metrics", multi=True, placeholder="Threshold: choose metrics"), md=6),
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

# 2) Load 버튼 → run_id 세팅
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

    task_ref = info.get("task_ref") or {}
    model = task_ref.get("model_family")
    options = []
    if model:
        options = [{"label": model, "value": model}]
        value = preselected or model
    else:
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

# 5) Summary / Metrics / Curves + (Threshold metrics 옵션/기본값) 렌더
@callback(
    Output("results-summary", "children"),
    Output("results-metrics", "children"),
    Output("results-curve-roc", "children"),
    Output("results-curve-pr", "children"),
    Output("results-confusion", "children"),
    Output("results-ks", "children"),
    Output("results-threshold", "children"),
    Output("results-thr-metrics", "options"),
    Output("results-thr-metrics", "value"),
    Input("results-run", "data"),
    Input("results-model-selected", "data"),
    Input("results-conf-norm", "value"),
    State("results-thr-metrics", "value"),
)
def _render_all(run, model, norm_flags, thr_pick):
    if not run:
        empty = dbc.Alert("Select a run and model", color="light", className="py-2")
        return empty, empty, empty, empty, empty, empty, empty, [], no_update

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

    metrics = run.get("metrics") or {}
    metrics_block = _metrics_table(metrics) if metrics else dbc.Alert("No metrics logged.", color="secondary", className="py-2")

    # 기본 안내
    if not model:
        empty = dbc.Alert("Select a run and model", color="light", className="py-2")
        return summary, metrics_block, empty, empty, empty, empty, empty, [], no_update

    # ROC
    roc_children = dbc.Alert("No ROC curve.", color="light", className="py-2")
    obj = _try_get_json(run_id, f"models/{model}/curves/roc.json")
    parsed = _parse_roc(obj)
    if parsed:
        fpr, tpr = parsed
        roc_children = dcc.Graph(figure=_fig_roc(fpr, tpr), style={"height":"360px"})

    # PR
    pr_children = dbc.Alert("No PR curve.", color="light", className="py-2")
    obj = _try_get_json(run_id, f"models/{model}/curves/pr.json")
    parsed = _parse_pr(obj)
    if parsed:
        rec, prec = parsed
        pr_children = dcc.Graph(figure=_fig_pr(rec, prec), style={"height":"360px"})

    # Confusion
    conf_children = dbc.Alert("No confusion matrix.", color="light", className="py-2")
    obj = _try_get_json(run_id, f"models/{model}/confusion.json")
    parsed = _parse_confusion(obj)
    if parsed:
        xlab, ylab, mat = parsed
        if norm_flags and "row" in norm_flags:
            mat = _row_normalize(mat)
        conf_children = dcc.Graph(figure=_fig_confusion(xlab, ylab, mat), style={"height":"420px"})

    # KS
    ks_children = dbc.Alert("No KS curve.", color="light", className="py-2")
    obj = _try_get_json(run_id, f"models/{model}/curves/ks.json")
    parsed = _parse_ks(obj)
    if parsed:
        thr, cg, cb = parsed
        ks_children = dcc.Graph(figure=_fig_ks(thr, cg, cb), style={"height":"360px"})

    # Threshold sweep (+ 옵션/기본값)
    thr_children = dbc.Alert("No threshold sweep.", color="light", className="py-2")
    thr_opts: List[Dict[str, str]] = []
    thr_val = thr_pick
    obj = _try_get_json(run_id, f"models/{model}/thresholds.json")
    parsed = _parse_thresholds(obj)
    if parsed:
        thr, series = parsed
        if series:
            keys_sorted = sorted(series.keys())
            thr_opts = [{"label": k, "value": k} for k in keys_sorted]
            # value가 비어있으면 대표 메트릭으로 기본 선택
            default_pref = ["tpr", "fpr", "precision", "recall", "accuracy", "f1", "auc"]
            if not thr_pick:
                pick = [k for k in default_pref if k in keys_sorted] or keys_sorted[: min(3, len(keys_sorted))]
                thr_val = pick
            thr_children = dcc.Graph(figure=_fig_thresholds(thr, series, thr_val), style={"height":"380px"})

    return summary, metrics_block, roc_children, pr_children, conf_children, ks_children, thr_children, thr_opts, thr_val