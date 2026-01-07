from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mssql import BIT
from sqlalchemy.orm import relationship

from app.db import Base


class 环境监测指标表(Base):
    __tablename__ = "环境监测指标表"

    index_id = Column(String(20), primary_key=True, comment="指标编号")
    index_name = Column(String(50), nullable=False, comment="指标名称")
    unit = Column(String(20), nullable=False, comment="计量单位")
    upper_threshold = Column(Float, nullable=False, comment="标准阈值上限")
    lower_threshold = Column(Float, nullable=False, comment="标准阈值下限")
    monitor_frequency = Column(String(10), nullable=False, comment="监测频率（小时/日/周）")
    created_at = Column(DateTime, comment="创建时间")
    updated_at = Column(DateTime, comment="更新时间")

    environment_data = relationship("环境监测数据表", back_populates="monitor_index")


class 环境监测数据表(Base):
    __tablename__ = "环境监测数据表"

    data_id = Column(String(30), primary_key=True, comment="数据编号")
    index_id = Column(String(20), ForeignKey("环境监测指标表.index_id"), nullable=False, comment="指标编号")
    device_id = Column(Integer, ForeignKey("监测设备表.id"), nullable=False, comment="监测设备编号")
    collect_time = Column(DateTime, nullable=False, comment="采集时间")
    monitor_value = Column(Float, nullable=False, comment="监测值")
    area_id = Column(Integer, ForeignKey("区域表.id"), nullable=False, comment="区域编号")
    data_quality = Column(String(10), nullable=False, comment="数据质量（优/良/中/差）")
    is_abnormal = Column(BIT, default=0, comment="是否异常（0-正常，1-异常）")
    abnormal_reason = Column(String(100), comment="异常原因")
    audit_status = Column(String(10), default="未审核", comment="审核状态（未审核/已审核/待核实）")
    created_at = Column(DateTime, comment="创建时间")
    updated_at = Column(DateTime, comment="更新时间")

    monitor_index = relationship("环境监测指标表", back_populates="environment_data")
    monitor_device = relationship("监测设备表")
    area = relationship("区域表")


class 设备校准记录表(Base):
    __tablename__ = "设备校准记录表"

    record_id = Column(String(30), primary_key=True, comment="校准记录编号")
    device_id = Column(Integer, ForeignKey("监测设备表.id"), nullable=False, comment="设备编号")
    calibration_time = Column(DateTime, nullable=False, comment="校准时间")
    calibrator_id = Column(Integer, ForeignKey("用户.id"), nullable=False, comment="校准人员ID")
    calibration_result = Column(String(10), nullable=False, comment="校准结果（合格/不合格）")
    calibration_desc = Column(Text, comment="校准说明")
    created_at = Column(DateTime, comment="创建时间")
    updated_at = Column(DateTime, comment="更新时间")

    monitor_device = relationship("监测设备表")
