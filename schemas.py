from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProtectLevel(str, Enum):
    LEVEL_1 = "国家一级"
    LEVEL_2 = "国家二级"
    NONE = "无"


class MonitoringMethod(str, Enum):
    INFRARED_CAMERA = "红外相机"
    MANUAL_PATROL = "人工巡查"
    DRONE = "无人机"


class DataStatus(str, Enum):
    VALID = "有效"
    PENDING_VERIFICATION = "待核实"


class SpeciesBase(BaseModel):
    chinese_name: str = Field(..., min_length=1, max_length=100)
    latin_name: Optional[str] = Field(None, max_length=100)

    kingdom: Optional[str] = Field(None, max_length=50)
    phylum: Optional[str] = Field(None, max_length=50)
    class_name: Optional[str] = Field(None, max_length=50)
    order: Optional[str] = Field(None, max_length=50)
    family: Optional[str] = Field(None, max_length=50)
    genus: Optional[str] = Field(None, max_length=50)
    species: Optional[str] = Field(None, max_length=50)

    protect_level: ProtectLevel = ProtectLevel.NONE
    live_habit: Optional[str] = None
    distribution_range: Optional[str] = None


class SpeciesCreate(SpeciesBase):
    pass


class SpeciesUpdate(BaseModel):
    chinese_name: Optional[str] = Field(None, min_length=1, max_length=100)
    latin_name: Optional[str] = Field(None, max_length=100)

    kingdom: Optional[str] = Field(None, max_length=50)
    phylum: Optional[str] = Field(None, max_length=50)
    class_name: Optional[str] = Field(None, max_length=50)
    order: Optional[str] = Field(None, max_length=50)
    family: Optional[str] = Field(None, max_length=50)
    genus: Optional[str] = Field(None, max_length=50)
    species: Optional[str] = Field(None, max_length=50)

    protect_level: Optional[ProtectLevel] = None
    live_habit: Optional[str] = None
    distribution_range: Optional[str] = None


class SpeciesResponse(SpeciesBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class SpeciesQueryParams(BaseModel):
    chinese_name: Optional[str] = None
    latin_name: Optional[str] = None
    protect_level: Optional[ProtectLevel] = None
    page: int = 1
    page_size: int = 20


class MonitoringRecordBase(BaseModel):
    species_id: int
    device_id: Optional[int] = None
    time: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    monitoring_method: MonitoringMethod
    image_path: Optional[str] = None
    count: Optional[int] = None
    behavior: Optional[str] = None
    state: DataStatus = DataStatus.PENDING_VERIFICATION


class MonitoringRecordCreate(MonitoringRecordBase):
    pass


class MonitoringRecordUpdate(BaseModel):
    time: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    monitoring_method: Optional[MonitoringMethod] = None
    image_path: Optional[str] = None
    count: Optional[int] = None
    behavior: Optional[str] = None
    state: Optional[DataStatus] = None


class MonitoringRecordResponse(MonitoringRecordBase):
    id: int
    recorder_id: int
    analysis_conclusion: Optional[str] = None
    analyst_id: Optional[int] = None
    analysis_time: Optional[datetime] = None
    confidence_level: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class MonitoringRecordQueryParams(BaseModel):
    species_id: Optional[int] = None
    recorder_id: Optional[int] = None
    device_id: Optional[int] = None
    monitoring_method: Optional[MonitoringMethod] = None
    state: Optional[DataStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    area_id: Optional[int] = None
    page: int = 1
    page_size: int = 20


class AreaSpeciesCreate(BaseModel):
    species_id: int
    is_main: int = Field(0, ge=0, le=1)


class AreaSpeciesResponse(BaseModel):
    area_id: int
    species_id: int
    is_main: int
    model_config = ConfigDict(from_attributes=False)


class AnalysisConclusionCreate(BaseModel):
    record_id: int
    conclusion: str = Field(..., min_length=1)
    confidence_level: str = Field("中")


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    model_config = ConfigDict(from_attributes=False)


class PaginatedMonitoringRecords(PaginatedResponse):
    records: List[MonitoringRecordResponse]


class PaginatedSpecies(PaginatedResponse):
    species: List[SpeciesResponse]


class PaginatedAnalysisRecords(PaginatedResponse):
    records: List[MonitoringRecordResponse]


class AnalystStatsResponse(BaseModel):
    analyst_id: int
    total_analyzed: int
    confidence_stats: Dict[str, int]


class OverallStatsResponse(BaseModel):
    species_stats: Dict[str, int]
    record_stats: Dict[str, Any]
