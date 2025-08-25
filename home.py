# backend/app/ui/pages/home.py

import dash
from dash import html, dcc, callback, Input, Output, State, ALL, no_update
import dash_bootstrap_components as dbc

from app.ui.clients import api_client as api

dash.register_page(__name__, path="/", name="Home")

# ──────────────────────────────────
# Layout
# ──────────────────────────────────
layout = dbc.Container([
    dcc.Location(id="home-url"),
    dcc.Store(id="home-refresh", data=0),   # 리스트 새로고침 트리거용 카운터

    html.H2("Projects", className="mb-3"),

    # 입력/생성 구역
    dbc.Row([
        dbc.Col(
            dbc.Input(id="home-proj-name", placeholder="New project name", type="text"),
            md=6
        ),
        dbc.Col(
            dbc.Button("Create", id="home-btn-create", color="primary"),
            width="auto"
        ),
    ], className="g-2 mb-3"),

    # 프로젝트 목록
    html.Div(id="home-proj-list"),
], fluid=True)


# ──────────────────────────────────
# 목록 렌더 (URL 진입 또는 refresh 시 갱신)
# ──────────────────────────────────
@callback(
    Output("home-proj-list", "children"),
    Input("home-url", "href"),
    Input("home-refresh", "data"),
    prevent_initial_call=False,
)
def _render_projects(_href, _refresh):
    try:
        projs = api.list_projects() or []
    except Exception as e:
        return dbc.Alert(f"Failed to load projects: {e}", color="danger")

    if not projs:
        return dbc.Alert("No projects yet. Create one above.", color="secondary")

    items = []
    for p in projs:
        pid = p.get("id")
        name = p.get("name") or "(no name)"

        row = dbc.Row([
            dbc.Col(html.B(name), md=4),
            dbc.Col(html.Code(pid), md=4),
            dbc.Col(
                dbc.ButtonGroup([
                    dcc.Link(
                        dbc.Button("Open", color="success", outline=True, size="sm"),
                        href=f"/analysis/design?project_id={pid}",
                        refresh=True  # 페이지 이동 시 새로 고침
                    ),
                    dbc.Button(
                        "Delete",
                        id={"type": "home-del", "pid": pid},
                        color="danger",
                        outline=True,
                        size="sm",
                        n_clicks=0
                    ),
                ]),
                md=4,
                className="text-end"
            )
        ], className="align-items-center py-1 border-bottom")

        items.append(row)

    header = dbc.Row([
        dbc.Col(html.Small("Name"), md=4, className="text-muted"),
        dbc.Col(html.Small("ID"), md=4, className="text-muted"),
        dbc.Col("", md=4)
    ], className="pb-2 border-bottom mb-2")

    return html.Div([header] + items)


# ──────────────────────────────────
# 생성/삭제를 하나의 콜백으로 처리 → 중복 출력 회피
# ──────────────────────────────────
@callback(
    Output("home-refresh", "data"),
    Input("home-btn-create", "n_clicks"),
    Input({"type": "home-del", "pid": ALL}, "n_clicks"),
    State("home-proj-name", "value"),
    State("home-refresh", "data"),
    prevent_initial_call=True,
)
def _create_or_delete(n_create, n_del_list, name, refresh_cnt):
    trig = dash.ctx.triggered_id
    refresh_cnt = int(refresh_cnt or 0)

    # 생성 버튼
    if trig == "home-btn-create":
        nm = (name or "").strip()
        if not nm:
            return no_update
        try:
            api.create_project(nm)
        except Exception:
            # 실패해도 화면 멈추지 않게 no_update
            return no_update
        return refresh_cnt + 1

    # 삭제 버튼들 (pattern-matching)
    if isinstance(trig, dict) and trig.get("type") == "home-del":
        pid = trig.get("pid")
        if not pid:
            return no_update
        try:
            api.delete_project(pid)
        except Exception:
            return no_update
        return refresh_cnt + 1

    return no_update