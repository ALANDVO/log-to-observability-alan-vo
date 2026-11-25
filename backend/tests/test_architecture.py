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
def test_gateway_inferred_edges_when_partial_explicit():
    """Test that gateway gets inferred edges to services it doesn't explicitly call."""
    raw_logs = """
    {"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "method": "GET", "path": "/api/v1/orders", "status": 200, "duration_ms": 35, "caller": "10.0.0.1", "downstream": "order-service"}
    {"ts": "2026-10-12T10:00:01Z", "service": "order-service", "method": "POST", "path": "/orders", "status": 200, "duration_ms": 90, "caller": "api-gateway", "datastore": "postgres"}
    {"ts": "2026-10-12T10:00:02Z", "service": "payment-service", "method": "POST", "path": "/charge", "status": 200, "duration_ms": 110, "datastore": "redis"}
    {"ts": "2026-10-12T10:00:03Z", "service": "inventory-service", "method": "GET", "path": "/items", "status": 200, "duration_ms": 45}
    """
    events = LogParser.parse_text(raw_logs)
    arch = ArchitectureDetector.detect(events)

    service_names = {s.name for s in arch.services}
    assert "api-gateway" in service_names
    assert "order-service" in service_names
    assert "payment-service" in service_names
    assert "inventory-service" in service_names

    # Gateway has explicit edge to order-service (via downstream field)
    edges = {(e.source, e.target) for e in arch.topology}
    assert ("api-gateway", "order-service") in edges

    # But gateway should also get inferred edges to payment-service and inventory-service
    # since they are business services and gateway has no explicit edges to them
    assert ("api-gateway", "payment-service") in edges
    assert ("api-gateway", "inventory-service") in edges


def test_gateway_inferred_edges_when_mostly_explicit():
    """Test that gateway gets inferred edges to remaining services when it has partial explicit edges.
    
    Scenario: gateway has explicit edges to 2 out of 3 business services,
    so 1 inferred edge is added for the missing service.
    """
    raw_logs = """
    {"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "method": "GET", "path": "/api/v1/orders", "status": 200, "duration_ms": 35, "caller": "10.0.0.1", "downstream": "order-service"}
    {"ts": "2026-10-12T10:00:01Z", "service": "order-service", "method": "POST", "path": "/orders", "status": 200, "duration_ms": 90, "caller": "api-gateway", "datastore": "postgres"}
    {"ts": "2026-10-12T10:00:02Z", "service": "payment-service", "method": "POST", "path": "/charge", "status": 200, "duration_ms": 110, "datastore": "redis"}
    {"ts": "2026-10-12T10:00:03Z", "service": "api-gateway", "method": "GET", "path": "/api/v1/payment", "status": 200, "duration_ms": 25, "caller": "10.0.0.1", "downstream": "payment-service"}
    {"ts": "2026-10-12T10:00:04Z", "service": "inventory-service", "method": "GET", "path": "/items", "status": 200, "duration_ms": 45}
    """
    events = LogParser.parse_text(raw_logs)
    arch = ArchitectureDetector.detect(events)

    service_names = {s.name for s in arch.services}
    assert "api-gateway" in service_names
    assert "order-service" in service_names
    assert "payment-service" in service_names
    assert "inventory-service" in service_names

    # Gateway has explicit edge to order-service (via downstream field) and payment-service (via downstream field)
    edges = {(e.source, e.target) for e in arch.topology}
    assert ("api-gateway", "order-service") in edges

    # Gateway has explicit edge to payment-service (via downstream field)
    assert ("api-gateway", "payment-service") in edges

    # But gateway should also get inferred edge to inventory-service
    # since it's a business service and gateway has no explicit edge to it
    assert ("api-gateway", "inventory-service") in edges


def test_gateway_inferred_edges_with_single_event():
    """Test that gateway gets inferred edges to business services when they have single events.
    
    Verifies the max(1, len // 2) count calculation works correctly when
    a business service has only 1 associated event.
    """
    raw_logs = """
    {"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "method": "GET", "path": "/api/v1/orders", "status": 200, "duration_ms": 35, "caller": "10.0.0.1", "downstream": "order-service"}
    {"ts": "2026-10-12T10:00:01Z", "service": "order-service", "method": "POST", "path": "/orders", "status": 200, "duration_ms": 90, "caller": "api-gateway"}
    {"ts": "2026-10-12T10:00:02Z", "service": "payment-service", "method": "POST", "path": "/charge", "status": 200, "duration_ms": 110, "datastore": "redis"}
    {"ts": "2026-10-12T10:00:03Z", "service": "inventory-service", "method": "GET", "path": "/items", "status": 200, "duration_ms": 45}
    """
    events = LogParser.parse_text(raw_logs)
    arch = ArchitectureDetector.detect(events)

    service_names = {s.name for s in arch.services}
    assert "api-gateway" in service_names
    assert "order-service" in service_names
    assert "payment-service" in service_names
    assert "inventory-service" in service_names

    # Gateway has explicit edge to order-service (via downstream field)
    edges = {(e.source, e.target) for e in arch.topology}
    assert ("api-gateway", "order-service") in edges

    # Gateway should get inferred edges to payment-service and inventory-service
    # since they are business services and gateway has no explicit edges to them
    # (each has 1 event, so count = max(1, 1//2) = 1)
    assert ("api-gateway", "payment-service") in edges
    assert ("api-gateway", "inventory-service") in edges

    # Verify edge counts: order-service has 2 events (1 from gateway downstream + 1 from caller),
    # so order-service edge count should be 2. payment-service and inventory-service have 1 event each,
    # so inferred edge counts should be max(1, 1//2) = 1
    edge_count_map = {(e.source, e.target): e.call_count for e in arch.topology}
    assert edge_count_map.get(("api-gateway", "order-service")) == 2
    assert edge_count_map.get(("api-gateway", "payment-service")) == 1
    assert edge_count_map.get(("api-gateway", "inventory-service")) == 1
