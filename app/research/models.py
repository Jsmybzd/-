
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, Unicode
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ResearchProjects(Base):
    __tablename__ = "ResearchProjects"

    project_id = Column(String(50), primary_key=True)
    project_name = Column(Unicode(200), nullable=False)
    leader_id = Column(String(50), nullable=False)
    apply_unit = Column(Unicode(100), nullable=False)
    approval_date = Column(Date, nullable=False)
    conclusion_date = Column(Date)
    status = Column(Unicode(20), nullable=False)
    research_field = Column(Unicode(50), nullable=False)

    collections = relationship("DataCollections", back_populates="project")
    achievements = relationship("ResearchAchievements", back_populates="project")


class DataCollections(Base):
    __tablename__ = "DataCollections"

    collection_id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("ResearchProjects.project_id"), nullable=False)
    collector_id = Column(String(50), nullable=False)
    collection_time = Column(DateTime, nullable=False)
    area_id = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    data_source = Column(Unicode(20), nullable=False)
    remarks = Column(Text)

    project = relationship("ResearchProjects", back_populates="collections")


class ResearchAchievements(Base):
    __tablename__ = "ResearchAchievements"

    achievement_id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("ResearchProjects.project_id"), nullable=False)
    achievement_type = Column(Unicode(20), nullable=False)
    title = Column(Unicode(200), nullable=False)
    publish_date = Column(Date, nullable=False)
    share_permission = Column(Unicode(20), nullable=False)
    file_path = Column(String(255), nullable=False)

    project = relationship("ResearchProjects", back_populates="achievements")
    authorizations = relationship("AuthorizedAccesses", back_populates="achievement")


class AuthorizedAccesses(Base):
    __tablename__ = "AuthorizedAccesses"

    access_id = Column(Integer, primary_key=True, autoincrement=True)
    achievement_id = Column(String(50), ForeignKey("ResearchAchievements.achievement_id"), nullable=False)
    user_id = Column(String(50), nullable=False)
    authorize_time = Column(DateTime, server_default=func.now(), nullable=False)

    achievement = relationship("ResearchAchievements", back_populates="authorizations")
