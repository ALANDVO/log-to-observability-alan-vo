from typing import List
from app.models.schemas import LogEvent, MetricMapping, ArchitectureResult

class MetricMapper:
    @classmethod
    def map_architecture_to_metrics(cls, arch: ArchitectureResult) -> List[MetricMapping]:
        mappings: List[MetricMapping] = [
            # Core RED metrics for services
            MetricMapping(
                pattern=r'HTTP\s+(GET|POST|PUT|DELETE)\s+(\S+)\s+(\d{3})',
                metric='http_requests_total',
                metric_type='counter',
                labels=['service', 'method', 'status', 'path'],
                unit='requests',
                description='Total HTTP request count partitioned by service and HTTP status code'
            ),
            MetricMapping(
                pattern=r'status\s*=\s*(5\d{2})|level\s*=\s*ERROR',
                metric='http_requests_failed_total',
                metric_type='counter',
                labels=['service', 'error_type'],
                unit='errors',
                description='Failed requests yielding 5xx status codes or ERROR level logs'
            ),
            MetricMapping(
                pattern=r'(\d+(?:\.\d+)?)\s*(?:ms|duration)',
                metric='http_request_duration_seconds',
                metric_type='histogram',
                labels=['service', 'path'],
                unit='seconds',
                description='Request latency distribution in seconds across service endpoints'
            )
        ]

        # USE metrics based on detected datastores
        for ds in arch.datastores:
            if ds.type == "cache":
                mappings.append(MetricMapping(
                    pattern=rf'{ds.name}\s+(?:hit|miss|get|set)',
                    metric=f'{ds.name}_operations_total',
                    metric_type='counter',
                    labels=['service', 'operation', 'status'],
                    unit='operations',
                    description=f'Cache access volume and hit/miss counts for {ds.name}'
                ))
            elif ds.type == "queue":
                mappings.append(MetricMapping(
                    pattern=rf'{ds.name}\s+(?:publish|consume|lag)',
                    metric=f'{ds.name}_messages_processed_total',
                    metric_type='counter',
                    labels=['service', 'topic'],
                    unit='messages',
                    description=f'Message ingestion and consumption rate for {ds.name}'
                ))
            elif ds.type == "relational":
                mappings.append(MetricMapping(
                    pattern=rf'{ds.name}.*?(?:pool|query|conn)',
                    metric=f'{ds.name}_connection_pool_saturation_ratio',
                    metric_type='gauge',
                    labels=['service'],
                    unit='ratio',
                    description=f'Connection pool utilization ratio for database {ds.name}'
                ))

        return mappings
