# WanderAI — Production Engineering Blueprint
# From 50/100 Portfolio App → 90+/100 Production-Grade AI Platform

**Version:** 1.0  
**Author:** Principal Engineering Blueprint  
**Project:** AI-TRAVEL-PLANNER-AGENT  
**Target Stack:** Flask · LangGraph · LiteLLM · PostgreSQL · Redis · Qdrant · Celery · Docker

---

## Top-Level Overview

This blueprint transforms the current single-file Flask app (`app.py`, ~530 lines, no DB, no auth, no tests, no observability) into a production-grade, modular, cloud-native AI SaaS platform. The approach is **incremental and phased** — the existing app continues running while each layer is added. Every section below maps directly to implementable code changes.

**Guiding principles:**
- Stateless API layer (horizontal scaling ready)
- Separation of concerns at every layer
- Security by default, not by addition
- Observability built-in, not bolted-on
- AI pipeline as a first-class engineering concern
- Zero vendor lock-in via abstraction layers

---

## Phase Overview

| Phase | Sections | Goal |
|-------|----------|------|
| **Phase 1** | 2, 3, 11 | Modular architecture + PostgreSQL + REST API redesign |
| **Phase 2** | 4, 13 | Auth (JWT + OAuth) + Security hardening |
| **Phase 3** | 5, 6, 7, 8 | AI pipeline + Multi-agent + Tool calling + RAG |
| **Phase 4** | 9, 10 | Redis caching + Celery background jobs |
| **Phase 5** | 14, 15 | Observability + Testing |
| **Phase 6** | 12, 16 | Frontend improvements + DevOps/CI-CD |
| **Phase 7** | 17, 18, 19, 20 | Scalability + Cost + Readiness + Resume |

---

## Sub-Task 1: Project Scaffold & Modular Architecture
**Status:** [ ] pending

### Intent
Replace the single `app.py` with a clean, industry-standard Flask application factory pattern. This is the foundation every other sub-task builds on.

### Expected Outcomes
- New folder structure exists with all `__init__.py` files
- `app.py` becomes a thin entry point (< 20 lines)
- Application factory `create_app()` in `wanderai/app.py`
- Configuration class hierarchy in `wanderai/config/`
- All existing routes preserved and working

