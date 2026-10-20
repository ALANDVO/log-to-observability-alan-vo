# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

log-architecture-detection

## Roadmap

### log-architecture-detection — Log Ingestion and Service Architecture Auto-Detection

Status: done

Acceptance:
- Ingests multi-format logs including JSON lines, syslog, Nginx access logs, and container streams
- Deterministically extracts service topology, communication edges, datastores, and error patterns without LLM
- Provides opt-in advisory LLM analysis for architectural insights with configurable multi-provider support
- Persists architecture analysis runs in SQLite with audit log and REST API endpoints

Implementation: `backend/app/main.py`, `backend/app/services/architecture_detector.py`, `backend/app/services/log_parser.py`, `backend/app/api/architecture.py`

Tests: `backend/tests/test_architecture.py`, `backend/tests/test_log_parser.py`

### metric-alert-generator — Log-to-Metric Mapping and Prometheus Alert Rule Generator

Status: done

Acceptance:
- Deterministic pattern extraction mapping logs to RED/USE metrics
- Generation of valid Prometheus and Alertmanager rule YAML with thresholds and runbook hints
- Export and test validation for alert syntax and label consistency

Implementation: `backend/app/services/metric_mapper.py`, `backend/app/services/alert_generator.py`, `backend/app/api/observability.py`

Tests: `backend/tests/test_metric_mapper.py`, `backend/tests/test_alert_generator.py`

### grafana-slo-engine — Grafana Dashboard and Multi-Window SLO Burn Rate Engine

Status: done

Acceptance:
- Export of Grafana dashboard JSON schemaVersion 39+ with PromQL panels
- Multi-window burn-rate SLO calculation (1h/6h/24h error budget consumption)
- Interactive dashboard visualization and JSON import verification

Implementation: `backend/app/services/dashboard_generator.py`, `backend/app/services/slo_engine.py`, `backend/app/api/observability.py`

Tests: `backend/tests/test_dashboard_generator.py`, `backend/tests/test_slo_engine.py`

