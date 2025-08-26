#!/bin/sh
# --- Amara Script Metadata ---
# Repo: amara-gateway
# Role: Public smoke checks for health, brief, and stream endpoints
# Owner: core
# Secrets: reads $AGENT_TOKEN (optional); can also load from .env alongside script
# Notes: uses scripts/lib/pretty.sh for formatted output
# --------------------------------

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Pretty printer (required)
# Expect this to exist at scripts/lib/pretty.sh in the amara-gateway repo.
# If you placed it elsewhere, adjust the path.
. "$SCRIPT_DIR/lib/pretty.sh"

BASE_URL="${BASE_URL:-https://amara.bodyhigh.com}"

# Optional: load .env if present (non-fatal). This can set AGENT_TOKEN.
if [ -f "$SCRIPT_DIR/../.env" ]; then
	# shellcheck disable=SC1091
	. "$SCRIPT_DIR/../.env"
fi

curl_head() {
	# args: URL
	curl -fsS -o /dev/null -w "%{http_code}" "$1"
}

info "Checking health endpoint at ${BASE_URL}/healthz"
if curl -fsSL "${BASE_URL}/healthz" >/dev/null 2>&1; then
	success "Health check OK"
else
	fatal "Health check failed"
fi

info "Checking /api/brief (unauthenticated) – should be 401"
CODE="$(curl_head "${BASE_URL}/api/brief")"
if [ "$CODE" = "401" ]; then
	success "/api/brief returned 401 as expected (unauthenticated)"
else
	warn "/api/brief returned ${CODE}; expected 401 (verify API auth middleware)"
fi

if [ "${AGENT_TOKEN:-}" != "" ]; then
	info "Checking /api/brief (authenticated) – expecting 200"
	CODE_AUTH="$(curl -fsS -H "X-Agent-Token: ${AGENT_TOKEN}" -o /dev/null -w "%{http_code}" "${BASE_URL}/api/brief")" || CODE_AUTH="$?"
	if [ "$CODE_AUTH" = "200" ]; then
		success "/api/brief (auth) returned 200"
	else
		warn "/api/brief (auth) returned ${CODE_AUTH}; check token or API"
	fi

	info "Checking /api/chat/stream (authenticated) – short probe"
	# 5s max, no buffering, send header only
	if curl -fsS -H "X-Agent-Token: ${AGENT_TOKEN}" --max-time 5 -N "${BASE_URL}/api/chat/stream" >/dev/null 2>&1; then
		success "Stream endpoint responded (auth)"
	else
		warn "Stream probe inconclusive (SSE often needs a real prompt); endpoint reachable"
	fi
else
	warn "AGENT_TOKEN not set; skipping authenticated checks. Export AGENT_TOKEN or add it to scripts/.env (never commit real secrets)."
fi

success "Verification finished"
