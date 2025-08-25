# backend/app/ui/pages/analysis_design.py

from __future__ import annotations
from typing import Any, Dict, List
import ast
import json
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ALL
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/design", name="Analysis Design")

# ─────────────────────────────────────────────────────────────────
# Presets (보편화된 초기값)
# ─────────────────────────────────────────────────────────────────
MODEL_PRESETS: Dict[str, Dict[str, Any]] = {
    "xgboost:classification": {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.1, "subsample": 0.8, "colsample_bytree": 0.8},
    "xgboost:regression": {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.1, "subsample": 0.8, "colsample_bytree": 0.8},
    "lightgbm:classification": {"n_estimators": 400, "num_leaves": 31, "learning_rate": 0.05, "feature_fraction": 0.9},
    "lightgbm:regression": {"n_estimators": 400, "num_leaves": 31, "learning_rate": 0.05, "feature_fraction": 0.9},
    "catboost:classification": {"iterations": 400, "depth": 6, "learning_rate": 0.1},
    "catboost:regression": {"iterations": 400, "depth": 6, "learning_rate": 0.1},
    "randomforest:classification": {"n_estimators": 300, "max_depth": None, "min_samples_split": 2},
    "randomforest:regression": {"n_estimators": 300, "max_depth": None, "min_samples_split": 2},
    "logreg:classification": {"C": 1.0, "penalty": "l2", "max_iter": 300},
    "svm:classification": {"C": 1.0, "kernel": "rbf", "gamma": "scale"},
    "elasticnet:regression": {"alpha": 0.001, "l1_ratio": 0.5, "max_iter": 5000},
    "knn:classification": {"n_neighbors": 15, "weights": "distance"},
    "mlp:classification": {"hidden_layer_sizes": "(128, 64)", "activation": "relu", "max_iter": 300},
    "mlp:regression": {"hidden_layer_sizes": "(128, 64)", "activation": "relu", "max_iter": 300},
}
MODEL_OPTIONS = [
    {"label": "XGBoost", "value": "xgboost"},
    {"label": "LightGBM", "value": "lightgbm"},
    {"label": "CatBoost", "value": "catboost"},
    {"label": "RandomForest", "value": "randomforest"},
    {"label": "Logistic Regression", "value": "logreg"},
    {"label": "SVM", "value": "svm"},
    {"label": "ElasticNet", "value": "elasticnet"},
    {"label": "KNN", "value": "knn"},
    {"label": "MLP", "value": "mlp"},
]

def _param_input(model_key: str, k: str, v: Any) -> dbc.Col:
    return dbc.Col(
        dbc.InputGroup([
            dbc.InputGroupText(k),
            dbc.Input(id={"type": "design-param", "model": model_key, "key": k}, value=v, type="text"),
        ]),
        md=4, className="mb-2"
    )

def _build_params_accordion(selected_models: List[str], task_type: str):
    if not selected_models:
        return html.Div(html.Small("Select one or more models above."), className="text-muted")
    items = []
    for m in selected_models:
        key = f"{m}:{task_type}"
        params = MODEL_PRESETS.get(key, {})
        rows = []
        buf = []
        for i, (k, v) in enumerate(params.items()):
            buf.append(_param_input(m, k, v))
            if (i + 1) % 3 == 0:
                rows.append(dbc.Row(buf, className="g-2"))
                buf = []
        if buf:
            rows.append(dbc.Row(buf, className="g-2"))
        items.append(
            dbc.AccordionItem(
                title=f"{m} parameters",
                children=rows or html.Div(html.Small("No preset parameters."), className="text-muted"),
                item_id=m
            )
        )
    return dbc.Accordion(children=items, start_collapsed=True, always_open=False, id="model-param-accordion")

