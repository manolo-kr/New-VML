# backend/app/queue_mongo.py
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime

from pymongo import MongoClient, ASCENDING
from bson import ObjectId

from .config import settings

# -------------------------------------------------------------------
# Mongo connections
# -------------------------------------------------------------------
_client = MongoClient(settings.MONGO_URI)
_db = _client[settings.MONGO_DB]
_jobs = _db[settings.MONGO_COLLECTION]  # 기본값 "jobs"

# -------------------------------------------------------------------
# Indexes
# -------------------------------------------------------------------
def ensure_indexes() -> None:
    """
    서버 시작 시 1회 호출 권장.
    - 활성 잡 조회(status + task_ref.task_id)
    - idem key 중복 방지(unique, sparse)
    """
    _jobs.create_index([("status", ASCENDING), ("task_ref.task_id", ASCENDING)])
    _jobs.create_index([("idempotency_key", ASCENDING)], unique=True, sparse=True)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _oid(s: str) -> ObjectId:
    return ObjectId(s)


# -------------------------------------------------------------------
# Basic queue API (compat)
# -------------------------------------------------------------------
def create_job(payload: Dict[str, Any]) -> str:
    """
    가장 단순한 큐잉: 활성 중복 체크 없이 무조건 insert.
    필요한 기본 필드 보강.
    """
    now = datetime.utcnow()
    doc = {
        **(payload or {}),
        "status": (payload.get("status") if payload and payload.get("status") else "queued"),
        "worker_id": (payload.get("worker_id") if payload else None),
        "progress": float(payload.get("progress", 0.0)) if payload else 0.0,
        "message": (payload.get("message") if payload else "") or "",
        "cancel_requested": bool(payload.get("cancel_requested", False)) if payload else False,
        "created_at": now,
        "updated_at": now,
    }
    ins = _jobs.insert_one(doc)
    return str(ins.inserted_id)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    try:
        return _jobs.find_one({"_id": _oid(job_id)})
    except Exception:
        return None


def set_job_fields(job_id: str, fields: Dict[str, Any]) -> None:
    fields = dict(fields or {})
    fields["updated_at"] = datetime.utcnow()
    _jobs.update_one({"_id": _oid(job_id)}, {"$set": fields})


# -------------------------------------------------------------------
# Advanced (idempotency + active-run guard)
# -------------------------------------------------------------------
def get_active_job_by_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    해당 task_id로 '진행 중'인(queued/running) 잡이 있는지 반환.
    cancel_requested=True 인지는 무시(=여전히 running일 수 있으니 워커에서 중단될 때까지 active).
    """
    return _jobs.find_one({
        "task_ref.task_id": task_id,
        "status": {"$in": ["queued", "running"]},
    })


def create_job_idempotent(
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = None,
    force: bool = False,
) -> str:
    """
    - force=False: 같은 task_id의 활성(queued/running) 잡이 있으면 그 run_id 반환(새로 안만듦).
    - idempotency_key 지정 시, 같은 key는 항상 같은 run_id 반환(unique index).
    - force=True: 활성 잡이 있더라도 무시하고 새로 생성.
    """
    # 1) task_id 기반 활성 중복 방지 (force가 아닌 경우만)
    task_ref = (payload or {}).get("task_ref") or {}
    task_id = task_ref.get("task_id")
    if not force and task_id:
        active = get_active_job_by_task(task_id)
        if active:
            return str(active["_id"])

    # 2) idempotency_key 기반 멱등
    if idempotency_key:
        prev = _jobs.find_one({"idempotency_key": idempotency_key})
        if prev:
            return str(prev["_id"])

    # 3) 신규 생성
    now = datetime.utcnow()
    doc = {
        **(payload or {}),
        "status": (payload.get("status") if payload and payload.get("status") else "queued"),
        "worker_id": (payload.get("worker_id") if payload else None),
        "progress": float(payload.get("progress", 0.0)) if payload else 0.0,
        "message": (payload.get("message") if payload else "") or "",
        "idempotency_key": idempotency_key or None,
        "cancel_requested": bool(payload.get("cancel_requested", False)) if payload else False,
        "created_at": now,
        "updated_at": now,
    }
    ins = _jobs.insert_one(doc)
    return str(ins.inserted_id)