### Folder Structure
```
AI-TRAVEL-PLANNER-AGENT/
├── app.py                          # Entry point only — calls create_app()
├── wsgi.py                         # Gunicorn WSGI entry point
├── requirements.txt                # Updated with all new deps
├── requirements-dev.txt            # Dev/test dependencies
├── .env.example                    # Updated env template
├── .env                            # Local secrets (gitignored)
├── docker-compose.yml              # Local dev stack
├── docker-compose.prod.yml         # Production stack
├── Dockerfile                      # App container
├── Makefile                        # Dev shortcuts
├── alembic.ini                     # DB migrations config
├── pytest.ini                      # Test configuration
├── .github/
│   └── workflows/
│       ├── ci.yml                  # CI pipeline
│       └── deploy.yml              # CD pipeline
│
├── wanderai/                       # Main application package
│   ├── __init__.py
│   ├── app.py                      # create_app() factory
│   │
│   ├── config/                     # Configuration classes
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseConfig
│   │   ├── development.py          # DevelopmentConfig
│   │   ├── production.py           # ProductionConfig
│   │   └── testing.py              # TestingConfig
│   │
│   ├── extensions.py               # Flask extensions (db, redis, celery, etc.)
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py                 # User, Role, Permission
│   │   ├── trip.py                 # Trip, Destination, Itinerary
│   │   ├── conversation.py         # Conversation, Message
│   │   ├── budget.py               # Budget, BudgetItem
│   │   ├── recommendation.py       # Recommendation
│   │   ├── preference.py           # UserPreference
│   │   ├── feedback.py             # Feedback
│   │   ├── audit.py                # AuditLog
│   │   └── session.py              # UserSession (device sessions)
│   │
│   ├── schemas/                    # Marshmallow/Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── auth.py                 # LoginSchema, RegisterSchema, TokenSchema
│   │   ├── trip.py                 # TripSchema, ItinerarySchema
│   │   ├── chat.py                 # ChatMessageSchema, ChatHistorySchema
│   │   ├── budget.py               # BudgetRequestSchema, BudgetResponseSchema
│   │   ├── profile.py              # ProfileSchema
│   │   └── common.py               # PaginationSchema, ErrorSchema
│   │
│   ├── routes/                     # Flask Blueprints
│   │   ├── __init__.py
│   │   ├── pages.py                # Page routes (GET /)
│   │   ├── auth.py                 # /api/v1/auth/*
│   │   ├── chat.py                 # /api/v1/chat/*
│   │   ├── trips.py                # /api/v1/trips/*
│   │   ├── itinerary.py            # /api/v1/itinerary/*
│   │   ├── budget.py               # /api/v1/budget/*
│   │   ├── recommendations.py      # /api/v1/recommendations/*
│   │   ├── profile.py              # /api/v1/profile/*
│   │   ├── weather.py              # /api/v1/weather/*
│   │   └── health.py               # /api/v1/health
│   │
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Auth business logic
│   │   ├── trip_service.py         # Trip CRUD + orchestration
│   │   ├── itinerary_service.py    # Itinerary generation
│   │   ├── budget_service.py       # Budget generation
│   │   ├── recommendation_service.py
│   │   ├── weather_service.py
│   │   ├── profile_service.py
│   │   └── email_service.py        # Email sending
│   │
│   ├── repositories/               # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseRepository with CRUD
│   │   ├── user_repository.py
│   │   ├── trip_repository.py
│   │   ├── conversation_repository.py
│   │   └── session_repository.py
│   │
│   ├── ai/                         # AI/LLM layer
│   │   ├── __init__.py
│   │   ├── client.py               # LiteLLM model-agnostic client
│   │   ├── pipeline.py             # Main AI pipeline orchestrator
│   │   ├── memory.py               # Conversation memory manager
│   │   ├── context_manager.py      # Context window manager
│   │   ├── output_validator.py     # Output validation + retry
│   │   ├── response_formatter.py   # Structured output formatter
│   │   ├── model_router.py         # Model selection logic
│   │   │
│   │   ├── prompts/                # Prompt templates (versioned)
│   │   │   ├── __init__.py
│   │   │   ├── registry.py         # Prompt version registry
│   │   │   ├── system.py           # System prompt builder
│   │   │   ├── itinerary.py        # Itinerary prompt templates
│   │   │   ├── budget.py           # Budget prompt templates
│   │   │   ├── weather.py          # Weather prompt templates
│   │   │   └── safety.py           # Safety prompt templates
│   │   │
│   │   ├── agents/                 # LangGraph multi-agent system
│   │   │   ├── __init__.py
│   │   │   ├── graph.py            # LangGraph state machine
│   │   │   ├── state.py            # TravelState dataclass
│   │   │   ├── coordinator.py      # Coordinator agent node
│   │   │   ├── planner.py          # Planner agent node
│   │   │   ├── destination.py      # Destination agent node
│   │   │   ├── budget_agent.py     # Budget agent node
│   │   │   ├── weather_agent.py    # Weather agent node
│   │   │   ├── safety_agent.py     # Safety agent node
│   │   │   ├── packing_agent.py    # Packing agent node
│   │   │   └── reviewer.py         # Reviewer/critic agent node
│   │   │
│   │   ├── tools/                  # LangGraph tool nodes
│   │   │   ├── __init__.py
│   │   │   ├── registry.py         # Tool registry
│   │   │   ├── weather_tool.py     # OpenWeatherMap/WeatherAPI
│   │   │   ├── currency_tool.py    # Exchange rate API
│   │   │   ├── places_tool.py      # Google Places / Foursquare
│   │   │   ├── timezone_tool.py    # Timezone lookup
│   │   │   └── visa_tool.py        # Visa requirements lookup
│   │   │
│   │   └── rag/                    # RAG system
│   │       ├── __init__.py
│   │       ├── ingestion.py        # Document ingestion pipeline
│   │       ├── chunker.py          # Text chunking strategies
│   │       ├── embedder.py         # Embedding generation
│   │       ├── retriever.py        # Qdrant vector retrieval
│   │       └── knowledge_base/     # Raw knowledge documents
│   │           ├── travel_guides/
│   │           ├── visa_rules/
│   │           ├── safety/
│   │           └── faqs/
│   │
│   ├── middleware/                 # WSGI/Flask middleware
│   │   ├── __init__.py
│   │   ├── correlation_id.py       # Request correlation IDs
│   │   ├── rate_limiter.py         # Rate limiting
│   │   ├── request_validator.py    # Request size/type validation
│   │   ├── security_headers.py     # Security HTTP headers
│   │   └── audit_logger.py         # Request audit logging
│   │
│   ├── utils/                      # Shared utilities
│   │   ├── __init__.py
│   │   ├── security.py             # Password hashing, token gen
│   │   ├── pagination.py           # Pagination helpers
│   │   ├── cache_keys.py           # Redis cache key builders
│   │   ├── validators.py           # Input validators
│   │   └── response.py             # Standardized API responses
│   │
│   ├── tasks/                      # Celery background tasks
│   │   ├── __init__.py
│   │   ├── itinerary_tasks.py      # Async itinerary generation
│   │   ├── email_tasks.py          # Email delivery
│   │   ├── pdf_tasks.py            # PDF generation
│   │   ├── weather_tasks.py        # Weather cache refresh
│   │   ├── analytics_tasks.py      # Analytics aggregation
│   │   └── cleanup_tasks.py        # DB/cache cleanup
│   │
│   └── observability/             # Logging + metrics + tracing
│       ├── __init__.py
│       ├── logger.py               # Structured JSON logger
│       ├── metrics.py              # Prometheus metrics
│       ├── tracing.py              # OpenTelemetry tracing
│       └── health.py               # Health check logic
│
├── migrations/                     # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
└── tests/                          # Test suite
    ├── __init__.py
    ├── conftest.py                 # Pytest fixtures
    ├── unit/
    │   ├── test_ai_pipeline.py
    │   ├── test_prompt_builder.py
    │   ├── test_validators.py
    │   └── test_repositories.py
    ├── integration/
    │   ├── test_auth_routes.py
    │   ├── test_chat_routes.py
    │   ├── test_trip_routes.py
    │   └── test_health.py
    ├── e2e/
    │   └── test_full_trip_flow.py
    └── fixtures/
        ├── users.json
        └── trips.json
```

### Todo List
1. Create all directories and `__init__.py` files
2. Create `wanderai/config/` with BaseConfig, DevelopmentConfig, ProductionConfig, TestingConfig
3. Create `wanderai/extensions.py` (db, redis, celery, limiter, cors, jwt singletons)
4. Create `wanderai/app.py` with `create_app(config_name)` factory
5. Create `wsgi.py` entry point
6. Move and refactor entry point `app.py` to thin launcher
7. Create `Makefile` with dev shortcuts
8. Update `requirements.txt` with all new dependencies

### Relevant Context
- Current: `app.py` lines 93–96 initialize Flask directly
- Pattern: Flask application factory is the industry standard for testability and multiple configs
- All existing routes will be moved to `wanderai/routes/` blueprints in Sub-Task 3

---

## Sub-Task 2: Database Models & PostgreSQL Setup
**Status:** [ ] pending

