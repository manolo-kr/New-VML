# backend/app/ui/clients/api_client.py

import os
import io
import base64
import time
import requests
from typing import Any, Dict, List, Optional

API_DIR = os.getenv("API_DIR", "http://127.0.0.1:8065").rstrip("/")
API_BASE = os.getenv("API_BASE", "/api").rstrip("/")

DEFAULT_TIMEOUT = float(os.getenv("API_TIMEOUT", "30"))
TOKEN_REFRESH_SKEW = 60

_auth_cache: Dict[str, Any] = {}

def set_auth(token_bundle: Optional[Dict[str, Any]]) -> None:
    global _auth_cache
    _auth_cache = token_bundle or {}

def _access_near_expiry() -> bool:
    try:
        exp = int(_auth_cache.get("access_exp") or 0)
        return (exp - int(time.time())) <= TOKEN_REFRESH_SKEW
    except Exception:
        return True

def _maybe_refresh() -> None:
    global _auth_cache
    if not _auth_cache or not _auth_cache.get("refresh_token"):
        return
    if not _access_near_expiry():
        return
    try:
        r = requests.post(f"{API_DIR}{API_BASE}/auth/refresh".replace("//auth", "/auth"),
                          json={"refresh_token": _auth_cache["refresh_token"]},
                          timeout=DEFAULT_TIMEOUT)
        if r.status_code == 200:
            _auth_cache.update(r.json())
        else:
            _auth_cache = {}
    except Exception:
        _auth_cache = {}

def _url(p: str) -> str:
    if not p.startswith("/"): p = "/" + p
    return f"{API_DIR}{API_BASE}{p}"

def _headers() -> Dict[str, str]:
    tok = _auth_cache.get("access_token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}

def upload_file_from_contents(contents: str, filename: str) -> Dict[str, Any]:
    _maybe_refresh()
    if not contents: raise ValueError("no contents")
    if "," not in contents: raise ValueError("invalid data url")
    _, b64data = contents.split(",", 1)
    raw = base64.b64decode(b64data)
    files = {"f": (filename, io.BytesIO(raw))}
    r = requests.post(_url("/upload"), files=files, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def preview_dataset(dataset_uri: str, limit: int = 50) -> Dict[str, Any]:
    _maybe_refresh()
    payload = {"dataset_uri": dataset_uri, "limit": int(limit)}
    r = requests.post(_url("/preview"), json=payload, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def create_project(name: str) -> Dict[str, Any]:
    _maybe_refresh()
    r = requests.post(_url("/projects"), json={"name": name}, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def list_projects() -> List[Dict[str, Any]]:
    _maybe_refresh()
    r = requests.get(_url("/projects"), headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def delete_project(project_id: str) -> Dict[str, Any]:
    _maybe_refresh()
    r = requests.delete(_url(f"/projects/{project_id}"), headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json() if r.content else {"ok": True}

def create_analysis(project_id: str, name: str, dataset_uri: str, dataset_original_name: Optional[str] = None) -> Dict[str, Any]:
    _maybe_refresh()
    payload = {"project_id": project_id, "name": name, "dataset_uri": dataset_uri}
    if dataset_original_name:
        payload["dataset_original_name"] = dataset_original_name
    r = requests.post(_url("/analyses"), json=payload, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def list_analyses(project_id: str) -> List[Dict[str, Any]]:
    _maybe_refresh()
    r = requests.get(_url(f"/projects/{project_id}/analyses"), headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def create_task(
    analysis_id: str,
    task_type: str,
    target: str,
    model_family: str,
    model_params: Dict[str, Any],
    features: Optional[List[str]] = None,
    split: Optional[Dict[str, Any]] = None,
    sampling: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    _maybe_refresh()
    payload = {
        "analysis_id": analysis_id,
        "task_type": task_type,
        "target": target,
        "model_family": model_family,
        "model_params": model_params or {},
        "split": split or {"test_size": 0.2, "random_state": 42},
    }
    if features:
        payload["features"] = features
    if sampling:
        payload["sampling"] = sampling
    r = requests.post(_url("/tasks"), json=payload, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def train_task(task_id: str, hpo: Optional[Dict[str, Any]] = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _maybe_refresh()
    payload: Dict[str, Any] = {}
    if hpo: payload["hpo"] = hpo
    if extra: payload.update(extra)
    r = requests.post(_url(f"/tasks/{task_id}/train"), json=payload, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def get_run(run_id: str) -> Dict[str, Any]:
    _maybe_refresh()
    r = requests.get(_url(f"/runs/{run_id}"), headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def cancel_run(run_id: str) -> Dict[str, Any]:
    _maybe_refresh()
    r = requests.post(_url(f"/runs/{run_id}/cancel"), headers=_headers(), timeout=DEFAULT_TIMEOUT)
    if r.status_code == 404:
        return {"ok": False, "error": "cancel endpoint not found"}
    r.raise_for_status()
    return r.json() if r.content else {"ok": True}

def get_artifact_json(run_id: str, name: str) -> Dict[str, Any]:
    _maybe_refresh()
    r = requests.get(_url(f"/runs/{run_id}/artifact"), params={"name": name}, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def get_artifact_file(run_id: str, name: str) -> bytes:
    _maybe_refresh()
    r = requests.get(_url(f"/runs/{run_id}/artifact"), params={"name": name}, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.content