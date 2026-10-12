import pytest
import yaml
from app.services.log_parser import LogParser
from app.services.architecture_detector import ArchitectureDetector
from app.services.alert_generator import AlertGenerator

def test_alert_rules_generation_and_yaml():
    logs = """
    {"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "method": "GET", "status": 200, "duration_ms": 25, "caller": "10.0.0.1"}
    {"ts": "2026-10-12T10:00:01Z", "service": "order-service", "method": "GET", "status": 200, "duration_ms": 50, "datastore": "postgres"}
    """
    events = LogParser.parse_text(logs)
    arch = ArchitectureDetector.detect(events)
    alert_group = AlertGenerator.generate_alerts(arch)

    assert len(alert_group.rules) >= 2
    # Check that rule names and expr are valid
    for rule in alert_group.rules:
        assert len(rule.alert) > 0
        assert ">" in rule.expr or "<" in rule.expr
        assert rule.severity in ["warning", "critical", "info"]

    yaml_text = AlertGenerator.to_prometheus_yaml(alert_group)
    parsed = yaml.safe_load(yaml_text)
    assert "groups" in parsed
    assert len(parsed["groups"][0]["rules"]) == len(alert_group.rules)
