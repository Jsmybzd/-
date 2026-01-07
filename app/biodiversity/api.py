import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "assets" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

from app.core.api import get_current_user
from app.core.models import User
from app.db import get_db
from app.shared.models import 区域表

from .analysis_report_service import AnalysisReportService
from .models import 物种表, 物种监测记录表, 区域物种关联表
from .monitoring_service import MonitoringRecordService
from .schemas import (
    AnalysisConclusionCreate,
    AnalystStatsResponse,
    AreaSpeciesCreate,
    AreaSpeciesResponse,
    DataStatus,
    MonitoringRecordCreate,
    MonitoringMethod,
    MonitoringRecordQueryParams,
    MonitoringRecordResponse,
    MonitoringRecordUpdate,
    OverallStatsResponse,
    PaginatedAnalysisRecords,
    PaginatedMonitoringRecords,
    PaginatedSpecies,
    ProtectLevel,
    SpeciesCreate,
    SpeciesQueryParams,
    SpeciesResponse,
    SpeciesUpdate,
)
from .species_service import SpeciesService

router = APIRouter(prefix="/biodiversity", tags=["生物多样性监测"])


def _require_roles(current_user: User, allowed_roles: List[str], detail: str = "权限不足"):
    if current_user.role_type not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


@router.post("/species", response_model=SpeciesResponse)
def create_species(
    species_data: SpeciesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["生态监测员", "数据分析师", "系统管理员", "公园管理人员", "科研人员"], "无权创建物种")
    return SpeciesService.create_species(db, species_data)


