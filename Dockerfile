# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────
#  WanderAI v2.0 — Multi-stage Dockerfile
# ─────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r wanderai && useradd -r -g wanderai wanderai

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=wanderai:wanderai . .

USER wanderai

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

# Production command
CMD ["gunicorn", "wsgi:application", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "2", \
     "--bind", "0.0.0.0:5000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--timeout", "120"]
