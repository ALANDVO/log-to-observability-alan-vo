import pytest
from app.services.log_parser import LogParser

def test_parse_json_lines():
    line = '{"ts": "2026-10-12T12:00:00Z", "service": "order-service", "method": "POST", "path": "/orders", "status": 201, "duration_ms": 75, "caller": "api-gateway", "datastore": "postgres", "msg": "order persisted"}'
    event = LogParser.parse_line(line)
    assert event is not None
    assert event.service == "order-service"
    assert event.method == "POST"
    assert event.path == "/orders"
    assert event.status == 201
    assert event.duration_ms == 75.0
    assert event.caller == "api-gateway"
    assert event.datastore == "postgresql"

def test_parse_nginx_combined_log():
    line = '192.168.1.50 - - [12/Oct/2026:14:20:10 +0000] "GET /api/v1/catalog HTTP/1.1" 200 4520 "-" "Mozilla/5.0"'
    event = LogParser.parse_line(line)
    assert event is not None
    assert event.service == "nginx-ingress"
    assert event.method == "GET"
    assert event.path == "/api/v1/catalog"
    assert event.status == 200
    assert event.downstream == "catalog-service"

def test_parse_syslog():
    line = '<134>1 2026-10-12T14:00:00Z web01 payment-service: error connecting to redis cache timeout'
    event = LogParser.parse_line(line)
    assert event is not None
    assert event.service == "payment-service"
    assert event.level == "ERROR"
    assert event.datastore == "redis"

def test_parse_malformed_and_empty_lines():
    content = "\n\n   \nnot a json line but mentions [worker-svc] and status=500 in 400ms\n"
    events = LogParser.parse_text(content)
    assert len(events) == 1
    assert events[0].service == "worker-svc"
    assert events[0].status == 500
    assert events[0].duration_ms == 400.0
