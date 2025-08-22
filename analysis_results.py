# backend/app/ui/pages/analysis_results.py

from __future__ import annotations
from typing import Dict, Any, List
import urllib.parse as up

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/analysis/results", name="Results")

layout = dbc.Container([
    dcc.Location(id="results-url"),
    dcc.Store(id="gs-auth", storage_type="session"),
    dcc.Store(id="results-run-id"),
    dcc.Store(id="results-model-key"),

    html.H2("Results"),

    dbc.Row([
        dbc.Col(dbc.Input(id="results-run-input", placeholder="Run ID", type="text"), md=4),
        dbc.Col(dbc.Button("Load", id="results-load", color="primary"), width="auto"),
        dbc.Col(dbc.Select(id="results-model-select", options=[], placeholder="Select model"), md=4),
    ], className="g-2 mb-3"),

    dbc.Tabs([
        dbc.Tab(label="Metrics", tab_id="tab-metrics", children=html.Div(id="results-metrics", className="p-3")),
        dbc.Tab(label="Curves",  tab_id="tab-curves",  children=html.Div(id="results-curves",  className="p-3")),
        dbc.Tab(label="Confusion", tab_id="tab-conf", children=html.Div(id="results-conf",    className="p-3")),
        dbc.Tab(label="KS / Gain / Lift", tab_id="tab-ks", children=html.Div(id="results-ks", className="p-3")),
        dbc.Tab(label="Threshold sweep", tab_id="tab-th", children=html.Div(id="results-th",  className="p-3")),
    ], id="results-tabs", active_tab="tab-metrics"),
], fluid=True)


# ---- URL init -------------------------------------------------------
@callback(
    Output("results-run-id", "data"),
    Output("results-run-input", "value"),
    Input("results-url", "href"),
    prevent_initial_call=False
)
def _init_run(href):
    rid = ""
    if href:
        q = up.urlparse(href).query
        params = dict(up.parse_qsl(q))
        rid = params.get("run_id") or ""
    return rid, rid


# ---- Load run info & model options ---------------------------------
@callback(
    Output("results-model-select", "options"),
    Output("results-model-select", "value"),
    Input("results-load", "n_clicks"),
    State("results-run-input", "value"),
    State("gs-auth", "data"),
    prevent_initial_call=True
)
def _load_models(_n, run_id, auth):
    token = (auth or {}).get("access_token")
    if not run_id:
        return [], None
    try:
        models = api.list_models(run_id, token)
        opts = [{"label": m, "value": m} for m in models]
        return opts, (models[0] if models else None)
    except Exception:
        return [], None


# ---- Store selected model ------------------------------------------
@callback(
    Output("results-model-key", "data"),
    Input("results-model-select", "value"),
)
def _sel_model(mkey):
    return mkey


# ---- Metrics tab ----------------------------------------------------
@callback(
    Output("results-metrics", "children"),
    Input("results-model-key", "data"),
    State("results-run-input", "value"),
    State("gs-auth", "data"),
)
def _render_metrics(model_key, run_id, auth):
    token = (auth or {}).get("access_token")
    if not (run_id and model_key):
        return dbc.Alert("Select a run and model.", color="secondary")
    try:
        j = api.get_artifact_json(run_id, f"models/{model_key}/metrics/metrics.json", token)
    except Exception:
        return dbc.Alert("No metrics.", color="warning")
    rows = []
    for k, v in j.items():
        rows.append(html.Tr([html.Td(k), html.Td(str(v))]))
    return dbc.Table([html.Thead(html.Tr([html.Th("metric"), html.Th("value")])), html.Tbody(rows)],
                     bordered=True, hover=True, responsive=True)


# ---- Curves tab (ROC / PR) -----------------------------------------
@callback(
    Output("results-curves", "children"),
    Input("results-model-key", "data"),
    State("results-run-input", "value"),
    State("gs-auth", "data"),
)
def _render_curves(model_key, run_id, auth):
    token = (auth or {}).get("access_token")
    if not (run_id and model_key):
        return dbc.Alert("Select a run and model.", color="secondary")
    parts: List[html.Div] = []

    try:
        roc = api.get_artifact_json(run_id, f"models/{model_key}/curves/roc.json", token)
        roc_rows = [html.Tr([html.Td(str(t)), html.Td(str(p))]) for t, p in zip(roc.get("fpr",[]), roc.get("tpr",[]))]
        parts.append(dbc.Card([
            dbc.CardHeader("ROC"),
            dbc.CardBody(dbc.Table([html.Thead(html.Tr([html.Th("fpr"), html.Th("tpr")])),
                                    html.Tbody(roc_rows)], bordered=True, hover=True, responsive=True))
        ], className="mb-3"))
    except Exception:
        parts.append(dbc.Alert("No ROC curve.", color="warning"))

    try:
        pr = api.get_artifact_json(run_id, f"models/{model_key}/curves/pr.json", token)
        pr_rows = [html.Tr([html.Td(str(p)), html.Td(str(r))]) for p, r in zip(pr.get("precision",[]), pr.get("recall",[]))]
        parts.append(dbc.Card([
            dbc.CardHeader("PR"),
            dbc.CardBody(dbc.Table([html.Thead(html.Tr([html.Th("precision"), html.Th("recall")])),
                                    html.Tbody(pr_rows)], bordered=True, hover=True, responsive=True))
        ]))
    except Exception:
        parts.append(dbc.Alert("No PR curve.", color="warning"))

    return html.Div(parts)


