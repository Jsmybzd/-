# dao/biodiversity_queries.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, desc, select, text
from sqlalchemy.orm import Session

from . import models


class BiodiversityQueries:
    # ======================
    # 物种表 (物种表)
    # ======================

    @staticmethod
    def get_species_by_id(db: Session, species_id: int) -> Optional[models.物种表]:
        return db.get(models.物种表, species_id)

    @staticmethod
    def get_species_by_chinese_name(db: Session, name: str) -> List[models.物种表]:
        return db.scalars(
            select(models.物种表).where(models.物种表.chinese_name == name)
        ).all()

    @staticmethod
    def list_species(
        db: Session,
        protect_level: Optional[str] = None,
        kingdom: Optional[str] = None,
        class_name: Optional[str] = None,
    ) -> List[models.物种表]:
        q = select(models.物种表)
        if protect_level:
            q = q.where(models.物种表.protect_level == protect_level)
        if kingdom:
            q = q.where(models.物种表.kingdom == kingdom)
        if class_name:
            q = q.where(models.物种表.class_name == class_name)
        return db.scalars(q.order_by(models.物种表.id)).all()

    @staticmethod
    def create_species(db: Session, payload) -> models.物种表:
        species = models.物种表(
            chinese_name=payload.chinese_name,
            latin_name=payload.latin_name,
            kingdom=payload.kingdom,
            phylum=payload.phylum,
            class_name=payload.class_name,
            order=payload.order,
            family=payload.family,
            genus=payload.genus,
            species=payload.species,
            protect_level=getattr(payload, "protect_level", "无"),
            live_habit=getattr(payload, "live_habit", None),
            distribution_range=getattr(payload, "distribution_range", None),
        )
        db.add(species)
        db.commit()
        db.refresh(species)
        return species

    @staticmethod
    def update_species(db: Session, species_id: int, update_data: dict) -> Optional[models.物种表]:
        species = db.get(models.物种表, species_id)
        if not species:
            return None
        for k, v in update_data.items():
            if hasattr(species, k) and v is not None:
                setattr(species, k, v)
        db.commit()
        db.refresh(species)
        return species

    # ======================
    # 物种监测记录表 (物种监测记录表)
    # ======================

    @staticmethod
    def get_monitoring_record(db: Session, record_id: int) -> Optional[models.物种监测记录表]:
        return db.get(models.物种监测记录表, record_id)

    @staticmethod
    def list_monitoring_records(
        db: Session,
        species_id: Optional[int] = None,
        recorder_id: Optional[int] = None,
        state: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        monitoring_method: Optional[str] = None,
    ) -> List[models.物种监测记录表]:
        q = select(models.物种监测记录表)
        if species_id is not None:
            q = q.where(models.物种监测记录表.species_id == species_id)
        if recorder_id is not None:
            q = q.where(models.物种监测记录表.recorder_id == recorder_id)
        if state:
            q = q.where(models.物种监测记录表.state == state)
        if monitoring_method:
            q = q.where(models.物种监测记录表.monitoring_method == monitoring_method)
        if start_time:
            q = q.where(models.物种监测记录表.time >= start_time)
        if end_time:
            q = q.where(models.物种监测记录表.time <= end_time)
        return db.scalars(q.order_by(desc(models.物种监测记录表.time))).all()

    @staticmethod
    def create_monitoring_record(db: Session, payload) -> models.物种监测记录表:
        # 校验物种存在
        if not db.get(models.物种表, payload.species_id):
            raise ValueError("物种不存在")
        # 校验用户（记录人）存在
        if not db.get(models.用户, payload.recorder_id):
            raise ValueError("记录人不存在")
        # 设备可为空
        device_id = getattr(payload, "device_id", None)
        if device_id and not db.get(models.监测设备表, device_id):
            raise ValueError("监测设备不存在")

        record = models.物种监测记录表(
            species_id=payload.species_id,
            device_id=device_id,
            time=getattr(payload, "time", datetime.now()),
            latitude=getattr(payload, "latitude", None),
            longitude=getattr(payload, "longitude", None),
            monitoring_method=payload.monitoring_method,  # 必填：'红外相机'/'人工巡查'/'无人机'
            image_path=getattr(payload, "image_path", None),
            count=getattr(payload, "count", None),
            behavior=getattr(payload, "behavior", None),
            state=getattr(payload, "state", "待核实"),
            recorder_id=payload.recorder_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def update_monitoring_record(db: Session, record_id: int, update_data: dict) -> Optional[models.物种监测记录表]:
        record = db.get(models.物种监测记录表, record_id)
        if not record:
            return None

        # 校验外键变更
        if "species_id" in update_data and update_data["species_id"]:
            if not db.get(models.物种表, update_data["species_id"]):
                raise ValueError("物种不存在")
        if "recorder_id" in update_data and update_data["recorder_id"]:
            if not db.get(models.用户, update_data["recorder_id"]):
                raise ValueError("记录人不存在")
        if "device_id" in update_data and update_data["device_id"]:
            if not db.get(models.监测设备表, update_data["device_id"]):
                raise ValueError("监测设备不存在")

        for field in [
            "species_id", "device_id", "time", "latitude", "longitude",
            "monitoring_method", "image_path", "count", "behavior", "state", "recorder_id"
        ]:
            if field in update_data and update_data[field] is not None:
                setattr(record, field, update_data[field])

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_monitoring_record(db: Session, record_id: int) -> bool:
        record = db.get(models.物种监测记录表, record_id)
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True

    # ======================
    # 区域物种关联 & 栖息地（按需扩展）
    # ======================

    @staticmethod
    def get_species_in_area(db: Session, area_id: int) -> List[models.区域物种关联表]:
        return db.scalars(
            select(models.区域物种关联表).where(models.区域物种关联表.area_id == area_id)
        ).all()

    @staticmethod
    def get_habitats_by_eco_type(db: Session, eco_type: str) -> List[models.栖息地信息表]:
        return db.scalars(
            select(models.栖息地信息表).where(models.栖息地信息表.eco_type == eco_type)
        ).all()

    # ======================
    # 统计分析（示例）
    # ======================

    @staticmethod
    def count_species_by_protect_level(db: Session) -> List[tuple]:
        """返回各保护级别物种数量"""
        stmt = text("""
            SELECT protect_level, COUNT(*) as count
            FROM 物种表
            GROUP BY protect_level
        """)
        return db.execute(stmt).fetchall()

    @staticmethod
    def count_valid_records_last_30_days(db: Session) -> int:
        """过去30天有效监测记录数"""
        thirty_days_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)
        return db.scalar(
            select(func.count()).select_from(models.物种监测记录表)
            .where(and_(
                models.物种监测记录表.state == "有效",
                models.物种监测记录表.time >= thirty_days_ago
            ))
        ) or 0