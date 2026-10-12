import re
from typing import Dict, Any, List
from app.models.schemas import GrafanaDashboard, GrafanaPanel, ArchitectureResult

class DashboardGenerator:
    @classmethod
    def generate(cls, arch: ArchitectureResult, title: str = "AI-Generated Observability Dashboard") -> GrafanaDashboard:
        uid_slug = re.sub(r'[^a-z0-9]', '', title.lower())[:12] or "ai-obs"
        uid = f"ai-obs-{uid_slug}"

        panels_list: List[GrafanaPanel] = []
        panels_json: List[Dict[str, Any]] = []

        # Panel 1: Overall Request Volume
        p1 = GrafanaPanel(
            id=1,
            title="Service Request Rate (req/sec)",
            type="timeseries",
            expr="sum by (service) (rate(http_requests_total[2m]))",
            grid_pos={"h": 8, "w": 12, "x": 0, "y": 0}
        )
        panels_list.append(p1)
        panels_json.append({
            "id": 1,
            "title": p1.title,
            "type": p1.type,
            "gridPos": p1.grid_pos,
            "targets": [{"refId": "A", "expr": p1.expr, "legendFormat": "{{service}}"}]
        })

        # Panel 2: HTTP 5xx Error Percentage
        p2 = GrafanaPanel(
            id=2,
            title="Service Error Rate (%)",
            type="timeseries",
            expr="sum by (service) (rate(http_requests_failed_total[2m])) / sum by (service) (rate(http_requests_total[2m])) * 100",
            grid_pos={"h": 8, "w": 12, "x": 12, "y": 0}
        )
        panels_list.append(p2)
        panels_json.append({
            "id": 2,
            "title": p2.title,
            "type": p2.type,
            "gridPos": p2.grid_pos,
            "targets": [{"refId": "A", "expr": p2.expr, "legendFormat": "{{service}} error %"}]
        })

        # Panel 3: Latency Distribution (p50, p95, p99)
        p3 = GrafanaPanel(
            id=3,
            title="Request Latency Percentiles (p50 / p95 / p99)",
            type="timeseries",
            expr="histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))",
            grid_pos={"h": 8, "w": 12, "x": 0, "y": 8}
        )
        panels_list.append(p3)
        panels_json.append({
            "id": 3,
            "title": p3.title,
            "type": p3.type,
            "gridPos": p3.grid_pos,
            "targets": [
                {"refId": "A", "expr": "histogram_quantile(0.50, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))", "legendFormat": "p50"},
                {"refId": "B", "expr": "histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))", "legendFormat": "p95"},
                {"refId": "C", "expr": "histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))", "legendFormat": "p99"}
            ]
        })

        # Panel 4: Datastore Saturation
        p4 = GrafanaPanel(
            id=4,
            title="Datastore Connection Saturation",
            type="gauge",
            expr="max by (service) (connection_pool_saturation_ratio)",
            grid_pos={"h": 8, "w": 12, "x": 12, "y": 8}
        )
        panels_list.append(p4)
        panels_json.append({
            "id": 4,
            "title": p4.title,
            "type": p4.type,
            "gridPos": p4.grid_pos,
            "targets": [{"refId": "A", "expr": p4.expr, "legendFormat": "{{service}}"}]
        })

        raw_dash = {
            "title": title,
            "uid": uid,
            "schemaVersion": 39,
            "refresh": "30s",
            "time": {"from": "now-6h", "to": "now"},
            "panels": panels_json,
            "templating": {
                "list": [
                    {
                        "name": "service",
                        "type": "query",
                        "query": "label_values(http_requests_total, service)",
                        "current": {"text": "All", "value": "$__all"}
                    }
                ]
            }
        }

        return GrafanaDashboard(
            title=title,
            uid=uid,
            schema_version=39,
            panels=panels_list,
            raw_json=raw_dash
        )