layout = dbc.Container([
    dcc.Location(id="design-url"),
    dcc.Store(id="design-project-id"),
    dcc.Store(id="design-analysis-id"),
    dcc.Store(id="design-dataset-uri"),
    dcc.Store(id="design-columns"),
    dcc.Store(id="design-features-selected"),
    dcc.Store(id="design-upload-meta"),  # {"original_name": "..."} 저장

    html.H2("Analysis - Design"),

    # 1) Upload
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

    # 2) Target & Features
    dbc.Card([
        dbc.CardHeader("2) Target & Features"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Select(id="design-sel-target", placeholder="Select target column"), md=4),
                dbc.Col(dbc.Button("Select Features (X)", id="open-feature-modal", color="info"), md=3),
                dbc.Col(html.Div(id="design-feature-summary", className="text-muted"), md=5),
            ], className="g-2"),
        ])
    ], className="mb-3"),

    # 3) Split & sampling
    dbc.Card([
        dbc.CardHeader("3) Split & sampling"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.InputGroup([dbc.InputGroupText("Test size"), dbc.Input(id="design-split-test", type="number", value=0.2, step=0.05, min=0.05, max=0.9)]), md=4),
                dbc.Col(dbc.InputGroup([dbc.InputGroupText("Random state"), dbc.Input(id="design-split-seed", type="number", value=42, step=1)]), md=4),
                dbc.Col(dbc.InputGroup([dbc.InputGroupText("Cap per class"), dbc.Input(id="design-sample-cap", type="number", value=10000, step=1000, min=1000)]), md=4),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Checklist(
                    id="design-sample-enable",
                    options=[{"label": "Enable stratified capping per class", "value": "on"}],
                    value=[],
                ), md=12)
            ], className="g-2"),
            html.Small("대용량 데이터에서 클래스별 샘플 수를 제한(불균형 완화 + 속도 향상)"),
        ])
    ], className="mb-3"),

    # 4) Task & Models
    dbc.Card([
        dbc.CardHeader("4) Task & Models"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Select(
                    id="design-task-type",
                    options=[{"label":"classification","value":"classification"},{"label":"regression","value":"regression"}],
                    value="classification"
                ), md=3),
                dbc.Col(dbc.Checklist(
                    id="design-models",
                    options=MODEL_OPTIONS,
                    value=["xgboost"],
                    inline=True,
                    style={"marginTop": "6px"}
                ), md=9),
            ], className="g-2"),
            html.Div(id="design-model-params", className="mt-2"),
        ])
    ], className="mb-3"),

    # 5) Create
    dbc.Row([
        dbc.Col(dbc.Button("Create Analysis & Task(s)", id="design-btn-create", color="primary", disabled=True), width="auto"),
        dbc.Col(html.Div(id="design-created-info"), width=True),
    ], className="g-2 mb-4"),

    # Preview Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Dataset Preview")),
        dbc.ModalBody(html.Div(id="design-preview-table", style={"overflowX": "auto","overflowY": "auto","maxHeight": "70vh"})),
        dbc.ModalFooter(dbc.Button("Close", id="preview-close", className="ms-auto", n_clicks=0)),
    ], id="preview-modal", is_open=False, size="xl", scrollable=False, centered=True),

    # Feature Select Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Select Features (X)")),
        dbc.ModalBody([
            html.Div(
                id="feature-checklist-wrapper",
                children=dbc.Checklist(id="feature-checklist", options=[], value=[]),
                style={"maxHeight":"40vh","overflowY":"auto","overflowX":"auto","whiteSpace":"nowrap"}
            ),
            dbc.ButtonGroup([
                dbc.Button("Select All", id="feature-select-all", color="secondary"),
                dbc.Button("Clear All", id="feature-clear-all", color="secondary", outline=True),
                dbc.Button("Apply", id="feature-apply", color="primary"),
            ], className="mt-2"),
        ]),
    ], id="feature-modal", is_open=False, size="lg", scrollable=True, centered=True),
], fluid=True)