### Intent
Replace Flask session-based state with a proper PostgreSQL schema. All trip data, user profiles, chat history, and audit logs persist to DB.

### Expected Outcomes
- All SQLAlchemy models created with proper relationships
- Alembic migrations initialized and first migration created
- Repository pattern implemented for all data access
- No direct DB queries in routes or services

### Database Schema Design

```
users
├── id (UUID PK)
├── email (unique, indexed)
├── username (unique, indexed)
├── password_hash (nullable — OAuth users have no password)
├── email_verified (bool)
├── is_active (bool)
├── role (enum: user, premium, admin)
├── provider (enum: local, google, github)
├── provider_id (nullable)
├── avatar_url (nullable)
├── created_at, updated_at

user_sessions (device sessions for JWT revocation)
├── id (UUID PK)
├── user_id (FK → users)
├── token_jti (JWT ID, indexed)
├── device_info (text)
├── ip_address
├── is_active (bool)
├── expires_at, created_at

user_preferences
├── id (UUID PK)
├── user_id (FK → users, unique)
├── budget_tier (enum: budget, mid, luxury)
├── trip_style (array of strings)
├── dietary (array of strings)
├── home_country, passport_country
├── preferred_transport, preferred_accommodation
├── dream_destinations (array)
├── notes (text)
├── updated_at

trips
├── id (UUID PK)
├── user_id (FK → users, indexed)
├── title
├── destination
├── country_code
├── start_date, end_date (nullable)
├── days (int)
├── travelers (int)
├── budget_tier (enum)
├── total_budget (numeric)
├── currency
├── status (enum: draft, planned, active, completed, archived)
├── created_at, updated_at

itineraries
├── id (UUID PK)
├── trip_id (FK → trips, unique)
├── raw_text (text — AI output)
├── structured_json (jsonb — parsed structure)
├── model_used
├── prompt_version
├── generation_time_ms (int)
├── created_at, updated_at

conversations
├── id (UUID PK)
├── user_id (FK → users, indexed)
├── trip_id (FK → trips, nullable)
├── context_mode (enum: general, itinerary, budget)
├── title (auto-generated)
├── created_at, updated_at

messages
├── id (UUID PK)
├── conversation_id (FK → conversations, indexed)
├── role (enum: user, assistant, system)
├── content (text)
├── model_used (nullable)
├── tokens_used (int, nullable)
├── latency_ms (int, nullable)
├── created_at

budgets
├── id (UUID PK)
├── trip_id (FK → trips, unique)
├── raw_text (text)
├── total_amount (numeric)
├── currency
├── breakdown (jsonb)
├── created_at, updated_at

recommendations
├── id (UUID PK)
├── user_id (FK → users, indexed)
├── interests (array)
├── budget_tier
├── season
├── raw_text (text)
├── structured_json (jsonb)
├── created_at

feedback
├── id (UUID PK)
├── user_id (FK → users, nullable)
├── entity_type (enum: itinerary, budget, recommendation, message)
├── entity_id (UUID)
├── rating (1–5)
├── comment (text, nullable)
├── created_at

audit_logs
├── id (UUID PK)
├── user_id (FK → users, nullable)
├── action (string, indexed)
├── entity_type, entity_id
├── metadata (jsonb)
├── ip_address
├── user_agent
├── created_at (indexed)
```

### Indexing Strategy
- `users.email` — unique index (login lookup)
- `users.provider, provider_id` — composite index (OAuth lookup)
- `user_sessions.token_jti` — unique index (JWT revocation check)
- `trips.user_id` — index (user's trips list)
- `trips.user_id, status` — composite (filter by status)
- `messages.conversation_id` — index (conversation history)
- `messages.created_at` — index (time-ordered retrieval)
- `audit_logs.user_id, created_at` — composite (user audit trail)
- `audit_logs.action` — index (action-based queries)

### Todo List
1. Install SQLAlchemy, psycopg2-binary, alembic, flask-sqlalchemy
2. Create all model files in `wanderai/models/`
3. Create `wanderai/repositories/base.py` with generic CRUD
4. Create all repository files
5. Run `alembic init migrations`
6. Configure `alembic/env.py` to use app models
7. Generate initial migration: `alembic revision --autogenerate -m "initial_schema"`
8. Add DB connection to `extensions.py`

### Relevant Context
- Replace: `session["trip_data"]` and `session["user_profile"]` in current `app.py`
- All session reads/writes become repository calls

---

## Sub-Task 3: REST API Redesign with Blueprints
**Status:** [ ] pending

### Intent
Refactor all 8 API endpoints into versioned, validated, paginated REST endpoints following OpenAPI standards.

### Expected Outcomes
- All routes in `wanderai/routes/` as Flask Blueprints
- URL prefix: `/api/v1/`
- Pydantic validation on all request bodies
- Standardized response envelope: `{success, data, error, meta}`
- OpenAPI/Swagger docs at `/api/v1/docs`
- HTTP status codes correct for all scenarios

### New API Surface

```
GET  /api/v1/health                     — Health + readiness
GET  /api/v1/health/ready               — Readiness check (DB + Redis + AI)

POST /api/v1/auth/register              — Email/password registration
POST /api/v1/auth/login                 — Login → JWT + refresh token
POST /api/v1/auth/refresh               — Refresh access token
POST /api/v1/auth/logout                — Revoke session
POST /api/v1/auth/google                — Google OAuth callback
POST /api/v1/auth/github                — GitHub OAuth callback
POST /api/v1/auth/verify-email          — Email verification
POST /api/v1/auth/forgot-password       — Send reset email
POST /api/v1/auth/reset-password        — Reset with token

GET  /api/v1/trips                      — List user's trips (paginated)
POST /api/v1/trips                      — Create trip
GET  /api/v1/trips/{id}                 — Get trip detail
PUT  /api/v1/trips/{id}                 — Update trip
DELETE /api/v1/trips/{id}              — Delete trip

POST /api/v1/itinerary                  — Generate itinerary (async task)
GET  /api/v1/itinerary/status/{task_id} — Poll task status
GET  /api/v1/trips/{id}/itinerary       — Get saved itinerary

POST /api/v1/conversations              — Create conversation
GET  /api/v1/conversations              — List conversations (paginated)
GET  /api/v1/conversations/{id}/messages — Get messages (paginated)
POST /api/v1/conversations/{id}/messages — Send message

POST /api/v1/budget                     — Generate budget plan
POST /api/v1/recommendations            — Get destination recommendations
POST /api/v1/weather                    — Get weather advice

GET  /api/v1/profile                    — Get profile + preferences
PUT  /api/v1/profile                    — Update profile
PUT  /api/v1/profile/preferences        — Update preferences

GET  /api/v1/admin/users               — List users (admin only)
GET  /api/v1/admin/stats               — Platform statistics
```

### Response Envelope
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "correlation_id": "abc-123"
  },
  "error": null
}
```

### Todo List
1. Create `wanderai/utils/response.py` with `APIResponse` builder
2. Create all Blueprint files in `wanderai/routes/`
3. Register blueprints with `/api/v1` prefix in `create_app()`
4. Create Pydantic schemas in `wanderai/schemas/`
5. Add Flask-RESTX or Flasgger for OpenAPI docs
6. Write `wanderai/utils/pagination.py`

---

## Sub-Task 4: Authentication & Authorization
**Status:** [ ] pending

### Intent
Implement production-grade JWT auth with Google + GitHub OAuth, RBAC, refresh token rotation, and session revocation.

### Expected Outcomes
- JWT access tokens (15 min expiry) + refresh tokens (30 day expiry)
- Google OAuth and GitHub OAuth working
- Password hashing with bcrypt
- Email verification flow
- Role-based access: `user`, `premium`, `admin`
- All protected routes require valid JWT
- Rate limiting on auth endpoints
- Multi-device session tracking with revocation

### Auth Flow
```
Register → Hash password (bcrypt, cost=12) → Create user → Send verify email
         → User clicks link → Set email_verified=True → Allow login

