# backend/app/store_sql.py

from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session, select
from app.models import Project, Analysis, MLTask


class Repo:
    def __init__(self, s: Session):
        self.s = s

    # ── Projects ─────────────────────────────────────────────
    def create_project(self, name: str) -> Dict[str, Any]:
        now = datetime.utcnow()
        p = Project(id=self._new_id("proj"), name=name, created_at=now)
        self.s.add(p)
        self.s.commit()
        self.s.refresh(p)
        return p.dict()

    def list_projects(self) -> List[Dict[str, Any]]:
        rows = self.s.exec(select(Project).order_by(Project.created_at.desc())).all()
        return [r.dict() for r in rows]

    def get_project(self, pid: str) -> Optional[Project]:
        return self.s.get(Project, pid)

    # ── Analyses ─────────────────────────────────────────────
    def create_analysis(self, project_id: str, name: str, dataset_uri: str,
                        dataset_original_name: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.utcnow()
        a = Analysis(
            id=self._new_id("ana"),
            project_id=project_id,
            name=name,
            dataset_uri=dataset_uri,
            dataset_original_name=dataset_original_name,
            created_at=now,
        )
        self.s.add(a)
        self.s.commit()
        self.s.refresh(a)
        return a.dict()

    def list_analyses(self, project_id: str) -> List[Dict[str, Any]]:
        rows = self.s.exec(
            select(Analysis).where(Analysis.project_id == project_id).order_by(Analysis.created_at.desc())
        ).all()
        return [r.dict() for r in rows]

    def get_analysis(self, aid: str) -> Optional[Analysis]:
        return self.s.get(Analysis, aid)

    # ── Tasks ────────────────────────────────────────────────
    def create_task(self, analysis_id: str, task_type: str, target: str,
                    model_family: str, split: Dict[str, Any], model_params: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        t = MLTask(
            id=self._new_id("task"),
            analysis_id=analysis_id,
            task_type=task_type,
            target=target,
            split=split or {},
            model_family=model_family,
            model_params=model_params or {},
            status="ready",
            created_at=now,
        )
        self.s.add(t)
        self.s.commit()
        self.s.refresh(t)
        return t.dict()

    def get_task(self, tid: str) -> Optional[MLTask]:
        return self.s.get(MLTask, tid)

    # ── util ────────────────────────────────────────────────
    @staticmethod
    def _new_id(prefix: str) -> str:
        from uuid import uuid4
        return f"{prefix}_{uuid4().hex[:12]}"