# Context 초기화
@callback(Output("design-project-id","data"), Input("design-url","href"))
def _init_ctx(href):
    pid = None
    if href:
        q = up.urlparse(href).query
        params = dict(up.parse_qsl(q))
        pid = params.get("project_id")
    if pid:
        return pid
    projs = api.list_projects()
    if projs:
        return projs[0]["id"]
    created = api.create_project("Default Project")
    return created["id"]

# 업로드
@callback(
    Output("design-dataset-uri", "data"),
    Output("design-upload-status", "children"),
    Output("design-upload-meta", "data"),
    Input("design-upload", "contents"),
    State("design-upload", "filename"),
    prevent_initial_call=True
)
def _on_upload(contents, filename):
    if not contents:
        return no_update, dbc.Badge("yet", color="warning"), no_update
    try:
        info = api.upload_file_from_contents(contents, filename or "uploaded.dat")
        meta = {"original_name": info.get("original_name") or (filename or "")}
        return info["dataset_uri"], dbc.Badge("ready", color="primary"), meta
    except Exception:
        return no_update, dbc.Badge("fail", color="danger"), no_update

# Preview 모달
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

# 컬럼 옵션 채우기
@callback(
    Output("design-sel-target","options"),
    Output("feature-checklist","options"),
    Output("design-columns","data"),
    Input("design-dataset-uri","data"),
    prevent_initial_call=True
)
def _fill_columns(dataset_uri):
    if not dataset_uri:
        return [], [], None
    prev = api.preview_dataset(dataset_uri, 50)
    cols = prev["columns"]
    opts = [{"label": c, "value": c} for c in cols]
    return opts, opts, cols

# Feature 모달 열고 닫기
@callback(
    Output("feature-modal","is_open"),
    Input("open-feature-modal","n_clicks"),
    Input("feature-apply","n_clicks"),
    State("feature-modal","is_open"),
    prevent_initial_call=True
)
def _feature_modal_is_open(open_n, apply_n, is_open):
    trig = dash.ctx.triggered_id
    if trig == "open-feature-modal":
        return True
    if trig == "feature-apply":
        return False
    return is_open

# Feature 체크 제어
@callback(
    Output("feature-checklist", "value"),
    Input("feature-checklist", "options"),
    Input("feature-select-all", "n_clicks"),
    Input("feature-clear-all", "n_clicks"),
    Input("design-sel-target", "value"),
    State("feature-checklist", "value"),
    prevent_initial_call=True
)
def _feature_select_control(options, sel_all, clr_all, target, current):
    trig = dash.ctx.triggered_id
    opts = options or []
    all_vals = [o["value"] for o in opts]

    def without_target(vals):
        return [v for v in vals if v != target] if target else vals

    if trig == "feature-select-all":
        return without_target(all_vals)
    if trig == "feature-clear-all":
        return []
    if trig == "feature-checklist":
        return without_target(all_vals)
    if trig == "design-sel-target":
        return without_target(current or [])
    if trig == "feature-checklist":
        return without_target(all_vals)
    return no_update

# Apply → 선택 스토어/요약
@callback(
    Output("design-features-selected","data"),
    Output("design-feature-summary","children"),
    Input("feature-apply","n_clicks"),
    Input("design-sel-target","value"),
    State("feature-checklist","value"),
    prevent_initial_call=True
)
def _apply_features(n_apply, target, selected):
    selected = selected or []
    if target:
        selected = [c for c in selected if c != target]
    summary = (html.Span("Features: (none)", className="text-muted")
               if not selected else
               html.Span(f"Features: {len(selected)} selected", className="text-muted"))
    return selected, summary

# 모델 파라미터 아코디언
@callback(
    Output("design-model-params", "children"),
    Input("design-models", "value"),
    Input("design-task-type", "value"),
)
def _render_model_params(models, task_type):
    models = models or []
    return _build_params_accordion(models, task_type or "classification")

# 버튼 활성화
@callback(
    Output("design-btn-create","disabled"),
    Input("design-dataset-uri","data"),
    Input("design-sel-target","value"),
)
def _btn_enable(uri, target):
    return not (bool(uri) and bool(target))

