# backend/app/ui/pages/analysis_train.py

from __future__ import annotations
from typing import Dict, List, Any
import json
import urllib.parse as up
import time

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/train", name="Training")

TERMINAL = {"succeeded", "failed", "error", "canceled", "finished", "completed"}

def is_terminal(status: str | None) -> bool:
    if not status:
        return False
    return status.lower() in TERMINAL

def _badge(status: str | None) -> dbc.Badge:
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
    return dbc.Badge(s if s != "-" else "-", color=color, className="text-uppercase")

def _render_table(task_ids: List[str],
                  run_ids: Dict[str, str],
                  status_map: Dict[str, Any],
                  meta: Dict[str, Dict[str, str]] | None) -> html.Div:
    meta = meta or {}
    header = html.Thead(html.Tr([
        html.Th("Task ID"),
        html.Th("Model"),
        html.Th("Type"),
        html.Th("File"),
        html.Th("Run ID"),
        html.Th("Status"),
        html.Th("Progress"),
        html.Th("Message"),
        html.Th("Results"),
    ]))
    rows = []
    for tid in task_ids or []:
        rid = (run_ids or {}).get(tid)
        info = (status_map or {}).get(rid or "", {}) if rid else {}
        st = info.get("status")
        prog = info.get("progress")
        msg = info.get("message")
        m = (meta or {}).get(tid, {})
        model = m.get("model_family") or (info.get("task_ref") or {}).get("model_family") or "-"
        ttype = m.get("task_type") or (info.get("task_ref") or {}).get("task_type") or "-"
        fname = m.get("dataset_original_name") or info.get("dataset_original_name") or "-"

        results_link = ("-" if not rid else
                        dcc.Link("Open", href=f"/analysis/results?run_id={rid}", target="_blank"))

        rows.append(html.Tr([
            html.Td(tid),
            html.Td(model),
            html.Td(ttype),
            html.Td(fname),
            html.Td(rid or "-"),
            html.Td(_badge(st)),
            html.Td(f"{int((prog or 0)*100)}%" if isinstance(prog, (int, float)) else "-"),
            html.Td(msg or "-"),
            html.Td(results_link),
        ]))
    table = dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, responsive=True, className="align-middle")
    return html.Div(table)


layout = dbc.Container([
    dcc.Location(id="train-url"),

    dcc.Store(id="train-task-ids"),
    dcc.Store(id="train-task-meta"),
    dcc.Store(id="train-run-ids"),
    dcc.Store(id="train-status"),
    dcc.Store(id="train-busy"),
    dcc.Store(id="gs-auth", storage_type="session"),

    dcc.Interval(id="train-poll", interval=2000, disabled=True),

    dbc.Row([
        dbc.Col(dbc.Button("Train All", id="btn-start-all", color="primary"), width="auto"),
        dbc.Col(dbc.Button("Cancel All", id="btn-cancel-all", color="danger", outline=True), width="auto"),
        dbc.Col(html.Div(id="train-mode-banner"), width=True),
    ], className="g-2 mb-3"),

    html.Div(id="train-contents"),
], fluid=True)


# 1) URL → task_ids, meta
@callback(
    Output("train-task-ids", "data"),
    Output("train-task-meta", "data"),
    Input("train-url", "href"),
    prevent_initial_call=False
)
def _init_from_url(href):
    task_ids: List[str] = []
    meta: Dict[str, Dict[str, str]] = {}
    if href:
        q = up.urlparse(href).query
        params = dict(up.parse_qsl(q, keep_blank_values=True))
        if "task_ids" in params and params["task_ids"]:
            task_ids = [t for t in params["task_ids"].split(",") if t]
        elif "task_id" in params and params["task_id"]:
            task_ids = [params["task_id"]]
        if "meta" in params and params["meta"]:
            try:
                meta = json.loads(up.unquote_plus(params["meta"]))
            except Exception:
                meta = {}
    return task_ids, meta or {}


# 2) Train All / Cancel All → run_ids
@callback(
    Output("train-run-ids", "data"),
    Input("btn-start-all", "n_clicks"),
    Input("btn-cancel-all", "n_clicks"),
    State("train-task-ids", "data"),
    State("train-run-ids", "data"),
    State("train-status", "data"),
    State("gs-auth", "data"),
    prevent_initial_call=True
)
def _control_runs(n_start, n_cancel, task_ids, run_ids, status_map, auth):
    token = (auth or {}).get("access_token")
    trig = dash.ctx.triggered_id
    task_ids = task_ids or []
    run_ids = (run_ids or {}).copy()
    status_map = status_map or {}

    if trig == "btn-start-all":
        # 새 시도마다 fresh keys + 강제 생성
        run_ids = {}
        now_tag = str(int(time.time()))
        for tid in task_ids:
            try:
                resp = api.train_task(
                    tid,
                    token=token,
                    hpo=None,
                    extra={"idempotency_key": f"start:{tid}:{now_tag}", "force": True}
                )
                new_rid = resp.get("run_id")
                if new_rid:
                    run_ids[tid] = new_rid
            except Exception:
                pass
        return run_ids

    if trig == "btn-cancel-all":
        for rid in (run_ids or {}).values():
            try:
                api.cancel_run(rid, token)
            except Exception:
                pass
        return run_ids

    return no_update


# 3) 폴링 → train-status만
@callback(
    Output("train-status", "data"),
    Input("train-poll", "n_intervals"),
    State("train-run-ids", "data"),
    State("gs-auth", "data"),
    prevent_initial_call=True
)
def _poll_status(_n, run_ids, auth):
    token = (auth or {}).get("access_token")
    run_ids = run_ids or {}
    out: Dict[str, Any] = {}
    if not run_ids:
        return out
    for rid in run_ids.values():
        try:
            info = api.get_run(rid, token)
            out[rid] = info or {}
        except Exception:
            out[rid] = {"status": "error", "message": "fetch failed"}
    return out


# 4) 폴링 on/off & busy
@callback(
    Output("train-poll", "disabled"),
    Output("train-busy", "data"),
    Input("train-run-ids", "data"),
    Input("train-status", "data"),
)
def _derive_poll_and_busy(run_ids, status_map):
    run_ids = run_ids or {}
    status_map = status_map or {}
    if not run_ids:
        return True, False
    any_active = False
    for rid in run_ids.values():
        st = (status_map.get(rid) or {}).get("status")
        if not is_terminal(st):
            any_active = True
            break
    return (not any_active), any_active


# 5) 배너 & 테이블
@callback(
    Output("train-mode-banner", "children"),
    Output("train-contents", "children"),
    Input("train-task-ids", "data"),
    Input("train-run-ids", "data"),
    Input("train-status", "data"),
    Input("train-task-meta", "data"),
)
def _render(task_ids, run_ids, status_map, meta):
    task_ids = task_ids or []
    run_ids = run_ids or {}
    status_map = status_map or {}
    meta = meta or {}

    any_active = False
    for rid in run_ids.values():
        st = (status_map.get(rid) or {}).get("status")
        if not is_terminal(st):
            any_active = True
            break
    banner = (dbc.Alert("Running... polling statuses", color="info", className="py-2")
              if any_active else
              dbc.Alert("Idle. Click Train All to enqueue runs.", color="secondary", className="py-2"))

    table = _render_table(task_ids, run_ids, status_map, meta)
    return banner, table