
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from . import models


class ResearchQueries:
    @staticmethod
    def create_project(db: Session, payload) -> models.ResearchProjects:
        project = models.ResearchProjects(
            project_id=payload.project_id,
            project_name=payload.project_name,
            leader_id=payload.leader_id,
            apply_unit=payload.apply_unit,
            approval_date=payload.approval_date,
            conclusion_date=payload.conclusion_date,
            status=payload.status,
            research_field=payload.research_field,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project(db: Session, project_id: str) -> Optional[models.ResearchProjects]:
        return db.get(models.ResearchProjects, project_id)

    @staticmethod
    def list_projects(
        db: Session,
        status_value: Optional[str] = None,
        research_field: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[models.ResearchProjects]:
        q = select(models.ResearchProjects)
        if status_value:
            q = q.where(models.ResearchProjects.status == status_value)
        if research_field:
            q = q.where(models.ResearchProjects.research_field == research_field)
        return db.scalars(q.order_by(desc(models.ResearchProjects.approval_date), models.ResearchProjects.project_id).offset(skip).limit(limit)).all()

    @staticmethod
    def update_project(db: Session, project_id: str, update_data: dict) -> Optional[models.ResearchProjects]:
        project = db.get(models.ResearchProjects, project_id)
        if not project:
            return None
        if "project_id" in update_data:
            update_data.pop("project_id", None)
        for k, v in update_data.items():
            if v is not None:
                setattr(project, k, v)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: str) -> bool:
        project = db.get(models.ResearchProjects, project_id)
        if not project:
            return False
        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def create_collection(db: Session, payload) -> models.DataCollections:
        project = db.get(models.ResearchProjects, payload.project_id)
        if not project:
            raise ValueError("关联项目不存在")
        if project.status == "已结题":
            raise ValueError("项目已结题，无法新增采集记录")

        collection = models.DataCollections(
            collection_id=payload.collection_id,
            project_id=payload.project_id,
            collector_id=payload.collector_id,
            collection_time=payload.collection_time,
            area_id=payload.area_id,
            content=payload.content,
            data_source=payload.data_source,
            remarks=payload.remarks,
        )
        db.add(collection)
        db.commit()
        db.refresh(collection)
        return collection

    @staticmethod
    def get_collection(db: Session, collection_id: str) -> Optional[models.DataCollections]:
        return db.get(models.DataCollections, collection_id)

    @staticmethod
    def list_collections(db: Session, project_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.DataCollections]:
        q = select(models.DataCollections)
        if project_id:
            q = q.where(models.DataCollections.project_id == project_id)
        return db.scalars(q.order_by(desc(models.DataCollections.collection_time), models.DataCollections.collection_id).offset(skip).limit(limit)).all()

    @staticmethod
    def update_collection(db: Session, collection_id: str, update_data: dict) -> Optional[models.DataCollections]:
        collection = db.get(models.DataCollections, collection_id)
        if not collection:
            return None
        if "collection_id" in update_data:
            update_data.pop("collection_id", None)
        for k, v in update_data.items():
            if v is not None:
                setattr(collection, k, v)
        db.commit()
        db.refresh(collection)
        return collection

    @staticmethod
    def delete_collection(db: Session, collection_id: str) -> bool:
        collection = db.get(models.DataCollections, collection_id)
        if not collection:
            return False
        db.delete(collection)
        db.commit()
        return True

    @staticmethod
    def create_achievement(db: Session, payload) -> models.ResearchAchievements:
        project = db.get(models.ResearchProjects, payload.project_id)
        if not project:
            raise ValueError("关联项目不存在")

        ach = models.ResearchAchievements(
            achievement_id=payload.achievement_id,
            project_id=payload.project_id,
            achievement_type=payload.achievement_type,
            title=payload.title,
            publish_date=payload.publish_date,
            share_permission=payload.share_permission,
            file_path=payload.file_path,
        )
        db.add(ach)
        db.commit()
        db.refresh(ach)
        return ach

    @staticmethod
    def get_achievement(db: Session, achievement_id: str) -> Optional[models.ResearchAchievements]:
        return db.get(models.ResearchAchievements, achievement_id)

    @staticmethod
    def list_achievements(db: Session, project_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.ResearchAchievements]:
        q = select(models.ResearchAchievements)
        if project_id:
            q = q.where(models.ResearchAchievements.project_id == project_id)
        return db.scalars(q.order_by(desc(models.ResearchAchievements.publish_date), models.ResearchAchievements.achievement_id).offset(skip).limit(limit)).all()

    @staticmethod
    def update_achievement(db: Session, achievement_id: str, update_data: dict) -> Optional[models.ResearchAchievements]:
        ach = db.get(models.ResearchAchievements, achievement_id)
        if not ach:
            return None
        if "achievement_id" in update_data:
            update_data.pop("achievement_id", None)
        for k, v in update_data.items():
            if v is not None:
                setattr(ach, k, v)
        try:
            db.commit()
        except DBAPIError as e:
            db.rollback()
            raise ValueError(str(e))
        db.refresh(ach)
        return ach

    @staticmethod
    def delete_achievement(db: Session, achievement_id: str) -> bool:
        ach = db.get(models.ResearchAchievements, achievement_id)
        if not ach:
            return False
        try:
            db.query(models.AuthorizedAccesses).filter(models.AuthorizedAccesses.achievement_id == achievement_id).delete(synchronize_session=False)
            db.delete(ach)
            db.commit()
        except DBAPIError as e:
            db.rollback()
            raise ValueError(str(e))
        return True

    @staticmethod
    def is_authorized(db: Session, achievement_id: str, user_id: str) -> bool:
        return db.scalar(
            select(models.AuthorizedAccesses.access_id)
            .where(
                models.AuthorizedAccesses.achievement_id == achievement_id,
                models.AuthorizedAccesses.user_id == user_id,
            )
            .limit(1)
        ) is not None

    @staticmethod
    def create_authorization(db: Session, achievement_id: str, user_id: str) -> models.AuthorizedAccesses:
        auth = models.AuthorizedAccesses(achievement_id=achievement_id, user_id=user_id, authorize_time=datetime.now())
        db.add(auth)
        db.commit()
        db.refresh(auth)
        return auth

    @staticmethod
    def list_authorizations(db: Session, achievement_id: Optional[str] = None, user_id: Optional[str] = None) -> List[models.AuthorizedAccesses]:
        q = select(models.AuthorizedAccesses)
        if achievement_id:
            q = q.where(models.AuthorizedAccesses.achievement_id == achievement_id)
        if user_id:
            q = q.where(models.AuthorizedAccesses.user_id == user_id)
        return db.scalars(q.order_by(desc(models.AuthorizedAccesses.authorize_time), models.AuthorizedAccesses.access_id)).all()

    @staticmethod
    def revoke_authorization(db: Session, achievement_id: str, user_id: str) -> None:
        db.execute(
            text("EXEC dbo.sp_revoke_achievement_auth @achievement_id=:aid, @user_id=:uid"),
            {"aid": achievement_id, "uid": user_id},
        )
        db.commit()

    @staticmethod
    def batch_authorize(db: Session, achievement_id: str, user_ids: List[str], authorizer_id: str) -> None:
        csv = ",".join(user_ids)
        db.execute(
            text("EXEC dbo.sp_batch_authorize_achievement @achievement_id=:aid, @user_ids=:uids, @authorizer_id=:auth"),
            {"aid": achievement_id, "uids": csv, "auth": authorizer_id},
        )
        db.commit()
