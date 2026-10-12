import yaml
from typing import List, Dict, Any
from app.models.schemas import PrometheusAlert, AlertGroup, ArchitectureResult

class AlertGenerator:
    @classmethod
    def generate_alerts(cls, arch: ArchitectureResult) -> AlertGroup:
        rules: List[PrometheusAlert] = []

        # Service-level alerts
        for svc in arch.services:
            name = svc.name.replace('-', '_')
            rules.append(PrometheusAlert(
                alert=f"{name}_high_error_rate",
                expr=(
                    'sum(rate(http_requests_failed_total{service="' + svc.name + '"}[5m])) / '
                    'sum(rate(http_requests_total{service="' + svc.name + '"}[5m])) * 100 > 5'
                ),
                for_duration="2m",
                severity="critical" if svc.user_facing else "warning",
                summary=f"High HTTP error rate detected on service {svc.name}",
                runbook=f"Inspect error logs for {svc.name}. Verify downstream dependencies and resource allocations."
            ))

            rules.append(PrometheusAlert(
                alert=f"{name}_latency_p95_high",
                expr=(
                    'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service="' +
                    svc.name + '"}[5m])) by (le)) > 1.0'
                ),
                for_duration="5m",
                severity="warning",
                summary=f"p95 latency exceeded 1000ms on service {svc.name}",
                runbook=f"Check CPU throttling and database query locks affecting {svc.name}."
            ))

        # Datastore alerts
        for ds in arch.datastores:
            ds_name = ds.name.replace('-', '_')
            if ds.type == "relational":
                rules.append(PrometheusAlert(
                    alert=f"{ds_name}_db_connection_pool_saturated",
                    expr=f'{ds.name}_connection_pool_saturation_ratio > 0.85',
                    for_duration="3m",
                    severity="critical",
                    summary=f"Database connection pool for {ds.name} near capacity (>85%)",
                    runbook=f"Increase pool limits or optimize connection leakages for {ds.name}."
                ))
            elif ds.type == "cache":
                rules.append(PrometheusAlert(
                    alert=f"{ds_name}_cache_hit_rate_drop",
                    expr=(
                        'sum(rate(' + ds.name + '_operations_total{status="hit"}[5m])) / '
                        'sum(rate(' + ds.name + '_operations_total[5m])) < 0.70'
                    ),
                    for_duration="10m",
                    severity="warning",
                    summary=f"Cache hit rate for {ds.name} dropped below 70%",
                    runbook=f"Investigate cache eviction policies and key expiration storms."
                ))

        return AlertGroup(name="observability_alerts", rules=rules)

    @classmethod
    def to_prometheus_yaml(cls, alert_group: AlertGroup) -> str:
        data = {
            "groups": [
                {
                    "name": alert_group.name,
                    "interval": "30s",
                    "rules": [
                        {
                            "alert": r.alert,
                            "expr": r.expr,
                            "for": r.for_duration,
                            "labels": {
                                "severity": r.severity,
                                "source": "log-to-observability"
                            },
                            "annotations": {
                                "summary": r.summary,
                                "runbook_url": r.runbook
                            }
                        }
                        for r in alert_group.rules
                    ]
                }
            ]
        }
        return yaml.dump(data, sort_keys=False)
