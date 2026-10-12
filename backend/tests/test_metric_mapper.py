import pytest
from app.services.log_parser import LogParser
from app.services.architecture_detector import ArchitectureDetector
from app.services.metric_mapper import MetricMapper

def test_metric_mapper_red_and_use():
    logs = '{"ts": "2026-10-12T10:00:00Z", "service": "order-service", "method": "GET", "status": 200, "duration_ms": 50, "datastore": "redis"}'
    events = LogParser.parse_text(logs)
    arch = ArchitectureDetector.detect(events)
    mappings = MetricMapper.map_architecture_to_metrics(arch)

    metric_names = [m.metric for m in mappings]
    assert "http_requests_total" in metric_names
    assert "http_requests_failed_total" in metric_names
    assert "http_request_duration_seconds" in metric_names
    assert any("redis" in m for m in metric_names)
