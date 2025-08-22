# backend/app/queue_mongo.py

from typing import Any, Dict, Optional
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from bson import ObjectId
from .config import MONGO_URI, MONGO_DB, MONGO_COLLECTION

_client = MongoClient(MONGO_URI)
_db = _client[MONGO_DB]
_jobs = _db[MONGO_COLLECTION]

# 인덱스(선택)
def ensure_indexes() -> None:
    _jobs.create_index([("status", ASCENDING)])
    _jobs.create_index([("task_ref.task_id", ASCENDING)])
    _jobs.create_index([("idempotency_key", ASCENDING)], unique=True, sparse=True)

def create_job(payload: Dict[str, Any]) -> str:
    now = datetime.utcnow()
    doc = {
        **payload,
        "status": payload.get("status", "queued"),
        "worker_id": payload.get("worker_id", None),
        "progress": float(payload.get("progress", 0.0)),
        "message": payload.get("message", ""),
        "created_at": now,
        "updated_at": now,
    }
    ins = _jobs.insert_one(doc)
    return str(ins.inserted_id)

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    try:
        return _jobs.find_one({"_id": ObjectId(job_id)})
    except Exception:
        return None

def set_job_fields(job_id: str, fields: Dict[str, Any]) -> None:
    fields = dict(fields or {})
    fields["updated_at"] = datetime.utcnow()
    _jobs.update_one({"_id": ObjectId(job_id)}, {"$set": fields})

# 확장: 활성잡 조회 / 멱등 생성 (현재 API는 기본 create_job 사용)
def get_active_job_by_task(task_id: str) -> Optional[Dict[str, Any]]:
    return _jobs.find_one({"task_ref.task_id": task_id, "status": {"$in": ["queued", "running"]}})

def create_job_idempotent(payload: Dict[str, Any], idempotency_key: Optional[str] = None, force: bool = False) -> str:
    if not force:
        tid = (payload.get("task_ref") or {}).get("task_id")
        if tid:
            active = get_active_job_by_task(tid)
            if active:
                return str(active["_id"])
    if idempotency_key:
        prev = _jobs.find_one({"idempotency_key": idempotency_key})
        if prev:
            return str(prev["_id"])
    now = datetime.utcnow()
    doc = {
        **payload,
        "status": payload.get("status", "queued"),
        "worker_id": payload.get("worker_id", None),
        "progress": float(payload.get("progress", 0.0)),
        "message": payload.get("message", ""),
        "idempotency_key": idempotency_key or None,
        "created_at": now,
        "updated_at": now,
    }
    r = _jobs.insert_one(doc)
    return str(r.inserted_id)