Login → Verify password → Create JWT (15min) + Refresh token (30d)
      → Store session in user_sessions → Return both tokens

Protected Request → Extract Bearer token → Verify signature → Check JTI not revoked
                  → Check email verified → Decode claims → Inject g.current_user

Token Refresh → Verify refresh token → Check session active → Rotate: new access + refresh
              → Invalidate old refresh JTI → Return new pair

Logout → Extract JTI from token → Set user_sessions.is_active=False

OAuth → Redirect to Google/GitHub → Callback with code → Exchange for user info
      → Find or create user (provider=google/github) → Issue JWT pair
```

### RBAC Design
```python
class Permission(Enum):
    READ_OWN_DATA = "read:own"
    WRITE_OWN_DATA = "write:own"
    READ_ANY_DATA = "read:any"   # admin
    WRITE_ANY_DATA = "write:any" # admin
    GENERATE_AI = "ai:generate"
    EXPORT_PDF = "export:pdf"    # premium+

ROLE_PERMISSIONS = {
    "user":    [READ_OWN_DATA, WRITE_OWN_DATA, GENERATE_AI],
    "premium": [READ_OWN_DATA, WRITE_OWN_DATA, GENERATE_AI, EXPORT_PDF],
    "admin":   [ALL],
}
```

### Todo List
1. Install flask-jwt-extended, authlib, bcrypt, flask-limiter
2. Create `wanderai/utils/security.py` (password hash, token gen)
3. Create `wanderai/models/user.py` with roles
4. Create `wanderai/routes/auth.py` with all auth endpoints
5. Create `wanderai/services/auth_service.py`
6. Configure JWT settings in config classes
7. Create `wanderai/middleware/rate_limiter.py`
8. Create `require_auth` and `require_role` decorators
9. Add `wanderai/services/email_service.py` (verification, reset)

---

## Sub-Task 5: AI Pipeline Redesign
**Status:** [ ] pending

### Intent
Replace the current direct `prompt → model.generate_text()` call with a proper AI pipeline: LiteLLM client, prompt versioning, output validation, retry logic, conversation memory, and model routing.

### Expected Outcomes
- LiteLLM wraps IBM watsonx.ai + any other provider via config
- `GRANITE_MODEL_ID` env var controls primary model
- Fallback chain: primary → secondary → error response
- All prompts in `wanderai/ai/prompts/` with version tracking
- Output validation rejects/retries malformed responses
- Conversation memory reads from DB (not browser sessionStorage)
- Token usage tracked per message

### AI Pipeline Stages
```
User Request
    │
    ▼
[1] ContextManager         — Load conversation history from DB (last N turns, fit within token budget)
    │
    ▼
[2] RAGRetriever            — Semantic search Qdrant for relevant travel knowledge
    │
    ▼
[3] PromptBuilder           — Select versioned template, inject context + RAG chunks
    │
    ▼
[4] ModelRouter             — Select model based on task type, user tier, load
    │
    ▼
[5] LiteLLMClient           — Call model (watsonx primary, OpenAI fallback)
    │
    ▼
[6] OutputValidator         — Check length, format, detect refusals, JSON validity
    │
    ▼ (retry up to 3x with modified prompt if invalid)
    │
    ▼
[7] ResponseFormatter       — Strip artifacts, render markdown, extract structured data
    │
    ▼
[8] MemoryWriter            — Save message pair to DB, update token counts
    │
    ▼
