# backend/app/store_sql.py

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from sqlmodel import SQLModel, Session, select, delete
from .models import Project, Analysis, MLTask

class Repo:
    def __init__(self, s: Session):
        self.s = s

    # ---------- Projects ----------
    def create_project(self, name: str) -> Dict[str, Any]:
        p = Project(id=uuid4().hex, name=name, created_at=datetime.utcnow())
        self.s.add(p)
        self.s.commit()
        self.s.refresh(p)
        return p.dict()

    def list_projects(self) -> List[Dict[str, Any]]:
        rows = self.s.exec(select(Project).order_by(Project.created_at.desc())).all()
        return [r.dict() for r in rows]

    def get_project(self, project_id: str) -> Optional[Project]:
        return self.s.get(Project, project_id)

    # ---------- Analyses ----------
    def create_analysis(self, project_id: str, name: str, dataset_uri: str, dataset_original_name: Optional[str] = None) -> Dict[str, Any]:
        a = Analysis(
            id=uuid4().hex,
            project_id=project_id,
            name=name,
            dataset_uri=dataset_uri,
            dataset_original_name=dataset_original_name,
            created_at=datetime.utcnow()
        )
        self.s.add(a)
        self.s.commit()
        self.s.refresh(a)
        return a.dict()

    def list_analyses(self, project_id: str) -> List[Dict[str, Any]]:
        rows = self.s.exec(select(Analysis).where(Analysis.project_id == project_id).order_by(Analysis.created_at.desc())).all()
        return [r.dict() for r in rows]

    def get_analysis(self, analysis_id: str) -> Optional[Analysis]:
        return self.s.get(Analysis, analysis_id)

    # ---------- Tasks ----------
    def create_task(
        self,
        analysis_id: str,
        task_type: str,
        target: str,
        model_family: str,
        split: Dict[str, Any],
        model_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        t = MLTask(
            id=uuid4().hex,
            analysis_id=analysis_id,
            task_type=task_type,
            target=target,
            model_family=model_family,
            split=split or {},
            model_params=model_params or {},
            status="ready",
            created_at=datetime.utcnow()
        )
        self.s.add(t)
        self.s.commit()
        self.s.refresh(t)
        return t.dict()

    def get_task(self, task_id: str) -> Optional[MLTask]:
        return self.s.get(MLTask, task_id)

    def list_tasks_by_analysis(self, analysis_id: str) -> List[Dict[str, Any]]:
        rows = self.s.exec(select(MLTask).where(MLTask.analysis_id == analysis_id).order_by(MLTask.created_at.desc())).all()
        return [r.dict() for r in rows]

    # ---------- Cascading Deletes (API에서 사용) ----------
    def delete_project_cascade(self, project_id: str) -> Dict[str, Any]:
        proj = self.s.get(Project, project_id)
        if not proj:
            return {"ok": False, "reason": "not_found"}

        ana_ids = [a.id for a in self.s.exec(select(Analysis).where(Analysis.project_id == project_id)).all()]
        if ana_ids:
            self.s.exec(delete(MLTask).where(MLTask.analysis_id.in_(ana_ids)))
        self.s.exec(delete(Analysis).where(Analysis.project_id == project_id))
        self.s.exec(delete(Project).where(Project.id == project_id))
        self.s.commit()
        return {"ok": True, "deleted_project_id": project_id, "deleted_analyses": len(ana_ids)}