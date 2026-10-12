import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.schemas import (
    ArchitectureResult,
    AnalyzeLogRequest,
    UserPrincipal
)
from app.models.entities import ArchitectureEntity, AuditLogEntity
from app.services.log_parser import LogParser
from app.services.architecture_detector import ArchitectureDetector
from app.services.llm_advisor import LLMAdvisor

router = APIRouter(prefix="/api/architecture", tags=["architecture"])

@router.post("/analyze", response_model=ArchitectureResult)
async def analyze_logs(
    payload: AnalyzeLogRequest,
    db: Session = Depends(get_db),
    user: UserPrincipal = Depends(require_role("operator"))
):
    if not payload.logs.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Log content cannot be empty.")

    events = LogParser.parse_text(payload.logs)
    if not events:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not parse any log events from input.")

    arch = ArchitectureDetector.detect(events, title=payload.title or "Architecture Analysis")

    llm_advisory_text = None
    if payload.enable_llm_advisory:
        advisor = LLMAdvisor()
        prompt = (
            f"Analyzed {len(events)} logs. Detected {len(arch.services)} services: "
            f"{[s.name for s in arch.services]}, datastores: {[d.name for d in arch.datastores]}, "
            f"failure patterns: {[f.summary for f in arch.failure_patterns]}. "
            f"Provide SRE architectural assessment and risk factors."
        )
        llm_advisory_text = await advisor.generate_advisory(prompt)
        arch.llm_advisory = llm_advisory_text
        arch.is_llm_assisted = True

    # Persist in SQLite
    entity = ArchitectureEntity(
        title=arch.title,
        log_count=arch.log_count,
        services_json=json.dumps([s.model_dump() for s in arch.services]),
        topology_json=json.dumps([t.model_dump() for t in arch.topology]),
        datastores_json=json.dumps([d.model_dump() for d in arch.datastores]),
        failures_json=json.dumps([f.model_dump() for f in arch.failure_patterns]),
        llm_advisory=llm_advisory_text,
        is_llm_assisted=arch.is_llm_assisted
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    arch.id = entity.id

    # Audit log
    audit = AuditLogEntity(
        actor=user.username,
        action="ANALYZE_LOGS",
        target=f"architecture_run_{entity.id}",
        details_json=json.dumps({"services": len(arch.services), "logs": len(events)})
    )
    db.add(audit)
    db.commit()

    return arch

@router.get("/runs", response_model=List[ArchitectureResult])
def list_runs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: UserPrincipal = Depends(require_role("viewer"))
):
    rows = db.query(ArchitectureEntity).order_by(ArchitectureEntity.created_at.desc()).offset(offset).limit(limit).all()
    results = []
    for r in rows:
        results.append(ArchitectureResult(
            id=r.id,
            created_at=r.created_at,
            title=r.title,
            log_count=r.log_count,
            services=json.loads(r.services_json),
            topology=json.loads(r.topology_json),
            datastores=json.loads(r.datastores_json),
            failure_patterns=json.loads(r.failures_json),
            llm_advisory=r.llm_advisory,
            is_llm_assisted=r.is_llm_assisted
        ))
    return results

@router.get("/runs/{run_id}", response_model=ArchitectureResult)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    user: UserPrincipal = Depends(require_role("viewer"))
):
    r = db.query(ArchitectureEntity).filter(ArchitectureEntity.id == run_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run #{run_id} not found")
    return ArchitectureResult(
        id=r.id,
        created_at=r.created_at,
        title=r.title,
        log_count=r.log_count,
        services=json.loads(r.services_json),
        topology=json.loads(r.topology_json),
        datastores=json.loads(r.datastores_json),
        failure_patterns=json.loads(r.failures_json),
        llm_advisory=r.llm_advisory,
        is_llm_assisted=r.is_llm_assisted
    )

@router.delete("/runs/{run_id}")
def delete_run(
    run_id: int,
    db: Session = Depends(get_db),
    user: UserPrincipal = Depends(require_role("admin"))
):
    r = db.query(ArchitectureEntity).filter(ArchitectureEntity.id == run_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run #{run_id} not found")
    db.delete(r)
    # Record audit log
    audit = AuditLogEntity(
        actor=user.username,
        action="DELETE_RUN",
        target=f"architecture_run_{run_id}",
        details_json=json.dumps({"deleted_id": run_id})
    )
    db.add(audit)
    db.commit()
    return {"status": "deleted", "id": run_id}
