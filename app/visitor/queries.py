from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_or_create_visitor_id(db: Session, visitor_name: str, id_card_no: str, phone: Optional[str]) -> int:
    vid = db.execute(
        text("SELECT VisitorId FROM dbo.Visitors WHERE IdCardNo = :idc"),
        {"idc": id_card_no},
    ).scalar()
    if vid:
        db.execute(
            text(
                "UPDATE dbo.Visitors SET VisitorName = :n, Phone = :p WHERE VisitorId = :vid"
            ),
            {"n": visitor_name, "p": phone, "vid": int(vid)},
        )
        return int(vid)

    new_id = db.execute(
        text(
            """
            INSERT INTO dbo.Visitors(VisitorName, IdCardNo, Phone)
            OUTPUT INSERTED.VisitorId
            VALUES (:n, :idc, :p)
            """
        ),
        {"n": visitor_name, "idc": id_card_no, "p": phone},
    ).scalar()
    if new_id is None:
        raise RuntimeError("Failed to insert visitor")
    return int(new_id)


def create_reservation(
    db: Session,
    visitor_id: int,
    reserve_date,
    time_slot: str,
    party_size: int,
    ticket_amount: float,
    area_id: Optional[int] = None,
    park_name: Optional[str] = None,
    user_id: Optional[int] = None,
    reserve_status: str = "待审核",
    pay_status: str = "未支付",
) -> int:
    rid = db.execute(
        text(
            """
            INSERT INTO dbo.Reservations(
                VisitorId, ReserveDate, TimeSlot, PartySize, 
                ReserveStatus, TicketAmount, PayStatus, ParkName, UserId
            )
            OUTPUT INSERTED.ReservationId
            VALUES (
                :vid, :d, :ts, :ps, :rs, :ta, :pay, :park_name, :user_id
            )
            """
        ),
        {
            "vid": visitor_id,
            "d": reserve_date,
            "ts": time_slot,
            "ps": party_size,
            "rs": reserve_status,
            "ta": ticket_amount,
            "pay": pay_status,
            "park_name": park_name,
            "user_id": user_id,
        },
    ).scalar()
    if rid is None:
        raise RuntimeError("Failed to insert reservation")
    return int(rid)


def cancel_reservation(db: Session, reservation_id: int, visitor_id: int) -> int:
    res = db.execute(
        text(
            """
            UPDATE dbo.Reservations
            SET ReserveStatus = N'已取消'
            WHERE ReservationId = :rid AND VisitorId = :vid AND ReserveStatus = N'已确认'
            """
        ),
        {"rid": reservation_id, "vid": visitor_id},
    )
    return int(res.rowcount or 0)


def create_visit(
    db: Session,
    visitor_id: int,
    area_id: int,
    entry_method: str,
    reservation_id: Optional[int],
    entry_time: Optional[datetime],
) -> int:
    if entry_time is None:
        entry_time = datetime.now()
    result = db.execute(
        text(
            """
            SET NOCOUNT ON;
            DECLARE @InsertedIds TABLE (VisitId INT);
            INSERT INTO dbo.Visits(VisitorId, ReservationId, AreaId, EntryTime, ExitTime, EntryMethod)
            OUTPUT INSERTED.VisitId INTO @InsertedIds
            VALUES (:vid, :rid, :aid, :et, NULL, :em);
            SELECT VisitId FROM @InsertedIds;
            """
        ),
        {"vid": visitor_id, "rid": reservation_id, "aid": area_id, "et": entry_time, "em": entry_method},
    )
    new_visit_id = result.scalar()
    if new_visit_id is None:
        raise RuntimeError("Failed to insert visit")
    return int(new_visit_id)


def exit_visit(db: Session, visit_id: int) -> int:
    res = db.execute(
        text("UPDATE dbo.Visits SET ExitTime = COALESCE(ExitTime, :t) WHERE VisitId = :id"),
        {"id": visit_id, "t": datetime.now()},
    )
    return int(res.rowcount or 0)


def create_track(
    db: Session,
    visitor_id: int,
    visit_id: Optional[int],
    locate_time: Optional[datetime],
    latitude: float,
    longitude: float,
    area_id: int,
    is_out_of_route: bool,
) -> int:
    if locate_time is None:
        locate_time = datetime.now()
    new_track_id = db.execute(
        text(
            """
            INSERT INTO dbo.VisitorTracks(VisitorId, VisitId, LocateTime, Latitude, Longitude, AreaId, IsOutOfRoute)
            OUTPUT INSERTED.TrackId
            VALUES (:vid, :visit, :t, :lat, :lng, :aid, :oor)
            """
        ),
        {
            "vid": visitor_id,
            "visit": visit_id,
            "t": locate_time,
            "lat": latitude,
            "lng": longitude,
            "aid": area_id,
            "oor": 1 if is_out_of_route else 0,
        },
    ).scalar()
    if new_track_id is None:
        raise RuntimeError("Failed to insert track")
    return int(new_track_id)


def list_flow_controls(db: Session) -> Sequence[dict]:
    return db.execute(text("SELECT * FROM dbo.v_AreaFlowControlStatus")).mappings().all()


def list_out_of_route_tracks(db: Session) -> Sequence[dict]:
    return db.execute(
        text("SELECT TOP 200 * FROM dbo.v_VisitorOutOfRouteTracksRecent ORDER BY LocateTime DESC")
    ).mappings().all()


def list_reservations(db: Session) -> Sequence[dict]:
    return db.execute(
        text("SELECT TOP 200 * FROM dbo.v_VisitorReservationStatus ORDER BY ReservationId DESC")
    ).mappings().all()


# ========== 新增：公园相关查询（修正版） ==========
def list_reservations_with_park(db: Session) -> Sequence[dict]:
    """查询预约记录并关联区域（公园）名称"""
    return db.execute(
        text("""
            SELECT DISTINCT TOP 200
                r.ReservationId, r.ReserveDate, r.TimeSlot, r.PartySize,
                r.ReserveStatus, r.TicketAmount, r.PayStatus,
                r.VisitorId, v.VisitorName, v.IdCardNo, v.Phone,
                NULL AS area_id, r.ParkName AS area_name
            FROM dbo.Reservations r
            JOIN dbo.Visitors v ON r.VisitorId = v.VisitorId
            ORDER BY r.ReservationId DESC
        """)
    ).mappings().all()


def list_my_reservations(db: Session, user_id: int) -> Sequence[dict]:
    """查询当前用户的预约记录"""
    return db.execute(
        text("""
            SELECT TOP 200
                r.ReservationId, r.ReserveDate, r.TimeSlot, r.PartySize,
                r.ReserveStatus, r.TicketAmount, r.PayStatus,
                r.VisitorId, v.VisitorName, v.IdCardNo, v.Phone,
                NULL AS area_id, r.ParkName AS area_name
            FROM dbo.Reservations r
            JOIN dbo.Visitors v ON r.VisitorId = v.VisitorId
            WHERE r.UserId = :user_id
            ORDER BY r.ReservationId DESC
        """),
        {"user_id": user_id},
    ).mappings().all()