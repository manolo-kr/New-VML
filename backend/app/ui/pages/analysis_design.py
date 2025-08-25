# backend/app/ui/pages/analysis_design.py

from __future__ import annotations
from typing import Dict, List, Any
import json
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ALL
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/design", name="Analysis Design")

# 간단 프리셋 (필요 최소한)
MODEL_PRESETS = {
    "xgboost:classification": {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.1},
    "lightgbm:classification": {"n_estimators": 300, "num_leaves": 31, "learning_rate": 0.05},
}
MODEL_OPTIONS = [
    {"label": "XGBoost", "value": "xgboost"},
    {"label": "LightGBM", "value": "lightgbm"},
]

def _param_input(model_key: str, k: str, v):
    return dbc.Col(
        dbc.InputGroup([
            dbc.InputGroupText(k),
            dbc.Input(id={"type": "design-param", "model": model_key, "key": k}, value=v, type="text"),
        ]),
        md=4, className="mb-2"
    )

def _build_params_accordion(selected_models: list[str], task_type: str):
    if not selected_models:
        return html.Div(html.Small("Select one or more models above."), className="text-muted")
    items = []
    for m in selected_models:
        key = f"{m}:{task_type}"
        params = MODEL_PRESETS.get(key, {})
        rows = []
        cols_row = []
        for i, (k, v) in enumerate(params.items()):
            cols_row.append(_param_input(m, k, v))
            if (i + 1) % 3 == 0:
                rows.append(dbc.Row(cols_row, className="g-2"))
                cols_row = []
        if cols_row:
            rows.append(dbc.Row(cols_row, className="g-2"))

        items.append(
            dbc.AccordionItem(
                children=rows or html.Div(html.Small("No preset parameters."), className="text-muted"),
                title=f"{m} parameters",
                item_id=m
            )
        )
    return dbc.Accordion(children=items, start_collapsed=True, always_open=False, id="model-param-accordion")

layout = dbc.Container([
    dcc.Location(id="design-url"),
    dcc.Store(id="design-project-id"),
    dcc.Store(id="design-analysis-id"),
    dcc.Store(id="design-dataset-uri"),
    dcc.Store(id="design-original-name"),
    dcc.Store(id="design-features-selected"),

    html.H2("Analysis - Design"),

    dbc.Card([
        dbc.CardHeader("1) Upload dataset"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dcc.Upload(
                    id="design-upload",
                    children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
                    multiple=False,
                    style={"width":"100%","height":"80px","lineHeight":"80px","borderWidth":"1px",
                           "borderStyle":"dashed","borderRadius":"6px","textAlign":"center"}
                ), md=7),
                dbc.Col(dbc.Button("Preview (modal)", id="design-btn-preview", color="secondary", outline=True), width="auto"),
                dbc.Col(html.Div(id="design-upload-status", children=dbc.Badge("yet", color="warning")), width="auto"),
                dbc.Col(html.Small("Allowed: .csv, .xlsx, .parquet"), width="auto")
            ], className="g-2"),
        ])
    ], className="mb-3"),

    dbc.Card([
        dbc.CardHeader("2) Target & Models"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Select(id="design-sel-target", placeholder="Select target column"), md=4),
                dbc.Col(dbc.Select(
                    id="design-task-type",
                    options=[{"label":"classification","value":"classification"}],
                    value="classification"
                ), md=3),
                dbc.Col(dbc.Checklist(
                    id="design-models",
                    options=MODEL_OPTIONS,
                    value=["xgboost"],
                    inline=True,
                    style={"marginTop": "6px"}
                ), md=5),
            ], className="g-2"),
            html.Div(id="design-model-params", className="mt-2"),
        ])
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(dbc.Button("Create Analysis & Task(s)", id="design-btn-create", color="primary", disabled=True), width="auto"),
        dbc.Col(html.Div(id="design-created-info"), width=True),
    ], className="g-2 mb-4"),

    # Preview Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Dataset Preview")),
        dbc.ModalBody(html.Div(id="design-preview-table", style={"overflowX": "auto","overflowY": "auto","maxHeight": "70vh"})),
        dbc.ModalFooter(dbc.Button("Close", id="preview-close", className="ms-auto")),
    ], id="preview-modal", is_open=False, size="xl", scrollable=False, centered=True),
], fluid=True)

# ─────────────────────────────
# Context 초기화 (project_id)
# ─────────────────────────────
@callback(Output("design-project-id","data"), Input("design-url","href"))
def _init_ctx(href):
    import urllib.parse as up
    pid = None
    if href:
        q = up.urlparse(href).query
        params = dict(up.parse_qsl(q))
        pid = params.get("project_id")
    if pid:
        return pid
    # 프로젝트 하나도 없으면 만들고 그걸 사용
    projs = api.list_projects()
    if projs:
        return projs[0]["id"]
    created = api.create_project("Default Project")
    return created["id"]

