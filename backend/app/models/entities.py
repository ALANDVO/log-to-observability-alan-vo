import json
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class ArchitectureEntity(Base):
    __tablename__ = "architecture_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, default="Architecture Run")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    log_count = Column(Integer, default=0, nullable=False)
    services_json = Column(Text, nullable=False, default="[]")
    topology_json = Column(Text, nullable=False, default="[]")
    datastores_json = Column(Text, nullable=False, default="[]")
    failures_json = Column(Text, nullable=False, default="[]")
    llm_advisory = Column(Text, nullable=True)
    is_llm_assisted = Column(Boolean, default=False, nullable=False)

    dashboards = relationship("DashboardEntity", back_populates="architecture", cascade="all, delete-orphan")
    alert_rules = relationship("AlertRuleEntity", back_populates="architecture", cascade="all, delete-orphan")
    slos = relationship("SloEntity", back_populates="architecture", cascade="all, delete-orphan")

class DashboardEntity(Base):
    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uid = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    architecture_id = Column(Integer, ForeignKey("architecture_runs.id"), nullable=True)
    dashboard_json = Column(Text, nullable=False)

    architecture = relationship("ArchitectureEntity", back_populates="dashboards")

class AlertRuleEntity(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    architecture_id = Column(Integer, ForeignKey("architecture_runs.id"), nullable=True)
    service = Column(String(128), nullable=False)
    rules_json = Column(Text, nullable=False)

    architecture = relationship("ArchitectureEntity", back_populates="alert_rules")

class SloEntity(Base):
    __tablename__ = "slo_definitions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    architecture_id = Column(Integer, ForeignKey("architecture_runs.id"), nullable=True)
    service = Column(String(128), nullable=False)
    target_percentage = Column(String(32), default="99.9", nullable=False)
    definition_json = Column(Text, nullable=False)

    architecture = relationship("ArchitectureEntity", back_populates="slos")

class AuditLogEntity(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    actor = Column(String(128), nullable=False)
    action = Column(String(64), nullable=False)
    target = Column(String(255), nullable=False)
    details_json = Column(Text, default="{}", nullable=False)
