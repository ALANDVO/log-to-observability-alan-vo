import pytest
from app.services.log_parser import LogParser
from app.services.architecture_detector import ArchitectureDetector
from app.services.dashboard_generator import DashboardGenerator

def test_grafana_dashboard_json_structure():
    logs = '{"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "method": "GET", "status": 200, "duration_ms": 30}'
    events = LogParser.parse_text(logs)
    arch = ArchitectureDetector.detect(events)
    dash = DashboardGenerator.generate(arch, title="E-Commerce Overview")

    assert dash.title == "E-Commerce Overview"
    assert dash.schema_version == 39
    assert len(dash.panels) >= 4

    raw = dash.raw_json
    assert raw["schemaVersion"] == 39
    assert "panels" in raw
    assert "time" in raw
    assert raw["time"]["from"] == "now-6h"
