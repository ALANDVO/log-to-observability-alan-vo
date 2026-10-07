#!/usr/bin/env python3
# log-to-observability — AI log-to-observability pipeline: takes raw logs, auto-detects the service architecture, and generates Grafana dashboard JSON, alert rules, and SLO definitions based on LLM analysis of log patterns.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_client import LLM
def detect(args):
    """Auto-detect the service architecture from logs."""
    llm = LLM()
    logs = _load_logs(args.logs)
    sample = "\n".join(_line(l) for l in logs[:120])
    result = llm.generate(
        f"Raw logs (120-line sample):\n{sample}\n\n"
        "Detect the architecture: 1) distinct services/components, 2) how they talk (sync/async, queues, HTTP), "
        "3) which are user-facing, 4) data stores touched, 5) failure patterns visible. "
        "Respond as JSON: {"services": [{"name": "...", "role": "...", "evidence": "..."}], "topology": ["A -> B", ...], "datastores": ["..."], "failure_modes": ["..."]}",
        system="You are an SRE reverse-engineering an architecture from its logs. Be evidence-based — quote the log line that proves each claim."
    )
    parsed = _json(result)
    print(f"\n{'='*60}\nDETECTED ARCHITECTURE\n{'='*60}")
    for s in parsed.get("services", []):
        print(f"  {s.get('name', '?')} [{s.get('role', '?')}]: {s.get('evidence', '')}")
    print("\nTopology:")
    for t in parsed.get("topology", []):
        print(f"  {t}")
    print("\nData stores: " + ", ".join(parsed.get("datastores", [])))
    print("\nFailure modes:")
    for f in parsed.get("failure_modes", []):
        print(f"  - {f}")
    if args.output:
        with open(args.output, "w") as fh:
            json.dump(parsed, fh, indent=2)
        print(f"\nArchitecture map written to {args.output}")
    return parsed

def dashboard(args):
    """Generate a Grafana dashboard JSON from logs."""
    llm = LLM()
    logs = _load_logs(args.logs)
    arch = llm.generate(
        f"Log sample:\n{chr(10).join(_line(l) for l in logs[:80])}\n\nList the services and the key request paths / operations visible. JSON: {{"services": ["..."], "operations": ["..."]}}",
        system="You are an SRE. JSON only."
    )
    meta = _json(arch)
    dash = llm.generate(
        f"Services: {meta.get('services', [])}\nOperations: {meta.get('operations', [])}\n\n"
        "Generate a complete Grafana dashboard JSON (schemaVersion >= 39) for monitoring these services. "
        "Panels required: request rate, error rate, p50/p95/p99 latency, saturation signals, per-service breakdown. "
        "Use PromQL queries. Output ONLY valid JSON matching the Grafana dashboard object."
        if not args.promql
        else "Generate a complete Grafana dashboard JSON (schemaVersion >= 39). Panels: request rate, error rate, p50/p95/p99 latency, per-service breakdown, saturation. PromQL. Output ONLY valid JSON."
    )
    dash = _json(dash)
    dash.setdefault("title", args.title or "AI-Generated Observability Dashboard")
    dash.setdefault("uid", "ai-obs-" + "".join(c.lower() for c in (args.title or "dash")[:8]))
    dash.setdefault("schemaVersion", 39)
    dash.setdefault("panels", [])
    dash.setdefault("time", {"from": "now-6h", "to": "now"})
    dash.setdefault("refresh", "30s")
    with open(args.output, "w") as fh:
        json.dump(dash, fh, indent=2)
    print(f"\nGrafana dashboard written to {args.output} ({len(dash.get('panels', []))} panels)")
    print("Import via Grafana: Dashboards -> Import -> paste file contents.")
    return dash

def alerts(args):
    """Generate alert rules from log failure patterns."""
    llm = LLM()
    logs = _load_logs(args.logs)
    sample = "\n".join(_line(l) for l in logs[:150])
    rules = llm.generate(
        f"Logs:\n{sample}\n\n"
        "Identify the failure patterns (error spikes, timeouts, retries, resource exhaustion, auth failures). "
        "For each, write a Prometheus/Alertmanager alert rule with a meaningful name, expression, for-duration, severity, "
        "and an LLM-written summary + runbook hint. "
        "Respond as JSON: {"alerts": [{"name": "...", "expr": "...", "for": "5m", "severity": "warning|critical", "summary": "...", "runbook": "..."}]}"
    )
    parsed = _json(rules)
    out = {
        "groups": [{
            "name": "ai-generated",
            "interval": "30s",
            "rules": [
                {
                    "alert": a.get("name", "unnamed"),
                    "expr": a.get("expr", ""),
                    "for": a.get("for", "5m"),
                    "labels": {"severity": a.get("severity", "warning"), "source": "ai-observability"},
                    "annotations": {"summary": a.get("summary", ""), "runbook": a.get("runbook", "")},
                }
                for a in parsed.get("alerts", [])
            ],
        }]
    }
    print(f"\n{'='*60}\nALERT RULES: {len(out['groups'][0]['rules'])}\n{'='*60}")
    for a in out["groups"][0]["rules"]:
        print(f"  [{a['labels']['severity'].upper()}] {a['alert']}")
        print(f"    expr: {a['expr']}\n    summary: {a['annotations']['summary']}")
    if args.output:
        with open(args.output, "w") as fh:
            json.dump(out, fh, indent=2)
        print(f"\nAlert rules written to {args.output}")
    return out

