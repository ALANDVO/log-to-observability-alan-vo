import json
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_role
from app.models.schemas import (
    GrafanaDashboard,
    AlertGroup,
    SloDefinition,
    MetricMapping,
    AuditLogItem,
    UserPrincipal
)
from app.models.entities import ArchitectureEntity, DashboardEntity, AlertRuleEntity, SloEntity, AuditLogEntity
from app.services.log_parser import LogParser
from app.services.architecture_detector import ArchitectureDetector
from app.services.dashboard_generator import DashboardGenerator
from app.services.alert_generator import AlertGenerator
from app.services.slo_engine import SloEngine
from app.services.metric_mapper import MetricMapper

router = APIRouter(prefix="/api/observability", tags=["observability"])

class GenerateDashboardRequest(BaseModel):
    architecture_id: Optional[int] = None
    logs: Optional[str] = None
    title: Optional[str] = "Observability Dashboard"

class GenerateAlertsRequest(BaseModel):
    architecture_id: Optional[int] = None
    logs: Optional[str] = None

class CalculateSloRequest(BaseModel):
    service: str
    target_percentage: float = 99.9
    latency_threshold_ms: float = 250.0

@router.post("/dashboards/generate", response_model=GrafanaDashboard)
def generate_dashboard(
    payload: GenerateDashboardRequest,
    db: Session = Depends(get_db),
    user: UserPrincipal = Depends(require_role("operator"))
):
    arch = None
    if payload.architecture_id:
        r = db.query(ArchitectureEntity).filter(ArchitectureEntity.id == payload.architecture_id).first()
        if not r:
            raise HTTPException(status_code=404, detail=f"Architecture #{payload.architecture_id} not found")
        arch = ArchitectureDetector.detect(LogParser.parse_text(""), title=r.title)
        arch.services = [type('Node', (), s) for s in json.loads(r.services_json)]  # type: ignore
        arch.datastores = [type('DS', (), d) for d in json.loads(r.datastores_json)]  # type: ignore
    elif payload.logs:
        events = LogParser.parse_text(payload.logs)
        arch = ArchitectureDetector.detect(events, title=payload.title or "Observability Dashboard")
    else:
        raise HTTPException(status_code=400, detail="Provide either architecture_id or logs content")

    dash = DashboardGenerator.generate(arch, title=payload.title or "Observability Dashboard")

    # Persist dashboard
    d_entity = DashboardEntity(
        uid=dash.uid,
        title=dash.title,
        architecture_id=payload.architecture_id,
        dashboard_json=json.dumps(dash.raw_json)
    )
    db.add(d_entity)
    db.commit()

    return dash

@router.post("/alerts/generate", response_model=AlertGroup)
def generate_alerts(
    payload: GenerateAlertsRequest,
    db: Session = Depends(get_db),
    user: UserPrincipal = Depends(require_role("operator"))
):
    if payload.architecture_id:
        r = db.query(ArchitectureEntity).filter(ArchitectureEntity.id == payload.architecture_id).first()
        if not r:
            raise HTTPException(status_code=404, detail=f"Architecture #{payload.architecture_id} not found")
        events = []
    elif payload.logs:
        events = LogParser.parse_text(payload.logs)
    else:
        raise HTTPException(status_code=400, detail="Provide either architecture_id or logs content")

    arch = ArchitectureDetector.detect(events)
    if payload.architecture_id and r:
        from app.models.schemas import ServiceNode, DatastoreNode
        arch.services = [ServiceNode(**s) for s in json.loads(r.services_json)]
        arch.datastores = [DatastoreNode(**d) for d in json.loads(r.datastores_json)]

    alert_group = AlertGenerator.generate_alerts(arch)

    # Persist alert group
    a_entity = AlertRuleEntity(
        architecture_id=payload.architecture_id,
        service="all",
        rules_json=json.dumps([r.model_dump() for r in alert_group.rules])
    )
    db.add(a_entity)
    db.commit()

    return alert_group

@router.post("/slo/calculate", response_model=SloDefinition)
def calculate_slo(
    payload: CalculateSloRequest,
    db: Session = Depends(get_db),
    user: UserPrincipal = Depends(require_role("operator"))
):
    slo = SloEngine.calculate_slo(
        service=payload.service,
        target_percentage=payload.target_percentage,
        latency_threshold_ms=payload.latency_threshold_ms
    )

    s_entity = SloEntity(
        service=payload.service,
        target_percentage=str(payload.target_percentage),
        definition_json=slo.model_dump_json()
    )
    db.add(s_entity)
    db.commit()

    return slo

@router.get("/metrics/mapping", response_model=List[MetricMapping])
def get_metric_mappings(
    user: UserPrincipal = Depends(require_role("viewer"))
):
    empty_arch = ArchitectureDetector.detect([])
    return MetricMapper.map_architecture_to_metrics(empty_arch)

@router.get("/audit-logs", response_model=List[AuditLogItem])
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: UserPrincipal = Depends(require_role("admin"))
):
    rows = db.query(AuditLogEntity).order_by(AuditLogEntity.created_at.desc()).limit(limit).all()
    return [
        AuditLogItem(
            id=r.id,
            created_at=r.created_at,
            actor=r.actor,
            action=r.action,
            target=r.target,
            details=json.loads(r.details_json)
        )
        for r in rows
    ]
