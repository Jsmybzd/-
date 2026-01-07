from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.db import Base


class 物种表(Base):
    __tablename__ = "物种表"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chinese_name = Column(String(100), nullable=False)
    latin_name = Column(String(100))

    kingdom = Column(String(50))
    phylum = Column(String(50))
    class_name = Column(String(50))
    order = Column(String(50))
    family = Column(String(50))
    genus = Column(String(50))
    species = Column(String(50))

    protect_level = Column(String(20), default="无")
    live_habit = Column(Text)
    distribution_range = Column(Text)


class 物种监测记录表(Base):
    __tablename__ = "物种监测记录表"

    __mapper_args__ = {"eager_defaults": False}
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    species_id = Column(Integer, ForeignKey("物种表.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("监测设备表.id"))

    time = Column(DateTime, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)

    monitoring_method = Column(Enum("红外相机", "人工巡查", "无人机"), nullable=False)
    image_path = Column(String(500))
    count = Column(Integer)
    behavior = Column(Text)

    state = Column(Enum("有效", "待核实"), default="待核实")
    recorder_id = Column(Integer, ForeignKey("用户.id"), nullable=False)

    analysis_conclusion = Column(Text)
    analyst_id = Column(Integer, ForeignKey("用户.id"))
    analysis_time = Column(DateTime)
    confidence_level = Column(String(20))

    analyst = relationship("User", foreign_keys=[analyst_id], backref="analyzed_records")


class 区域物种关联表(Base):
    __tablename__ = "区域物种关联表"

    id = Column(Integer, primary_key=True, autoincrement=True)
    area_id = Column(Integer, ForeignKey("区域表.id"), nullable=False)
    species_id = Column(Integer, ForeignKey("物种表.id"), nullable=False)
    is_main = Column(Integer, default=0)
