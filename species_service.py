from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from .models import 物种表, 区域物种关联表


class SpeciesService:
    @staticmethod
    def create_species(db: Session, species_data) -> 物种表:
        existing = db.execute(
            select(物种表).where(物种表.chinese_name == species_data.chinese_name)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="物种名称已存在",
            )

        db_species = 物种表(
            chinese_name=species_data.chinese_name,
            latin_name=species_data.latin_name,
            kingdom=species_data.kingdom,
            phylum=species_data.phylum,
            class_name=species_data.class_name,
            order=species_data.order,
            family=species_data.family,
            genus=species_data.genus,
            species=species_data.species,
            protect_level=(
                species_data.protect_level.value
                if hasattr(species_data.protect_level, "value")
                else species_data.protect_level
            ),
            live_habit=species_data.live_habit,
            distribution_range=species_data.distribution_range,
        )

        db.add(db_species)
        db.commit()
        db.refresh(db_species)
        return db_species

    @staticmethod
    def get_species(db: Session, species_id: int) -> Optional[物种表]:
        return db.get(物种表, species_id)

    @staticmethod
    def list_species(db: Session, query_params) -> Dict[str, Any]:
        conditions = []

        if query_params.chinese_name:
            conditions.append(物种表.chinese_name.like(f"%{query_params.chinese_name}%"))
        if query_params.latin_name:
            conditions.append(物种表.latin_name.like(f"%{query_params.latin_name}%"))
        if query_params.protect_level:
            level = (
                query_params.protect_level.value
                if hasattr(query_params.protect_level, "value")
                else query_params.protect_level
            )
            conditions.append(物种表.protect_level == level)

        base_query = select(物种表)
        if conditions:
            base_query = base_query.where(and_(*conditions))

        total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

        offset = (query_params.page - 1) * query_params.page_size
        species_list = (
            db.scalars(base_query.order_by(desc(物种表.id)).offset(offset).limit(query_params.page_size))
            .all()
        )

        return {
            "total": total,
            "species": species_list,
            "page": query_params.page,
            "page_size": query_params.page_size,
        }

    @staticmethod
    def update_species(db: Session, species_id: int, update_data) -> 物种表:
        species = db.get(物种表, species_id)
        if not species:
            raise HTTPException(status_code=404, detail="物种不存在")

        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is None:
                continue
            if field == "protect_level" and hasattr(value, "value"):
                value = value.value
            setattr(species, field, value)

        db.commit()
        db.refresh(species)
        return species

    @staticmethod
    def delete_species(db: Session, species_id: int) -> None:
        species = db.get(物种表, species_id)
        if not species:
            raise HTTPException(status_code=404, detail="物种不存在")

        from .models import 物种监测记录表

        has_records = db.scalar(
            select(func.count()).select_from(物种监测记录表).where(物种监测记录表.species_id == species_id)
        )
        if (has_records or 0) > 0:
            raise HTTPException(status_code=400, detail="该物种存在监测记录，无法删除")

        has_associations = db.scalar(
            select(func.count()).select_from(区域物种关联表).where(区域物种关联表.species_id == species_id)
        )
        if (has_associations or 0) > 0:
            raise HTTPException(status_code=400, detail="该物种关联到区域，无法删除")

        db.delete(species)
        db.commit()

    @staticmethod
    def get_protected_species_stats(db: Session) -> Dict[str, int]:
        stats: Dict[str, int] = {}
        for level in ["国家一级", "国家二级", "无"]:
            count = db.scalar(select(func.count()).select_from(物种表).where(物种表.protect_level == level)) or 0
            stats[level] = count

        total = db.scalar(select(func.count()).select_from(物种表)) or 0
        stats["总物种数"] = total
        stats["受保护物种"] = total - stats.get("无", 0)
        return stats

    @staticmethod
    def get_species_taxonomy_stats(db: Session) -> Dict[str, Dict[str, int]]:
        stats: Dict[str, Dict[str, int]] = {
            "by_class": {},
            "by_order": {},
            "by_family": {},
        }

        class_results = db.execute(
            select(物种表.class_name, func.count().label("count"))
            .where(物种表.class_name.isnot(None))
            .group_by(物种表.class_name)
        ).all()
        for class_name, count in class_results:
            if class_name:
                stats["by_class"][class_name] = int(count)

        order_results = db.execute(
            select(物种表.order, func.count().label("count"))
            .where(物种表.order.isnot(None))
            .group_by(物种表.order)
        ).all()
        for order_name, count in order_results:
            if order_name:
                stats["by_order"][order_name] = int(count)

        family_results = db.execute(
            select(物种表.family, func.count().label("count"))
            .where(物种表.family.isnot(None))
            .group_by(物种表.family)
        ).all()
        for family_name, count in family_results:
            if family_name:
                stats["by_family"][family_name] = int(count)

        return stats