Formatted Response
```

### Prompt Versioning
Each prompt template has:
```python
@dataclass
class PromptTemplate:
    name: str           # "itinerary_v2"
    version: str        # "2.1.0"
    model_family: str   # "llama3" | "granite" | "generic"
    system: str         # system prompt text
    user_template: str  # Jinja2 template for user turn
    output_schema: dict # Expected JSON schema (optional)
```

### Todo List
1. Install litellm, langchain-core, tenacity (retry)
2. Create `wanderai/ai/client.py` — LiteLLM wrapper
3. Create `wanderai/ai/prompts/registry.py` — prompt registry
4. Create `wanderai/ai/prompts/system.py` — migrate AGENT_INSTRUCTIONS
5. Create `wanderai/ai/prompts/itinerary.py`, `budget.py`, `weather.py`
6. Create `wanderai/ai/memory.py` — DB-backed conversation memory
7. Create `wanderai/ai/context_manager.py` — token-aware context window
8. Create `wanderai/ai/output_validator.py` — retry logic
9. Create `wanderai/ai/model_router.py` — routing rules
10. Create `wanderai/ai/pipeline.py` — orchestrates stages 1–8

---

## Sub-Task 6: Multi-Agent System (LangGraph)
**Status:** [ ] pending

### Intent
Convert the single-call AI flow into a LangGraph multi-agent system where specialized agents handle different aspects of trip planning. The Coordinator routes user intent to the right agent(s), collects results, and produces a unified response.

### Expected Outcomes
- LangGraph `StateGraph` with typed `TravelState`
- 8 agent nodes (Coordinator, Planner, Destination, Budget, Weather, Safety, Packing, Reviewer)
- Conditional routing based on intent classification
- Parallel execution where agents are independent
- Reviewer agent critiques and refines output
- Full graph state persisted to DB

### Agent Responsibilities
```
CoordinatorAgent  — Classify intent, route to agents, merge results
PlannerAgent      — Multi-day itinerary structure and timing
DestinationAgent  — Destination research, attractions, local tips
BudgetAgent       — Cost estimation, budget breakdown, savings tips
WeatherAgent      — Climate advice, seasonal recommendations
SafetyAgent       — Travel advisories, emergency info, health requirements
PackingAgent      — Packing list based on climate + activities
ReviewerAgent     — Quality check, consistency, hallucination detection
```

### LangGraph State
```python
class TravelState(TypedDict):
    user_id: str
    conversation_id: str
    user_message: str
    intent: str              # classified by coordinator
    destination: str
    days: int
    budget_tier: str
    rag_context: list[str]   # from RAG retrieval
    agent_outputs: dict      # {agent_name: output}
    final_response: str
    errors: list[str]
    metadata: dict
```

### Execution Flow
```
User Message → CoordinatorAgent (intent classification)
    ├── intent=itinerary → PlannerAgent + DestinationAgent (parallel)
    │                    → BudgetAgent → SafetyAgent → PackingAgent
    │                    → ReviewerAgent → Final Response
    │
    ├── intent=budget    → BudgetAgent → ReviewerAgent → Final Response
    │
    ├── intent=weather   → WeatherAgent → Final Response
    │
    ├── intent=safety    → SafetyAgent → Final Response
    │
    └── intent=general   → DestinationAgent → Final Response
```

### Todo List
1. Install langgraph, langchain-core
2. Create `wanderai/ai/agents/state.py` — TravelState TypedDict
3. Create all agent node files
4. Create `wanderai/ai/agents/graph.py` — compile StateGraph
5. Wire agent graph into `wanderai/ai/pipeline.py`
6. Add intent classification to CoordinatorAgent

---

## Sub-Task 7: Tool Calling
**Status:** [ ] pending

### Intent
Give agents access to real-world data via tool functions. Tools are Python functions decorated with LangGraph's tool protocol, cached in Redis, with input validation and graceful fallbacks.

### Expected Outcomes
- 5 tools implemented: weather, currency, places, timezone, visa
- All tool outputs Redis-cached with appropriate TTL
- Tool failures return structured fallback data (never crash agent)
- Tool inputs validated with Pydantic models

### Tool Specifications
```
WeatherTool       — OpenWeatherMap API, TTL: 1 hour
CurrencyTool      — exchangerate.host (free), TTL: 6 hours
PlacesTool        — Foursquare Places API (free tier), TTL: 24 hours
TimezoneTool      — timezondb.com or pytz lookup, TTL: 7 days
VisaTool          — travelbriefing.org or static KB, TTL: 24 hours
```

### Todo List
1. Create `wanderai/ai/tools/registry.py` — tool registry
2. Create each tool file with Pydantic input/output models
3. Add tool caching layer using Redis
4. Register tools with LangGraph tool executor
5. Add tool API keys to `.env.example`

---

## Sub-Task 8: RAG System (Qdrant)
**Status:** [ ] pending

### Intent
Add a vector knowledge base that gives agents access to curated travel guides, visa rules, safety data, and FAQs. RAG context is injected into every prompt to ground responses in factual data.

### Expected Outcomes
- Qdrant running in Docker
- Knowledge base documents ingested and indexed
- Semantic search returns top-k relevant chunks per query
- RAG context injected into AI pipeline stage 2
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (free, fast)

### RAG Pipeline
```
Ingestion:
  Raw docs → Chunker (512 tokens, 50 overlap) → Embedder → Qdrant upsert

Retrieval:
  User query → Embed query → Qdrant search (top 5, score > 0.7)
  → Re-rank by metadata (destination match) → Return chunks

Prompt Injection:
  system_prompt += "\n\nRELEVANT KNOWLEDGE:\n" + "\n---\n".join(chunks)
