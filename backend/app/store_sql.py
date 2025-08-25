# backend/app/store_sql.py

from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select
from uuid import uuid4

from app.models import Project, Analysis, MLTask, User

class Repo:
    def __init__(self, s: Session):
        self.s = s

    # Projects
    def create_project(self, name: str) -> dict:
        p = Project(id=uuid4().hex, name=name, created_at=datetime.utcnow())
        self.s.add(p)
        self.s.commit()
        self.s.refresh(p)
        return p.dict()

    def list_projects(self) -> List[dict]:
        rows = self.s.exec(select(Project).order_by(Project.created_at.desc())).all()
        return [r.dict() for r in rows]

    def delete_project_cascade(self, project_id: str) -> dict:
        # 분석→태스크를 순차적으로 삭제 (FK 제약 없는 단순 스키마를 고려)
        analyses = self.s.exec(select(Analysis).where(Analysis.project_id == project_id)).all()
        deleted_tasks = 0
        for a in analyses:
            tasks = self.s.exec(select(MLTask).where(MLTask.analysis_id == a.id)).all()
            for t in tasks:
                self.s.delete(t)
                deleted_tasks += 1
            self.s.delete(a)
        proj = self.s.get(Project, project_id)
        if proj:
            self.s.delete(proj)
        self.s.commit()
        return {"ok": True, "deleted_tasks": deleted_tasks, "deleted_analyses": len(analyses), "deleted_project_id": project_id}

    # Analyses
    def create_analysis(self, project_id: str, name: str, dataset_uri: str, dataset_original_name: Optional[str] = None) -> dict:
        a = Analysis(
            id=uuid4().hex,
            project_id=project_id,
            name=name or "Analysis",
            dataset_uri=dataset_uri,
            dataset_original_name=dataset_original_name,
            created_at=datetime.utcnow(),
        )
        self.s.add(a)
        self.s.commit()
        self.s.refresh(a)
        return a.dict()

    def list_analyses(self, project_id: str) -> List[dict]:
        rows = self.s.exec(select(Analysis).where(Analysis.project_id == project_id).order_by(Analysis.created_at.desc())).all()
        return [r.dict() for r in rows]

    def get_analysis(self, analysis_id: str) -> Optional[Analysis]:
        return self.s.get(Analysis, analysis_id)

    # Tasks
    def create_task(self, analysis_id: str, task_type: str, target: str, model_family: str, split: dict, model_params: dict) -> dict:
        t = MLTask(
            id=uuid4().hex,
            analysis_id=analysis_id,
            task_type=task_type,
            target=target,
            model_family=model_family,
            split=split,
            model_params=model_params,
            created_at=datetime.utcnow(),
        )
        self.s.add(t)
        self.s.commit()
        self.s.refresh(t)
        return t.dict()

    def get_task(self, task_id: str) -> Optional[MLTask]:
        return self.s.get(MLTask, task_id)

    # Users
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.s.exec(select(User).where(User.email == email)).first()

    def create_user(self, email: str, password_hash: str, name: Optional[str] = None, role: str = "user") -> dict:
        u = User(id=uuid4().hex, email=email, name=name, password_hash=password_hash, role=role, created_at=datetime.utcnow())
        self.s.add(u)
        self.s.commit()
        self.s.refresh(u)
        return u.dict()