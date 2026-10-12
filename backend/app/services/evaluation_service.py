import json
from typing import Dict, Any, Set, Tuple
from app.models.schemas import EvaluationReport
from app.services.log_parser import LogParser
from app.services.architecture_detector import ArchitectureDetector

# Standard labeled benchmark dataset with ground truth topology
BENCHMARK_LOGS = """
{"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "method": "POST", "path": "/api/v1/orders", "status": 200, "duration_ms": 120, "caller": "192.168.1.10", "downstream": "order-service", "msg": "forwarding order"}
{"ts": "2026-10-12T10:00:01Z", "service": "api-gateway", "method": "GET", "path": "/api/v1/auth/verify", "status": 200, "duration_ms": 45, "caller": "192.168.1.10", "downstream": "auth-service", "msg": "validating jwt token"}
{"ts": "2026-10-12T10:00:02Z", "service": "order-service", "method": "POST", "path": "/orders", "status": 200, "duration_ms": 95, "caller": "api-gateway", "downstream": "payment-service", "datastore": "postgres", "msg": "created order in postgres"}
{"ts": "2026-10-12T10:00:03Z", "service": "order-service", "method": "GET", "path": "/orders/cache", "status": 200, "duration_ms": 12, "datastore": "redis", "msg": "checking redis session cache"}
{"ts": "2026-10-12T10:00:04Z", "service": "order-service", "method": "GET", "path": "/inventory/check", "status": 200, "duration_ms": 60, "downstream": "inventory-service", "msg": "checking stock"}
{"ts": "2026-10-12T10:00:05Z", "service": "payment-service", "method": "POST", "path": "/charge", "status": 200, "duration_ms": 150, "caller": "order-service", "downstream": "notification-worker", "msg": "dispatched receipt"}
{"ts": "2026-10-12T10:00:06Z", "service": "notification-worker", "method": "POST", "path": "/notify", "status": 200, "duration_ms": 30, "caller": "payment-service", "msg": "notification sent"}
{"ts": "2026-10-12T10:00:07Z", "service": "auth-service", "method": "POST", "path": "/verify", "status": 200, "duration_ms": 25, "caller": "api-gateway", "msg": "token verified"}
{"ts": "2026-10-12T10:00:08Z", "service": "inventory-service", "method": "GET", "path": "/items", "status": 200, "duration_ms": 35, "caller": "order-service", "msg": "inventory checked"}
{"ts": "2026-10-12T10:00:09Z", "service": "order-service", "level": "ERROR", "status": 504, "duration_ms": 3100, "caller": "api-gateway", "downstream": "payment-service", "msg": "gateway timeout calling payment-service"}
{"ts": "2026-10-12T10:00:10Z", "service": "order-service", "level": "WARN", "msg": "db pool near limit: postgres connection pool exhausted"}
""".strip()

GROUND_TRUTH_SERVICES = {
    "api-gateway",
    "auth-service",
    "order-service",
    "payment-service",
    "inventory-service",
    "notification-worker"
}

GROUND_TRUTH_EDGES = {
    ("api-gateway", "order-service"),
    ("api-gateway", "auth-service"),
    ("order-service", "payment-service"),
    ("order-service", "inventory-service"),
    ("payment-service", "notification-worker")
}

class EvaluationService:
    @classmethod
    def run_benchmark(cls, custom_logs: str = "") -> EvaluationReport:
        logs_to_use = custom_logs.strip() if custom_logs.strip() else BENCHMARK_LOGS
        events = LogParser.parse_text(logs_to_use)
        arch = ArchitectureDetector.detect(events, title="Benchmark Run")

        detected_services: Set[str] = {s.name for s in arch.services}
        detected_edges: Set[Tuple[str, str]] = {(e.source, e.target) for e in arch.topology}

        # Calculate Service Precision & Recall
        true_positive_services = len(detected_services & GROUND_TRUTH_SERVICES)
        precision_svc = true_positive_services / len(detected_services) if detected_services else 0.0
        recall_svc = true_positive_services / len(GROUND_TRUTH_SERVICES) if GROUND_TRUTH_SERVICES else 0.0

        # Calculate Edge Precision & Recall
        true_positive_edges = len(detected_edges & GROUND_TRUTH_EDGES)
        precision_edge = true_positive_edges / len(detected_edges) if detected_edges else 0.0
        recall_edge = true_positive_edges / len(GROUND_TRUTH_EDGES) if GROUND_TRUTH_EDGES else 0.0

        # Overall composite metrics
        avg_precision = round((precision_svc + precision_edge) / 2.0, 4)
        avg_recall = round((recall_svc + recall_edge) / 2.0, 4)
        if (avg_precision + avg_recall) > 0:
            f1 = round(2 * (avg_precision * avg_recall) / (avg_precision + avg_recall), 4)
        else:
            f1 = 0.0

        notes = (
            f"Evaluated on {len(events)} log lines. Service Precision: {precision_svc:.2f}, "
            f"Service Recall: {recall_svc:.2f}. Edge Precision: {precision_edge:.2f}, "
            f"Edge Recall: {recall_edge:.2f}."
        )

        return EvaluationReport(
            dataset_name="synthetic_microservice_baseline",
            total_log_lines=len(events),
            precision=avg_precision,
            recall=avg_recall,
            f1_score=f1,
            services_detected=len(detected_services),
            expected_services=len(GROUND_TRUTH_SERVICES),
            edges_detected=len(detected_edges),
            expected_edges=len(GROUND_TRUTH_EDGES),
            failure_patterns_detected=len(arch.failure_patterns),
            notes=notes
        )