```

### Knowledge Base Documents (initial set)
- `travel_guides/` — 50 popular destination guides (markdown)
- `visa_rules/` — Visa requirements by country pair (markdown)
- `safety/` — Country safety ratings and advisories (markdown)
- `faqs/` — Common travel questions and answers (markdown)

### Todo List
1. Add Qdrant to docker-compose.yml
2. Install qdrant-client, sentence-transformers
3. Create `wanderai/ai/rag/chunker.py`
4. Create `wanderai/ai/rag/embedder.py`
5. Create `wanderai/ai/rag/retriever.py`
6. Create `wanderai/ai/rag/ingestion.py`
7. Write seed knowledge base documents
8. Create CLI command: `flask rag ingest`
9. Wire retriever into AI pipeline stage 2

---

## Sub-Task 9: Redis Caching
**Status:** [ ] pending

### Intent
Add Redis for LLM response caching, session tokens, rate limit counters, and tool output caching. Redis eliminates redundant LLM calls for identical requests.

### Expected Outcomes
- Redis in Docker
- LLM responses cached by prompt hash (TTL: 1 hour)
- Tool outputs cached with per-tool TTL
- Rate limit counters stored in Redis
- Cache hit rate tracked as Prometheus metric

### Cache Key Schema
```
llm:{sha256(prompt_hash)}               TTL: 3600s
weather:{destination}:{month}           TTL: 3600s
currency:{from}:{to}                    TTL: 21600s
places:{destination}:{category}         TTL: 86400s
ratelimit:{user_id}:{endpoint}          TTL: 60s
session:{jti}                           TTL: match JWT expiry
rag_embedding:{text_hash}              TTL: 86400s
```

### Todo List
1. Add Redis to docker-compose.yml
2. Install redis-py, flask-caching
3. Create `wanderai/utils/cache_keys.py`
4. Create `wanderai/extensions.py` Redis client
5. Add cache decorator to AI pipeline
6. Add cache warming on startup for popular destinations

---

## Sub-Task 10: Celery Background Jobs
**Status:** [ ] pending

### Intent
Move slow AI operations (itinerary generation: ~5-15s) to async Celery tasks. Users get immediate task ID, poll for completion. Add scheduled jobs for cache warming and cleanup.

### Expected Outcomes
- Celery worker running in Docker
- Itinerary generation returns `task_id` immediately
- Frontend polls `/api/v1/itinerary/status/{task_id}`
- PDF generation task
- Email tasks (verify, reset, welcome)
- Scheduled: weather cache refresh every hour, cleanup nightly

### Task Definitions
```python
# wanderai/tasks/itinerary_tasks.py
@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def generate_itinerary_task(self, trip_id: str, user_id: str) -> dict:
    ...

# wanderai/tasks/email_tasks.py
@celery.task(bind=True, max_retries=5)
def send_verification_email(self, user_id: str) -> None:
    ...

