from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MonitorIndexBase(BaseModel):
    index_name: str = Field(..., min_length=1, max_length=50)
    unit: str = Field(..., min_length=1, max_length=20)
    upper_threshold: float
    lower_threshold: float
    monitor_frequency: str = Field(..., min_length=1, max_length=10)


class MonitorIndexCreate(MonitorIndexBase):
    index_id: str = Field(..., min_length=1, max_length=20)


class MonitorIndexUpdate(BaseModel):
    index_name: Optional[str] = None
    unit: Optional[str] = None
    upper_threshold: Optional[float] = None
    lower_threshold: Optional[float] = None
    monitor_frequency: Optional[str] = None


class MonitorIndex(MonitorIndexBase):
    index_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class MonitorDeviceCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    deployment_area_id: Optional[int] = None
    install_time: Optional[datetime] = None
    calibration_cycle: int = Field(30, ge=1)
    status: str = Field(default="正常")
    communication_protocol: Optional[str] = Field(None, max_length=50)
    last_calibration_time: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MonitorDeviceUpdate(BaseModel):
    type: Optional[str] = None
    deployment_area_id: Optional[int] = None
    calibration_cycle: Optional[int] = None
    status: Optional[str] = None
    communication_protocol: Optional[str] = None
    last_calibration_time: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MonitorDevice(BaseModel):
    id: int
    type: str
    deployment_area_id: Optional[int] = None
    install_time: Optional[datetime] = None
    calibration_cycle: Optional[int] = 30
    last_calibration_time: Optional[datetime] = None
    status: Optional[str] = "正常"
    communication_protocol: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class EnvironmentDataBase(BaseModel):
    index_id: str = Field(..., min_length=1, max_length=20)
    device_id: int
    collect_time: datetime
    monitor_value: float
    area_id: int
    data_quality: str = Field(default="中")


class EnvironmentDataCreate(EnvironmentDataBase):
    data_id: Optional[str] = Field(None, min_length=1, max_length=30)


class EnvironmentDataUpdate(BaseModel):
    data_quality: Optional[str] = None
    is_abnormal: Optional[int] = None
    abnormal_reason: Optional[str] = None
    audit_status: Optional[str] = None


class EnvironmentData(EnvironmentDataBase):
    data_id: str
    is_abnormal: int = 0
    abnormal_reason: Optional[str] = None
    audit_status: str = "未审核"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class CalibrationRecordBase(BaseModel):
    device_id: int
    calibration_time: datetime
    calibrator_id: int
    calibration_result: str
    calibration_desc: Optional[str] = None


class CalibrationRecordCreate(CalibrationRecordBase):
    record_id: Optional[str] = Field(None, min_length=1, max_length=30)


class CalibrationRecord(CalibrationRecordBase):
    record_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AreaStatisticsResponse(BaseModel):
    total_count: int
    abnormal_count: int
    abnormal_rate: float
    avg_value: float
    min_value: float
    max_value: float
    model_config = ConfigDict(from_attributes=False)


class ReportRow(BaseModel):
    data: Dict[str, Any]
    model_config = ConfigDict(from_attributes=False)
