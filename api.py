# backend/app/api.py

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse, FileResponse
from sqlmodel import Session, select, delete
from uuid import uuid4
import os, json, tempfile
import mlflow

from app.config import settings
from app.db import get_session
from app.store_sql import Repo
from app.models import Project as ProjectModel, Analysis as AnalysisModel, MLTask as MLTaskModel
from app.services.data_loader import load_dataset
from app.queue_mongo import create_job, get_job
from app.utils.json_safe import df_preview_safe

router = APIRouter()

# -------------------------------------------------------------------
# Upload
# -------------------------------------------------------------------
@router.post("/upload")
async def upload_file(f: UploadFile = File(...)):
    os.makedirs(os.path.join(settings.ARTIFACT_ROOT, "datasets"), exist_ok=True)
    ext = os.path.splitext(f.filename or "")[-1].lower()
    if ext not in [".csv", ".xlsx", ".parquet"]:
        raise HTTPException(status_code=400, detail="Only .csv, .xlsx, .parquet allowed")

    save_path = os.path.join(settings.ARTIFACT_ROOT, "datasets", f"{uuid4().hex}{ext}")
    with open(save_path, "wb") as out:
        out.write(await f.read())

    return {"dataset_uri": f"file://{save_path}", "original_name": (f.filename or os.path.basename(save_path))}

# -------------------------------------------------------------------
# Preview
# -------------------------------------------------------------------
@router.post("/preview")
def preview(body: dict):
    uri = (body.get("dataset_uri") or "").strip()
    if not uri:
        raise HTTPException(400, "dataset_uri required")
    import pandas as pd
    df = load_dataset(uri)
    return df_preview_safe(df, int(body.get("limit", 50)))

# -------------------------------------------------------------------
# Projects
# -------------------------------------------------------------------
@router.post("/projects")
def create_project(body: dict, s: Session = Depends(get_session)):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "name required")
    return Repo(s).create_project(name)

@router.get("/projects")
def list_projects(s: Session = Depends(get_session)):
    return Repo(s).list_projects()

@router.delete("/projects/{project_id}")
def delete_project(project_id: str, s: Session = Depends(get_session)):
    proj = s.get(ProjectModel, project_id)
    if not proj:
        raise HTTPException(404, "project not found")

    ana_ids = [a.id for a in s.exec(
        select(AnalysisModel).where(AnalysisModel.project_id == project_id)
    ).all()]

    if ana_ids:
        s.exec(delete(MLTaskModel).where(MLTaskModel.analysis_id.in_(ana_ids)))
    s.exec(delete(AnalysisModel).where(AnalysisModel.project_id == project_id))
    s.exec(delete(ProjectModel).where(ProjectModel.id == project_id))
    s.commit()
    return {"ok": True, "deleted_project_id": project_id, "deleted_analyses": len(ana_ids)}

# -------------------------------------------------------------------
# Analyses
# -------------------------------------------------------------------
@router.post("/analyses")
def create_analysis(body: dict, s: Session = Depends(get_session)):
    project_id = body.get("project_id")
    name = body.get("name") or "Analysis"
    dataset_uri = body.get("dataset_uri")
    dataset_original_name = body.get("dataset_original_name") or body.get("original_name")

    if not (project_id and dataset_uri):
        raise HTTPException(400, "project_id and dataset_uri required")

    return Repo(s).create_analysis(project_id, name, dataset_uri, dataset_original_name=dataset_original_name)

@router.get("/projects/{project_id}/analyses")
def list_analyses(project_id: str, s: Session = Depends(get_session)):
    return Repo(s).list_analyses(project_id)

# -------------------------------------------------------------------
# Tasks
# -------------------------------------------------------------------
@router.post("/tasks")
def create_task(body: dict, s: Session = Depends(get_session)):
    analysis_id = body.get("analysis_id")
    task_type = body.get("task_type")
    target = body.get("target")
    model_family = body.get("model_family", "xgboost")
    split = body.get("split") or {"test_size": 0.2, "random_state": 42}
    model_params = body.get("model_params") or {}
    features = body.get("features")
    sampling = body.get("sampling")

    if not (analysis_id and task_type and target):
        raise HTTPException(400, "analysis_id, task_type, target required")

    if features:
        model_params = {**model_params, "_features": features}
    if sampling:
        model_params = {**model_params, "_sampling": sampling}

    return Repo(s).create_task(
        analysis_id=analysis_id,
        task_type=task_type,
        target=target,
        model_family=model_family,
        split=split,
        model_params=model_params
    )

# -------------------------------------------------------------------
# Train
# -------------------------------------------------------------------
@router.post("/tasks/{task_id}/train")
def train_task(task_id: str, body: dict, s: Session = Depends(get_session)):
    repo = Repo(s)
    task = repo.get_task(task_id)
    if not task:
        raise HTTPException(404, "task not found")

    analysis = repo.get_analysis(task.analysis_id)
    if not analysis:
        raise HTTPException(404, "analysis not found")

    dataset_original_name = getattr(analysis, "dataset_original_name", None)

    job_id = create_job({
        "task_ref": {
            "task_id": task.id,
            "task_type": task.task_type,
            "target": task.target,
            "split": task.split,
            "model_family": task.model_family,
            "model_params": task.model_params,
        },
        "dataset_uri": analysis.dataset_uri,
        "dataset_original_name": dataset_original_name,
        "mlflow_uri": settings.MLFLOW_URI,
    })
    return {"run_id": job_id}

# -------------------------------------------------------------------
# Runs
# -------------------------------------------------------------------
@router.get("/runs/{run_id}")
def get_run(run_id: str):
    j = get_job(run_id)
    if not j:
        raise HTTPException(404, "run not found")
    return {
        "id": run_id,
        "status": j.get("status"),
        "progress": j.get("progress", 0.0),
        "message": j.get("message", ""),
        "metrics": j.get("metrics", {}),
        "artifacts": j.get("artifacts", {}),
        "mlflow": j.get("mlflow", {}),
        "task_ref": j.get("task_ref", {}),
        "dataset_original_name": j.get("dataset_original_name"),
    }

@router.post("/runs/{run_id}/cancel")
def cancel_run(run_id: str):
    j = get_job(run_id)
    if not j:
        raise HTTPException(404, "run not found")
    from app.queue_mongo import _jobs
    _jobs.update_one({"_id": j["_id"]}, {"$set": {"cancel_requested": True, "message": "cancel requested"}})
    return {"ok": True}

# -------------------------------------------------------------------
# Artifact proxy (MLflow 파일 모드)
# -------------------------------------------------------------------
@router.get("/runs/{run_id}/artifact")
def get_artifact(run_id: str, name: str):
    j = get_job(run_id)
    if not j:
        raise HTTPException(404, "run not found")

    mlflow.set_tracking_uri(j.get("mlflow_uri") or settings.MLFLOW_URI)

    from mlflow.tracking import MlflowClient
    mlrun = (j.get("mlflow") or {}).get("run_id")
    if not mlrun:
        raise HTTPException(404, "mlflow run not set")

    with tempfile.TemporaryDirectory() as d:
        p = MlflowClient().download_artifacts(mlrun, name, d)
        if name.endswith(".json"):
            with open(p, "r", encoding="utf-8") as f:
                return JSONResponse(json.load(f))
        return FileResponse(p)