# Scheduled (Celery Beat)
CELERYBEAT_SCHEDULE = {
    "refresh-weather-cache": {
        "task": "wanderai.tasks.weather_tasks.refresh_popular_weather",
        "schedule": crontab(minute=0),  # every hour
    },
    "cleanup-expired-sessions": {
        "task": "wanderai.tasks.cleanup_tasks.expire_old_sessions",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

### Todo List
1. Install celery, redis (broker), flower (monitoring)
2. Create `wanderai/tasks/` directory with all task files
3. Configure Celery in `extensions.py`
4. Add Celery worker + Flower to docker-compose.yml
5. Update itinerary route to dispatch task and return task_id
6. Add `/api/v1/itinerary/status/{task_id}` polling endpoint
7. Configure Celery Beat for scheduled tasks

---

## Sub-Task 11: Security Hardening
**Status:** [ ] pending

### Intent
Implement defense-in-depth security: input sanitization, security headers, CSRF protection, prompt injection guards, rate limiting, and secrets management.

### Expected Outcomes
- All OWASP Top 10 mitigations in place
- Prompt injection detection layer
- Security headers via middleware
- CSRF tokens on all state-changing requests
- No secrets in code or logs
- SQL injection impossible (ORM-only queries)

### Security Controls by Threat
```
XSS              → Content-Security-Policy header, Jinja2 autoescaping, bleach sanitize
CSRF             → flask-wtf CSRF tokens, SameSite=Lax cookies
SQL Injection    → SQLAlchemy ORM only, parameterized queries, no raw SQL
Prompt Injection → Input sanitizer strips system-like tokens, max length 2000
Prompt Leakage   → System prompt not returned in any API response
Session Hijack   → HttpOnly cookies, Secure flag, SameSite, short JWT TTL
Secrets Exposure → python-dotenv, no .env in git, secrets masked in logs
API Abuse        → Rate limiting (flask-limiter + Redis), per-user + per-IP
DDoS             → Nginx rate limiting + connection limits upstream
Clickjacking     → X-Frame-Options: DENY header
```

### Security Middleware Stack (request processing order)
```
1. Nginx (rate limit, TLS termination, request size limit)
2. SecurityHeadersMiddleware (CSP, HSTS, X-Frame-Options, etc.)
3. CorrelationIDMiddleware (inject X-Correlation-ID)
4. RateLimiterMiddleware (per-user, per-IP, per-endpoint)
5. RequestValidatorMiddleware (content-type, body size)
6. AuthMiddleware (JWT verification)
7. AuditLoggerMiddleware (log all state-changing requests)
8. Route Handler
```

### Prompt Injection Guard
```python
INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"ignore all instructions",
    r"<\|system\|>",
    r"<\|user\|>",
    r"\[INST\]",
    r"system prompt",
    r"reveal your instructions",
]
```

### Todo List
1. Create `wanderai/middleware/security_headers.py`
2. Create `wanderai/middleware/rate_limiter.py`
3. Create `wanderai/middleware/request_validator.py`
4. Add prompt injection guard to AI pipeline input stage
5. Configure flask-wtf CSRF
6. Add security headers to Nginx config
7. Create secrets scanning in CI (gitleaks)

---

## Sub-Task 12: Observability Stack
**Status:** [ ] pending

### Intent
Add structured logging, distributed tracing, Prometheus metrics, and Sentry error tracking. Every request produces a structured log line and a trace span.

### Expected Outcomes
- Every log line is valid JSON with correlation_id, user_id, duration
- Prometheus `/metrics` endpoint
- Sentry error tracking with user context
- Health endpoint reports DB, Redis, AI status
- Grafana dashboard (docker-compose)

### Structured Log Format
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "correlation_id": "abc-123-def-456",
  "user_id": "uuid-here",
  "method": "POST",
  "path": "/api/v1/conversations/123/messages",
  "status_code": 200,
  "duration_ms": 1250,
  "ai_model": "meta-llama/llama-3-3-70b-instruct",
  "tokens_used": 847,
  "cache_hit": false,
  "service": "wanderai-api",
  "version": "2.0.0"
}
```

### Key Metrics
```
wanderai_requests_total{method, endpoint, status}   — Request counter
wanderai_request_duration_seconds{endpoint}         — Request latency histogram
wanderai_ai_calls_total{model, status}              — AI call counter
wanderai_ai_duration_seconds{model}                 — AI call latency
wanderai_cache_hits_total{cache_type}               — Cache hit counter
wanderai_active_users_gauge                         — Active user gauge
wanderai_celery_tasks_total{task, status}           — Task counter
```

### Todo List
1. Install structlog, prometheus-flask-exporter, sentry-sdk, opentelemetry-sdk
2. Create `wanderai/observability/logger.py`
3. Create `wanderai/observability/metrics.py`
4. Create `wanderai/observability/tracing.py`
5. Create `wanderai/observability/health.py`
6. Add correlation ID middleware
7. Add Prometheus + Grafana to docker-compose.yml
8. Configure Sentry DSN in config

---

## Sub-Task 13: Testing Suite
**Status:** [ ] pending

### Intent
Implement a comprehensive testing strategy: unit tests for all AI pipeline components, integration tests for all API endpoints, and load tests for performance baselines.

### Expected Outcomes
- 80%+ code coverage enforced in CI
- All routes have integration tests
- AI pipeline has unit tests with mocked LLM
- Load test baseline: 100 concurrent users, p95 < 2s
- All tests pass in < 2 minutes

### Test Structure
```python
# tests/conftest.py — Fixtures
@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    # Create test user, login, return Bearer headers

@pytest.fixture
def mock_llm(mocker):
    # Mock LiteLLM calls to return fixture responses
```

### Todo List
1. Install pytest, pytest-flask, pytest-mock, pytest-cov, locust
2. Create `tests/conftest.py` with all fixtures
3. Write unit tests for AI pipeline (mocked LLM)
4. Write integration tests for all route files
5. Write load test `tests/load/locustfile.py`
6. Configure coverage thresholds in `pytest.ini`
7. Add test commands to Makefile

---

## Sub-Task 14: DevOps & CI/CD
**Status:** [ ] pending

### Intent
Create complete Docker setup for local development and production, plus GitHub Actions CI/CD pipeline with automated testing, security scanning, and deployment.

### Expected Outcomes
- `docker-compose up` starts full local stack (API, DB, Redis, Qdrant, Celery, Flower, Grafana)
- GitHub Actions runs on every PR: lint → test → security scan → build
- Deployment workflow pushes to registry and deploys
- Zero-downtime deployment via rolling update
- Environment-specific configs via environment variables

### docker-compose.yml Services
```yaml
services:
  api:          # Flask + Gunicorn
  worker:       # Celery worker
  beat:         # Celery beat scheduler
  flower:       # Celery monitoring
  postgres:     # PostgreSQL 16
  redis:        # Redis 7
  qdrant:       # Qdrant vector DB
  nginx:        # Reverse proxy
  prometheus:   # Metrics
  grafana:      # Dashboards
```

### CI Pipeline (.github/workflows/ci.yml)
```
on: [push, pull_request]
jobs:
  quality:   — ruff lint + black format check + mypy type check
  test:      — pytest with coverage, fail if < 80%
  security:  — bandit (SAST) + safety (dep scan) + gitleaks (secrets)
  build:     — docker build (verify image builds)
```

### CD Pipeline (.github/workflows/deploy.yml)
```
on: push to main
jobs:
  deploy:
    - Run full CI
    - Build and push Docker image to registry
    - Deploy with zero-downtime rolling update
    - Run smoke tests against production
    - Rollback if smoke tests fail
```

### Todo List
1. Create `Dockerfile` (multi-stage: builder + runtime)
2. Create `docker-compose.yml` (dev stack)
3. Create `docker-compose.prod.yml` (production overrides)
4. Create `nginx/nginx.conf`
5. Create `.github/workflows/ci.yml`
6. Create `.github/workflows/deploy.yml`
7. Create `Makefile` with shortcuts
8. Create `scripts/` for DB seed, health check, rollback

---

## Sub-Task 15: Frontend Improvements
**Status:** [ ] pending

### Intent
Upgrade the frontend with component-based organization, PWA manifest, accessibility improvements, real-time job polling UI, and charts for budget visualization.

### Expected Outcomes
- PWA manifest + service worker (offline page)
- Budget breakdown shown as Chart.js doughnut chart
- Itinerary generation shows async progress bar (polls task status)
- All forms have proper ARIA labels
- Trip list page showing saved trips
- Authentication pages (login, register)

### New Frontend Files
```
templates/
├── auth/
│   ├── login.html
│   └── register.html
├── trips/
│   ├── list.html       — Trip list with cards
│   └── detail.html     — Single trip view
└── components/         — Reusable Jinja2 macros
    ├── trip_card.html
    ├── message_bubble.html
    └── kpi_card.html

static/
├── js/
│   ├── auth.js         — Login/register forms
│   ├── trips.js        — Trip list management
│   ├── charts.js       — Chart.js budget visualization
│   └── pwa.js          — Service worker registration
├── manifest.json       — PWA manifest
└── sw.js              — Service worker
```

### Todo List
1. Create auth templates (login, register)
2. Create trips list template
3. Add Chart.js budget doughnut chart to budget.html
4. Add async progress polling to itinerary.html
5. Create PWA manifest.json and sw.js
6. Add ARIA labels to all form elements
7. Update base.html to include new nav items (Login/Profile)

---

## Sub-Task 16: Final Integration & Documentation
**Status:** [ ] pending

### Intent
Wire all sub-tasks together, verify the complete system works end-to-end, generate API documentation, and create the production deployment guide.

### Expected Outcomes
- Full system boots with `docker-compose up`
- All tests pass
- README updated with architecture, setup, and API docs
- ARCHITECTURE.md with system design document
- API docs at `/api/v1/docs`
- `.env.example` updated with all new variables

### Todo List
1. End-to-end integration test of full trip planning flow
2. Update README.md with new architecture
3. Create ARCHITECTURE.md
4. Update `.env.example` with all 30+ variables
5. Create `CONTRIBUTING.md`
6. Final security review of all endpoints
7. Performance test: verify p95 < 2s under 50 concurrent users

---

## Technology Decision Log

| Decision | Options Considered | Choice | Reason |
|----------|-------------------|--------|--------|
| AI Abstraction | LiteLLM vs LangChain vs custom | **LiteLLM** | Lightest, 100+ providers, drop-in |
| Agent Framework | LangGraph vs CrewAI vs AutoGen | **LangGraph** | Stateful graphs, production-proven, fine-grained control |
| Vector DB | Qdrant vs ChromaDB vs pgvector | **Qdrant** | Purpose-built, Docker-native, Rust performance |
| Task Queue | Celery vs RQ vs Dramatiq | **Celery + Redis** | Industry standard, best Flask integration |
| Auth | Custom vs Auth0 vs flask-jwt-extended | **flask-jwt-extended** | Full control, no vendor dependency, well-maintained |
| ORM | SQLAlchemy vs Tortoise vs raw SQL | **SQLAlchemy 2.0** | Industry standard for Python, excellent Flask integration |
| Validation | Pydantic vs Marshmallow vs cerberus | **Pydantic v2** | Fastest, best DX, used in FastAPI ecosystem |
| Logging | structlog vs loguru vs stdlib | **structlog** | JSON output, context vars, production-proven |
| Testing | pytest vs unittest | **pytest** | Universal Python standard, best fixture system |
| Embedding | OpenAI vs sentence-transformers | **sentence-transformers** | Free, local, no API cost, sufficient quality |

---

## Migration Roadmap

### Step 1 — Parallel (no user impact)
- Create new folder structure alongside existing `app.py`
- All new code in `wanderai/` package
- Existing `app.py` continues serving requests

### Step 2 — Database introduction
- Stand up PostgreSQL
- New features write to DB; old features still use session
- Run both state stores simultaneously

### Step 3 — Route migration
- Move routes to Blueprints one-by-one
- Keep `/api/` prefix identical (backward compatible)
- Old `app.py` routes removed as new ones confirmed working

### Step 4 — Auth addition
- Auth is purely additive
- Existing routes gain optional auth first, then required auth

### Step 5 — AI pipeline swap
- New AI pipeline produces identical outputs
- A/B test old vs new pipeline on 10% of traffic
- Full cutover once quality confirmed

### Step 6 — Session deprecation
- All session reads replaced by DB queries
- Flask session removed entirely

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LiteLLM watsonx adapter breaks | Low | High | Pin LiteLLM version, test adapter in CI |
| LangGraph adds latency | Medium | Medium | Measure baseline, optimize graph paths, cache coordinator decisions |
| Qdrant adds complexity to local dev | Low | Low | Single Docker container, simple client, health check |
| PostgreSQL migration data loss | Low | High | Keep session backup, migrate only new data, no destructive migrations |
| JWT secret rotation causes logouts | Low | Low | Graceful token refresh, inform users |
| Celery worker crashes | Medium | Medium | Supervisor/Docker restart policy, dead letter queue |

---

## Resume & Recruiter Impact Summary

| Section | Resume Keywords Added | Interview Topics Unlocked |
|---------|----------------------|--------------------------|
| Modular Architecture | Application factory pattern, Flask Blueprints, separation of concerns | "Walk me through your system design" |
| PostgreSQL + SQLAlchemy | Relational DB design, ORM, migrations, indexing strategy | "How did you model the data?" |
| JWT + OAuth | Auth flows, token rotation, RBAC, session management | "How does your auth work?" |
| LiteLLM + AI Pipeline | LLM abstraction, model routing, prompt engineering, output validation | "How do you handle AI reliability?" |
| LangGraph Agents | Multi-agent systems, state machines, orchestration | "What's your AI architecture?" |
| RAG + Qdrant | Vector databases, embeddings, semantic search, RAG pipeline | "How do you ground your AI responses?" |
| Redis Caching | Caching strategies, TTL, cache invalidation, cost optimization | "How do you handle scale?" |
| Celery | Async task processing, task queues, distributed workers | "How do you handle long-running tasks?" |
| Security | OWASP, JWT security, prompt injection, rate limiting | "How do you secure your API?" |
| Observability | Structured logging, Prometheus, distributed tracing | "How do you debug production issues?" |
| Testing | pytest, mocking, coverage, load testing | "What's your testing strategy?" |
| Docker + CI/CD | Containerization, GitHub Actions, zero-downtime deployment | "Walk me through your deployment" |
