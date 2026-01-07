
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.api import get_current_user
from app.core.models import User
from app.db import get_db

from . import schemas
from .queries import ResearchQueries


router = APIRouter(prefix="/research", tags=["科研数据支撑"])


def _require_roles(user: User, allowed: List[str], detail: str = "权限不足"):
    if user.role_type not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


@router.post("/projects", response_model=schemas.ResearchProject, status_code=201)
def create_project(
    payload: schemas.ResearchProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    if ResearchQueries.get_project(db, payload.project_id):
        raise HTTPException(status_code=400, detail="项目编号已存在")
    return ResearchQueries.create_project(db, payload)


@router.get("/projects/{project_id}", response_model=schemas.ResearchProject)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    project = ResearchQueries.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.get("/projects", response_model=List[schemas.ResearchProject])
def list_projects(
    status_value: Optional[str] = Query(None, alias="status"),
    research_field: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    return ResearchQueries.list_projects(db, status_value, research_field, skip, limit)


@router.put("/projects/{project_id}", response_model=schemas.ResearchProject)
def update_project(
    project_id: str,
    payload: schemas.ResearchProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    updated = ResearchQueries.update_project(db, project_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="项目不存在")
    return updated


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["系统管理员"], "需要系统管理员权限")
    ok = ResearchQueries.delete_project(db, project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="项目不存在")
    return {"success": True}


@router.post("/projects/apply-audit", response_model=schemas.ProjectAuditResponse)
def apply_audit_project(
    payload: schemas.ProjectAuditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["系统管理员", "公园管理人员"], "需要系统管理员或公园管理人员权限")

    if ResearchQueries.get_project(db, payload.project_apply_info.project_id):
        return {
            "status": "failed",
            "message": f"项目申请失败：项目编号「{payload.project_apply_info.project_id}」已存在",
            "audit_user": payload.audit_user_id,
            "project_info": None,
        }

    if not payload.is_approved:
        return {
            "status": "failed",
            "message": f"项目「{payload.project_apply_info.project_name}」审核未通过，未生成项目信息",
            "audit_user": payload.audit_user_id,
            "project_info": None,
        }

    created = ResearchQueries.create_project(db, payload.project_apply_info)
    return {
        "status": "success",
        "message": f"项目「{created.project_name}」审核通过，已生成科研项目信息",
        "audit_user": payload.audit_user_id,
        "project_info": created,
    }


@router.post("/collections", response_model=schemas.DataCollection, status_code=201)
def create_collection(
    payload: schemas.DataCollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    if ResearchQueries.get_collection(db, payload.collection_id):
        raise HTTPException(status_code=400, detail="采集编号已存在")
    try:
        return ResearchQueries.create_collection(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/collections/{collection_id}", response_model=schemas.DataCollection)
def get_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    c = ResearchQueries.get_collection(db, collection_id)
    if not c:
        raise HTTPException(status_code=404, detail="采集记录不存在")
    return c


@router.get("/collections", response_model=List[schemas.DataCollection])
def list_collections(
    project_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    return ResearchQueries.list_collections(db, project_id, skip, limit)


@router.put("/collections/{collection_id}", response_model=schemas.DataCollection)
def update_collection(
    collection_id: str,
    payload: schemas.DataCollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    updated = ResearchQueries.update_collection(db, collection_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="采集记录不存在")
    return updated


@router.delete("/collections/{collection_id}")
def delete_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["系统管理员"], "需要系统管理员权限")
    ok = ResearchQueries.delete_collection(db, collection_id)
    if not ok:
        raise HTTPException(status_code=404, detail="采集记录不存在")
    return {"success": True}


@router.post("/collections/create", response_model=schemas.CollectionCreateResponse)
def create_collection_record(
    payload: schemas.CollectionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    if ResearchQueries.get_collection(db, payload.collection_info.collection_id):
        return {"status": "failed", "message": "采集编号已存在", "collection_info": None}

    data_source_map = {"input": "实地采集", "call": "系统调用"}
    if payload.data_type not in data_source_map:
        return {"status": "failed", "message": "数据类型仅支持：input/call", "collection_info": None}

    fixed = payload.collection_info.model_copy(deep=True)
    fixed.data_source = data_source_map[payload.data_type]

    try:
        created = ResearchQueries.create_collection(db, fixed)
    except ValueError as e:
        return {"status": "failed", "message": str(e), "collection_info": None}

    return {"status": "success", "message": "创建采集记录成功", "collection_info": created}


@router.post("/achievements", response_model=schemas.ResearchAchievement, status_code=201)
def create_achievement(
    payload: schemas.ResearchAchievementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    if ResearchQueries.get_achievement(db, payload.achievement_id):
        raise HTTPException(status_code=400, detail="成果编号已存在")
    try:
        return ResearchQueries.create_achievement(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/achievements/{achievement_id}", response_model=schemas.ResearchAchievement)
def get_achievement(
    achievement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ach = ResearchQueries.get_achievement(db, achievement_id)
    if not ach:
        raise HTTPException(status_code=404, detail="成果不存在")

    if ach.share_permission == "保密":
        uid = str(current_user.id)
        if not (
            current_user.role_type in ["系统管理员", "公园管理人员", "科研人员"]
            or ResearchQueries.is_authorized(db, achievement_id, uid)
        ):
            raise HTTPException(status_code=403, detail="无权限访问保密成果")

    return ach


@router.get("/achievements", response_model=List[schemas.ResearchAchievement])
def list_achievements(
    project_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    return ResearchQueries.list_achievements(db, project_id, skip, limit)


@router.put("/achievements/{achievement_id}", response_model=schemas.ResearchAchievement)
def update_achievement(
    achievement_id: str,
    payload: schemas.ResearchAchievementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    try:
        updated = ResearchQueries.update_achievement(db, achievement_id, payload.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="成果不存在")
    return updated


@router.delete("/achievements/{achievement_id}")
def delete_achievement(
    achievement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["系统管理员"], "需要系统管理员权限")
    try:
        ok = ResearchQueries.delete_achievement(db, achievement_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="成果不存在")
    return {"success": True}


@router.post("/authorizations", response_model=schemas.AuthorizedAccess, status_code=201)
def authorize_access(
    payload: schemas.AuthorizedAccessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    ach = ResearchQueries.get_achievement(db, payload.achievement_id)
    if not ach:
        raise HTTPException(status_code=404, detail="成果不存在")
    if ach.share_permission != "保密":
        raise HTTPException(status_code=400, detail="仅保密成果需要授权")
    if ResearchQueries.is_authorized(db, payload.achievement_id, payload.user_id):
        raise HTTPException(status_code=400, detail="该用户已获得此成果的授权")
    return ResearchQueries.create_authorization(db, payload.achievement_id, payload.user_id)


@router.get("/authorizations", response_model=List[schemas.AuthorizedAccess])
def list_authorizations(
    achievement_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    return ResearchQueries.list_authorizations(db, achievement_id, user_id)


@router.post("/authorizations/batch")
def batch_authorize(
    payload: schemas.BatchAuthorizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    try:
        ResearchQueries.batch_authorize(db, payload.achievement_id, payload.user_ids, authorizer_id=str(current_user.id))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True}


@router.post("/authorizations/revoke")
def revoke_authorize(
    achievement_id: str = Query(...),
    user_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["科研人员", "系统管理员", "公园管理人员"], "需要科研人员/管理人员权限")
    try:
        ResearchQueries.revoke_authorization(db, achievement_id, user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True}
