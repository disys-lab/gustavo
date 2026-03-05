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
export FASTAPI_URL=${FASTAPI_URL:-http://localhost:8000}
export NODE_ENV=production
export NEXT_TELEMETRY_DISABLED=1

echo "Starting Gustavo — FastAPI on :8000, Next.js UI on :${UI_PORT}"

exec supervisord -n -c /etc/supervisord.conf
