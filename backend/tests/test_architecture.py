import pytest
from app.services.log_parser import LogParser
from app.services.architecture_detector import ArchitectureDetector

def test_detect_topology_and_roles():
    raw_logs = """
    {"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "method": "GET", "path": "/api/v1/orders", "status": 200, "duration_ms": 35, "caller": "10.0.0.1", "downstream": "order-service"}
    {"ts": "2026-10-12T10:00:01Z", "service": "order-service", "method": "POST", "path": "/orders", "status": 200, "duration_ms": 90, "caller": "api-gateway", "downstream": "payment-service", "datastore": "postgres"}
    {"ts": "2026-10-12T10:00:02Z", "service": "payment-service", "method": "POST", "path": "/charge", "status": 200, "duration_ms": 110, "caller": "order-service", "datastore": "redis"}
    {"ts": "2026-10-12T10:00:03Z", "service": "notification-worker", "msg": "processed email event from kafka"}
    """
    events = LogParser.parse_text(raw_logs)
    arch = ArchitectureDetector.detect(events)

    service_names = {s.name for s in arch.services}
    assert "api-gateway" in service_names
    assert "order-service" in service_names
    assert "payment-service" in service_names
    assert "notification-worker" in service_names

    gw = next(s for s in arch.services if s.name == "api-gateway")
    assert gw.role == "gateway"
    assert gw.user_facing is True

    worker = next(s for s in arch.services if s.name == "notification-worker")
    assert worker.role == "worker"

    # Verify topology edges
    edges = {(e.source, e.target) for e in arch.topology}
    assert ("api-gateway", "order-service") in edges
    assert ("order-service", "payment-service") in edges

    # Verify datastores
    ds_names = {d.name for d in arch.datastores}
    assert "postgresql" in ds_names or "postgres" in ds_names
    assert "redis" in ds_names

def test_detect_failure_patterns_with_evidence():
    raw_logs = """
    {"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "level": "ERROR", "status": 504, "msg": "gateway timeout waiting for response"}
    {"ts": "2026-10-12T10:00:01Z", "service": "order-service", "level": "ERROR", "msg": "connection pool near limit: db pool exhausted"}
    """
    events = LogParser.parse_text(raw_logs)
    arch = ArchitectureDetector.detect(events)

    assert len(arch.failure_patterns) >= 2
    types = {f.pattern_type for f in arch.failure_patterns}
    assert "timeout_spike" in types or "upstream_unavailable" in types
    assert "resource_exhaustion" in types
    # Evidence lines must be non-empty
    for fp in arch.failure_patterns:
        assert len(fp.evidence_lines) > 0
