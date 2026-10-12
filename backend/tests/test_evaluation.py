import pytest
from app.services.evaluation_service import EvaluationService

def test_ai_ml_evaluation_benchmark_metrics():
    report = EvaluationService.run_benchmark()

    assert report.dataset_name == "synthetic_microservice_baseline"
    assert report.total_log_lines > 0
    assert report.precision > 0.0
    assert report.recall > 0.0
    assert report.f1_score > 0.0
    assert report.services_detected >= 5
    assert report.edges_detected >= 3
    assert len(report.notes) > 0
