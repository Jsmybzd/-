from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.api import get_current_user, verify_token
from app.core.models import User
from app.db import get_db

from . import schemas
from .queries import EnvironmentQueries

router = APIRouter(prefix="/environment", tags=["生态环境监测"])


def _require_roles(current_user: User, allowed_roles: List[str], detail: str = "权限不足"):
    if current_user.role_type not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    payload = verify_token(token)
    if not payload:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    return db.get(User, user_id)


@router.post("/monitor-indices", response_model=schemas.MonitorIndex)
async def create_monitor_index(
    index: schemas.MonitorIndexCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    existing = EnvironmentQueries.get_monitor_index(db, index.index_id)
    if existing:
        raise HTTPException(status_code=400, detail="指标编号已存在")
    return EnvironmentQueries.create_monitor_index(db, index)


@router.get("/monitor-indices/{index_id}", response_model=schemas.MonitorIndex)
async def get_monitor_index(index_id: str, db: Session = Depends(get_db)):
    index = EnvironmentQueries.get_monitor_index(db, index_id)
    if not index:
        raise HTTPException(status_code=404, detail="监测指标不存在")
    return index


@router.get("/monitor-indices", response_model=List[schemas.MonitorIndex])
async def list_monitor_indices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return EnvironmentQueries.list_monitor_indices(db, skip, limit)


@router.patch("/monitor-indices/{index_id}", response_model=schemas.MonitorIndex)
async def update_monitor_index(
    index_id: str,
    payload: schemas.MonitorIndexUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    updated = EnvironmentQueries.update_monitor_index(db, index_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="监测指标不存在")
    return updated


@router.post("/monitor-devices", response_model=schemas.MonitorDevice)
async def create_monitor_device(
    device: schemas.MonitorDeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    return EnvironmentQueries.create_monitor_device(db, device)


@router.get("/monitor-devices/{device_id}", response_model=schemas.MonitorDevice)
async def get_monitor_device(device_id: int, db: Session = Depends(get_db)):
    device = EnvironmentQueries.get_monitor_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="监测设备不存在")
    return device


@router.get("/monitor-devices", response_model=List[schemas.MonitorDevice])
async def list_monitor_devices(
    area_id: int = Query(None, description="区域编号(可选，不传则返回所有)"),
    db: Session = Depends(get_db),
):
    if area_id is not None:
        return EnvironmentQueries.list_monitor_devices_by_area(db, area_id)
    return EnvironmentQueries.list_all_monitor_devices(db)


@router.put("/monitor-devices/{device_id}/status", response_model=schemas.MonitorDevice)
async def update_device_status(
    device_id: int,
    status_value: str = Query(..., description="设备状态（正常/故障/离线）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    device = EnvironmentQueries.update_device_status(db, device_id, status_value)
    if not device:
        raise HTTPException(status_code=404, detail="监测设备不存在")
    return device


@router.get("/monitor-devices/need-calibration", response_model=List[schemas.MonitorDevice])
async def get_devices_needing_calibration(db: Session = Depends(get_db)):
    return EnvironmentQueries.get_devices_needing_calibration(db)


@router.post("/environment-data", response_model=schemas.EnvironmentData)
async def create_environment_data(
    data: schemas.EnvironmentDataCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    if current_user is not None:
        _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")

    if not data.data_id:
        data.data_id = f"ED_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"

    existing = EnvironmentQueries.get_environment_data(db, data.data_id)
    if existing:
        raise HTTPException(status_code=400, detail="数据编号已存在")

    return EnvironmentQueries.create_environment_data(db, data)


@router.get("/environment-data/{data_id}", response_model=schemas.EnvironmentData)
async def get_environment_data(data_id: str, db: Session = Depends(get_db)):
    data = EnvironmentQueries.get_environment_data(db, data_id)
    if not data:
        raise HTTPException(status_code=404, detail="监测数据不存在")
    return data


@router.get("/environment-data/device/{device_id}", response_model=List[schemas.EnvironmentData])
async def get_environment_data_by_device(
    device_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db),
):
    return EnvironmentQueries.get_environment_data_by_device(db, device_id, start_time, end_time)


@router.get("/environment-data/abnormal/area/{area_id}", response_model=List[schemas.EnvironmentData])
async def get_abnormal_data_by_area(
    area_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    return EnvironmentQueries.get_abnormal_data_by_area(db, area_id, start_time, end_time)


@router.put("/environment-data/{data_id}/audit", response_model=schemas.EnvironmentData)
async def audit_environment_data(
    data_id: str,
    audit_status: str = Query(..., description="审核状态（已审核/待核实）"),
    abnormal_reason: Optional[str] = Query(None, description="异常原因"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    updated = EnvironmentQueries.update_data_audit_status(db, data_id, audit_status, abnormal_reason)
    if not updated:
        raise HTTPException(status_code=404, detail="监测数据不存在")
    return updated


@router.post("/calibration-records", response_model=schemas.CalibrationRecord)
async def create_calibration_record(
    record: schemas.CalibrationRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    if not record.record_id:
        record.record_id = f"CR_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
    return EnvironmentQueries.create_calibration_record(db, record)


@router.get("/calibration-records/device/{device_id}", response_model=List[schemas.CalibrationRecord])
async def get_calibration_records_by_device(device_id: int, db: Session = Depends(get_db)):
    return EnvironmentQueries.get_calibration_records_by_device(db, device_id)


@router.get("/reports/core-protection-abnormal")
async def get_core_protection_abnormal_report(
    index_name: str = Query("空气质量PM2.5", description="指标名称"),
    days: int = Query(30, ge=1, le=365, description="天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    return EnvironmentQueries.query_core_protection_abnormal_data(db, index_name, days)


@router.get("/reports/device-quality-rate")
async def get_device_quality_rate_report(
    days: int = Query(90, ge=1, le=365, description="天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    return EnvironmentQueries.get_device_data_quality_rate(db, days)


@router.get("/reports/overdue-calibration-data")
async def get_overdue_calibration_data_report(
    days: int = Query(30, ge=1, le=90, description="天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    return EnvironmentQueries.get_overdue_calibration_devices_data(db, days)


@router.get("/statistics/area/{area_id}", response_model=schemas.AreaStatisticsResponse)
async def get_area_statistics(
    area_id: int,
    days: int = Query(30, ge=1, le=365, description="天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    return EnvironmentQueries.get_data_statistics_by_area(db, area_id, days)


@router.delete("/monitor-indices/{index_id}")
async def delete_monitor_index(
    index_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    success = EnvironmentQueries.delete_monitor_index(db, index_id)
    if not success:
        raise HTTPException(status_code=404, detail="监测指标不存在")
    return {"message": "删除成功"}


@router.delete("/monitor-devices/{device_id}")
async def delete_monitor_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    success = EnvironmentQueries.delete_monitor_device(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="监测设备不存在")
    return {"message": "删除成功"}


@router.delete("/environment-data/{data_id}")
async def delete_environment_data(
    data_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    success = EnvironmentQueries.delete_environment_data(db, data_id)
    if not success:
        raise HTTPException(status_code=404, detail="监测数据不存在")
    return {"message": "删除成功"}


@router.delete("/calibration-records/{record_id}")
async def delete_calibration_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_roles(current_user, ["公园管理人员", "系统管理员"], "需要公园管理人员权限")
    success = EnvironmentQueries.delete_calibration_record(db, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="校准记录不存在")
    return {"message": "删除成功"}

