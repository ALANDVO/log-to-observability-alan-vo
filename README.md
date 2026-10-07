# log-to-observability-alan-vo

> AI log-to-observability pipeline: takes raw logs, auto-detects the service architecture, and generates Grafana dashboard JSON, alert rules, and SLO definitions based on LLM analysis of log patterns.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-React-3178C6)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![SSO](https://img.shields.io/badge/SSO-SAML%20%2F%20OAuth2-8A2BE2)
![License](https://img.shields.io/badge/License-MIT-green)
![AI](https://img.shields.io/badge/AI-Powered-purple)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

</div>

## Why log-to-observability-alan-vo?

AI log-to-observability pipeline: takes raw logs, auto-detects the service architecture, and generates Grafana dashboard JSON, alert rules, and SLO definitions based on LLM analysis of log patterns.

Built by [Alan Vo](https://github.com/ALANDVO) — AI/ML & cybersecurity engineer.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     log-to-observability-alan-vo                                    │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│  Frontend   │   API Layer │  Services   │   LLM Engine      │
│  React/TS   │  FastAPI    │  Domain     │  Multi-provider   │
│  Dashboard  │  SSO/SAML   │  Logic      │  OpenAI/Claude/   │
│  Real-time  │  JWT Auth   │  Processing │  Gemini/Ollama    │
└─────────────┴─────────────┴─────────────┴───────────────────┘
         │              │              │               │
         ▼              ▼              ▼               ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────┐
    │ Browser │   │  REST   │   │  Domain │   │  LLM API    │
    │  SPA    │   │  API    │   │  Logic  │   │  (any)      │
    └─────────┘   └─────────┘   └─────────┘   └─────────────┘
```

## Features

- **Architecture auto-detection — LLM infers services, tiers, and topology from log patterns**
- **Metric extraction: identifies which log signals map to RED/USE metrics**
- **Grafana dashboard JSON generation, ready to import (panels, queries, layout)**
- **Alert rules in Prometheus/Alertmanager format with LLM-written descriptions**
- **SLO definitions: availability, latency, and error-budget burn-rate alerts**
- **Log-to-metric mapping table — every alert traces back to a concrete log pattern**
- **Multi-format input: JSON lines, syslog, nginx, Docker/K8s logs**

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/ALANDVO/log-to-observability-alan-vo.git
cd log-to-observability-alan-vo
cp .env.example .env
docker compose up -d
# Open http://localhost:3000
```

### Local Development

```bash
git clone https://github.com/ALANDVO/log-to-observability-alan-vo.git
cd log-to-observability-alan-vo
pip install -r requirements.txt
```

## Usage

```
python main.py detect --logs access.log
python main.py dashboard --logs app.jsonl --output dashboards.json
python main.py slo --logs app.jsonl --service api-gateway --budget 99.9
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_KEY` | LLM API key (OpenAI, Anthropic, Gemini) | Required |
| `LLM_BASE_URL` | Custom LLM endpoint (Ollama, vLLM) | `https://api.openai.com/v1` |
| `LLM_MODEL` | Model name | `gpt-4o` |
| `SAML_IDP_ENTITY` | SAML Identity Provider URL | — |
| `JWT_SECRET` | JWT signing secret | Generate one |

## Tech Stack

`Python` `OpenAI/Anthropic/Gemini` `Grafana` `Prometheus` `SLO/error budget`

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login (SSO or email) |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/stats` | Statistics & metrics |
| `POST` | `/api/process` | Main processing endpoint |
| `GET` | `/api/results` | Query results |

## SSO Setup

### SAML
1. Set `SAML_IDP_ENTITY` to your IdP URL
2. Set `SAML_IDP_CERT` to your IdP certificate
3. Set `SAML_ACS_URL` to `https://yourdomain.com/saml/acs`

### OAuth2
1. Register your app with the OAuth provider
2. Set `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET`
3. Set `OAUTH_REDIRECT_URI`

## License

MIT — see [LICENSE](LICENSE)

---

**Built by [Alan Vo](https://github.com/ALANDVO)** | alanvo@gmail.com | AI, ML & Cybersecurity


