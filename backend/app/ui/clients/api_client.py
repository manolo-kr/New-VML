# backend/app/ui/clients/api_client.py

import os
import io
import base64
import requests
from typing import Any, Dict, List, Optional

# ---- 기본 경로 설정 ----------------------------------------------------
# 백엔드 FastAPI가 같은 호스트에서 /api 로 서비스된다고 가정
API_DIR = os.getenv("API_DIR", "http://127.0.0.1:8065").rstrip("/")
API_BASE = os.getenv("API_BASE", "/api").strip()
if not API_BASE.startswith("/"):
    API_BASE = "/" + API_BASE
API_BASE = API_BASE.rstrip("/")

DEFAULT_TIMEOUT = float(os.getenv("API_TIMEOUT", "30"))

def _url(p: str) -> str:
    if not p.startswith("/"):
        p = "/" + p
    return f"{API_DIR}{API_BASE}{p}"

# 전역 토큰 보관 (gs-auth를 직접 접근할 수 없으니, 페이지 콜백에서 set_bearer_token 호출)
_BEARER: Optional[str] = None

def set_bearer_token(token: Optional[str]) -> None:
    """페이지 콜백에서 gs-auth 갱신될 때마다 호출해 Authorization 동기화"""
    global _BEARER
    _BEARER = token or None

def _auth_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if _BEARER:
        h["Authorization"] = f"Bearer {_BEARER}"
    if extra:
        h.update(extra)
    return h

# ---- Auth --------------------------------------------------------------
def login(username: str, password: str) -> Dict[str, Any]:
    """
    /auth/login → {"access_token": "...", "user": {...}}
    로그인 성공 시 set_bearer_token은 호출자(페이지 콜백)에서 처리
    """
    r = requests.post(
        _url("/auth/login"),
        json={"username": username, "password": password},
        timeout=DEFAULT_TIMEOUT,
        headers=_auth_headers()
    )
    r.raise_for_status()
    return r.json()

def refresh(token: str) -> Dict[str, Any]:
    r = requests.post(_url("/auth/refresh"), json={"token": token}, timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json()

# ---- Upload / Preview --------------------------------------------------
def upload_file_from_contents(contents: str, filename: str) -> Dict[str, Any]:
    """
    dcc.Upload contents ("data:<mime>;base64,<b64data>") → /upload 멀티파트 업로드.
    응답: {"dataset_uri": "file://...", "original_name": "<원본파일이름>"}
    """
    if not contents:
        raise ValueError("no contents")

    if "," not in contents:
        raise ValueError("invalid data url")
    _, b64data = contents.split(",", 1)
    raw = base64.b64decode(b64data)

    files = {"f": (filename, io.BytesIO(raw))}
    r = requests.post(_url("/upload"), files=files, timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json()

def preview_dataset(dataset_uri: str, limit: int = 50) -> Dict[str, Any]:
    payload = {"dataset_uri": dataset_uri, "limit": int(limit)}
    r = requests.post(_url("/preview"), json=payload, timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json()

# ---- Projects / Analyses / Tasks --------------------------------------
def create_project(name: str) -> Dict[str, Any]:
    r = requests.post(_url("/projects"), json={"name": name}, timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json()

def list_projects() -> List[Dict[str, Any]]:
    r = requests.get(_url("/projects"), timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json()

def delete_project(project_id: str) -> Dict[str, Any]:
    r = requests.delete(_url(f"/projects/{project_id}"), timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json() if r.content else {"ok": True}

def create_analysis(project_id: str, name: str, dataset_uri: str, dataset_original_name: Optional[str] = None) -> Dict[str, Any]:
    payload = {"project_id": project_id, "name": name, "dataset_uri": dataset_uri}
    if dataset_original_name:
        payload["dataset_original_name"] = dataset_original_name
    r = requests.post(_url("/analyses"), json=payload, timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json()

def list_analyses(project_id: str) -> List[Dict[str, Any]]:
    r = requests.get(_url(f"/projects/{project_id}/analyses"), timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
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

    r = requests.post(_url("/tasks"), json=payload, timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json()

# ---- Train / Run -------------------------------------------------------
def train_task(task_id: str, hpo: Optional[Dict[str, Any]] = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if hpo:
        payload["hpo"] = hpo
    if extra:
        payload.update(extra)
    r = requests.post(_url(f"/tasks/{task_id}/train"), json=payload, timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json()  # {"run_id": ...}

def get_run(run_id: str) -> Dict[str, Any]:
    r = requests.get(_url(f"/runs/{run_id}"), timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json()

def cancel_run(run_id: str) -> Dict[str, Any]:
    r = requests.post(_url(f"/runs/{run_id}/cancel"), timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    if r.status_code == 404:
        return {"ok": False, "error": "cancel endpoint not found"}
    r.raise_for_status()
    return r.json() if r.content else {"ok": True}

# ---- Artifacts ---------------------------------------------------------
def get_artifact_json(run_id: str, name: str) -> Dict[str, Any]:
    r = requests.get(_url(f"/runs/{run_id}/artifact"), params={"name": name}, timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.json()

def get_artifact_file(run_id: str, name: str) -> bytes:
    r = requests.get(_url(f"/runs/{run_id}/artifact"), params={"name": name}, timeout=DEFAULT_TIMEOUT, headers=_auth_headers())
    r.raise_for_status()
    return r.content