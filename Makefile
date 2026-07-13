.PHONY: help install dev test lint format security build up down clean migrate seed-rag

# ─── Help ────────────────────────────────────────────────────
help:
	@echo "WanderAI v2.0 — Makefile shortcuts"
	@echo ""
	@echo "  make install       Install Python dependencies"
	@echo "  make dev           Start development server"
	@echo "  make up            Start full Docker stack"
	@echo "  make down          Stop Docker stack"
	@echo "  make test          Run test suite"
	@echo "  make lint          Run linter"
	@echo "  make format        Auto-format code"
	@echo "  make security      Run security scans"
	@echo "  make migrate       Run database migrations"
	@echo "  make seed-rag      Ingest knowledge base into Qdrant"
	@echo "  make clean         Remove cache files"

# ─── Setup ───────────────────────────────────────────────────
install:
	pip install -r requirements.txt -r requirements-dev.txt

# ─── Development ─────────────────────────────────────────────
dev:
	FLASK_ENV=development python app.py

# ─── Docker ──────────────────────────────────────────────────
up:
	docker-compose up --build

down:
	docker-compose down

up-api:
	docker-compose up postgres redis qdrant api

# ─── Database ────────────────────────────────────────────────
migrate:
	flask db upgrade

migrate-new:
	flask db migrate -m "$(msg)"

migrate-down:
	flask db downgrade

# ─── RAG ─────────────────────────────────────────────────────
seed-rag:
	flask rag ingest

# ─── Tests ───────────────────────────────────────────────────
test:
	pytest tests/ -v --cov=wanderai --cov-report=term-missing

test-fast:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-load:
	locust -f tests/load/locustfile.py --host=http://localhost:5000

# ─── Code Quality ────────────────────────────────────────────
lint:
	ruff check .

format:
	black .
	ruff check --fix .

security:
	bandit -r wanderai/ -ll
	safety check -r requirements.txt

# ─── Cleanup ─────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name ".coverage" -delete
	rm -rf .pytest_cache htmlcov dist build
