
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.api import get_current_user
from app.core import models as core_models
from app.visitor import schemas
from app.visitor import queries


router = APIRouter(prefix="/visitor", tags=["游客智能管理"])


def _require_role(user: core_models.User, allowed: set[str]):
    if user.role_type not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该接口")


@router.get("/flow-controls", response_model=list[schemas.FlowControlOut])
def get_flow_controls(
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"游客", "公园管理人员", "系统管理员"})
    return queries.list_flow_controls(db)


@router.get("/reservations", response_model=list[schemas.ReservationOut])
def list_all_reservations(
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    #return queries.list_reservations(db)
    return queries.list_reservations_with_park(db)


@router.get("/reservations/me", response_model=list[schemas.ReservationOut])
def list_my_reservations_api(
        db: Session = Depends(get_db),
        current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"游客"})
    return queries.list_my_reservations(db, current_user.id)


@router.post("/reservations", response_model=dict)
def create_reservation(
    payload: schemas.ReservationCreate,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"游客", "公园管理人员", "系统管理员"})

    try:
        phone = payload.phone or current_user.phone
        visitor_id = queries.get_or_create_visitor_id(db, payload.visitor_name, payload.id_card_no, phone)

        ticket_amount = payload.ticket_amount
        if ticket_amount is None:
            ticket_amount = float(payload.party_size) * 120.0

        reservation_id = queries.create_reservation(
            db,
            visitor_id=visitor_id,
            reserve_date=payload.reserve_date,
            time_slot=payload.time_slot,
            party_size=payload.party_size,
            ticket_amount=ticket_amount,
            area_id=payload.area_id,
            park_name=payload.park_name,
            user_id=current_user.id,
        )

        db.commit()
        return {"reservation_id": reservation_id, "ticket_amount": ticket_amount, "status": "待审核"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"预约创建失败: {str(e)}")


@router.post("/reservations/{reservation_id}/cancel", response_model=dict)
def cancel_my_reservation(
    reservation_id: int,
    id_card_no: str,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"游客"})
    visitor_id = db.execute(
        text("SELECT VisitorId FROM dbo.Visitors WHERE IdCardNo = :idc"),
        {"idc": id_card_no},
    ).scalar()
    if not visitor_id:
        raise HTTPException(status_code=404, detail="游客不存在")

    changed = queries.cancel_reservation(db, reservation_id, int(visitor_id))
    db.commit()
    if changed == 0:
        raise HTTPException(status_code=400, detail="取消失败：订单不存在或状态不可取消")
    return {"success": True}


