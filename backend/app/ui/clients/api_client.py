# backend/app/ui/clients/api_client.py

import os
import io
import base64
import requests
from typing import Any, Dict, List, Optional

# ----- 설정 -----
API_BASE = os.getenv("API_BASE", "/api").strip()
API_DIR = os.getenv("API_DIR", "http://127.0.0.1:8065").strip()

def _normalize_base(s: str) -> str:
    if s.startswith("http://") or s.startswith("https://"):
        return s.rstrip("/")
    if not s.startswith("/"):
        s = "/" + s
    return s.rstrip("/")

API_BASE = _normalize_base(API_BASE)

def _url(p: str) -> str:
    if not p.startswith("/"):
        p = "/" + p
    return f"{API_DIR}{API_BASE}{p}"

DEFAULT_TIMEOUT = float(os.getenv("API_TIMEOUT", "30"))

# ----- 모듈 전역 토큰 관리 -----
_AUTH_TOKEN: Optional[str] = None

def set_auth(token: Optional[str]) -> None:
    global _AUTH_TOKEN
    _AUTH_TOKEN = token

def clear_auth() -> None:
    set_auth(None)

def _headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if _AUTH_TOKEN:
        h["Authorization"] = f"Bearer {_AUTH_TOKEN}"
    if extra:
        h.update(extra)
    return h

# ----- Auth -----
def login(username: str, password: str) -> Dict[str, Any]:
    r = requests.post(_url("/auth/login"), json={"username": username, "password": password}, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def logout() -> Dict[str, Any]:
    r = requests.post(_url("/auth/logout"), headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    clear_auth()
    return r.json() if r.content else {"ok": True}

# ----- Upload / Preview -----
def upload_file_from_contents(contents: str, filename: str) -> Dict[str, Any]:
    if not contents:
        raise ValueError("no contents")
    if "," not in contents:
        raise ValueError("invalid data url")
    _, b64data = contents.split(",", 1)
    raw = base64.b64decode(b64data)
    files = {"f": (filename, io.BytesIO(raw))}
    r = requests.post(_url("/upload"), files=files, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def preview_dataset(dataset_uri: str, limit: int = 50) -> Dict[str, Any]:
    payload = {"dataset_uri": dataset_uri, "limit": int(limit)}
    r = requests.post(_url("/preview"), json=payload, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

# ----- Projects / Analyses / Tasks -----
def create_project(name: str) -> Dict[str, Any]:
    r = requests.post(_url("/projects"), json={"name": name}, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def list_projects() -> List[Dict[str, Any]]:
    r = requests.get(_url("/projects"), headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def delete_project(project_id: str) -> Dict[str, Any]:
    r = requests.delete(_url(f"/projects/{project_id}"), headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json() if r.content else {"ok": True}

def create_analysis(project_id: str, name: str, dataset_uri: str, dataset_original_name: Optional[str] = None) -> Dict[str, Any]:
    payload = {"project_id": project_id, "name": name, "dataset_uri": dataset_uri}
    if dataset_original_name:
        payload["dataset_original_name"] = dataset_original_name
    r = requests.post(_url("/analyses"), json=payload, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def list_analyses(project_id: str) -> List[Dict[str, Any]]:
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

# ----- Train / Run -----
def train_task(task_id: str, hpo: Optional[Dict[str, Any]] = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if hpo:
        payload["hpo"] = hpo
    if extra:
        payload.update(extra)
    r = requests.post(_url(f"/tasks/{task_id}/train"), json=payload, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def get_run(run_id: str) -> Dict[str, Any]:
    r = requests.get(_url(f"/runs/{run_id}"), headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def cancel_run(run_id: str) -> Dict[str, Any]:
    r = requests.post(_url(f"/runs/{run_id}/cancel"), headers=_headers(), timeout=DEFAULT_TIMEOUT)
    if r.status_code == 404:
        return {"ok": False, "error": "cancel endpoint not found"}
    r.raise_for_status()
    return r.json() if r.content else {"ok": True}

# ----- Artifacts -----
def get_artifact_json(run_id: str, name: str) -> Dict[str, Any]:
    r = requests.get(_url(f"/runs/{run_id}/artifact"), params={"name": name}, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def get_artifact_file(run_id: str, name: str) -> bytes:
    r = requests.get(_url(f"/runs/{run_id}/artifact"), params={"name": name}, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.content