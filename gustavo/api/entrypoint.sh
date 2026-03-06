#!/bin/bash
set -e

# Default UI port — can be overridden by PORT env var or -p flag (mirrors "gustavo gui -p PORT")
UI_PORT=${PORT:-3000}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -p|--port) UI_PORT="$2"; shift ;;
        *) echo "Unknown parameter: $1" >&2; exit 1 ;;
    esac
    shift
done

export PORT=$UI_PORT
export FASTAPI_URL=${FASTAPI_URL:-http://127.0.0.1:8000}
export NODE_ENV=production
export NEXT_TELEMETRY_DISABLED=1

echo "Starting Gustavo — FastAPI on :8000, Next.js UI on :${UI_PORT}"

# Start FastAPI in the background first so it has a head start before
# the Next.js proxy begins serving requests.
/opt/venv/bin/uvicorn gustavo.api.main:app --host 127.0.0.1 --port 8000 &
UVICORN_PID=$!

# Wait up to 30 s for FastAPI to be ready before handing control to supervisor.
echo "Waiting for FastAPI to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "FastAPI is ready."
        break
    fi
    sleep 1
done

# Stop the pre-flight uvicorn; supervisor will restart it under its own control.
kill "$UVICORN_PID" 2>/dev/null || true
wait "$UVICORN_PID" 2>/dev/null || true

exec supervisord -n -c /etc/supervisord.conf
