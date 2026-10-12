# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.0.0] - 2026-10-12

### Added
- Multi-format log parser supporting JSON lines, syslog RFC 5424/3164, Nginx combined access logs, and container stdout.
- Deterministic architecture topology engine discovering microservice dependencies, protocols (HTTP, queue, gRPC), entrypoint routing, datastore dependencies, and failure modes.
- Opt-in advisory multi-provider LLM adapter supporting OpenAI-compatible, Anthropic, Gemini, and local Ollama endpoints with strict timeouts and credential isolation.
- REST API with FastAPI, SQLite persistent storage, UTC timestamps, audit log, pagination, and role-based access control.
- Keycloak OIDC authentication with PKCE authorization code flow and SAML identity brokering support, plus safe local demo mode refusing production activation.
- React + TypeScript dashboard with interactive SVG service topology graph, log ingestion workflow, and real-time analysis details.
- Comprehensive test suite covering log parsing, topology discovery, security role enforcement, and HTTP boundaries.
