#!/bin/bash
# ──────────────────────────────────────────────
# Alive – Docker Entrypoint
# ──────────────────────────────────────────────
# Starts the application in the appropriate mode:
#   ENVIRONMENT=development  → uvicorn with --reload
#   ENVIRONMENT=production   → gunicorn with uvicorn workers
# ──────────────────────────────────────────────

set -e

# If running as root (e.g. on Railway, where mounted volumes are root-owned),
# fix ownership of the ChromaDB volume, then drop to the 'alive' user.
if [ "$(id -u)" = "0" ]; then
    mkdir -p /app/chroma_db
    chown -R alive:alive /app/chroma_db
    exec gosu alive "$0" "$@"
fi

# Port is injected by the host platform (Render, HF Spaces, etc.) via
# $PORT; falls back to 8000 when unset (local Docker, Oracle VM, VPS).
PORT="${PORT:-8000}"

if [ "$ENVIRONMENT" = "production" ]; then
    echo "Starting in production mode (gunicorn + uvicorn workers) on port ${PORT}..."
    exec gunicorn backend.main:app \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind "0.0.0.0:${PORT}" \
        --workers "${GUNICORN_WORKERS:-4}" \
        --timeout "${GUNICORN_TIMEOUT:-120}" \
        --graceful-timeout "${SHUTDOWN_TIMEOUT:-30}" \
        --access-logfile - \
        --error-logfile -
else
    echo "Starting in development mode (uvicorn --reload) on port ${PORT}..."
    exec uvicorn backend.main:app \
        --host 0.0.0.0 \
        --port "${PORT}" \
        --reload \
        --log-level "$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')"
fi
