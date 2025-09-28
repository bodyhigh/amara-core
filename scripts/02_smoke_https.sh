#!/bin/sh
# --- Amara Script Metadata ---
# Repo: amara-gateway
# Role: Quick HTTPS smoke tests (health, brief, stream)
# Owner: bodyhigh@github.com
# Notes: Uses minimal shell; no dependencies
# Secrets: reads $AGENT_TOKEN (optional); can also load from .env alongside script
# --------------------------------

set -euo pipefail

BASE_URL="${BASE_URL:-https://amara.bodyhigh.com}"
AGENT_TOKEN="${AGENT_TOKEN:-}"
H() { printf "\n== %s ==\n" "$*"; }

H "GET /api/healthz"
curl -fsS "${BASE_URL}/api/healthz" | sed 's/.*/OK/'

if [[ -n "${AGENT_TOKEN}" ]]; then
  H "Authorized ping"
  curl -fsS -H "X-Agent-Token: ${AGENT_TOKEN}" "${BASE_URL}/api/brief/view" >/dev/null && echo "OK"
fi

H "SSE smoke (5s)"
curl -N --max-time 5 "${BASE_URL}/api/stream/test" >/dev/null && echo "OK (no-buffer)"