@router.get("/species", response_model=PaginatedSpecies)
def list_species(
    chinese_name: Optional[str] = Query(None),
    latin_name: Optional[str] = Query(None),
    protect_level: Optional[ProtectLevel] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 所有角色可查
    query_params = SpeciesQueryParams(
        chinese_name=chinese_name,
        latin_name=latin_name,
        protect_level=protect_level,
        page=page,
        page_size=page_size,
    )
    result = SpeciesService.list_species(db, query_params)
    # 手动序列化物种列表
    species_list = [SpeciesResponse.model_validate(s) for s in result["species"]]
    return {
        "total": result["total"],
        "species": species_list,
        "page": result["page"],
        "page_size": result["page_size"],
    }


@router.get("/species/{species_id}", response_model=SpeciesResponse)
def get_species(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    species = SpeciesService.get_species(db, species_id)
    if not species:
        raise HTTPException(status_code=404, detail="物种不存在")
    return species


@router.put("/species/{species_id}", response_model=SpeciesResponse)
def update_species(
    species_id: int,
    species_data: SpeciesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["生态监测员", "数据分析师", "系统管理员", "公园管理人员", "科研人员"], "无权更新物种信息")
    return SpeciesService.update_species(db, species_id, species_data)


@router.delete("/species/{species_id}")
def delete_species(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["系统管理员"], "需要系统管理员权限")
    SpeciesService.delete_species(db, species_id)
    return {"message": "删除成功"}


@router.post("/records", response_model=MonitoringRecordResponse)
def create_monitoring_record(
    record_data: MonitoringRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["生态监测员", "数据分析师", "系统管理员", "公园管理人员", "科研人员"], "无权创建监测记录")
    return MonitoringRecordService.create_record(db, record_data, current_user.id)


@router.get("/records", response_model=PaginatedMonitoringRecords)
def list_monitoring_records(
    species_id: Optional[int] = Query(None),
    recorder_id: Optional[int] = Query(None),
    device_id: Optional[int] = Query(None),
    monitoring_method: Optional[MonitoringMethod] = Query(None),
    state: Optional[DataStatus] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    area_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 所有角色可查
    query_params = MonitoringRecordQueryParams(
        species_id=species_id,
        recorder_id=recorder_id,
        device_id=device_id,
        monitoring_method=monitoring_method,
        state=state,
        start_date=start_date,
        end_date=end_date,
        area_id=area_id,
        page=page,
        page_size=page_size,
    )
    result = MonitoringRecordService.list_records(db, query_params)
    # 手动序列化记录列表
    records_list = [MonitoringRecordResponse.model_validate(r) for r in result["records"]]
    return {
        "total": result["total"],
        "records": records_list,
        "page": result["page"],
        "page_size": result["page_size"],
    }


@router.get("/records/pending", response_model=PaginatedMonitoringRecords)
def list_pending_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["数据分析师", "系统管理员"], "无权查看待核实记录")
    result = MonitoringRecordService.get_pending_records(db, page=page, page_size=page_size)
    return result


@router.post("/records/{record_id}/verify", response_model=MonitoringRecordResponse)
def verify_monitoring_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["数据分析师", "系统管理员", "公园管理人员"], "无权核实数据")
    return MonitoringRecordService.verify_record(db, record_id)


@router.put("/records/{record_id}", response_model=MonitoringRecordResponse)
def update_monitoring_record(
    record_id: int,
    record_data: MonitoringRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MonitoringRecordService.update_record(db, record_id, record_data, current_user.id)


@router.delete("/records/{record_id}")
def delete_monitoring_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    MonitoringRecordService.delete_record(db, record_id, current_user.id)
    return {"message": "删除成功"}


@router.post("/records/{record_id}/upload")
async def upload_record_file(
    record_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传监测记录文件"""
    _require_roles(current_user, ["生态监测员", "数据分析师", "系统管理员", "公园管理人员", "科研人员"], "无权上传文件")
    
    # 检查记录是否存在
    record = db.get(物种监测记录表, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="监测记录不存在")
    
    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"bio_{record_id}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = UPLOAD_DIR / unique_name
    
    # 保存文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 更新数据库中的 image_path 字段
    relative_path = f"/web/assets/uploads/{unique_name}"
    record.image_path = relative_path
    db.commit()
    
    return {"message": "上传成功", "file_path": relative_path}


@router.post("/areas/{area_id}/species", response_model=AreaSpeciesResponse)
def add_species_to_area(
    area_id: int,
    species_data: AreaSpeciesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["生态监测员", "数据分析师", "系统管理员", "公园管理人员", "科研人员"], "无权管理区域物种")
    area = db.get(区域表, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="区域不存在")
    species = db.get(物种表, species_data.species_id)
    if not species:
        raise HTTPException(status_code=404, detail="物种不存在")

    existing = db.execute(
        select(区域物种关联表).where(
            and_(区域物种关联表.area_id == area_id, 区域物种关联表.species_id == species_data.species_id)
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="该物种已关联到此区域")

    assoc = 区域物种关联表(area_id=area_id, species_id=species_data.species_id, is_main=species_data.is_main)
    db.add(assoc)
    db.commit()
    db.refresh(assoc)
    return {"area_id": assoc.area_id, "species_id": assoc.species_id, "is_main": assoc.is_main}


@router.get("/areas/{area_id}/species", response_model=List[Dict[str, Any]])
def get_species_by_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    area = db.get(区域表, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="区域不存在")

    rows = db.execute(
        select(区域物种关联表, 物种表)
        .join(物种表, 区域物种关联表.species_id == 物种表.id)
        .where(区域物种关联表.area_id == area_id)
    ).all()

    result: List[Dict[str, Any]] = []
    for assoc, sp in rows:
        result.append(
            {
                "species_id": sp.id,
                "chinese_name": sp.chinese_name,
                "latin_name": sp.latin_name,
                "protect_level": sp.protect_level,
                "is_main": assoc.is_main,
            }
        )
    return result


@router.put("/areas/{area_id}/species/{species_id}", response_model=AreaSpeciesResponse)
def update_area_species(
    area_id: int,
    species_id: int,
    is_main: int = Query(..., ge=0, le=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["生态监测员", "数据分析师", "系统管理员", "公园管理人员", "科研人员"], "无权管理区域物种")
    assoc = db.execute(
        select(区域物种关联表).where(
            and_(区域物种关联表.area_id == area_id, 区域物种关联表.species_id == species_id)
        )
    ).scalar_one_or_none()
    if not assoc:
        raise HTTPException(status_code=404, detail="该物种未关联到此区域")

    assoc.is_main = is_main
    db.commit()
    db.refresh(assoc)
    return {"area_id": assoc.area_id, "species_id": assoc.species_id, "is_main": assoc.is_main}


@router.delete("/areas/{area_id}/species/{species_id}")
def remove_species_from_area(
    area_id: int,
    species_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["生态监测员", "数据分析师", "系统管理员", "公园管理人员", "科研人员"], "无权管理区域物种")
    assoc = db.execute(
        select(区域物种关联表).where(
            and_(区域物种关联表.area_id == area_id, 区域物种关联表.species_id == species_id)
        )
    ).scalar_one_or_none()
    if not assoc:
        raise HTTPException(status_code=404, detail="该物种未关联到此区域")
    db.delete(assoc)
    db.commit()
    return {"message": "移除成功"}


@router.get("/all-areas", response_model=List[Dict[str, Any]])
def get_all_areas_for_biodiversity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有区域列表（供生物多样性模块使用）"""
    areas = db.query(区域表).all()
    return [{"area_id": a.id, "area_name": a.name, "area_type": a.type} for a in areas]


@router.get("/stats/overall", response_model=OverallStatsResponse)
def get_overall_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    species_stats = SpeciesService.get_protected_species_stats(db)
    record_stats = MonitoringRecordService.get_overall_stats(db)
    return {"species_stats": species_stats, "record_stats": record_stats}


@router.get("/stats/taxonomy", response_model=Dict[str, Dict[str, int]])
def get_taxonomy_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SpeciesService.get_species_taxonomy_stats(db)


@router.post("/analysis/conclusions", response_model=Dict[str, Any])
def add_analysis_conclusion(
    conclusion_data: AnalysisConclusionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["数据分析师"], "需要数据分析师权限")
    return AnalysisReportService.add_analysis_conclusion(
        db=db,
        record_id=conclusion_data.record_id,
        conclusion=conclusion_data.conclusion,
        analyst_id=current_user.id,
        confidence_level=conclusion_data.confidence_level,
    )


@router.get("/analysis/pending", response_model=PaginatedAnalysisRecords)
def get_pending_analysis_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["数据分析师"], "需要数据分析师权限")
    result = AnalysisReportService.get_records_without_conclusion(db=db, page=page, page_size=page_size)
    return result


@router.get("/analysis/analyst-stats/{analyst_id}", response_model=AnalystStatsResponse)
def get_analyst_statistics(
    analyst_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 数据分析师只能看自己；管理员可看所有
    if current_user.role_type != "系统管理员" and current_user.id != analyst_id:
        raise HTTPException(status_code=403, detail="只能查看自己的统计信息")
    return AnalysisReportService.get_analyst_work_stats(db=db, analyst_id=analyst_id)
