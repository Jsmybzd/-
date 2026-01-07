
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class ReservationCreate(BaseModel):
    visitor_name: str = Field(..., min_length=1, max_length=50)
    id_card_no: str = Field(..., min_length=5, max_length=30)
    phone: Optional[str] = Field(None, max_length=30)
    reserve_date: date
    time_slot: str = Field(..., description="上午/下午/全天")
    party_size: int = Field(..., gt=0, le=20)
    ticket_amount: Optional[float] = Field(None, ge=0)
    area_id: Optional[int] = Field(None, description="预约的区域ID（公园ID）")
    park_name: Optional[str] = Field(None, description="公园名称")


class ReservationOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reservation_id: Optional[int] = Field(None, alias="ReservationId")
    reserve_date: Optional[date] = Field(None, alias="ReserveDate")
    time_slot: Optional[str] = Field(None, alias="TimeSlot")
    party_size: Optional[int] = Field(None, alias="PartySize")
    reserve_status: Optional[str] = Field(None, alias="ReserveStatus")
    ticket_amount: Optional[float] = Field(None, alias="TicketAmount")
    pay_status: Optional[str] = Field(None, alias="PayStatus")
    visitor_id: Optional[int] = Field(None, alias="VisitorId")
    visitor_name: Optional[str] = Field(None, alias="VisitorName")
    id_card_no: Optional[str] = Field(None, alias="IdCardNo")
    phone: Optional[str] = Field(None, alias="Phone")
    area_id: Optional[int] = Field(None, alias="area_id")
    area_name: Optional[str] = Field(None, alias="area_name")


class FlowControlOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    area_id: Optional[int] = Field(None, alias="AreaId")
    area_name: Optional[str] = Field(None, alias="AreaName")
    daily_max_capacity: Optional[int] = Field(None, alias="DailyMaxCapacity")
    current_in_park: Optional[int] = Field(0, alias="CurrentInPark")
    warning_threshold: Optional[int] = Field(None, alias="WarningThreshold")
    current_status: Optional[str] = Field(None, alias="CurrentStatus")


class VisitEnterCreate(BaseModel):
    id_card_no: str = Field(..., min_length=5, max_length=30)
    area_id: int
    entry_method: str = Field(..., description="线上预约/现场购票")
    reservation_id: Optional[int] = None
    entry_time: Optional[datetime] = None


class VisitOut(BaseModel):
    visit_id: int
    visitor_id: int
    reservation_id: Optional[int]
    area_id: int
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_method: str


class TrackCreate(BaseModel):
    id_card_no: str = Field(..., min_length=5, max_length=30)
    visit_id: Optional[int] = None
    locate_time: Optional[datetime] = None
    latitude: float
    longitude: float
    area_id: int
    is_out_of_route: bool = False


class OutOfRouteTrackOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    track_id: Optional[int] = Field(None, alias="TrackId")
    locate_time: Optional[datetime] = Field(None, alias="LocateTime")
    area_name: Optional[str] = Field(None, alias="AreaName")
    visitor_name: Optional[str] = Field(None, alias="VisitorName")
    id_card_no: Optional[str] = Field(None, alias="IdCardNo")
    latitude: Optional[float] = Field(None, alias="Latitude")
    longitude: Optional[float] = Field(None, alias="Longitude")


class RecalcFlowControlRequest(BaseModel):
    area_id: Optional[int] = None


class VisitorOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    visitor_id: Optional[int] = Field(None, alias="VisitorId")
    visitor_name: Optional[str] = Field(None, alias="VisitorName")
    id_card_no: Optional[str] = Field(None, alias="IdCardNo")
    phone: Optional[str] = Field(None, alias="Phone")
    created_at: Optional[datetime] = Field(None, alias="CreatedAt")


class VisitListOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    visit_id: Optional[int] = Field(None, alias="VisitId")
    visitor_id: Optional[int] = Field(None, alias="VisitorId")
    visitor_name: Optional[str] = Field(None, alias="VisitorName")
    reservation_id: Optional[int] = Field(None, alias="ReservationId")
    area_id: Optional[int] = Field(None, alias="AreaId")
    entry_time: Optional[datetime] = Field(None, alias="EntryTime")
    exit_time: Optional[datetime] = Field(None, alias="ExitTime")
    entry_method: Optional[str] = Field(None, alias="EntryMethod")


class AlertOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    alert_id: int = Field(..., alias="AlertId")
    alert_type: str = Field(..., alias="AlertType")
    area_id: Optional[int] = Field(None, alias="AreaId")
    visitor_id: Optional[int] = Field(None, alias="VisitorId")
    severity: str = Field(..., alias="Severity")
    message: str = Field(..., alias="Message")
    status: str = Field(..., alias="Status")
    created_at: datetime = Field(..., alias="CreatedAt")


class ReservationConfirm(BaseModel):
    status: str = Field(..., description="已确认/已取消/已完成")

