from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.core.models import User
from app.shared.models import 监测设备表, 区域表

from .models import 物种表, 物种监测记录表, 区域物种关联表


class MonitoringRecordService:
    @staticmethod
    def create_record(db: Session, record_data, current_user_id: int) -> 物种监测记录表:
        species = db.get(物种表, record_data.species_id)
        if not species:
            raise HTTPException(status_code=404, detail="物种不存在")

        if record_data.device_id:
            device = db.get(监测设备表, record_data.device_id)
            if not device:
                raise HTTPException(status_code=404, detail="监测设备不存在")

        recorder = db.get(User, current_user_id)
        if not recorder:
            raise HTTPException(status_code=404, detail="记录人不存在")

        monitoring_method_value = (
            record_data.monitoring_method.value
            if hasattr(record_data.monitoring_method, "value")
            else record_data.monitoring_method
        )
        state_value = record_data.state.value if hasattr(record_data.state, "value") else record_data.state

        db_record = 物种监测记录表(
            species_id=record_data.species_id,
            device_id=record_data.device_id,
            time=record_data.time,
            latitude=record_data.latitude,
            longitude=record_data.longitude,
            monitoring_method=monitoring_method_value,
            image_path=record_data.image_path,
            count=record_data.count,
            behavior=record_data.behavior,
            state=state_value,
            recorder_id=current_user_id,
        )

        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_record(db: Session, record_id: int) -> Optional[物种监测记录表]:
        return db.get(物种监测记录表, record_id)

    @staticmethod
    def list_records(db: Session, query_params) -> Dict[str, Any]:
        conditions = []

        if query_params.species_id:
            conditions.append(物种监测记录表.species_id == query_params.species_id)
        if query_params.recorder_id:
            conditions.append(物种监测记录表.recorder_id == query_params.recorder_id)
        if query_params.device_id:
            conditions.append(物种监测记录表.device_id == query_params.device_id)
        if query_params.monitoring_method:
            conditions.append(
                物种监测记录表.monitoring_method
                == (
                    query_params.monitoring_method.value
                    if hasattr(query_params.monitoring_method, "value")
                    else query_params.monitoring_method
                )
            )
        if query_params.state:
            conditions.append(
                物种监测记录表.state
                == (
                    query_params.state.value
                    if hasattr(query_params.state, "value")
                    else query_params.state
                )
            )
        if query_params.start_date:
            conditions.append(物种监测记录表.time >= query_params.start_date)
        if query_params.end_date:
            conditions.append(物种监测记录表.time <= query_params.end_date)

        if query_params.area_id:
            species_in_area = db.scalars(
                select(区域物种关联表.species_id).where(区域物种关联表.area_id == query_params.area_id)
            ).all()
            if species_in_area:
                conditions.append(物种监测记录表.species_id.in_(species_in_area))
            else:
                conditions.append(物种监测记录表.species_id == -1)

        base_query = select(物种监测记录表)
        if conditions:
            base_query = base_query.where(and_(*conditions))

        total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

        offset = (query_params.page - 1) * query_params.page_size
        records = (
            db.scalars(
                base_query.order_by(desc(物种监测记录表.time)).offset(offset).limit(query_params.page_size)
            ).all()
        )

        return {
            "total": total,
            "records": records,
            "page": query_params.page,
            "page_size": query_params.page_size,
        }

    @staticmethod
    def get_pending_records(db: Session, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        base_query = select(物种监测记录表).where(物种监测记录表.state == "待核实")
        total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

        offset = (page - 1) * page_size
        records = (
            db.scalars(base_query.order_by(desc(物种监测记录表.time)).offset(offset).limit(page_size)).all()
        )

        return {"total": total, "records": records, "page": page, "page_size": page_size}

    @staticmethod
    def verify_record(db: Session, record_id: int) -> 物种监测记录表:
        record = db.get(物种监测记录表, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="监测记录不存在")

        record.state = "有效"
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def update_record(db: Session, record_id: int, update_data, current_user_id: int) -> 物种监测记录表:
        record = db.get(物种监测记录表, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="监测记录不存在")

        current_user = db.get(User, current_user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if current_user.id != record.recorder_id and current_user.role_type != "数据分析师":
            raise HTTPException(status_code=403, detail="无权修改此记录")

        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is None:
                continue
            if field == "monitoring_method" and hasattr(value, "value"):
                value = value.value
            if field == "state" and hasattr(value, "value"):
                value = value.value
            setattr(record, field, value)

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_record(db: Session, record_id: int, current_user_id: int) -> None:
        record = db.get(物种监测记录表, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="监测记录不存在")

        current_user = db.get(User, current_user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if current_user.id != record.recorder_id and current_user.role_type != "数据分析师":
            raise HTTPException(status_code=403, detail="无权删除此记录")

        db.delete(record)
        db.commit()

    @staticmethod
    def get_overall_stats(db: Session) -> Dict[str, Any]:
        total_records = db.scalar(select(func.count()).select_from(物种监测记录表)) or 0
        pending_records = (
            db.scalar(select(func.count()).select_from(物种监测记录表).where(物种监测记录表.state == "待核实"))
            or 0
        )

        method_stats: Dict[str, int] = {}
        for method in ["红外相机", "人工巡查", "无人机"]:
            cnt = (
                db.scalar(
                    select(func.count()).select_from(物种监测记录表).where(物种监测记录表.monitoring_method == method)
                )
                or 0
            )
            method_stats[method] = cnt

        return {
            "total_records": total_records,
            "pending_records": pending_records,
            "method_stats": method_stats,
        }
