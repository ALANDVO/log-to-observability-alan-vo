from typing import List
from app.models.schemas import SloDefinition, BurnRateAlert

class SloEngine:
    @classmethod
    def calculate_slo(
        cls,
        service: str,
        target_percentage: float = 99.9,
        latency_threshold_ms: float = 250.0
    ) -> SloDefinition:
        target_ratio = target_percentage / 100.0
        allowed_error_ratio = round(1.0 - target_ratio, 6)

        good_request_expr = (
            'sum(rate(http_requests_total{service="' + service + '", status=~"2..|3.."}[5m]))'
        )
        total_request_expr = (
            'sum(rate(http_requests_total{service="' + service + '"}[5m]))'
        )
        slo_expr = f"{good_request_expr} / {total_request_expr}"

        # Google SRE multi-window burn rate alerts
        burn_alerts: List[BurnRateAlert] = [
            BurnRateAlert(
                window="1h",
                burn_rate=14.4,
                severity="critical",
                expr=(
                    '(1 - (sum(rate(http_requests_total{service="' + service + '", status=~"2..|3.."}[1h])) / '
                    'sum(rate(http_requests_total{service="' + service + '"}[1h])))) > '
                    f'({allowed_error_ratio} * 14.4)'
                )
            ),
            BurnRateAlert(
                window="6h",
                burn_rate=6.0,
                severity="warning",
                expr=(
                    '(1 - (sum(rate(http_requests_total{service="' + service + '", status=~"2..|3.."}[6h])) / '
                    'sum(rate(http_requests_total{service="' + service + '"}[6h])))) > '
                    f'({allowed_error_ratio} * 6.0)'
                )
            ),
            BurnRateAlert(
                window="24h",
                burn_rate=1.0,
                severity="info",
                expr=(
                    '(1 - (sum(rate(http_requests_total{service="' + service + '", status=~"2..|3.."}[24h])) / '
                    'sum(rate(http_requests_total{service="' + service + '"}[24h])))) > '
                    f'{allowed_error_ratio}'
                )
            )
        ]

        latency_thresh_sec = latency_threshold_ms / 1000.0
        latency_slo_expr = (
            'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{service="' +
            service + '"}[5m])) by (le)) <= ' + str(latency_thresh_sec)
        )

        return SloDefinition(
            service=service,
            target_percentage=target_percentage,
            good_request_expr=good_request_expr,
            total_request_expr=total_request_expr,
            slo_expr=slo_expr,
            latency_slo=latency_slo_expr,
            burn_alerts=burn_alerts
        )
