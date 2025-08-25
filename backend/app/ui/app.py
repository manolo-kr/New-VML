# backend/app/ui/app.py
#
# Dash application factory with:
# - Global session stores (auth/project/design-state)
# - Top navbar showing user & client IP, and Logout
# - Auth guard that redirects unauthenticated users to /auth/login?next=...
# - Inactivity reminder (10-minute idle timer) with “Extend 10 min” button
# - No duplicate-callback outputs; all IDs are unique to this file.

from __future__ import annotations

import time
import urllib.parse as up
import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# ────────────────────────────────────────────────────────────────────
# Global stores available to every page (kept in sessionStorage)
# ────────────────────────────────────────────────────────────────────
GLOBAL_STORES = [
    dcc.Store(id="gs-auth", storage_type="session"),         # {"access_token": "...", "user": {...}, "ip": "..."}
    dcc.Store(id="gs-project", storage_type="session"),      # {"id": "...", "name": "..."}
    dcc.Store(id="gs-design-state", storage_type="session"), # {"analysis_id": "...", ...}
]

# These are purely internal to app-level guard/UX
APP_INTERNALS = [
    dcc.Store(id="guard-last-activity", storage_type="session"),  # epoch seconds of last activity
    dcc.Interval(id="guard-tick", interval=60_000, n_intervals=0), # 1 min tick
    dcc.Location(id="_guard_loc"),     # current location (read)
    dcc.Location(id="_guard_go"),      # programmatic redirect (write .href)
]

# Idle timeout (seconds). The toast appears at (IDLE_LIMIT - GRACE) seconds
IDLE_LIMIT_SEC = 10 * 60
GRACE_BEFORE_TOAST_SEC = 60

def _navbar() -> dbc.Navbar:
    return dbc.Navbar(
        dbc.Container([
            html.Div([
                dbc.NavbarBrand("Visual ML", class_name="me-3"),
                dbc.Nav(
                    [
                        dbc.NavItem(dcc.Link("Home", href="/", className="nav-link")),
                        dbc.NavItem(dcc.Link("Design", href="/analysis/design", className="nav-link")),
                        dbc.NavItem(dcc.Link("Train", href="/analysis/train", className="nav-link")),
                        dbc.NavItem(dcc.Link("Results", href="/analysis/results", className="nav-link")),
                        dbc.NavItem(dcc.Link("Compare", href="/analysis/compare", className="nav-link")),
                    ],
                    class_name="me-auto",
                    pills=False,
                ),
            ], className="d-flex align-items-center flex-grow-1"),

            # Right side: user/ip + Logout
            dbc.Nav(
                [
                    dbc.Badge(id="nav-user-badge", color="info", class_name="me-2"),
                    dbc.Badge(id="nav-ip-badge", color="secondary", class_name="me-3"),
                    dbc.Button("Logout", id="nav-logout", color="dark", outline=True, size="sm"),
                ],
                class_name="ms-auto align-items-center",
                navbar=True,
            ),
        ], fluid=True),
        color="dark",
        dark=True,
        class_name="mb-3",
    )

def _idle_toast() -> html.Div:
    """Small toast shown near the top-right when idle is near timeout."""
    return html.Div(
        dbc.Toast(
            [
                html.Div("Are you still there?", className="fw-bold mb-1"),
                html.Div("You’ll be logged out soon due to inactivity."),
                dbc.Button("Extend 10 min", id="guard-extend", color="primary", size="sm", class_name="mt-2"),
            ],
            id="guard-toast",
            header="Session expiring",
            icon="warning",
            dismissable=True,
            is_open=False,
            style={"position": "fixed", "top": "80px", "right": "16px", "zIndex": 1080},
        )
    )

