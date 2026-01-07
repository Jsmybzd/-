
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResearchProjectBase(BaseModel):
    project_name: str
    leader_id: str
    apply_unit: str
    approval_date: date
    conclusion_date: Optional[date] = None
    status: str = "在研"
    research_field: str


class ResearchProjectCreate(ResearchProjectBase):
    project_id: str


class ResearchProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    leader_id: Optional[str] = None
    apply_unit: Optional[str] = None
    approval_date: Optional[date] = None
    conclusion_date: Optional[date] = None
    status: Optional[str] = None
    research_field: Optional[str] = None


class ResearchProject(ResearchProjectCreate):
    class Config:
        from_attributes = True


class DataCollectionBase(BaseModel):
    project_id: str
    collector_id: str
    collection_time: datetime
    area_id: str
    content: str
    data_source: str
    remarks: Optional[str] = None


class DataCollectionCreate(DataCollectionBase):
    collection_id: str


class DataCollectionUpdate(BaseModel):
    project_id: Optional[str] = None
    collector_id: Optional[str] = None
    collection_time: Optional[datetime] = None
    area_id: Optional[str] = None
    content: Optional[str] = None
    data_source: Optional[str] = None
    remarks: Optional[str] = None


class DataCollection(DataCollectionCreate):
    class Config:
        from_attributes = True


class ResearchAchievementBase(BaseModel):
    project_id: str
    achievement_type: str
    title: str
    publish_date: date
    share_permission: str
    file_path: str


class ResearchAchievementCreate(ResearchAchievementBase):
    achievement_id: str


class ResearchAchievementUpdate(BaseModel):
    project_id: Optional[str] = None
    achievement_type: Optional[str] = None
    title: Optional[str] = None
    publish_date: Optional[date] = None
    share_permission: Optional[str] = None
    file_path: Optional[str] = None


class ResearchAchievement(ResearchAchievementCreate):
    class Config:
        from_attributes = True


class AuthorizedAccessBase(BaseModel):
    achievement_id: str
    user_id: str
    authorize_time: Optional[datetime] = None


class AuthorizedAccessCreate(AuthorizedAccessBase):
    pass


class AuthorizedAccess(AuthorizedAccessBase):
    access_id: int

    class Config:
        from_attributes = True


class ProjectAuditRequest(BaseModel):
    project_apply_info: ResearchProjectCreate
    audit_user_id: str
    is_approved: bool


class ProjectAuditResponse(BaseModel):
    status: str
    message: str
    audit_user: Optional[str] = None
    project_info: Optional[ResearchProject] = None


class CollectionCreateRequest(BaseModel):
    collection_info: DataCollectionCreate
    data_type: str = Field(default="input", description="input/call")


class CollectionCreateResponse(BaseModel):
    status: str
    message: str
    collection_info: Optional[DataCollection] = None


class BatchAuthorizeRequest(BaseModel):
    achievement_id: str
    user_ids: list[str]
