# ──────────────────────────────────────────────
# Stage 1 — Builder
# ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ──────────────────────────────────────────────
# Stage 2 — Runtime
# ──────────────────────────────────────────────
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r alive && useradd --no-log-init -r -g alive alive

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local /usr/local

# Copy application code
COPY --chown=alive:alive backend/ backend/
COPY --chown=alive:alive scripts/ scripts/

# Create writable ChromaDB directory for the non-root user
RUN mkdir -p /app/chroma_db && chown -R alive:alive /app/chroma_db

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

USER alive

EXPOSE 8000

ENTRYPOINT ["bash", "scripts/entrypoint.sh"]