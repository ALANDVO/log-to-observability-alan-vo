#!/usr/bin/env python3
"""CLI entrypoint for log-to-observability and FastAPI application export."""
import sys
import os
import json
import argparse

# Add backend directory to sys.path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app, create_app
from app.services.log_parser import LogParser
from app.services.architecture_detector import ArchitectureDetector
from app.services.dashboard_generator import DashboardGenerator
from app.services.alert_generator import AlertGenerator
from app.services.slo_engine import SloEngine
from app.services.metric_mapper import MetricMapper

def _load_log_text(path: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    # Sample fallback
    return (
        '{"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "method": "GET", "path": "/orders", "status": 200, "duration_ms": 42}\n'
        '{"ts": "2026-10-12T10:00:01Z", "service": "order-service", "level": "WARN", "msg": "db pool near limit: 96%", "duration_ms": 310, "datastore": "postgres"}\n'
        '{"ts": "2026-10-12T10:00:02Z", "service": "api-gateway", "level": "ERROR", "method": "POST", "path": "/orders", "status": 502, "duration_ms": 3001, "downstream": "order-service"}\n'
    )

def detect(args):
    content = _load_log_text(args.logs)
    events = LogParser.parse_text(content)
    result = ArchitectureDetector.detect(events)

    print(f"\n{'='*60}\nDETECTED ARCHITECTURE\n{'='*60}")
    for s in result.services:
        print(f"  {s.name} [{s.role}]: {s.evidence}")
    print("\nTopology:")
    for t in result.topology:
        print(f"  {t.source} -> {t.target} ({t.protocol})")
    print("\nData stores: " + ", ".join(d.name for d in result.datastores))
    print("\nFailure modes:")
    for f in result.failure_patterns:
        print(f"  - {f.summary}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        print(f"\nArchitecture written to {args.output}")
    return result

def dashboard(args):
    content = _load_log_text(args.logs)
    events = LogParser.parse_text(content)
    arch = ArchitectureDetector.detect(events)
    dash = DashboardGenerator.generate(arch, title=args.title or "AI-Generated Observability Dashboard")

    output_file = args.output or "dashboards.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dash.raw_json, f, indent=2)
    print(f"\nGrafana dashboard written to {output_file} ({len(dash.panels)} panels)")
    return dash

def alerts(args):
    content = _load_log_text(args.logs)
    events = LogParser.parse_text(content)
    arch = ArchitectureDetector.detect(events)
    alert_group = AlertGenerator.generate_alerts(arch)

    print(f"\n{'='*60}\nALERT RULES: {len(alert_group.rules)}\n{'='*60}")
    for a in alert_group.rules:
        print(f"  [{a.severity.upper()}] {a.alert}")
        print(f"    expr: {a.expr}\n    summary: {a.summary}")

    if args.output:
        yaml_content = AlertGenerator.to_prometheus_yaml(alert_group)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(yaml_content)
        print(f"\nAlert rules written to {args.output}")
    return alert_group

def slo(args):
    service = args.service or "service"
    budget = float(args.budget or 99.9)
    result = SloEngine.calculate_slo(service=service, target_percentage=budget)

    print(f"\n{'='*60}\nSLO: {service} @ {budget}%\n{'='*60}")
    print(f"Good-request definition: {result.good_request_expr}")
    print(f"SLO expression: {result.slo_expr}")
    if result.latency_slo:
        print(f"Latency SLO: {result.latency_slo}")
    print("\nBurn-rate alerts:")
    for a in result.burn_alerts:
        print(f"  {a.window} ({a.burn_rate}x): {a.expr}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2)
        print(f"\nSLO written to {args.output}")
    return result

def mapping(args):
    content = _load_log_text(args.logs)
    events = LogParser.parse_text(content)
    arch = ArchitectureDetector.detect(events)
    mappings = MetricMapper.map_architecture_to_metrics(arch)

    print(f"\n{'='*60}\nLOG -> METRIC MAPPING\n{'='*60}")
    for m in mappings:
        print(f"  {m.pattern} -> {m.metric} ({m.metric_type})")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump([m.model_dump() for m in mappings], f, indent=2)
        print(f"\nMapping written to {args.output}")
    return mappings

def main():
    p = argparse.ArgumentParser(description="log-to-observability CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="detect architecture")
    d.add_argument("--logs", required=True)
    d.add_argument("--output")
    d.set_defaults(fn=detect)

    h = sub.add_parser("dashboard", help="generate Grafana dashboard")
    h.add_argument("--logs", required=True)
    h.add_argument("--output", default="dashboards.json")
    h.add_argument("--title")
    h.add_argument("--promql", action="store_true")
    h.set_defaults(fn=dashboard)

    a = sub.add_parser("alerts", help="generate alert rules")
    a.add_argument("--logs", required=True)
    a.add_argument("--output")
    a.set_defaults(fn=alerts)

    s = sub.add_parser("slo", help="generate SLO definitions")
    s.add_argument("--logs", required=True)
    s.add_argument("--service")
    s.add_argument("--budget", default="99.9")
    s.add_argument("--output")
    s.set_defaults(fn=slo)

    m = sub.add_parser("mapping", help="log-to-metric mapping")
    m.add_argument("--logs", required=True)
    m.add_argument("--output")
    m.set_defaults(fn=mapping)

    args = p.parse_args()
    args.fn(args)

if __name__ == "__main__":
    main()