def build_dash_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        use_pages=True,
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="Visual ML",
    )

    app.layout = dbc.Container(
        [
            *_navbar(),
        ], fluid=True
    )  # dummy to avoid type hints confusion

    # Real layout below (explicit for clarity)
    app.layout = dbc.Container(
        [
            # Router & global stores
            *_navbar(),
            dcc.Location(id="_page_location"),
            dcc.Store(id="_page_store"),
            *GLOBAL_STORES,
            *APP_INTERNALS,
            _idle_toast(),

            # Where pages render
            dash.page_container,
        ],
        fluid=True,
    )

    # ────────────────────────────────────────────────────────────────
    # Callbacks (no duplicate outputs)
    # ────────────────────────────────────────────────────────────────

    # 1) Auth guard: redirect unauthenticated users to /auth/login?next=...
    @callback(
        Output("_guard_go", "href"),
        Input("_guard_loc", "pathname"),
        State("_guard_loc", "search"),
        State("gs-auth", "data"),
        prevent_initial_call=False,
    )
    def _auth_guard(pathname, search, auth):
        # Always allow the login route and assets
        path = pathname or "/"
        if path.startswith("/auth/login") or path.startswith("/_dash") or path.startswith("/assets"):
            return no_update

        # If not logged in, send to /auth/login?next=<current>
        if not (auth and auth.get("access_token")):
            q = f"?next={up.quote(path + (search or ''), safe='/:&?=')}"
            return f"/auth/login{q}"

        return no_update

    # 2) Logout → clear gs-auth and go to /auth/login?next=<current>
    @callback(
        Output("gs-auth", "data"),
        Output("_guard_go", "href"),
        Input("nav-logout", "n_clicks"),
        State("_guard_loc", "pathname"),
        State("_guard_loc", "search"),
        prevent_initial_call=True,
    )
    def _logout(n, pathname, search):
        if not n:
            return no_update, no_update
        # Clear session auth and redirect to login
        nxt = (pathname or "/") + (search or "")
        return {}, f"/auth/login?next={up.quote(nxt, safe='/:&?=')}"

    # 3) Show username/IP on navbar
    @callback(
        Output("nav-user-badge", "children"),
        Output("nav-ip-badge", "children"),
        Input("gs-auth", "data"),
        prevent_initial_call=False,
    )
    def _paint_user(auth):
        user_label = "-"
        ip_label = "-"
        if auth and isinstance(auth, dict):
            u = auth.get("user") or {}
            name = u.get("username") or u.get("email") or "user"
            role = u.get("role") or ""
            user_label = f"{name}" + (f" ({role})" if role else "")
            ip_label = auth.get("ip") or "-"
        return user_label, ip_label

    # 4) Maintain last-activity timestamp
    @callback(
        Output("guard-last-activity", "data"),
        Input("_guard_loc", "pathname"),     # user navigates
        Input("guard-extend", "n_clicks"),   # user extends
        prevent_initial_call=False,
    )
    def _touch_last_activity(_path, _extend):
        # Whenever path changes or extend is clicked, refresh activity clock
        return int(time.time())

    # 5) Idle toast open/close logic
    @callback(
        Output("guard-toast", "is_open"),
        Input("guard-tick", "n_intervals"),
        Input("guard-extend", "n_clicks"),
        State("guard-last-activity", "data"),
        State("gs-auth", "data"),
        State("guard-toast", "is_open"),
        prevent_initial_call=False,
    )
    def _idle_toast_logic(_tick, _extend, last_ts, auth, is_open):
        # If not logged in, no toast
        if not (auth and auth.get("access_token")):
            return False

        now = int(time.time())
        last = int(last_ts or now)
        idle = now - last

        # Extend button closes the toast (and _touch_last_activity already refreshed the clock)
        if dash.ctx.triggered_id == "guard-extend":
            return False

        # Open when approaching timeout
        if idle >= (IDLE_LIMIT_SEC - GRACE_BEFORE_TOAST_SEC) and idle < IDLE_LIMIT_SEC:
            return True

        # Auto-close when freshly active
        if idle < (IDLE_LIMIT_SEC - GRACE_BEFORE_TOAST_SEC):
            return False

        # (Optional) Here you could also auto-logout if idle >= IDLE_LIMIT_SEC
        return is_open

    return app