from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from app.core.auth import require_role
from app.models.schemas import EvaluationReport, UserPrincipal
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

class RunEvaluationRequest(BaseModel):
    custom_logs: Optional[str] = None

@router.get("/benchmark", response_model=EvaluationReport)
def get_benchmark_report(
    user: UserPrincipal = Depends(require_role("viewer"))
):
    return EvaluationService.run_benchmark()

@router.post("/run", response_model=EvaluationReport)
def run_evaluation(
    payload: RunEvaluationRequest,
    user: UserPrincipal = Depends(require_role("operator"))
):
    return EvaluationService.run_benchmark(custom_logs=payload.custom_logs or "")
