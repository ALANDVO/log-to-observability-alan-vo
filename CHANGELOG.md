# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.0.0] - 2026-10-20

### Added
- Multi-format log parser supporting JSON lines, syslog RFC 5424/3164, Nginx combined access logs, and container stdout.
- Deterministic architecture topology engine discovering microservice dependencies, communication protocols (HTTP, queue, gRPC), entrypoint routing, datastore dependencies, and failure modes.
- Opt-in advisory multi-provider LLM adapter supporting OpenAI-compatible, Anthropic, Gemini, and local Ollama endpoints with strict timeouts and credential isolation.
- REST API with FastAPI, SQLite persistent storage, UTC timestamps, audit log, pagination, and role-based access control.
- Keycloak OIDC authentication with PKCE authorization code flow and SAML identity brokering support, plus safe local demo mode refusing production activation.
- React + TypeScript dashboard with interactive SVG service topology graph, log ingestion workflow, and real-time analysis details.
- Comprehensive test suite covering log parsing, topology discovery, security role enforcement, and HTTP boundaries.

### Features
- **Log Architecture Detection**: Ingests multi-format logs and deterministically extracts service topology, communication edges, datastores, and error patterns. Opt-in advisory LLM analysis with multi-provider support.
- **Metric Mapping & Alert Generation**: Maps log patterns to RED/USE metrics, generates valid Prometheus/Alertmanager rule YAML with severity tags and runbook annotations.
- **Grafana Dashboard & SLO Engine**: Exports Grafana dashboard JSON (schemaVersion 39+) with PromQL panels. Multi-window burn-rate SLO calculation (1h @ 14.4x, 6h @ 6x, 24h @ 1x) following Google SRE methodology.
- **AI/ML Evaluation Benchmark**: Reproducible evaluation harness against synthetic microservice baseline with ground-truth topology and injected failure anomalies.

## [1.0.0] - 2026-10-12 (Initial checkpoint)

### Added
- Multi-format log parser supporting JSON lines, syslog RFC 5424/3164, Nginx combined access logs, and container stdout.
- Deterministic architecture topology engine discovering microservice dependencies, communication protocols (HTTP, queue, gRPC), entrypoint routing, datastore dependencies, and failure modes.
- Opt-in advisory multi-provider LLM adapter supporting OpenAI-compatible, Anthropic, Gemini, and local Ollama endpoints with strict timeouts and credential isolation.
- REST API with FastAPI, SQLite persistent storage, UTC timestamps, audit log, pagination, and role-based access control.
- Keycloak OIDC authentication with PKCE authorization code flow and SAML identity brokering support, plus safe local demo mode refusing production activation.
- React + TypeScript dashboard with interactive SVG service topology graph, log ingestion workflow, and real-time analysis details.
- Comprehensive test suite covering log parsing, topology discovery, security role enforcement, and HTTP boundaries.