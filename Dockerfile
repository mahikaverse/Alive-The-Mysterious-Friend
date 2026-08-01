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

# Ensure the entrypoint is executable (file modes are not preserved by git)
RUN chmod +x scripts/entrypoint.sh

# gosu lets the entrypoint drop from root to the 'alive' user after
# fixing ownership of mounted volumes (Railway mounts volumes as root).
RUN apt-get update && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*

# Create writable ChromaDB directory for the non-root user
RUN mkdir -p /app/chroma_db && chown -R alive:alive /app/chroma_db

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Runs as root so the entrypoint can chown mounted volumes, then
# drops to the 'alive' user via gosu.
ENTRYPOINT ["bash", "scripts/entrypoint.sh"]