# 생성 + Train 페이지 이동 링크(Train all + 각 Task 링크)
@callback(
    Output("design-analysis-id","data"),
    Output("design-created-info","children"),
    Input("design-btn-create","n_clicks"),
    State("design-project-id","data"),
    State("design-dataset-uri","data"),
    State("design-upload-meta","data"),
    State("design-sel-target","value"),
    State("design-features-selected","data"),
    State("design-task-type","value"),
    State("design-models","value"),
    State({"type":"design-param","model":ALL,"key":ALL}, "id"),
    State({"type":"design-param","model":ALL,"key":ALL}, "value"),
    State("design-split-test","value"),
    State("design-split-seed","value"),
    State("design-sample-enable","value"),
    State("design-sample-cap","value"),
    prevent_initial_call=True
)
def _create_all(n, project_id, dataset_uri, upload_meta, target, features, task_type, model_list,
                param_ids, param_vals, test_size, seed, sample_enable, sample_cap):
    if not (project_id and dataset_uri and target and model_list):
        return no_update, dbc.Alert("Missing project/dataset/target/models", color="danger")

    split = {"test_size": float(test_size or 0.2), "random_state": int(seed or 42)}
    sampling = None
    if sample_enable and "on" in (sample_enable or []):
        sampling = {"method": "stratified_cap", "cap_per_class": int(sample_cap or 10000)}

    # 파라미터 override 수집
    overrides: Dict[str, Dict[str, Any]] = {}
    if param_ids and param_vals:
        for pid, val in zip(param_ids, param_vals):
            m = pid.get("model")
            k = pid.get("key")
            if not m or not k:
                continue
            parsed = None
            if isinstance(val, str):
                s = val.strip()
                try:
                    parsed = ast.literal_eval(s)
                except Exception:
                    try:
                        parsed = float(s) if ("." in s or "e" in s.lower()) else int(s)
                    except Exception:
                        parsed = s
            else:
                parsed = val
            overrides.setdefault(m, {})[k] = parsed

    # Analysis 생성 (+ 원본 파일명 메모는 Repo/DB 스키마에 맞게 백엔드에서 처리)
    a = api.create_analysis(project_id, "My Analysis", dataset_uri)
    aid = a["id"]

    # Task 생성(모델별)
    created = []
    for model_family in (model_list or []):
        preset_key = f"{model_family}:{task_type}"
        model_params = MODEL_PRESETS.get(preset_key, {}).copy()
        if model_family in overrides:
            model_params.update({k: v for k, v in overrides[model_family].items() if v is not None and v != ""})

        t = api.create_task(
            analysis_id=aid,
            task_type=task_type,
            target=target,
            model_family=model_family,
            model_params=model_params,
            features=features or None,
            split=split,
            sampling=sampling,
        )
        created.append(t)

    # Train 페이지로 이동할 수 있는 링크(여러 task를 meta와 함께 전달)
    meta = {
        t["id"]: {
            "model_family": t.get("model_family"),
            "task_type": t.get("task_type"),
            "dataset_original_name": (upload_meta or {}).get("original_name"),
        } for t in created
    }
    task_ids = ",".join([t["id"] for t in created])
    meta_q = up.quote_plus(json.dumps(meta, ensure_ascii=False))
    train_url = f"/analysis/train?task_ids={task_ids}&meta={meta_q}"

    msg = [html.Div(f"Analysis created: {aid}")]
    msg += [
        html.Div([
            f"Task: {t['id']} ({t['model_family']}, {t['task_type']}) — ",
            dcc.Link("Go to Train →", href=f"/analysis/train?task_id={t['id']}")
        ]) for t in created
    ]
    msg.append(html.Hr())
    msg.append(dcc.Link("Train ALL →", href=train_url, className="btn btn-outline-primary"))
    return aid, dbc.Alert(msg, color="success")