# ---- Confusion tab --------------------------------------------------
@callback(
    Output("results-conf", "children"),
    Input("results-model-key", "data"),
    State("results-run-input", "value"),
    State("gs-auth", "data"),
)
def _render_conf(model_key, run_id, auth):
    token = (auth or {}).get("access_token")
    if not (run_id and model_key):
        return dbc.Alert("Select a run and model.", color="secondary")
    try:
        cm = api.get_artifact_json(run_id, f"models/{model_key}/confusion/confusion.json", token)
    except Exception:
        return dbc.Alert("No confusion matrix.", color="warning")
    labels = cm.get("labels", [])
    mat = cm.get("matrix", [])
    thead = html.Thead(html.Tr([html.Th("")] + [html.Th(f"pred:{l}") for l in labels]))
    body_rows = []
    for i, row in enumerate(mat):
        body_rows.append(html.Tr([html.Td(f"true:{labels[i]}")] + [html.Td(str(v)) for v in row]))
    return dbc.Table([thead, html.Tbody(body_rows)], bordered=True, hover=True, responsive=True)


# ---- KS/Gain/Lift tab ----------------------------------------------
@callback(
    Output("results-ks", "children"),
    Input("results-model-key", "data"),
    State("results-run-input", "value"),
    State("gs-auth", "data"),
)
def _render_ks(model_key, run_id, auth):
    token = (auth or {}).get("access_token")
    if not (run_id and model_key):
        return dbc.Alert("Select a run and model.", color="secondary")
    cards = []
    # KS
    try:
        ks = api.get_artifact_json(run_id, f"models/{model_key}/curves/ks.json", token)
        rows = [html.Tr([html.Td(str(x)), html.Td(str(y))]) for x, y in zip(ks.get("x",[]), ks.get("y",[]))]
        cards.append(dbc.Card([dbc.CardHeader("KS"), dbc.CardBody(dbc.Table([html.Thead(html.Tr([html.Th("x"), html.Th("y")])),
                                                                            html.Tbody(rows)], bordered=True, hover=True, responsive=True))], className="mb-3"))
    except Exception:
        cards.append(dbc.Alert("No KS.", color="warning"))
    # Gain
    try:
        gain = api.get_artifact_json(run_id, f"models/{model_key}/curves/gain.json", token)
        rows = [html.Tr([html.Td(str(x)), html.Td(str(y))]) for x, y in zip(gain.get("x",[]), gain.get("y",[]))]
        cards.append(dbc.Card([dbc.CardHeader("Gain"), dbc.CardBody(dbc.Table([html.Thead(html.Tr([html.Th("x"), html.Th("y")])),
                                                                               html.Tbody(rows)], bordered=True, hover=True, responsive=True))], className="mb-3"))
    except Exception:
        cards.append(dbc.Alert("No Gain.", color="warning"))
    # Lift
    try:
        lift = api.get_artifact_json(run_id, f"models/{model_key}/curves/lift.json", token)
        rows = [html.Tr([html.Td(str(x)), html.Td(str(y))]) for x, y in zip(lift.get("x",[]), lift.get("y",[]))]
        cards.append(dbc.Card([dbc.CardHeader("Lift"), dbc.CardBody(dbc.Table([html.Thead(html.Tr([html.Th("x"), html.Th("y")])),
                                                                               html.Tbody(rows)], bordered=True, hover=True, responsive=True))]))
    except Exception:
        cards.append(dbc.Alert("No Lift.", color="warning"))
    return html.Div(cards)


# ---- Threshold sweep tab -------------------------------------------
@callback(
    Output("results-th", "children"),
    Input("results-model-key", "data"),
    State("results-run-input", "value"),
    State("gs-auth", "data"),
)
def _render_th(model_key, run_id, auth):
    token = (auth or {}).get("access_token")
    if not (run_id and model_key):
        return dbc.Alert("Select a run and model.", color="secondary")
    try:
        th = api.get_artifact_json(run_id, f"models/{model_key}/metrics/thresholds.json", token)
    except Exception:
        return dbc.Alert("No threshold sweep.", color="warning")
    head = html.Thead(html.Tr([html.Th(k) for k in th["columns"]]))
    body = html.Tbody([html.Tr([html.Td(str(v)) for v in row]) for row in th["rows"]])
    return dbc.Table([head, body], bordered=True, hover=True, responsive=True)