from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.orm import Session

from app.shared.models import 区域表, 监测设备表

from .models import 环境监测数据表, 环境监测指标表, 设备校准记录表


class EnvironmentQueries:
    @staticmethod
    def create_monitor_index(db: Session, index) -> 环境监测指标表:
        db_index = 环境监测指标表(
            index_id=index.index_id,
            index_name=index.index_name,
            unit=index.unit,
            upper_threshold=index.upper_threshold,
            lower_threshold=index.lower_threshold,
            monitor_frequency=index.monitor_frequency,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(db_index)
        db.commit()
        db.refresh(db_index)
        return db_index

    @staticmethod
    def get_monitor_index(db: Session, index_id: str) -> Optional[环境监测指标表]:
        return db.get(环境监测指标表, index_id)

    @staticmethod
    def list_monitor_indices(db: Session, skip: int = 0, limit: int = 100) -> List[环境监测指标表]:
        return db.scalars(
            select(环境监测指标表)
            .order_by(desc(环境监测指标表.created_at), 环境监测指标表.index_id)
            .offset(skip)
            .limit(limit)
        ).all()

    @staticmethod
    def update_monitor_index(db: Session, index_id: str, update_data: Dict[str, Any]) -> Optional[环境监测指标表]:
        db_index = db.get(环境监测指标表, index_id)
        if not db_index:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(db_index, key, value)
        db_index.updated_at = datetime.now()

        db.commit()
        db.refresh(db_index)
        return db_index

    @staticmethod
    def create_monitor_device(db: Session, device) -> 监测设备表:
        db_device = 监测设备表(
            type=device.type,
            deployment_area_id=device.deployment_area_id,
            install_time=device.install_time or datetime.now(),
            calibration_cycle=device.calibration_cycle,
            last_calibration_time=device.last_calibration_time,
            status=device.status,
            communication_protocol=device.communication_protocol,
            latitude=device.latitude,
            longitude=device.longitude,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        return db_device

    @staticmethod
    def get_monitor_device(db: Session, device_id: int) -> Optional[监测设备表]:
        return db.get(监测设备表, device_id)

    @staticmethod
    def list_monitor_devices_by_area(db: Session, area_id: int) -> List[监测设备表]:
        return db.scalars(select(监测设备表).where(监测设备表.deployment_area_id == area_id)).all()

    @staticmethod
    def list_all_monitor_devices(db: Session) -> List[监测设备表]:
        return db.scalars(select(监测设备表).order_by(监测设备表.id)).all()

    @staticmethod
    def update_device_status(db: Session, device_id: int, status_value: str) -> Optional[监测设备表]:
        db_device = db.get(监测设备表, device_id)
        if not db_device:
            return None
        db_device.status = status_value
        db_device.updated_at = datetime.now()
        db.commit()
        db.refresh(db_device)
        return db_device

    @staticmethod
    def get_devices_needing_calibration(db: Session) -> List[监测设备表]:
        now = datetime.now()
        
        # 获取所有设备，在Python中过滤需要校准的
        all_devices = db.scalars(
            select(监测设备表).where(监测设备表.status != "离线")
        ).all()
        
        result = []
        for device in all_devices:
            if device.last_calibration_time is None:
                result.append(device)
            else:
                days_since = (now - device.last_calibration_time).days
                if days_since >= (device.calibration_cycle or 30):
                    result.append(device)
        
        return result

    @staticmethod
    def create_environment_data(db: Session, data) -> 环境监测数据表:
        monitor_index = db.get(环境监测指标表, data.index_id)
        is_abnormal = 0
        abnormal_reason = None

        if monitor_index:
            if data.monitor_value > monitor_index.upper_threshold:
                is_abnormal = 1
                abnormal_reason = f"监测值{data.monitor_value}超过上限阈值{monitor_index.upper_threshold}"
            elif data.monitor_value < monitor_index.lower_threshold:
                is_abnormal = 1
                abnormal_reason = f"监测值{data.monitor_value}低于下限阈值{monitor_index.lower_threshold}"

        db_data = 环境监测数据表(
            data_id=data.data_id,
            index_id=data.index_id,
            device_id=data.device_id,
            collect_time=data.collect_time,
            monitor_value=data.monitor_value,
            area_id=data.area_id,
            data_quality=data.data_quality,
            is_abnormal=is_abnormal,
            abnormal_reason=abnormal_reason,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(db_data)
        db.commit()
        db.refresh(db_data)
        return db_data

    @staticmethod
    def get_environment_data(db: Session, data_id: str) -> Optional[环境监测数据表]:
        return db.get(环境监测数据表, data_id)

    @staticmethod
    def get_environment_data_by_device(
        db: Session,
        device_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[环境监测数据表]:
        query = select(环境监测数据表).where(环境监测数据表.device_id == device_id)
        if start_time:
            query = query.where(环境监测数据表.collect_time >= start_time)
        if end_time:
            query = query.where(环境监测数据表.collect_time <= end_time)
        return db.scalars(query.order_by(desc(环境监测数据表.collect_time))).all()

    @staticmethod
    def get_abnormal_data_by_area(
        db: Session,
        area_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[环境监测数据表]:
        query = select(环境监测数据表).where(
            and_(环境监测数据表.area_id == area_id, 环境监测数据表.is_abnormal == 1)
        )
        if start_time:
            query = query.where(环境监测数据表.collect_time >= start_time)
        if end_time:
            query = query.where(环境监测数据表.collect_time <= end_time)
        return db.scalars(query.order_by(desc(环境监测数据表.collect_time))).all()

    @staticmethod
    def update_data_audit_status(
        db: Session,
        data_id: str,
        audit_status: str,
        abnormal_reason: Optional[str] = None,
    ) -> Optional[环境监测数据表]:
        db_data = db.get(环境监测数据表, data_id)
        if not db_data:
            return None

        db_data.audit_status = audit_status
        if abnormal_reason is not None:
            db_data.abnormal_reason = abnormal_reason
        db_data.updated_at = datetime.now()

        db.commit()
        db.refresh(db_data)
        return db_data

    @staticmethod
    def create_calibration_record(db: Session, record) -> 设备校准记录表:
        db_record = 设备校准记录表(
            record_id=record.record_id,
            device_id=record.device_id,
            calibration_time=record.calibration_time,
            calibrator_id=record.calibrator_id,
            calibration_result=record.calibration_result,
            calibration_desc=record.calibration_desc,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        device = db.get(监测设备表, record.device_id)
        if device:
            device.last_calibration_time = record.calibration_time
            device.updated_at = datetime.now()

        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_calibration_records_by_device(db: Session, device_id: int) -> List[设备校准记录表]:
        return db.scalars(
            select(设备校准记录表).where(设备校准记录表.device_id == device_id).order_by(desc(设备校准记录表.calibration_time))
        ).all()

    @staticmethod
    def get_device_data_quality_rate(db: Session, days: int = 90) -> List[Dict[str, Any]]:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        q = (
            select(
                监测设备表.id.label("device_id"),
                监测设备表.type.label("device_type"),
                区域表.name.label("area_name"),
                func.count(环境监测数据表.data_id).label("total_data_count"),
                func.sum(case((环境监测数据表.data_quality.in_(["优", "良"]), 1), else_=0)).label("qualified_count"),
            )
            .select_from(监测设备表)
            .join(区域表, 监测设备表.deployment_area_id == 区域表.id)
            .join(
                环境监测数据表,
                and_(环境监测数据表.device_id == 监测设备表.id, 环境监测数据表.collect_time >= start_time),
                isouter=True,
            )
            .group_by(监测设备表.id, 监测设备表.type, 区域表.name)
        )

        rows = db.execute(q).mappings().all()
        result: List[Dict[str, Any]] = []
        for r in rows:
            total = int(r["total_data_count"] or 0)
            qualified = int(r["qualified_count"] or 0)
            rate = round((qualified * 100.0 / total), 2) if total else 0.0
            result.append({
                "device_id": r["device_id"],
                "device_type": r["device_type"],
                "area_name": r["area_name"],
                "total_data_count": total,
                "qualified_count": qualified,
                "qualified_rate": rate,
            })
        result.sort(key=lambda x: x["qualified_rate"], reverse=True)
        return result

    @staticmethod
    def get_overdue_calibration_devices_data(db: Session, days: int = 30) -> List[Dict[str, Any]]:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        q = (
            select(
                环境监测数据表.data_id,
                环境监测数据表.collect_time,
                环境监测数据表.index_id,
                环境监测指标表.index_name,
                环境监测数据表.monitor_value,
                监测设备表.id.label("device_id"),
                监测设备表.type.label("device_type"),
                监测设备表.calibration_cycle,
                监测设备表.last_calibration_time,
                环境监测数据表.data_quality,
            )
            .select_from(环境监测数据表)
            .join(监测设备表, 环境监测数据表.device_id == 监测设备表.id)
            .join(环境监测指标表, 环境监测数据表.index_id == 环境监测指标表.index_id)
            .where(环境监测数据表.collect_time >= start_time)
            .where(
                or_(
                    监测设备表.last_calibration_time.is_(None),
                    func.datediff("day", 监测设备表.last_calibration_time, datetime.now()) > 监测设备表.calibration_cycle,
                )
            )
            .order_by(监测设备表.id, desc(环境监测数据表.collect_time))
        )

        return [dict(r) for r in db.execute(q).mappings().all()]

    @staticmethod
    def query_core_protection_abnormal_data(db: Session, index_name: str, days: int = 30) -> List[Dict[str, Any]]:
        start_time = datetime.now() - timedelta(days=days)

        q = (
            select(
                环境监测数据表.data_id,
                环境监测数据表.collect_time,
                环境监测数据表.monitor_value,
                环境监测指标表.upper_threshold,
                环境监测指标表.lower_threshold,
                监测设备表.id.label("device_id"),
                监测设备表.type.label("device_type"),
                监测设备表.status.label("run_status"),
                区域表.name.label("area_name"),
                环境监测数据表.abnormal_reason,
            )
            .select_from(环境监测数据表)
            .join(环境监测指标表, 环境监测数据表.index_id == 环境监测指标表.index_id)
            .join(监测设备表, 环境监测数据表.device_id == 监测设备表.id)
            .join(区域表, 环境监测数据表.area_id == 区域表.id)
            .where(区域表.type == "核心保护区")
            .where(环境监测指标表.index_name == index_name)
            .where(环境监测数据表.is_abnormal == 1)
            .where(环境监测数据表.collect_time >= start_time)
            .order_by(desc(环境监测数据表.collect_time))
        )

        return [dict(r) for r in db.execute(q).mappings().all()]

    @staticmethod
    def get_data_statistics_by_area(db: Session, area_id: int, days: int = 30) -> Dict[str, Any]:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        stats = db.execute(
            select(
                func.count(环境监测数据表.data_id).label("total_count"),
                func.sum(case((环境监测数据表.is_abnormal == 1, 1), else_=0)).label("abnormal_count"),
                func.avg(环境监测数据表.monitor_value).label("avg_value"),
                func.min(环境监测数据表.monitor_value).label("min_value"),
                func.max(环境监测数据表.monitor_value).label("max_value"),
            ).where(
                and_(
                    环境监测数据表.area_id == area_id,
                    环境监测数据表.collect_time >= start_time,
                    环境监测数据表.collect_time <= end_time,
                )
            )
        ).mappings().first()

        total = int(stats["total_count"] or 0)
        abnormal = int(stats["abnormal_count"] or 0)

        return {
            "total_count": total,
            "abnormal_count": abnormal,
            "abnormal_rate": (abnormal / total * 100) if total else 0.0,
            "avg_value": float(stats["avg_value"] or 0),
            "min_value": float(stats["min_value"] or 0),
            "max_value": float(stats["max_value"] or 0),
        }

    @staticmethod
    def delete_monitor_index(db: Session, index_id: str) -> bool:
        db_index = db.get(环境监测指标表, index_id)
        if not db_index:
            return False
        db.delete(db_index)
        db.commit()
        return True

    @staticmethod
    def delete_monitor_device(db: Session, device_id: int) -> bool:
        db_device = db.get(监测设备表, device_id)
        if not db_device:
            return False
        db.delete(db_device)
        db.commit()
        return True

    @staticmethod
    def delete_environment_data(db: Session, data_id: str) -> bool:
        db_data = db.get(环境监测数据表, data_id)
        if not db_data:
            return False
        db.delete(db_data)
        db.commit()
        return True

    @staticmethod
    def delete_calibration_record(db: Session, record_id: str) -> bool:
        db_record = db.get(设备校准记录表, record_id)
        if not db_record:
            return False
        db.delete(db_record)
        db.commit()
        return True