# ─────────────────────────────
# 업로드
# ─────────────────────────────
@callback(
    Output("design-dataset-uri", "data"),
    Output("design-original-name", "data"),
    Output("design-upload-status", "children"),
    Input("design-upload", "contents"),
    State("design-upload", "filename"),
    prevent_initial_call=True
)
def _on_upload(contents, filename):
    if not contents:
        return no_update, no_update, dbc.Badge("yet", color="warning")
    try:
        info = api.upload_file_from_contents(contents, filename or "uploaded.dat")
        return info["dataset_uri"], info.get("original_name"), dbc.Badge("ready", color="primary")
    except Exception as e:
        return no_update, no_update, dbc.Badge(f"fail", color="danger")

# ─────────────────────────────
# Preview Modal 토글 + 테이블
# ─────────────────────────────
@callback(
    Output("preview-modal", "is_open"),
    Output("design-preview-table","children"),
    Input("design-btn-preview","n_clicks"),
    Input("preview-close","n_clicks"),
    State("preview-modal","is_open"),
    State("design-dataset-uri","data"),
    prevent_initial_call=True
)
def _toggle_preview(open_clicks, close_clicks, is_open, dataset_uri):
    trig = dash.ctx.triggered_id
    if trig == "design-btn-preview":
        if not dataset_uri:
            return False, dbc.Alert("Please upload a dataset first.", color="warning")
        prev = api.preview_dataset(dataset_uri, 50)
        header = html.Tr([html.Th(c, style={"whiteSpace": "nowrap"}) for c in prev["columns"]])
        rows = [html.Tr([html.Td(v, style={"whiteSpace": "nowrap"}) for v in r]) for r in prev["rows"]]
        table = dbc.Table([html.Thead(header), html.Tbody(rows)], bordered=True, hover=True, responsive=False)
        return True, table
    if trig == "preview-close":
        return False, no_update
    return is_open, no_update

# ─────────────────────────────
# 컬럼 옵션 세팅 (타깃 select)
# ─────────────────────────────
@callback(
    Output("design-sel-target","options"),
    Input("design-dataset-uri","data"),
    prevent_initial_call=True
)
def _fill_columns(dataset_uri):
    if not dataset_uri:
        return []
    prev = api.preview_dataset(dataset_uri, 50)
    cols = prev["columns"]
    return [{"label": c, "value": c} for c in cols]

# ─────────────────────────────
# 모델 파라미터 아코디언 렌더
# ─────────────────────────────
@callback(
    Output("design-model-params", "children"),
    Input("design-models", "value"),
    Input("design-task-type", "value"),
)
def _render_model_params(models, task_type):
    models = models or []
    return _build_params_accordion(models, task_type or "classification")

# ─────────────────────────────
# 생성 버튼 활성화
# ─────────────────────────────
@callback(
    Output("design-btn-create","disabled"),
    Input("design-dataset-uri","data"),
    Input("design-sel-target","value"),
)
def _btn_enable(uri, target):
    return not (bool(uri) and bool(target))

# ─────────────────────────────
# 생성: Analysis + Task(s)
# ─────────────────────────────
@callback(
    Output("design-analysis-id","data"),
    Output("design-created-info","children"),
    Input("design-btn-create","n_clicks"),
    State("design-project-id","data"),
    State("design-dataset-uri","data"),
    State("design-original-name","data"),
    State("design-sel-target","value"),
    State("design-task-type","value"),
    State("design-models","value"),
    State({"type":"design-param","model":ALL,"key":ALL}, "id"),
    State({"type":"design-param","model":ALL,"key":ALL}, "value"),
    prevent_initial_call=True
)
def _create_all(n, project_id, dataset_uri, original_name, target, task_type, model_list, param_ids, param_vals):
    import ast
    if not n:
        return no_update, no_update
    if not (project_id and dataset_uri and target and model_list):
        return no_update, dbc.Alert("Missing project/dataset/target/models", color="danger")

    # 파라미터 수집
    overrides = {}
    if param_ids and param_vals:
        for pid, val in zip(param_ids, param_vals):
            m = pid.get("model")
            k = pid.get("key")
            if not m or not k:
                continue
            raw = val
            parsed = None
            if isinstance(raw, str):
                s = raw.strip()
                try:
                    parsed = ast.literal_eval(s)
                except Exception:
                    try:
                        parsed = float(s) if ("." in s or "e" in s.lower()) else int(s)
                    except Exception:
                        parsed = s
            else:
                parsed = raw
            overrides.setdefault(m, {})[k] = parsed

    # Analysis
    a = api.create_analysis(project_id, "My Analysis", dataset_uri, dataset_original_name=original_name)
    aid = a["id"]

    # Tasks
    created = []
    for model_family in (model_list or []):
        preset_key = f"{model_family}:{task_type}"
        model_params = (MODEL_PRESETS.get(preset_key, {}) or {}).copy()
        if model_family in overrides:
            model_params.update({k: v for k, v in overrides[model_family].items() if v is not None and v != ""})
        t = api.create_task(
            analysis_id=aid,
            task_type=task_type,
            target=target,
            model_family=model_family,
            model_params=model_params,
        )
        created.append(t)

    # 링크: Train 페이지로 이동(선택된 모든 task_ids)
    task_ids = ",".join([t["id"] for t in created])
    return aid, dbc.Alert([
        html.Div(f"Analysis created: {aid}"),
        html.Div(dcc.Link("Go to Train →", href=f"/analysis/train?task_ids={task_ids}")),
    ], color="success")