def slo(args):
    """Generate SLO definitions + burn-rate alerts."""
    llm = LLM()
    logs = _load_logs(args.logs)
    svc = args.service or "service"
    budget = args.budget or 99.9
    plan = llm.generate(
        f"Service: {svc}\nTarget: {budget}%\nLog sample:\n{chr(10).join(_line(l) for l in logs[:80])}\n\n"
        f"Design an SLO for {svc}: 1) which metric defines 'good request' (from the logs), 2) the availability SLO expression, "
        f"3) a latency SLO if latency signals exist, 4) multi-window burn-rate alerts (2h/1h windows, 14.4x and 6x burn rates). "
        "Respond as JSON: {{"good_request": "...", "slo_expr": "...", "latency_slo": "...", "burn_alerts": [{{"name": "...", "expr": "..."}}]}}"
    )
    parsed = _json(plan)
    print(f"\n{'='*60}\nSLO: {svc} @ {budget}%\n{'='*60}")
    print(f"Good-request definition: {parsed.get('good_request', '')}")
    print(f"SLO expression: {parsed.get('slo_expr', '')}")
    if parsed.get("latency_slo"):
        print(f"Latency SLO: {parsed.get('latency_slo', '')}")
    print("\nBurn-rate alerts:")
    for a in parsed.get("burn_alerts", []):
        print(f"  {a.get('name', '')}: {a.get('expr', '')}")
    if args.output:
        with open(args.output, "w") as fh:
            json.dump(parsed, fh, indent=2)
        print(f"\nSLO written to {args.output}")
    return parsed

def mapping(args):
    """Produce a log-to-metric mapping table."""
    llm = LLM()
    logs = _load_logs(args.logs)
    table = llm.generate(
        f"Logs:\n{chr(10).join(_line(l) for l in logs[:150])}\n\n"
        "Build a mapping: each distinct log pattern -> the metric it should produce (name, type, labels, unit). "
        "Respond as JSON: {"mappings": [{"pattern": "...", "metric": "...", "type": "counter|histogram|gauge", "labels": "...", "unit": "..."}]}"
    )
    parsed = _json(table)
    print(f"\n{'='*60}\nLOG -> METRIC MAPPING\n{'='*60}")
    for m in parsed.get("mappings", []):
        print(f"  {m.get('pattern', '')} -> {m.get('metric', '')} ({m.get('type', '?')})")
    if args.output:
        with open(args.output, "w") as fh:
            json.dump(parsed, fh, indent=2)
        print(f"\nMapping written to {args.output}")
    return parsed

def _line(l):
    if isinstance(l, dict):
        return json.dumps(l)
    return str(l)

def _load_logs(path):
    try:
        content = open(path).read().strip()
    except FileNotFoundError:
        print(f"Log file not found: {path} — using built-in sample", file=sys.stderr)
        content = "\n".join([
            json.dumps({"ts": "2026-10-06T10:00:00Z", "service": "api-gateway", "level": "INFO", "method": "GET", "path": "/orders", "status": 200, "ms": 42}),
            json.dumps({"ts": "2026-10-06T10:00:01Z", "service": "order-service", "level": "WARN", "msg": "db pool near limit: 96%", "ms": 310}),
            json.dumps({"ts": "2026-10-06T10:00:02Z", "service": "api-gateway", "level": "ERROR", "method": "POST", "path": "/orders", "status": 502, "ms": 3001}),
        ])
    out = []
    for line in content.split("\n"):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            out.append(line)
    return out

def _json(text):
    start, end = text.find("{"), text.rfind("}") + 1
    if start < 0 or end <= 1:
        return {}
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return {}

def main():
    import argparse
    p = argparse.ArgumentParser(description="log-to-observability")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect", help="detect architecture")
    d.add_argument("--logs", required=True); d.add_argument("--output"); d.set_defaults(fn=detect)
    h = sub.add_parser("dashboard", help="generate Grafana dashboard")
    h.add_argument("--logs", required=True); h.add_argument("--output", default="dashboards.json")
    h.add_argument("--title"); h.add_argument("--promql", action="store_true"); h.set_defaults(fn=dashboard)
    a = sub.add_parser("alerts", help="generate alert rules")
    a.add_argument("--logs", required=True); a.add_argument("--output"); a.set_defaults(fn=alerts)
    s = sub.add_parser("slo", help="generate SLO definitions")
    s.add_argument("--logs", required=True); s.add_argument("--service")
    s.add_argument("--budget", default="99.9"); s.add_argument("--output"); s.set_defaults(fn=slo)
    m = sub.add_parser("mapping", help="log-to-metric mapping")
    m.add_argument("--logs", required=True); m.add_argument("--output"); m.set_defaults(fn=mapping)
    args = p.parse_args()
    args.fn(args)

if __name__ == '__main__':
    main()
