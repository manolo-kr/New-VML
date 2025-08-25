# backend/app/store_sql.py

from __future__ import annotations

from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlmodel import Session, select

from .models import Project, Analysis, MLTask, User


class Repo:
    def __init__(self, s: Session):
        self.s = s

    # ---------- Users ----------
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.s.exec(select(User).where(User.email == email)).first()

    def create_user(self, email: str, name: str, password_hash: str, role: str = "user") -> User:
        u = User(id=uuid4().hex, email=email, name=name, password_hash=password_hash, role=role)
        self.s.add(u)
        self.s.commit()
        self.s.refresh(u)
        return u

    # ---------- Projects ----------
    def create_project(self, name: str) -> Dict[str, Any]:
        p = Project(id=uuid4().hex, name=name)
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
    def create_analysis(
        self,
        project_id: str,
        name: str,
        dataset_uri: str,
        dataset_original_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        a = Analysis(
            id=uuid4().hex,
            project_id=project_id,
            name=name,
            dataset_uri=dataset_uri,
            dataset_original_name=dataset_original_name,
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
            split=split,
            model_family=model_family,
            model_params=model_params,
        )
        self.s.add(t)
        self.s.commit()
        self.s.refresh(t)
        return t.dict()

    def get_task(self, task_id: str) -> Optional[MLTask]:
        return self.s.get(MLTask, task_id)