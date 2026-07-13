# WanderAI v2.0 — AI-Powered Travel Planner

A **production-grade**, full-stack AI SaaS platform for intelligent travel planning.

Built on: **Flask** · **LangGraph** · **IBM watsonx.ai** · **PostgreSQL** · **Redis** · **Qdrant** · **Celery**

Live demo: https://ai-travel-planner-agent-maga.onrender.com

---

## 🏗️ Architecture

```
Browser → Nginx → Flask API (Gunicorn)
                      │
          ┌───────────┼───────────────┐
          │           │               │
       PostgreSQL    Redis          Qdrant
       (data)       (cache/queue)  (vector DB)
          │           │
       Celery Workers (background jobs)
          │
       IBM watsonx.ai / LangGraph Agents
```

## ⚡ Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd AI-TRAVEL-PLANNER-AGENT
cp .env.example .env  # fill in WATSONX_API_KEY, etc.

# 2. Start full stack with Docker
docker-compose up

# OR start only what you need
make up-api

# 3. Run DB migrations
make migrate

# 4. (Optional) Ingest knowledge base for RAG
make seed-rag

# 5. Open http://localhost:5000
```

## 🔑 Key Features vs v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Architecture | Single app.py (530 lines) | Modular package (25+ files) |
| Database | Flask session cookies | PostgreSQL + SQLAlchemy |
| Authentication | None | JWT + Google/GitHub OAuth + RBAC |
| AI Pipeline | Direct prompt → LLM | 8-stage pipeline with RAG |
| Multi-Agent | None | LangGraph (8 specialized agents) |
| Vector DB | None | Qdrant RAG system |
| Caching | None | Redis (LLM + tool responses) |
| Background Jobs | None | Celery + beat scheduler |
| Observability | print() | structlog + Prometheus + Sentry |
| Testing | None | pytest (unit + integration + load) |
| Security | Minimal | OWASP mitigations, prompt injection guard |
| Deployment | Single process | Docker Compose (10 services) |
| CI/CD | None | GitHub Actions (lint + test + deploy) |

## 📁 Structure

```
wanderai/
├── app.py              # create_app() factory
├── config/             # Environment-specific config
├── models/             # SQLAlchemy models (9 tables)
├── repositories/       # Data access layer
├── routes/             # Flask Blueprints (10 blueprints)
├── services/           # Business logic
├── ai/
│   ├── pipeline.py     # 8-stage AI pipeline
│   ├── agents/         # LangGraph multi-agent system
│   ├── prompts/        # Versioned prompt templates
│   ├── rag/            # Qdrant RAG system
│   └── tools/          # Weather, currency, places tools
├── tasks/              # Celery background tasks
├── middleware/         # Security headers, correlation IDs
├── observability/      # Structured logging, metrics, health
└── utils/              # Shared utilities
```

## 🔐 Security

- JWT access tokens (15-min TTL) + refresh tokens (30-day TTL)
- Prompt injection detection on all user inputs
- bcrypt password hashing (cost=12)
- Rate limiting per user + per IP
- Security headers (CSP, HSTS, X-Frame-Options)
- No secrets in code (`.env` loaded at startup)
- RBAC (user / premium / admin roles)

## 🤖 AI Architecture

```
User Input
  → Prompt Injection Guard
  → RAG Retrieval (Qdrant)
  → System Prompt Builder
  → LangGraph CoordinatorAgent
      ├── PlannerAgent    (itineraries)
      ├── BudgetAgent     (cost planning)
      ├── WeatherAgent    (climate advice)
      ├── SafetyAgent     (travel advisories)
      ├── DestinationAgent (recommendations)
      └── ReviewerAgent   (quality check)
  → Output Validator
  → Response Formatter
  → DB Persistence
```

## 🧪 Testing

```bash
make test              # full test suite with coverage
make test-fast         # unit tests only
make test-load         # locust load test
```

## 📊 API

All endpoints are at `/api/v1/` with standard envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": { "correlation_id": "...", "version": "2.0.0" }
}
```

See full API docs at `/api/v1/docs` when running locally.

## 🌐 Deployment

```bash
# Production with Gunicorn + 4 workers
gunicorn wsgi:application -w 4 -b 0.0.0.0:5000

# Docker production
docker-compose -f docker-compose.prod.yml up
```

## 🧩 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3.0, Gunicorn |
| AI/LLM | IBM watsonx.ai, LangGraph, LiteLLM-compatible |
| Database | PostgreSQL 16, SQLAlchemy 2.0, Alembic |
| Cache | Redis 7, Flask-Caching |
| Queue | Celery 5, Redis broker |
| Vector DB | Qdrant 1.9, sentence-transformers |
| Auth | Flask-JWT-Extended, Authlib (OAuth), bcrypt |
| Observability | structlog, Prometheus, Grafana, Sentry |
| Security | bleach, Flask-Limiter, Flask-WTF |
| DevOps | Docker, Docker Compose, GitHub Actions |

## 📄 License

MIT — free to use, modify, and distribute.