@router.post("/visits/enter", response_model=dict)
def enter_park(
    payload: schemas.VisitEnterCreate,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    visitor_row = db.execute(
        text("SELECT VisitorId, VisitorName, Phone FROM dbo.Visitors WHERE IdCardNo = :idc"),
        {"idc": payload.id_card_no},
    ).mappings().first()
    if not visitor_row:
        raise HTTPException(status_code=404, detail="游客不存在，请先创建游客/预约")

    # 验证预约编号是否存在且属于该游客
    reservation_id = payload.reservation_id
    if reservation_id is not None:
        res_check = db.execute(
            text("SELECT ReservationId, VisitorId FROM dbo.Reservations WHERE ReservationId = :rid"),
            {"rid": reservation_id}
        ).mappings().first()
        if not res_check:
            raise HTTPException(status_code=400, detail="预约编号不存在")
        if int(res_check["VisitorId"]) != int(visitor_row["VisitorId"]):
            raise HTTPException(status_code=400, detail="预约编号与游客身份证不匹配")

    try:
        visit_id = queries.create_visit(
            db,
            visitor_id=int(visitor_row["VisitorId"]),
            area_id=payload.area_id,
            entry_method=payload.entry_method,
            reservation_id=reservation_id,
            entry_time=payload.entry_time,
        )
        db.commit()
        return {"visit_id": visit_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"入园登记失败: {str(e)}")


@router.post("/visits/{visit_id}/exit", response_model=dict)
def exit_park(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    changed = queries.exit_visit(db, visit_id)
    db.commit()
    if changed == 0:
        raise HTTPException(status_code=404, detail="入园记录不存在")
    return {"success": True}


@router.post("/tracks", response_model=dict)
def create_track(
    payload: schemas.TrackCreate,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"游客", "公园管理人员", "系统管理员"})

    visitor_row = db.execute(
        text("SELECT VisitorId, VisitorName, Phone FROM dbo.Visitors WHERE IdCardNo = :idc"),
        {"idc": payload.id_card_no},
    ).mappings().first()
    if not visitor_row:
        # 自动创建游客记录（用于模拟轨迹测试）
        visitor_id = queries.get_or_create_visitor_id(
            db,
            visitor_name="模拟游客",
            id_card_no=payload.id_card_no,
            phone=None,
        )
        visitor_row = {"VisitorId": visitor_id}

    track_id = queries.create_track(
        db,
        visitor_id=int(visitor_row["VisitorId"]),
        visit_id=payload.visit_id,
        locate_time=payload.locate_time,
        latitude=payload.latitude,
        longitude=payload.longitude,
        area_id=payload.area_id,
        is_out_of_route=payload.is_out_of_route,
    )
    db.commit()
    return {"track_id": track_id}


@router.get("/tracks/out-of-route", response_model=list[schemas.OutOfRouteTrackOut])
def list_out_of_route(
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    return queries.list_out_of_route_tracks(db)


@router.post("/flow-controls/recalc", response_model=dict)
def recalc_flow_controls(
    payload: schemas.RecalcFlowControlRequest,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    if payload.area_id is None:
        db.execute(text("EXEC dbo.sp_RecalcFlowControl NULL"))
    else:
        db.execute(text("EXEC dbo.sp_RecalcFlowControl :aid"), {"aid": payload.area_id})
    db.commit()
    return {"success": True}


@router.get("/visitors", response_model=list[schemas.VisitorOut])
def list_visitors(
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    """获取游客列表"""
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    rows = db.execute(
        text("SELECT TOP 500 * FROM dbo.Visitors ORDER BY CreatedAt DESC")
    ).mappings().all()
    return rows


@router.get("/visits", response_model=list[schemas.VisitListOut])
def list_visits(
    in_park_only: bool = False,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    """获取入园记录列表"""
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    if in_park_only:
        sql = """
            SELECT v.*, vs.VisitorName 
            FROM dbo.Visits v
            JOIN dbo.Visitors vs ON v.VisitorId = vs.VisitorId
            WHERE v.ExitTime IS NULL
            ORDER BY v.EntryTime DESC
        """
    else:
        sql = """
            SELECT TOP 500 v.*, vs.VisitorName 
            FROM dbo.Visits v
            JOIN dbo.Visitors vs ON v.VisitorId = vs.VisitorId
            ORDER BY v.EntryTime DESC
        """
    rows = db.execute(text(sql)).mappings().all()
    return rows


@router.put("/reservations/{reservation_id}/confirm", response_model=dict)
def confirm_reservation(
    reservation_id: int,
    payload: schemas.ReservationConfirm,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    """管理员确认/取消/完成预约"""
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    
    if payload.status not in ["已确认", "已取消", "已完成"]:
        raise HTTPException(status_code=400, detail="无效的状态值")
    
    result = db.execute(
        text("UPDATE dbo.Reservations SET ReserveStatus = :st WHERE ReservationId = :rid"),
        {"st": payload.status, "rid": reservation_id}
    )
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    
    return {"success": True, "new_status": payload.status}


@router.get("/alerts", response_model=list)
def list_alerts(
    status: str = None,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    """获取预警列表"""
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    
    # 检查Alerts表是否存在
    table_exists = db.execute(
        text("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Alerts'")
    ).scalar()
    
    if not table_exists:
        return []
    
    try:
        if status:
            rows = db.execute(
                text("SELECT TOP 200 * FROM dbo.Alerts WHERE Status = :st ORDER BY CreatedAt DESC"),
                {"st": status}
            ).mappings().all()
        else:
            rows = db.execute(
                text("SELECT TOP 200 * FROM dbo.Alerts ORDER BY CreatedAt DESC")
            ).mappings().all()
        return [dict(r) for r in rows]
    except Exception:
        return []


@router.put("/alerts/{alert_id}/handle", response_model=dict)
def handle_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    """处理预警，同时更新关联的轨迹记录状态"""
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    
    try:
        # 1. 获取预警信息，找到关联的轨迹记录
        alert_row = db.execute(
            text("SELECT SourceTable, SourceId FROM dbo.Alerts WHERE AlertId = :aid"),
            {"aid": alert_id}
        ).mappings().first()
        
        if not alert_row:
            raise HTTPException(status_code=404, detail="预警记录不存在")
        
        # 2. 更新预警状态为已处理
        db.execute(
            text("""
                UPDATE dbo.Alerts 
                SET Status = N'已处理', HandledAt = SYSUTCDATETIME(), HandledBy = :uid 
                WHERE AlertId = :aid
            """),
            {"aid": alert_id, "uid": current_user.id}
        )
        
        # 3. 如果是轨迹越界预警，同时更新轨迹记录状态为已解决
        source_table = alert_row.get("SourceTable")
        source_id = alert_row.get("SourceId")
        
        if source_table == "VisitorTracks" and source_id:
            db.execute(
                text("""
                    UPDATE dbo.VisitorTracks 
                    SET Status = N'已解决' 
                    WHERE TrackId = :tid
                """),
                {"tid": source_id}
            )
        
        db.commit()
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/tracks", response_model=list)
def list_tracks(
    visitor_id: int = None,
    visit_id: int = None,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    """获取游客轨迹列表"""
    _require_role(current_user, {"公园管理人员", "系统管理员"})
    
    if visitor_id:
        rows = db.execute(
            text("""
                SELECT TOP 500 t.*, v.VisitorName 
                FROM dbo.VisitorTracks t
                JOIN dbo.Visitors v ON t.VisitorId = v.VisitorId
                WHERE t.VisitorId = :vid
                ORDER BY t.LocateTime DESC
            """),
            {"vid": visitor_id}
        ).mappings().all()
    elif visit_id:
        rows = db.execute(
            text("""
                SELECT TOP 500 t.*, v.VisitorName 
                FROM dbo.VisitorTracks t
                JOIN dbo.Visitors v ON t.VisitorId = v.VisitorId
                WHERE t.VisitId = :vid
                ORDER BY t.LocateTime DESC
            """),
            {"vid": visit_id}
        ).mappings().all()
    else:
        rows = db.execute(
            text("""
                SELECT TOP 200 t.*, v.VisitorName 
                FROM dbo.VisitorTracks t
                JOIN dbo.Visitors v ON t.VisitorId = v.VisitorId
                ORDER BY t.LocateTime DESC
            """)
        ).mappings().all()
    return [dict(r) for r in rows]

# ========== 新增：区域列表接口（供前端地图/下拉框） ==========
@router.get("/areas", response_model=list[dict])
def get_all_areas(
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    """获取所有区域（公园）列表"""
    _require_role(current_user, {"游客", "公园管理人员", "系统管理员", "生态监测员", "数据分析师", "科研人员"})
    rows = db.execute(
        text("""
            SELECT 
                id AS area_id,
                name AS area_name,
                type AS area_type,
                lng AS longitude,
                lat AS latitude,
                area AS area_size
            FROM dbo.区域表
            ORDER BY id ASC
        """)
    ).mappings().all()
    return [dict(row) for row in rows]

# ========== 新增：区域详情接口（供前端地图弹窗） ==========
@router.get("/areas/{area_id}", response_model=dict)
def get_area_info(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: core_models.User = Depends(get_current_user),
):
    """获取单个区域详情"""
    _require_role(current_user, {"游客", "公园管理人员", "系统管理员"})
    row = db.execute(
        text("""
            SELECT 
                id AS area_id,
                name AS area_name,
                type AS area_type,
                lng AS longitude,
                lat AS latitude,
                area AS area_size,
                main_protect AS protect_rules,
                main_species_id AS species_id,
                suitable_score AS score
            FROM dbo.区域表
            WHERE id = :area_id
        """),
        {"area_id": area_id}
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="区域不存在")
    return dict(row)

@router.get("/areas/names", response_model=list[dict])
def get_area_names(
        q: str = None,  # 模糊搜索关键词
        db: Session = Depends(get_db),
        current_user: core_models.User = Depends(get_current_user),
):
    _require_role(current_user, {"游客", "公园管理人员", "系统管理员"})

    base_sql = """
        SELECT id AS area_id, name AS area_name
        FROM dbo.区域表
    """
    if q:
        sql = base_sql + " WHERE name LIKE :q ORDER BY name ASC"
        rows = db.execute(text(sql), {"q": f"%{q}%"}).mappings().all()
    else:
        sql = base_sql + " ORDER BY name ASC"
        rows = db.execute(text(sql)).mappings().all()

    return [dict(row) for row in rows]