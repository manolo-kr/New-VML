# backend/app/ui/clients/api_client.py

import os
import io
import base64
import requests
from typing import Any, Dict, List, Optional

# 프론트 → 백엔드 API 접근 기본 경로
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


def _headers(token: Optional[str] = None) -> Dict[str, str]:
    h = {}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# ------------------------
# Upload / Preview
# ------------------------
def upload_file_from_contents(contents: str, filename: str, *, token: Optional[str] = None) -> Dict[str, Any]:
    """
    dcc.Upload contents -> /upload 멀티파트 업로드
    반환: {"dataset_uri": "file://...", "original_name": "<원본파일이름>"}
    """
    if not contents:
        raise ValueError("no contents")
    if "," not in contents:
        raise ValueError("invalid data url")
    _, b64data = contents.split(",", 1)
    try:
        raw = base64.b64decode(b64data)
    except Exception as e:
        raise ValueError(f"base64 decode failed: {e}")

    files = {"f": (filename, io.BytesIO(raw))}
    r = requests.post(_url("/upload"), files=files, headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()


def preview_dataset(dataset_uri: str, limit: int = 50, *, token: Optional[str] = None) -> Dict[str, Any]:
    payload = {"dataset_uri": dataset_uri, "limit": int(limit)}
    r = requests.post(_url("/preview"), json=payload, headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()


# ------------------------
# Projects / Analyses / Tasks
# ------------------------
def create_project(name: str, *, token: Optional[str] = None) -> Dict[str, Any]:
    r = requests.post(_url("/projects"), json={"name": name}, headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()


def list_projects(*, token: Optional[str] = None) -> List[Dict[str, Any]]:
    r = requests.get(_url("/projects"), headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()


def delete_project(project_id: str, *, token: Optional[str] = None) -> Dict[str, Any]:
    r = requests.delete(_url(f"/projects/{project_id}"), headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json() if r.content else {"ok": True}


def create_analysis(project_id: str, name: str, dataset_uri: str,
                    *, dataset_original_name: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Any]:
    payload = {"project_id": project_id, "name": name, "dataset_uri": dataset_uri}
    if dataset_original_name:
        payload["dataset_original_name"] = dataset_original_name
    r = requests.post(_url("/analyses"), json=payload, headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()


def list_analyses(project_id: str, *, token: Optional[str] = None) -> List[Dict[str, Any]]:
    r = requests.get(_url(f"/projects/{project_id}/analyses"), headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()


def create_task(
    analysis_id: str,
    task_type: str,
    target: str,
    model_family: str,
    model_params: Dict[str, Any],
    *,
    features: Optional[List[str]] = None,
    split: Optional[Dict[str, Any]] = None,
    sampling: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
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

    r = requests.post(_url("/tasks"), json=payload, headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()


# ------------------------
# Train / Run
# ------------------------
def train_task(task_id: str, *, hpo: Optional[Dict[str, Any]] = None, extra: Optional[Dict[str, Any]] = None,
               token: Optional[str] = None) -> Dict[str, Any]:
    """
    extra 예: {"idempotency_key": "...", "force": True}
    """
    payload: Dict[str, Any] = {}
    if hpo:
        payload["hpo"] = hpo
    if extra:
        payload.update(extra)
    r = requests.post(_url(f"/tasks/{task_id}/train"), json=payload, headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()  # {"run_id": ...}


def get_run(run_id: str, *, token: Optional[str] = None) -> Dict[str, Any]:
    r = requests.get(_url(f"/runs/{run_id}"), headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()


def cancel_run(run_id: str, *, token: Optional[str] = None) -> Dict[str, Any]:
    r = requests.post(_url(f"/runs/{run_id}/cancel"), headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    if r.status_code == 404:
        return {"ok": False, "error": "cancel endpoint not found"}
    r.raise_for_status()
    return r.json() if r.content else {"ok": True}


# ------------------------
# Artifacts
# ------------------------
def get_artifact_json(run_id: str, name: str, *, token: Optional[str] = None) -> Dict[str, Any]:
    r = requests.get(_url(f"/runs/{run_id}/artifact"), params={"name": name}, headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()


def get_artifact_file(run_id: str, name: str, *, token: Optional[str] = None) -> bytes:
    r = requests.get(_url(f"/runs/{run_id}/artifact"), params={"name": name}, headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.content


def get_artifact_png_src(run_id: str, name: str, *, token: Optional[str] = None) -> Optional[str]:
    try:
        b = get_artifact_file(run_id, name, token=token)
        import base64 as _b64
        return "data:image/png;base64," + _b64.b64encode(b).decode()
    except Exception:
        return None


# ------------------------
# 유틸 (모델 네임스페이스 탐색)
# ------------------------
def list_models(run_id: str, *, token: Optional[str] = None) -> List[str]:
    """
    /runs/{id} 응답의 artifacts 가 모델 키별 맵이라면 그 키를 반환.
    아니라면 알려진 후보를 ping.
    """
    run = get_run(run_id, token=token)
    arts = run.get("artifacts") or {}
    if isinstance(arts, dict) and all(isinstance(v, dict) or v is None for v in arts.values()):
        return list(arts.keys())

    candidates = ["xgboost", "lightgbm", "catboost", "randomforest", "logreg", "svm", "elasticnet", "knn", "mlp"]
    present: List[str] = []
    for k in candidates:
        try:
            _ = get_artifact_json(run_id, f"models/{k}/curves/roc.json", token=token)
            present.append(k)
        except Exception:
            pass
    return present