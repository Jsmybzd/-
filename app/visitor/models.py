
from sqlalchemy import Column, Integer, String, DateTime, Date, DECIMAL, ForeignKey, CheckConstraint
from sqlalchemy.sql import func

from app.db import Base


class Visitor(Base):
    __tablename__ = "Visitors"

    VisitorId = Column(Integer, primary_key=True, autoincrement=True)
    VisitorName = Column(String(50), nullable=False)
    IdCardNo = Column(String(30), nullable=False, unique=True)
    Phone = Column(String(30), nullable=True)
    CreatedAt = Column(DateTime, server_default=func.now(), nullable=False)


class Reservation(Base):
    __tablename__ = "Reservations"

    ReservationId = Column(Integer, primary_key=True, autoincrement=True)
    VisitorId = Column(Integer, ForeignKey("Visitors.VisitorId"), nullable=False)
    ReserveDate = Column(Date, nullable=False)
    TimeSlot = Column(String(20), nullable=False)
    PartySize = Column(Integer, nullable=False)
    ReserveStatus = Column(String(10), nullable=False)
    TicketAmount = Column(DECIMAL(10, 2), nullable=False)
    PayStatus = Column(String(10), nullable=False)
    CreatedAt = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("TimeSlot IN ('上午','下午','全天')", name="CK_Reservations_TimeSlot"),
        CheckConstraint("ReserveStatus IN ('已确认','已取消','已完成')", name="CK_Reservations_Status"),
        CheckConstraint("PayStatus IN ('未支付','已支付','已退款')", name="CK_Reservations_PayStatus"),
        CheckConstraint("PartySize > 0 AND PartySize <= 20", name="CK_Reservations_PartySize"),
    )


class Visit(Base):
    __tablename__ = "Visits"

    VisitId = Column(Integer, primary_key=True, autoincrement=True)
    VisitorId = Column(Integer, ForeignKey("Visitors.VisitorId"), nullable=False)
    ReservationId = Column(Integer, ForeignKey("Reservations.ReservationId"), nullable=True)
    AreaId = Column(Integer, nullable=False)
    EntryTime = Column(DateTime, nullable=False)
    ExitTime = Column(DateTime, nullable=True)
    EntryMethod = Column(String(10), nullable=False)

    __table_args__ = (
        CheckConstraint("EntryMethod IN ('线上预约','现场购票')", name="CK_Visits_EntryMethod"),
    )


class VisitorTrack(Base):
    __tablename__ = "VisitorTracks"

    TrackId = Column(Integer, primary_key=True, autoincrement=True)
    VisitorId = Column(Integer, ForeignKey("Visitors.VisitorId"), nullable=False)
    VisitId = Column(Integer, ForeignKey("Visits.VisitId"), nullable=True)
    LocateTime = Column(DateTime, nullable=False)
    Latitude = Column(DECIMAL(9, 6), nullable=False)
    Longitude = Column(DECIMAL(9, 6), nullable=False)
    AreaId = Column(Integer, nullable=False)
    IsOutOfRoute = Column(Integer, nullable=False, default=0)


class FlowControl(Base):
    __tablename__ = "FlowControls"

    AreaId = Column(Integer, primary_key=True)
    DailyMaxCapacity = Column(Integer, nullable=False)
    CurrentInPark = Column(Integer, nullable=False, default=0)
    WarningRatio = Column(DECIMAL(5, 2), nullable=False, default=0.80)
    CurrentStatus = Column(String(10), nullable=False, default="正常")

    __table_args__ = (
        CheckConstraint("CurrentStatus IN ('正常','预警','限流')", name="CK_FlowControls_Status"),
        CheckConstraint("DailyMaxCapacity > 0", name="CK_FlowControls_Capacity"),
        CheckConstraint("CurrentInPark >= 0", name="CK_FlowControls_Current"),
    )

