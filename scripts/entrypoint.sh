#!/bin/bash
# ──────────────────────────────────────────────
# Alive – Docker Entrypoint
# ──────────────────────────────────────────────
# Starts the application in the appropriate mode:
#   ENVIRONMENT=development  → uvicorn with --reload
#   ENVIRONMENT=production   → gunicorn with uvicorn workers
# ──────────────────────────────────────────────

set -e

if [ "$ENVIRONMENT" = "production" ]; then
    echo "Starting in production mode (gunicorn + uvicorn workers)..."
    exec gunicorn backend.main:app \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-4}" \
        --timeout "${GUNICORN_TIMEOUT:-120}" \
        --graceful-timeout "${SHUTDOWN_TIMEOUT:-30}" \
        --access-logfile - \
        --error-logfile -
else
    echo "Starting in development mode (uvicorn --reload)..."
    exec uvicorn backend.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --log-level "${LOG_LEVEL,,:-info}"
fi
