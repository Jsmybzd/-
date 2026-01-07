from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.shared.models import 区域表

from .models import 物种表, 物种监测记录表


class AnalysisReportService:
    @staticmethod
    def add_analysis_conclusion(
        db: Session,
        record_id: int,
        conclusion: str,
        analyst_id: int,
        confidence_level: str = "中",
    ) -> Dict[str, Any]:
        record = db.get(物种监测记录表, record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="监测记录不存在")

        if record.state != "有效":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能为有效数据添加分析结论")

        if confidence_level not in ["高", "中", "低"]:
            confidence_level = "中"

        record.analysis_conclusion = conclusion
        record.analyst_id = analyst_id
        record.analysis_time = datetime.now()
        record.confidence_level = confidence_level

        db.commit()
        db.refresh(record)

        return {
            "record_id": record_id,
            "conclusion": conclusion,
            "analyst_id": analyst_id,
            "analysis_time": record.analysis_time,
            "confidence_level": confidence_level,
        }

    @staticmethod
    def get_records_without_conclusion(db: Session, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        base_query = select(物种监测记录表).where(
            and_(物种监测记录表.state == "有效", 物种监测记录表.analysis_conclusion.is_(None))
        )

        total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
        offset = (page - 1) * page_size
        records = (
            db.scalars(base_query.order_by(desc(物种监测记录表.time)).offset(offset).limit(page_size)).all()
        )

        return {"total": total, "records": records, "page": page, "page_size": page_size}

    @staticmethod
    def get_analyst_work_stats(
        db: Session,
        analyst_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        conditions = [物种监测记录表.analyst_id == analyst_id]
        if start_date:
            conditions.append(物种监测记录表.analysis_time >= start_date)
        if end_date:
            conditions.append(物种监测记录表.analysis_time <= end_date)

        total_analyzed = db.scalar(select(func.count()).where(and_(*conditions))) or 0

        confidence_stats: Dict[str, int] = {}
        for level in ["高", "中", "低"]:
            cnt = (
                db.scalar(select(func.count()).where(and_(*conditions, 物种监测记录表.confidence_level == level)))
                or 0
            )
            confidence_stats[level] = cnt

        return {
            "analyst_id": analyst_id,
            "total_analyzed": total_analyzed,
            "confidence_stats": confidence_stats,
        }

    @staticmethod
    def generate_area_monitoring_report(db: Session, area_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        area = db.get(区域表, area_id)
        if not area:
            raise HTTPException(status_code=404, detail="区域不存在")

        species_ids = db.execute(
            select(func.distinct(物种表.id))
            .select_from(物种表)
            .join_from(物种表, 物种监测记录表, 物种监测记录表.species_id == 物种表.id, isouter=True)
        )

        _ = species_ids  # keep placeholder for future extensions

        total_records = (
            db.scalar(
                select(func.count())
                .select_from(物种监测记录表)
                .where(
                    and_(
                        物种监测记录表.time >= start_date,
                        物种监测记录表.time <= end_date,
                    )
                )
            )
            or 0
        )

        return {
            "area": {"id": area.id, "name": area.name, "type": area.type},
            "time_range": {"start": start_date, "end": end_date},
            "total_records": total_records,
        }
